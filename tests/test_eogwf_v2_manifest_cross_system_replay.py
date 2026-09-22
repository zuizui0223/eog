from benchmarks.eogwf_v2_manifest_cross_system_replay import run_replay


def test_same_manifest_contract_makes_system_specific_prediction_decisions():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert (
        result["genericity_result"]
        == "same_pre_response_contract_supports_system_specific_prediction_decisions"
    )

    louisiana = result["systems"]["southwest_louisiana_passive_acoustics"]
    tampa = result["systems"]["tampa_bay_seagrass_transects"]

    assert louisiana["structural_status"] == "structural_ready"
    assert tampa["structural_status"] == "structural_ready"
    assert louisiana["predictive_status"] == "predictive_complement_candidate"
    assert louisiana["predictive_use_allowed"] is True
    assert tampa["predictive_status"] == "ineligible_generation_shift"
    assert tampa["predictive_use_allowed"] is False
