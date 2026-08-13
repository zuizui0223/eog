"""Explicit island-level viability, reachability, and persistence layers for EOG-R.

The module keeps node-level ecological roles separate. In particular, island area may
be transformed into a target-capture support and a persistence support with different,
predeclared scales. Neither quantity is an occupancy or colonisation probability.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class AreaSupportDeclaration:
    """Independent half-saturation scales for area-related ecological roles."""

    capture_half_saturation_area: float
    persistence_half_saturation_area: float

    def __post_init__(self) -> None:
        values = (self.capture_half_saturation_area, self.persistence_half_saturation_area)
        if not all(np.isfinite(values)) or any(value <= 0.0 for value in values):
            raise ValueError("area half-saturation scales must be finite and positive")


@dataclass(frozen=True)
class AreaSupportResult:
    area: np.ndarray
    target_capture_support: np.ndarray
    persistence_support: np.ndarray
    declaration: AreaSupportDeclaration
    fingerprint: str


@dataclass(frozen=True)
class IslandStateLayers:
    """Auditable V/R/P layers without an implicit fusion rule."""

    node_ids: tuple[str, ...]
    viability_support: np.ndarray
    reachability_support: np.ndarray
    persistence_support: np.ndarray
    observation_support: np.ndarray | None
    state_class: tuple[str, ...]
    viability_threshold: float
    reachability_threshold: float
    fingerprint: str


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _support_vector(values: Sequence[float], n: int, label: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (n,) or not np.isfinite(result).all():
        raise ValueError(f"{label} must contain one finite value per node")
    if np.any((result < 0.0) | (result > 1.0)):
        raise ValueError(f"{label} must lie in [0, 1]")
    return result


def area_support_layers(
    area: Sequence[float],
    declaration: AreaSupportDeclaration,
) -> AreaSupportResult:
    """Convert island area into two deliberately separate saturating support layers.

    For either ecological role, ``support = area / (area + half_saturation_area)``.
    The scales are independent declarations because interception/capture during arrival
    and post-arrival persistence are not the same process. The transform is a
    sensitivity-ready support convention, not a fitted demographic relationship.
    """

    values = np.asarray(area, dtype=float)
    if values.ndim != 1 or values.size < 1 or not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("area must be a finite non-negative one-dimensional vector")
    capture = values / (values + declaration.capture_half_saturation_area)
    persistence = values / (values + declaration.persistence_half_saturation_area)
    payload = {
        "area": values.tolist(),
        "capture_half_saturation_area": declaration.capture_half_saturation_area,
        "persistence_half_saturation_area": declaration.persistence_half_saturation_area,
        "target_capture_support": capture.tolist(),
        "persistence_support": persistence.tolist(),
    }
    return AreaSupportResult(
        area=values,
        target_capture_support=capture,
        persistence_support=persistence,
        declaration=declaration,
        fingerprint=_sha256(payload),
    )


def assemble_island_state_layers(
    node_ids: Sequence[str],
    viability_support: Sequence[float],
    reachability_support: Sequence[float],
    persistence_support: Sequence[float],
    *,
    viability_threshold: float,
    reachability_threshold: float,
    observation_support: Sequence[float] | None = None,
) -> IslandStateLayers:
    """Assemble V/R/P layers and classify viability-reachability mismatch states.

    The function intentionally does **not** return a combined occupancy-like score.
    ``state_class`` is based only on predeclared V and R thresholds; persistence and
    observation remain separately reportable attributes.
    """

    ids = tuple(str(value) for value in node_ids)
    if not ids or len(set(ids)) != len(ids) or any(not value.strip() for value in ids):
        raise ValueError("node_ids must be unique non-empty strings")
    n = len(ids)
    viability = _support_vector(viability_support, n, "viability_support")
    reachability = _support_vector(reachability_support, n, "reachability_support")
    persistence = _support_vector(persistence_support, n, "persistence_support")
    if not np.isfinite(viability_threshold) or not 0.0 <= viability_threshold <= 1.0:
        raise ValueError("viability_threshold must lie in [0, 1]")
    if not np.isfinite(reachability_threshold) or not 0.0 <= reachability_threshold <= 1.0:
        raise ValueError("reachability_threshold must lie in [0, 1]")
    observation = None
    if observation_support is not None:
        observation = _support_vector(observation_support, n, "observation_support")

    classes: list[str] = []
    for viability_value, reachability_value in zip(viability, reachability):
        high_v = viability_value >= viability_threshold
        high_r = reachability_value >= reachability_threshold
        if high_v and high_r:
            classes.append("high_viability_high_reachability")
        elif high_v:
            classes.append("high_viability_low_reachability")
        elif high_r:
            classes.append("low_viability_high_reachability")
        else:
            classes.append("low_viability_low_reachability")

    payload = {
        "node_ids": list(ids),
        "viability_support": viability.tolist(),
        "reachability_support": reachability.tolist(),
        "persistence_support": persistence.tolist(),
        "observation_support": None if observation is None else observation.tolist(),
        "state_class": classes,
        "viability_threshold": float(viability_threshold),
        "reachability_threshold": float(reachability_threshold),
    }
    return IslandStateLayers(
        node_ids=ids,
        viability_support=viability,
        reachability_support=reachability,
        persistence_support=persistence,
        observation_support=observation,
        state_class=tuple(classes),
        viability_threshold=float(viability_threshold),
        reachability_threshold=float(reachability_threshold),
        fingerprint=_sha256(payload),
    )
