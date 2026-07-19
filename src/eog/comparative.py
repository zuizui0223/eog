"""Comparative EOG under one predeclared robust scaling reference."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from .geometry import (
    OccupancyGeometry,
    _component_labels,
    _feature_matrix,
    _gap_threshold,
    minimum_spanning_tree,
)


@dataclass(frozen=True)
class RobustReference:
    """Serializable median/MAD transformation fitted once for multiple groups."""

    median: np.ndarray
    scale: np.ndarray
    constant: np.ndarray
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "median": self.median.tolist(),
            "scale": self.scale.tolist(),
            "constant": self.constant.astype(bool).tolist(),
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RobustReference":
        required = {"median", "scale", "constant", "provenance"}
        missing = required.difference(payload)
        if missing:
            raise ValueError(f"reference payload missing fields: {sorted(missing)}")
        median = np.asarray(payload["median"], dtype=float)
        scale = np.asarray(payload["scale"], dtype=float)
        constant = np.asarray(payload["constant"], dtype=bool)
        if median.ndim != 1 or scale.shape != median.shape or constant.shape != median.shape:
            raise ValueError("reference arrays must be one-dimensional and have matching shapes")
        if not np.isfinite(median).all() or not np.isfinite(scale).all() or np.any(scale <= 0):
            raise ValueError("reference median and scale must be finite with positive scales")
        return cls(median=median, scale=scale, constant=constant, provenance=str(payload["provenance"]))


def fit_robust_reference(values: np.ndarray, *, provenance: str) -> RobustReference:
    """Fit one median/MAD transform without using downstream group outcomes."""
    if not str(provenance).strip():
        raise ValueError("provenance must be a non-empty description")
    matrix = _feature_matrix(values)
    median = np.median(matrix, axis=0)
    mad = np.median(np.abs(matrix - median), axis=0) * 1.4826
    constant = mad == 0.0
    scale = np.where(constant, 1.0, mad)
    return RobustReference(
        median=np.asarray(median, dtype=float),
        scale=np.asarray(scale, dtype=float),
        constant=np.asarray(constant, dtype=bool),
        provenance=str(provenance),
    )


def transform_with_reference(values: np.ndarray, reference: RobustReference) -> np.ndarray:
    """Apply an already-fitted reference transform to a new occurrence matrix."""
    matrix = _feature_matrix(values)
    if matrix.shape[1] != len(reference.median):
        raise ValueError("values must match the reference feature dimension")
    transformed = (matrix - reference.median) / reference.scale
    transformed[:, reference.constant] = 0.0
    return transformed


def infer_comparative_geometry(
    values: np.ndarray,
    reference: RobustReference,
    *,
    gap_multiplier: float = 3.0,
    span_quantile: float = 0.90,
) -> OccupancyGeometry:
    """Infer geometry in shared reference units without re-scaling each group."""
    if gap_multiplier < 0.0:
        raise ValueError("gap_multiplier must be non-negative")
    if not 0.0 < span_quantile <= 1.0:
        raise ValueError("span_quantile must lie in (0, 1]")
    matrix = transform_with_reference(values, reference)
    delta = matrix[:, None, :] - matrix[None, :, :]
    distances = np.sqrt(np.sum(delta * delta, axis=2))
    upper = distances[np.triu_indices(len(matrix), k=1)]
    positive = upper[upper > 0.0]
    span = float(np.quantile(positive, span_quantile)) if positive.size else 0.0
    edges = minimum_spanning_tree(distances)
    lengths = edges[:, 2]
    mst_length = float(lengths.sum())
    diameter = float(upper.max()) if upper.size else 0.0
    continuity = 1.0 if mst_length == 0.0 else float(diameter / mst_length)
    positive_edges = lengths[lengths > 0.0]
    if positive_edges.size:
        median_edge = float(np.median(positive_edges))
        gap_strength = float(positive_edges.max() / median_edge) if median_edge > 0 else 1.0
    else:
        gap_strength = 1.0
    threshold = _gap_threshold(positive_edges, gap_multiplier)
    labels = _component_labels(len(matrix), edges, threshold)
    return OccupancyGeometry(
        n_occurrences=int(matrix.shape[0]),
        n_features=int(matrix.shape[1]),
        span=span,
        mst_length=mst_length,
        continuity=continuity,
        gap_strength=gap_strength,
        component_count=int(labels.max() + 1),
        labels=labels,
        mst_edges=edges,
    )
