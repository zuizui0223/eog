from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
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
USER_AGENT = "EOG-Algar-Whitetail-Endpoint3-Gate0/1.0"
EARTH_RADIUS_KM = 6371.0088
ByteFetcher = Callable[[str, int], bytes]


class Gate0Stop(RuntimeError):
    """Terminal response-blind source/registry/geometry STOP."""


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
    if not header or len(set(header)) != len(header):
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


def _finite_float(value: object, label: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise Gate0Stop(f"{label} is not numeric") from exc
    if not math.isfinite(numeric):
        raise Gate0Stop(f"{label} is not finite")
    return numeric


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.casefold() in {"na", "nan", "null", "none"}:
        return None
    try:
        numeric = float(text)
    except ValueError:
        return None
    return numeric if math.isfinite(numeric) else None


def _parse_date(value: str, label: str, *, allow_missing: bool = False) -> date | None:
    text = value.strip()
    if allow_missing and (not text or text.casefold() in {"na", "nan", "null", "none"}):
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise Gate0Stop(f"{label} is not ISO date") from exc


def parse_projects(raw: bytes, contract: dict[str, object]) -> dict[str, str]:
    source = contract["source"]["safe_files"]["projects"]
    _verify_source_bytes(raw, source, "projects")
    header, rows = _csv_rows(raw, "projects")
    _require_columns(header, list(contract["safe_schema"]["project_required_columns"]), "projects")
    project_id = str(contract["source_identity"]["project_id"])
    matches = [row for row in rows if row["project_id"] == project_id]
    if len(matches) != 1:
        raise Gate0Stop(f"expected exactly one frozen project row for {project_id!r}")
    row = matches[0]
    if row["project_short_name"] != contract["source_identity"]["project_short_name"]:
        raise Gate0Stop("project short-name identity drift")
    return row


def parse_common_names(raw: bytes, contract: dict[str, object]) -> None:
    source = contract["source"]["safe_files"]["common_names"]
    _verify_source_bytes(raw, source, "common names")
    header, rows = _csv_rows(raw, "common names")
    expected = list(contract["safe_schema"]["common_names_exact_columns"])
    if header != expected:
        raise Gate0Stop(f"common-names header drift: {header!r} != {expected!r}")
    common = str(contract["source_identity"]["focal_common_name"])
    species = str(contract["source_identity"]["focal_species_identifier"])
    matches = [row for row in rows if row["common_name"] == common and row["sp"] == species]
    if len(matches) != 1:
        raise Gate0Stop("frozen focal species mapping is not uniquely reproduced")


def parse_cameras(raw: bytes, contract: dict[str, object]) -> dict[str, object]:
    source = contract["source"]["safe_files"]["cameras"]
    _verify_source_bytes(raw, source, "cameras")
    header, rows = _csv_rows(raw, "cameras")
    _require_columns(header, list(contract["safe_schema"]["camera_required_columns"]), "cameras")
    ids = [row["camera_id"].strip() for row in rows if row["camera_id"].strip()]
    return {
        "physical_row_count": len(rows),
        "nonempty_camera_id_count": len(ids),
        "unique_nonempty_camera_id_count": len(set(ids)),
        "fingerprint": canonical_sha256(rows),
    }


def parse_local_covariate(raw: bytes, contract: dict[str, object]) -> dict[str, float | None]:
    source = contract["source"]["safe_files"]["local_covariate"]
    _verify_source_bytes(raw, source, "local covariate")
    header, rows = _csv_rows(raw, "local covariate")
    expected = list(contract["safe_schema"]["local_covariate_exact_columns"])
    if header != expected:
        raise Gate0Stop(f"local-covariate header drift: {header!r} != {expected!r}")
    mapping: dict[str, float | None] = {}
    for row_number, row in enumerate(rows, start=2):
        placename = row["placename"].strip()
        if not placename or placename != row["placename"] or placename in mapping:
            raise Gate0Stop(f"invalid/duplicate local-covariate placename at row {row_number}")
        mapping[placename] = _optional_float(row["line_of_sight_m"])
    return mapping


def parse_deployments(
    raw: bytes,
    contract: dict[str, object],
) -> tuple[dict[str, tuple[float, float]], dict[str, list[tuple[date, date]]], dict[str, object]]:
    source = contract["source"]["safe_files"]["deployments"]
    _verify_source_bytes(raw, source, "deployments")
    header, rows = _csv_rows(raw, "deployments")
    _require_columns(header, list(contract["safe_schema"]["deployment_required_columns"]), "deployments")
    project_id = str(contract["source_identity"]["project_id"])
    operational = str(contract["deployment_registry"]["valid_operational_status"]).split(" == ", 1)[-1]
    tolerance = 1e-9
    coords: dict[str, tuple[float, float]] = {}
    intervals: dict[str, list[tuple[date, date]]] = {}
    project_rows = 0
    valid_coverage_rows = 0
    missing_end_rows = 0
    nonoperational_rows = 0
    deployment_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        if row["project_id"] != project_id:
            continue
        project_rows += 1
        deployment_id = row["deployment_id"].strip()
        placename = row["placename"].strip()
        if not deployment_id or deployment_id in deployment_ids:
            raise Gate0Stop(f"invalid/duplicate Algar deployment_id at row {row_number}")
        deployment_ids.add(deployment_id)
        if not placename or placename != row["placename"]:
            raise Gate0Stop(f"invalid Algar placename at row {row_number}")
        lon = _finite_float(row["longitude"], f"longitude for {placename}")
        lat = _finite_float(row["latitude"], f"latitude for {placename}")
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise Gate0Stop(f"invalid WGS84 coordinate for {placename}")
        old = coords.get(placename)
        if old is None:
            coords[placename] = (lon, lat)
        elif abs(old[0] - lon) > tolerance or abs(old[1] - lat) > tolerance:
            raise Gate0Stop(f"coordinate drift across deployments for {placename}")

        start = _parse_date(row["start_date"], f"start_date for {deployment_id}")
        end = _parse_date(row["end_date"], f"end_date for {deployment_id}", allow_missing=True)
        if end is None:
            missing_end_rows += 1
            continue
        if end <= start:
            raise Gate0Stop(f"nonpositive deployment interval for {deployment_id}")
        if row["camera_functioning"].strip() != operational:
            nonoperational_rows += 1
            continue
        intervals.setdefault(placename, []).append((start, end))
        valid_coverage_rows += 1
    if not project_rows:
        raise Gate0Stop("no frozen Algar deployment rows")
    return coords, intervals, {
        "physical_row_count": len(rows),
        "algar_row_count": project_rows,
        "valid_coverage_row_count": valid_coverage_rows,
        "missing_end_row_count": missing_end_rows,
        "nonoperational_row_count": nonoperational_rows,
        "deployment_id_count": len(deployment_ids),
    }


def union_intervals(values: list[tuple[date, date]]) -> list[tuple[date, date]]:
    if not values:
        return []
    ordered = sorted(values)
    merged: list[tuple[date, date]] = [ordered[0]]
    for start, end in ordered[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end:
            if end > current_end:
                merged[-1] = (current_start, end)
        else:
            merged.append((start, end))
    return merged


def candidate_week_starts(contract: dict[str, object]) -> tuple[date, ...]:
    start = date.fromisoformat(str(contract["candidate_registry"]["first_candidate_week_start"]))
    last = date.fromisoformat(str(contract["candidate_registry"]["last_candidate_week_start"]))
    if start.weekday() != 0 or last.weekday() != 0 or last < start:
        raise Gate0Stop("frozen candidate week anchors are invalid")
    values: list[date] = []
    cursor = start
    while cursor <= last:
        values.append(cursor)
        cursor += timedelta(days=7)
    return tuple(values)


def interval_covers_week(intervals: list[tuple[date, date]], week_start: date) -> bool:
    week_end = week_start + timedelta(days=7)
    return any(start <= week_start and end >= week_end for start, end in intervals)


def _fold(placename: str) -> int:
    digest = hashlib.sha256(placename.encode("utf-8")).digest()
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
    nodes: list[str],
    coords: dict[str, tuple[float, float]],
    contract: dict[str, object],
) -> dict[str, object]:
    pairs: list[tuple[str, str, float]] = []
    for i, left in enumerate(nodes):
        lon1, lat1 = coords[left]
        for right in nodes[i + 1 :]:
            lon2, lat2 = coords[right]
            distance = haversine_km(lon1, lat1, lon2, lat2)
            if not math.isfinite(distance) or distance <= 0:
                raise Gate0Stop(f"nonpositive pair distance for {left}/{right}")
            pairs.append((left, right, distance))
    distances = sorted(distance for _, _, distance in pairs)
    worlds: list[dict[str, object]] = []
    seen_graphs: set[str] = set()
    for raw_q in contract["world_geometry"]["threshold_quantiles"]:
        q = float(raw_q)
        threshold = linear_quantile(distances, q)
        edges = sorted([[a, b] for a, b, d in pairs if d <= threshold])
        graph_fp = canonical_sha256({"nodes": nodes, "edges": edges})
        if graph_fp in seen_graphs:
            continue
        seen_graphs.add(graph_fp)
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
    payload = {
        "node_ids": nodes,
        "local_worlds": worlds,
        "external_open": "explicit_permissive",
    }
    return {
        "pair_count": len(pairs),
        "pair_distance_fingerprint": canonical_sha256([[a, b, d] for a, b, d in pairs]),
        "local_worlds": worlds,
        "external_open": {"world_id": "external_open", "semantics": "explicit permissive analytical alternative"},
        "world_family_fingerprint": canonical_sha256(payload),
    }


def evaluate_pre_response(payloads: dict[str, bytes], contract: dict[str, object]) -> dict[str, object]:
    parse_projects(payloads["projects"], contract)
    parse_common_names(payloads["common_names"], contract)
    camera_audit = parse_cameras(payloads["cameras"], contract)
    local_covariates = parse_local_covariate(payloads["local_covariate"], contract)
    coords, raw_intervals, deployment_audit = parse_deployments(payloads["deployments"], contract)

    weeks = candidate_week_starts(contract)
    unioned = {placename: union_intervals(values) for placename, values in raw_intervals.items()}
    node_weeks: dict[str, list[date]] = {}
    for placename in sorted(unioned):
        eligible = [week for week in weeks if interval_covers_week(unioned[placename], week)]
        if eligible:
            node_weeks[placename] = eligible
    nodes = sorted(node_weeks)
    minimum_nodes = int(contract["candidate_registry"]["minimum_unique_nodes"])
    if len(nodes) < minimum_nodes:
        raise Gate0Stop(f"only {len(nodes)} response-independent eligible Algar nodes; require >= {minimum_nodes}")
    units = [
        CandidateUnit(
            unit_id=f"{placename}|{week.isoformat()}",
            node_id=placename,
            context_id=week.isoformat(),
            fold=_fold(placename),
        )
        for placename in nodes
        for week in node_weeks[placename]
    ]
    if len(units) < int(contract["candidate_registry"]["minimum_candidate_units"]):
        raise Gate0Stop(f"only {len(units)} response-independent candidate site-weeks")
    contexts = sorted({unit.context_id for unit in units})
    if len(contexts) < int(contract["candidate_registry"]["minimum_distinct_contexts"]):
        raise Gate0Stop(f"only {len(contexts)} distinct complete-week contexts")
    fold_counts = Counter(_fold(node) for node in nodes)
    if sorted(fold_counts) != [1, 2, 3, 4, 5]:
        raise Gate0Stop("frozen placename hash did not populate all five folds")

    world_family = derive_world_family(nodes, coords, contract)
    split_fingerprint = canonical_sha256([[node, _fold(node)] for node in nodes])
    source_fingerprint = canonical_sha256(
        {
            "repository": contract["source"]["repository"],
            "commit": contract["source"]["commit"],
            "safe_blobs": {
                role: contract["source"]["safe_files"][role]["git_blob_sha1"]
                for role in sorted(contract["source"]["safe_files"])
            },
            "adapter_schema": "eog.algar_whitetail_endpoint3.adapter.v1",
        }
    )
    baseline_specs = tuple(
        BaselineFieldSpec(**raw)
        for raw in [
            *contract["baseline"]["required_fields"],
            *contract["baseline"]["optional_fields"],
        ]
    )
    normalized = freeze_pre_response_problem(
        node_ids=nodes,
        component_ids=[str(contract["world_geometry"]["component_id"])] * len(nodes),
        context_ids=contexts,
        candidate_units=units,
        observation_semantics=ObservationSemantics(
            effort_eligible_rule=str(contract["observation_semantics"]["effort_eligible_rule"]),
            positive_rule=str(contract["observation_semantics"]["positive_rule"]),
            negative_rule=str(contract["observation_semantics"]["negative_rule"]),
            unsurveyed_rule=str(contract["observation_semantics"]["unsurveyed_rule"]),
            zero_interpretation=str(contract["observation_semantics"]["zero_interpretation"]),
        ),
        baseline_fields=baseline_specs,
        split_fingerprint=split_fingerprint,
        world_family_fingerprint=str(world_family["world_family_fingerprint"]),
        source_fingerprint=source_fingerprint,
    )

    optional_values = {node: local_covariates.get(node) for node in nodes}
    missing_line_of_sight = sum(value is None for value in optional_values.values())
    candidate_unit_rows = [[unit.unit_id, unit.node_id, unit.context_id, unit.fold] for unit in units]
    interval_rows = [
        [node, [[start.isoformat(), end.isoformat()] for start, end in unioned[node]]]
        for node in nodes
    ]
    result: dict[str, object] = {
        "schema": "eog.algar_whitetail_endpoint3.gate0_pre_response.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": "gate0_pre_response_ready",
        "focal_species": contract["source_identity"]["focal_species_identifier"],
        "candidate_node_count": len(nodes),
        "candidate_unit_count": len(units),
        "context_count": len(contexts),
        "first_context": contexts[0],
        "last_context": contexts[-1],
        "site_fold_counts": {str(k): v for k, v in sorted(fold_counts.items())},
        "deployment_audit": deployment_audit,
        "camera_file_audit": camera_audit,
        "eligible_interval_fingerprint": canonical_sha256(interval_rows),
        "candidate_unit_fingerprint": canonical_sha256(candidate_unit_rows),
        "optional_baseline_audit": {
            "line_of_sight_rows_in_source": len(local_covariates),
            "candidate_nodes_missing_or_nonnumeric_line_of_sight": missing_line_of_sight,
            "missing_policy": "calibration_median_plus_indicator",
            "missingness_causes_gate0_stop": False,
        },
        "world_family": world_family,
        "normalized_problem": {
            "schema": "eog.normalized_pre_response_problem.v1",
            "fingerprint": normalized.fingerprint,
            "response_locked": normalized.response_locked,
            "node_count": len(normalized.node_ids),
            "context_count": len(normalized.context_ids),
            "candidate_unit_count": len(normalized.candidate_units),
            "baseline_fields": [
                {"name": spec.name, "kind": spec.kind, "missing_policy": spec.missing_policy}
                for spec in normalized.baseline_fields
            ],
            "split_fingerprint": normalized.split_fingerprint,
            "world_family_fingerprint": normalized.world_family_fingerprint,
            "source_fingerprint": normalized.source_fingerprint,
        },
        "safe_file_requests": 5,
        "safe_file_bytes_opened": sum(len(value) for value in payloads.values()),
        "images_requests": 0,
        "images_header_bytes_opened": 0,
        "images_payload_bytes_opened": 0,
        "images_rows_opened": 0,
        "images_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
        "next_gate": "freeze exact images.csv physical header only; no response data row/value",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def _http_fetch_bytes(url: str, maximum: int) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise Gate0Stop("safe source URL left raw.githubusercontent.com")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status != 200:
                raise Gate0Stop(f"safe file returned HTTP {status}")
            if response.geturl() != url:
                raise Gate0Stop("safe file request changed frozen URL identity")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate0Stop("safe file unexpectedly used content encoding")
            body = response.read(maximum + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise Gate0Stop(f"safe file transport unavailable: {exc}") from exc
    if len(body) > maximum:
        raise Gate0Stop("safe file exceeded frozen byte cap")
    return body


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    fetch_bytes: ByteFetcher = _http_fetch_bytes,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    base: dict[str, object] = {
        "schema": "eog.algar_whitetail_endpoint3.gate0_pre_response.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "safe_file_requests": 0,
        "safe_file_bytes_opened": 0,
        "images_requests": 0,
        "images_header_bytes_opened": 0,
        "images_payload_bytes_opened": 0,
        "images_rows_opened": 0,
        "images_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    payloads: dict[str, bytes] = {}
    requests = 0
    opened = 0
    try:
        safe = contract["source"]["safe_files"]
        for role in ("deployments", "cameras", "projects", "local_covariate", "common_names"):
            source = safe[role]
            raw = fetch_bytes(str(source["raw_url"]), int(source["size_bytes"]))
            requests += 1
            opened += len(raw)
            payloads[role] = raw
        if opened > int(contract["gate0_firewall"]["maximum_safe_file_bytes_total"]):
            raise Gate0Stop("safe-file total exceeded frozen byte cap")
        result = {**base, **evaluate_pre_response(payloads, contract)}
        result["safe_file_requests"] = requests
        result["safe_file_bytes_opened"] = opened
        result["fingerprint"] = canonical_sha256({k: v for k, v in result.items() if k != "fingerprint"})
    except (Gate0Stop, ValueError) as exc:
        result = {
            **base,
            "safe_file_requests": requests,
            "safe_file_bytes_opened": opened,
            "status": "stop_pre_response_source_registry_or_geometry",
            "reason": str(exc),
            "next_gate": "none; do not open images.csv and do not repair this attempt post-STOP",
        }
        result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
