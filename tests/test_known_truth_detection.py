import pytest

from eog.v2.known_truth_detection import (
    ObservationWorld,
    observation_history_probability,
    robustly_falsified_states,
    run_detection_boundary_v26,
)


@pytest.mark.parametrize("p", [0.25, 0.5, 0.75])
@pytest.mark.parametrize("n", [1, 2, 4, 8])
def test_finite_nondetection_remains_possible_under_imperfect_detection(p, n):
    world = ObservationWorld("w", p, 0.0)
    probability = observation_history_probability(
        "present",
        detections=0,
        surveys=n,
        observation_world=world,
    )
    assert probability == pytest.approx((1.0 - p) ** n)
    assert probability > 0.0
    assert "present" not in robustly_falsified_states(
        detections=0,
        surveys=n,
        observation_worlds=(world,),
    )


@pytest.mark.parametrize("n", [1, 2, 4, 8])
def test_perfect_detection_makes_nondetection_an_exact_negative(n):
    world = ObservationWorld("perfect", 1.0, 0.0)
    assert observation_history_probability(
        "present",
        detections=0,
        surveys=n,
        observation_world=world,
    ) == 0.0
    assert "present" in robustly_falsified_states(
        detections=0,
        surveys=n,
        observation_worlds=(world,),
    )


def test_false_positive_world_removes_hard_positive_exclusion():
    strict = (ObservationWorld("strict", 0.5, 0.0),)
    broad = (
        ObservationWorld("strict", 0.5, 0.0),
        ObservationWorld("false_positive", 0.5, 0.01),
    )

    assert "absent" in robustly_falsified_states(
        detections=1,
        surveys=1,
        observation_worlds=strict,
    )
    assert "absent" not in robustly_falsified_states(
        detections=1,
        surveys=1,
        observation_worlds=broad,
    )


def test_frozen_v26_verdicts():
    result = run_detection_boundary_v26()

    assert result["failure_counts"] == {
        "O1": 0,
        "O2": 0,
        "O3": 0,
        "O4": 0,
        "O5": 0,
    }
    assert result["verdicts"] == {
        "O1_imperfect_nondetection_not_hard_absence": "SUPPORTED",
        "O2_perfect_detection_hard_negative": "SUPPORTED",
        "O3_more_nondetections_change_weight_not_possibility": "SUPPORTED",
        "O4_false_positive_breaks_hard_positive": "SUPPORTED",
        "O5_observation_world_expansion_weakens_or_preserves_falsification": "SUPPORTED",
    }
