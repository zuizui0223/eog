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
from validation.leipzig_roedeer_endpoint3.gate0_pre_response import (
    Gate0Stop,
    canonical_sha256,
    fetch_exact_raw_github,
    freeze_from_safe_bytes,
    git_blob_sha1,
    haversine_km,
)

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE_CONTRACT = HERE / "source_contract.json"
DEFAULT_FINAL_CONTRACT = HERE / "final_endpoint_contract.json"
DEFAULT_DECLARATION = HERE / "final_endpoint_declaration.json"
DEFAULT_OUTPUT = HERE / "final_endpoint_result.json"
EPS = 1e-6
USER_AGENT = "EOG-Leipzig-RoeDeer-Final/1.0"


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


def _parse_aware_datetime(value: str, label: str) -> datetime:
    if not isinstance(value, str) or not value or value != value.strip():
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", f"{label} is empty or padded"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", f"{label} is not ISO-8601"
        ) from exc
    if parsed.utcoffset() is None:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", f"{label} lacks timezone offset"
        )
    return parsed


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


def _csv_rows(raw: bytes, label: str) -> tuple[list[str], list[list[str]]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"safe {label} is not UTF-8") from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise RuntimeError(f"safe {label} is empty") from exc
    if not header or len(set(header)) != len(header):
        raise RuntimeError(f"safe {label} has invalid header")
    rows = list(reader)
    if any(len(row) != len(header) for row in rows):
        raise RuntimeError(f"safe {label} has malformed row width")
    return header, rows


