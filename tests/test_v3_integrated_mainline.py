import json
import sys

from eog.v2.known_truth_bam_v2_1 import build_v21_system
from eog.v3.adaptive import (
    adaptive_forced_first_depth,
    plan_robust_evidence_set,
    solve_adaptive_evidence_policy,
)
from eog.v3.cli import plan_adaptive_main
from eog.v3.joint_world_engine import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    evaluation_is_contraction,
)


def _bam_projection_fixture():
    system = build_v21_system()
    target = "r1c3"
    ecological = tuple(
        EcologicalWorld(
            world.world_id,
            ((target, "present" if target in world.occupied_ids else "absent"),),
        )
        for world in system.worlds
    )
    perfect = ObservationWorld(
        "perfect",
        (
            ObservationSupport("survey4", "present", ("positive",)),
            ObservationSupport("survey4", "absent", ("zero",)),
            ObservationSupport("calibration", "present", ("perfect",)),
            ObservationSupport("calibration", "absent", ("perfect",)),
        ),
    )
    imperfect = ObservationWorld(
        "imperfect",
        (
            ObservationSupport("survey4", "present", ("zero", "positive")),
            ObservationSupport("survey4", "absent", ("zero",)),
            ObservationSupport("calibration", "present", ("imperfect",)),
            ObservationSupport("calibration", "absent", ("imperfect",)),
        ),
    )
    zero = EvidenceEvent(target, "survey4", "zero")
    calibration = EvidenceEvent(target, "calibration", "perfect")
    return ecological, perfect, imperfect, zero, calibration


def _three_hypothesis_fixture():
    ecological = (
        EcologicalWorld("absent", (("site", "absent"),)),
        EcologicalWorld("present", (("site", "present"),)),
    )
    p1 = ObservationWorld(
        "p1",
        (
            ObservationSupport("survey", "absent", ("zero",)),
            ObservationSupport("survey", "present", ("positive",)),
        ),
    )
    p075 = ObservationWorld(
        "p075",
        (
            ObservationSupport("survey", "absent", ("zero",)),
            ObservationSupport("survey", "present", ("zero", "positive")),
        ),
    )
    evaluation = evaluate_joint_worlds(
        ecological,
        (p1, p075),
        (EvidenceEvent("site", "survey", "zero"),),
    )
    actions = {
        "repeat_one_survey": {
            "absent::p1": frozenset({0}),
            "absent::p075": frozenset({0}),
            "present::p075": frozenset({0, 1}),
        },
        "repeat_four_surveys": {
            "absent::p1": frozenset({0}),
            "absent::p075": frozenset({0}),
            "present::p075": frozenset({0, 1, 2, 3, 4}),
        },
        "direct_detection_calibration": {
            "absent::p1": frozenset({1.0}),
            "absent::p075": frozenset({0.75}),
            "present::p075": frozenset({0.75}),
        },
        "direct_target_state_assay": {
            "absent::p1": frozenset({"absent"}),
            "absent::p075": frozenset({"absent"}),
            "present::p075": frozenset({"present"}),
        },
    }
    return evaluation, actions


def test_integrated_v3_reproduces_joint_projection_v27():
    ecological, perfect, imperfect, zero, calibration = _bam_projection_fixture()

    strict = evaluate_joint_worlds(ecological, (perfect,), (zero,))
    broad = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))
    calibrated = evaluate_joint_worlds(
        ecological,
        (perfect, imperfect),
        (zero, calibration),
    )

    assert len(strict.surviving_members) == 48
    assert len(strict.ecological_projection) == 48
    assert len(broad.surviving_members) == 112
    assert len(broad.ecological_projection) == 64
    assert len(calibrated.surviving_members) == 48
    assert calibrated.ecological_projection == strict.ecological_projection
    assert evaluation_is_contraction(broad, calibrated)


