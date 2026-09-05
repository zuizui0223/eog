from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, Mapping

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
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import (
    PREDICTIVE_FEATURE_NAMES,
    summarize_worldset_for_prediction,
)
from eog.v2.world_reconstruction import FiniteWorld

from validation.hokkaido_streamfish_endpoint3.pre_response_geometry import (
    canonical_sha256,
    derive_baseline_features,
    derive_worlds,
    git_blob_sha1,
    haversine_km,
    parse_coordinate_registry,
)


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE_CONTRACT = HERE / "source_contract.json"
DEFAULT_FINAL_CONTRACT = HERE / "final_endpoint_contract.json"
DEFAULT_DECLARATION = HERE / "final_endpoint_declaration.json"
EPS = 1e-6


class FinalEndpointTerminal(RuntimeError):
    """Accepted terminal endpoint state, including non-estimable protocol outcomes."""

    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = str(status)
        self.reason = str(reason)


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} must contain a JSON object")
    return value


def load_contracts(
    source_path: Path = DEFAULT_SOURCE_CONTRACT,
    final_path: Path = DEFAULT_FINAL_CONTRACT,
    declaration_path: Path = DEFAULT_DECLARATION,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    return _load_json(source_path), _load_json(final_path), _load_json(declaration_path)


def _canonical_positive_int(value: str, label: str) -> int:
    if not isinstance(value, str) or value != value.strip() or not value.isdigit():
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"{label} is not a canonical positive base-10 integer: {value!r}",
        )
    number = int(value)
    if number <= 0 or str(number) != value:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"{label} is not a canonical positive base-10 integer: {value!r}",
        )
    return number


def _canonical_year(value: str, year_min: int, year_max: int) -> int:
    if not isinstance(value, str) or value != value.strip() or not value.isdigit():
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"year is not a canonical base-10 integer: {value!r}",
        )
    year = int(value)
    if str(year) != value or not year_min <= year <= year_max:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"year {value!r} lies outside frozen {year_min}-{year_max}",
        )
    return year


def _abundance_value(value: str, missing_tokens: set[str]) -> tuple[float, bool]:
    if value in missing_tokens:
        return 0.0, True
    if value != value.strip():
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"abundance has surrounding whitespace: {value!r}",
        )
    try:
        number = float(value)
    except ValueError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"invalid abundance token: {value!r}",
        ) from exc
    if not math.isfinite(number) or number < 0.0:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"abundance must be finite and non-negative: {value!r}",
        )
    return number, False


