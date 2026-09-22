from benchmarks.eogwf_v2_cross_system_preflight import run_benchmark


def test_v2_cross_system_preflight_separates_structural_predictive_and_authorized_states():
    result = run_benchmark()

    assert result["uses_biological_response"] is False
    assert result["uses_historical_predictive_scores"] is False
    assert result["reruns_frozen_endpoints"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["system_count"] == 3
    assert result["distinct_disposition_count"] == 3

    stoc = result["systems"]["stoc"]
    assert stoc["disposition"] == "stop_before_response_structural_scale"
    assert stoc["historical_q90_largest_component_fraction"] < 0.1
    assert stoc["v2_domain_target_fraction"] == 0.9
    assert stoc["response_blind_bracketing_largest_component_fraction"] >= 0.9

    louisiana = result["systems"]["louisiana"]
    assert louisiana["disposition"] == "predictive_outcome_authorized"
    assert louisiana["node_count"] == 33
    assert louisiana["surveyed_unit_count"] == 660
    assert louisiana["initialization_unit_count"] == 33
    assert louisiana["scored_candidate_count"] == 627
    assert louisiana["predictive_state_status"] == "predictive_complement_candidate"

    tampa = result["systems"]["tampa"]
    assert (
        tampa["disposition"]
        == "response_ready_but_layer_b_prediction_blocked"
    )
    assert tampa["historical_gate0_ready"] is True
    assert tampa["node_count"] == 71
    assert tampa["candidate_unit_count"] == 1497
    assert tampa["predictive_state_status"] == "ineligible_generation_shift"
    assert "train_and_serve_feature_generators_differ" in tampa["reasons"]
