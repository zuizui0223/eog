from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Callable
from urllib.parse import urlparse

from eog.v2.problem_contract import (
    BaselineFieldSpec,
    CandidateUnit,
    ObservationSemantics,
    freeze_pre_response_problem,
)


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_pre_response_certificate.json"
USER_AGENT = "EOG-Leipzig-RoeDeer-Endpoint3-Gate0/1.0"
EARTH_RADIUS_KM = 6371.0088
ByteFetcher = Callable[[str, int], bytes]


class Gate0Stop(RuntimeError):
    """Terminal response-blind source, registry, geometry or effort STOP."""


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _verify_source_bytes(raw: bytes, source: dict[str, object], label: str) -> None:
    if len(raw) != int(source["size_bytes"]):
        raise Gate0Stop(f"{label} byte-size drift")
    if git_blob_sha1(raw) != str(source["git_blob_sha1"]):
        raise Gate0Stop(f"{label} Git blob SHA-1 drift")


def _csv_rows(raw: bytes, label: str) -> tuple[list[str], list[dict[str, str]]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise Gate0Stop(f"{label} is not UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise Gate0Stop(f"{label} is empty") from exc
    if not header or any(not name for name in header) or len(set(header)) != len(header):
        raise Gate0Stop(f"{label} has duplicate/invalid physical columns")
    rows: list[dict[str, str]] = []
    for row_number, row in enumerate(reader, start=2):
        if len(row) != len(header):
            raise Gate0Stop(
                f"{label} row {row_number} has {len(row)} cells for {len(header)} columns"
            )
        rows.append(dict(zip(header, row, strict=True)))
    if not rows:
        raise Gate0Stop(f"{label} has no data rows")
    return header, rows


def _require_columns(header: list[str], required: list[str], label: str) -> None:
    missing = [name for name in required if name not in header]
    if missing:
        raise Gate0Stop(f"{label} missing required columns: {missing!r}")


def _strict_nonempty(value: object, label: str) -> str:
    text = str(value)
    if not text or text != text.strip():
        raise Gate0Stop(f"{label} is empty or padded")
    return text


def _finite_float(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise Gate0Stop(f"{label} is not numeric") from exc
    if not math.isfinite(numeric):
        raise Gate0Stop(f"{label} is not finite")
    return numeric


def _optional_float(value: object) -> float | None:
    text = "" if value is None else str(value).strip()
    if not text or text.casefold() in {"na", "nan", "null", "none"}:
        return None
    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _parse_aware_datetime(value: str, label: str) -> datetime:
    text = _strict_nonempty(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Gate0Stop(f"{label} is not an ISO-8601 datetime") from exc
    if parsed.utcoffset() is None:
        raise Gate0Stop(f"{label} lacks an explicit timezone offset")
    return parsed


def parse_source_code(raw: bytes, contract: dict[str, object]) -> dict[str, object]:
    source = contract["source"]["safe_files"]["source_code"]
    _verify_source_bytes(raw, source, "source code")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Gate0Stop("source code is not UTF-8") from exc
    match = re.search(r"species_of_interest\s*<-\s*c\((.*?)\)", text, flags=re.DOTALL)
    if match is None:
        raise Gate0Stop("source code no longer declares species_of_interest")
    observed = re.findall(r'[\"\']([^\"\']+)[\"\']', match.group(1))
    expected = list(contract["source_identity"]["focal_vector_exact"])
    if observed != expected:
        raise Gate0Stop(f"source focal vector drift: {observed!r} != {expected!r}")
    if not observed or observed[0] != contract["source_identity"]["focal_taxon"]:
        raise Gate0Stop("frozen focal taxon is not first in source vector")
    return {
        "focal_vector": observed,
        "focal_taxon": observed[0],
        "source_contains_year_rewrite_logic": (
            "Change year to 2024" in text or "year(deploymentStart) != 2024" in text
        ),
        "source_contains_LE39_manual_repair": "LE39" in text,
        "eog_applies_year_rewrite": False,
        "eog_applies_LE39_manual_repair": False,
        "fingerprint": canonical_sha256({"focal_vector": observed}),
    }


def parse_covariates(
    raw: bytes, contract: dict[str, object]
) -> tuple[dict[str, dict[str, str | None]], dict[str, object]]:
    source = contract["source"]["safe_files"]["covariates"]
    _verify_source_bytes(raw, source, "covariates")
    header, rows = _csv_rows(raw, "covariates")
    expected = list(contract["safe_schema"]["covariate_exact_columns"])
    if header != expected:
        raise Gate0Stop(f"covariate header drift: {header!r} != {expected!r}")
    mapping: dict[str, dict[str, str | None]] = {}
    for row_number, row in enumerate(rows, start=2):
        name = _strict_nonempty(row["locationName"], f"covariate locationName row {row_number}")
        if name in mapping:
            raise Gate0Stop(f"duplicate covariate locationName: {name}")
        mapping[name] = {
            field: (row[field].strip() or None)
            for field in ("TreeDensity", "VegetationCover", "ForestType")
        }
    return mapping, {
        "physical_row_count": len(rows),
        "location_count": len(mapping),
        "fingerprint": canonical_sha256(mapping),
    }


def union_intervals(values: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    if not values:
        return []
    normalized = sorted(
        (start.astimezone(timezone.utc), end.astimezone(timezone.utc))
        for start, end in values
    )
    merged: list[tuple[datetime, datetime]] = [normalized[0]]
    for start, end in normalized[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end:
            if end > current_end:
                merged[-1] = (current_start, end)
        else:
            merged.append((start, end))
    return merged


def interval_effort_days(values: list[tuple[datetime, datetime]]) -> float:
    return sum((end - start).total_seconds() for start, end in union_intervals(values)) / 86400.0


def parse_deployments(
    raw: bytes,
    contract: dict[str, object],
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    source = contract["source"]["safe_files"]["deployments"]
    _verify_source_bytes(raw, source, "deployments")
    header, rows = _csv_rows(raw, "deployments")
    _require_columns(
        header,
        list(contract["safe_schema"]["deployment_required_columns"]),
        "deployments",
    )
    seen_deployment_ids: set[str] = set()
    state: dict[str, dict[str, object]] = {}
    raw_years: Counter[int] = Counter()
    for row_number, row in enumerate(rows, start=2):
        deployment_id = _strict_nonempty(row["deploymentID"], f"deploymentID row {row_number}")
        if deployment_id in seen_deployment_ids:
            raise Gate0Stop(f"duplicate deploymentID: {deployment_id}")
        seen_deployment_ids.add(deployment_id)
        location_id = _strict_nonempty(row["locationID"], f"locationID row {row_number}")
        location_name = _strict_nonempty(row["locationName"], f"locationName row {row_number}")
        lat = _finite_float(row["latitude"], f"latitude for {location_id}")
        lon = _finite_float(row["longitude"], f"longitude for {location_id}")
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise Gate0Stop(f"invalid WGS84 coordinate for {location_id}")
        start = _parse_aware_datetime(row["deploymentStart"], f"deploymentStart for {deployment_id}")
        end = _parse_aware_datetime(row["deploymentEnd"], f"deploymentEnd for {deployment_id}")
        if end <= start:
            raise Gate0Stop(f"nonpositive raw deployment interval for {deployment_id}")
        raw_years[start.year] += 1
        current = state.get(location_id)
        if current is None:
            current = {
                "location_id": location_id,
                "location_name": location_name,
                "longitude": lon,
                "latitude": lat,
                "intervals": [],
                "camera_heights": [],
                "deployment_groups": set(),
                "deployment_ids": [],
            }
            state[location_id] = current
        else:
            if current["location_name"] != location_name:
                raise Gate0Stop(f"locationID maps to multiple locationName values: {location_id}")
            if current["longitude"] != lon or current["latitude"] != lat:
                raise Gate0Stop(f"coordinate drift across raw deployments for {location_id}")
        current["intervals"].append((start, end))
        current["deployment_ids"].append(deployment_id)
        height = _optional_float(row["cameraHeight"])
        if height is not None:
            current["camera_heights"].append(height)
        group = row["deploymentGroups"].strip()
        if group:
            current["deployment_groups"].add(group)

    threshold = float(contract["deployment_registry"]["minimum_effort_days_per_retained_location"])
    retained: dict[str, dict[str, object]] = {}
    effort_days_all: dict[str, float] = {}
    for location_id, current in state.items():
        merged = union_intervals(current["intervals"])
        effort_days = sum((end - start).total_seconds() for start, end in merged) / 86400.0
        effort_days_all[location_id] = effort_days
        if effort_days + 1e-12 < threshold:
            continue
        heights = list(current["camera_heights"])
        groups = sorted(current["deployment_groups"])
        retained[location_id] = {
            "location_id": location_id,
            "location_name": current["location_name"],
            "longitude": current["longitude"],
            "latitude": current["latitude"],
            "effort_days": effort_days,
            "merged_intervals": [
                [start.isoformat(), end.isoformat()] for start, end in merged
            ],
            "camera_height": float(median(heights)) if heights else None,
            "deployment_group": "|".join(groups) if groups else None,
            "deployment_count": len(current["deployment_ids"]),
        }
    minimum_nodes = int(contract["deployment_registry"]["minimum_stable_locations"])
    if len(retained) < minimum_nodes:
        raise Gate0Stop(
            f"only {len(retained)} stable raw locations meet effort threshold; require >= {minimum_nodes}"
        )
    return retained, {
        "physical_row_count": len(rows),
        "deployment_id_count": len(seen_deployment_ids),
        "raw_location_count": len(state),
        "retained_location_count": len(retained),
        "excluded_below_effort_count": len(state) - len(retained),
        "raw_start_year_counts": {str(year): raw_years[year] for year in sorted(raw_years)},
        "raw_year_values_preserved": True,
        "LE39_manual_repair_applied": False,
        "effort_days_fingerprint": canonical_sha256(
            [[key, effort_days_all[key]] for key in sorted(effort_days_all)]
        ),
    }


def _fold(node_id: str) -> int:
    digest = hashlib.sha256(node_id.encode("utf-8")).digest()
    return 1 + (int.from_bytes(digest[:8], "big") % 5)


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def linear_quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise Gate0Stop("no positive node-pair distances")
    position = (len(sorted_values) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    frac = position - lo
    return float(sorted_values[lo] + frac * (sorted_values[hi] - sorted_values[lo]))


def derive_world_family(
    node_ids: list[str],
    registry: dict[str, dict[str, object]],
    contract: dict[str, object],
) -> dict[str, object]:
    pairs: list[tuple[str, str, float]] = []
    for index, left in enumerate(node_ids):
        lon1 = float(registry[left]["longitude"])
        lat1 = float(registry[left]["latitude"])
        for right in node_ids[index + 1 :]:
            lon2 = float(registry[right]["longitude"])
            lat2 = float(registry[right]["latitude"])
            distance = haversine_km(lon1, lat1, lon2, lat2)
            if not math.isfinite(distance) or distance <= 0:
                raise Gate0Stop(f"nonpositive pair distance for {left}/{right}")
            pairs.append((left, right, distance))
    distances = sorted(distance for _, _, distance in pairs)
    worlds: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw_q in contract["world_geometry"]["threshold_quantiles"]:
        q = float(raw_q)
        threshold = linear_quantile(distances, q)
        edges = sorted([[a, b] for a, b, distance in pairs if distance <= threshold])
        graph_fp = canonical_sha256({"nodes": node_ids, "edges": edges})
        if graph_fp in seen:
            continue
        seen.add(graph_fp)
        worlds.append(
            {
                "world_id": f"haversine_q{int(round(q * 100)):02d}",
                "quantile": q,
                "threshold_km": threshold,
                "edge_count": len(edges),
                "graph_fingerprint": graph_fp,
            }
        )
    minimum = int(contract["world_geometry"]["minimum_distinct_positive_local_worlds"])
    if len(worlds) < minimum or any(int(world["edge_count"]) <= 0 for world in worlds):
        raise Gate0Stop(f"only {len(worlds)} distinct positive local worlds; require >= {minimum}")
    complete_edges = [[a, b] for i, a in enumerate(node_ids) for b in node_ids[i + 1 :]]
    external_fp = canonical_sha256({"nodes": node_ids, "edges": complete_edges})
    payload = {
        "node_ids": node_ids,
        "local_worlds": worlds,
        "external_open": {
            "world_id": "external_open",
            "edge_count": len(complete_edges),
            "graph_fingerprint": external_fp,
        },
    }
    return {
        "pair_count": len(pairs),
        "pair_distance_fingerprint": canonical_sha256([[a, b, d] for a, b, d in pairs]),
        "local_worlds": worlds,
        "external_open": payload["external_open"],
        "fingerprint": canonical_sha256(payload),
    }


def _problem_to_dict(problem) -> dict[str, object]:
    return {
        "schema": "eog.normalized_pre_response_problem.v1",
        "node_ids": list(problem.node_ids),
        "component_ids": list(problem.component_ids),
        "context_ids": list(problem.context_ids),
        "candidate_units": [
            {
                "unit_id": unit.unit_id,
                "node_id": unit.node_id,
                "context_id": unit.context_id,
                "fold": unit.fold,
            }
            for unit in problem.candidate_units
        ],
        "observation_semantics": {
            "effort_eligible_rule": problem.observation_semantics.effort_eligible_rule,
            "positive_rule": problem.observation_semantics.positive_rule,
            "negative_rule": problem.observation_semantics.negative_rule,
            "unsurveyed_rule": problem.observation_semantics.unsurveyed_rule,
            "zero_interpretation": problem.observation_semantics.zero_interpretation,
        },
        "baseline_fields": [
            {
                "name": field.name,
                "kind": field.kind,
                "missing_policy": field.missing_policy,
            }
            for field in problem.baseline_fields
        ],
        "split_fingerprint": problem.split_fingerprint,
        "world_family_fingerprint": problem.world_family_fingerprint,
        "source_fingerprint": problem.source_fingerprint,
        "response_locked": problem.response_locked,
        "fingerprint": problem.fingerprint,
    }


def freeze_from_safe_bytes(
    deployments_raw: bytes,
    covariates_raw: bytes,
    source_code_raw: bytes,
    contract: dict[str, object],
) -> dict[str, object]:
    source_code = parse_source_code(source_code_raw, contract)
    covariates, covariate_audit = parse_covariates(covariates_raw, contract)
    registry, deployment_audit = parse_deployments(deployments_raw, contract)
    node_ids = sorted(registry)
    fold_map = {node_id: _fold(node_id) for node_id in node_ids}
    fold_counts = Counter(fold_map.values())
    expected_folds = set(int(value) for value in contract["heldout_split"]["fold_ids"])
    if set(fold_counts) != expected_folds or any(fold_counts[fold] <= 0 for fold in expected_folds):
        raise Gate0Stop(f"response-blind location folds are not all nonempty: {dict(fold_counts)}")
    split_fp = canonical_sha256([[node_id, fold_map[node_id]] for node_id in node_ids])
    world_family = derive_world_family(node_ids, registry, contract)

    baseline_rows: list[dict[str, object]] = []
    for node_id in node_ids:
        row = registry[node_id]
        cov = covariates.get(str(row["location_name"]), {})
        baseline_rows.append(
            {
                "node_id": node_id,
                "longitude": row["longitude"],
                "latitude": row["latitude"],
                "log_effort_days": math.log(float(row["effort_days"])),
                "camera_height": row["camera_height"],
                "deployment_group": row["deployment_group"],
                "TreeDensity": cov.get("TreeDensity"),
                "VegetationCover": cov.get("VegetationCover"),
                "ForestType": cov.get("ForestType"),
            }
        )
    baseline_fp = canonical_sha256(baseline_rows)
    source_fp = canonical_sha256(
        {
            "repository": contract["source"]["repository"],
            "commit": contract["source"]["commit"],
            "safe_git_blobs": {
                role: entry["git_blob_sha1"]
                for role, entry in sorted(contract["source"]["safe_files"].items())
            },
            "focal_vector": source_code["focal_vector"],
            "retained_nodes": node_ids,
        }
    )
    fields = tuple(
        BaselineFieldSpec(
            name=str(spec["name"]),
            kind=str(spec["kind"]),
            missing_policy=str(spec["missing_policy"]),
        )
        for spec in contract["baseline"]["fields"]
    )
    semantics = ObservationSemantics(**contract["observation_semantics"])
    context_id = "raw_effort_aggregate"
    units = tuple(
        CandidateUnit(
            unit_id=node_id,
            node_id=node_id,
            context_id=context_id,
            fold=fold_map[node_id],
        )
        for node_id in node_ids
    )
    problem = freeze_pre_response_problem(
        node_ids=node_ids,
        component_ids=[contract["world_geometry"]["component_id"]] * len(node_ids),
        context_ids=[context_id],
        candidate_units=units,
        observation_semantics=semantics,
        baseline_fields=fields,
        split_fingerprint=split_fp,
        world_family_fingerprint=str(world_family["fingerprint"]),
        source_fingerprint=source_fp,
    )
    return {
        "source_code_audit": source_code,
        "covariate_audit": covariate_audit,
        "deployment_audit": deployment_audit,
        "candidate_node_count": len(node_ids),
        "candidate_unit_count": len(units),
        "context_count": 1,
        "site_fold_counts": {str(fold): fold_counts[fold] for fold in sorted(fold_counts)},
        "split_fingerprint": split_fp,
        "world_family": world_family,
        "baseline_rows": baseline_rows,
        "baseline_fingerprint": baseline_fp,
        "source_fingerprint": source_fp,
        "normalized_problem": _problem_to_dict(problem),
        "node_registry_fingerprint": canonical_sha256(
            [
                {
                    "node_id": node_id,
                    "location_name": registry[node_id]["location_name"],
                    "longitude": registry[node_id]["longitude"],
                    "latitude": registry[node_id]["latitude"],
                    "effort_days": registry[node_id]["effort_days"],
                }
                for node_id in node_ids
            ]
        ),
    }


def fetch_exact_raw_github(url: str, expected_size: int) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise Gate0Stop("safe file URL left frozen raw.githubusercontent.com host")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise Gate0Stop(f"safe file GET returned HTTP {exc.code}; body was not opened") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise Gate0Stop(f"safe file transport unavailable: {exc}") from exc
    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200:
            raise Gate0Stop(f"safe file GET returned HTTP {status}")
        if response.geturl() != url:
            raise Gate0Stop("safe file GET final URL drift")
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise Gate0Stop("safe file GET unexpectedly applied content encoding")
        body = response.read(expected_size + 1)
    if len(body) != expected_size:
        raise Gate0Stop(f"safe file GET opened {len(body)} bytes instead of exact {expected_size}")
    return body


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    fetcher: ByteFetcher = fetch_exact_raw_github,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    safe_files = contract["source"]["safe_files"]
    forbidden_url = str(contract["source"]["forbidden_response"]["raw_url"])
    safe_urls = [str(safe_files[role]["raw_url"]) for role in ("deployments", "covariates", "source_code")]
    if forbidden_url in safe_urls or len(set(safe_urls)) != 3:
        raise RuntimeError("Gate0 safe URL firewall is internally invalid")
    base: dict[str, object] = {
        "schema": "eog.leipzig_roedeer_endpoint3.gate0_pre_response.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "status": None,
        "safe_file_requests": 0,
        "safe_file_bytes_opened": 0,
        "observations_requests": 0,
        "observations_header_bytes_opened": 0,
        "observations_payload_bytes_opened": 0,
        "observations_rows_opened": 0,
        "observations_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    opened: dict[str, bytes] = {}
    try:
        for role in ("deployments", "covariates", "source_code"):
            entry = safe_files[role]
            raw = fetcher(str(entry["raw_url"]), int(entry["size_bytes"]))
            base["safe_file_requests"] = int(base["safe_file_requests"]) + 1
            base["safe_file_bytes_opened"] = int(base["safe_file_bytes_opened"]) + len(raw)
            opened[role] = raw
        frozen = freeze_from_safe_bytes(
            opened["deployments"],
            opened["covariates"],
            opened["source_code"],
            contract,
        )
        result = {
            **base,
            **frozen,
            "status": "gate0_pre_response_ready",
            "next_gate": "observations_header_only",
            "response_locked": True,
        }
    except Gate0Stop as exc:
        result = {
            **base,
            "status": "stop_pre_response_source_registry_geometry_or_effort",
            "reason": str(exc),
            "response_locked": True,
            "retry_or_post_result_repair_allowed": False,
        }
    result["result_fingerprint"] = canonical_sha256(result)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