def parse_response_table(
    response_bytes: bytes,
    nodes: list[dict[str, object]],
    missing_coordinate_site_ids: Iterable[str],
    source_contract: dict[str, object],
    final_contract: dict[str, object],
) -> tuple[dict[str, int], dict[str, object]]:
    """Parse the frozen full response table and reduce it to site-level ever-detection."""

    source = final_contract["source"]["response_table"]
    parser = final_contract["response_parser"]
    if len(response_bytes) != int(source["size_bytes"]):
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            f"response byte size drift: {len(response_bytes)} != {source['size_bytes']}",
        )
    if git_blob_sha1(response_bytes) != source["git_blob_sha1"]:
        raise FinalEndpointTerminal(
            "stop_full_response_transport_or_integrity",
            "response Git blob SHA-1 drift",
        )
    try:
        text = response_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            "response table is not UTF-8",
        ) from exc

    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_header = [str(value) for value in parser["header_exact_order"]]
    if reader.fieldnames != expected_header:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"response physical header drift: {reader.fieldnames!r} != {expected_header!r}",
        )

    valid_ids = {str(row["site_id"]) for row in nodes}
    missing_ids = {str(value) for value in missing_coordinate_site_ids}
    all_registry_ids = valid_ids | missing_ids
    labels = {site_id: 0 for site_id in valid_ids}
    represented_valid: set[str] = set()
    physical_rows = 0
    focal_rows = 0
    focal_rows_valid_nodes = 0
    focal_positive_rows = 0
    missing_abundance_rows = 0
    year_counts: dict[int, int] = {}
    missing_tokens = {str(value) for value in parser["abundance_missing_tokens"]}
    focal_latin = str(parser["focal_physical_latin"])
    year_min = int(parser["year_min"])
    year_max = int(parser["year_max"])

    for physical_row, row in enumerate(reader, start=2):
        physical_rows += 1
        if None in row or any(value is None for value in row.values()):
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_coverage",
                f"malformed CSV field count at physical row {physical_row}",
            )
        year = _canonical_year(str(row["year"]), year_min, year_max)
        river = str(row["river"])
        if not river or river != river.strip():
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_coverage",
                f"invalid river spelling at physical row {physical_row}",
            )
        site = _canonical_positive_int(str(row["site"]), f"site at physical row {physical_row}")
        site_id = f"{river}{site}"
        if site_id not in all_registry_ids:
            raise FinalEndpointTerminal(
                "stop_full_response_schema_or_coverage",
                f"response site {site_id!r} is outside the frozen 129-site registry",
            )
        abundance, missing_abundance = _abundance_value(
            str(row["abundance"]), missing_tokens
        )
        if missing_abundance:
            missing_abundance_rows += 1
        year_counts[year] = year_counts.get(year, 0) + 1
        if site_id in valid_ids:
            represented_valid.add(site_id)
        if str(row["latin"]) == focal_latin:
            focal_rows += 1
            if site_id in valid_ids:
                focal_rows_valid_nodes += 1
                if abundance > 0.0:
                    labels[site_id] = 1
                    focal_positive_rows += 1

    if physical_rows <= 0:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            "response table contains no data rows",
        )
    absent = sorted(valid_ids.difference(represented_valid))
    if absent:
        raise FinalEndpointTerminal(
            "stop_full_response_schema_or_coverage",
            f"{len(absent)} frozen valid nodes have no survey-table representation: {absent}",
        )

    positive_ids = sorted(site_id for site_id, value in labels.items() if value == 1)
    audit: dict[str, object] = {
        "physical_response_rows": physical_rows,
        "represented_valid_node_count": len(represented_valid),
        "focal_physical_latin": focal_latin,
        "focal_rows": focal_rows,
        "focal_rows_at_valid_nodes": focal_rows_valid_nodes,
        "focal_positive_rows": focal_positive_rows,
        "missing_abundance_rows": missing_abundance_rows,
        "positive_node_count": len(positive_ids),
        "negative_node_count": len(valid_ids) - len(positive_ids),
        "positive_node_ids": positive_ids,
        "year_row_counts": {str(year): year_counts[year] for year in sorted(year_counts)},
        "response_git_blob_sha1": git_blob_sha1(response_bytes),
        "response_size_bytes": len(response_bytes),
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return labels, audit


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
                f"frozen paired declaration fingerprint drift for {key}: {observed} != {paired[key]}"
            )


