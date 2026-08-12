import numpy as np
import pytest

from eog.island_isolation_reference import build_island_isolation_reference_features
from eog.prepared_island_connectivity import PreparedIslandConnectivity


def _prepared() -> PreparedIslandConnectivity:
    distance = np.asarray(
        [
            [0.0, 10.0, 40.0, 60.0, 100.0],
            [10.0, 0.0, 30.0, 50.0, 90.0],
            [40.0, 30.0, 0.0, 20.0, 70.0],
            [60.0, 50.0, 20.0, 0.0, 50.0],
            [100.0, 90.0, 70.0, 50.0, 0.0],
        ]
    )
    return PreparedIslandConnectivity(
        node_ids=("a", "b", "c", "d", "e"),
        geographic_distance_km=distance,
        scenario_ids=(
            "g25_env_none",
            "g50_env_none",
            "g125_env_none",
            "g250_env_none",
        ),
        component_labels=(
            np.asarray([0, 0, 1, 1, 2]),
            np.asarray([0, 0, 0, 1, 1]),
            np.asarray([0, 0, 0, 0, 1]),
            np.asarray([0, 0, 0, 0, 0]),
        ),
    )


def _areas() -> np.ndarray:
    return np.asarray([1.0, 2.0, 100.0, 4.0, 5.0])


def _mainland_distances() -> np.ndarray:
    # a is a direct mainland-entry island at every scale; c becomes a direct
    # entry at 125 km. Other targets may still become mainland-connected through
    # their species-independent island component.
    return np.asarray([10.0, 80.0, 100.0, 300.0, 400.0])


def _build(anchors, training):
    return build_island_isolation_reference_features(
        _prepared(),
        anchors,
        training,
        _areas(),
        _mainland_distances(),
    )


def test_training_presence_cannot_create_its_own_source_signal() -> None:
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = _build(anchors, training)

    assert result.nearest_training_presence_km[0] == pytest.approx(40.0)
    assert result.nearest_training_presence_km[2] == pytest.approx(40.0)
    assert result.nearest_training_presence_km[1] == pytest.approx(10.0)
    assert result.geography_only_eog_connected_frequency[0] == pytest.approx(0.75)
    assert result.geography_only_eog_connected_frequency[2] == pytest.approx(0.75)
    assert result.geography_only_eog_connected_frequency[1] == pytest.approx(1.0)


def test_multi_source_pressure_and_neutral_geometry_are_separate() -> None:
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = _build(anchors, training)

    assert result.multi_source_pressure[1] > result.multi_source_pressure[4]
    assert result.nearest_other_island_km.tolist() == pytest.approx([10.0, 10.0, 20.0, 20.0, 50.0])
    assert result.surrounding_island_pressure[1] > 0.0
    assert result.unanchored_component_exposure[4] == pytest.approx((0.0 + 0.25 + 0.0 + 1.0) / 4.0)


def test_area_weighted_pressures_are_distinct_from_count_pressures() -> None:
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = _build(anchors, training)

    assert not np.allclose(result.area_weighted_source_pressure, result.multi_source_pressure)
    assert result.area_weighted_source_pressure[1] > result.multi_source_pressure[1]
    assert not np.allclose(result.surrounding_landmass_pressure, result.surrounding_island_pressure)
    assert result.surrounding_landmass_pressure[3] > result.surrounding_island_pressure[3]


def test_mainland_stepping_stone_frequency_is_species_independent() -> None:
    anchors_a = np.asarray([True, False, True, False, False])
    anchors_b = np.asarray([False, True, False, True, False])
    training = np.asarray([True, True, True, True, False])
    result_a = _build(anchors_a, training)
    result_b = _build(anchors_b, training)

    # Radius 25: a,b are connected to the direct mainland-entry island a; c,d,e are not.
    # Radius 50: a,b,c share a component containing a; d,e do not.
    # Radius 125: a,b,c,d are connected and c is also a direct entry; e is not.
    # Radius 250: all islands form one component containing mainland-entry islands.
    expected = np.asarray([1.0, 1.0, 0.75, 0.5, 0.25])
    assert result_a.mainland_stepping_stone_frequency == pytest.approx(expected)
    assert result_b.mainland_stepping_stone_frequency == pytest.approx(expected)
    assert not np.allclose(
        result_a.geography_only_eog_connected_frequency,
        result_b.geography_only_eog_connected_frequency,
    )


def test_feature_builder_rejects_single_source_after_self_exclusion() -> None:
    anchors = np.asarray([True, False, False, False, False])
    training = np.asarray([True, True, True, False, False])
    with pytest.raises(ValueError, match="at least two outer-training presence anchors"):
        _build(anchors, training)


def test_feature_builder_rejects_invalid_area() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    bad_area = _areas()
    bad_area[2] = 0.0
    with pytest.raises(ValueError, match="island_area_km2"):
        build_island_isolation_reference_features(
            prepared,
            anchors,
            training,
            bad_area,
            _mainland_distances(),
        )


def test_feature_builder_rejects_invalid_mainland_distance() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    bad_distance = _mainland_distances()
    bad_distance[4] = -1.0
    with pytest.raises(ValueError, match="distance_to_mainland_km"):
        build_island_isolation_reference_features(
            prepared,
            anchors,
            training,
            _areas(),
            bad_distance,
        )
