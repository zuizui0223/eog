#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path

from eog.v2.bam_ecological_expansion_margin import build_expanded_ecological_lattice
from eog.v2.bam_structured_counterfactuals import (
    declared_world_counterfactual,
    expanded_variant_bam_state_key,
    expanded_variant_counterfactual,
)
from eog.v2.known_truth_bam_direct_evidence import bam_state_key
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_structured_counterfactuals_v1/protocol_v1.json"
PARENT_TARGET = ROOT / "validation/bam_counterfactual_identifiability_v1/result_summary_v1.json"
PARENT_EXPANSION = ROOT / "validation/bam_ecological_expansion_margin_v1/result_summary_v1.json"
EXPECTED_TARGET = "77314699090fd3b0a19066363eab0589c3a0c89ac41aabbce49873c84b468172"
EXPECTED_EXPANSION = "58b8412f7167672c37cd8a2e4b310362335adc71edccbd3f1c824fee23b90ade"

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


def _identified(values) -> bool:
    values = tuple(values)
    if not values:
        raise ValueError("identification target must be non-empty")
    return len(set(values)) == 1


def _fiber_summary_w0(system, survivors):
    return {
        "parameter_world_identified": len(survivors) == 1,
        "current_bam_state_identified": _identified(
            bam_state_key(world) for world in survivors
        ),
    }


def _fiber_summary_w1(system, survivors):
    return {
        "parameter_world_identified": len(survivors) == 1,
        "current_bam_state_identified": _identified(
            expanded_variant_bam_state_key(system, world) for world in survivors
        ),
    }


def _transformation_summary_w0(system, survivors, transformation):
    outcomes = [
        declared_world_counterfactual(system, world, transformation)
        for world in survivors
    ]
    exact_values = [row.counterfactual_G for row in outcomes]
    binary_values = [row.binary_decision for row in outcomes]
    return {
        "exact_map_identified": _identified(exact_values),
        "binary_decision_identified": _identified(binary_values),
        "exact_map_class_count": len(set(exact_values)),
        "binary_class_count": len(set(binary_values)),
        "binary_values": sorted(set(binary_values)),
    }