def _validate_pre_response_reconstruction(
    nodes: list[dict[str, object]],
    source_contract: dict[str, object],
    final_contract: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    geometry = derive_worlds(nodes, source_contract)
    baseline = derive_baseline_features(nodes)
    frozen = final_contract["worlds"]
    observed_local = geometry["local_worlds"]
    expected_local = frozen["local_worlds"]
    if len(observed_local) != len(expected_local):
        raise RuntimeError("pre-response local-world count drift")
    for observed, expected in zip(observed_local, expected_local, strict=True):
        for key in ("world_id", "edge_count", "graph_fingerprint"):
            if observed[key] != expected[key]:
                raise RuntimeError(f"pre-response world drift for {key}")
        if not math.isclose(
            float(observed["threshold_km"]),
            float(expected["threshold_km"]),
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise RuntimeError("pre-response world threshold drift")
    if geometry["external_open"]["graph_fingerprint"] != frozen["external_open"]["graph_fingerprint"]:
        raise RuntimeError("external_open graph fingerprint drift")
    if baseline["matrix_fingerprint"] != final_contract["baseline"]["matrix_fingerprint"]:
        raise RuntimeError("conventional baseline matrix fingerprint drift")
    return geometry, baseline


def build_frozen_operators(
    nodes: list[dict[str, object]],
    final_contract: dict[str, object],
) -> dict[str, DynamicTransitionOperator]:
    """Build exact EOG transition operators from the response-blind frozen graphs."""

    node_ids = tuple(str(row["site_id"]) for row in nodes)
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    operators: dict[str, DynamicTransitionOperator] = {}
    worlds = final_contract["worlds"]

    for world in worlds["local_worlds"]:
        threshold = float(world["threshold_km"])
        directed: list[DynamicReachabilityEdge] = []
        undirected_count = 0
        for i, left in enumerate(nodes):
            for right in nodes[i + 1 :]:
                if left["river"] != right["river"]:
                    continue
                distance = haversine_km(
                    float(left["longitude"]),
                    float(left["latitude"]),
                    float(right["longitude"]),
                    float(right["latitude"]),
                )
                if distance <= threshold:
                    a = index[str(left["site_id"])]
                    b = index[str(right["site_id"])]
                    directed.append(DynamicReachabilityEdge(a, b, geographic_support=1.0))
                    directed.append(DynamicReachabilityEdge(b, a, geographic_support=1.0))
                    undirected_count += 1
        if undirected_count != int(world["edge_count"]):
            raise RuntimeError(
                f"local operator edge count drift for {world['world_id']}: "
                f"{undirected_count} != {world['edge_count']}"
            )
        operators[str(world["world_id"])] = build_dynamic_transition_operator(
            node_ids,
            directed,
            loss_support=1.0,
        )

    external = worlds["external_open"]
    directed_external: list[DynamicReachabilityEdge] = []
    undirected_external = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            directed_external.append(DynamicReachabilityEdge(i, j, geographic_support=1.0))
            directed_external.append(DynamicReachabilityEdge(j, i, geographic_support=1.0))
            undirected_external += 1
    if undirected_external != int(external["edge_count"]):
        raise RuntimeError("external_open edge count drift")
    operators[str(external["world_id"])] = build_dynamic_transition_operator(
        node_ids,
        directed_external,
        loss_support=1.0,
    )
    if len(operators) != int(worlds["world_count"]):
        raise RuntimeError("declared world/operator count drift")
    return operators


def precompute_cumulative_hitting(
    operator: DynamicTransitionOperator,
    *,
    max_steps: int,
) -> np.ndarray:
    """Exact all-source/all-target cumulative first-passage recurrence.

    For each target j, overwriting H_t[j,j]=1 makes j absorbing in the dynamic
    recurrence. Therefore H_t[s,j] equals the same cumulative first-passage support
    returned by target-specific ``summarize_first_passage`` for a unit source s.
    """

    n = len(operator.node_ids)
    current = np.eye(n, dtype=float)
    history = np.empty((max_steps + 1, n, n), dtype=float)
    history[0] = current
    q = np.asarray(operator.transition, dtype=float)
    for step in range(1, max_steps + 1):
        current = q @ current
        np.fill_diagonal(current, 1.0)
        if not np.isfinite(current).all():
            raise RuntimeError("batch first-passage recurrence produced non-finite support")
        if np.any(current < -1e-14) or np.any(current > 1.0 + 1e-10):
            raise RuntimeError("batch first-passage recurrence left [0,1] support bounds")
        history[step] = current
    return history


def _ordered_occurrences(node_ids: tuple[str, ...], occurrence_ids: Iterable[str]) -> tuple[str, ...]:
    requested = {str(value) for value in occurrence_ids}
    if not requested.issubset(set(node_ids)):
        raise RuntimeError("occurrence set contains node outside frozen node universe")
    return tuple(node_id for node_id in node_ids if node_id in requested)


def select_fixed_sources(
    occurrence_ids: tuple[str, ...],
    node_by_id: Mapping[str, dict[str, object]],
) -> tuple[str, ...]:
    if len(occurrence_ids) < 2:
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "Layer-A reconstruction requires at least two positive occurrence nodes",
        )
    by_river: dict[str, list[str]] = {}
    for node_id in occurrence_ids:
        river = str(node_by_id[node_id]["river"])
        by_river.setdefault(river, []).append(node_id)
    selected: list[str] = []
    for river in sorted(by_river):
        selected.append(
            min(
                by_river[river],
                key=lambda node_id: (
                    int(node_by_id[node_id]["site_integer"]),
                    node_id,
                ),
            )
        )
    sources = tuple(node_id for node_id in occurrence_ids if node_id in set(selected))
    if len(sources) >= len(occurrence_ids):
        raise FinalEndpointTerminal(
            "non_estimable_layer_a_crossfit",
            "all current positive occurrences would be fixed sources, leaving no compatibility target",
        )
    return sources


def training_occurrence_set(
    full_calibration_positive_ids: Iterable[str],
    training_node_id: str,
    node_ids: tuple[str, ...],
) -> tuple[str, ...]:
    """Leave every training node out of its own label contribution.

    Removing a negative node is a no-op because it is not in the positive set; removing
    a positive node prevents direct self-label leakage into that row's Layer-B features.
    """

    positives = {str(value) for value in full_calibration_positive_ids}
    positives.discard(str(training_node_id))
    return tuple(node_id for node_id in node_ids if node_id in positives)


def _support_from_sources(history: np.ndarray, source_indices: np.ndarray) -> np.ndarray:
    cumulative = np.mean(history[:, source_indices, :], axis=1)
    cumulative[:, source_indices] = 1.0
    return cumulative


def layer_b_for_occurrences(
    occurrence_ids: Iterable[str],
    *,
    nodes: list[dict[str, object]],
    operators: Mapping[str, DynamicTransitionOperator],
    hitting_history: Mapping[str, np.ndarray],
    final_contract: dict[str, object],
) -> tuple[np.ndarray, dict[str, object]]:
    """Create unchanged symmetric Layer-B features for one cross-fit occurrence set."""

    node_ids = tuple(str(row["site_id"]) for row in nodes)
    node_by_id = {str(row["site_id"]): row for row in nodes}
    ordered_occurrences = _ordered_occurrences(node_ids, occurrence_ids)
    sources = select_fixed_sources(ordered_occurrences, node_by_id)
    source_set = set(sources)
    targets = tuple(node_id for node_id in ordered_occurrences if node_id not in source_set)
    source_index = np.asarray([node_ids.index(node_id) for node_id in sources], dtype=int)
    target_index = np.asarray([node_ids.index(node_id) for node_id in targets], dtype=int)
    tolerance = float(final_contract["worlds"]["support_tolerance"])
    max_steps = int(final_contract["worlds"]["max_steps"])

    declared_worlds: list[FiniteWorld] = []
    compatible_ids: list[str] = []
    compatibility_support: dict[str, list[float]] = {}
    for world_id, operator in operators.items():
        world = FiniteWorld(world_id=world_id, operator=operator, source_ids=sources)
        declared_worlds.append(world)
        final_support = np.mean(hitting_history[world_id][-1, source_index, :], axis=0)
        target_support = final_support[target_index]
        compatibility_support[world_id] = [float(value) for value in target_support]
        if bool(np.all(target_support > tolerance)):
            compatible_ids.append(world_id)

    if not compatible_ids:
        raise FinalEndpointTerminal(
            "universe_falsified_stop",
            "no frozen local/external world remains compatible with the cross-fit occurrence set",
        )

    gate = ForecastGateDeclaration(reachability_threshold=0.0)
    members: list[SimpleNamespace] = []
    declared_by_id = {world.world_id: world for world in declared_worlds}
    for world_id in compatible_ids:
        cumulative = _support_from_sources(hitting_history[world_id], source_index)
        supported = cumulative > tolerance
        members.append(
            SimpleNamespace(
                cumulative_reachability=cumulative,
                supported_state=supported,
            )
        )
    forecast_fingerprint = canonical_sha256(
        {
            "occurrence_ids": list(ordered_occurrences),
            "source_ids": list(sources),
            "compatible_world_ids": compatible_ids,
            "world_fingerprints": [
                [world.world_id, world.fingerprint] for world in declared_worlds
            ],
            "max_steps": max_steps,
            "gate_fingerprint": gate.fingerprint,
        }
    )
    forecast = SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=max_steps,
        gate_declaration=gate,
        world_fingerprints=tuple(
            (world.world_id, world.fingerprint) for world in declared_worlds
        ),
        fingerprint=forecast_fingerprint,
    )
    summary = summarize_worldset_for_prediction(forecast, step=max_steps)
    if tuple(summary.feature_names) != tuple(PREDICTIVE_FEATURE_NAMES):
        raise RuntimeError("unchanged Layer-B feature names drifted")
    matrix = np.asarray(summary.feature_matrix, dtype=float)
    if matrix.shape != (len(node_ids), len(PREDICTIVE_FEATURE_NAMES)):
        raise RuntimeError("Layer-B feature matrix shape drifted")
    if not np.isfinite(matrix).all():
        raise RuntimeError("Layer-B feature matrix contains non-finite values")
    audit: dict[str, object] = {
        "occurrence_count": len(ordered_occurrences),
        "source_ids": list(sources),
        "compatibility_target_ids": list(targets),
        "compatible_world_ids": compatible_ids,
        "declared_world_count": len(declared_worlds),
        "feature_fingerprint": summary.feature_fingerprint,
        "forecast_fingerprint": forecast_fingerprint,
        "compatibility_support": compatibility_support,
    }
    audit["fingerprint"] = canonical_sha256(audit)
    return matrix, audit


