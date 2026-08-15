import runpy


def _benchmark():
    namespace = runpy.run_path("benchmarks/inverse_estimand_comparator.py")
    return namespace["run_inverse_estimand_comparator"]()


def test_inverse_comparator_is_explicitly_estimand_separation_not_superiority():
    result = _benchmark()
    assert result["schema_version"] == 1
    assert result["claim_boundary"] == (
        "known-truth estimand-separation benchmark; not external-method superiority"
    )


def test_endpoint_only_summary_cannot_see_the_temporal_constraint():
    baseline = _benchmark()["endpoint_only_baseline"]
    assert baseline["late_signature"] == ["C"]
    assert baseline["early_signature"] == ["C"]
    assert baseline["cannot_distinguish_t2_from_t3"] is True


def test_final_horizon_reachability_keeps_slow_and_fast_explanations_together():
    baseline = _benchmark()["final_horizon_reachability_baseline"]
    assert set(baseline["compatible_world_ids_at_C_t3"]) == {
        "slow_baseline",
        "fast_geo",
        "fast_env",
        "fast_barrier",
        "dominated",
    }
    assert baseline["retains_slow_and_fast_worlds"] is True


def test_temporal_evidence_eliminates_the_zero_relaxation_slow_world():
    eog = _benchmark()["eog_inverse"]
    assert set(eog["compatible_world_ids_at_C_t2"]) == {
        "fast_geo",
        "fast_env",
        "fast_barrier",
        "dominated",
    }
    assert eog["slow_world_eliminated_by_timing"] is True
    assert eog["identifiable"] is False


def test_eog_retains_three_non_dominated_axis_specific_rescues():
    eog = _benchmark()["eog_inverse"]
    assert set(tuple(row) for row in eog["frontier_axis_signatures"]) == {
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    }
    assert set(eog["frontier_world_ids"]) == {
        "fast_geo",
        "fast_env",
        "fast_barrier",
    }
    assert eog["preserves_three_axis_specific_rescues"] is True
    assert eog["dominated_world_removed"] is True
    assert eog["keeps_history_set_valued"] is True


def test_one_scalar_relaxation_score_loses_axis_identity_and_cannot_pick_a_history():
    scalar = _benchmark()["scalar_relaxation_baseline"]
    checks = _benchmark()["separation_checks"]

    assert scalar["minimum_score"] == 1.0
    assert scalar["tie_count"] == 3
    assert set(scalar["tied_world_ids"]) == {
        "fast_geo",
        "fast_env",
        "fast_barrier",
    }
    assert checks["axis_identity_is_lost_by_scalarization"] is True
    assert checks["single_history_would_require_extra_tie_break"] is True


def test_timing_adds_information_without_changing_endpoint_identity():
    checks = _benchmark()["separation_checks"]
    assert checks["timing_adds_information_beyond_endpoint_identity"] is True
