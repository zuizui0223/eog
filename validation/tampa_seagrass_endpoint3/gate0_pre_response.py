"""Response-blind Gate0 adapter for Tampa Bay seagrass endpoint 3.

Only the frozen Darwin Core Event file is opened here. Occurrence and eMoF are
biological-response-bearing files and remain completely unopened until later gates.
"""
from __future__ import annotations

import csv
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from eog.v2.problem_contract import (
    BaselineFieldSpec,
    CandidateUnit,
    ObservationSemantics,
    freeze_pre_response_problem,
)


ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "source_contract.json"
OUTPUT_PATH = ROOT / "gate0_pre_response_certificate.json"
EARTH_RADIUS_KM = 6371.0088


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def deterministic_fold(node_id: str) -> int:
    digest = hashlib.sha256(node_id.encode("utf-8")).hexdigest()
    return 1 + (int(digest[:16], 16) % 5)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1 = a
    lon2, lat2 = b
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2.0) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2.0) ** 2
    h = min(1.0, max(0.0, h))
    return 2.0 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def linear_quantile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        raise ValueError("cannot compute quantile of empty values")
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(sorted_values[lo])
    weight = pos - lo
    return float(sorted_values[lo] * (1.0 - weight) + sorted_values[hi] * weight)


def _finite_float(value: object, label: str) -> float:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is not numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} is not finite")
    return result


def _optional_finite_float(value: object, label: str) -> float | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    return _finite_float(text, label)


def _required_text(value: object, label: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _strict_int(value: object, label: str) -> int:
    text = _required_text(value, label)
    try:
        result = int(text)
    except ValueError as exc:
        raise ValueError(f"{label} is not an integer") from exc
    if str(result) != text and text != f"+{result}":
        raise ValueError(f"{label} is not a canonical integer")
    return result


def _parse_parent_date(row: dict[str, str], row_number: int) -> date:
    text = _required_text(row.get("eventDate"), f"eventDate row {row_number}")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"parent eventDate must be YYYY-MM-DD at row {row_number}") from exc
    year = _strict_int(row.get("year"), f"year row {row_number}")
    month = _strict_int(row.get("month"), f"month row {row_number}")
    day = _strict_int(row.get("day"), f"day row {row_number}")
    if (year, month, day) != (parsed.year, parsed.month, parsed.day):
        raise ValueError(f"parent date fields disagree at row {row_number}")
    return parsed


def _normalized_problem_dict(problem) -> dict[str, object]:
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
            {"name": field.name, "kind": field.kind, "missing_policy": field.missing_policy}
            for field in problem.baseline_fields
        ],
        "split_fingerprint": problem.split_fingerprint,
        "world_family_fingerprint": problem.world_family_fingerprint,
        "source_fingerprint": problem.source_fingerprint,
        "response_locked": problem.response_locked,
        "fingerprint": problem.fingerprint,
    }


def _default_fetcher(file_spec: dict[str, object], state: dict[str, object]) -> bytes:
    url = str(file_spec["url"])
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "raw.githubusercontent.com":
        raise ValueError("safe Event URL is outside frozen raw.githubusercontent.com HTTPS host")
    state["safe_file_requests"] += 1
    req = Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "eog-response-blind-gate0"})
    expected = int(file_spec["size_bytes"])
    with urlopen(req, timeout=60) as response:
        if response.status != 200:
            raise ValueError(f"safe Event GET returned HTTP {response.status}")
        encoding = response.headers.get("Content-Encoding")
        if encoding not in (None, "", "identity"):
            raise ValueError(f"unexpected safe Event content encoding: {encoding}")
        data = response.read(expected + 1)
    state["safe_file_bytes_opened"] += len(data)
    return data