def _class_counts(values: np.ndarray) -> tuple[int, int]:
    values = np.asarray(values, dtype=int)
    return int(np.sum(values == 1)), int(np.sum(values == 0))


def _rf_from_contract(final_contract: dict[str, object]) -> RandomForestClassifier:
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
    classes = list(model.classes_)
    if classes != [0, 1]:
        raise RuntimeError(f"RandomForest class order drifted: {classes!r}")
    probability = model.predict_proba(features)[:, 1].astype(float)
    return np.clip(probability, EPS, 1.0 - EPS)


def evaluate_final_endpoint(
    coordinate_bytes: bytes,
    response_bytes: bytes,
    source_contract: dict[str, object],
    final_contract: dict[str, object],
    declaration: dict[str, object],
) -> dict[str, object]:
    """Execute the prospectively frozen five-fold paired endpoint once."""

    _validate_frozen_declaration(declaration)
    nodes, missing_coordinate_site_ids = parse_coordinate_registry(
        coordinate_bytes, source_contract
    )
    if len(nodes) != int(final_contract["node_and_split"]["valid_node_count"]):
        raise RuntimeError("valid-node count drift before response evaluation")
    node_ids = tuple(str(row["site_id"]) for row in nodes)
    node_index = {node_id: i for i, node_id in enumerate(node_ids)}
    node_by_id = {str(row["site_id"]): row for row in nodes}

    geometry_audit, baseline = _validate_pre_response_reconstruction(
        nodes, source_contract, final_contract
    )
    labels_by_id, response_audit = parse_response_table(
        response_bytes,
        nodes,
        missing_coordinate_site_ids,
        source_contract,
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

    operators = build_frozen_operators(nodes, final_contract)
    max_steps = int(final_contract["worlds"]["max_steps"])
    hitting_history = {
        world_id: precompute_cumulative_hitting(operator, max_steps=max_steps)
        for world_id, operator in operators.items()
    }

    baseline_rows = baseline["rows"]
    baseline_by_id = {
        str(row[0]): np.asarray(row[1:], dtype=float) for row in baseline_rows
    }
    if set(baseline_by_id) != set(node_ids):
        raise RuntimeError("baseline row IDs differ from frozen node universe")

    layer_b_cache: dict[tuple[str, ...], tuple[np.ndarray, dict[str, object]]] = {}

    def layer_b_cached(occurrence_ids: tuple[str, ...]) -> tuple[np.ndarray, dict[str, object]]:
        key = tuple(occurrence_ids)
        if key not in layer_b_cache:
            layer_b_cache[key] = layer_b_for_occurrences(
                key,
                nodes=nodes,
                operators=operators,
                hitting_history=hitting_history,
                final_contract=final_contract,
            )
        return layer_b_cache[key]

    fold_rows: list[dict[str, object]] = []
    paired_scores: list[PairedOuterUnitScore] = []
    model_fits = 0
    heldout_folds_with_both = 0
    fold_ids = [int(value) for value in final_contract["node_and_split"]["fold_ids"]]

    for fold in fold_ids:
        train_ids = tuple(
            node_id for node_id in node_ids if int(node_by_id[node_id]["fold"]) != fold
        )
        heldout_ids = tuple(
            node_id for node_id in node_ids if int(node_by_id[node_id]["fold"]) == fold
        )
        train_y = np.asarray([labels_by_id[node_id] for node_id in train_ids], dtype=int)
        heldout_y = np.asarray([labels_by_id[node_id] for node_id in heldout_ids], dtype=int)
        train_positive, train_negative = _class_counts(train_y)
        held_positive, held_negative = _class_counts(heldout_y)
        if (
            train_positive < int(estimability["minimum_calibration_positive_nodes_each_fold"])
            or train_negative < int(estimability["minimum_calibration_negative_nodes_each_fold"])
        ):
            raise FinalEndpointTerminal(
                "non_estimable_response_balance",
                f"fold {fold} calibration balance {train_positive}/{train_negative} fails frozen minima",
            )
        if held_positive > 0 and held_negative > 0:
            heldout_folds_with_both += 1

        full_positive = tuple(
            node_id for node_id in train_ids if labels_by_id[node_id] == 1
        )
        full_layer_b, heldout_layer_audit = layer_b_cached(full_positive)

        train_layer_b_rows: list[np.ndarray] = []
        crossfit_audits: dict[str, str] = {}
        for node_id in train_ids:
            occurrence_set = training_occurrence_set(full_positive, node_id, node_ids)
            matrix, audit = layer_b_cached(occurrence_set)
            train_layer_b_rows.append(matrix[node_index[node_id]])
            crossfit_audits[node_id] = str(audit["fingerprint"])

        x_train_base = np.vstack([baseline_by_id[node_id] for node_id in train_ids])
        x_held_base = np.vstack([baseline_by_id[node_id] for node_id in heldout_ids])
        x_train_layer_b = np.vstack(train_layer_b_rows)
        x_held_layer_b = np.vstack(
            [full_layer_b[node_index[node_id]] for node_id in heldout_ids]
        )
        x_train_aug = np.column_stack([x_train_base, x_train_layer_b])
        x_held_aug = np.column_stack([x_held_base, x_held_layer_b])

        baseline_model = _rf_from_contract(final_contract)
        augmented_model = _rf_from_contract(final_contract)
        baseline_model.fit(x_train_base, train_y)
        augmented_model.fit(x_train_aug, train_y)
        model_fits += 2
        baseline_p = _positive_probability(baseline_model, x_held_base)
        augmented_p = _positive_probability(augmented_model, x_held_aug)
        baseline_loss = float(log_loss(heldout_y, baseline_p, labels=[0, 1]))
        augmented_loss = float(log_loss(heldout_y, augmented_p, labels=[0, 1]))
        paired_scores.append(
            PairedOuterUnitScore(
                outer_unit_id=f"fold_{fold}",
                baseline_score=baseline_loss,
                augmented_score=augmented_loss,
            )
        )
        fold_row: dict[str, object] = {
            "fold": fold,
            "calibration_node_count": len(train_ids),
            "heldout_node_count": len(heldout_ids),
            "calibration_positive": train_positive,
            "calibration_negative": train_negative,
            "heldout_positive": held_positive,
            "heldout_negative": held_negative,
            "baseline_log_loss": baseline_loss,
            "augmented_log_loss": augmented_loss,
            "augmented_minus_baseline": augmented_loss - baseline_loss,
            "heldout_layer_a": heldout_layer_audit,
            "crossfit_occurrence_set_count": len(
                {training_occurrence_set(full_positive, node_id, node_ids) for node_id in train_ids}
            ),
            "crossfit_audit_fingerprint": canonical_sha256(crossfit_audits),
        }
        fold_row["fingerprint"] = canonical_sha256(fold_row)
        fold_rows.append(fold_row)

    if heldout_folds_with_both < int(estimability["minimum_heldout_folds_with_both_classes"]):
        raise FinalEndpointTerminal(
            "non_estimable_response_balance",
            f"only {heldout_folds_with_both}/5 heldout folds contain both classes",
        )
    if model_fits != 10:
        raise RuntimeError(f"paired five-fold endpoint must fit exactly 10 models, got {model_fits}")

    frozen_paired = declaration["paired_complementarity"]
    paired_declaration = PredictiveComplementarityDeclaration(
        metric_name=str(frozen_paired["metric_name"]),
        lower_is_better=bool(frozen_paired["lower_is_better"]),
        expected_outer_unit_count=int(frozen_paired["expected_outer_unit_count"]),
        favorable_min_augmented_wins=int(frozen_paired["favorable_min_augmented_wins"]),
        adverse_min_baseline_wins=int(frozen_paired["adverse_min_baseline_wins"]),
        learner_fit_fingerprint=str(frozen_paired["learner_fit_fingerprint"]),
        response_endpoint_fingerprint=str(frozen_paired["response_endpoint_fingerprint"]),
        split_fingerprint=str(frozen_paired["split_fingerprint"]),
        external_feature_fingerprint=str(frozen_paired["external_feature_fingerprint"]),
        eog_feature_fingerprint=str(frozen_paired["eog_feature_fingerprint"]),
    )
    paired_result = evaluate_predictive_complementarity(
        paired_declaration,
        paired_scores,
        tie_tolerance=float(frozen_paired["tie_tolerance"]),
    )

    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "predictive_result",
        "status": paired_result.status,
        "response_endpoint": source_contract["response_endpoint"]["unit"],
        "focal_taxon": source_contract["focal_taxon"]["canonical_name"],
        "total_positive_nodes": total_positive,
        "total_negative_nodes": total_negative,
        "heldout_folds_with_both_classes": heldout_folds_with_both,
        "model_fits": model_fits,
        "heldout_scores": len(paired_scores),
        "baseline_macro_log_loss": paired_result.baseline_macro_score,
        "augmented_macro_log_loss": paired_result.augmented_macro_score,
        "augmented_minus_baseline": paired_result.augmented_minus_baseline,
        "augmented_heldout_wins": paired_result.augmented_better_outer_units,
        "baseline_heldout_wins": paired_result.baseline_better_outer_units,
        "tied_heldout_units": paired_result.tied_outer_units,
        "paired_declaration_fingerprint": paired_result.declaration_fingerprint,
        "paired_score_fingerprint": paired_result.paired_score_fingerprint,
        "fold_results": fold_rows,
        "response_audit": response_audit,
        "pre_response_geometry_fingerprint": geometry_audit["distance_sample_sha256"],
        "baseline_matrix_fingerprint": baseline["matrix_fingerprint"],
        "unique_layer_b_crossfit_reconstructions": len(layer_b_cache),
        "layer_b_representation": "symmetric_world_support_summary_v1",
        "counts_as_predictive_evidence": True,
        "candidate_hunting_hard_stop": True,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def terminal_result(
    final_contract: dict[str, object],
    terminal: FinalEndpointTerminal,
    *,
    response_bytes_opened: int,
    coordinate_bytes_opened: int,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema": "eog.hokkaido_streamfish_endpoint3.final_endpoint.v1",
        "attempt_id": final_contract["attempt_id"],
        "issue": final_contract["issue"],
        "terminal_class": "protocol_or_estimability_stop",
        "status": terminal.status,
        "reason": terminal.reason,
        "coordinate_bytes_opened": int(coordinate_bytes_opened),
        "response_bytes_opened": int(response_bytes_opened),
        "counts_as_predictive_evidence": False,
        "candidate_hunting_hard_stop": False,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result
