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
    ecological_flip_margin,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_ecological_expansion_margin_v1/protocol_v1.json"
PARENT_TARGET = ROOT / "validation/bam_counterfactual_identifiability_v1/result_summary_v1.json"
PARENT_LOGICAL = ROOT / "validation/bam_decision_robustness_margin_v1/result_summary_v1.json"
EXPECTED_TARGET = "77314699090fd3b0a19066363eab0589c3a0c89ac41aabbce49873c84b468172"
EXPECTED_LOGICAL = "ffd0d11bbe75d4e27cc8918ab77a95e991ab52b43bd39ee83ce81b8a3bd52050"


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


def _median(values):
    return None if not values else float(statistics.median(values))


def _mean(values):
    return None if not values else float(statistics.mean(values))


def _decision_from_world(world, axis):
    G = int(world.occupied_mask)
    if axis == "A":
        released = int(world.biotic_mask & world.movement_mask)
    elif axis == "B":
        released = int(world.abiotic_mask & world.movement_mask)
    elif axis == "M":
        released = int(world.abiotic_mask & world.biotic_mask)
    else:
        raise ValueError(axis)
    return bool(released & ~G)


def _irrelevant_axis_audit(lattice, axis):
    if axis == "A":
        key = lambda row: (row.biotic_mask, row.movement_mask, row.occupied_mask)
    elif axis == "B":
        key = lambda row: (row.abiotic_mask, row.movement_mask, row.occupied_mask)
    elif axis == "M":
        key = lambda row: (row.abiotic_mask, row.biotic_mask, row.occupied_mask)
    else:
        raise ValueError(axis)

    groups = {}
    for row in lattice:
        groups.setdefault(key(row), set()).add(row.release_expands(axis))
    return sum(len(values) > 1 for values in groups.values())


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("Phase-IV protocol is not frozen")

    parent_target = json.loads(PARENT_TARGET.read_text(encoding="utf-8"))
    parent_logical = json.loads(PARENT_LOGICAL.read_text(encoding="utf-8"))
    if parent_target.get("result_fingerprint") != EXPECTED_TARGET:
        raise RuntimeError("Phase-II parent fingerprint mismatch")
    if parent_logical.get("result_fingerprint") != EXPECTED_LOGICAL:
        raise RuntimeError("Phase-III parent fingerprint mismatch")

    axes = ("A", "B", "M")
    roster = []
    fiber_rows = []
    truth_rows = []
    irrelevant_axis_violations = 0

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
            raise RuntimeError(f"unexpected lattice size: {len(lattice)}")
        for axis in axes:
            irrelevant_axis_violations += _irrelevant_axis_audit(lattice, axis)

        source_id = f"r{system.landscape.height // 2}c0"
        eligible_truths = tuple(
            world
            for world in system.worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        by_G = {}
        for truth in eligible_truths:
            by_G.setdefault(int(truth.occupied_mask), []).append(truth)

        fiber_result_by_G = {}
        for G, truths in sorted(by_G.items()):
            survivor_ids = tuple(
                world.world_id
                for world in system.worlds
                if int(world.occupied_mask) == G
            )
            axis_rows = {}
            for axis in axes:
                margin = ecological_flip_margin(
                    system,
                    survivor_ids,
                    lattice,
                    axis=axis,
                )
                axis_rows[axis] = {
                    "identified_in_declared_universe": margin.identified_in_declared_universe,
                    "current_decision": margin.current_decision,
                    "minimum_ecological_distance": margin.minimum_distance,
                    "nearest_variant_count": len(margin.nearest_variant_ids),
                    "nearest_variant_ids": list(margin.nearest_variant_ids[:20]),
                    "nearest_changed_dimensions": list(margin.nearest_changed_dimensions),
                    "eligible_same_G_expanded_worlds": margin.eligible_same_G_expanded_worlds,
                    "opposite_decision_expanded_worlds": margin.opposite_decision_expanded_worlds,
                }
            record = {
                "system_id": spec.system_id,
                "G_mask": G,
                "G_count": G.bit_count(),
                "truth_multiplicity": len(truths),
                "survivor_count": len(survivor_ids),
                "expanded_lattice_size": len(lattice),
                "axes": axis_rows,
            }
            fiber_result_by_G[G] = record
            fiber_rows.append(record)

        for truth in eligible_truths:
            record = fiber_result_by_G[int(truth.occupied_mask)]
            truth_rows.append(
                {
                    "system_id": spec.system_id,
                    "truth_world_id": truth.world_id,
                    "G_mask": int(truth.occupied_mask),
                    "G_count": len(truth.occupied_ids),
                    "axes": record["axes"],
                }
            )

    if len(truth_rows) != 768:
        raise RuntimeError(f"expected 768 frozen truths, got {len(truth_rows)}")
    if irrelevant_axis_violations:
        raise RuntimeError(
            f"irrelevant-axis invariance violations: {irrelevant_axis_violations}"
        )

    H1 = False
    H2 = False
    axes_with_directional_asymmetry = 0
    by_axis = {}

    for axis in axes:
        identified = [
            row for row in truth_rows
            if row["axes"][axis]["identified_in_declared_universe"]
        ]
        unresolved = [
            row for row in truth_rows
            if not row["axes"][axis]["identified_in_declared_universe"]
        ]
        finite = [
            row for row in identified
            if row["axes"][axis]["minimum_ecological_distance"] is not None
        ]
        no_counterexample = [
            row for row in identified
            if row["axes"][axis]["minimum_ecological_distance"] is None
        ]
        margins = [
            int(row["axes"][axis]["minimum_ecological_distance"])
            for row in finite
        ]
        H1 = H1 or any(value == 1 for value in margins)
        H2 = H2 or any(value >= 2 for value in margins) or bool(no_counterexample)

        by_decision = {}
        medians = {}
        for decision in (False, True):
            subset = [
                row for row in finite
                if row["axes"][axis]["current_decision"] is decision
            ]
            vals = [
                int(row["axes"][axis]["minimum_ecological_distance"])
                for row in subset
            ]
            medians[decision] = _median(vals)
            by_decision[str(decision).lower()] = {
                "finite_counterexample_truths": len(subset),
                "margin_distribution": _dist(vals),
                "median_margin": _median(vals),
                "mean_margin": _mean(vals),
                "maximum_margin": None if not vals else max(vals),
            }
        if (
            medians[True] is not None
            and medians[False] is not None
            and medians[True] > medians[False]
        ):
            axes_with_directional_asymmetry += 1

        fiber_identified = [
            row for row in fiber_rows
            if row["axes"][axis]["identified_in_declared_universe"]
        ]
        fiber_finite = [
            row for row in fiber_identified
            if row["axes"][axis]["minimum_ecological_distance"] is not None
        ]
        fiber_margins = [
            int(row["axes"][axis]["minimum_ecological_distance"])
            for row in fiber_finite
        ]

        changed_counter = Counter()
        for row in finite:
            for dim in row["axes"][axis]["nearest_changed_dimensions"]:
                changed_counter[dim] += 1

        by_axis[axis] = {
            "truth_weighted": {
                "identified_in_declared_universe": len(identified),
                "unresolved_in_declared_universe": len(unresolved),
                "finite_ecological_counterexample_truths": len(finite),
                "no_counterexample_in_frozen_lattice": len(no_counterexample),
                "margin_distribution": _dist(margins),
                "margin_1_count": sum(value == 1 for value in margins),
                "median_margin": _median(margins),
                "mean_margin": _mean(margins),
                "maximum_margin": None if not margins else max(margins),
                "nearest_changed_dimension_frequency": dict(sorted(changed_counter.items())),
                "by_current_decision": by_decision,
            },
            "unique_fiber": {
                "identified_fibers": len(fiber_identified),
                "finite_ecological_counterexample_fibers": len(fiber_finite),
                "no_counterexample_in_frozen_lattice": len(fiber_identified) - len(fiber_finite),
                "margin_distribution": _dist(fiber_margins),
                "median_margin": _median(fiber_margins),
                "mean_margin": _mean(fiber_margins),
                "maximum_margin": None if not fiber_margins else max(fiber_margins),
            },
        }

    verdicts = {
        "H1_one_step_fragility_exists": "SUPPORTED" if H1 else "REFUTED",
        "H2_nontrivial_robustness_exists": "SUPPORTED" if H2 else "REFUTED",
        "H3_irrelevant_axis_invariance": (
            "SUPPORTED" if irrelevant_axis_violations == 0 else "REFUTED"
        ),
        "H4_directional_margin_asymmetry": (
            "SUPPORTED" if axes_with_directional_asymmetry >= 2 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.bam_ecological_expansion_margin.result.v1",
        "parent_target_fingerprint": EXPECTED_TARGET,
        "parent_logical_margin_fingerprint": EXPECTED_LOGICAL,
        "truth_count": len(truth_rows),
        "unique_E1_fiber_count": len(fiber_rows),
        "expanded_worlds_per_system": 2592,
        "irrelevant_axis_invariance_violations": irrelevant_axis_violations,
        "axes_with_directional_margin_asymmetry": axes_with_directional_asymmetry,
        "verdicts": verdicts,
        "by_axis": by_axis,
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
        "expanded_worlds_per_system": result["expanded_worlds_per_system"],
        "verdicts": result["verdicts"],
        "by_axis": result["by_axis"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
