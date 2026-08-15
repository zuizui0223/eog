import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/mce_environmental_exposure_boundary.py")
    return namespace["run_mce_environmental_exposure_boundary"]()


def test_mce_boundary_records_primary_reference():
    boundary = _benchmark()["literature_boundary"]
    assert boundary["method"] == "minimum cumulative exposure / minimum exposure least-cost path"
    assert boundary["reference"] == "Dobrowski & Parks 2016, Nature Communications 7:12349"
    assert boundary["doi"] == "10.1038/ncomms12349"


def test_equal_climate_endpoints_can_have_nonzero_intermediate_exposure():
    truth = _benchmark()["known_truth"]
    assert truth["endpoint_temperature_difference"] == pytest.approx(0.0)
    assert truth["shortest_distance_path"] == ["A", "B", "C"]
    assert truth["shortest_distance"] == pytest.approx(2.0)
    assert truth["exposure_of_shortest_distance_path"] == pytest.approx(2.0)


def test_minimum_exposure_route_can_be_longer_than_shortest_distance_route():
    truth = _benchmark()["known_truth"]
    assert truth["minimum_exposure_path"] == ["A", "D", "E", "C"]
    assert truth["minimum_cumulative_exposure"] == pytest.approx(0.4)
    assert truth["length_of_minimum_exposure_path"] == pytest.approx(3.0)
    assert truth["longer_path_has_lower_exposure"] is True


def test_existing_eog_bridge_recovers_same_pure_environmental_least_exposure_path():
    result = _benchmark()
    bridge = result["eog_existing_bridge"]
    boundary = result["negative_boundary"]

    assert bridge["minimum_environmental_path"] == ["A", "D", "E", "C"]
    assert bridge["minimum_environmental_cost"] == pytest.approx(0.4)
    assert bridge["geographic_length_of_environmental_path"] == pytest.approx(3.0)
    assert boundary["minimum_exposure_path_matches"] is True
    assert boundary["minimum_cumulative_exposure_matches"] is True


def test_path_environmental_exposure_is_removed_from_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["endpoint_similarity_does_not_imply_zero_path_exposure"] is True
    assert boundary["do_not_claim_path_environmental_exposure_as_unique"] is True
    assert boundary["do_not_claim_least_exposure_route_as_unique"] is True
    assert "occurrence-conditioned multi-axis relaxation Pareto sets" in boundary[
        "remaining_layers_to_validate"
    ]
