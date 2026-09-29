from eog.v2.joint_ecology_observation import run_joint_ecology_observation_v27
from eog.v2.known_truth_bam_v2_1 import build_v21_system
from eog.v2.stochastic_evidence_design import (
    action_supports_v28,
    build_active_joint_worlds_v28,
    run_stochastic_evidence_design_v28,
)
from eog.v3.joint_world_engine import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    evaluation_is_contraction,
    plan_next_evidence_action,
)


def _fixture():
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


def test_v3_1_reproduces_frozen_v27_joint_projections():
    ecological, perfect, imperfect, zero, calibration = _fixture()
    frozen = run_joint_ecology_observation_v27()

    strict = evaluate_joint_worlds(ecological, (perfect,), (zero,))
    broad = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))
    calibrated = evaluate_joint_worlds(
        ecological,
        (perfect, imperfect),
        (zero, calibration),
    )

    assert len(strict.surviving_members) == frozen["strict_joint_survivor_count"] == 48
    assert len(broad.surviving_members) == frozen["broad_joint_survivor_count"] == 112
    assert strict.ecological_projection == tuple(frozen["strict_ecological_projection"])
    assert broad.ecological_projection == tuple(frozen["broad_ecological_projection"])
    assert calibrated.ecological_projection == tuple(
        frozen["calibrated_ecological_projection"]
    )


def test_v3_2_reproduces_frozen_v28_action_metrics_and_winners():
    ecological, perfect, imperfect, zero, _ = _fixture()
    evaluation = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))

    active, target = build_active_joint_worlds_v28()
    assert target == "r1c3"
    raw_supports = action_supports_v28(active)
    supports = {
        action_id: {
            joint_id: tuple(str(value) for value in values)
            for joint_id, values in mapping.items()
        }
        for action_id, mapping in raw_supports.items()
    }

    joint_plan = plan_next_evidence_action(
        evaluation,
        supports,
        objective="joint",
    )
    ecological_plan = plan_next_evidence_action(
        evaluation,
        supports,
        objective="ecological",
    )
    frozen = run_stochastic_evidence_design_v28()
    frozen_rows = {
        row["action_id"]: row for row in frozen["action_summaries"]
    }

    for row in joint_plan.rankings:
        expected = frozen_rows[row.action_id]
        assert row.guaranteed_joint_pair_splits == expected[
            "guaranteed_joint_pair_splits"
        ]
        assert row.worst_case_joint_survivors == expected[
            "worst_case_joint_survivors"
        ]
        assert row.worst_case_ecological_survivors == expected[
            "worst_case_ecological_survivors"
        ]

    assert joint_plan.best_action_ids == ("calibrate_detection_world",)
    assert ecological_plan.best_action_ids == ("gold_standard_target_state",)


def test_v3_3_evidence_update_is_monotone_contraction():
    ecological, perfect, imperfect, zero, calibration = _fixture()
    before = evaluate_joint_worlds(
        ecological,
        (perfect, imperfect),
        (zero,),
    )
    after = evaluate_joint_worlds(
        ecological,
        (perfect, imperfect),
        (zero, calibration),
    )

    assert evaluation_is_contraction(before, after)
    assert set(after.surviving_joint_world_ids) < set(before.surviving_joint_world_ids)
    assert set(after.ecological_projection) < set(before.ecological_projection)


def test_v3_4_expanding_observation_universe_preserves_prior_ecological_survivors():
    ecological, perfect, imperfect, zero, _ = _fixture()
    strict = evaluate_joint_worlds(ecological, (perfect,), (zero,))
    broad = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))

    assert set(strict.ecological_projection) < set(broad.ecological_projection)


def test_v3_5_planner_fails_closed_when_no_action_improves_objective():
    ecological, perfect, imperfect, zero, _ = _fixture()
    evaluation = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))

    noops = {
        "noop_a": {
            joint_id: ("same",)
            for joint_id in evaluation.surviving_joint_world_ids
        },
        "noop_b": {
            joint_id: ("same",)
            for joint_id in evaluation.surviving_joint_world_ids
        },
    }

    joint_plan = plan_next_evidence_action(
        evaluation,
        noops,
        objective="joint",
    )
    ecological_plan = plan_next_evidence_action(
        evaluation,
        noops,
        objective="ecological",
    )

    assert joint_plan.best_action_ids == ()
    assert joint_plan.fail_closed_no_improvement is True
    assert ecological_plan.best_action_ids == ()
    assert ecological_plan.fail_closed_no_improvement is True
