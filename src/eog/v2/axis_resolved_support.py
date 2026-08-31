"""Audit niche/use partition hidden by planar support projections.

The functions in this module compare two non-negative support tensors in their
full axis-resolved state space and after marginalising vertical and/or temporal
axes. They are intentionally descriptive: they do not infer a fundamental
niche, causal interaction, competition, predation, or simultaneous encounter
from occurrence data.

The canonical tensor layout is ``(y, x, z, time)``, but callers may identify
different axis positions explicitly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AxisResolvedOverlapResult:
    """Pairwise overlap and the partition hidden by lower-dimensional maps."""

    shape: tuple[int, ...]
    horizontal_axes: tuple[int, int]
    vertical_axis: int
    temporal_axis: int
    available_cell_count: int
    support_mass_a: float
    support_mass_b: float
    full_overlap: float
    horizontal_projection_overlap: float
    horizontal_vertical_overlap: float
    horizontal_temporal_overlap: float
    vertical_hidden_partition_gap: float
    temporal_hidden_partition_gap: float
    total_projection_collapse_gap: float
    joint_only_hidden_partition_gap: float
    fingerprint: str

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation."""

        return asdict(self)


def _canonical_axis(axis: int, ndim: int) -> int:
    value = int(axis)
    if value < 0:
        value += ndim
    if not 0 <= value < ndim:
        raise ValueError(f"axis {axis} is outside a {ndim}-dimensional support tensor")
    return value


def _validate_axes(
    ndim: int,
    horizontal_axes: Sequence[int],
    vertical_axis: int,
    temporal_axis: int,
) -> tuple[tuple[int, int], int, int]:
    horizontal = tuple(_canonical_axis(axis, ndim) for axis in horizontal_axes)
    if len(horizontal) != 2:
        raise ValueError("horizontal_axes must identify exactly two axes")
    vertical = _canonical_axis(vertical_axis, ndim)
    temporal = _canonical_axis(temporal_axis, ndim)
    if len(set((*horizontal, vertical, temporal))) != 4:
        raise ValueError(
            "horizontal, vertical and temporal axes must identify four distinct axes"
        )
    return (int(horizontal[0]), int(horizontal[1])), vertical, temporal


