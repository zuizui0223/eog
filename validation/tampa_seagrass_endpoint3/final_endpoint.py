from __future__ import annotations

import csv
import io
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Mapping
from urllib.parse import urlparse

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    DynamicTransitionOperator,
    build_dynamic_transition_operator,
)
from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.problem_contract import (
    BaselineFieldSpec,
    fit_numeric_baseline_state,
    transform_numeric_baseline_rows,
)
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)
from eog.v2.world_reconstruction import FiniteWorld
from validation.tampa_seagrass_endpoint3.gate0_pre_response import (
    build_gate0_certificate,
    canonical_sha256,
    deterministic_fold,
    git_blob_sha1,
    haversine_km,
)

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE_CONTRACT = HERE / "source_contract.json"
DEFAULT_FINAL_CONTRACT = HERE / "final_endpoint_contract.json"
DEFAULT_DECLARATION = HERE / "final_endpoint_declaration.json"
DEFAULT_OUTPUT = HERE / "final_endpoint_result.json"
EPS = 1e-6
USER_AGENT = "EOG-Tampa-Seagrass-Final/1.0"


class FinalEndpointTerminal(RuntimeError):
    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = str(status)
        self.reason = str(reason)


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def load_contracts() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return (
        _load_json(DEFAULT_SOURCE_CONTRACT),
        _load_json(DEFAULT_FINAL_CONTRACT),
        _load_json(DEFAULT_DECLARATION),
    )


def _validate_frozen_declaration(declaration: dict[str, object]) -> None:
    paired = declaration["paired_complementarity"]
    checks = (
        ("learner_fit_fingerprint", declaration["learner_payload"]),
        ("response_endpoint_fingerprint", declaration["response_endpoint_payload"]),
        ("split_fingerprint", declaration["split_payload"]),
        ("external_feature_fingerprint", declaration["external_feature_payload"]),
        ("eog_feature_fingerprint", declaration["eog_feature_payload"]),
    )
    for key, payload in checks:
        observed = canonical_sha256(payload)
        if observed != paired[key]:
            raise RuntimeError(
                f"frozen paired declaration fingerprint drift for {key}: "
                f"{observed} != {paired[key]}"
            )


def _required_text(value: object, label: str) -> str:
    text = "" if value is None else str(value)
    if not text or text != text.strip():
        raise RuntimeError(f"{label} must be non-empty and unpadded")
    return text


def _finite_float(value: object, label: str) -> float:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"{label} is not numeric") from exc
    if not np.isfinite(result):
        raise RuntimeError(f"{label} is not finite")
    return result


def _optional_float(value: object, label: str) -> float | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    return _finite_float(text, label)


def _strict_int(value: object, label: str) -> int:
    text = _required_text(value, label)
    try:
        result = int(text)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not an integer") from exc
    if str(result) != text and text != f"+{result}":
        raise RuntimeError(f"{label} is not a canonical integer")
    return result


def _parse_parent_date(row: Mapping[str, str], row_number: int) -> datetime:
    text = _required_text(row.get("eventDate"), f"eventDate row {row_number}")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise RuntimeError(
            f"parent eventDate must be YYYY-MM-DD at row {row_number}"
        ) from exc
    year = _strict_int(row.get("year"), f"year row {row_number}")
    month = _strict_int(row.get("month"), f"month row {row_number}")
    day = _strict_int(row.get("day"), f"day row {row_number}")
    if (year, month, day) != (parsed.year, parsed.month, parsed.day):
        raise RuntimeError(f"parent date fields disagree at row {row_number}")
    return parsed


def fetch_exact_raw_github(url: str, expected_size: int, label: str) -> bytes:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "raw.githubusercontent.com"
        or parsed.query
        or parsed.fragment
    ):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{label} URL is outside the frozen raw.githubusercontent.com HTTPS identity",
        )
    request = urllib.request.Request(
        url,
        headers={
            "Accept-Encoding": "identity",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        response = urllib.request.urlopen(request, timeout=120)
    except urllib.error.HTTPError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{label} full GET returned HTTP {exc.code} before body open",
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{label} transport unavailable before body open: {exc}",
        ) from exc
    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200 or response.geturl() != url:
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"{label} transport identity drift status={status}",
            )
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"{label} unexpectedly content-encoded",
            )
        body = response.read(int(expected_size) + 1)
    if len(body) != int(expected_size):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"{label} opened {len(body)} bytes, expected {expected_size}",
        )
    return body


