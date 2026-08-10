from __future__ import annotations

import math

import numpy as np
import pytest

pytest.importorskip("scipy")

from eog.tanzania_current_flow_candidates import (
    PreparedCurrentFlowRegion,
    aggregate_isolation,
    build_grid_laplacian,
    coarsen_categorical_raster,
    compute_candidate,
    effective_resistance_matrix,
    resistance_surface,
    shard_candidate_indices,
)
from eog.tanzania_current_flow_contract import (
    PRIMARY_HELDOUT_AREA_WEIGHT,
    SENSITIVITY_HELDOUT_AREA_WEIGHT,
)


def _focal_indices(compact: np.ndarray, cells: list[tuple[int, int]]) -> np.ndarray:
    return np.asarray([compact[cell] for cell in cells], dtype=int)


def test_unit_resistance_line_has_exact_pairwise_values() -> None:
    laplacian, compact = build_grid_laplacian(np.ones((1, 3)), connect_four_neighbors_only=True)
    observed = effective_resistance_matrix(laplacian, _focal_indices(compact, [(0, 0), (0, 1), (0, 2)]))
    expected = np.asarray([[0.0, 1.0, 2.0], [1.0, 0.0, 1.0], [2.0, 1.0, 0.0]])
    assert np.allclose(observed, expected, atol=1e-10)


def test_unit_square_matches_cycle_effective_resistance() -> None:
    laplacian, compact = build_grid_laplacian(np.ones((2, 2)), connect_four_neighbors_only=True)
    observed = effective_resistance_matrix(
        laplacian,
        _focal_indices(compact, [(0, 0), (0, 1), (1, 1), (1, 0)]),
    )
    assert observed[0, 1] == pytest.approx(0.75)
    assert observed[0, 2] == pytest.approx(1.0)


def test_average_conductance_and_average_resistance_are_distinct() -> None:
    values = np.asarray([[1.0, 3.0]])
    lap_conductance, compact = build_grid_laplacian(
        values,
        connect_four_neighbors_only=True,
        connect_using_avg_resistances=False,
    )
    lap_resistance, _ = build_grid_laplacian(
        values,
        connect_four_neighbors_only=True,
        connect_using_avg_resistances=True,
    )
    focals = _focal_indices(compact, [(0, 0), (0, 1)])
    assert effective_resistance_matrix(lap_conductance, focals)[0, 1] == pytest.approx(1.5)
    assert effective_resistance_matrix(lap_resistance, focals)[0, 1] == pytest.approx(2.0)


def test_region_specific_source_class_mapping() -> None:
    classes = np.asarray([[1, 2, 3, 4]], dtype=np.uint8)
    combination = {"eucalyptus": 8, "tea": 16, "other_agriculture": 32}
    assert resistance_surface(classes, "E", combination).tolist() == [[32.0, 1.0, 16.0, 8.0]]
    assert resistance_surface(classes, "W", combination).tolist() == [[32.0, 8.0, 1.0, 16.0]]


def test_focal_preserving_mode_and_collision_guard() -> None:
    raster = np.asarray(
        [
            [2, 3, 3, 3],
            [3, 3, 3, 3],
            [1, 1, 4, 4],
            [1, 1, 4, 4],
        ],
        dtype=np.uint8,
    )
    coarse, audit = coarsen_categorical_raster(raster, factor=2, focal_fine_cells=[(0, 0), (3, 3)])
    assert coarse.tolist() == [[2, 3], [1, 4]]
    assert audit["n_focal_class_overrides"] == 1
    with pytest.raises(ValueError, match="collapses multiple focal"):
        coarsen_categorical_raster(raster, factor=4, focal_fine_cells=[(0, 0), (3, 3)])


def test_area_weighted_isolation_uses_source_axis() -> None:
    pairwise = np.asarray([[0.0, 1.0], [1.0, 0.0]])
    primary = aggregate_isolation(pairwise, [1.0, 9.0], PRIMARY_HELDOUT_AREA_WEIGHT)
    sensitivity = aggregate_isolation(pairwise, [1.0, 9.0], SENSITIVITY_HELDOUT_AREA_WEIGHT)
    assert primary[0] == pytest.approx(1.0 / math.log10(10.0))
    assert primary[1] == pytest.approx(1.0 / math.log10(2.0))
    assert sensitivity.tolist() == pytest.approx([1.0 / 9.0, 1.0])


def test_shards_cover_all_candidates_once() -> None:
    values = [index for shard in range(16) for index in shard_candidate_indices(shard, 16)]
    assert values == list(range(512))


def test_candidate_generation_is_deterministic_without_outcomes() -> None:
    classes = np.full((6, 7), 2, dtype=np.uint8)
    prepared = PreparedCurrentFlowRegion(
        region="E",
        classes=classes,
        focal_patch_numbers=np.arange(1, 43),
        focal_flat_indices=np.arange(42),
        focal_areas_ha=np.linspace(1.1, 43.0, 42),
        metadata={"synthetic": True},
    )
    first = compute_candidate(prepared, 0)
    second = compute_candidate(prepared, 0)
    assert first["candidate_id"] == "c000_e001_t001_o001"
    assert np.array_equal(first["pairwise_resistance"], second["pairwise_resistance"])
    assert np.array_equal(first["isolation_primary"], second["isolation_primary"])
    assert first["pairwise_resistance"].shape == (42, 42)
