from eog.v2.joint_ecology_observation import (
    evaluate_joint_worlds,
    run_joint_ecology_observation_v27,
)
from eog.v2.known_truth_detection import ObservationWorld


def test_broad_observation_universe_can_only_expand_ecological_projection():
    result = run_joint_ecology_observation_v27()

    strict = set(result["strict_ecological_projection"])
    broad = set(result["broad_ecological_projection"])
    assert strict < broad
    assert result["resurrected_ecological_world_count"] > 0


def test_calibration_restores_strict_ecological_projection():
    result = run_joint_ecology_observation_v27()

    assert set(result["calibrated_ecological_projection"]) == set(
        result["strict_ecological_projection"]
    )


def test_more_finite_nondetections_do_not_remove_all_present_worlds_if_p_less_than_one_is_admissible():
    result = run_joint_ecology_observation_v27()

    assert result["target_present_survivors_by_nondetection_count"] == {
        "1": result["target_present_world_count"],
        "2": result["target_present_world_count"],
        "4": result["target_present_world_count"],
        "8": result["target_present_world_count"],
    }


def test_joint_v27_frozen_verdicts():
    result = run_joint_ecology_observation_v27()

    assert result["truth_target_present"] is False
    assert result["truth_history_probability"] == 1.0
    assert result["J1_mismatches"] == 0
    assert result["J4_failures"] == 0
    assert result["verdicts"] == {
        "J1_joint_factorization": "SUPPORTED",
        "J2_observation_uncertainty_resurrects_ecological_worlds": "SUPPORTED",
        "J3_calibration_restores_ecological_falsification": "SUPPORTED",
        "J4_more_nondetections_do_not_replace_calibration": "SUPPORTED",
        "J5_observation_world_expansion_is_ecologically_monotone": "SUPPORTED",
        "J6_calibration_can_dominate_more_same_type_data": "SUPPORTED",
    }
