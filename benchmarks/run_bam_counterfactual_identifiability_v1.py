#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

from eog.v2.bam_counterfactual_identifiability import (
    axis_release_outcome,
    exact_minimum_truth_target_measurements,
    joint_release_signature,
    release_expands_current,
    target_identified,
    truth_relative_direct_measurements,
)
from eog.v2.known_truth_bam_direct_evidence import bam_state_key
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_counterfactual_identifiability_v1/protocol_v1.json"
PARENT_RESULT = ROOT / "validation/known_truth_bam_v3/result_summary_v3.json"
EXPECTED_PARENT_FINGERPRINT = "7bbc2683dee1f277474995e84d44a2b840abc4d57e429276880233bea5225415"


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


def _eligible_truths(system):
    source_id = f"r{system.landscape.height // 2}c0"
    return tuple(
        world
        for world in system.worlds
        if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
    )


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("counterfactual protocol is not frozen")

    parent = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    if parent.get("fingerprint") != EXPECTED_PARENT_FINGERPRINT:
        raise RuntimeError("frozen deterministic BAM parent fingerprint mismatch")

    axes = ("A", "B", "M")
    roster = []
    truth_rows = []

    h1_exists = False
    h2_exists = False
    h3_violations = 0
    h4_exists = False

    state_burdens = []
    per_axis = {
        axis: {
            "exact_divergent": 0,
            "binary_divergent": 0,
            "exact_identified": 0,
            "binary_identified": 0,
            "exact_burdens": [],
            "binary_burdens": [],
            "strict_binary_savings": 0,
            "strict_exact_savings": 0,
        }
        for axis in axes
    }
    nonidentified_truths = 0
    harmless_all_binary_truths = 0
    consequential_exact_truths = 0
    joint_signature_class_counts = []

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

        worlds = system.worlds
        by_id = {world.world_id: world for world in worlds}
        eligible = _eligible_truths(system)

        for truth in eligible:
            survivors = tuple(
                world.world_id
                for world in worlds
                if world.occupied_mask == truth.occupied_mask
            )
            state_target = {
                world_id: bam_state_key(by_id[world_id])
                for world_id in survivors
            }
            state_identified = target_identified(survivors, state_target)
            if not state_identified:
                nonidentified_truths += 1

            measurements = truth_relative_direct_measurements(
                worlds,
                truth,
                survivors,
                include_arrival=True,
            )
            state_plan = exact_minimum_truth_target_measurements(
                survivors,
                truth.world_id,
                state_target,
                measurements,
            )
            if state_plan.minimum_size is None:
                raise RuntimeError(
                    f"full BAM state not resolvable by complete direct library: "
                    f"{spec.system_id} {truth.world_id}"
                )
            state_burdens.append(state_plan.minimum_size)

            axis_rows = {}
            any_exact_divergence = False
            all_binary_identified = True

            joint_targets = {
                world_id: joint_release_signature(by_id[world_id])
                for world_id in survivors
            }
            joint_signature_class_counts.append(len(set(joint_targets.values())))

            for axis in axes:
                exact_target = {
                    world_id: axis_release_outcome(by_id[world_id], axis)
                    for world_id in survivors
                }
                binary_target = {
                    world_id: release_expands_current(by_id[world_id], axis)
                    for world_id in survivors
                }

                exact_is_identified = target_identified(survivors, exact_target)
                binary_is_identified = target_identified(survivors, binary_target)
                if exact_is_identified:
                    per_axis[axis]["exact_identified"] += 1
                else:
                    per_axis[axis]["exact_divergent"] += 1
                    any_exact_divergence = True
                if binary_is_identified:
                    per_axis[axis]["binary_identified"] += 1
                else:
                    per_axis[axis]["binary_divergent"] += 1
                    all_binary_identified = False

                exact_plan = exact_minimum_truth_target_measurements(
                    survivors,
                    truth.world_id,
                    exact_target,
                    measurements,
                )
                binary_plan = exact_minimum_truth_target_measurements(
                    survivors,
                    truth.world_id,
                    binary_target,
                    measurements,
                )
                if exact_plan.minimum_size is None or binary_plan.minimum_size is None:
                    raise RuntimeError(
                        f"counterfactual target not resolvable by complete direct library: "
                        f"{spec.system_id} {truth.world_id} axis={axis}"
                    )

                per_axis[axis]["exact_burdens"].append(exact_plan.minimum_size)
                per_axis[axis]["binary_burdens"].append(binary_plan.minimum_size)

                if not (
                    binary_plan.minimum_size
                    <= exact_plan.minimum_size
                    <= state_plan.minimum_size
                ):
                    h3_violations += 1

                if binary_plan.minimum_size < state_plan.minimum_size:
                    per_axis[axis]["strict_binary_savings"] += 1
                    h4_exists = True
                if exact_plan.minimum_size < state_plan.minimum_size:
                    per_axis[axis]["strict_exact_savings"] += 1

                axis_rows[axis] = {
                    "exact_class_count": len(set(exact_target.values())),
                    "binary_class_count": len(set(binary_target.values())),
                    "truth_exact_outcome": int(exact_target[truth.world_id]),
                    "truth_binary_expands": bool(binary_target[truth.world_id]),
                    "minimum_exact_measurements": exact_plan.minimum_size,
                    "minimum_binary_measurements": binary_plan.minimum_size,
                }

            if not state_identified and any_exact_divergence:
                h1_exists = True
                consequential_exact_truths += 1
            if not state_identified and all_binary_identified:
                h2_exists = True
                harmless_all_binary_truths += 1

            truth_rows.append(
                {
                    "system_id": spec.system_id,
                    "truth_world_id": truth.world_id,
                    "current_G_count": len(truth.occupied_ids),
                    "E1_survivor_count": len(survivors),
                    "E1_bam_state_count": len(set(state_target.values())),
                    "bam_state_identified": state_identified,
                    "minimum_bam_state_measurements": state_plan.minimum_size,
                    "joint_release_signature_class_count": len(set(joint_targets.values())),
                    "probes": axis_rows,
                }
            )

    truth_count = len(truth_rows)
    if truth_count != 768:
        raise RuntimeError(f"expected frozen 768 truth cases, got {truth_count}")

    summary_by_axis = {}
    for axis in axes:
        row = per_axis[axis]
        summary_by_axis[axis] = {
            "exact_identified_truths": row["exact_identified"],
            "exact_divergent_truths": row["exact_divergent"],
            "binary_identified_truths": row["binary_identified"],
            "binary_divergent_truths": row["binary_divergent"],
            "minimum_exact_measurement_distribution": _dist(row["exact_burdens"]),
            "minimum_binary_measurement_distribution": _dist(row["binary_burdens"]),
            "strict_exact_saving_vs_bam_state": row["strict_exact_savings"],
            "strict_binary_saving_vs_bam_state": row["strict_binary_savings"],
        }

    verdicts = {
        "H1_counterfactual_divergence_exists": "SUPPORTED" if h1_exists else "REFUTED",
        "H2_harmless_nonidentification_exists": "SUPPORTED" if h2_exists else "REFUTED",
        "H3_target_coarsening_burden_monotonicity": (
            "SUPPORTED" if h3_violations == 0 else "REFUTED"
        ),
        "H4_strict_decision_saving_exists": "SUPPORTED" if h4_exists else "REFUTED",
    }

    result = {
        "schema": "eog.bam_counterfactual_identifiability.result.v1",
        "protocol_status": protocol["status"],
        "parent_fingerprint": EXPECTED_PARENT_FINGERPRINT,
        "system_roster_size": len(SYSTEM_SPECS),
        "eligible_system_count": sum(row["activation_status"] == "PASS" for row in roster),
        "truth_count": truth_count,
        "bam_state_nonidentified_truths_at_E1": nonidentified_truths,
        "bam_state_identified_truths_at_E1": truth_count - nonidentified_truths,
        "consequential_exact_counterfactual_truths": consequential_exact_truths,
        "harmless_all_binary_release_truths": harmless_all_binary_truths,
        "full_bam_state_minimum_measurement_distribution": _dist(state_burdens),
        "joint_release_signature_class_count_distribution": _dist(
            joint_signature_class_counts
        ),
        "by_axis": summary_by_axis,
        "H3_monotonicity_violations": h3_violations,
        "verdicts": verdicts,
        "roster": roster,
        "truth_rows": truth_rows,
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
        "truth_count": result["truth_count"],
        "bam_state_nonidentified_truths_at_E1": result["bam_state_nonidentified_truths_at_E1"],
        "consequential_exact_counterfactual_truths": result["consequential_exact_counterfactual_truths"],
        "harmless_all_binary_release_truths": result["harmless_all_binary_release_truths"],
        "by_axis": result["by_axis"],
        "verdicts": result["verdicts"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
