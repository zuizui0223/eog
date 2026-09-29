#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from eog.v2.known_truth_bam_v2_1 import build_v21_system
from eog.v3.adaptive import (
    adaptive_forced_first_depth,
    plan_robust_evidence_set,
    solve_adaptive_evidence_policy,
)
from eog.v3.joint_world_engine import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    evaluation_is_contraction,
)


def bam_projection_fixture():
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


def three_hypothesis_fixture():
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/eog_v3_joint_world_engine/integrated_result_v1.json"
        ),
    )
    args = parser.parse_args()

    ecological, perfect, imperfect, zero, calibration = bam_projection_fixture()
    strict = evaluate_joint_worlds(ecological, (perfect,), (zero,))
    broad = evaluate_joint_worlds(ecological, (perfect, imperfect), (zero,))
    calibrated = evaluate_joint_worlds(
        ecological,
        (perfect, imperfect),
        (zero, calibration),
    )
    iv31 = (
        len(strict.surviving_members) == 48
        and len(strict.ecological_projection) == 48
        and len(broad.surviving_members) == 112
        and len(broad.ecological_projection) == 64
        and len(calibrated.surviving_members) == 48
        and calibrated.ecological_projection == strict.ecological_projection
    )

    evaluation, actions = three_hypothesis_fixture()
    robust = plan_robust_evidence_set(evaluation, actions)
    split_counts = {
        row.action_id: row.robust_split_pair_count
        for row in robust.rankings
    }
    iv32 = (
        split_counts
        == {
            "direct_detection_calibration": 2,
            "direct_target_state_assay": 2,
            "repeat_four_surveys": 0,
            "repeat_one_survey": 0,
        }
        and robust.minimum_robust_separating_set
        == (
            "direct_detection_calibration",
            "direct_target_state_assay",
        )
        and robust.minimum_robust_set_size == 2
    )

    adaptive = solve_adaptive_evidence_policy(evaluation, actions)
    forced = {
        action_id: adaptive_forced_first_depth(
            evaluation, actions, action_id
        )
        for action_id in sorted(actions)
    }
    iv33 = (
        adaptive.resolvable
        and adaptive.worst_case_depth == 2
        and adaptive.optimal_first_actions
        == (
            "direct_detection_calibration",
            "direct_target_state_assay",
        )
        and forced["repeat_one_survey"] == 3
        and forced["repeat_four_surveys"] == 3
    )

    no_calibration = solve_adaptive_evidence_policy(
        evaluation,
        actions,
        available_action_ids=(
            "direct_target_state_assay",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    no_state = solve_adaptive_evidence_policy(
        evaluation,
        actions,
        available_action_ids=(
            "direct_detection_calibration",
            "repeat_one_survey",
            "repeat_four_surveys",
        ),
    )
    iv34 = not no_calibration.resolvable and not no_state.resolvable
    iv35 = evaluation_is_contraction(broad, calibrated)

    verdicts = {
        "IV3_1_joint_projection_reproduction": (
            "SUPPORTED" if iv31 else "REFUTED"
        ),
        "IV3_2_robust_design_reproduction": (
            "SUPPORTED" if iv32 else "REFUTED"
        ),
        "IV3_3_adaptive_tree_reproduction": (
            "SUPPORTED" if iv33 else "REFUTED"
        ),
        "IV3_4_ablation_fail_closed": (
            "SUPPORTED" if iv34 else "REFUTED"
        ),
        "IV3_5_evidence_contraction": (
            "SUPPORTED" if iv35 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.v3.integrated_joint_engine.result.v1",
        "parent_fingerprints": {
            "joint_v2_7": "085587287263d5ebb4016455ac74406b14979e7de25e57e12b8a607becd5cd1d",
            "robust_v2_8": "a459ebd6bdde502c5d86aad7baf37443d17d1156fb358a373c5429c5c94115f8",
            "adaptive_v2_9": "19e441e930c1c3fc116780fa8bfb4b09c178e69c4379a1ef69e47f5b13218822",
        },
        "joint_projection": {
            "strict_joint_survivors": len(strict.surviving_members),
            "strict_ecological_survivors": len(strict.ecological_projection),
            "broad_joint_survivors": len(broad.surviving_members),
            "broad_ecological_survivors": len(broad.ecological_projection),
            "calibrated_joint_survivors": len(calibrated.surviving_members),
            "calibrated_ecological_survivors": len(
                calibrated.ecological_projection
            ),
        },
        "robust_design": {
            "active_joint_hypotheses": list(
                evaluation.surviving_joint_world_ids
            ),
            "split_counts": split_counts,
            "minimum_robust_separating_set": list(
                robust.minimum_robust_separating_set or ()
            ),
            "minimum_robust_set_size": robust.minimum_robust_set_size,
            "plan_fingerprint": robust.fingerprint,
        },
        "adaptive_design": {
            "resolvable": adaptive.resolvable,
            "worst_case_depth": adaptive.worst_case_depth,
            "optimal_first_actions": list(adaptive.optimal_first_actions),
            "canonical_first_action": adaptive.canonical_first_action,
            "forced_first_action_depths": forced,
            "without_calibration_resolvable": no_calibration.resolvable,
            "without_state_assay_resolvable": no_state.resolvable,
            "policy_fingerprint": adaptive.fingerprint,
        },
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
