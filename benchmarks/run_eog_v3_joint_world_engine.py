#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

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


def fixture():
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation/eog_v3_joint_world_engine/result_v1.json"),
    )
    args = parser.parse_args()

    ecological, perfect, imperfect, zero, calibration = fixture()
    frozen27 = run_joint_ecology_observation_v27()
    frozen28 = run_stochastic_evidence_design_v28()

    strict = evaluate_joint_worlds(ecological, (perfect,), (zero,))
    broad = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))
    calibrated = evaluate_joint_worlds(
        ecological, (perfect, imperfect), (zero, calibration)
    )

    v31 = (
        len(strict.surviving_members) == frozen27["strict_joint_survivor_count"]
        and len(broad.surviving_members) == frozen27["broad_joint_survivor_count"]
        and strict.ecological_projection
        == tuple(frozen27["strict_ecological_projection"])
        and broad.ecological_projection
        == tuple(frozen27["broad_ecological_projection"])
        and calibrated.ecological_projection
        == tuple(frozen27["calibrated_ecological_projection"])
    )

    active, _ = build_active_joint_worlds_v28()
    raw_supports = action_supports_v28(active)
    supports = {
        action_id: {
            joint_id: tuple(str(value) for value in values)
            for joint_id, values in mapping.items()
        }
        for action_id, mapping in raw_supports.items()
    }
    joint_plan = plan_next_evidence_action(broad, supports, objective="joint")
    ecological_plan = plan_next_evidence_action(
        broad, supports, objective="ecological"
    )
    frozen_rows = {
        row["action_id"]: row for row in frozen28["action_summaries"]
    }
    metric_match = True
    for row in joint_plan.rankings:
        expected = frozen_rows[row.action_id]
        metric_match &= (
            row.guaranteed_joint_pair_splits
            == expected["guaranteed_joint_pair_splits"]
            and row.worst_case_joint_survivors
            == expected["worst_case_joint_survivors"]
            and row.worst_case_ecological_survivors
            == expected["worst_case_ecological_survivors"]
        )
    v32 = (
        metric_match
        and joint_plan.best_action_ids == ("calibrate_detection_world",)
        and ecological_plan.best_action_ids
        == ("gold_standard_target_state",)
    )

    v33 = evaluation_is_contraction(broad, calibrated)
    v34 = set(strict.ecological_projection).issubset(
        broad.ecological_projection
    )

    noops = {
        "noop_a": {
            joint_id: ("same",)
            for joint_id in broad.surviving_joint_world_ids
        },
        "noop_b": {
            joint_id: ("same",)
            for joint_id in broad.surviving_joint_world_ids
        },
    }
    no_joint = plan_next_evidence_action(broad, noops, objective="joint")
    no_eco = plan_next_evidence_action(broad, noops, objective="ecological")
    v35 = (
        no_joint.best_action_ids == ()
        and no_joint.fail_closed_no_improvement
        and no_eco.best_action_ids == ()
        and no_eco.fail_closed_no_improvement
    )

    verdicts = {
        "V3_1_reproduce_joint_v27": "SUPPORTED" if v31 else "REFUTED",
        "V3_2_reproduce_stochastic_v28": "SUPPORTED" if v32 else "REFUTED",
        "V3_3_evidence_update_monotonicity": "SUPPORTED" if v33 else "REFUTED",
        "V3_4_observation_universe_expansion": "SUPPORTED" if v34 else "REFUTED",
        "V3_5_fail_closed_action_choice": "SUPPORTED" if v35 else "REFUTED",
    }

    result = {
        "schema": "eog.v3.joint_world_engine.result.v1",
        "strict_joint_survivor_count": len(strict.surviving_members),
        "broad_joint_survivor_count": len(broad.surviving_members),
        "strict_ecological_projection_count": len(strict.ecological_projection),
        "broad_ecological_projection_count": len(broad.ecological_projection),
        "calibrated_ecological_projection_count": len(
            calibrated.ecological_projection
        ),
        "joint_objective_best_actions": list(joint_plan.best_action_ids),
        "ecological_objective_best_actions": list(
            ecological_plan.best_action_ids
        ),
        "joint_plan_fingerprint": joint_plan.fingerprint,
        "ecological_plan_fingerprint": ecological_plan.fingerprint,
        "strict_evaluation_fingerprint": strict.fingerprint,
        "broad_evaluation_fingerprint": broad.fingerprint,
        "calibrated_evaluation_fingerprint": calibrated.fingerprint,
        "fail_closed_joint": no_joint.fail_closed_no_improvement,
        "fail_closed_ecological": no_eco.fail_closed_no_improvement,
        "coverage_certificate": broad.coverage_certificate,
        "verdicts": verdicts,
    }
    payload = json.dumps(
        result,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    result["fingerprint"] = hashlib.sha256(payload).hexdigest()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