def parse_deployment_linkage(
    deployments_raw: bytes, source_contract: dict[str, object]
) -> dict[str, dict[str, object]]:
    entry = source_contract["source"]["safe_files"]["deployments"]
    if (
        len(deployments_raw) != int(entry["size_bytes"])
        or git_blob_sha1(deployments_raw) != entry["git_blob_sha1"]
    ):
        raise RuntimeError("safe deployment blob drift before response open")
    header, rows = _csv_rows(deployments_raw, "deployments")
    required = [
        "deploymentID",
        "locationID",
        "locationName",
        "latitude",
        "longitude",
        "deploymentStart",
        "deploymentEnd",
    ]
    if any(name not in header for name in required):
        raise RuntimeError("safe deployment schema drift before response open")
    idx = {name: header.index(name) for name in required}
    mapping: dict[str, dict[str, object]] = {}
    for physical_row, row in enumerate(rows, start=2):
        deployment_id = row[idx["deploymentID"]]
        location_id = row[idx["locationID"]]
        location_name = row[idx["locationName"]]
        if (
            not deployment_id
            or deployment_id != deployment_id.strip()
            or deployment_id in mapping
        ):
            raise RuntimeError(f"safe deploymentID drift at row {physical_row}")
        if (
            not location_id
            or location_id != location_id.strip()
            or not location_name
            or location_name != location_name.strip()
        ):
            raise RuntimeError(f"safe location identity drift at row {physical_row}")
        try:
            start = datetime.fromisoformat(
                row[idx["deploymentStart"]].replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                row[idx["deploymentEnd"]].replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise RuntimeError(
                f"safe deployment timestamp drift at row {physical_row}"
            ) from exc
        if start.utcoffset() is None or end.utcoffset() is None or end <= start:
            raise RuntimeError(f"safe deployment interval drift at row {physical_row}")
        mapping[deployment_id] = {
            "location_id": location_id,
            "location_name": location_name,
            "start": start,
            "end": end,
        }
    if len(mapping) != 75:
        raise RuntimeError(f"safe deployment registry count drift: {len(mapping)} != 75")
    return mapping


def validate_pre_response(
    deployments_raw: bytes,
    covariates_raw: bytes,
    source_code_raw: bytes,
    source_contract: dict[str, object],
    final_contract: dict[str, object],
) -> dict[str, object]:
    try:
        frozen = freeze_from_safe_bytes(
            deployments_raw, covariates_raw, source_code_raw, source_contract
        )
    except Gate0Stop as exc:
        raise RuntimeError(
            f"Gate0 reconstruction drift before response open: {exc}"
        ) from exc
    node_and_split = final_contract["node_and_split"]
    checks = {
        "candidate_node_count": int(node_and_split["valid_node_count"]),
        "node_registry_fingerprint": node_and_split["node_registry_fingerprint"],
        "source_fingerprint": node_and_split["source_fingerprint"],
        "baseline_fingerprint": node_and_split["gate0_baseline_fingerprint"],
        "split_fingerprint": node_and_split["fold_assignment_fingerprint"],
    }
    for key, expected in checks.items():
        if frozen[key] != expected:
            raise RuntimeError(
                f"pre-response freeze drift for {key}: "
                f"{frozen[key]!r} != {expected!r}"
            )
    if (
        frozen["normalized_problem"]["fingerprint"]
        != final_contract["prerequisites"]["normalized_problem_fingerprint"]
    ):
        raise RuntimeError("normalized problem fingerprint drift")
    if (
        frozen["world_family"]["fingerprint"]
        != final_contract["worlds"]["world_family_fingerprint"]
    ):
        raise RuntimeError("world-family fingerprint drift")
    return frozen


def parse_response_table(
    response_bytes: bytes,
    deployment_linkage: Mapping[str, dict[str, object]],
    retained_node_ids: tuple[str, ...],
    final_contract: dict[str, object],
) -> tuple[dict[str, int], dict[str, object]]:
    source = final_contract["source"]["response_table"]
    parser = final_contract["response_parser"]
    if len(response_bytes) != int(source["size_bytes"]):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"response byte size drift: {len(response_bytes)}",
        )
    if git_blob_sha1(response_bytes) != source["git_blob_sha1"]:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity", "response Git blob SHA-1 drift"
        )
    if response_bytes.startswith(b"\xef\xbb\xbf"):
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage",
            "response unexpectedly begins with UTF-8 BOM",
        )
    try:
        text = response_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", "response table is not UTF-8"
        ) from exc
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage", "response table is empty"
        ) from exc
    expected = [str(value) for value in parser["header_exact_order"]]
    if header != expected:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage",
            f"response header drift: {header!r}",
        )
    col = {name: index for index, name in enumerate(expected)}
    valid = set(retained_node_ids)
    labels = {node_id: 0 for node_id in retained_node_ids}
    focal = str(parser["focal_scientific_name"])
    physical_rows = 0
    focal_rows = 0
    focal_rows_retained = 0
    focal_rows_excluded = 0
    focal_event_start_year_counts: dict[int, int] = {}
    represented_deployments: set[str] = set()
    represented_retained_locations: set[str] = set()
    for physical_row, row in enumerate(reader, start=2):
        physical_rows += 1
        if len(row) != len(expected):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"physical row {physical_row} has {len(row)} cells",
            )
        deployment_id = row[col["deploymentID"]]
        if (
            not deployment_id
            or deployment_id != deployment_id.strip()
            or deployment_id not in deployment_linkage
        ):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"unknown/invalid deploymentID at physical row {physical_row}",
            )
        represented_deployments.add(deployment_id)
        deployment = deployment_linkage[deployment_id]
        location_id = str(deployment["location_id"])
        if location_id in valid:
            represented_retained_locations.add(location_id)
        if row[col["scientificName"]] != focal:
            continue
        focal_rows += 1
        event_start = _parse_aware_datetime(
            row[col["eventStart"]], f"eventStart row {physical_row}"
        )
        event_end = _parse_aware_datetime(
            row[col["eventEnd"]], f"eventEnd row {physical_row}"
        )
        if event_end < event_start:
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"eventEnd precedes eventStart at row {physical_row}",
            )
        if not (deployment["start"] <= event_start < deployment["end"]):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_linkage",
                f"focal eventStart lies outside raw deployment interval at row {physical_row}",
            )
        focal_event_start_year_counts[event_start.year] = (
            focal_event_start_year_counts.get(event_start.year, 0) + 1
        )
        if location_id in valid:
            labels[location_id] = 1
            focal_rows_retained += 1
        else:
            focal_rows_excluded += 1
    if physical_rows <= 0:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_linkage",
            "response table contains no data rows",
        )
    positive_ids = [node_id for node_id in retained_node_ids if labels[node_id] == 1]
    audit: dict[str, object] = {
        "physical_response_rows": physical_rows,
        "represented_deployment_count": len(represented_deployments),
        "represented_retained_location_count": len(represented_retained_locations),
        "focal_scientific_name": focal,
        "focal_rows": focal_rows,
        "focal_rows_at_retained_locations": focal_rows_retained,
        "focal_rows_at_excluded_locations": focal_rows_excluded,
        "positive_node_count": len(positive_ids),
        "negative_node_count": len(retained_node_ids) - len(positive_ids),
        "positive_node_ids": positive_ids,
        "focal_event_start_year_counts": {
            str(year): focal_event_start_year_counts[year]
            for year in sorted(focal_event_start_year_counts)
        },
        "response_git_blob_sha1": git_blob_sha1(response_bytes),
        "response_size_bytes": len(response_bytes),
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return labels, audit


def build_frozen_operators(
    node_ids: tuple[str, ...],
    baseline_by_id: Mapping[str, dict[str, object]],
    final_contract: dict[str, object],
) -> dict[str, DynamicTransitionOperator]:
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    operators: dict[str, DynamicTransitionOperator] = {}
    for world in final_contract["worlds"]["local_worlds"]:
        threshold = float(world["threshold_km"])
        directed: list[DynamicReachabilityEdge] = []
        edges: list[list[str]] = []
        for i, left in enumerate(node_ids):
            for right in node_ids[i + 1 :]:
                left_row = baseline_by_id[left]
                right_row = baseline_by_id[right]
                distance = haversine_km(
                    float(left_row["longitude"]),
                    float(left_row["latitude"]),
                    float(right_row["longitude"]),
                    float(right_row["latitude"]),
                )
                if distance <= threshold:
                    a, b = index[left], index[right]
                    directed.append(
                        DynamicReachabilityEdge(a, b, geographic_support=1.0)
                    )
                    directed.append(
                        DynamicReachabilityEdge(b, a, geographic_support=1.0)
                    )
                    edges.append([left, right])
        graph_fp = canonical_sha256({"nodes": list(node_ids), "edges": sorted(edges)})
        if (
            len(edges) != int(world["edge_count"])
            or graph_fp != world["graph_fingerprint"]
        ):
            raise RuntimeError(f"operator graph drift for {world['world_id']}")
        operators[str(world["world_id"])] = build_dynamic_transition_operator(
            node_ids, directed, loss_support=1.0
        )
    external = final_contract["worlds"]["external_open"]
    directed_external: list[DynamicReachabilityEdge] = []
    edges_external: list[list[str]] = []
    for i, left in enumerate(node_ids):
        for right in node_ids[i + 1 :]:
            a, b = index[left], index[right]
            directed_external.append(
                DynamicReachabilityEdge(a, b, geographic_support=1.0)
            )
            directed_external.append(
                DynamicReachabilityEdge(b, a, geographic_support=1.0)
            )
            edges_external.append([left, right])
    if (
        len(edges_external) != int(external["edge_count"])
        or canonical_sha256({"nodes": list(node_ids), "edges": edges_external})
        != external["graph_fingerprint"]
    ):
        raise RuntimeError("external_open graph drift")
    operators["external_open"] = build_dynamic_transition_operator(
        node_ids, directed_external, loss_support=1.0
    )
    if len(operators) != int(final_contract["worlds"]["world_count"]):
        raise RuntimeError("world/operator count drift")
    return operators


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
            raise RuntimeError(
                "first-passage recurrence left finite [0,1] support bounds"
            )
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
    full_positive: Iterable[str], training_node_id: str, node_ids: tuple[str, ...]
) -> tuple[str, ...]:
    positives = {str(value) for value in full_positive}
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
    if len(ordered) < int(
        final_contract["layer_a"]["minimum_occurrences_for_any_reconstruction"]
    ):
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "Layer-A reconstruction requires at least two positive occurrence nodes",
        )
    source = min(ordered)
    targets = tuple(node_id for node_id in ordered if node_id != source)
    if len(targets) < int(
        final_contract["layer_a"]["minimum_non_source_occurrence_targets"]
    ):
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "Layer-A reconstruction has no non-source compatibility target",
        )
    source_index = node_ids.index(source)
    target_index = np.asarray(
        [node_ids.index(node_id) for node_id in targets], dtype=int
    )
    tolerance = float(final_contract["worlds"]["support_tolerance"])
    compatible: list[str] = []
    compatibility_support: dict[str, list[float]] = {}
    declared: list[FiniteWorld] = []
    for world_id, operator in operators.items():
        world = FiniteWorld(
            world_id=world_id, operator=operator, source_ids=(source,)
        )
        declared.append(world)
        final_support = hitting_history[world_id][-1, source_index, :]
        target_support = final_support[target_index]
        compatibility_support[world_id] = [float(value) for value in target_support]
        if bool(np.all(target_support > tolerance)):
            compatible.append(world_id)
    if not compatible:
        raise FinalEndpointTerminal(
            "universe_falsified_stop",
            "no frozen local/external world remains compatible with cross-fit occurrence set",
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
            "world_fingerprints": [
                [world.world_id, world.fingerprint] for world in declared
            ],
            "max_steps": int(final_contract["worlds"]["max_steps"]),
            "gate_fingerprint": gate.fingerprint,
        }
    )
    forecast = SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=int(final_contract["worlds"]["max_steps"]),
        gate_declaration=gate,
        world_fingerprints=tuple(
            (world.world_id, world.fingerprint) for world in declared
        ),
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
        "occurrence_count": len(ordered),
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


