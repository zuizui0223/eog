from eog.v2.adaptive_evidence_tree import (
    forced_first_action_depth,
    run_adaptive_evidence_v29,
    solve_adaptive_policy,
)
from eog.v2.robust_evidence_design import build_v28_fixture


def test_optimal_adaptive_policy_has_depth_two_and_two_optimal_first_actions():
    hypotheses, _, _, actions = build_v28_fixture()
    value = solve_adaptive_policy(hypotheses, actions)

    assert value.resolvable is True
    assert value.worst_case_depth == 2
    assert value.optimal_first_actions == (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )
    assert value.canonical_first_action == "direct_detection_calibration"


def test_repeat_first_has_worse_worst_case_depth():
    hypotheses, _, _, actions = build_v28_fixture()

    assert forced_first_action_depth(
        hypotheses, actions, "repeat_one_survey"
    ) == 3
    assert forced_first_action_depth(
        hypotheses, actions, "repeat_four_surveys"
    ) == 3


def test_removing_either_direct_channel_makes_worst_case_resolution_impossible():
    hypotheses, _, _, actions = build_v28_fixture()

    without_calibration = solve_adaptive_policy(
        hypotheses,
        actions,
        available_action_ids=(
            "direct_target_state_assay",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    without_state = solve_adaptive_policy(
        hypotheses,
        actions,
        available_action_ids=(
            "direct_detection_calibration",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )

    assert without_calibration.resolvable is False
    assert without_state.resolvable is False


def test_frozen_v29_result():
    result = run_adaptive_evidence_v29()

    assert result["minimum_worst_case_depth"] == 2
    assert result["optimal_first_actions"] == [
        "direct_detection_calibration",
        "direct_target_state_assay",
    ]
    assert result["canonical_first_action"] == "direct_detection_calibration"
    assert result["first_action_worst_case_depths"] == {
        "direct_detection_calibration": 2,
        "direct_target_state_assay": 2,
        "repeat_four_surveys": 3,
        "repeat_one_survey": 3,
    }
    assert result["bruteforce_worst_case_depth"] == 2
    assert result["known_truth_realized_depth"] == 1
    assert result["known_truth_realized_path"][0]["after_hypotheses"] == [
        "absent::p1"
    ]
    assert result["ablation_without_calibration"]["resolvable"] is False
    assert result["ablation_without_state_assay"]["resolvable"] is False
    assert result["verdicts"] == {
        "A1_exact_adaptive_recursion": "SUPPORTED",
        "A2_optimal_worst_case_depth": "SUPPORTED",
        "A3_repeat_first_is_worse": "SUPPORTED",
        "A4_known_truth_realized_depth": "SUPPORTED",
        "A5_direct_channels_are_jointly_necessary_for_worst_case_resolution": "SUPPORTED",
    }
