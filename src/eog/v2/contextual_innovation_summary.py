"""Contextual innovation projection for prediction-facing EOG Layer B v2.

This module leaves exact Layer A untouched.  It takes two already source-symmetric
prediction-facing summaries computed under pre-outcome information constraints and
returns only their change from a fixed reference context.  Any node-by-feature component
that is identical in reference and current summaries therefore cancels exactly.

The representation is a candidate interface motivated by post-closure mechanism work.
It has not been shown to improve ecological prediction and cannot revise any frozen
endpoint result.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import numpy as np

from .source_symmetric_predictive_summary import SourceSymmetricPredictiveSummary


INNOVATION_PREFIX = "delta_from_reference__"


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ContextualInnovationSummary:
    """Node-level change in source-symmetric Layer-B state from a fixed reference."""

    node_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    feature_matrix: np.ndarray
    changed_node_fraction: float
    mean_absolute_innovation: float
    max_absolute_innovation: float
    exact_zero_matrix: bool
    representation_name: str
    reference_feature_fingerprint: str
    current_feature_fingerprint: str
    innovation_feature_fingerprint: str
    fingerprint: str


def _validate_summary(summary: Any, label: str) -> SourceSymmetricPredictiveSummary:
    if not isinstance(summary, SourceSymmetricPredictiveSummary):
        raise TypeError(f"{label} must be SourceSymmetricPredictiveSummary")
    if summary.representation_name != "source_symmetric_world_support_summary_v2_candidate":
        raise ValueError(f"{label} has unexpected representation_name")
    matrix = np.asarray(summary.feature_matrix, dtype=float)
    expected = (len(summary.node_ids), len(summary.feature_names))
    if matrix.shape != expected:
        raise ValueError(f"{label} feature matrix must have shape {expected}")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{label} feature matrix must be finite")
    return summary


def summarize_contextual_innovation(
    reference: SourceSymmetricPredictiveSummary,
    current: SourceSymmetricPredictiveSummary,
    *,
    zero_tolerance: float = 0.0,
) -> ContextualInnovationSummary:
    """Return cumulative prediction-facing innovation since a fixed pre-outcome state.

    ``reference`` and ``current`` must have identical node and feature identity.  Both
    should have been computed before the outcome of the scored current context is opened.
    The transform itself is deterministic and response-free::

        innovation[node, feature] = current[node, feature] - reference[node, feature]

    Because subtraction is performed row-wise, any static node-specific spatial/topology
    signature shared by both contexts cancels exactly.  This does *not* imply that every
    remaining change is ecological mechanism; it is change in the declared Layer-B state.
    """

    ref = _validate_summary(reference, "reference")
    cur = _validate_summary(current, "current")
    if tuple(ref.node_ids) != tuple(cur.node_ids):
        raise ValueError("reference/current node_ids must match exactly and in order")
    if tuple(ref.feature_names) != tuple(cur.feature_names):
        raise ValueError("reference/current feature_names must match exactly and in order")
    tolerance = float(zero_tolerance)
    if not np.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("zero_tolerance must be finite and non-negative")

    matrix = np.asarray(cur.feature_matrix, dtype=float) - np.asarray(
        ref.feature_matrix, dtype=float
    )
    absolute = np.abs(matrix)
    changed = np.any(absolute > tolerance, axis=1)
    feature_names = tuple(INNOVATION_PREFIX + name for name in ref.feature_names)
    representation_name = "contextual_source_symmetric_innovation_v2_candidate"

    rows = [
        [node_id, *[float(value) for value in row]]
        for node_id, row in zip(ref.node_ids, matrix, strict=True)
    ]
    feature_payload = {
        "node_ids": list(ref.node_ids),
        "feature_names": list(feature_names),
        "rows": rows,
        "representation_name": representation_name,
        "zero_tolerance": tolerance,
    }
    feature_fp = _canonical_sha256(feature_payload)
    object_payload = {
        **feature_payload,
        "reference_feature_fingerprint": ref.feature_fingerprint,
        "current_feature_fingerprint": cur.feature_fingerprint,
        "innovation_feature_fingerprint": feature_fp,
    }
    return ContextualInnovationSummary(
        node_ids=tuple(ref.node_ids),
        feature_names=feature_names,
        feature_matrix=matrix,
        changed_node_fraction=float(np.mean(changed)),
        mean_absolute_innovation=float(np.mean(absolute)),
        max_absolute_innovation=float(np.max(absolute)),
        exact_zero_matrix=bool(np.array_equal(matrix, np.zeros_like(matrix))),
        representation_name=representation_name,
        reference_feature_fingerprint=ref.feature_fingerprint,
        current_feature_fingerprint=cur.feature_fingerprint,
        innovation_feature_fingerprint=feature_fp,
        fingerprint=_canonical_sha256(object_payload),
    )
