from benchmarks.run_eog_original_idea_analyst_worlds_v3 import run


def test_analyst_world_panel_has_same_frozen_ecological_size():
    result = run()
    assert result["row_count"] == 384
    assert result["analyst_rules"] == [
        "relative_edge_q70",
        "absolute_raw_0.5",
        "standardized_sd_1.0",
    ]


def test_analyst_universe_expansion_obeys_exact_monotonicity():
    result = run()
    assert result["aggregate"]["analyst_universe_monotonicity_violations"] == 0


def test_every_predeclared_analyst_world_hypothesis_gets_a_verdict():
    result = run()
    assert set(result["predeclared_verdicts"]) == {
        "A1_analyst_rule_disagreement_exists",
        "A2_analyst_universe_expansion_weakens_certificates_monotonically",
        "A3_autocorrelation_conclusion_is_rule_sensitive",
        "A4_barrier_effect_is_robust_across_analyst_rules",
        "A5_some_relations_remain_robust_despite_analyst_uncertainty",
    }
