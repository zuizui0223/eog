"""Experimental source-symmetric prediction-facing summary for EOG v2.

The exact Layer-A source identities remain upstream scientific state.  This module only
changes the prediction-facing projection: support is first aggregated equally across a
declared source set, then summarized symmetrically across surviving worlds.  Therefore
arbitrary source ordering or source-ID spelling cannot change the feature matrix.

This is a candidate interface motivated by a post-closure mechanism audit.  It has not
been shown to improve prediction and must not be used to revise frozen endpoint results.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


SOURCE_SYMMETRIC_FEATURE_NAMES: tuple[str, ...] = (
    "surviving_world_fraction",
    "support_mean",
    "support_std",
    "support_min",
    "support_max",
    "support_q25",
    "support_q50",
    "support_q75",
    "positive_support_fraction",
    "support_range",
)


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ids(values: Sequence[str], label: str) -> tuple[str, ...]:
    result = tuple(str(value).strip() for value in values)
    if not result or any(not value for value in result) or len(set(result)) != len(result):
        raise ValueError(f"{label} must contain unique non-empty values")
    return result


@dataclass(frozen=True)
class SourceSymmetricPredictiveSummary:
    node_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    feature_matrix: np.ndarray
    statuses: tuple[str, ...]
    declared_world_count: int
    surviving_world_count: int
    source_count: int
    representation_name: str
    feature_fingerprint: str
    latent_state_fingerprint: str
    fingerprint: str


def summarize_source_symmetric_support(
    support_by_source_world_node: np.ndarray,
    *,
    source_ids: Sequence[str],
    world_ids: Sequence[str],
    node_ids: Sequence[str],
    declared_world_count: int,
    support_threshold: float = 0.0,
) -> SourceSymmetricPredictiveSummary:
    """Build a source-label/order-invariant Layer-B candidate representation.

    ``support_by_source_world_node`` must have shape ``(source, world, node)`` and values
    in [0, 1].  Supports are equally averaged across sources inside each world before the
    usual symmetric statistics are taken across worlds.  The prediction-facing feature
    fingerprint excludes source/world labels.  A separate latent-state fingerprint keeps
    those exact identities auditable upstream.
    """

    sources = _ids(source_ids, "source_ids")
    worlds = _ids(world_ids, "world_ids")
    nodes = _ids(node_ids, "node_ids")
    matrix = np.asarray(support_by_source_world_node, dtype=float)
    expected = (len(sources), len(worlds), len(nodes))
    if matrix.shape != expected:
        raise ValueError(f"support tensor must have shape {expected}, got {matrix.shape}")
    if not np.isfinite(matrix).all() or np.any(matrix < 0.0) or np.any(matrix > 1.0):
        raise ValueError("support tensor must contain finite values in [0, 1]")
    declared = int(declared_world_count)
    if declared <= 0 or len(worlds) > declared:
        raise ValueError("declared_world_count must be >= surviving world count and positive")
    threshold = float(support_threshold)
    if not np.isfinite(threshold):
        raise ValueError("support_threshold must be finite")

    # Equal-weight source aggregation is symmetric in source order and labels.
    world_node = np.mean(matrix, axis=0)
    surviving_fraction = len(worlds) / declared
    rows: list[list[float]] = []
    statuses: list[str] = []
    feature_payload_rows: list[list[object]] = []
    for node_index, node_id in enumerate(nodes):
        values = world_node[:, node_index]
        flags = values > threshold
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        row = [
            float(surviving_fraction),
            float(np.mean(values)),
            float(np.std(values, ddof=0)),
            minimum,
            maximum,
            float(np.quantile(values, 0.25, method="linear")),
            float(np.quantile(values, 0.50, method="linear")),
            float(np.quantile(values, 0.75, method="linear")),
            float(np.mean(flags)),
            float(maximum - minimum),
        ]
        count = int(np.sum(flags))
        if count == 0:
            status = "excluded_in_all_worlds"
        elif count == len(worlds):
            status = "robustly_supported"
        else:
            status = "contingent"
        rows.append(row)
        statuses.append(status)
        feature_payload_rows.append([node_id, *row, status])

    feature_matrix = np.asarray(rows, dtype=float)
    representation_name = "source_symmetric_world_support_summary_v2_candidate"
    feature_payload = {
        "node_ids": list(nodes),
        "feature_names": list(SOURCE_SYMMETRIC_FEATURE_NAMES),
        "rows": feature_payload_rows,
        "declared_world_count": declared,
        "surviving_world_count": len(worlds),
        "source_count": len(sources),
        "representation_name": representation_name,
        "support_threshold": threshold,
    }
    feature_fp = _canonical_sha256(feature_payload)
    latent_payload = {
        "source_ids": list(sources),
        "world_ids": list(worlds),
        "node_ids": list(nodes),
        "support_tensor": matrix.tolist(),
    }
    latent_fp = _canonical_sha256(latent_payload)
    object_payload = {
        **feature_payload,
        "feature_fingerprint": feature_fp,
        "latent_state_fingerprint": latent_fp,
    }
    return SourceSymmetricPredictiveSummary(
        node_ids=nodes,
        feature_names=SOURCE_SYMMETRIC_FEATURE_NAMES,
        feature_matrix=feature_matrix,
        statuses=tuple(statuses),
        declared_world_count=declared,
        surviving_world_count=len(worlds),
        source_count=len(sources),
        representation_name=representation_name,
        feature_fingerprint=feature_fp,
        latent_state_fingerprint=latent_fp,
        fingerprint=_canonical_sha256(object_payload),
    )
