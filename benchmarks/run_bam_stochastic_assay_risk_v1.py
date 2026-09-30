#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from eog.v2.bam_ecological_expansion_margin import (
    build_expanded_ecological_lattice,
)
from eog.v2.bam_future_assay_observation import (
    PARAMETER_FIELDS,
    build_action_supports,
    build_joint_hypotheses,
    exact_minimum_deterministic_target_design,
)
from eog.v2.bam_stochastic_assay_risk import (
    minimum_repeat_plan,
    worst_target_pair_risk,
)
from eog.v2.bam_structured_counterfactuals import (
    expanded_variant_counterfactual,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_stochastic_assay_risk_v1/protocol_v1.json"
PARENT = ROOT / "validation/bam_future_assay_observation_v1/result_summary_v1.json"
EXPECTED_PARENT = "3bed33f39d2c8845cb52989855f2ab024327464870224a11568ebb7436bbe332"
TRANSFORMATIONS = ("climate_shift", "biotic_stress", "barrier_restoration")
RISK_THRESHOLD = 0.05
REPEAT_CAP = 30


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _dist(values):
    return {str(k): int(v) for k, v in sorted(Counter(values).items())}


def _mean(values):
    return None if not values else float(statistics.mean(values))


def _median(values):
    return None if not values else float(statistics.median(values))


def _risk_row(result):
    if result is None:
        return None
    return {
        "repeat_depth": result.repeat_depth,
        "worst_bhattacharyya_affinity": result.worst_bhattacharyya_affinity,
        "worst_pair_error_upper_bound": result.worst_pair_error_upper_bound,
        "worst_pair_quality_relation": result.worst_pair_quality_relation,
        "worst_pair_description": list(result.worst_pair_description),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-VIII protocol is not frozen")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    if parent.get("result_fingerprint") != EXPECTED_PARENT:
        raise RuntimeError("Phase-VII parent fingerprint mismatch")

    full_phase_vii_actions = tuple(
        sorted(
            [
                *(f"assay:{field}" for field in PARAMETER_FIELDS),
                *(f"repeat2:{field}" for field in PARAMETER_FIELDS),
                "assay_process_calibration",
            ]
        )
    )

    roster = []
    fiber_rows = []
    exact_robust_failures = 0
    s11_rows = []

    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        activation = audit_system_activation(system)
        roster.append(
            {
                "system_id": spec.system_id,
                "activation_status": activation.status,
                "system_fingerprint": system.fingerprint,
                "activation_fingerprint": activation.fingerprint,
            }
        )
        if activation.status != "PASS":
            continue

        lattice = build_expanded_ecological_lattice(system)
        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        by_G = {}
        for truth in eligible_truths:
            by_G.setdefault(int(truth.occupied_mask), []).append(truth)

        for G, truths in sorted(by_G.items()):
            variants = tuple(row for row in lattice if int(row.occupied_mask) == G)
            for transformation in TRANSFORMATIONS:
                target = {
                    row.variant_id: expanded_variant_counterfactual(
                        system, row, transformation
                    ).binary_decision
                    for row in variants
                }
                if len(set(target.values())) <= 1:
                    continue

                # Reproduce the frozen Phase-VII canonical robust minimum action set,
                # then retain only its ecological assay fields for stochastic scoring.
                hypotheses = build_joint_hypotheses(variants, target)
                actions = build_action_supports(variants, hypotheses)
                phase_vii = exact_minimum_deterministic_target_design(
                    hypotheses,
                    actions,
                    available_action_ids=full_phase_vii_actions,
                )
                if phase_vii.minimum_action_ids is None:
                    raise RuntimeError(
                        f"Phase-VII full action library unexpectedly insufficient: "
                        f"{spec.system_id} G={G} {transformation}"
                    )
                selected_fields = tuple(
                    sorted(
                        action_id.split("assay:", 1)[1]
                        for action_id in phase_vii.minimum_action_ids
                        if action_id.startswith("assay:")
                    )
                )
                if not selected_fields:
                    raise RuntimeError("Phase-VII minimum contains no ecological assay")

                plan = minimum_repeat_plan(
                    variants,
                    target,
                    selected_fields,
                    risk_threshold=RISK_THRESHOLD,
                    repeat_cap=REPEAT_CAP,
                )
                if plan.exact_robust_separation_possible_finite_repeats:
                    exact_robust_failures += 1

                one_no_cal = worst_target_pair_risk(
                    variants,
                    target,
                    selected_fields,
                    repeat_depth=1,
                    quality_calibrated=False,
                )
                one_cal = worst_target_pair_risk(
                    variants,
                    target,
                    selected_fields,
                    repeat_depth=1,
                    quality_calibrated=True,
                )

                row = {
                    "system_id": spec.system_id,
                    "G_mask": G,
                    "G_count": G.bit_count(),
                    "truth_multiplicity": len(truths),
                    "W1_same_G_variants": len(variants),
                    "transformation": transformation,
                    "phase_vii_minimum_action_ids": list(
                        phase_vii.minimum_action_ids
                    ),
                    "selected_assay_fields": list(selected_fields),
                    "selected_field_count": len(selected_fields),
                    "n1_no_calibration": _risk_row(one_no_cal),
                    "n1_quality_calibration": _risk_row(one_cal),
                    "no_calibration_min_repeat": plan.no_calibration_min_repeat,
                    "no_calibration_total_action_count": (
                        plan.no_calibration_total_action_count
                    ),
                    "quality_calibration_min_repeat": (
                        plan.quality_calibration_min_repeat
                    ),
                    "quality_calibration_total_action_count": (
                        plan.quality_calibration_total_action_count
                    ),
                    "no_calibration_at_minimum": _risk_row(
                        plan.no_calibration_at_minimum
                    ),
                    "quality_calibration_at_minimum": _risk_row(
                        plan.quality_calibration_at_minimum
                    ),
                    "exact_robust_separation_possible_finite_repeats": (
                        plan.exact_robust_separation_possible_finite_repeats
                    ),
                }
                fiber_rows.append(row)

                if (
                    spec.system_id == "S11_9x5_gap"
                    and G == 2138792820255
                    and transformation == "climate_shift"
                ):
                    s11_rows.append(row)

    if len(fiber_rows) != 67:
        raise RuntimeError(
            f"expected Phase-VII 67 unresolved fibers, got {len(fiber_rows)}"
        )
    if exact_robust_failures:
        raise RuntimeError(
            f"finite-repeat exact robust separation appeared in "
            f"{exact_robust_failures} fibers"
        )
    if len(s11_rows) != 1:
        raise RuntimeError(f"expected one S11 climate fiber, got {len(s11_rows)}")

    by_transformation = {}
    repetition_crossing_exists = False
    calibrated_all = True
    calibration_saves_cost = False

    for transformation in TRANSFORMATIONS:
        rows = [row for row in fiber_rows if row["transformation"] == transformation]
        no_cal_repeat = [
            int(row["no_calibration_min_repeat"])
            for row in rows
            if row["no_calibration_min_repeat"] is not None
        ]
        cal_repeat = [
            int(row["quality_calibration_min_repeat"])
            for row in rows
            if row["quality_calibration_min_repeat"] is not None
        ]
        no_cal_fail = [
            row for row in rows if row["no_calibration_min_repeat"] is None
        ]
        cal_fail = [
            row for row in rows if row["quality_calibration_min_repeat"] is None
        ]
        calibrated_all = calibrated_all and not cal_fail

        crossing = [
            row
            for row in rows
            if row["n1_no_calibration"]["worst_pair_error_upper_bound"]
            > RISK_THRESHOLD
            and row["no_calibration_min_repeat"] is not None
        ]
        repetition_crossing_exists = repetition_crossing_exists or bool(crossing)

        saving_rows = []
        for row in rows:
            no_cost = row["no_calibration_total_action_count"]
            cal_cost = row["quality_calibration_total_action_count"]
            if cal_cost is None:
                continue
            if no_cost is None or int(cal_cost) < int(no_cost):
                saving_rows.append(row)
        calibration_saves_cost = calibration_saves_cost or bool(saving_rows)

        same_quality_bottlenecks_no_cal = sum(
            row["no_calibration_at_minimum"] is not None
            and row["no_calibration_at_minimum"]["worst_pair_quality_relation"]
            == "same_quality"
            for row in rows
        )
        cross_quality_bottlenecks_no_cal = sum(
            row["no_calibration_at_minimum"] is not None
            and row["no_calibration_at_minimum"]["worst_pair_quality_relation"]
            == "cross_quality"
            for row in rows
        )

        by_transformation[transformation] = {
            "unresolved_unique_fibers": len(rows),
            "truth_weighted_cases": sum(
                int(row["truth_multiplicity"]) for row in rows
            ),
            "selected_field_count_distribution": _dist(
                [int(row["selected_field_count"]) for row in rows]
            ),
            "no_calibration_min_repeat_distribution": _dist(no_cal_repeat),
            "no_calibration_fail_by_repeat_cap": len(no_cal_fail),
            "no_calibration_repeat_mean": _mean(no_cal_repeat),
            "no_calibration_repeat_median": _median(no_cal_repeat),
            "quality_calibration_min_repeat_distribution": _dist(cal_repeat),
            "quality_calibration_fail_by_repeat_cap": len(cal_fail),
            "quality_calibration_repeat_mean": _mean(cal_repeat),
            "quality_calibration_repeat_median": _median(cal_repeat),
            "calibration_strict_total_cost_saving_fibers": len(saving_rows),
            "n1_above_threshold_then_repetition_crosses_fibers": len(crossing),
            "no_calibration_same_quality_bottleneck_at_minimum": (
                same_quality_bottlenecks_no_cal
            ),
            "no_calibration_cross_quality_bottleneck_at_minimum": (
                cross_quality_bottlenecks_no_cal
            ),
        }

    s11 = s11_rows[0]
    verdicts = {
        "H1_exact_robustness_remains_impossible": (
            "SUPPORTED" if exact_robust_failures == 0 else "REFUTED"
        ),
        "H2_repetition_reduces_pairwise_risk": (
            "SUPPORTED" if repetition_crossing_exists else "REFUTED"
        ),
        "H3_calibrated_design_reaches_threshold_all": (
            "SUPPORTED" if calibrated_all else "REFUTED"
        ),
        "H4_quality_calibration_saves_cost_exists": (
            "SUPPORTED" if calibration_saves_cost else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.bam_stochastic_assay_risk.result.v1",
        "parent_result_fingerprint": EXPECTED_PARENT,
        "risk_threshold": RISK_THRESHOLD,
        "repeat_cap": REPEAT_CAP,
        "scored_unresolved_fiber_count": len(fiber_rows),
        "finite_repeat_exact_robust_separation_count": exact_robust_failures,
        "predeclared_verdicts": verdicts,
        "by_transformation": by_transformation,
        "S11_dormant_climate": s11,
        "activation_roster": roster,
        "fiber_rows": fiber_rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "scored_unresolved_fiber_count": result["scored_unresolved_fiber_count"],
        "finite_repeat_exact_robust_separation_count": result[
            "finite_repeat_exact_robust_separation_count"
        ],
        "predeclared_verdicts": result["predeclared_verdicts"],
        "by_transformation": result["by_transformation"],
        "S11_dormant_climate": result["S11_dormant_climate"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