def validate_gate0_reconstruction(
    event_bytes: bytes,
    source_contract: dict[str, object],
    final_contract: dict[str, object],
) -> dict[str, object]:
    state = {
        "safe_file_requests": 1,
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
    try:
        certificate = build_gate0_certificate(event_bytes, source_contract, state)
    except Exception as exc:
        raise RuntimeError(f"Gate0 Event reconstruction failed before response open: {exc}") from exc
    if certificate["status"] != "gate0_pre_response_ready":
        raise RuntimeError(f"Gate0 Event reconstruction no longer passes: {certificate['status']}")
    prerequisite = final_contract["prerequisites"]
    if certificate["fingerprint"] != prerequisite["gate0_result_fingerprint"]:
        raise RuntimeError("Gate0 result fingerprint drift before response open")
    if (
        certificate["normalized_problem"]["fingerprint"]
        != prerequisite["normalized_problem_fingerprint"]
    ):
        raise RuntimeError("normalized problem fingerprint drift before response open")
    frozen = final_contract["candidate_and_split"]
    checks = {
        "candidate_node_count": int(frozen["node_count"]),
        "candidate_unit_count": int(frozen["candidate_unit_count"]),
        "context_count": int(frozen["context_count"]),
        "candidate_registry_fingerprint": frozen["candidate_registry_fingerprint"],
        "child_linkage_fingerprint": frozen["child_linkage_fingerprint"],
        "baseline_registry_fingerprint": frozen["baseline_registry_fingerprint"],
    }
    for key, expected in checks.items():
        if certificate[key] != expected:
            raise RuntimeError(
                f"Gate0 freeze drift for {key}: {certificate[key]!r} != {expected!r}"
            )
    if certificate["normalized_problem"]["source_fingerprint"] != frozen["source_fingerprint"]:
        raise RuntimeError("source fingerprint drift before response open")
    if (
        certificate["normalized_problem"]["split_fingerprint"]
        != frozen["fold_assignment_fingerprint"]
    ):
        raise RuntimeError("split fingerprint drift before response open")
    if (
        certificate["normalized_problem"]["world_family_fingerprint"]
        != final_contract["worlds"]["world_family_fingerprint"]
    ):
        raise RuntimeError("world-family fingerprint drift before response open")
    return certificate


def parse_event_structure(
    event_bytes: bytes,
    source_contract: dict[str, object],
    final_contract: dict[str, object],
) -> dict[str, object]:
    event_entry = final_contract["source"]["safe_event"]
    if len(event_bytes) != int(event_entry["size_bytes"]):
        raise RuntimeError("Event size drift before response open")
    if git_blob_sha1(event_bytes) != event_entry["git_blob_sha1"]:
        raise RuntimeError("Event Git blob drift before response open")
    if event_bytes.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("Event unexpectedly begins with UTF-8 BOM")
    try:
        text = event_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Event is not strict UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_header = list(source_contract["event_header"])
    if reader.fieldnames != expected_header:
        raise RuntimeError("Event header drift before response open")

    event_ids: set[str] = set()
    parents: dict[str, dict[str, object]] = {}
    child_links: dict[str, list[tuple[str, float | None]]] = {}
    for row_number, row in enumerate(reader, start=2):
        event_id = _required_text(row.get("eventID"), f"eventID row {row_number}")
        if event_id in event_ids:
            raise RuntimeError(f"duplicate Event eventID at row {row_number}")
        event_ids.add(event_id)
        event_type = _required_text(row.get("eventType"), f"eventType row {row_number}")
        if event_type not in {"Transect", "Point"}:
            raise RuntimeError(f"unsupported Event eventType at row {row_number}: {event_type}")
        if _required_text(row.get("geodeticDatum"), f"geodeticDatum row {row_number}") != "EPSG:4326":
            raise RuntimeError(f"Event datum drift at row {row_number}")
        lon = _finite_float(row.get("decimalLongitude"), f"longitude row {row_number}")
        lat = _finite_float(row.get("decimalLatitude"), f"latitude row {row_number}")
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise RuntimeError(f"Event coordinate out of range at row {row_number}")
        if event_type == "Transect":
            if str(row.get("parentEventID") or "").strip():
                raise RuntimeError(f"parent Transect has parentEventID at row {row_number}")
            parsed = _parse_parent_date(row, row_number)
            location_id = _required_text(row.get("locationID"), f"locationID row {row_number}")
            water_body = _required_text(row.get("waterBody"), f"waterBody row {row_number}")
            parents[event_id] = {
                "unit_id": event_id,
                "node_id": location_id,
                "event_date": parsed.strftime("%Y-%m-%d"),
                "context_id": str(parsed.year),
                "survey_year": parsed.year,
                "day_of_year": parsed.timetuple().tm_yday,
                "longitude": lon,
                "latitude": lat,
                "water_body": water_body,
            }
        else:
            parent_id = _required_text(row.get("parentEventID"), f"child parentEventID row {row_number}")
            depth = _optional_float(
                row.get("minimumDepthInMeters"), f"minimumDepthInMeters row {row_number}"
            )
            child_links.setdefault(parent_id, []).append((event_id, depth))

    unknown_parent = sorted(set(child_links).difference(parents))
    if unknown_parent:
        raise RuntimeError(f"child Event links to unknown parent: {unknown_parent[0]}")
    minimum_children = int(source_contract["candidate_registry"]["minimum_child_point_events_per_candidate"])
    candidate_rows: list[dict[str, object]] = []
    candidate_registry_payload: list[dict[str, object]] = []
    child_linkage_payload: list[dict[str, object]] = []
    baseline_payload: list[dict[str, object]] = []
    child_to_parent: dict[str, str] = {}
    node_coords: dict[str, tuple[float, float]] = {}
    node_water: dict[str, str] = {}
    candidate_keys: set[tuple[str, str]] = set()
    ineligible = 0
    for parent_id in sorted(parents):
        parent = parents[parent_id]
        children = child_links.get(parent_id, [])
        if len(children) < minimum_children:
            ineligible += 1
            continue
        key = (str(parent["node_id"]), str(parent["event_date"]))
        if key in candidate_keys:
            raise RuntimeError(f"duplicate frozen candidate key: {key}")
        candidate_keys.add(key)
        node_id = str(parent["node_id"])
        coord = (float(parent["longitude"]), float(parent["latitude"]))
        if node_id in node_coords and node_coords[node_id] != coord:
            raise RuntimeError(f"stable Event coordinate drift: {node_id}")
        node_coords[node_id] = coord
        water_body = str(parent["water_body"])
        if node_id in node_water and node_water[node_id] != water_body:
            raise RuntimeError(f"stable Event waterBody drift: {node_id}")
        node_water[node_id] = water_body
        depths = sorted(depth for _, depth in children if depth is not None)
        row = {
            **parent,
            "fold": deterministic_fold(node_id),
            "child_point_count": len(children),
            "depth_min_m": depths[0] if depths else None,
            "depth_median_m": float(np.median(np.asarray(depths, dtype=float))) if depths else None,
            "depth_max_m": depths[-1] if depths else None,
        }
        candidate_rows.append(row)
        for child_id, _ in children:
            if child_id in child_to_parent:
                raise RuntimeError(f"child event belongs to multiple candidates: {child_id}")
            child_to_parent[child_id] = parent_id
        child_ids = sorted(child_id for child_id, _ in children)
        child_linkage_payload.append(
            {"parent_event_id": parent_id, "child_event_ids": child_ids}
        )
        candidate_registry_payload.append(
            {
                "unit_id": parent_id,
                "node_id": node_id,
                "event_date": str(parent["event_date"]),
                "context_id": str(parent["context_id"]),
                "fold": int(row["fold"]),
                "child_point_count": int(row["child_point_count"]),
            }
        )
        baseline_payload.append(
            {
                "unit_id": parent_id,
                "longitude": coord[0],
                "latitude": coord[1],
                "survey_year": int(parent["survey_year"]),
                "day_of_year": int(parent["day_of_year"]),
                "child_point_count": len(children),
                "depth_min_m": row["depth_min_m"],
                "depth_median_m": row["depth_median_m"],
                "depth_max_m": row["depth_max_m"],
                "water_body": water_body,
            }
        )
    candidate_rows.sort(key=lambda row: str(row["unit_id"]))
    frozen = final_contract["candidate_and_split"]
    if ineligible != 0:
        raise RuntimeError(f"Event eligibility drift: {ineligible} parent rows now ineligible")
    if len(candidate_rows) != int(frozen["candidate_unit_count"]):
        raise RuntimeError("candidate-unit count drift before response open")
    if len(node_coords) != int(frozen["node_count"]):
        raise RuntimeError("candidate-node count drift before response open")
    if canonical_sha256(candidate_registry_payload) != frozen["candidate_registry_fingerprint"]:
        raise RuntimeError("candidate registry fingerprint drift before response open")
    if canonical_sha256(child_linkage_payload) != frozen["child_linkage_fingerprint"]:
        raise RuntimeError("child linkage fingerprint drift before response open")
    if canonical_sha256(baseline_payload) != frozen["baseline_registry_fingerprint"]:
        raise RuntimeError("baseline registry fingerprint drift before response open")
    fold_node_counts = {str(i): 0 for i in range(1, 6)}
    for node_id in sorted(node_coords):
        fold_node_counts[str(deterministic_fold(node_id))] += 1
    if fold_node_counts != frozen["fold_node_counts"]:
        raise RuntimeError("fold-node count drift before response open")
    fold_candidate_counts = {str(i): 0 for i in range(1, 6)}
    for row in candidate_rows:
        fold_candidate_counts[str(row["fold"])] += 1
    if fold_candidate_counts != frozen["fold_candidate_counts"]:
        raise RuntimeError("fold-candidate count drift before response open")
    return {
        "candidate_rows": candidate_rows,
        "child_to_parent": child_to_parent,
        "node_ids": tuple(sorted(node_coords)),
        "node_coords": node_coords,
        "node_water": node_water,
        "event_id_count": len(event_ids),
        "child_event_count": len(child_to_parent),
    }


def parse_occurrence_response(
    response_bytes: bytes,
    event_state: dict[str, object],
    final_contract: dict[str, object],
) -> tuple[dict[str, int], dict[str, object]]:
    source = final_contract["source"]["occurrence_response"]
    parser = final_contract["response_parser"]
    if len(response_bytes) != int(source["size_bytes"]):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"occurrence byte size drift: {len(response_bytes)}",
        )
    if git_blob_sha1(response_bytes) != source["git_blob_sha1"]:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity", "occurrence Git blob SHA-1 drift"
        )
    if response_bytes.startswith(b"\xef\xbb\xbf"):
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage",
            "occurrence unexpectedly begins with UTF-8 BOM",
        )
    try:
        text = response_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", "occurrence table is not UTF-8"
        ) from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", "occurrence table is empty"
        ) from exc
    expected = [str(value) for value in parser["header_exact_order"]]
    if header != expected:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", f"occurrence header drift: {header!r}"
        )
    col = {name: index for index, name in enumerate(expected)}
    child_to_parent = event_state["child_to_parent"]
    labels = {str(row["unit_id"]): 0 for row in event_state["candidate_rows"]}
    occurrence_ids: set[str] = set()
    represented_children: set[str] = set()
    represented_candidates: set[str] = set()
    focal_parent_ids: set[str] = set()
    focal = str(parser["focal_scientific_name"])
    physical_rows = 0
    focal_rows = 0
    status_counts = {"present": 0, "absent": 0}
    for physical_row, row in enumerate(reader, start=2):
        physical_rows += 1
        if len(row) != len(expected):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"occurrence row {physical_row} has {len(row)} cells, require {len(expected)}",
            )
        occurrence_id = row[col["occurrenceID"]]
        if (
            not occurrence_id
            or occurrence_id != occurrence_id.strip()
            or occurrence_id in occurrence_ids
        ):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"invalid/duplicate occurrenceID at physical row {physical_row}",
            )
        occurrence_ids.add(occurrence_id)
        event_id = row[col["eventID"]]
        if (
            not event_id
            or event_id != event_id.strip()
            or event_id not in child_to_parent
        ):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"unknown/invalid child eventID at physical row {physical_row}",
            )
        parent_id = str(child_to_parent[event_id])
        represented_children.add(event_id)
        represented_candidates.add(parent_id)
        if row[col["basisOfRecord"]] != parser["basis_of_record_exact"]:
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"basisOfRecord drift at physical row {physical_row}",
            )
        status = row[col["occurrenceStatus"]]
        if status not in set(parser["occurrence_status_allowed"]):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"unexpected occurrenceStatus at physical row {physical_row}: {status!r}",
            )
        status_counts[status] += 1
        scientific_name = row[col["scientificName"]]
        if scientific_name == focal:
            focal_rows += 1
            if status != "present":
                raise FinalEndpointTerminal(
                    "stop_full_response_schema_or_linkage",
                    f"exact focal row is not present at physical row {physical_row}",
                )
            labels[parent_id] = 1
            focal_parent_ids.add(parent_id)
    if physical_rows <= 0:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", "occurrence table contains no data rows"
        )
    candidate_by_unit = {
        str(row["unit_id"]): row for row in event_state["candidate_rows"]
    }
    positive_units = sorted(unit_id for unit_id, value in labels.items() if value == 1)
    positive_nodes = sorted({str(candidate_by_unit[unit_id]["node_id"]) for unit_id in positive_units})
    audit: dict[str, object] = {
        "physical_occurrence_rows": physical_rows,
        "unique_occurrence_ids": len(occurrence_ids),
        "represented_child_event_count": len(represented_children),
        "represented_candidate_count": len(represented_candidates),
        "status_counts": status_counts,
        "focal_scientific_name": focal,
        "focal_rows": focal_rows,
        "positive_candidate_count": len(positive_units),
        "negative_candidate_count": len(labels) - len(positive_units),
        "ever_positive_node_count": len(positive_nodes),
        "positive_candidate_ids": positive_units,
        "ever_positive_node_ids": positive_nodes,
        "occurrence_git_blob_sha1": git_blob_sha1(response_bytes),
        "occurrence_size_bytes": len(response_bytes),
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return labels, audit


def build_frozen_operators(
    node_ids: tuple[str, ...],
    node_coords: Mapping[str, tuple[float, float]],
    final_contract: dict[str, object],
) -> tuple[dict[str, DynamicTransitionOperator], dict[str, object]]:
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    pair_distances: list[float] = []
    for i, left in enumerate(node_ids):
        for right in node_ids[i + 1 :]:
            distance = haversine_km(node_coords[left], node_coords[right])
            if not np.isfinite(distance) or distance <= 0:
                raise RuntimeError(f"nonpositive/failing node distance {left}/{right}")
            pair_distances.append(float(distance))
    world_payload = {
        "metric": "haversine_km",
        "local_thresholds_km": [
            float(world["threshold_km"]) for world in final_contract["worlds"]["local_worlds"]
        ],
        "external_open": True,
        "pair_distance_count": len(pair_distances),
    }
    if canonical_sha256(world_payload) != final_contract["worlds"]["world_family_fingerprint"]:
        raise RuntimeError("frozen world-family reconstruction drift before response open")

    operators: dict[str, DynamicTransitionOperator] = {}
    graph_audit: list[dict[str, object]] = []
    for world in final_contract["worlds"]["local_worlds"]:
        threshold = float(world["threshold_km"])
        directed: list[DynamicReachabilityEdge] = []
        edges: list[list[str]] = []
        for i, left in enumerate(node_ids):
            for right in node_ids[i + 1 :]:
                distance = haversine_km(node_coords[left], node_coords[right])
                if distance <= threshold:
                    a, b = index[left], index[right]
                    directed.append(DynamicReachabilityEdge(a, b, geographic_support=1.0))
                    directed.append(DynamicReachabilityEdge(b, a, geographic_support=1.0))
                    edges.append([left, right])
        if not edges:
            raise RuntimeError(f"frozen local world has no edges: {world['world_id']}")
        operators[str(world["world_id"])] = build_dynamic_transition_operator(
            node_ids, directed, loss_support=1.0
        )
        graph_audit.append(
            {
                "world_id": str(world["world_id"]),
                "threshold_km": threshold,
                "edge_count": len(edges),
                "graph_fingerprint": canonical_sha256({"nodes": list(node_ids), "edges": edges}),
            }
        )
    directed_external: list[DynamicReachabilityEdge] = []
    external_edges: list[list[str]] = []
    for i, left in enumerate(node_ids):
        for right in node_ids[i + 1 :]:
            a, b = index[left], index[right]
            directed_external.append(DynamicReachabilityEdge(a, b, geographic_support=1.0))
            directed_external.append(DynamicReachabilityEdge(b, a, geographic_support=1.0))
            external_edges.append([left, right])
    operators["external_open"] = build_dynamic_transition_operator(
        node_ids, directed_external, loss_support=1.0
    )
    graph_audit.append(
        {
            "world_id": "external_open",
            "edge_count": len(external_edges),
            "graph_fingerprint": canonical_sha256({"nodes": list(node_ids), "edges": external_edges}),
        }
    )
    if len(operators) != int(final_contract["worlds"]["world_count"]):
        raise RuntimeError("world/operator count drift")
    audit: dict[str, object] = {
        "pair_distance_count": len(pair_distances),
        "graphs": graph_audit,
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return operators, audit


def precompute_cumulative_hitting(
    operator: DynamicTransitionOperator, *, max_steps: int
) -> np.ndarray:
    n = len(operator.node_ids)
    current = np.eye(n, dtype=float)
    history = np.empty((max_steps + 1, n, n), dtype=float)
    history[0] = current
    transition = np.asarray(operator.transition, dtype=float)
    for step in range(1, max_steps + 1):
        current = transition @ current
        np.fill_diagonal(current, 1.0)
        if (
            not np.isfinite(current).all()
            or np.any(current < -1e-14)
            or np.any(current > 1.0 + 1e-10)
        ):
            raise RuntimeError("first-passage recurrence left finite [0,1] support bounds")
        history[step] = current
    return history


def _ordered_occurrences(
    node_ids: tuple[str, ...], occurrence_ids: Iterable[str]
) -> tuple[str, ...]:
    wanted = {str(value) for value in occurrence_ids}
    if not wanted.issubset(set(node_ids)):
        raise RuntimeError("occurrence set leaves frozen node universe")
    return tuple(node_id for node_id in node_ids if node_id in wanted)


def training_occurrence_set(
    full_positive_nodes: Iterable[str], training_node_id: str, node_ids: tuple[str, ...]
) -> tuple[str, ...]:
    positives = {str(value) for value in full_positive_nodes}
    positives.discard(str(training_node_id))
    return tuple(node_id for node_id in node_ids if node_id in positives)


def layer_b_for_occurrences(
    occurrence_ids: Iterable[str],
    *,
    node_ids: tuple[str, ...],
    operators: Mapping[str, DynamicTransitionOperator],
    hitting_history: Mapping[str, np.ndarray],
    final_contract: dict[str, object],
) -> tuple[np.ndarray, dict[str, object]]:
    ordered = _ordered_occurrences(node_ids, occurrence_ids)
    if len(ordered) < int(final_contract["layer_a"]["minimum_occurrence_nodes_for_any_reconstruction"]):
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "Layer-A reconstruction requires at least two ever-positive calibration nodes",
        )
    source = min(ordered)
    targets = tuple(node_id for node_id in ordered if node_id != source)
    if len(targets) < int(final_contract["layer_a"]["minimum_non_source_occurrence_targets"]):
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "Layer-A reconstruction has no non-source compatibility target",
        )
    source_index = node_ids.index(source)
    target_index = np.asarray([node_ids.index(node_id) for node_id in targets], dtype=int)
    tolerance = float(final_contract["worlds"]["support_tolerance"])
    compatible: list[str] = []
    compatibility_support: dict[str, list[float]] = {}
    declared: list[FiniteWorld] = []
    for world_id, operator in operators.items():
        world = FiniteWorld(world_id=world_id, operator=operator, source_ids=(source,))
        declared.append(world)
        final_support = hitting_history[world_id][-1, source_index, :]
        target_support = final_support[target_index]
        compatibility_support[world_id] = [float(value) for value in target_support]
        if bool(np.all(target_support > tolerance)):
            compatible.append(world_id)
    if not compatible:
        raise FinalEndpointTerminal(
            "universe_falsified_stop",
            "no frozen local/external world remains compatible with cross-fit ever-positive node set",
        )
    gate = ForecastGateDeclaration(reachability_threshold=0.0)
    members = []
    for world_id in compatible:
        cumulative = hitting_history[world_id][:, source_index, :].copy()
        cumulative[:, source_index] = 1.0
        members.append(
            SimpleNamespace(
                cumulative_reachability=cumulative,
                supported_state=cumulative > tolerance,
            )
        )
    forecast_fp = canonical_sha256(
        {
            "occurrence_ids": list(ordered),
            "source_id": source,
            "compatible_world_ids": compatible,
            "world_fingerprints": [[world.world_id, world.fingerprint] for world in declared],
            "max_steps": int(final_contract["worlds"]["max_steps"]),
            "gate_fingerprint": gate.fingerprint,
        }
    )
    forecast = SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=int(final_contract["worlds"]["max_steps"]),
        gate_declaration=gate,
        world_fingerprints=tuple((world.world_id, world.fingerprint) for world in declared),
        fingerprint=forecast_fp,
    )
    summary = summarize_worldset_for_prediction(
        forecast, step=int(final_contract["layer_b"]["forecast_step"])
    )
    if tuple(summary.feature_names) != tuple(PREDICTIVE_FEATURE_NAMES):
        raise RuntimeError("Layer-B feature names drifted")
    matrix = np.asarray(summary.feature_matrix, dtype=float)
    if matrix.shape != (len(node_ids), 10) or not np.isfinite(matrix).all():
        raise RuntimeError("Layer-B matrix shape/finite check failed")
    audit: dict[str, object] = {
        "occurrence_node_count": len(ordered),
        "source_id": source,
        "compatibility_target_ids": list(targets),
        "compatible_world_ids": compatible,
        "declared_world_count": len(declared),
        "feature_fingerprint": summary.feature_fingerprint,
        "forecast_fingerprint": forecast_fp,
        "compatibility_support": compatibility_support,
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return matrix, audit


def _categorical_value_required(value: object, field: str) -> str:
    if value is None or not str(value).strip():
        raise RuntimeError(f"required categorical baseline field missing: {field}")
    return str(value).strip()


def encode_baseline_fold(
    train_rows: list[dict[str, object]],
    heldout_rows: list[dict[str, object]],
    final_contract: dict[str, object],
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    numeric_specs = tuple(
        BaselineFieldSpec(
            name=str(spec["name"]),
            kind="numeric",
            missing_policy=str(spec["missing_policy"]),
        )
        for spec in final_contract["baseline"]["numeric_fields"]
    )
    state = fit_numeric_baseline_state(train_rows, numeric_specs)
    train_numeric = np.asarray(transform_numeric_baseline_rows(train_rows, state), dtype=float)
    heldout_numeric = np.asarray(transform_numeric_baseline_rows(heldout_rows, state), dtype=float)
    train_parts = [train_numeric]
    heldout_parts = [heldout_numeric]
    feature_names = list(state.feature_names)
    levels_audit: dict[str, list[str]] = {}
    for field in [str(v) for v in final_contract["baseline"]["categorical_fields"]]:
        train_values = [_categorical_value_required(row.get(field), field) for row in train_rows]
        heldout_values = [_categorical_value_required(row.get(field), field) for row in heldout_rows]
        levels = sorted(set(train_values))
        if not levels:
            raise RuntimeError(f"no calibration categories for {field}")
        levels_audit[field] = levels
        train_block = np.zeros((len(train_rows), len(levels) + 1), dtype=float)
        heldout_block = np.zeros((len(heldout_rows), len(levels) + 1), dtype=float)
        level_index = {level: index for index, level in enumerate(levels)}
        for row_index, value in enumerate(train_values):
            train_block[row_index, level_index[value]] = 1.0
        for row_index, value in enumerate(heldout_values):
            if value in level_index:
                heldout_block[row_index, level_index[value]] = 1.0
            else:
                heldout_block[row_index, -1] = 1.0
        train_parts.append(train_block)
        heldout_parts.append(heldout_block)
        feature_names.extend([f"{field}=={level}" for level in levels])
        feature_names.append(f"{field}__UNSEEN")
    x_train = np.column_stack(train_parts)
    x_heldout = np.column_stack(heldout_parts)
    if not np.isfinite(x_train).all() or not np.isfinite(x_heldout).all():
        raise RuntimeError("baseline preprocessing produced non-finite values")
    audit: dict[str, object] = {
        "numeric_state_fingerprint": state.fingerprint,
        "categorical_levels": levels_audit,
        "feature_names": feature_names,
        "feature_count": len(feature_names),
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return x_train, x_heldout, audit


def _rf(final_contract: dict[str, object]) -> RandomForestClassifier:
    learner = final_contract["learner"]
    return RandomForestClassifier(
        n_estimators=int(learner["n_estimators"]),
        max_features=str(learner["max_features"]),
        min_samples_leaf=int(learner["min_samples_leaf"]),
        class_weight=None,
        random_state=int(learner["random_state"]),
        n_jobs=int(learner["n_jobs"]),
    )


def _positive_probability(model: RandomForestClassifier, features: np.ndarray) -> np.ndarray:
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(f"RandomForest class order drift: {list(model.classes_)!r}")
    return np.clip(model.predict_proba(features)[:, 1].astype(float), EPS, 1.0 - EPS)


def permute_layer_b_partition(
    train: np.ndarray, heldout: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    if train.shape[1] != 10 or heldout.shape[1] != 10:
        raise RuntimeError("placebo requires exactly ten Layer-B columns")
    rng = np.random.default_rng(int(seed))
    train_out = np.empty_like(train)
    heldout_out = np.empty_like(heldout)
    for column in range(10):
        train_out[:, column] = train[rng.permutation(train.shape[0]), column]
        heldout_out[:, column] = heldout[rng.permutation(heldout.shape[0]), column]
    return train_out, heldout_out


def _class_counts(values: np.ndarray) -> tuple[int, int]:
    values = np.asarray(values, dtype=int)
    return int(np.sum(values == 1)), int(np.sum(values == 0))


def prepare_pre_response(
    source_contract: dict[str, object],
    final_contract: dict[str, object],
    declaration: dict[str, object],
) -> tuple[dict[str, object], int]:
    _validate_frozen_declaration(declaration)
    event_entry = final_contract["source"]["safe_event"]
    event_bytes = fetch_exact_raw_github(
        str(event_entry["raw_url"]), int(event_entry["size_bytes"]), "safe Event"
    )
    validate_gate0_reconstruction(event_bytes, source_contract, final_contract)
    event_state = parse_event_structure(event_bytes, source_contract, final_contract)
    node_ids = event_state["node_ids"]
    operators, graph_audit = build_frozen_operators(
        node_ids, event_state["node_coords"], final_contract
    )
    max_steps = int(final_contract["worlds"]["max_steps"])
    hitting_history = {
        world_id: precompute_cumulative_hitting(operator, max_steps=max_steps)
        for world_id, operator in operators.items()
    }
    baseline_folds: dict[int, dict[str, object]] = {}
    candidate_rows = event_state["candidate_rows"]
    for fold in [int(v) for v in final_contract["candidate_and_split"]["fold_ids"]]:
        train_rows = [row for row in candidate_rows if int(row["fold"]) != fold]
        heldout_rows = [row for row in candidate_rows if int(row["fold"]) == fold]
        x_train, x_heldout, audit = encode_baseline_fold(train_rows, heldout_rows, final_contract)
        baseline_folds[fold] = {
            "train_rows": train_rows,
            "heldout_rows": heldout_rows,
            "x_train": x_train,
            "x_heldout": x_heldout,
            "audit": audit,
        }
    return {
        "event_state": event_state,
        "operators": operators,
        "hitting_history": hitting_history,
        "world_graph_audit": graph_audit,
        "baseline_folds": baseline_folds,
    }, len(event_bytes)


def evaluate_final_endpoint(
    prepared: dict[str, object],
    occurrence_bytes: bytes,
    final_contract: dict[str, object],
    declaration: dict[str, object],
) -> dict[str, object]:
    event_state = prepared["event_state"]
    candidate_rows = event_state["candidate_rows"]
    labels_by_unit, response_audit = parse_occurrence_response(
        occurrence_bytes, event_state, final_contract
    )
    y_all = np.asarray([labels_by_unit[str(row["unit_id"])] for row in candidate_rows], dtype=int)
    total_positive, total_negative = _class_counts(y_all)
    positive_nodes_all = {
        str(row["node_id"])
        for row in candidate_rows
        if labels_by_unit[str(row["unit_id"])] == 1
    }
    estimability = final_contract["estimability"]
    if (
        total_positive < int(estimability["minimum_total_positive_candidate_units"])
        or total_negative < int(estimability["minimum_total_negative_candidate_units"])
        or len(positive_nodes_all) < int(estimability["minimum_total_ever_positive_nodes"])
    ):
        raise FinalEndpointTerminal(
            "non_estimable_response_balance",
            f"total response balance candidates={total_positive}/{total_negative}, ever-positive-nodes={len(positive_nodes_all)} fails frozen minima",
        )

    node_ids = event_state["node_ids"]
    layer_b_cache: dict[tuple[str, ...], tuple[np.ndarray, dict[str, object]]] = {}

    def layer_b_cached(occurrence_ids: tuple[str, ...]) -> tuple[np.ndarray, dict[str, object]]:
        if occurrence_ids not in layer_b_cache:
            layer_b_cache[occurrence_ids] = layer_b_for_occurrences(
                occurrence_ids,
                node_ids=node_ids,
                operators=prepared["operators"],
                hitting_history=prepared["hitting_history"],
                final_contract=final_contract,
            )
        return layer_b_cache[occurrence_ids]

    fold_prepared: list[dict[str, object]] = []
    heldout_folds_with_both = 0
    for fold in [int(v) for v in final_contract["candidate_and_split"]["fold_ids"]]:
        baseline_fold = prepared["baseline_folds"][fold]
        train_rows = baseline_fold["train_rows"]
        heldout_rows = baseline_fold["heldout_rows"]
        train_y = np.asarray([labels_by_unit[str(row["unit_id"])] for row in train_rows], dtype=int)
        heldout_y = np.asarray([labels_by_unit[str(row["unit_id"])] for row in heldout_rows], dtype=int)
        train_positive, train_negative = _class_counts(train_y)
        heldout_positive, heldout_negative = _class_counts(heldout_y)
        if (
            train_positive < int(estimability["minimum_calibration_positive_candidate_units_each_fold"])
            or train_negative < int(estimability["minimum_calibration_negative_candidate_units_each_fold"])
        ):
            raise FinalEndpointTerminal(
                "non_estimable_response_balance",
                f"fold {fold} calibration candidate balance {train_positive}/{train_negative} fails frozen minima",
            )
        positive_nodes = tuple(
            node_id
            for node_id in node_ids
            if any(
                str(row["node_id"]) == node_id
                and labels_by_unit[str(row["unit_id"])] == 1
                for row in train_rows
            )
        )
        if len(positive_nodes) < int(estimability["minimum_calibration_ever_positive_nodes_each_fold"]):
            raise FinalEndpointTerminal(
                "non_estimable_response_balance",
                f"fold {fold} has only {len(positive_nodes)} calibration ever-positive nodes",
            )
        if heldout_positive > 0 and heldout_negative > 0:
            heldout_folds_with_both += 1
        full_matrix, heldout_layer_audit = layer_b_cached(positive_nodes)
        train_node_vectors: dict[str, np.ndarray] = {}
        crossfit_audits: dict[str, str] = {}
        for node_id in sorted({str(row["node_id"]) for row in train_rows}):
            occurrence_set = training_occurrence_set(positive_nodes, node_id, node_ids)
            matrix, audit = layer_b_cached(occurrence_set)
            train_node_vectors[node_id] = matrix[node_ids.index(node_id)]
            crossfit_audits[node_id] = str(audit["fingerprint"])
        x_train_layer_b = np.vstack(
            [train_node_vectors[str(row["node_id"])] for row in train_rows]
        )
        x_heldout_layer_b = np.vstack(
            [full_matrix[node_ids.index(str(row["node_id"]))] for row in heldout_rows]
        )
        fold_prepared.append(
            {
                "fold": fold,
                "train_rows": train_rows,
                "heldout_rows": heldout_rows,
                "train_y": train_y,
                "heldout_y": heldout_y,
                "train_positive": train_positive,
                "train_negative": train_negative,
                "heldout_positive": heldout_positive,
                "heldout_negative": heldout_negative,
                "calibration_ever_positive_nodes": len(positive_nodes),
                "x_train_layer_b": x_train_layer_b,
                "x_heldout_layer_b": x_heldout_layer_b,
                "heldout_layer_audit": heldout_layer_audit,
                "crossfit_audit_fingerprint": canonical_sha256(crossfit_audits),
                "x_train_base": baseline_fold["x_train"],
                "x_heldout_base": baseline_fold["x_heldout"],
                "baseline_audit": baseline_fold["audit"],
            }
        )
    if heldout_folds_with_both < int(estimability["minimum_heldout_folds_with_both_classes"]):
        raise FinalEndpointTerminal(
            "non_estimable_response_balance",
            f"only {heldout_folds_with_both}/5 heldout folds contain both classes",
        )

    paired_scores: list[PairedOuterUnitScore] = []
    fold_results: list[dict[str, object]] = []
    placebo_fold_losses: dict[int, list[float]] = {
        int(seed): [] for seed in final_contract["placebo"]["replicate_seeds"]
    }
    primary_model_fits = 0
    placebo_model_fits = 0
    for prepared_fold in fold_prepared:
        x_train_base = np.asarray(prepared_fold["x_train_base"], dtype=float)
        x_heldout_base = np.asarray(prepared_fold["x_heldout_base"], dtype=float)
        x_train_layer_b = np.asarray(prepared_fold["x_train_layer_b"], dtype=float)
        x_heldout_layer_b = np.asarray(prepared_fold["x_heldout_layer_b"], dtype=float)
        x_train_augmented = np.column_stack([x_train_base, x_train_layer_b])
        x_heldout_augmented = np.column_stack([x_heldout_base, x_heldout_layer_b])
        baseline_model = _rf(final_contract)
        augmented_model = _rf(final_contract)
        baseline_model.fit(x_train_base, prepared_fold["train_y"])
        augmented_model.fit(x_train_augmented, prepared_fold["train_y"])
        primary_model_fits += 2
        baseline_loss = float(
            log_loss(
                prepared_fold["heldout_y"],
                _positive_probability(baseline_model, x_heldout_base),
                labels=[0, 1],
            )
        )
        augmented_loss = float(
            log_loss(
                prepared_fold["heldout_y"],
                _positive_probability(augmented_model, x_heldout_augmented),
                labels=[0, 1],
            )
        )
        paired_scores.append(
            PairedOuterUnitScore(
                outer_unit_id=f"fold_{prepared_fold['fold']}",
                baseline_score=baseline_loss,
                augmented_score=augmented_loss,
            )
        )
        for seed in final_contract["placebo"]["replicate_seeds"]:
            train_permuted, heldout_permuted = permute_layer_b_partition(
                x_train_layer_b, x_heldout_layer_b, int(seed)
            )
            placebo_model = _rf(final_contract)
            placebo_model.fit(
                np.column_stack([x_train_base, train_permuted]), prepared_fold["train_y"]
            )
            placebo_model_fits += 1
            placebo_loss = float(
                log_loss(
                    prepared_fold["heldout_y"],
                    _positive_probability(
                        placebo_model,
                        np.column_stack([x_heldout_base, heldout_permuted]),
                    ),
                    labels=[0, 1],
                )
            )
            placebo_fold_losses[int(seed)].append(placebo_loss)
        fold_row: dict[str, object] = {
            "fold": prepared_fold["fold"],
            "calibration_candidate_count": len(prepared_fold["train_rows"]),
            "heldout_candidate_count": len(prepared_fold["heldout_rows"]),
            "calibration_positive": prepared_fold["train_positive"],
            "calibration_negative": prepared_fold["train_negative"],
            "heldout_positive": prepared_fold["heldout_positive"],
            "heldout_negative": prepared_fold["heldout_negative"],
            "calibration_ever_positive_nodes": prepared_fold["calibration_ever_positive_nodes"],
            "baseline_log_loss": baseline_loss,
            "augmented_log_loss": augmented_loss,
            "augmented_minus_baseline": augmented_loss - baseline_loss,
            "baseline_preprocessing": prepared_fold["baseline_audit"],
            "heldout_layer_a": prepared_fold["heldout_layer_audit"],
            "crossfit_audit_fingerprint": prepared_fold["crossfit_audit_fingerprint"],
        }
        fold_row["fingerprint"] = canonical_sha256(fold_row)
        fold_results.append(fold_row)

    if primary_model_fits != 10 or placebo_model_fits != 100:
        raise RuntimeError(
            f"model-fit count drift primary={primary_model_fits}, placebo={placebo_model_fits}"
        )
    paired_contract = declaration["paired_complementarity"]
    paired_declaration = PredictiveComplementarityDeclaration(
        metric_name=str(paired_contract["metric_name"]),
        lower_is_better=bool(paired_contract["lower_is_better"]),
        expected_outer_unit_count=int(paired_contract["expected_outer_unit_count"]),
        favorable_min_augmented_wins=int(paired_contract["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(paired_contract["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=str(paired_contract["learner_fit_fingerprint"]),
        response_endpoint_fingerprint=str(paired_contract["response_endpoint_fingerprint"]),
        split_fingerprint=str(paired_contract["split_fingerprint"]),
        external_feature_fingerprint=str(paired_contract["external_feature_fingerprint"]),
        eog_feature_fingerprint=str(paired_contract["eog_feature_fingerprint"]),
    )
    paired_result = evaluate_predictive_complementarity(
        paired_declaration,
        paired_scores,
        tie_tolerance=float(paired_contract["tie_tolerance"]),
    )
    placebo_macro = {
        seed: float(np.mean(losses)) for seed, losses in placebo_fold_losses.items()
    }
    ordered_placebo = np.asarray(
        [placebo_macro[int(seed)] for seed in final_contract["placebo"]["replicate_seeds"]],
        dtype=float,
    )
    placebo_summary: dict[str, object] = {
        "macro_log_loss_by_seed": {
            str(seed): placebo_macro[int(seed)]
            for seed in final_contract["placebo"]["replicate_seeds"]
        },
        "median_macro_log_loss": float(np.median(ordered_placebo)),
        "q25_macro_log_loss": float(np.quantile(ordered_placebo, 0.25, method="linear")),
        "q75_macro_log_loss": float(np.quantile(ordered_placebo, 0.75, method="linear")),
        "real_augmented_minus_placebo_median": float(
            paired_result.augmented_macro_score - np.median(ordered_placebo)
        ),
        "fraction_placebo_replicates_beaten_by_real_augmented": float(
            np.mean(paired_result.augmented_macro_score < ordered_placebo)
        ),
        "secondary_only": True,
        "changes_primary_status": False,
    }
    placebo_summary["fingerprint"] = canonical_sha256(placebo_summary)
    result: dict[str, object] = {
        "schema": "eog.tampa_seagrass_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "predictive_result",
        "status": paired_result.status,
        "response_endpoint": declaration["response_endpoint_payload"]["unit"],
        "focal_taxon": final_contract["response_parser"]["focal_scientific_name"],
        "candidate_unit_count": len(candidate_rows),
        "node_count": len(event_state["node_ids"]),
        "total_positive_candidate_units": total_positive,
        "total_negative_candidate_units": total_negative,
        "total_ever_positive_nodes": len(positive_nodes_all),
        "heldout_folds_with_both_classes": heldout_folds_with_both,
        "primary_model_fits": primary_model_fits,
        "placebo_model_fits": placebo_model_fits,
        "model_fits_total": primary_model_fits + placebo_model_fits,
        "heldout_scores": 10,
        "baseline_macro_log_loss": paired_result.baseline_macro_score,
        "augmented_macro_log_loss": paired_result.augmented_macro_score,
        "augmented_minus_baseline": paired_result.augmented_minus_baseline,
        "augmented_better_folds": paired_result.augmented_better_outer_units,
        "baseline_better_folds": paired_result.baseline_better_outer_units,
        "tied_folds": paired_result.tied_outer_units,
        "paired_result_fingerprint": paired_result.fingerprint,
        "fold_results": fold_results,
        "response_audit": response_audit,
        "world_graph_audit": prepared["world_graph_audit"],
        "layer_b_cache_entry_count": len(layer_b_cache),
        "placebo": placebo_summary,
        "emof_full_gets": 0,
        "emof_full_bytes_opened": 0,
        "counts_as_predictive_evidence": True,
        "candidate_hunting_hard_stop": True,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_result(
    final_contract: dict[str, object],
    terminal: FinalEndpointTerminal,
    *,
    safe_bytes_opened: int,
    occurrence_bytes_opened: int,
    occurrence_full_gets: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.tampa_seagrass_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "protocol_or_estimability_stop",
        "status": terminal.status,
        "reason": terminal.reason,
        "safe_event_bytes_opened": int(safe_bytes_opened),
        "occurrence_bytes_opened": int(occurrence_bytes_opened),
        "occurrence_full_gets": int(occurrence_full_gets),
        "emof_full_gets": 0,
        "emof_full_bytes_opened": 0,
        "counts_as_predictive_evidence": False,
        "candidate_hunting_hard_stop": False,
        "retry_after_occurrence_consumption_allowed": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run_live(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    source_contract, final_contract, declaration = load_contracts()
    safe_bytes_opened = 0
    occurrence_bytes_opened = 0
    occurrence_full_gets = 0
    try:
        prepared, safe_bytes_opened = prepare_pre_response(
            source_contract, final_contract, declaration
        )
        response_entry = final_contract["source"]["occurrence_response"]
        occurrence_full_gets = 1
        occurrence_bytes = fetch_exact_raw_github(
            str(response_entry["raw_url"]),
            int(response_entry["size_bytes"]),
            "occurrence response",
        )
        occurrence_bytes_opened = len(occurrence_bytes)
        result = evaluate_final_endpoint(
            prepared, occurrence_bytes, final_contract, declaration
        )
        result["safe_event_bytes_opened"] = safe_bytes_opened
        result["occurrence_bytes_opened"] = occurrence_bytes_opened
        result["occurrence_full_gets"] = occurrence_full_gets
        result["emof_full_gets"] = 0
        result["emof_full_bytes_opened"] = 0
        result["fingerprint"] = canonical_sha256(
            {key: value for key, value in result.items() if key != "fingerprint"}
        )
    except FinalEndpointTerminal as terminal:
        result = terminal_result(
            final_contract,
            terminal,
            safe_bytes_opened=safe_bytes_opened,
            occurrence_bytes_opened=occurrence_bytes_opened,
            occurrence_full_gets=occurrence_full_gets,
        )
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    run_live()
