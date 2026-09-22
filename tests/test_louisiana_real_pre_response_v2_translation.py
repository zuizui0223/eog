from benchmarks.louisiana_real_pre_response_v2_translation import run_replay


def test_real_louisiana_pre_response_registry_translates_to_generic_v2():
    result = run_replay()

    assert result["uses_biological_response"] is False
    assert result["reruns_frozen_endpoint"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["source_rows_recovered_from_authoritative_gate0_log"] is True
    assert result["uses_original_safe_file_bytes"] is False

    assert result["registry"]["node_count"] == 33
    assert result["registry"]["context_count"] == 20
    assert result["registry"]["chronological_periods"] == [
        1,2,3,4,5,6,7,8,9,10,11,12,17,13,18,14,19,15,20,16
    ]

    assert result["effort"]["surveyed_count"] == 660
    assert result["effort"]["initialization_count"] == 33
    assert result["effort"]["scored_candidate_count"] == 627
    assert result["effort"]["unsurveyed_count"] == 0

    assert result["worlds"]["declared_world_count"] == 7
    assert result["worlds"]["distinct_geometry_thresholds_km"] == [
        2.728021756372908,
        2.976793133666009,
        17.008648432743254,
    ]
    assert len(result["worlds"]["structural_world_ids"]) == 3
    assert result["worlds"]["distance_matrix_fingerprint_matches_historical"] is True
    assert result["worlds"]["structural_ladder_fingerprint_matches_historical"] is True
    assert result["worlds"]["structural_gate_passed"] is True

    assert result["observation"]["mode"] == "explicit_binary_tokens"
    assert result["predictive_state"]["status"] == "predictive_complement_candidate"
    assert result["predictive_state"]["predictive_use_allowed"] is True
    assert result["certificate"]["predictive_outcome_access_allowed"] is True
