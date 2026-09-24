"""Structure-preserving Layer-B placebo utilities.

The historical Tampa placebo permuted columns independently. That preserved each
column's marginal distribution but destroyed cross-column dependence. These utilities
provide prospective controls that randomize feature-to-observation correspondence while
preserving the joint feature vector.

Two modes are exposed:

- joint-row permutation: preserves the exact multiset of row vectors;
- grouped-vector permutation: preserves one static feature vector per declared group,
  suitable for repeated-measure nodes whose Layer-B state is intentionally reused.

These controls are prospective only and must not be used to revise frozen endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _matrix(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("feature_matrix must be a non-empty two-dimensional array")
    if not np.isfinite(matrix).all():
        raise ValueError("feature_matrix must be finite")
    return matrix


@dataclass(frozen=True)
class StructurePreservingPlacebo:
    feature_matrix: np.ndarray
    mode: str
    seed: int
    permutation: tuple[int, ...]
    group_ids: tuple[str, ...] | None
    fingerprint: str


def permute_joint_rows(
    feature_matrix: np.ndarray,
    *,
    seed: int,
) -> StructurePreservingPlacebo:
    """Permute complete feature rows, preserving all column dependence exactly."""

    matrix = _matrix(feature_matrix)
    rng = np.random.default_rng(int(seed))
    permutation = tuple(int(value) for value in rng.permutation(matrix.shape[0]))
    permuted = matrix[np.asarray(permutation, dtype=int), :].copy()
    payload = {
        "mode": "joint_row",
        "seed": int(seed),
        "permutation": list(permutation),
        "feature_matrix": permuted.tolist(),
    }
    return StructurePreservingPlacebo(
        feature_matrix=permuted,
        mode="joint_row",
        seed=int(seed),
        permutation=permutation,
        group_ids=None,
        fingerprint=_canonical_sha256(payload),
    )


def permute_group_vectors(
    feature_matrix: np.ndarray,
    *,
    group_ids: Sequence[str],
    seed: int,
) -> StructurePreservingPlacebo:
    """Permute complete static feature vectors among groups.

    Every row belonging to one group must have the same original feature vector. The
    permutation operates on the group-level vector table, then assigns the permuted
    vector to every row of the target group. This preserves within-group static reuse and
    the group-level multiset of joint feature vectors.
    """

    matrix = _matrix(feature_matrix)
    groups = tuple(str(value).strip() for value in group_ids)
    if len(groups) != matrix.shape[0]:
        raise ValueError("group_ids length must equal feature_matrix row count")
    if any(not value for value in groups):
        raise ValueError("group_ids must be non-empty strings")

    ordered_groups = tuple(sorted(set(groups)))
    representatives: list[np.ndarray] = []
    for group in ordered_groups:
        indices = np.asarray([i for i, value in enumerate(groups) if value == group], dtype=int)
        block = matrix[indices, :]
        if not np.all(block == block[0, :]):
            raise ValueError(
                "grouped-vector placebo requires one identical feature vector per group"
            )
        representatives.append(block[0, :].copy())

    representative_matrix = np.vstack(representatives)
    rng = np.random.default_rng(int(seed))
    permutation = tuple(int(value) for value in rng.permutation(len(ordered_groups)))
    permuted_representatives = representative_matrix[
        np.asarray(permutation, dtype=int), :
    ]

    group_to_vector = {
        group: permuted_representatives[index, :]
        for index, group in enumerate(ordered_groups)
    }
    permuted = np.vstack([group_to_vector[group] for group in groups])
    payload = {
        "mode": "group_vector",
        "seed": int(seed),
        "ordered_groups": list(ordered_groups),
        "permutation": list(permutation),
        "group_level_feature_matrix": permuted_representatives.tolist(),
    }
    return StructurePreservingPlacebo(
        feature_matrix=permuted,
        mode="group_vector",
        seed=int(seed),
        permutation=permutation,
        group_ids=groups,
        fingerprint=_canonical_sha256(payload),
    )
