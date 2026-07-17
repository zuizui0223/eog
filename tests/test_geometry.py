import numpy as np
import pytest

from eog import (
    OccupancyGeometry,
    infer_occupancy_geometry,
    minimum_spanning_tree,
    pairwise_distances,
    project_states,
    robust_scale,
)


def test_invariant_to_feature_units_and_offsets():
    values = np.array([[0.0, 2.0], [0.2, 2.2], [3.0, 8.0], [3.2, 8.2]])
    transformed = values * np.array([1000.0, 0.01]) + np.array([50.0, -4.0])
    first = infer_occupancy_geometry(values)
    second = infer_occupancy_geometry(transformed)
    assert first.span == pytest.approx(second.span)
    assert first.continuity == pytest.approx(second.continuity)
    assert first.gap_strength == pytest.approx(second.gap_strength)
    np.testing.assert_array_equal(first.labels, second.labels)


def test_two_modes_are_separated_by_large_gap():
    values = np.array([
        [0.0, 0.0], [0.1, -0.1], [-0.1, 0.1],
        [8.0, 8.0], [8.1, 7.9], [7.9, 8.1],
    ])
    geometry = infer_occupancy_geometry(values, gap_multiplier=2.0)
    assert geometry.component_count == 2
    assert geometry.gap_strength > 10.0
    assert len(set(geometry.labels[:3])) == 1
    assert len(set(geometry.labels[3:])) == 1
    assert geometry.labels[0] != geometry.labels[3]


def test_public_result_fields_are_stable():
    geometry = infer_occupancy_geometry(np.array([[0.0], [1.0], [2.0]]))
    assert isinstance(geometry, OccupancyGeometry)
    assert tuple(geometry.__dataclass_fields__) == (
        "n_occurrences", "n_features", "span", "mst_length", "continuity",
        "gap_strength", "component_count", "labels", "mst_edges",
    )


def test_one_dimensional_input_is_supported():
    geometry = infer_occupancy_geometry(np.array([[0.0], [1.0], [2.0], [3.0]]))
    assert geometry.n_features == 1
    assert geometry.continuity == pytest.approx(1.0)
    assert geometry.gap_strength == pytest.approx(1.0)


def test_duplicate_and_identical_rows_are_supported():
    duplicate = infer_occupancy_geometry(np.array([[0.0], [0.0], [1.0], [1.0]]))
    assert duplicate.n_occurrences == 4
    assert np.isfinite(duplicate.mst_edges).all()

    identical = infer_occupancy_geometry(np.ones((4, 3), dtype=float))
    assert identical.span == 0.0
    assert identical.mst_length == 0.0
    assert identical.continuity == 1.0
    assert identical.gap_strength == 1.0
    assert identical.component_count == 1


def test_mst_shape_and_total_length_are_stable():
    edges = minimum_spanning_tree(pairwise_distances(np.array([[0.0], [1.0], [2.0]])))
    assert edges.shape == (2, 3)
    assert float(edges[:, 2].sum()) == pytest.approx(2.0 / 1.4826)


def test_projection_and_empty_candidates():
    occurrences = np.array([[0.0], [0.2], [10.0], [10.2]])
    geometry = infer_occupancy_geometry(occurrences, gap_multiplier=2.0)
    distance, label = project_states(occurrences, np.array([[0.1], [10.1], [5.0]]), geometry)
    assert label[0] == geometry.labels[0]
    assert label[1] == geometry.labels[2]
    assert distance[2] > distance[0]
    assert distance[2] > distance[1]

    empty_distance, empty_label = project_states(occurrences, np.empty((0, 1)), geometry)
    assert empty_distance.shape == (0,)
    assert empty_label.shape == (0,)


def test_validation_contract():
    with pytest.raises(ValueError):
        infer_occupancy_geometry(np.array([[1.0, 2.0]]))
    with pytest.raises(ValueError):
        infer_occupancy_geometry(np.array([[0.0], [np.nan]]))
    with pytest.raises(ValueError):
        infer_occupancy_geometry(np.array([[0.0], [1.0]]), gap_multiplier=-1.0)
    for invalid in (0.0, -0.1, 1.1):
        with pytest.raises(ValueError):
            infer_occupancy_geometry(np.array([[0.0], [1.0]]), span_quantile=invalid)


def test_constant_features_are_neutral():
    values = np.array([[0.0, 4.0], [1.0, 4.0], [2.0, 4.0]])
    scaled = robust_scale(values)
    assert np.allclose(scaled[:, 1], 0.0)
    assert np.isfinite(pairwise_distances(values)).all()
