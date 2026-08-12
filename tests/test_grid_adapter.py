import numpy as np
import pytest

from eog.distribution import EOGDistributionPrediction
from eog.grid_adapter import build_regular_grid_nodes, prediction_field_to_grid


def _prediction(node_ids, values):
    array = np.asarray(values, dtype=float)
    zeros = np.zeros_like(array)
    return EOGDistributionPrediction(
        node_ids=tuple(node_ids),
        environmental_support=array,
        structural_accessibility=array,
        minimum_cumulative_cost=zeros,
        minimum_bottleneck_cost=zeros,
        secondary_source_cost=zeros,
        source_redundancy=zeros,
        distribution_support=array,
    )


def test_regular_grid_adapter_builds_deterministic_nodes_and_roundtrips_values():
    latitude = np.asarray([35.0, 35.1])
    longitude = np.asarray([139.0, 139.1, 139.2])
    predictors = np.dstack(
        [
            np.asarray([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
            np.asarray([[10.0, 20.0, 30.0], [40.0, 50.0, 60.0]]),
        ]
    )
    available = np.asarray([[True, False, True], [True, True, True]])

    nodes, index = build_regular_grid_nodes(
        latitude,
        longitude,
        predictors,
        available_mask=available,
        node_prefix="g",
    )

    assert index.shape == (2, 3)
    assert index.node_ids == (
        "g_r0000c0000",
        "g_r0000c0002",
        "g_r0001c0000",
        "g_r0001c0001",
        "g_r0001c0002",
    )
    assert index.node_id_at(1, 1) == "g_r0001c0001"
    with pytest.raises(KeyError):
        index.node_id_at(0, 1)

    assert nodes[0].latitude == 35.0
    assert nodes[0].longitude == 139.0
    assert nodes[0].environmental_state == (1.0, 10.0)

    restored = index.values_to_grid(np.arange(5.0))
    assert np.isnan(restored[0, 1])
    assert restored[1, 2] == 4.0


def test_prediction_field_to_grid_aligns_by_node_id_not_input_order():
    latitude = np.asarray([0.0, 0.1])
    longitude = np.asarray([10.0, 10.1])
    predictors = np.asarray([[0.2, 0.3], [0.4, 0.5]])
    _, index = build_regular_grid_nodes(latitude, longitude, predictors)
    reversed_ids = tuple(reversed(index.node_ids))
    prediction = _prediction(reversed_ids, [4.0, 3.0, 2.0, 1.0])

    grid = prediction_field_to_grid(prediction, index)
    assert np.array_equal(grid, np.asarray([[1.0, 2.0], [3.0, 4.0]]))


def test_regular_grid_adapter_ignores_nonfinite_values_only_on_unavailable_cells():
    latitude = np.asarray([0.0, 0.1])
    longitude = np.asarray([10.0, 10.1])
    predictors = np.asarray([[0.2, np.nan], [0.4, 0.5]])
    available = np.asarray([[True, False], [True, True]])
    nodes, _ = build_regular_grid_nodes(
        latitude,
        longitude,
        predictors,
        available_mask=available,
    )
    assert len(nodes) == 3

    with pytest.raises(ValueError, match="predictors must be finite"):
        build_regular_grid_nodes(latitude, longitude, predictors)
