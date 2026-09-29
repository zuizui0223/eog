from eog.v2.robust_evidence_design import (
    build_v28_fixture,
    plan_robust_set_valued_evidence,
    robustly_separates,
    run_robust_set_valued_v28,
)


def test_repeat_surveys_have_overlapping_support_and_no_robust_split():
    hypotheses, _, _, actions = build_v28_fixture()
    plan = plan_robust_set_valued_evidence(hypotheses, actions)
    rows = {row.action_id: row.robust_split_pair_count for row in plan.rankings}

    assert rows["repeat_one_survey"] == 0
    assert rows["repeat_four_surveys"] == 0


def test_direct_channels_each_split_two_of_three_pairs():
    hypotheses, _, _, actions = build_v28_fixture()
    plan = plan_robust_set_valued_evidence(hypotheses, actions)
    rows = {row.action_id: row.robust_split_pair_count for row in plan.rankings}

    assert rows["direct_detection_calibration"] == 2
    assert rows["direct_target_state_assay"] == 2
    assert plan.minimum_robust_separating_set == (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )


def test_possible_outcome_overlap_is_the_robust_separation_boundary():
    assert robustly_separates({0}, {1})
    assert not robustly_separates({0}, {0, 1})


def test_frozen_v28_result():
    result = run_robust_set_valued_v28()

    assert result["unresolved_pair_count"] == 3
    assert result["robust_split_pair_count_by_action"] == {
        "direct_detection_calibration": 2,
        "direct_target_state_assay": 2,
        "repeat_four_surveys": 0,
        "repeat_one_survey": 0,
    }
    assert result["minimum_robust_separating_set"] == [
        "direct_detection_calibration",
        "direct_target_state_assay",
    ]
    assert result["minimum_robust_set_size"] == 2
    assert result["known_truth_after_calibration"] == ["absent::p1"]
    assert result["R1_mismatches"] == 0
    assert result["verdicts"] == {
        "R1_disjoint_support_criterion": "SUPPORTED",
        "R2_more_surveys_have_no_guaranteed_split": "SUPPORTED",
        "R3_direct_channels_each_split_two_pairs": "SUPPORTED",
        "R4_minimum_robust_design": "SUPPORTED",
        "R5_truth_conditional_adaptive_shortcut": "SUPPORTED",
    }
