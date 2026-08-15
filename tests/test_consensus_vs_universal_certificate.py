import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/consensus_vs_universal_certificate.py")
    return namespace["run_consensus_certificate_comparator"]()


def test_consensus_certificate_benchmark_keeps_estimands_distinct():
    result = _benchmark()
    assert result["schema_version"] == 1
    assert result["claim_boundary"] == (
        "known-truth consensus-frequency vs universal finite-world certificate comparison; "
        "neither estimand is treated as incorrect"
    )


def test_99_of_100_worlds_is_high_consensus_but_not_robust():
    target = _benchmark()["target_T"]
    assert target["reachability_frequency"] == pytest.approx(0.99)
    assert target["consensus_threshold"] == pytest.approx(0.95)
    assert target["consensus_supported"] is True
    assert target["robust_in_99_supporting_worlds"] is True
    assert target["robust_after_adding_one_excluding_world"] is False
    assert target["contingent_after_expansion"] is True


def test_unanimous_exclusion_remains_a_finite_universe_certificate():
    excluded = _benchmark()["always_excluded_E"]
    assert excluded["reachability_frequency"] == pytest.approx(0.0)
    assert excluded["robustly_unreachable"] is True


def test_world_universe_expansion_weakens_the_target_robustness_claim():
    result = _benchmark()
    monotonicity = result["monotonicity"]
    assert "T" in monotonicity["base_reachable_in_all_ids"]
    assert "T" not in monotonicity["expanded_reachable_in_all_ids"]
    assert "T" in monotonicity["expanded_contingent_ids"]
    assert monotonicity["adding_world_does_not_create_new_robust_target_claim"] is True
    assert monotonicity["possible_target_is_not_relabelled_impossible"] is True


def test_consensus_and_universal_certificate_answer_different_questions():
    checks = _benchmark()["separation_checks"]
    assert checks["high_consensus_is_not_universal_robustness"] is True
    assert checks["unanimous_exclusion_supports_finite_certificate"] is True
    assert checks["consensus_and_certificate_answer_different_questions"] is True
