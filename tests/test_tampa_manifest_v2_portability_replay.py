from benchmarks.tampa_manifest_v2_portability_replay import run_replay


def test_tampa_manifest_preserves_structural_use_but_withholds_prediction():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["uses_observed_tampa_predictive_score"] is False
    assert result["reruns_frozen_endpoint"] is False
    assert result["counts_as_predictive_evidence"] is False

    assert result["counts"] == {
        "node_count": 71,
        "context_count": 29,
        "scored_candidate_count": 1497,
        "initialization_count": 0,
        "unsurveyed_count": 0,
        "declared_world_count": 5,
        "structural_world_count": 4,
    }
    assert result["fold_node_counts"] == {1: 14, 2: 14, 3: 16, 4: 14, 5: 13}
    assert result["fold_candidate_counts"] == {
        1: 265,
        2: 336,
        3: 315,
        4: 315,
        5: 266,
    }

    statuses = result["statuses"]
    assert statuses["structural"] == "structural_ready"
    assert statuses["structural_response_access_allowed"] is True
    assert statuses["predictive"] == "ineligible_generation_shift"
    assert statuses["predictive_use_allowed"] is False
    assert statuses["predictive_outcome_access_allowed"] is False
    assert result["predictive_state_fingerprint_matches_existing_v2_replay"] is True
