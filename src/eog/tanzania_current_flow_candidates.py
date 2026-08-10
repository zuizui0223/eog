"""Outcome-free Tanzania matrix-aware current-flow candidate generation.

The implementation computes the same effective-resistance estimand used by
raster Circuitscape while making every previously implicit choice explicit:
an eight-neighbour grid, cell values interpreted as resistances, and edge
conductances formed by averaging adjacent cell conductances. Focal IDs are
explicit patch numbers. No species outcome is accepted by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from .tanzania_current_flow_contract import (
    PRIMARY_HELDOUT_AREA_WEIGHT,
    REGION_LANDCOVER_MAPPING,
    SENSITIVITY_HELDOUT_AREA_WEIGHT,
    enumerate_resistance_combinations,
    heldout_area_weight,
)

EXECUTION_SCHEMA_VERSION = "tanzania_current_flow_candidates_v1"
SOURCE_AUDIT_FINGERPRINT = "3ed8ed203fec441deef5eacd9c03cb5055911a859c4b187893c0beefbc7c46da"
COARSENING_FACTOR = 8
N_SHARDS = 16
N_FOCAL_PATCHES = 42
CONNECT_FOUR_NEIGHBORS_ONLY = False
CONNECT_USING_AVG_RESISTANCES = False
HABITAT_MAP_IS_RESISTANCES = True
FOCAL_FIELD = "patch_number"
FLOAT_DECIMALS = 12


def canonical_json(value: object) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def array_sha256(values: np.ndarray, *, decimals: int | None = None) -> str:
    array = np.asarray(values)
    if decimals is not None:
        array = np.round(array.astype(np.float64), decimals=decimals)
    if array.dtype.kind == "f":
        array = np.asarray(array, dtype="<f8")
    elif array.dtype.kind in "iu":
        array = np.asarray(array, dtype="<i8")
    array = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(canonical_json(list(array.shape)).encode("ascii"))
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


@dataclass(frozen=True)
class PreparedCurrentFlowRegion:
    region: str
    classes: np.ndarray
    focal_patch_numbers: np.ndarray
    focal_flat_indices: np.ndarray
    focal_areas_ha: np.ndarray
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.region not in {"E", "W"}:
            raise ValueError(f"unexpected region: {self.region!r}")
        classes = np.asarray(self.classes)
        if classes.ndim != 2 or classes.size < 4:
            raise ValueError("classes must be a two-dimensional raster")
        valid = classes != 255
        if not np.any(valid) or not set(np.unique(classes[valid])).issubset({1, 2, 3, 4}):
            raise ValueError("classes must contain only 1..4 and optional nodata=255")
        patches = np.asarray(self.focal_patch_numbers, dtype=int)
        focals = np.asarray(self.focal_flat_indices, dtype=int)
        areas = np.asarray(self.focal_areas_ha, dtype=float)
        if patches.shape != (N_FOCAL_PATCHES,) or not np.array_equal(
            patches, np.arange(1, N_FOCAL_PATCHES + 1)
        ):
            raise ValueError("focal patch numbers must be 1..42 in order")
        if focals.shape != patches.shape or len(np.unique(focals)) != N_FOCAL_PATCHES:
            raise ValueError("all 42 focal patches must occupy distinct coarse cells")
        if np.any(focals < 0) or np.any(focals >= classes.size):
            raise ValueError("focal indices outside coarse raster")
        if np.any(~valid.ravel()[focals]):
            raise ValueError("focal patches cannot lie on nodata cells")
        if areas.shape != patches.shape or not np.isfinite(areas).all() or np.any(areas <= 0):
            raise ValueError("focal areas must be finite and positive")


def coarsen_categorical_raster(
    values: np.ndarray,
    *,
    factor: int = COARSENING_FACTOR,
    nodata: int = 255,
    focal_fine_cells: Sequence[tuple[int, int]] = (),
) -> tuple[np.ndarray, dict[str, Any]]:
    """Coarsen classes by block mode, then preserve each focal's fine-cell class.

    Class ties are resolved toward the numerically smallest source class. The
    focal override is label-free and prevents small verified source patches
    from disappearing during categorical aggregation.
    """
    array = np.asarray(values)
    if array.ndim != 2 or factor < 1:
        raise ValueError("values must be 2D and factor must be positive")
    valid = array != nodata
    if np.any(~np.isin(array[valid], [1, 2, 3, 4])):
        raise ValueError("available raster cells must use classes 1..4")
    height, width = array.shape
    coarse_height = (height + factor - 1) // factor
    coarse_width = (width + factor - 1) // factor
    padded = np.full(
        (coarse_height * factor, coarse_width * factor), nodata, dtype=array.dtype
    )
    padded[:height, :width] = array
    blocks = padded.reshape(
        coarse_height, factor, coarse_width, factor
    ).transpose(0, 2, 1, 3)
    blocks = blocks.reshape(coarse_height, coarse_width, factor * factor)
    counts = np.stack(
        [(blocks == value).sum(axis=2) for value in (1, 2, 3, 4)], axis=2
    )
    block_valid_count = counts.sum(axis=2)
    coarse = (np.argmax(counts, axis=2) + 1).astype(np.uint8)
    coarse[block_valid_count == 0] = nodata

    coarse_focals: list[tuple[int, int]] = []
    override_count = 0
    for row_raw, col_raw in focal_fine_cells:
        row = int(row_raw)
        col = int(col_raw)
        if not (0 <= row < height and 0 <= col < width) or array[row, col] == nodata:
            raise ValueError("focal fine cell outside available raster")
        coarse_cell = (row // factor, col // factor)
        if coarse_cell in coarse_focals:
            raise ValueError("coarsening collapses multiple focal patches into one cell")
        coarse_focals.append(coarse_cell)
        fine_class = int(array[row, col])
        if int(coarse[coarse_cell]) != fine_class:
            override_count += 1
            coarse[coarse_cell] = fine_class

    tied = np.sum((counts == counts.max(axis=2, keepdims=True)).sum(axis=2) > 1)
    return coarse, {
        "factor": int(factor),
        "fine_shape": [int(height), int(width)],
        "coarse_shape": [int(coarse_height), int(coarse_width)],
        "n_available_coarse_cells": int(np.sum(coarse != nodata)),
        "n_focal_cells": len(coarse_focals),
        "n_focal_class_overrides": int(override_count),
        "n_mode_tie_blocks": int(tied),
        "tie_rule": "smallest_source_class",
        "focal_preservation_rule": (
            "replace coarse focal cell with its verified fine-cell class"
        ),
    }


def resistance_surface(
    classes: np.ndarray,
    region: str,
    combination: Mapping[str, int],
    *,
    nodata: int = 255,
) -> np.ndarray:
    if region not in REGION_LANDCOVER_MAPPING:
        raise ValueError(f"unexpected region: {region!r}")
    expected = {"eucalyptus", "tea", "other_agriculture"}
    if set(combination) != expected:
        raise ValueError("resistance combination must contain the three frozen nonforest axes")
    values = {key: int(value) for key, value in combination.items()}
    if any(value not in {1, 2, 4, 8, 16, 32, 64, 128} for value in values.values()):
        raise ValueError("resistance values outside frozen powers-of-two grid")
    array = np.asarray(classes)
    resistance = np.full(array.shape, np.nan, dtype=float)
    mapping = REGION_LANDCOVER_MAPPING[region]
    for source_class, cover in mapping.items():
        value = 1.0 if cover == "forest" else float(values[cover])
        resistance[array == int(source_class)] = value
    available = array != nodata
    if np.any(~np.isfinite(resistance[available])) or np.any(resistance[available] <= 0):
        raise RuntimeError("failed to map all available source classes to positive resistances")
    return resistance


def build_grid_laplacian(
    resistance: np.ndarray,
    *,
    connect_four_neighbors_only: bool = CONNECT_FOUR_NEIGHBORS_ONLY,
    connect_using_avg_resistances: bool = CONNECT_USING_AVG_RESISTANCES,
) -> tuple[Any, np.ndarray]:
    """Build a sparse conductance Laplacian under explicit Circuitscape semantics."""
    try:
        from scipy import sparse
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scipy is required for current-flow candidate generation") from exc
    values = np.asarray(resistance, dtype=float)
    if values.ndim != 2:
        raise ValueError("resistance must be a two-dimensional raster")
    valid = np.isfinite(values) & (values > 0)
    if np.sum(valid) < 2:
        raise ValueError("at least two available cells are required")
    compact = np.full(values.shape, -1, dtype=np.int64)
    compact[valid] = np.arange(int(np.sum(valid)), dtype=np.int64)

    offsets = [(0, 1, 1.0), (1, 0, 1.0)]
    if not connect_four_neighbors_only:
        offsets.extend([(1, 1, math.sqrt(2.0)), (1, -1, math.sqrt(2.0))])
    all_i: list[np.ndarray] = []
    all_j: list[np.ndarray] = []
    all_g: list[np.ndarray] = []
    height, width = values.shape
    for row_delta, col_delta, distance_multiplier in offsets:
        if col_delta >= 0:
            left = (
                slice(0, height - row_delta),
                slice(0, width - col_delta),
            )
            right = (
                slice(row_delta, height),
                slice(col_delta, width),
            )
        else:
            left = (
                slice(0, height - row_delta),
                slice(-col_delta, width),
            )
            right = (
                slice(row_delta, height),
                slice(0, width + col_delta),
            )
        mask = valid[left] & valid[right]
        if not np.any(mask):
            continue
        source = compact[left][mask]
        target = compact[right][mask]
        source_resistance = values[left][mask]
        target_resistance = values[right][mask]
        if connect_using_avg_resistances:
            conductance = 1.0 / (
                distance_multiplier
                * (source_resistance + target_resistance)
                / 2.0
            )
        else:
            conductance = (
                (1.0 / source_resistance) + (1.0 / target_resistance)
            ) / (2.0 * distance_multiplier)
        all_i.append(source)
        all_j.append(target)
        all_g.append(conductance)
    if not all_i:
        raise ValueError("available raster cells form no graph edges")
    source = np.concatenate(all_i)
    target = np.concatenate(all_j)
    conductance = np.concatenate(all_g)
    n_nodes = int(np.sum(valid))
    diagonal = np.bincount(
        np.concatenate([source, target]),
        weights=np.concatenate([conductance, conductance]),
        minlength=n_nodes,
    )
    rows = np.concatenate([source, target, np.arange(n_nodes, dtype=np.int64)])
    columns = np.concatenate([target, source, np.arange(n_nodes, dtype=np.int64)])
    data = np.concatenate([-conductance, -conductance, diagonal])
    matrix = sparse.coo_matrix(
        (data, (rows, columns)), shape=(n_nodes, n_nodes)
    ).tocsc()
    return matrix, compact


def effective_resistance_matrix(
    laplacian: Any, focal_indices: Sequence[int]
) -> np.ndarray:
    """Compute all focal-pair effective resistances using one grounded factorization."""
    try:
        from scipy.sparse.linalg import splu
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("scipy is required for current-flow candidate generation") from exc
    matrix = laplacian.tocsc()
    focals = np.asarray(focal_indices, dtype=np.int64)
    if focals.ndim != 1 or len(focals) < 2 or len(np.unique(focals)) != len(focals):
        raise ValueError("focal indices must be a unique one-dimensional vector")
    n_nodes = matrix.shape[0]
    if matrix.shape != (n_nodes, n_nodes) or np.any(focals < 0) or np.any(
        focals >= n_nodes
    ):
        raise ValueError("focal indices outside Laplacian")
    ground = int(focals[0])
    keep = np.ones(n_nodes, dtype=bool)
    keep[ground] = False
    reduced = matrix[keep][:, keep]
    reduced_index = np.cumsum(keep, dtype=np.int64) - 1
    focal_reduced = reduced_index[focals[1:]]
    try:
        factor = splu(reduced, permc_spec="COLAMD")
    except RuntimeError as exc:
        raise ValueError(
            "grid Laplacian is singular; focal landscape is disconnected"
        ) from exc
    right_hand_side = np.zeros((n_nodes - 1, len(focal_reduced)), dtype=float)
    right_hand_side[focal_reduced, np.arange(len(focal_reduced))] = 1.0
    solution = factor.solve(right_hand_side)
    grounded_inverse = np.zeros((len(focals), len(focals)), dtype=float)
    grounded_inverse[1:, 1:] = solution[focal_reduced, :]
    diagonal = np.diag(grounded_inverse)
    resistance = diagonal[:, None] + diagonal[None, :] - 2.0 * grounded_inverse
    resistance = (resistance + resistance.T) / 2.0
    tiny_negative = (resistance < 0.0) & (resistance > -1e-9)
    resistance[tiny_negative] = 0.0
    np.fill_diagonal(resistance, 0.0)
    if not np.isfinite(resistance).all() or np.any(resistance < 0.0):
        raise RuntimeError("effective resistance matrix contains invalid values")
    return resistance


def aggregate_isolation(
    pairwise_resistance: np.ndarray,
    source_areas_ha: Sequence[float],
    mode: str,
) -> np.ndarray:
    matrix = np.asarray(pairwise_resistance, dtype=float)
    areas = np.asarray(source_areas_ha, dtype=float)
    if matrix.shape != (len(areas), len(areas)) or len(areas) < 2:
        raise ValueError("pairwise matrix and source areas must align")
    weights = np.asarray(
        [heldout_area_weight(value, mode) for value in areas], dtype=float
    )
    isolation = weights @ matrix
    if not np.isfinite(isolation).all() or np.any(isolation < 0.0):
        raise RuntimeError("aggregated isolation contains invalid values")
    return isolation


def combination_id(index: int, combination: Mapping[str, int]) -> str:
    return (
        f"c{int(index):03d}_e{int(combination['eucalyptus']):03d}"
        f"_t{int(combination['tea']):03d}"
        f"_o{int(combination['other_agriculture']):03d}"
    )


def compute_candidate(
    prepared: PreparedCurrentFlowRegion, candidate_index: int
) -> dict[str, Any]:
    combinations = enumerate_resistance_combinations()
    if not 0 <= int(candidate_index) < len(combinations):
        raise ValueError("candidate_index outside frozen resistance grid")
    combination = combinations[int(candidate_index)]
    surface = resistance_surface(prepared.classes, prepared.region, combination)
    laplacian, compact = build_grid_laplacian(surface)
    coarse_focals = np.asarray(prepared.focal_flat_indices, dtype=np.int64)
    compact_focals = compact.ravel()[coarse_focals]
    if np.any(compact_focals < 0):
        raise RuntimeError("focal patch mapped to unavailable graph cell")
    pairwise = effective_resistance_matrix(laplacian, compact_focals)
    primary = aggregate_isolation(
        pairwise, prepared.focal_areas_ha, PRIMARY_HELDOUT_AREA_WEIGHT
    )
    sensitivity = aggregate_isolation(
        pairwise, prepared.focal_areas_ha, SENSITIVITY_HELDOUT_AREA_WEIGHT
    )
    return {
        "candidate_index": int(candidate_index),
        "candidate_id": combination_id(int(candidate_index), combination),
        "combination": dict(combination),
        "pairwise_resistance": pairwise,
        "isolation_primary": primary,
        "isolation_sensitivity": sensitivity,
    }


def shard_candidate_indices(
    shard_index: int, n_shards: int = N_SHARDS
) -> tuple[int, ...]:
    if n_shards < 1 or not 0 <= shard_index < n_shards:
        raise ValueError("invalid shard declaration")
    n_candidates = len(enumerate_resistance_combinations())
    start = (n_candidates * shard_index) // n_shards
    end = (n_candidates * (shard_index + 1)) // n_shards
    return tuple(range(start, end))


def write_prepared_region(
    path: Path, prepared: PreparedCurrentFlowRegion
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata_json = canonical_json(dict(prepared.metadata))
    np.savez_compressed(
        path,
        region=np.asarray(prepared.region),
        classes=np.asarray(prepared.classes, dtype=np.uint8),
        focal_patch_numbers=np.asarray(
            prepared.focal_patch_numbers, dtype=np.int64
        ),
        focal_flat_indices=np.asarray(
            prepared.focal_flat_indices, dtype=np.int64
        ),
        focal_areas_ha=np.asarray(prepared.focal_areas_ha, dtype=np.float64),
        metadata_json=np.asarray(metadata_json),
    )
    payload = {
        "region": prepared.region,
        "classes_sha256": array_sha256(prepared.classes),
        "focal_patch_numbers_sha256": array_sha256(
            prepared.focal_patch_numbers
        ),
        "focal_flat_indices_sha256": array_sha256(
            prepared.focal_flat_indices
        ),
        "focal_areas_sha256": array_sha256(
            prepared.focal_areas_ha, decimals=FLOAT_DECIMALS
        ),
        "metadata": dict(prepared.metadata),
    }
    return canonical_sha256(payload)


def read_prepared_region(path: Path) -> PreparedCurrentFlowRegion:
    with np.load(path, allow_pickle=False) as data:
        return PreparedCurrentFlowRegion(
            region=str(data["region"].item()),
            classes=np.asarray(data["classes"], dtype=np.uint8),
            focal_patch_numbers=np.asarray(
                data["focal_patch_numbers"], dtype=np.int64
            ),
            focal_flat_indices=np.asarray(
                data["focal_flat_indices"], dtype=np.int64
            ),
            focal_areas_ha=np.asarray(data["focal_areas_ha"], dtype=float),
            metadata=json.loads(str(data["metadata_json"].item())),
        )


def write_candidate_shard(
    path: Path,
    prepared: PreparedCurrentFlowRegion,
    shard_index: int,
    n_shards: int = N_SHARDS,
) -> dict[str, Any]:
    indices = shard_candidate_indices(shard_index, n_shards)
    results = [compute_candidate(prepared, index) for index in indices]
    pairwise = np.stack([row["pairwise_resistance"] for row in results])
    primary = np.stack([row["isolation_primary"] for row in results])
    sensitivity = np.stack(
        [row["isolation_sensitivity"] for row in results]
    )
    combinations = np.asarray(
        [
            [
                row["combination"][axis]
                for axis in ("eucalyptus", "tea", "other_agriculture")
            ]
            for row in results
        ],
        dtype=np.int64,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        region=np.asarray(prepared.region),
        shard_index=np.asarray(shard_index, dtype=np.int64),
        n_shards=np.asarray(n_shards, dtype=np.int64),
        candidate_indices=np.asarray(indices, dtype=np.int64),
        combinations=combinations,
        pairwise_resistance=pairwise,
        isolation_primary=primary,
        isolation_sensitivity=sensitivity,
    )
    manifest = {
        "schema_version": EXECUTION_SCHEMA_VERSION,
        "region": prepared.region,
        "shard_index": int(shard_index),
        "n_shards": int(n_shards),
        "n_candidates": len(indices),
        "candidate_indices": list(indices),
        "candidate_indices_sha256": array_sha256(
            np.asarray(indices, dtype=np.int64)
        ),
        "combinations_sha256": array_sha256(combinations),
        "pairwise_resistance_sha256": array_sha256(
            pairwise, decimals=FLOAT_DECIMALS
        ),
        "isolation_primary_sha256": array_sha256(
            primary, decimals=FLOAT_DECIMALS
        ),
        "isolation_sensitivity_sha256": array_sha256(
            sensitivity, decimals=FLOAT_DECIMALS
        ),
        "scientific_boundary": {
            "species_outcomes_inspected": False,
            "current_flow_computed": True,
            "resistance_selected": False,
            "occurrence_model_fitted": False,
            "eog_performance_inspected": False,
        },
    }
    manifest["shard_fingerprint"] = canonical_sha256(manifest)
    return manifest
