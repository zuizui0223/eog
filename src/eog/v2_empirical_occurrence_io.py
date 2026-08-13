"""I/O helpers for prospective two-stage EOG v2 occurrence validation.

The freeze stage accepts only response-free node predictors and graph edges. The score
stage reads a previously fingerprinted feature bundle and a separate surveyed-response
file. This separation makes it difficult to tune source-conditioned predictors after
observing target outcomes by accident.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from .dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from .v2_empirical_occurrence_validation import (
    FixedSourceOccurrenceFeatures,
    FixedSourceOccurrenceValidationResult,
    _feature_fingerprint,
    build_fixed_source_occurrence_features,
)

FEATURE_SCHEMA = "eog_v2_fixed_source_occurrence_features_v1"
RESULT_SCHEMA = "eog_v2_fixed_source_occurrence_validation_v1"
_MISSING = {"", "na", "nan", "null", "."}


def _read_rows(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        fieldnames = [str(value).strip() for value in reader.fieldnames]
        if len(fieldnames) != len(set(fieldnames)) or any(not value for value in fieldnames):
            raise ValueError(f"CSV headers must be unique and non-empty: {path}")
        rows = []
        for raw in reader:
            rows.append({key.strip(): ("" if value is None else value.strip()) for key, value in raw.items()})
    if not rows:
        raise ValueError(f"CSV contains no data rows: {path}")
    return fieldnames, rows


def _parse_bool(value: str, label: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y"}:
        return True
    if normalized in {"0", "false", "f", "no", "n"}:
        return False
    raise ValueError(f"{label} must be encoded as 0/1 or true/false")


def _parse_finite(value: str, label: str) -> float:
    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not np.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def freeze_occurrence_features_from_csv(
    nodes_csv: str | Path,
    edges_csv: str | Path,
    *,
    max_steps: int,
    loss_support: float = 1.0,
) -> FixedSourceOccurrenceFeatures:
    """Freeze fixed-source EOG-R predictors from response-free CSV files.

    Node columns are exactly ``node_id``, ``viability``, ``source`` and optional
    ``ref_<name>`` conventional reference predictors. Columns such as ``response`` or
    ``fold_id`` are deliberately rejected at this stage.
    """

    fields, rows = _read_rows(nodes_csv)
    required = {"node_id", "viability", "source"}
    missing = required - set(fields)
    if missing:
        raise ValueError(f"nodes CSV missing required columns: {sorted(missing)}")
    unexpected = [name for name in fields if name not in required and not name.startswith("ref_")]
    if unexpected:
        raise ValueError(
            "nodes CSV freeze stage accepts only node_id, viability, source and ref_* columns; "
            f"unexpected columns: {unexpected}"
        )
    reference_columns = [name for name in fields if name.startswith("ref_")]
    reference_names = [name[4:] for name in reference_columns]
    if any(not name for name in reference_names) or len(reference_names) != len(set(reference_names)):
        raise ValueError("every ref_* column must define one unique non-empty reference name")

    node_ids = tuple(row["node_id"] for row in rows)
    if len(set(node_ids)) != len(node_ids) or any(not value for value in node_ids):
        raise ValueError("node_id values must be unique and non-empty")
    viability = [_parse_finite(row["viability"], f"viability for {row['node_id']}") for row in rows]
    source_mask = [_parse_bool(row["source"], f"source for {row['node_id']}") for row in rows]
    references = {
        name: [
            _parse_finite(row[column], f"{column} for {row['node_id']}")
            for row in rows
        ]
        for column, name in zip(reference_columns, reference_names)
    }

    edge_fields, edge_rows = _read_rows(edges_csv)
    edge_required = {"source_id", "target_id", "geographic_support"}
    edge_optional = {
        "environmental_support",
        "barrier_support",
        "directional_support",
        "target_capture_support",
    }
    missing_edges = edge_required - set(edge_fields)
    if missing_edges:
        raise ValueError(f"edges CSV missing required columns: {sorted(missing_edges)}")
    unexpected_edges = set(edge_fields) - edge_required - edge_optional
    if unexpected_edges:
        raise ValueError(f"edges CSV contains unexpected columns: {sorted(unexpected_edges)}")
    lookup = {node_id: index for index, node_id in enumerate(node_ids)}
    edges: list[DynamicReachabilityEdge] = []
    for row in edge_rows:
        source_id = row["source_id"]
        target_id = row["target_id"]
        if source_id not in lookup or target_id not in lookup:
            raise ValueError("every edge endpoint must occur in nodes CSV")

        def support(column: str, default: float = 1.0) -> float:
            value = row.get(column, "")
            return default if value == "" else _parse_finite(value, f"{column} on {source_id}->{target_id}")

        edges.append(
            DynamicReachabilityEdge(
                lookup[source_id],
                lookup[target_id],
                geographic_support=support("geographic_support"),
                environmental_support=support("environmental_support"),
                barrier_support=support("barrier_support"),
                directional_support=support("directional_support"),
                target_capture_support=support("target_capture_support"),
            )
        )
    operator = build_dynamic_transition_operator(node_ids, edges, loss_support=float(loss_support))
    return build_fixed_source_occurrence_features(
        node_ids,
        viability,
        source_mask,
        operator,
        max_steps=int(max_steps),
        reference_features=references,
    )


def feature_bundle_to_payload(features: FixedSourceOccurrenceFeatures) -> dict[str, object]:
    return {
        "schema": FEATURE_SCHEMA,
        "node_ids": list(features.node_ids),
        "viability": features.viability.tolist(),
        "dynamic_reachability": features.dynamic_reachability.tolist(),
        "source_mask": features.source_mask.astype(int).tolist(),
        "reference_names": list(features.reference_names),
        "reference_values": features.reference_values.tolist(),
        "max_steps": int(features.max_steps),
        "operator_fingerprint": features.operator_fingerprint,
        "feature_fingerprint": features.feature_fingerprint,
    }


def write_feature_bundle(path: str | Path, features: FixedSourceOccurrenceFeatures) -> None:
    Path(path).write_text(
        json.dumps(feature_bundle_to_payload(features), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def read_feature_bundle(path: str | Path) -> FixedSourceOccurrenceFeatures:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema") != FEATURE_SCHEMA:
        raise ValueError("unsupported occurrence feature-bundle schema")
    ids = tuple(str(value) for value in payload["node_ids"])
    viability = np.asarray(payload["viability"], dtype=float)
    dynamic = np.asarray(payload["dynamic_reachability"], dtype=float)
    source_mask = np.asarray(payload["source_mask"], dtype=int).astype(bool)
    reference_names = tuple(str(value) for value in payload["reference_names"])
    reference_values = np.asarray(payload["reference_values"], dtype=float)
    n = len(ids)
    if viability.shape != (n,) or dynamic.shape != (n,) or source_mask.shape != (n,):
        raise ValueError("feature-bundle node vectors are misaligned")
    if reference_values.shape != (n, len(reference_names)):
        raise ValueError("feature-bundle reference matrix is misaligned")
    if not np.isfinite(viability).all() or not np.isfinite(dynamic).all() or not np.isfinite(reference_values).all():
        raise ValueError("feature-bundle predictors must be finite")
    max_steps = int(payload["max_steps"])
    operator_fingerprint = str(payload["operator_fingerprint"])
    observed_fingerprint = str(payload["feature_fingerprint"])
    expected_fingerprint = _feature_fingerprint(
        ids,
        viability,
        dynamic,
        source_mask,
        reference_names,
        reference_values,
        max_steps,
        operator_fingerprint,
    )
    if observed_fingerprint != expected_fingerprint:
        raise ValueError("occurrence feature-bundle fingerprint mismatch")
    return FixedSourceOccurrenceFeatures(
        node_ids=ids,
        viability=viability,
        dynamic_reachability=dynamic,
        source_mask=source_mask,
        reference_names=reference_names,
        reference_values=reference_values,
        max_steps=max_steps,
        operator_fingerprint=operator_fingerprint,
        feature_fingerprint=observed_fingerprint,
    )


def read_occurrence_response_csv(
    path: str | Path,
    node_ids: Sequence[str],
) -> tuple[np.ndarray, tuple[str, ...]]:
    fields, rows = _read_rows(path)
    required = {"node_id", "response", "fold_id"}
    if set(fields) != required:
        raise ValueError("response CSV must contain exactly node_id,response,fold_id")
    expected = tuple(str(value) for value in node_ids)
    by_id: dict[str, tuple[float, str]] = {}
    for row in rows:
        node_id = row["node_id"]
        if node_id in by_id:
            raise ValueError("response CSV contains duplicate node_id")
        fold = row["fold_id"]
        if not fold:
            raise ValueError("every response row requires a non-empty fold_id")
        raw = row["response"].strip().lower()
        if raw in _MISSING:
            response = float("nan")
        else:
            response = _parse_finite(row["response"], f"response for {node_id}")
            if response not in (0.0, 1.0):
                raise ValueError("observed responses must be 0/1; use blank/NA for missing")
        by_id[node_id] = (response, fold)
    if set(by_id) != set(expected):
        missing = sorted(set(expected) - set(by_id))
        extra = sorted(set(by_id) - set(expected))
        raise ValueError(f"response CSV node set must match feature bundle; missing={missing}, extra={extra}")
    response = np.asarray([by_id[node_id][0] for node_id in expected], dtype=float)
    folds = tuple(by_id[node_id][1] for node_id in expected)
    return response, folds


def validation_result_to_payload(
    result: FixedSourceOccurrenceValidationResult,
) -> dict[str, object]:
    return {
        "schema": RESULT_SCHEMA,
        "feature_fingerprint": result.feature_fingerprint,
        "operator_fingerprint": result.operator_fingerprint,
        "fold_ids": list(result.fold_ids),
        "model_scores": [
            {
                "model_name": score.model_name,
                "log_loss": score.log_loss,
                "brier": score.brier,
                "n_evaluated": score.n_evaluated,
            }
            for score in result.model_scores
        ],
        "dynamic_increment_over_viability": result.dynamic_increment_over_viability,
        "dynamic_increment_over_references": [
            {"reference": name, "delta_log_loss": value}
            for name, value in result.dynamic_increment_over_references
        ],
        "n_evaluated": result.n_evaluated,
        "n_missing_response": result.n_missing_response,
    }


def write_validation_result(
    path: str | Path,
    result: FixedSourceOccurrenceValidationResult,
) -> None:
    Path(path).write_text(
        json.dumps(validation_result_to_payload(result), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