def _class_counts(values: np.ndarray) -> tuple[int, int]:
    values = np.asarray(values, dtype=int)
    return int(np.sum(values == 1)), int(np.sum(values == 0))


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


def _positive_probability(
    model: RandomForestClassifier, features: np.ndarray
) -> np.ndarray:
    if list(model.classes_) != [0, 1]:
        raise RuntimeError(
            f"RandomForest class order drift: {list(model.classes_)!r}"
        )
    return np.clip(
        model.predict_proba(features)[:, 1].astype(float), EPS, 1.0 - EPS
    )


def _categorical_value(value: object, missing_token: str) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return missing_token
    return str(value)


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
    train_numeric = np.asarray(
        transform_numeric_baseline_rows(train_rows, state), dtype=float
    )
    heldout_numeric = np.asarray(
        transform_numeric_baseline_rows(heldout_rows, state), dtype=float
    )
    missing = str(final_contract["baseline"]["categorical_missing_token"])
    categorical_fields = [
        str(value) for value in final_contract["baseline"]["categorical_fields"]
    ]
    train_parts = [train_numeric]
    heldout_parts = [heldout_numeric]
    feature_names = list(state.feature_names)
    levels_audit: dict[str, list[str]] = {}
    for field in categorical_fields:
        train_values = [
            _categorical_value(row.get(field), missing) for row in train_rows
        ]
        heldout_values = [
            _categorical_value(row.get(field), missing) for row in heldout_rows
        ]
        levels = sorted(set(train_values))
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


