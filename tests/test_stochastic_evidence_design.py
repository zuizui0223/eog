from eog.v2.stochastic_evidence_design import (
    build_active_joint_worlds_v28,
    run_stochastic_evidence_design_v28,
)


def test_v28_reconstructs_frozen_active_joint_state():
    active, target = build_active_joint_worlds_v28()

    assert target == "r1c3"
    assert len(active) == 112
    assert len({row.ecological_world_id for row in active}) == 64


def test_v28_frozen_action_values():
    result = run_stochastic_evidence_design_v28()
    rows = {row["action_id"]: row for row in result["action_summaries"]}

    assert rows["repeat_4_same_protocol"] == {
        "action_id": "repeat_4_same_protocol",
        "guaranteed_joint_pair_splits": 0,
        "worst_case_joint_survivors": 112,
        "worst_case_ecological_survivors": 64,
        "possible_outcomes": [0, 1, 2, 3, 4],
    }
    assert rows["calibrate_detection_world"] == {
        "action_id": "calibrate_detection_world",
        "guaranteed_joint_pair_splits": 3072,
        "worst_case_joint_survivors": 64,
        "worst_case_ecological_survivors": 64,
        "possible_outcomes": ["imperfect", "perfect"],
    }
    assert rows["gold_standard_target_state"] == {
        "action_id": "gold_standard_target_state",
        "guaranteed_joint_pair_splits": 1536,
        "worst_case_joint_survivors": 96,
        "worst_case_ecological_survivors": 48,
        "possible_outcomes": ["absent", "present"],
    }


def test_v28_objective_changes_best_action():
    result = run_stochastic_evidence_design_v28()

    assert result["best_action_joint_objective"] == [
        "calibrate_detection_world"
    ]
    assert result["best_action_ecological_objective"] == [
        "gold_standard_target_state"
    ]
    assert result["S1_mismatches"] == 0
    assert result["verdicts"] == {
        "S1_support_disjointness": "SUPPORTED",
        "S2_frozen_action_values": "SUPPORTED",
        "S3_objective_dependent_choice": "SUPPORTED",
        "S4_more_same_type_data_is_robustly_dominated": "SUPPORTED",
    }
