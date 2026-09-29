from eog.v3 import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    plan_next_evidence_action,
    plan_robust_evidence_set,
    solve_adaptive_evidence_policy,
)


def test_public_v3_import_surface_runs_end_to_end():
    ecological = (
        EcologicalWorld("absent", (("site", "absent"),)),
        EcologicalWorld("present", (("site", "present"),)),
    )
    observation = (
        ObservationWorld(
            "perfect",
            (
                ObservationSupport("survey", "absent", ("zero",)),
                ObservationSupport("survey", "present", ("positive",)),
            ),
        ),
        ObservationWorld(
            "imperfect",
            (
                ObservationSupport("survey", "absent", ("zero",)),
                ObservationSupport("survey", "present", ("zero", "positive")),
            ),
        ),
    )
    evidence = (EvidenceEvent("site", "survey", "zero"),)

    evaluation = evaluate_joint_worlds(ecological, observation, evidence)

    assert evaluation.surviving_joint_world_ids == (
        "absent::imperfect",
        "absent::perfect",
        "present::imperfect",
    )

    action_supports = {
        "calibrate": {
            "absent::imperfect": ("imperfect",),
            "absent::perfect": ("perfect",),
            "present::imperfect": ("imperfect",),
        },
        "state": {
            "absent::imperfect": ("absent",),
            "absent::perfect": ("absent",),
            "present::imperfect": ("present",),
        },
    }

    one_step = plan_next_evidence_action(
        evaluation,
        action_supports,
        objective="ecological",
    )
    robust = plan_robust_evidence_set(evaluation, action_supports)
    adaptive = solve_adaptive_evidence_policy(evaluation, action_supports)

    assert one_step.best_action_ids == ("state",)
    assert robust.minimum_robust_set_size == 2
    assert robust.all_pairs_robustly_separated is True
    assert adaptive.resolvable is True
    assert adaptive.worst_case_depth == 2