def permute_layer_b_partition(
    train: np.ndarray, heldout: np.ndarray, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    if train.shape[1] != 10 or heldout.shape[1] != 10:
        raise RuntimeError("placebo requires exactly ten Layer-B columns")
    rng = np.random.default_rng(int(seed))
    train_out = np.empty_like(train)
    heldout_out = np.empty_like(heldout)
    for column in range(10):
        train_out[:, column] = train[
            rng.permutation(train.shape[0]), column
        ]
        heldout_out[:, column] = heldout[
            rng.permutation(heldout.shape[0]), column
        ]
    return train_out, heldout_out


def evaluate_final_endpoint(
    prepared: dict[str, object],
    response_bytes: bytes,
    source_contract: dict[str, object],
    final_contract: dict[str, object],
    declaration: dict[str, object],
) -> dict[str, object]:
    frozen = prepared["frozen"]
    node_ids = tuple(
        str(value) for value in frozen["normalized_problem"]["node_ids"]
    )
    fold_map = {
        str(unit["node_id"]): int(unit["fold"])
        for unit in frozen["normalized_problem"]["candidate_units"]
    }
    baseline_by_id = {
        str(row["node_id"]): row for row in frozen["baseline_rows"]
    }
    labels_by_id, response_audit = parse_response_table(
        response_bytes,
        prepared["deployment_linkage"],
        node_ids,
        final_contract,
    )
    y_all = np.asarray([labels_by_id[node_id] for node_id in node_ids], dtype=int)
    total_positive, total_negative = _class_counts(y_all)
    estimability = final_contract["estimability"]
    if (
        total_positive < int(estimability["minimum_total_positive_nodes"])
        or total_negative < int(estimability["minimum_total_negative_nodes"])
    ):
        raise FinalEndpointTerminal(
            "non_estimable_response_balance",
            f"total response balance {total_positive}/{total_negative} fails frozen minima",
        )

    layer_b_cache: dict[
        tuple[str, ...], tuple[np.ndarray, dict[str, object]]
    ] = {}

    def layer_b_cached(
        occurrence_ids: tuple[str, ...]
    ) -> tuple[np.ndarray, dict[str, object]]:
        if occurrence_ids not in layer_b_cache:
            layer_b_cache[occurrence_ids] = layer_b_for_occurrences(
                occurrence_ids,
                node_ids=node_ids,
                operators=prepared["operators"],
                hitting_history=prepared["hitting_history"],
                final_contract=final_contract,
            )
        return layer_b_cache[occurrence_ids]

    # Construct and validate all real Layer-B rows before fitting any model.
    fold_prepared: list[dict[str, object]] = []
    heldout_folds_with_both = 0
    for fold in [
        int(value) for value in final_contract["node_and_split"]["fold_ids"]
    ]:
        train_ids = tuple(
            node_id for node_id in node_ids if fold_map[node_id] != fold
        )
        heldout_ids = tuple(
            node_id for node_id in node_ids if fold_map[node_id] == fold
        )
        train_y = np.asarray(
            [labels_by_id[node_id] for node_id in train_ids], dtype=int
        )
        heldout_y = np.asarray(
            [labels_by_id[node_id] for node_id in heldout_ids], dtype=int
        )
        train_positive, train_negative = _class_counts(train_y)
        heldout_positive, heldout_negative = _class_counts(heldout_y)
        if (
            train_positive
            < int(estimability["minimum_calibration_positive_nodes_each_fold"])
            or train_negative
            < int(estimability["minimum_calibration_negative_nodes_each_fold"])
        ):
            raise FinalEndpointTerminal(
                "non_estimable_response_balance",
                f"fold {fold} calibration balance "
                f"{train_positive}/{train_negative} fails frozen minima",
            )
        if heldout_positive > 0 and heldout_negative > 0:
            heldout_folds_with_both += 1
        full_positive = tuple(
            node_id for node_id in train_ids if labels_by_id[node_id] == 1
        )
        full_matrix, heldout_layer_audit = layer_b_cached(full_positive)
        train_layer_b_rows: list[np.ndarray] = []
        crossfit_audits: dict[str, str] = {}
        for node_id in train_ids:
            occurrence_set = training_occurrence_set(
                full_positive, node_id, node_ids
            )
            matrix, audit = layer_b_cached(occurrence_set)
            train_layer_b_rows.append(matrix[node_ids.index(node_id)])
            crossfit_audits[node_id] = str(audit["fingerprint"])
        fold_prepared.append(
            {
                "fold": fold,
                "train_ids": train_ids,
                "heldout_ids": heldout_ids,
                "train_y": train_y,
                "heldout_y": heldout_y,
                "train_positive": train_positive,
                "train_negative": train_negative,
                "heldout_positive": heldout_positive,
                "heldout_negative": heldout_negative,
                "x_train_layer_b": np.vstack(train_layer_b_rows),
                "x_heldout_layer_b": np.vstack(
                    [full_matrix[node_ids.index(node_id)] for node_id in heldout_ids]
                ),
                "heldout_layer_audit": heldout_layer_audit,
                "crossfit_audit_fingerprint": canonical_sha256(crossfit_audits),
            }
        )
    if heldout_folds_with_both < int(
        estimability["minimum_heldout_folds_with_both_classes"]
    ):
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
        train_rows = [
            baseline_by_id[node_id] for node_id in prepared_fold["train_ids"]
        ]
        heldout_rows = [
            baseline_by_id[node_id] for node_id in prepared_fold["heldout_ids"]
        ]
        x_train_base, x_heldout_base, baseline_audit = encode_baseline_fold(
            train_rows, heldout_rows, final_contract
        )
        x_train_layer_b = prepared_fold["x_train_layer_b"]
        x_heldout_layer_b = prepared_fold["x_heldout_layer_b"]
        x_train_augmented = np.column_stack(
            [x_train_base, x_train_layer_b]
        )
        x_heldout_augmented = np.column_stack(
            [x_heldout_base, x_heldout_layer_b]
        )
        baseline_model = _rf(final_contract)
        augmented_model = _rf(final_contract)
        baseline_model.fit(x_train_base, prepared_fold["train_y"])
        augmented_model.fit(
            x_train_augmented, prepared_fold["train_y"]
        )
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
                np.column_stack([x_train_base, train_permuted]),
                prepared_fold["train_y"],
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
            "calibration_node_count": len(prepared_fold["train_ids"]),
            "heldout_node_count": len(prepared_fold["heldout_ids"]),
            "calibration_positive": prepared_fold["train_positive"],
            "calibration_negative": prepared_fold["train_negative"],
            "heldout_positive": prepared_fold["heldout_positive"],
            "heldout_negative": prepared_fold["heldout_negative"],
            "baseline_log_loss": baseline_loss,
            "augmented_log_loss": augmented_loss,
            "augmented_minus_baseline": augmented_loss - baseline_loss,
            "baseline_preprocessing": baseline_audit,
            "heldout_layer_a": prepared_fold["heldout_layer_audit"],
            "crossfit_audit_fingerprint": prepared_fold[
                "crossfit_audit_fingerprint"
            ],
        }
        fold_row["fingerprint"] = canonical_sha256(fold_row)
        fold_results.append(fold_row)

    if primary_model_fits != 10 or placebo_model_fits != 100:
        raise RuntimeError(
            f"model-fit count drift primary={primary_model_fits}, "
            f"placebo={placebo_model_fits}"
        )
    paired_contract = declaration["paired_complementarity"]
    paired_declaration = PredictiveComplementarityDeclaration(
        metric_name=str(paired_contract["metric_name"]),
        lower_is_better=bool(paired_contract["lower_is_better"]),
        expected_outer_unit_count=int(
            paired_contract["expected_outer_unit_count"]
        ),
        favorable_min_augmented_wins=int(
            paired_contract["favorable_min_augmented_wins"]
        ),
        adverse_min_baseline_wins=int(
            paired_contract["adverse_min_baseline_wins"]
        ),
        learner_fit_fingerprint=str(
            paired_contract["learner_fit_fingerprint"]
        ),
        response_endpoint_fingerprint=str(
            paired_contract["response_endpoint_fingerprint"]
        ),
        split_fingerprint=str(paired_contract["split_fingerprint"]),
        external_feature_fingerprint=str(
            paired_contract["external_feature_fingerprint"]
        ),
        eog_feature_fingerprint=str(
            paired_contract["eog_feature_fingerprint"]
        ),
    )
    paired_result = evaluate_predictive_complementarity(
        paired_declaration,
        paired_scores,
        tie_tolerance=float(paired_contract["tie_tolerance"]),
    )
    placebo_macro = {
        seed: float(np.mean(losses))
        for seed, losses in placebo_fold_losses.items()
    }
    ordered_placebo = np.asarray(
        [
            placebo_macro[int(seed)]
            for seed in final_contract["placebo"]["replicate_seeds"]
        ],
        dtype=float,
    )
    placebo_summary: dict[str, object] = {
        "macro_log_loss_by_seed": {
            str(seed): placebo_macro[int(seed)]
            for seed in final_contract["placebo"]["replicate_seeds"]
        },
        "median_macro_log_loss": float(np.median(ordered_placebo)),
        "q25_macro_log_loss": float(
            np.quantile(ordered_placebo, 0.25, method="linear")
        ),
        "q75_macro_log_loss": float(
            np.quantile(ordered_placebo, 0.75, method="linear")
        ),
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
        "schema": "eog.leipzig_roedeer_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "predictive_result",
        "status": paired_result.status,
        "response_endpoint": declaration["response_endpoint_payload"]["unit"],
        "focal_taxon": "Capreolus capreolus",
        "total_positive_nodes": total_positive,
        "total_negative_nodes": total_negative,
        "heldout_folds_with_both_classes": heldout_folds_with_both,
        "primary_model_fits": primary_model_fits,
        "placebo_model_fits": placebo_model_fits,
        "model_fits_total": primary_model_fits + placebo_model_fits,
        "heldout_scores": len(paired_scores),
        "baseline_macro_log_loss": paired_result.baseline_macro_score,
        "augmented_macro_log_loss": paired_result.augmented_macro_score,
        "augmented_minus_baseline": paired_result.augmented_minus_baseline,
        "augmented_heldout_wins": paired_result.augmented_better_outer_units,
        "baseline_heldout_wins": paired_result.baseline_better_outer_units,
        "tied_heldout_units": paired_result.tied_outer_units,
        "paired_declaration_fingerprint": paired_result.declaration_fingerprint,
        "paired_score_fingerprint": paired_result.paired_score_fingerprint,
        "fold_results": fold_results,
        "placebo": placebo_summary,
        "response_audit": response_audit,
        "gate0_result_fingerprint": final_contract["prerequisites"][
            "gate0_result_fingerprint"
        ],
        "response_header_result_fingerprint": final_contract["prerequisites"][
            "response_header_result_fingerprint"
        ],
        "unique_layer_b_crossfit_reconstructions": len(layer_b_cache),
        "layer_b_representation": "symmetric_world_support_summary_v1",
        "counts_as_predictive_evidence": True,
        "candidate_hunting_hard_stop": True,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def fetch_full_response_once(url: str, expected_size: int) -> bytes:
    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "raw.githubusercontent.com"
        or parsed.query
        or parsed.fragment
    ):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            "frozen full-response URL left authorized raw GitHub identity",
        )
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"}
    )
    try:
        response = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"full response GET returned HTTP {exc.code} before body open",
        ) from exc
    except (OSError, urllib.error.URLError) as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"full response transport unavailable before body open: {exc}",
        ) from exc
    with response:
        status = int(getattr(response, "status", response.getcode()))
        if status != 200 or response.geturl() != url:
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                f"full response transport identity drift status={status}",
            )
        if response.headers.get("Content-Encoding", "identity").casefold() != "identity":
            raise FinalEndpointTerminal(
                "stop_full_response_transport_or_integrity",
                "full response unexpectedly content-encoded",
            )
        body = response.read(expected_size + 1)
    if len(body) != expected_size:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"full response opened {len(body)} bytes, expected {expected_size}",
        )
    return body


