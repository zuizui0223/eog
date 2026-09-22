from benchmarks.stoc_schema_contract_replay import run_replay


def test_stoc_historical_schema_mapping_is_representable_by_generic_v2_adapter():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["reruns_frozen_stoc"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["historical_mapping"] == {
        "x_wgs84": "X_WGS84",
        "y_wgs84": "Y_WGS84",
    }
    assert result["generic_role_mapping"]["x"] == "x_wgs84"
    assert result["generic_role_mapping"]["y"] == "y_wgs84"
