from benchmarks.layer_b_v2_known_truth_factorial import run_benchmark


def test_frozen_layer_b_v2_known_truth_factorial():
    result = run_benchmark()
    assert result["counts_as_fresh_predictive_endpoint"] is False
    assert result["uses_biological_response"] is False
    assert result["eligibility"]["tampa_like"]["status"] == "ineligible_generation_shift"
    assert result["eligibility"]["matched_sequential"]["status"] == "predictive_complement_candidate"
    assert result["refresh"]["static"]["refresh_fraction"] == 0.0
    assert result["refresh"]["sequential"]["refresh_fraction"] == 1.0
    assert result["source_symmetric_invariance"]["feature_fingerprint_equal"] is True
    assert result["worldsets"]["saturated"]["fully_saturated_context_fraction"] == 1.0
    assert result["worldsets"]["falsified"]["terminal_universe_falsified"] is True
