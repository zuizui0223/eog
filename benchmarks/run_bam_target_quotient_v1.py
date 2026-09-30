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
from eog.v2.bam_structured_counterfactuals import (
    _movement_state_for_coords,
    expanded_variant_counterfactual,
)
from eog.v2.bam_target_quotient import (
    joint_value_partition,
    partition_from_values,
    partition_relation,
    refines,
    singleton_parameter_partition,
    target_sufficient,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_target_quotient_v1/protocol_v1.json"
PARENTS = {
    "structured_counterfactuals": (
        ROOT / "validation/bam_structured_counterfactuals_v1/result_summary_v1.json",
        "f502fb647ba4666f5c40ddbd5639123f3e0296fe492dd97a1ec19ec246531cb1",
    ),
    "future_target_evidence": (
        ROOT / "validation/bam_future_target_evidence_v1/result_summary_v1.json",
        "b87bfa721e21acfdc0a03239b0ed556f77bd77e3ee49f25c11d56ece02b8db58",
    ),
    "joint_uncertainty_lattice": (
        ROOT / "validation/bam_joint_uncertainty_lattice_v1/result_summary_v1.json",
        "7dd641878ae21212de5ab9af54593498d1decae379a514346579de5642d107d9",
    ),
}
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


def _state_keys_for_lattice(system, lattice):
    tau_by_m = {}
    out = {}
    for row in lattice:
        coords = row.coordinates
        mkey = (
            coords.dispersal_radius_level,
            coords.barrier_permeable,
            coords.horizon_level,
        )
        if mkey not in tau_by_m:
            movement = _movement_state_for_coords(system, coords)
            if int(movement.accessible_mask) != int(row.movement_mask):
                raise RuntimeError("movement reconstruction mismatch in quotient audit")
            tau_by_m[mkey] = tuple(movement.first_arrival_steps)
        out[row.variant_id] = (
            int(row.abiotic_mask),
            int(row.biotic_mask),
            int(row.movement_mask),
            tau_by_m[mkey],
        )
    return out


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_computation":
        raise RuntimeError("Phase-X protocol is not frozen")

    for label, (path, expected) in PARENTS.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("result_fingerprint") != expected:
            raise RuntimeError(f"{label} parent fingerprint mismatch")

    rows = []
    roster = []
    invariant_violations = []
    examples = {
        "current_state_over_detailed": [],
        "current_state_under_detailed": [],
        "current_state_incomparable": [],
    }

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
        state_by_id = _state_keys_for_lattice(system, lattice)

        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        current_G_values = sorted({int(world.occupied_mask) for world in eligible_truths})

        for G in current_G_values:
            variants = tuple(
                sorted(
                    (row for row in lattice if int(row.occupied_mask) == G),
                    key=lambda row: row.variant_id,
                )
            )
            ids = tuple(row.variant_id for row in variants)
            parameter = singleton_parameter_partition(ids)
            current_values = {world_id: state_by_id[world_id] for world_id in ids}
            current = partition_from_values(ids, current_values)

            exact_mappings = {}
            decision_mappings = {}
            target_rows = {}

            for transformation in TRANSFORMATIONS:
                outcomes = {
                    row.variant_id: expanded_variant_counterfactual(
                        system, row, transformation
                    )
                    for row in variants
                }
                exact_values = {
                    world_id: outcome.counterfactual_G
                    for world_id, outcome in outcomes.items()
                }
                decision_values = {
                    world_id: outcome.binary_decision
                    for world_id, outcome in outcomes.items()
                }
                exact_mappings[transformation] = exact_values
                decision_mappings[transformation] = decision_values

                exact_partition = partition_from_values(ids, exact_values)
                decision_partition = partition_from_values(ids, decision_values)

                checks = {
                    "parameter_refines_exact": refines(parameter, exact_partition),
                    "parameter_refines_decision": refines(parameter, decision_partition),
                    "exact_refines_decision": refines(
                        exact_partition, decision_partition
                    ),
                }
                for check, passed in checks.items():
                    if not passed:
                        invariant_violations.append(
                            {
                                "system_id": spec.system_id,
                                "G_mask": G,
                                "transformation": transformation,
                                "check": check,
                            }
                        )

                current_exact_relation = partition_relation(
                    current,
                    exact_partition,
                    left_label="current_state",
                    right_label="exact_future",
                )
                current_decision_relation = partition_relation(
                    current,
                    decision_partition,
                    left_label="current_state",
                    right_label="decision",
                )

                target_rows[transformation] = {
                    "exact_future_blocks": exact_partition.block_count,
                    "binary_decision_blocks": decision_partition.block_count,
                    "exact_future_compression_factor": exact_partition.compression_factor,
                    "binary_decision_compression_factor": (
                        decision_partition.compression_factor
                    ),
                    "current_state_sufficient_for_exact_future": target_sufficient(
                        current, exact_partition
                    ),
                    "current_state_sufficient_for_binary_decision": target_sufficient(
                        current, decision_partition
                    ),
                    "current_vs_exact_relation": current_exact_relation,
                    "current_vs_decision_relation": current_decision_relation,
                }

                if (
                    current_decision_relation == "current_state_refines"
                    and len(examples["current_state_over_detailed"]) < 5
                ):
                    examples["current_state_over_detailed"].append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "transformation": transformation,
                            "worlds": len(ids),
                            "current_state_blocks": current.block_count,
                            "decision_blocks": decision_partition.block_count,
                        }
                    )
                if (
                    current_decision_relation == "decision_refines"
                    and len(examples["current_state_under_detailed"]) < 5
                ):
                    examples["current_state_under_detailed"].append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "transformation": transformation,
                            "worlds": len(ids),
                            "current_state_blocks": current.block_count,
                            "decision_blocks": decision_partition.block_count,
                        }
                    )
                if (
                    current_decision_relation == "incomparable"
                    and len(examples["current_state_incomparable"]) < 5
                ):
                    examples["current_state_incomparable"].append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "transformation": transformation,
                            "worlds": len(ids),
                            "current_state_blocks": current.block_count,
                            "decision_blocks": decision_partition.block_count,
                        }
                    )

            joint_exact = joint_value_partition(
                ids,
                tuple(exact_mappings[t] for t in TRANSFORMATIONS),
            )
            joint_decision = joint_value_partition(
                ids,
                tuple(decision_mappings[t] for t in TRANSFORMATIONS),
            )

            for transformation in TRANSFORMATIONS:
                single_exact = partition_from_values(
                    ids, exact_mappings[transformation]
                )
                single_decision = partition_from_values(
                    ids, decision_mappings[transformation]
                )
                if not refines(joint_exact, single_exact):
                    invariant_violations.append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "check": f"joint_exact_refines_{transformation}",
                        }
                    )
                if not refines(joint_decision, single_decision):
                    invariant_violations.append(
                        {
                            "system_id": spec.system_id,
                            "G_mask": G,
                            "check": f"joint_decision_refines_{transformation}",
                        }
                    )
            if not refines(parameter, current):
                invariant_violations.append(
                    {
                        "system_id": spec.system_id,
                        "G_mask": G,
                        "check": "parameter_refines_current",
                    }
                )
            if not refines(parameter, joint_exact):
                invariant_violations.append(
                    {
                        "system_id": spec.system_id,
                        "G_mask": G,
                        "check": "parameter_refines_joint_exact",
                    }
                )
            if not refines(parameter, joint_decision):
                invariant_violations.append(
                    {
                        "system_id": spec.system_id,
                        "G_mask": G,
                        "check": "parameter_refines_joint_decision",
                    }
                )
            if not refines(joint_exact, joint_decision):
                invariant_violations.append(
                    {
                        "system_id": spec.system_id,
                        "G_mask": G,
                        "check": "joint_exact_refines_joint_decision",
                    }
                )

            current_joint_relation = partition_relation(
                current,
                joint_decision,
                left_label="current_state",
                right_label="joint_decision",
            )

            truth_multiplicity = sum(
                int(world.occupied_mask) == G for world in eligible_truths
            )
            rows.append(
                {
                    "system_id": spec.system_id,
                    "G_mask": G,
                    "G_count": G.bit_count(),
                    "truth_multiplicity": truth_multiplicity,
                    "W1_same_G_worlds": len(ids),
                    "parameter_world_blocks": parameter.block_count,
                    "current_state_blocks": current.block_count,
                    "joint_exact_suite_blocks": joint_exact.block_count,
                    "joint_decision_suite_blocks": joint_decision.block_count,
                    "joint_decision_compression_factor": (
                        joint_decision.compression_factor
                    ),
                    "current_vs_joint_decision_relation": current_joint_relation,
                    "current_state_sufficient_for_joint_decision": target_sufficient(
                        current, joint_decision
                    ),
                    "targets": target_rows,
                }
            )

    if invariant_violations:
        raise RuntimeError(
            f"target quotient invariant violations: {len(invariant_violations)}"
        )
    if len(rows) != 129:
        raise RuntimeError(f"expected 129 W1 current-G fibers, got {len(rows)}")

    by_transformation = {}
    for transformation in TRANSFORMATIONS:
        relations = [
            row["targets"][transformation]["current_vs_decision_relation"]
            for row in rows
        ]
        exact_relations = [
            row["targets"][transformation]["current_vs_exact_relation"]
            for row in rows
        ]
        decision_blocks = [
            row["targets"][transformation]["binary_decision_blocks"]
            for row in rows
        ]
        exact_blocks = [
            row["targets"][transformation]["exact_future_blocks"]
            for row in rows
        ]
        by_transformation[transformation] = {
            "current_vs_binary_relation_counts": dict(
                sorted(Counter(relations).items())
            ),
            "current_vs_exact_relation_counts": dict(
                sorted(Counter(exact_relations).items())
            ),
            "current_state_sufficient_for_binary_fibers": sum(
                row["targets"][transformation][
                    "current_state_sufficient_for_binary_decision"
                ]
                for row in rows
            ),
            "current_state_insufficient_for_binary_fibers": sum(
                not row["targets"][transformation][
                    "current_state_sufficient_for_binary_decision"
                ]
                for row in rows
            ),
            "binary_decision_block_distribution": _dist(decision_blocks),
            "exact_future_block_distribution": _dist(exact_blocks),
        }

    joint_relations = [
        row["current_vs_joint_decision_relation"] for row in rows
    ]
    world_counts = [row["W1_same_G_worlds"] for row in rows]
    current_blocks = [row["current_state_blocks"] for row in rows]
    joint_blocks = [row["joint_decision_suite_blocks"] for row in rows]
    compression = [row["joint_decision_compression_factor"] for row in rows]

    result = {
        "schema": "eog.bam_target_quotient.result.v1",
        "fiber_count": len(rows),
        "required_invariant_violation_count": len(invariant_violations),
        "by_transformation": by_transformation,
        "joint_decision_suite": {
            "current_vs_joint_relation_counts": dict(
                sorted(Counter(joint_relations).items())
            ),
            "current_state_sufficient_fibers": sum(
                row["current_state_sufficient_for_joint_decision"]
                for row in rows
            ),
            "current_state_insufficient_fibers": sum(
                not row["current_state_sufficient_for_joint_decision"]
                for row in rows
            ),
            "parameter_world_count_distribution": _dist(world_counts),
            "current_state_block_distribution": _dist(current_blocks),
            "joint_decision_block_distribution": _dist(joint_blocks),
            "joint_decision_compression_factor_mean": _mean(compression),
            "joint_decision_compression_factor_median": _median(compression),
            "joint_decision_compression_factor_maximum": max(compression),
        },
        "examples": examples,
        "activation_roster": roster,
        "rows": rows,
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
        "fiber_count": result["fiber_count"],
        "required_invariant_violation_count": result[
            "required_invariant_violation_count"
        ],
        "by_transformation": result["by_transformation"],
        "joint_decision_suite": result["joint_decision_suite"],
        "examples": result["examples"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
