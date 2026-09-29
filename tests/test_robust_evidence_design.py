from eog.v2.robust_evidence_design import (
    ObservationWorld,
    observed_count_support,
    run_robust_evidence_design_v27,
)


def test_perfect_binary_observation_has_disjoint_support():
    worlds = (ObservationWorld("perfect", 1.0, 0.0),)

    assert observed_count_support(True, surveys=1, observation_worlds=worlds) == frozenset({1})
    assert observed_count_support(False, surveys=1, observation_worlds=worlds) == frozenset({0})


def test_imperfect_detection_preserves_zero_overlap_at_finite_n():
    worlds = (
        ObservationWorld("perfect", 1.0, 0.0),
        ObservationWorld("imperfect", 0.75, 0.0),
    )

    for n in (1, 8):
        positive = observed_count_support(True, surveys=n, observation_worlds=worlds)
        negative = observed_count_support(False, surveys=n, observation_worlds=worlds)
        assert 0 in positive
        assert negative == frozenset({0})
        assert positive.intersection(negative) == {0}


def test_false_positive_preserves_positive_overlap_at_finite_n():
    worlds = (
        ObservationWorld("perfect", 1.0, 0.0),
        ObservationWorld("false_positive", 1.0, 0.01),
    )

    for n in (1, 8):
        positive = observed_count_support(True, surveys=n, observation_worlds=worlds)
        negative = observed_count_support(False, surveys=n, observation_worlds=worlds)
        assert n in positive
        assert n in negative
        assert positive.intersection(negative)


def test_frozen_v27_verdicts_and_fail_closed_behavior():
    result = run_robust_evidence_design_v27()

    perfect = result["regimes"]["perfect_n1"]
    assert perfect["split_counts"] == {
        "H_long_corridor_challenge": 8,
        "P_barrier_challenge": 8,
        "repeat_passive_state": 0,
    }
    assert perfect["minimum_separating_set"] == [
        "H_long_corridor_challenge",
        "P_barrier_challenge",
    ]
    assert perfect["insufficient_library"] is False

    for key in (
        "imperfect_detection_n1",
        "imperfect_detection_n8",
        "false_positive_n1",
        "false_positive_n8",
    ):
        row = result["regimes"][key]
        assert row["split_counts"]["H_long_corridor_challenge"] == 0
        assert row["split_counts"]["P_barrier_challenge"] == 0
        assert row["minimum_separating_set"] is None
        assert row["insufficient_library"] is True

    assert result["observation_uncertainty_monotonicity_violations"] == 0
    assert result["verdicts"] == {
        "R1_perfect_reduces_to_deterministic": "SUPPORTED",
        "R2_imperfect_detection_blocks_exact_split": "SUPPORTED",
        "R3_false_positive_blocks_exact_split": "SUPPORTED",
        "R4_observation_uncertainty_cannot_improve_exact_design": "SUPPORTED",
        "R5_fail_closed_under_unobservable_intervention": "SUPPORTED",
    }
