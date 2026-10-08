"""Compact source-symmetric Layer-B candidate representation.

This post-closure candidate removes deterministic feature expansion from the prediction
interface. Layer A keeps exact source/world identities. Prediction first averages support
across the declared source set inside each surviving world, then exposes only four
prospectively declared summaries:

- surviving-world fraction;
- support mean;
- support standard deviation;
- minimum support.

The representation is intentionally lossy. It does not claim to be a sufficient statistic
for the latent world-support vector. Its purpose is to avoid presenting a small latent
world vector as a larger set of highly dependent supervised columns.

This module must not be used to revise any frozen EOG-WF endpoint.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES: tuple[str, ...] = (
    "surviving_world_fraction",
    "support_mean",
    "support_std",
    "support_min",
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
class CompactSourceSymmetricSummary:
    node_ids: tuple[str, ...]
    feature_names: tuple[str, ...]
    feature_matrix: np.ndarray
    statuses: tuple[str, ...]
    declared_world_count: int
    surviving_world_count: int
    source_count: int
    latent_dimension_upper_bound: int
    constant_feature_names: tuple[str, ...]
    centered_feature_rank: int
    representation_name: str
    feature_fingerprint: str
    latent_state_fingerprint: str
    fingerprint: str


def summarize_compact_source_symmetric_support(
    support_by_source_world_node: np.ndarray,
    *,
    source_ids: Sequence[str],
    world_ids: Sequence[str],
    node_ids: Sequence[str],
    declared_world_count: int,
    support_threshold: float = 0.0,
) -> CompactSourceSymmetricSummary:
    """Build the compact source/world-label-invariant Layer-B candidate.

    support_by_source_world_node has shape (source, world, node) with values in [0, 1].
    Source support is equally averaged inside each surviving world. The four
    prediction-facing columns are then computed across surviving worlds.

    The feature fingerprint excludes exact source/world labels. Exact identities and the
    original tensor remain separately represented by latent_state_fingerprint.
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

    world_node = np.mean(matrix, axis=0)
    surviving_fraction = len(worlds) / declared

    rows: list[list[float]] = []
    statuses: list[str] = []
    feature_payload_rows: list[list[object]] = []
    for node_index, node_id in enumerate(nodes):
        values = world_node[:, node_index]
        flags = values > threshold
        row = [
            float(surviving_fraction),
            float(np.mean(values)),
            float(np.std(values, ddof=0)),
            float(np.min(values)),
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
    constant_mask = np.all(feature_matrix == feature_matrix[0, :], axis=0)
    constant_names = tuple(
        name
        for name, is_constant in zip(
            COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES, constant_mask, strict=True
        )
        if bool(is_constant)
    )
    centered = feature_matrix - np.mean(feature_matrix, axis=0, keepdims=True)
    centered_rank = int(np.linalg.matrix_rank(centered))

    representation_name = "compact_source_symmetric_world_support_summary_v3_candidate"
    feature_payload = {
        "node_ids": list(nodes),
        "feature_names": list(COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES),
        "rows": feature_payload_rows,
        "declared_world_count": declared,
        "surviving_world_count": len(worlds),
        "source_count": len(sources),
        "latent_dimension_upper_bound": len(worlds),
        "constant_feature_names": list(constant_names),
        "centered_feature_rank": centered_rank,
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
    return CompactSourceSymmetricSummary(
        node_ids=nodes,
        feature_names=COMPACT_SOURCE_SYMMETRIC_FEATURE_NAMES,
        feature_matrix=feature_matrix,
        statuses=tuple(statuses),
        declared_world_count=declared,
        surviving_world_count=len(worlds),
        source_count=len(sources),
        latent_dimension_upper_bound=len(worlds),
        constant_feature_names=constant_names,
        centered_feature_rank=centered_rank,
        representation_name=representation_name,
        feature_fingerprint=feature_fp,
        latent_state_fingerprint=latent_fp,
        fingerprint=_canonical_sha256(object_payload),
    )
