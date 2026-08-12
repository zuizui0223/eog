"""Leakage-safe reference features for the A-Islands isolation-adequacy extension.

The feature family is frozen by
``docs/aislands_isolation_adequacy_preoutcome_contract.md``.  It deliberately
separates direct source proximity, multi-source pressure, source landmass,
species-independent archipelago geometry, and species-conditioned EOG reachability.

None of these quantities is a dispersal or colonisation probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .prepared_island_connectivity import PreparedIslandConnectivity


AISLANDS_ISOLATION_SCALES_KM = (25.0, 50.0, 125.0, 250.0)


@dataclass(frozen=True)
class IslandIsolationReferenceFeatures:
    """Frozen spatial features for one species × outer-fold anchor set."""

    nearest_training_presence_km: np.ndarray
    multi_source_pressure: np.ndarray
    area_weighted_source_pressure: np.ndarray
    nearest_other_island_km: np.ndarray
    surrounding_island_pressure: np.ndarray
    surrounding_landmass_pressure: np.ndarray
    unanchored_component_exposure: np.ndarray
    geography_only_eog_connected_frequency: np.ndarray


def _validate_scales(scales_km: Sequence[float]) -> np.ndarray:
    scales = np.asarray(tuple(scales_km), dtype=float)
    if scales.ndim != 1 or scales.size < 1 or not np.isfinite(scales).all():
        raise ValueError("scales_km must be a finite non-empty vector")
    if np.any(scales <= 0):
        raise ValueError("all scales_km must be positive")
    return scales


def _kernel_pressure(
    distances: np.ndarray,
    scales: np.ndarray,
    *,
    source_weights: np.ndarray | None = None,
) -> np.ndarray:
    """Mean log-one-plus exponential pressure over the frozen scale ensemble."""
    if distances.ndim != 2:
        raise ValueError("distances must be a row-by-source matrix")
    if source_weights is None:
        weights_vector = np.ones(distances.shape[1], dtype=float)
    else:
        weights_vector = np.asarray(source_weights, dtype=float)
        if weights_vector.shape != (distances.shape[1],):
            raise ValueError("source_weights must align with distance columns")
        if not np.isfinite(weights_vector).all() or np.any(weights_vector <= 0):
            raise ValueError("source_weights must be finite and positive")

    values = []
    for scale in scales:
        kernel = np.exp(-distances / float(scale))
        kernel[~np.isfinite(distances)] = 0.0
        values.append(np.log1p(np.sum(kernel * weights_vector[None, :], axis=1)))
    return np.mean(np.vstack(values), axis=0)


def build_island_isolation_reference_features(
    prepared: PreparedIslandConnectivity,
    anchor_mask: Sequence[bool],
    self_exclusion_mask: Sequence[bool],
    island_area_km2: Sequence[float],
    *,
    scales_km: Sequence[float] = AISLANDS_ISOLATION_SCALES_KM,
) -> IslandIsolationReferenceFeatures:
    """Build the frozen strong-isolation reference and EOG probe features.

    Parameters
    ----------
    prepared:
        Outcome-independent island geometry/scenario components for the outer fold.
    anchor_mask:
        Outer-training presence islands for the focal species.
    self_exclusion_mask:
        Rows whose own occurrence must not act as a source when their feature is used
        for fitting.  In the planned benchmark this is ``training_mask``: for an
        outer-training presence the diagonal source contribution is removed; for a
        training absence the operation is a no-op; held-out rows are not sources and
        therefore need no special handling.
    island_area_km2:
        Positive polygon areas recovered from the frozen A-Islands v1.0 shapefile.
        They weight source-landmass and surrounding-landmass pressure only; the EOG
        graph itself remains the predeclared unweighted geographic graph.
    scales_km:
        Must remain the predeclared 25/50/125/250-km ensemble in the authoritative
        extension runner.  The argument exists for synthetic tests only.
    """
    n = len(prepared.node_ids)
    anchors = np.asarray(anchor_mask, dtype=bool)
    exclude_self = np.asarray(self_exclusion_mask, dtype=bool)
    areas = np.asarray(island_area_km2, dtype=float)
    if anchors.shape != (n,) or exclude_self.shape != (n,):
        raise ValueError("anchor and self-exclusion masks must align with prepared nodes")
    if areas.shape != (n,) or not np.isfinite(areas).all() or np.any(areas <= 0):
        raise ValueError("island_area_km2 must be finite, positive and align with prepared nodes")
    if np.sum(anchors) < 2:
        raise ValueError("at least two outer-training presence anchors are required")
    scales = _validate_scales(scales_km)

    geographic = np.asarray(prepared.geographic_distance_km, dtype=float)
    if geographic.shape != (n, n) or not np.isfinite(geographic).all():
        raise ValueError("prepared geographic distance matrix must be finite and square")
    if not np.allclose(geographic, geographic.T, atol=1e-12):
        raise ValueError("prepared geographic distances must be symmetric")

    anchor_indices = np.flatnonzero(anchors)
    source_distances = geographic[:, anchor_indices].copy()
    anchor_column = {int(node): col for col, node in enumerate(anchor_indices)}
    for node in np.flatnonzero(exclude_self & anchors):
        source_distances[int(node), anchor_column[int(node)]] = np.inf

    nearest_source = np.min(source_distances, axis=1)
    if not np.isfinite(nearest_source).all():
        raise ValueError("self exclusion left at least one row without another source")
    source_pressure = _kernel_pressure(source_distances, scales)
    area_weighted_source_pressure = _kernel_pressure(
        source_distances,
        scales,
        source_weights=areas[anchor_indices],
    )

    all_other = geographic.copy()
    np.fill_diagonal(all_other, np.inf)
    nearest_other = np.min(all_other, axis=1)
    if not np.isfinite(nearest_other).all():
        raise ValueError("nearest-other-island distance is not finite")
    surrounding_pressure = _kernel_pressure(all_other, scales)
    surrounding_landmass_pressure = _kernel_pressure(
        all_other,
        scales,
        source_weights=areas,
    )

    geo_indices = [
        index
        for index, scenario_id in enumerate(prepared.scenario_ids)
        if scenario_id.endswith("env_none")
    ]
    if not geo_indices:
        raise ValueError("prepared geometry contains no geography-only scenarios")

    component_exposure_rows: list[np.ndarray] = []
    eog_reach_rows: list[np.ndarray] = []
    for index in geo_indices:
        labels = np.asarray(prepared.component_labels[index], dtype=int)
        if labels.shape != (n,) or np.any(labels < 0):
            raise ValueError("component labels must align and be non-negative")
        component_sizes = np.bincount(labels)
        component_exposure_rows.append((component_sizes[labels] - 1.0) / (n - 1.0))

        anchor_counts = np.bincount(labels[anchors], minlength=len(component_sizes))
        effective_anchor_count = anchor_counts[labels].astype(int)
        effective_anchor_count -= (anchors & exclude_self).astype(int)
        eog_reach_rows.append((effective_anchor_count > 0).astype(float))

    component_exposure = np.mean(np.vstack(component_exposure_rows), axis=0)
    geography_eog = np.mean(np.vstack(eog_reach_rows), axis=0)

    return IslandIsolationReferenceFeatures(
        nearest_training_presence_km=nearest_source,
        multi_source_pressure=source_pressure,
        area_weighted_source_pressure=area_weighted_source_pressure,
        nearest_other_island_km=nearest_other,
        surrounding_island_pressure=surrounding_pressure,
        surrounding_landmass_pressure=surrounding_landmass_pressure,
        unanchored_component_exposure=component_exposure,
        geography_only_eog_connected_frequency=geography_eog,
    )
