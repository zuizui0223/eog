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
    repeat_equivalence_violations_deterministic,
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
PROTOCOL = ROOT / "validation/bam_future_assay_observation_v1/protocol_v1.json"
PARENT = ROOT / "validation/bam_future_target_evidence_v1/result_summary_v1.json"
EXPECTED_PARENT = "b87bfa721e21acfdc0a03239b0ed556f77bd77e3ee49f25c11d56ece02b8db58"
TRANSFORMATIONS = ("climate_shift", "biotic_stress", "barrier_restoration")


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


def _plan_row(plan):
    return {
        "minimum_size": plan.minimum_size,
        "minimum_action_ids": (
            None if plan.minimum_action_ids is None else list(plan.minimum_action_ids)
        ),
        "all_target_pairs_separated": bool(plan.all_target_pairs_separated),
        "insufficient_action_library": bool(plan.insufficient_action_library),
        "target_discordant_pair_count": int(plan.target_discordant_pair_count),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-VII protocol is not frozen")
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    if parent.get("result_fingerprint") != EXPECTED_PARENT:
        raise RuntimeError("Phase-VI parent fingerprint mismatch")

    assay_ids = tuple(f"assay:{field}" for field in PARAMETER_FIELDS)
    repeat_ids = tuple(f"repeat2:{field}" for field in PARAMETER_FIELDS)
    assay_repeat_ids = tuple(sorted((*assay_ids, *repeat_ids)))
    calibrated_ids = tuple(sorted((*assay_ids, "assay_process_calibration")))
    full_ids = tuple(sorted((*assay_ids, *repeat_ids, "assay_process_calibration")))

    roster = []
    fiber_rows = []
    repeat_violations = 0
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
            if not variants:
                raise RuntimeError("W1 same-G fiber unexpectedly empty")

            for transformation in TRANSFORMATIONS:
                target = {
                    row.variant_id: expanded_variant_counterfactual(
                        system, row, transformation
                    ).binary_decision
                    for row in variants
                }
                target_values = tuple(sorted(set(bool(v) for v in target.values())))
                if len(target_values) <= 1:
                    continue

                hypotheses = build_joint_hypotheses(variants, target)
                actions = build_action_supports(variants, hypotheses)
                violations = repeat_equivalence_violations_deterministic(hypotheses, actions)
                repeat_violations += violations

                assay_only = exact_minimum_deterministic_target_design(
                    hypotheses,
                    actions,
                    available_action_ids=assay_ids,
                )
                assay_repeat = exact_minimum_deterministic_target_design(
                    hypotheses,
                    actions,
                    available_action_ids=assay_repeat_ids,
                )
                calibrated = exact_minimum_deterministic_target_design(
                    hypotheses,
                    actions,
                    available_action_ids=calibrated_ids,
                )
                full = exact_minimum_deterministic_target_design(
                    hypotheses,
                    actions,
                    available_action_ids=full_ids,
                )

                if (
                    assay_only.minimum_size != assay_repeat.minimum_size
                    or assay_only.all_target_pairs_separated
                    != assay_repeat.all_target_pairs_separated
                ):
                    raise RuntimeError(
                        f"repeat-only design changed robust sufficiency: "
                        f"{spec.system_id} G={G} {transformation}"
                    )
                if full.minimum_size != calibrated.minimum_size:
                    raise RuntimeError(
                        f"repeat actions unexpectedly improved calibrated minimum: "
                        f"{spec.system_id} G={G} {transformation}"
                    )

                row = {
                    "system_id": spec.system_id,
                    "G_mask": G,
                    "G_count": G.bit_count(),
                    "truth_multiplicity": len(truths),
                    "W1_same_G_variants": len(variants),
                    "transformation": transformation,
                    "binary_target_values": list(target_values),
                    "joint_hypothesis_count": len(hypotheses),
                    "repeat_equivalence_violations": violations,
                    "assay_only": _plan_row(assay_only),
                    "assay_plus_repeat": _plan_row(assay_repeat),
                    "calibration_plus_assays": _plan_row(calibrated),
                    "full_action_library": _plan_row(full),
                }
                fiber_rows.append(row)

                if (
                    spec.system_id == "S11_9x5_gap"
                    and G == 2138792820255
                    and transformation == "climate_shift"
                ):
                    s11_rows.append(row)

    if repeat_violations:
        raise RuntimeError(
            f"same-assay repeat robust coverage violations: {repeat_violations}"
        )
    if not fiber_rows:
        raise RuntimeError("no future-target-unresolved W1 fibers were scored")
    if len(s11_rows) != 1:
        raise RuntimeError(
            f"expected exactly one S11 dormant climate fiber, got {len(s11_rows)}"
        )

    by_transformation = {}
    any_calibration_necessary = False
    all_restored = True
    canonical_action_frequency = {}

    for transformation in TRANSFORMATIONS:
        rows = [row for row in fiber_rows if row["transformation"] == transformation]
        assay_solvable = [
            row for row in rows if row["assay_only"]["all_target_pairs_separated"]
        ]
        assay_impossible = [
            row for row in rows if not row["assay_only"]["all_target_pairs_separated"]
        ]
        restored = [
            row
            for row in assay_impossible
            if row["calibration_plus_assays"]["all_target_pairs_separated"]
        ]
        not_restored = [
            row
            for row in rows
            if not row["calibration_plus_assays"]["all_target_pairs_separated"]
        ]
        any_calibration_necessary = any_calibration_necessary or bool(restored)
        all_restored = all_restored and not not_restored

        finite_sizes = [
            int(row["calibration_plus_assays"]["minimum_size"])
            for row in rows
            if row["calibration_plus_assays"]["minimum_size"] is not None
        ]
        assay_sizes = [
            int(row["assay_only"]["minimum_size"])
            for row in assay_solvable
            if row["assay_only"]["minimum_size"] is not None
        ]

        freq = Counter()
        calibration_in_minimum = 0
        for row in rows:
            ids = row["calibration_plus_assays"]["minimum_action_ids"]
            if ids is None:
                continue
            for action_id in ids:
                freq[action_id] += 1
            if "assay_process_calibration" in ids:
                calibration_in_minimum += 1
        canonical_action_frequency[transformation] = dict(sorted(freq.items()))

        truth_weight = sum(int(row["truth_multiplicity"]) for row in rows)
        truth_weight_assay_impossible = sum(
            int(row["truth_multiplicity"]) for row in assay_impossible
        )
        truth_weight_calibration_minimum = sum(
            int(row["truth_multiplicity"])
            for row in rows
            if row["calibration_plus_assays"]["minimum_action_ids"] is not None
            and "assay_process_calibration"
            in row["calibration_plus_assays"]["minimum_action_ids"]
        )

        by_transformation[transformation] = {
            "unresolved_unique_fibers": len(rows),
            "truth_weighted_unresolved_cases": truth_weight,
            "assay_only_robust_solvable_fibers": len(assay_solvable),
            "assay_only_robust_impossible_fibers": len(assay_impossible),
            "assay_only_robust_impossible_truth_weight": truth_weight_assay_impossible,
            "calibration_restored_fibers": len(restored),
            "calibration_failed_fibers": len(not_restored),
            "calibration_in_canonical_minimum_fibers": calibration_in_minimum,
            "calibration_in_canonical_minimum_truth_weight": (
                truth_weight_calibration_minimum
            ),
            "assay_only_minimum_size_distribution": _dist(assay_sizes),
            "robust_minimum_size_distribution": _dist(finite_sizes),
            "robust_minimum_size_mean": _mean(finite_sizes),
            "robust_minimum_size_median": _median(finite_sizes),
            "canonical_minimum_action_frequency": canonical_action_frequency[
                transformation
            ],
        }

    s11 = s11_rows[0]
    s11_expected = tuple(
        sorted(("assay:A_level", "assay_process_calibration"))
    )
    s11_minimum = s11["calibration_plus_assays"]["minimum_action_ids"]
    H3 = (
        s11["assay_only"]["minimum_size"] is None
        and s11["assay_plus_repeat"]["minimum_size"] is None
        and s11["calibration_plus_assays"]["minimum_size"] == 2
        and tuple(s11_minimum or ()) == s11_expected
    )

    verdicts = {
        "H1_repeat_same_assay_no_extra_robust_split": (
            "SUPPORTED" if repeat_violations == 0 else "REFUTED"
        ),
        "H2_calibration_necessity_exists": (
            "SUPPORTED" if any_calibration_necessary else "REFUTED"
        ),
        "H3_S11_climate_minimum": "SUPPORTED" if H3 else "REFUTED",
        "H4_calibration_plus_assays_restores_all": (
            "SUPPORTED" if all_restored else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.bam_future_assay_observation.result.v1",
        "parent_result_fingerprint": EXPECTED_PARENT,
        "scored_unresolved_fiber_count": len(fiber_rows),
        "repeat_equivalence_violations": repeat_violations,
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
        "repeat_equivalence_violations": result["repeat_equivalence_violations"],
        "predeclared_verdicts": result["predeclared_verdicts"],
        "by_transformation": result["by_transformation"],
        "S11_dormant_climate": result["S11_dormant_climate"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