def test_integrated_v3_reproduces_robust_v28():
    evaluation, actions = _three_hypothesis_fixture()
    assert evaluation.surviving_joint_world_ids == (
        "absent::p075",
        "absent::p1",
        "present::p075",
    )

    plan = plan_robust_evidence_set(evaluation, actions)
    split_counts = {
        row.action_id: row.robust_split_pair_count
        for row in plan.rankings
    }

    assert split_counts == {
        "direct_detection_calibration": 2,
        "direct_target_state_assay": 2,
        "repeat_four_surveys": 0,
        "repeat_one_survey": 0,
    }
    assert plan.minimum_robust_separating_set == (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )
    assert plan.minimum_robust_set_size == 2
    assert plan.all_pairs_robustly_separated is True
    assert plan.insufficient_action_library is False


def test_integrated_v3_reproduces_adaptive_v29():
    evaluation, actions = _three_hypothesis_fixture()

    policy = solve_adaptive_evidence_policy(evaluation, actions)
    assert policy.resolvable is True
    assert policy.worst_case_depth == 2
    assert policy.optimal_first_actions == (
        "direct_detection_calibration",
        "direct_target_state_assay",
    )
    assert policy.canonical_first_action == "direct_detection_calibration"

    assert adaptive_forced_first_depth(
        evaluation, actions, "repeat_one_survey"
    ) == 3
    assert adaptive_forced_first_depth(
        evaluation, actions, "repeat_four_surveys"
    ) == 3

    without_calibration = solve_adaptive_evidence_policy(
        evaluation,
        actions,
        available_action_ids=(
            "direct_target_state_assay",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    without_state = solve_adaptive_evidence_policy(
        evaluation,
        actions,
        available_action_ids=(
            "direct_detection_calibration",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    assert without_calibration.resolvable is False
    assert without_state.resolvable is False


def test_v3_adaptive_cli_uses_same_json_action_library(tmp_path, monkeypatch):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "adaptive.json"
    payload = {
        "ecological_worlds": [
            {
                "world_id": "eco_absent",
                "state_by_target": {"site": "absent"},
            },
            {
                "world_id": "eco_present",
                "state_by_target": {"site": "present"},
            },
        ],
        "observation_worlds": [
            {
                "world_id": "perfect",
                "supports": [
                    {
                        "channel_id": "survey",
                        "ecological_state": "absent",
                        "possible_outcomes": ["zero"],
                    },
                    {
                        "channel_id": "survey",
                        "ecological_state": "present",
                        "possible_outcomes": ["positive"],
                    },
                ],
            },
            {
                "world_id": "imperfect",
                "supports": [
                    {
                        "channel_id": "survey",
                        "ecological_state": "absent",
                        "possible_outcomes": ["zero"],
                    },
                    {
                        "channel_id": "survey",
                        "ecological_state": "present",
                        "possible_outcomes": ["zero", "positive"],
                    },
                ],
            },
        ],
        "evidence_events": [
            {
                "target_id": "site",
                "channel_id": "survey",
                "observed_outcome": "zero",
            }
        ],
        "action_supports": {
            "calibrate_detection_world": {
                "eco_absent::imperfect": ["imperfect"],
                "eco_absent::perfect": ["perfect"],
                "eco_present::imperfect": ["imperfect"],
            },
            "gold_standard_target_state": {
                "eco_absent::imperfect": ["absent"],
                "eco_absent::perfect": ["absent"],
                "eco_present::imperfect": ["present"],
            },
            "repeat_same_information": {
                "eco_absent::imperfect": ["same"],
                "eco_absent::perfect": ["same"],
                "eco_present::imperfect": ["same"],
            },
        },
    }
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v3-plan-adaptive",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
    )

    assert plan_adaptive_main() == 0
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["minimum_robust_separating_set"] == [
        "calibrate_detection_world",
        "gold_standard_target_state",
    ]
    assert result["minimum_robust_set_size"] == 2
    assert result["adaptive_resolvable"] is True
    assert result["adaptive_worst_case_depth"] == 2
    assert set(result["adaptive_optimal_first_actions"]) == {
        "calibrate_detection_world",
        "gold_standard_target_state",
    }
    assert result["forced_first_action_depths"]["repeat_same_information"] == 3
