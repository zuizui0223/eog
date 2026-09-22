from benchmarks.algar_coordinate_contract_replay import run_replay


def test_algar_historical_coordinate_stop_remains_a_real_registry_failure():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["reruns_frozen_endpoint"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["passes_frozen_tolerance"] is False
    assert result["passes_0_01_degree_tolerance"] is False
    assert result["minimum_axis_tolerance_to_accept_degrees"] > 0.9
    assert result["first_to_second_displacement_km"] > 50
    assert result["classification"] == "large_registry_discontinuity_not_interface_noise"
