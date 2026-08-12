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


def test_training_presence_cannot_create_its_own_source_signal() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = build_island_isolation_reference_features(prepared, anchors, training, _areas())

    assert result.nearest_training_presence_km[0] == pytest.approx(40.0)
    assert result.nearest_training_presence_km[2] == pytest.approx(40.0)
    assert result.nearest_training_presence_km[1] == pytest.approx(10.0)
    assert result.geography_only_eog_connected_frequency[0] == pytest.approx(0.75)
    assert result.geography_only_eog_connected_frequency[2] == pytest.approx(0.75)
    assert result.geography_only_eog_connected_frequency[1] == pytest.approx(1.0)


def test_multi_source_pressure_and_neutral_geometry_are_separate() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = build_island_isolation_reference_features(prepared, anchors, training, _areas())

    assert result.multi_source_pressure[1] > result.multi_source_pressure[4]
    assert result.nearest_other_island_km.tolist() == pytest.approx([10.0, 10.0, 20.0, 20.0, 50.0])
    assert result.surrounding_island_pressure[1] > 0.0
    assert result.unanchored_component_exposure[4] == pytest.approx((0.0 + 0.25 + 0.0 + 1.0) / 4.0)


def test_area_weighted_pressures_are_distinct_from_count_pressures() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    result = build_island_isolation_reference_features(prepared, anchors, training, _areas())

    # The large area assigned to source c changes the source-pressure ranking/value
    # without altering the unweighted source count-pressure definition.
    assert not np.allclose(result.area_weighted_source_pressure, result.multi_source_pressure)
    assert result.area_weighted_source_pressure[1] > result.multi_source_pressure[1]
    assert not np.allclose(result.surrounding_landmass_pressure, result.surrounding_island_pressure)
    assert result.surrounding_landmass_pressure[3] > result.surrounding_island_pressure[3]


def test_feature_builder_rejects_single_source_after_self_exclusion() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, False, False, False])
    training = np.asarray([True, True, True, False, False])
    with pytest.raises(ValueError, match="at least two outer-training presence anchors"):
        build_island_isolation_reference_features(prepared, anchors, training, _areas())


def test_feature_builder_rejects_invalid_area() -> None:
    prepared = _prepared()
    anchors = np.asarray([True, False, True, False, False])
    training = np.asarray([True, True, True, False, False])
    bad_area = _areas()
    bad_area[2] = 0.0
    with pytest.raises(ValueError, match="island_area_km2"):
        build_island_isolation_reference_features(prepared, anchors, training, bad_area)