def prepare_pre_response(
    source_contract: dict[str, object],
    final_contract: dict[str, object],
    declaration: dict[str, object],
) -> tuple[dict[str, object], int]:
    _validate_frozen_declaration(declaration)
    opened: dict[str, bytes] = {}
    safe_total = 0
    for role in ("deployments", "covariates", "source_code"):
        entry = final_contract["source"]["safe_files"][role]
        raw = fetch_exact_raw_github(
            str(entry["raw_url"]), int(entry["size_bytes"])
        )
        opened[role] = raw
        safe_total += len(raw)
    frozen = validate_pre_response(
        opened["deployments"],
        opened["covariates"],
        opened["source_code"],
        source_contract,
        final_contract,
    )
    linkage = parse_deployment_linkage(
        opened["deployments"], source_contract
    )
    node_ids = tuple(
        str(value) for value in frozen["normalized_problem"]["node_ids"]
    )
    baseline_by_id = {
        str(row["node_id"]): row for row in frozen["baseline_rows"]
    }
    operators = build_frozen_operators(
        node_ids, baseline_by_id, final_contract
    )
    max_steps = int(final_contract["worlds"]["max_steps"])
    hitting_history = {
        world_id: precompute_cumulative_hitting(operator, max_steps=max_steps)
        for world_id, operator in operators.items()
    }
    return {
        "frozen": frozen,
        "deployment_linkage": linkage,
        "operators": operators,
        "hitting_history": hitting_history,
    }, safe_total


