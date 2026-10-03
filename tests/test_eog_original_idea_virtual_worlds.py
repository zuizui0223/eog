from benchmarks.run_eog_original_idea_virtual_worlds_v1 import run


def test_all_predeclared_original_eog_hypotheses_are_evaluated():
    result = run()
    expected = {
        "H1_viability_not_reachability",
        "H2_pathwise_IBE_matters",
        "H3_stepping_stones_change_reachability",
        "H4_bottleneck_and_route_redundancy_are_distinct",
        "H5_occurrences_do_not_identify_unique_history",
        "H6_temporal_evidence_contracts_history_fiber",
        "H7_robust_impossibility_is_monotone_under_world_expansion",
    }
    assert set(result["predeclared_verdicts"]) == expected
    assert len(result["fingerprint"]) == 64


def test_temporal_archetype_strictly_contracts_static_alias():
    result = run()
    row = result["results"]["V6_static_alias_temporal_split"]
    assert set(row["before_compatible_world_ids"]) == {
        "fast_history",
        "slow_history",
    }
    assert row["after_compatible_world_ids"] == ["fast_history"]
    assert row["eliminated_world_ids"] == ["slow_history"]


def test_bottleneck_and_redundant_worlds_share_endpoint_support_but_differ_in_knockout():
    result = run()
    row = result["results"]["V4_bottleneck_vs_redundancy"]
    assert row["observed_occurrences"] == ["S", "T"]
    assert row["bottleneck_path_count"] == 1
    assert row["redundant_path_count"] == 2
    assert row["bottleneck_after_A_knockout_reachable"] is False
    assert row["redundant_after_A_knockout_reachable"] is True
