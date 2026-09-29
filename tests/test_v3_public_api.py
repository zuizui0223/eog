from eog.v3 import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    plan_next_evidence_action,
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
    plan = plan_next_evidence_action(
        evaluation,
        action_supports,
        objective="ecological",
    )

    assert plan.best_action_ids == ("state",)
    assert plan.fail_closed_no_improvement is False
