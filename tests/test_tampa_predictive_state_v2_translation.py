from benchmarks.tampa_predictive_state_v2_translation import run_replay


def test_frozen_tampa_design_is_stopped_by_v2_before_predictive_outcome_access():
    result = run_replay()

    assert result["uses_biological_response"] is False
    assert result["uses_observed_tampa_predictive_score"] is False
    assert result["reruns_frozen_endpoint"] is False
    assert result["counts_as_predictive_evidence"] is False

    assert result["frozen_candidate_universe"]["node_count"] == 71
    assert result["frozen_candidate_universe"]["context_count"] == 29
    assert result["frozen_candidate_universe"]["candidate_unit_count"] == 1497
    assert (
        result["frozen_candidate_universe"]["baseline_contains_spatial_coordinates"]
        is True
    )

    assert result["world_state"]["declared_world_count"] == 5
    assert result["world_state"]["surviving_world_count_every_fold"] == 5
    assert result["world_state"]["contraction_event_count"] == 0
    assert result["world_state"]["fully_saturated_context_fraction"] == 1.0

    assert result["geometry_signature"]["source_reconstruction_count"] == 2
    assert result["geometry_signature"]["all_exact_fingerprint_match"] is True
    assert result["geometry_signature"]["unique_node_feature_vectors_each_source"] == [
        71,
        71,
    ]

    gate = result["v2_predictive_state_gate"]
    assert gate["status"] == "ineligible_generation_shift"
    assert gate["predictive_use_allowed"] is False
    assert "train_and_serve_feature_generators_differ" in gate["reasons"]
    assert (
        "prediction_facing_source_policy_depends_on_arbitrary_source_labels"
        in gate["reasons"]
    )
    assert (
        "repeated_endpoint_reuses_static_state_without_predictive_opt_in"
        in gate["reasons"]
    )
    assert (
        "static_state_may_duplicate_or_reencode_baseline_spatial_identity"
        in gate["warnings"]
    )