def _validate_pair(
    support_a: np.ndarray,
    support_b: np.ndarray,
    unavailable_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    a = np.asarray(support_a, dtype=float)
    b = np.asarray(support_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("support tensors must have the same shape")
    if a.ndim < 4 or a.size == 0:
        raise ValueError("axis-resolved support tensors must be non-empty and at least 4D")
    mask = (
        np.zeros(a.shape, dtype=bool)
        if unavailable_mask is None
        else np.asarray(unavailable_mask, dtype=bool)
    )
    if mask.shape != a.shape:
        raise ValueError("unavailable_mask must match the support tensor shape")
    available = ~mask
    if not np.any(available):
        raise ValueError("support tensors have no available cells")
    for label, field in (("support_a", a), ("support_b", b)):
        values = field[available]
        if not np.isfinite(values).all():
            raise ValueError(f"{label} must be finite on available cells")
        if np.any(values < 0):
            raise ValueError(f"{label} must be non-negative on available cells")
        if float(values.sum()) <= 0:
            raise ValueError(f"{label} must have positive mass on available cells")
    return a, b, available


def _normalise(field: np.ndarray, available: np.ndarray) -> tuple[np.ndarray, float]:
    mass = float(field[available].sum())
    probability = np.zeros(field.shape, dtype=float)
    probability[available] = field[available] / mass
    return probability, mass


def _marginal(probability: np.ndarray, keep_axes: Sequence[int]) -> np.ndarray:
    keep = tuple(sorted(int(axis) for axis in keep_axes))
    if len(set(keep)) != len(keep):
        raise ValueError("keep_axes must be unique")
    dropped = tuple(axis for axis in range(probability.ndim) if axis not in keep)
    return probability.sum(axis=dropped) if dropped else probability.copy()


def _overlap_of_probabilities(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError("probability arrays must have the same shape")
    value = 1.0 - 0.5 * float(np.abs(a - b).sum())
    if value < 0 and value > -1e-12:
        value = 0.0
    if value > 1 and value < 1 + 1e-12:
        value = 1.0
    return float(np.clip(value, 0.0, 1.0))


def schoener_overlap(
    support_a: np.ndarray,
    support_b: np.ndarray,
    *,
    unavailable_mask: np.ndarray | None = None,
) -> float:
    """Return Schoener overlap after independently normalising two supports."""

    a, b, available = _validate_pair(support_a, support_b, unavailable_mask)
    pa, _ = _normalise(a, available)
    pb, _ = _normalise(b, available)
    return _overlap_of_probabilities(pa, pb)


def audit_axis_resolved_overlap(
    support_a: np.ndarray,
    support_b: np.ndarray,
    *,
    horizontal_axes: Sequence[int] = (0, 1),
    vertical_axis: int = 2,
    temporal_axis: int = 3,
    unavailable_mask: np.ndarray | None = None,
) -> AxisResolvedOverlapResult:
    """Quantify partition hidden by marginalising vertical and temporal axes.

    ``vertical_hidden_partition_gap`` is ``D_xy - D_xyz``.
    ``temporal_hidden_partition_gap`` is ``D_xy - D_xyt``.
    ``total_projection_collapse_gap`` is ``D_xy - D_xyzt``.
    ``joint_only_hidden_partition_gap`` is
    ``min(D_xyz, D_xyt) - D_xyzt``.

    All quantities are threshold-free differences in Schoener overlap. Positive
    gaps mean the lower-dimensional map made the two supports appear more similar
    than they are in the retained state space.
    """

    a, b, available = _validate_pair(support_a, support_b, unavailable_mask)
    horizontal, vertical, temporal = _validate_axes(
        a.ndim, horizontal_axes, vertical_axis, temporal_axis
    )
    pa, mass_a = _normalise(a, available)
    pb, mass_b = _normalise(b, available)

    full_overlap = _overlap_of_probabilities(pa, pb)
    xy_overlap = _overlap_of_probabilities(
        _marginal(pa, horizontal), _marginal(pb, horizontal)
    )
    xyz_axes = (*horizontal, vertical)
    xyt_axes = (*horizontal, temporal)
    xyz_overlap = _overlap_of_probabilities(
        _marginal(pa, xyz_axes), _marginal(pb, xyz_axes)
    )
    xyt_overlap = _overlap_of_probabilities(
        _marginal(pa, xyt_axes), _marginal(pb, xyt_axes)
    )

    vertical_gap = max(0.0, xy_overlap - xyz_overlap)
    temporal_gap = max(0.0, xy_overlap - xyt_overlap)
    total_gap = max(0.0, xy_overlap - full_overlap)
    joint_only_gap = max(0.0, min(xyz_overlap, xyt_overlap) - full_overlap)

    fingerprint_payload = {
        "shape": list(a.shape),
        "horizontal_axes": list(horizontal),
        "vertical_axis": vertical,
        "temporal_axis": temporal,
        "available_cell_count": int(available.sum()),
        "support_a_sha256": hashlib.sha256(
            np.ascontiguousarray(pa, dtype="<f8").tobytes()
        ).hexdigest(),
        "support_b_sha256": hashlib.sha256(
            np.ascontiguousarray(pb, dtype="<f8").tobytes()
        ).hexdigest(),
        "available_mask_sha256": hashlib.sha256(
            np.ascontiguousarray(available, dtype=np.uint8).tobytes()
        ).hexdigest(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(
            fingerprint_payload, sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()

    return AxisResolvedOverlapResult(
        shape=tuple(int(value) for value in a.shape),
        horizontal_axes=horizontal,
        vertical_axis=vertical,
        temporal_axis=temporal,
        available_cell_count=int(available.sum()),
        support_mass_a=mass_a,
        support_mass_b=mass_b,
        full_overlap=full_overlap,
        horizontal_projection_overlap=xy_overlap,
        horizontal_vertical_overlap=xyz_overlap,
        horizontal_temporal_overlap=xyt_overlap,
        vertical_hidden_partition_gap=vertical_gap,
        temporal_hidden_partition_gap=temporal_gap,
        total_projection_collapse_gap=total_gap,
        joint_only_hidden_partition_gap=joint_only_gap,
        fingerprint=fingerprint,
    )