def _transformation_summary_w1(system, survivors, transformation):
    outcomes = [
        expanded_variant_counterfactual(system, world, transformation)
        for world in survivors
    ]
    exact_values = [row.counterfactual_G for row in outcomes]
    binary_values = [row.binary_decision for row in outcomes]
    return {
        "exact_map_identified": _identified(exact_values),
        "binary_decision_identified": _identified(binary_values),
        "exact_map_class_count": len(set(exact_values)),
        "binary_class_count": len(set(binary_values)),
        "binary_values": sorted(set(binary_values)),
    }


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "amended_before_implementation_and_scoring":
        raise RuntimeError("Phase-V amended protocol is not frozen")

    target_parent = json.loads(PARENT_TARGET.read_text(encoding="utf-8"))
    expansion_parent = json.loads(PARENT_EXPANSION.read_text(encoding="utf-8"))
    if target_parent.get("result_fingerprint") != EXPECTED_TARGET:
        raise RuntimeError("Phase-II parent fingerprint mismatch")
    if expansion_parent.get("result_fingerprint") != EXPECTED_EXPANSION:
        raise RuntimeError("Phase-IV parent fingerprint mismatch")

    roster = []
    fiber_rows = []
    truth_rows = []
    hierarchy_violations = 0

    dormant_alias_counts = {
        "W0": {name: 0 for name in TRANSFORMATIONS},
        "W1": {name: 0 for name in TRANSFORMATIONS},
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
        if len(lattice) != 2592:
            raise RuntimeError(f"unexpected expanded lattice size {len(lattice)}")

        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        by_G = {}
        for truth in eligible_truths:
            by_G.setdefault(int(truth.occupied_mask), []).append(truth)

        fiber_by_G = {}
        for G, truths in sorted(by_G.items()):
            w0_survivors = tuple(
                world for world in system.worlds
                if int(world.occupied_mask) == G
            )
            w1_survivors = tuple(
                world for world in lattice
                if int(world.occupied_mask) == G
            )
            if not w1_survivors:
                raise RuntimeError("W1 lost a W0 same-G fiber")

            W0 = _fiber_summary_w0(system, w0_survivors)
            W1 = _fiber_summary_w1(system, w1_survivors)
            W0["survivor_count"] = len(w0_survivors)
            W1["survivor_count"] = len(w1_survivors)
            W0["transformations"] = {}
            W1["transformations"] = {}

            for name in TRANSFORMATIONS:
                a = _transformation_summary_w0(system, w0_survivors, name)
                b = _transformation_summary_w1(system, w1_survivors, name)
                W0["transformations"][name] = a
                W1["transformations"][name] = b

                # Guaranteed coarsening is parameter world -> exact future map -> binary.
                if W0["parameter_world_identified"] and not a["exact_map_identified"]:
                    hierarchy_violations += 1
                if a["exact_map_identified"] and not a["binary_decision_identified"]:
                    hierarchy_violations += 1
                if W1["parameter_world_identified"] and not b["exact_map_identified"]:
                    hierarchy_violations += 1
                if b["exact_map_identified"] and not b["binary_decision_identified"]:
                    hierarchy_violations += 1

                if (
                    W0["current_bam_state_identified"]
                    and (
                        not a["exact_map_identified"]
                        or not a["binary_decision_identified"]
                    )
                ):
                    dormant_alias_counts["W0"][name] += 1
                if (
                    W1["current_bam_state_identified"]
                    and (
                        not b["exact_map_identified"]
                        or not b["binary_decision_identified"]
                    )
                ):
                    dormant_alias_counts["W1"][name] += 1

            record = {
                "system_id": spec.system_id,
                "G_mask": G,
                "G_count": G.bit_count(),
                "truth_multiplicity": len(truths),
                "W0": W0,
                "W1": W1,
            }
            fiber_by_G[G] = record
            fiber_rows.append(record)

        for truth in eligible_truths:
            base = fiber_by_G[int(truth.occupied_mask)]
            truth_rows.append(
                {
                    "system_id": spec.system_id,
                    "truth_world_id": truth.world_id,
                    "G_mask": int(truth.occupied_mask),
                    "W0": base["W0"],
                    "W1": base["W1"],
                }
            )

    if len(truth_rows) != 768:
        raise RuntimeError(f"expected 768 truths, got {len(truth_rows)}")
    if hierarchy_violations:
        raise RuntimeError(f"target-coarsening hierarchy violations: {hierarchy_violations}")

    by_transformation = {}
    H2_by = {}
    H4_by = {}
    any_W0_to_W1_loss = False

    for name in TRANSFORMATIONS:
        row = {}
        for universe in ("W0", "W1"):
            truths = truth_rows
            parameter_ident = sum(
                bool(truth[universe]["parameter_world_identified"])
                for truth in truths
            )
            bam_state_ident = sum(
                bool(truth[universe]["current_bam_state_identified"])
                for truth in truths
            )
            exact_ident = sum(
                bool(truth[universe]["transformations"][name]["exact_map_identified"])
                for truth in truths
            )
            binary_ident = sum(
                bool(truth[universe]["transformations"][name]["binary_decision_identified"])
                for truth in truths
            )
            exact_classes = [
                int(truth[universe]["transformations"][name]["exact_map_class_count"])
                for truth in truths
            ]
            row[universe] = {
                "parameter_world_identified": parameter_ident,
                "current_bam_state_identified": bam_state_ident,
                "exact_map_identified": exact_ident,
                "binary_decision_identified": binary_ident,
                "exact_map_class_count_distribution": _dist(exact_classes),
            }

        lost = sum(
            truth["W0"]["transformations"][name]["binary_decision_identified"]
            and not truth["W1"]["transformations"][name]["binary_decision_identified"]
            for truth in truth_rows
        )
        retained = sum(
            truth["W0"]["transformations"][name]["binary_decision_identified"]
            and truth["W1"]["transformations"][name]["binary_decision_identified"]
            for truth in truth_rows
        )
        any_W0_to_W1_loss = any_W0_to_W1_loss or lost > 0
        row["W0_binary_certificates_lost_in_W1"] = lost
        row["W0_binary_certificates_retained_in_W1"] = retained
        row["dormant_alias_reopened_fibers"] = {
            "W0": dormant_alias_counts["W0"][name],
            "W1": dormant_alias_counts["W1"][name],
        }

        H2_count = sum(
            (not truth["W0"]["parameter_world_identified"])
            and truth["W0"]["transformations"][name]["binary_decision_identified"]
            for truth in truth_rows
        )
        H4_count = sum(
            (not truth["W1"]["parameter_world_identified"])
            and truth["W1"]["transformations"][name]["binary_decision_identified"]
            for truth in truth_rows
        )
        H2_by[name] = H2_count > 0
        H4_by[name] = H4_count > 0
        row["W0_parameter_nonidentified_but_binary_identified"] = H2_count
        row["W1_parameter_nonidentified_but_binary_identified"] = H4_count
        by_transformation[name] = row

    dormant_any = any(
        count > 0
        for universe in dormant_alias_counts.values()
        for count in universe.values()
    )

    verdicts = {
        "H1_target_hierarchy_persists": "SUPPORTED",
        "H1b_dormant_alias_activation_exists": (
            "SUPPORTED" if dormant_any else "REFUTED"
        ),
        "H2_decision_without_mechanism_exists": {
            name: "SUPPORTED" if H2_by[name] else "REFUTED"
            for name in TRANSFORMATIONS
        },
        "H3_ecological_universe_expansion_can_remove_decision_certificate": (
            "SUPPORTED" if any_W0_to_W1_loss else "REFUTED"
        ),
        "H4_nontrivial_robust_decisions_exist": {
            name: "SUPPORTED" if H4_by[name] else "REFUTED"
            for name in TRANSFORMATIONS
        },
    }

    result = {
        "schema": "eog.bam_structured_counterfactuals.result.v1",
        "parent_target_fingerprint": EXPECTED_TARGET,
        "parent_expansion_fingerprint": EXPECTED_EXPANSION,
        "truth_count": len(truth_rows),
        "unique_E1_fiber_count": len(fiber_rows),
        "hierarchy_violations": hierarchy_violations,
        "dormant_alias_counts": dormant_alias_counts,
        "verdicts": verdicts,
        "by_transformation": by_transformation,
        "activation_roster": roster,
        "fiber_rows": fiber_rows,
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
        "unique_E1_fiber_count": result["unique_E1_fiber_count"],
        "hierarchy_violations": result["hierarchy_violations"],
        "dormant_alias_counts": result["dormant_alias_counts"],
        "verdicts": result["verdicts"],
        "by_transformation": result["by_transformation"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
