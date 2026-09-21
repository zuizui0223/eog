from benchmarks.eogwf_v2_generality_known_truth import run_benchmark


def test_integrated_generality_known_truth_path():
    result = run_benchmark()
    assert result["uses_biological_response"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["coordinate_registry"]["status"] == "within_frozen_tolerance"
    assert result["structural_scale"]["adequacy_passed"] is True
    assert result["predictive_state"]["safe_status"] == "predictive_complement_candidate"
    assert result["predictive_state"]["tampa_like_status"] == "ineligible_generation_shift"
    assert result["pre_response_certificate"]["safe_status"] == "structural_ready"
    assert (
        result["pre_response_certificate"]["safe_predictive_status"]
        == "predictive_complement_candidate"
    )
    assert result["pre_response_certificate"]["safe_predictive_use_allowed"] is True
    assert (
        result["pre_response_certificate"]["tampa_like_predictive_use_allowed"]
        is False
    )
