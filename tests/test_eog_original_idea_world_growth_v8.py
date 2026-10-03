from benchmarks.run_eog_original_idea_world_growth_v8 import (
    _lifetime_summary,
    _survival_probability,
)


def test_exact_survival_probability_endpoints():
    assert _survival_probability(10, 0, 10) == 1.0
    assert _survival_probability(10, 2, 10) == 0.0
    assert _survival_probability(10, 2, 0) == 1.0


def test_expected_lifetime_is_one_for_unthreatened_certificate():
    pool = tuple(
        {"reachable": frozenset({"A"})}
        for _ in range(5)
    )
    row = _lifetime_summary(pool, "robust_reachable", "A")
    assert row["threat_count_K"] == 0
    assert row["normalized_expected_lifetime"] == 1.0
    assert row["survives_complete_pool"] is True


def test_expected_lifetime_is_finite_with_threatening_world():
    pool = (
        {"reachable": frozenset({"A"})},
        {"reachable": frozenset()},
        {"reachable": frozenset({"A"})},
    )
    row = _lifetime_summary(pool, "robust_reachable", "A")
    assert row["threat_count_K"] == 1
    assert 0 < row["normalized_expected_lifetime"] < 1
    assert row["survives_complete_pool"] is False