def build_gate0_certificate(event_bytes: bytes, contract: dict[str, object], state: dict[str, object] | None = None) -> dict[str, object]:
    state = state if state is not None else {
        "safe_file_requests": 0,
        "safe_file_bytes_opened": len(event_bytes),
        "occurrence_requests": 0,
        "occurrence_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "occurrence_values_opened": False,
        "emof_requests": 0,
        "emof_bytes_opened": 0,
        "emof_rows_opened": 0,
        "emof_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    event_spec = contract["safe_files"]["event"]
    expected_size = int(event_spec["size_bytes"])
    if len(event_bytes) != expected_size:
        raise ValueError(f"Event byte size mismatch: {len(event_bytes)} != {expected_size}")
    observed_blob = git_blob_sha1(event_bytes)
    if observed_blob != event_spec["git_blob_sha1"]:
        raise ValueError(f"Event Git blob mismatch: {observed_blob}")

    try:
        text = event_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Event file is not strict UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_header = list(contract["event_header"])
    if reader.fieldnames != expected_header:
        raise ValueError(f"Event header mismatch: {reader.fieldnames!r}")

    event_ids: set[str] = set()
    parents: dict[str, dict[str, object]] = {}
    child_links: dict[str, list[tuple[str, float | None]]] = {}
    event_row_count = 0
    parent_row_count = 0
    child_row_count = 0

    for row_number, row in enumerate(reader, start=2):
        event_row_count += 1
        event_id = _required_text(row.get("eventID"), f"eventID row {row_number}")
        if event_id in event_ids:
            raise ValueError(f"duplicate eventID at row {row_number}: {event_id}")
        event_ids.add(event_id)
        event_type = _required_text(row.get("eventType"), f"eventType row {row_number}")
        if event_type not in {"Transect", "Point"}:
            raise ValueError(f"unsupported eventType at row {row_number}: {event_type}")
        datum = _required_text(row.get("geodeticDatum"), f"geodeticDatum row {row_number}")
        if datum != contract["candidate_registry"]["required_geodetic_datum"]:
            raise ValueError(f"unexpected geodeticDatum at row {row_number}: {datum}")
        lon = _finite_float(row.get("decimalLongitude"), f"decimalLongitude row {row_number}")
        lat = _finite_float(row.get("decimalLatitude"), f"decimalLatitude row {row_number}")
        if not (-180.0 <= lon <= 180.0 and -90.0 <= lat <= 90.0):
            raise ValueError(f"coordinate out of range at row {row_number}")

        if event_type == "Transect":
            parent_row_count += 1
            if str(row.get("parentEventID") or "").strip():
                raise ValueError(f"parent Transect has parentEventID at row {row_number}")
            parsed_date = _parse_parent_date(row, row_number)
            location_id = _required_text(row.get("locationID"), f"parent locationID row {row_number}")
            water_body = _required_text(row.get("waterBody"), f"parent waterBody row {row_number}")
            parents[event_id] = {
                "event_id": event_id,
                "location_id": location_id,
                "event_date": parsed_date.isoformat(),
                "year": parsed_date.year,
                "day_of_year": parsed_date.timetuple().tm_yday,
                "longitude": lon,
                "latitude": lat,
                "water_body": water_body,
            }
        else:
            child_row_count += 1
            parent_id = _required_text(row.get("parentEventID"), f"child parentEventID row {row_number}")
            depth = _optional_finite_float(row.get("minimumDepthInMeters"), f"minimumDepthInMeters row {row_number}")
            child_links.setdefault(parent_id, []).append((event_id, depth))

    if not parents:
        raise ValueError("Event core contains no parent Transect events")
    if not child_links:
        raise ValueError("Event core contains no child Point events")
    unknown_parent_links = sorted(set(child_links).difference(parents))
    if unknown_parent_links:
        raise ValueError(f"child Point links to unknown parent event: {unknown_parent_links[0]}")

    minimum_children = int(contract["candidate_registry"]["minimum_child_point_events_per_candidate"])
    eligible: list[dict[str, object]] = []
    ineligible_parent_count = 0
    candidate_keys: set[tuple[str, str]] = set()
    node_geometry: dict[str, tuple[float, float]] = {}
    node_water_body: dict[str, str] = {}
    child_linkage_payload: list[dict[str, object]] = []
    baseline_payload: list[dict[str, object]] = []

    for parent_id in sorted(parents):
        parent = parents[parent_id]
        children = child_links.get(parent_id, [])
        if len(children) < minimum_children:
            ineligible_parent_count += 1
            continue
        key = (str(parent["location_id"]), str(parent["event_date"]))
        if key in candidate_keys:
            raise ValueError(f"duplicate candidate key: {key[0]}|{key[1]}")
        candidate_keys.add(key)
        node_id = key[0]
        coord = (float(parent["longitude"]), float(parent["latitude"]))
        if node_id in node_geometry and node_geometry[node_id] != coord:
            raise ValueError(f"stable transect coordinate drift: {node_id}")
        node_geometry[node_id] = coord
        water_body = str(parent["water_body"])
        if node_id in node_water_body and node_water_body[node_id] != water_body:
            raise ValueError(f"stable transect waterBody drift: {node_id}")
        node_water_body[node_id] = water_body

        depths = sorted(depth for _, depth in children if depth is not None)
        depth_min = depths[0] if depths else None
        depth_median = float(statistics.median(depths)) if depths else None
        depth_max = depths[-1] if depths else None
        fold = deterministic_fold(node_id)
        item = {
            **parent,
            "fold": fold,
            "child_point_count": len(children),
            "depth_min_m": depth_min,
            "depth_median_m": depth_median,
            "depth_max_m": depth_max,
        }
        eligible.append(item)
        child_linkage_payload.append(
            {"parent_event_id": parent_id, "child_event_ids": sorted(child_id for child_id, _ in children)}
        )
        baseline_payload.append(
            {
                "unit_id": parent_id,
                "longitude": coord[0],
                "latitude": coord[1],
                "survey_year": int(parent["year"]),
                "day_of_year": int(parent["day_of_year"]),
                "child_point_count": len(children),
                "depth_min_m": depth_min,
                "depth_median_m": depth_median,
                "depth_max_m": depth_max,
                "water_body": water_body,
            }
        )

    node_ids = sorted(node_geometry)
    context_ids = sorted({str(item["year"]) for item in eligible}, key=int)
    if len(node_ids) < int(contract["candidate_registry"]["minimum_unique_nodes"]):
        raise ValueError(f"too few stable transect nodes: {len(node_ids)}")
    if len(eligible) < int(contract["candidate_registry"]["minimum_candidate_units"]):
        raise ValueError(f"too few eligible transect visits: {len(eligible)}")
    if len(context_ids) < int(contract["candidate_registry"]["minimum_contexts"]):
        raise ValueError(f"too few survey-year contexts: {len(context_ids)}")

    fold_map = {node_id: deterministic_fold(node_id) for node_id in node_ids}
    fold_node_counts = {str(fold): 0 for fold in range(1, 6)}
    for fold in fold_map.values():
        fold_node_counts[str(fold)] += 1
    if any(count == 0 for count in fold_node_counts.values()):
        raise ValueError(f"one or more frozen folds have no nodes: {fold_node_counts}")
    fold_candidate_counts = {str(fold): 0 for fold in range(1, 6)}
    for item in eligible:
        fold_candidate_counts[str(item["fold"])] += 1

    distances: list[float] = []
    for i, first in enumerate(node_ids):
        for second in node_ids[i + 1 :]:
            value = haversine_km(node_geometry[first], node_geometry[second])
            if value > 0.0:
                distances.append(value)
    distances.sort()
    if not distances:
        raise ValueError("no positive inter-transect distances")
    thresholds = [linear_quantile(distances, float(q)) for q in contract["world_family"]["quantiles"]]
    distinct_thresholds: list[float] = []
    for value in thresholds:
        if value > 0.0 and value not in distinct_thresholds:
            distinct_thresholds.append(value)
    if len(distinct_thresholds) < int(contract["world_family"]["minimum_distinct_positive_local_worlds"]):
        raise ValueError(f"too few distinct positive local worlds: {distinct_thresholds}")
    world_family = {
        "metric": "haversine_km",
        "local_thresholds_km": distinct_thresholds,
        "external_open": True,
        "pair_distance_count": len(distances),
    }
    split_payload = [{"node_id": node_id, "fold": fold_map[node_id]} for node_id in node_ids]
    source_payload = {
        "repository": contract["source"]["repository"],
        "commit": contract["source"]["commit"],
        "event_path": event_spec["path"],
        "event_git_blob_sha1": observed_blob,
        "event_size_bytes": len(event_bytes),
        "event_header": expected_header,
    }

    candidate_units = tuple(
        CandidateUnit(
            unit_id=str(item["event_id"]),
            node_id=str(item["location_id"]),
            context_id=str(item["year"]),
            fold=int(item["fold"]),
        )
        for item in sorted(eligible, key=lambda row: str(row["event_id"]))
    )
    semantics = ObservationSemantics(**contract["observation_semantics"])
    baseline_fields = tuple(BaselineFieldSpec(**field) for field in contract["baseline_fields"])
    problem = freeze_pre_response_problem(
        node_ids=node_ids,
        component_ids=["tampa_bay"] * len(node_ids),
        context_ids=context_ids,
        candidate_units=candidate_units,
        observation_semantics=semantics,
        baseline_fields=baseline_fields,
        split_fingerprint=canonical_sha256(split_payload),
        world_family_fingerprint=canonical_sha256(world_family),
        source_fingerprint=canonical_sha256(source_payload),
    )

    candidate_registry_payload = [
        {
            "unit_id": str(item["event_id"]),
            "node_id": str(item["location_id"]),
            "event_date": str(item["event_date"]),
            "context_id": str(item["year"]),
            "fold": int(item["fold"]),
            "child_point_count": int(item["child_point_count"]),
        }
        for item in sorted(eligible, key=lambda row: str(row["event_id"]))
    ]
    node_coordinates = [
        {
            "node_id": node_id,
            "longitude": node_geometry[node_id][0],
            "latitude": node_geometry[node_id][1],
            "water_body": node_water_body[node_id],
            "fold": fold_map[node_id],
        }
        for node_id in node_ids
    ]
    certificate = {
        "schema": "eog.tampa_seagrass_endpoint3.gate0_pre_response_certificate.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": contract["gate0_ready_status"],
        "reason": None,
        "counts_as_predictive_evidence": False,
        "safe_file_requests": state["safe_file_requests"],
        "safe_file_bytes_opened": state["safe_file_bytes_opened"],
        "occurrence_requests": 0,
        "occurrence_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "occurrence_values_opened": False,
        "emof_requests": 0,
        "emof_bytes_opened": 0,
        "emof_rows_opened": 0,
        "emof_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "event_git_blob_sha1": observed_blob,
        "event_size_bytes": len(event_bytes),
        "event_row_count": event_row_count,
        "parent_event_count": parent_row_count,
        "child_event_count": child_row_count,
        "ineligible_parent_count": ineligible_parent_count,
        "candidate_node_count": len(node_ids),
        "candidate_unit_count": len(eligible),
        "context_count": len(context_ids),
        "context_ids": context_ids,
        "fold_node_counts": fold_node_counts,
        "fold_candidate_counts": fold_candidate_counts,
        "node_coordinates": node_coordinates,
        "world_family": world_family,
        "candidate_registry_fingerprint": canonical_sha256(candidate_registry_payload),
        "child_linkage_fingerprint": canonical_sha256(child_linkage_payload),
        "baseline_registry_fingerprint": canonical_sha256(baseline_payload),
        "normalized_problem": _normalized_problem_dict(problem),
    }
    certificate["fingerprint"] = canonical_sha256(certificate)
    return certificate


def _stop_certificate(contract: dict[str, object], state: dict[str, object], reason: str) -> dict[str, object]:
    result = {
        "schema": "eog.tampa_seagrass_endpoint3.gate0_pre_response_certificate.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "status": contract["gate0_stop_status"],
        "reason": reason,
        "counts_as_predictive_evidence": False,
        "safe_file_requests": state["safe_file_requests"],
        "safe_file_bytes_opened": state["safe_file_bytes_opened"],
        "occurrence_requests": 0,
        "occurrence_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "occurrence_values_opened": False,
        "emof_requests": 0,
        "emof_bytes_opened": 0,
        "emof_rows_opened": 0,
        "emof_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "retry_or_post_stop_repair_allowed": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def execute_gate0(
    contract: dict[str, object],
    fetcher: Callable[[dict[str, object], dict[str, object]], bytes] = _default_fetcher,
) -> dict[str, object]:
    state = {
        "safe_file_requests": 0,
        "safe_file_bytes_opened": 0,
        "occurrence_requests": 0,
        "occurrence_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "occurrence_values_opened": False,
        "emof_requests": 0,
        "emof_bytes_opened": 0,
        "emof_rows_opened": 0,
        "emof_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        event_bytes = fetcher(contract["safe_files"]["event"], state)
        return build_gate0_certificate(event_bytes, contract, state)
    except Exception as exc:  # Fail closed and preserve exact response firewall counters.
        return _stop_certificate(contract, state, str(exc))


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    result = execute_gate0(contract)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "fingerprint": result["fingerprint"],
        "candidate_node_count": result.get("candidate_node_count"),
        "candidate_unit_count": result.get("candidate_unit_count"),
        "context_count": result.get("context_count"),
        "occurrence_bytes_opened": result["occurrence_bytes_opened"],
        "emof_bytes_opened": result["emof_bytes_opened"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