def terminal_result(
    final_contract: dict[str, object],
    terminal: FinalEndpointTerminal,
    *,
    safe_bytes_opened: int,
    response_bytes_opened: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.leipzig_roedeer_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "protocol_or_estimability_stop",
        "status": terminal.status,
        "reason": terminal.reason,
        "safe_bytes_opened": int(safe_bytes_opened),
        "response_bytes_opened": int(response_bytes_opened),
        "counts_as_predictive_evidence": False,
        "candidate_hunting_hard_stop": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def run_live(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    source_contract, final_contract, declaration = load_contracts()
    safe_bytes_opened = 0
    response_bytes_opened = 0
    try:
        prepared, safe_bytes_opened = prepare_pre_response(
            source_contract, final_contract, declaration
        )
        response_entry = final_contract["source"]["response_table"]
        response_bytes = fetch_full_response_once(
            str(response_entry["raw_url"]), int(response_entry["size_bytes"])
        )
        response_bytes_opened = len(response_bytes)
        result = evaluate_final_endpoint(
            prepared,
            response_bytes,
            source_contract,
            final_contract,
            declaration,
        )
        result["safe_bytes_opened"] = safe_bytes_opened
        result["response_bytes_opened"] = response_bytes_opened
        result["full_response_gets"] = 1
        result["fingerprint"] = canonical_sha256(
            {key: value for key, value in result.items() if key != "fingerprint"}
        )
    except FinalEndpointTerminal as terminal:
        result = terminal_result(
            final_contract,
            terminal,
            safe_bytes_opened=safe_bytes_opened,
            response_bytes_opened=response_bytes_opened,
        )
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    run_live()
