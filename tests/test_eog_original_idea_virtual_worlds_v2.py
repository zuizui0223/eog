from benchmarks.run_eog_original_idea_virtual_worlds_v2 import run


def test_randomized_panel_has_frozen_factorial_size_and_no_monotonicity_failure():
    result = run()
    assert result["row_count"] == 384
    assert result["contrasts"]["G8"]["monotonicity_violation_count"] == 0


def test_barrier_levels_are_evaluated_as_nested_relaxation_factor():
    result = run()
    for row in result["contrasts"]["G1"]["strata"].values():
        assert row["nondecreasing"] is True


def test_all_preregistered_generalization_hypotheses_receive_verdicts():
    result = run()
    assert set(result["predeclared_verdicts"]) == {
        "G1_barriers_increase_viable_unreachable_fraction",
        "G2_low_autocorrelation_increases_pathwise_IBE_failures",
        "G3_sparse_neighbourhood_increases_critical_stepping_stones",
        "G4_wider_neighbourhood_increases_single_node_route_robustness",
        "G5_static_history_aliasing_is_common",
        "G6_temporal_positive_evidence_contracts_source_history_aliases",
        "G7_impossibility_has_multiple_mechanistic_rescue_classes",
        "G8_world_expansion_monotonicity",
    }
    assert len(result["fingerprint"]) == 64
