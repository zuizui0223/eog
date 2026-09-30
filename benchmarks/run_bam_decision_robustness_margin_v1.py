#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import statistics

from eog.v2.bam_decision_robustness_margin import (
    survivor_fiber_completion_margin,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    audit_system_activation,
    build_generality_system,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/bam_decision_robustness_margin_v1/protocol_v1.json"
PARENT = ROOT / "validation/bam_counterfactual_identifiability_v1/result_summary_v1.json"
EXPECTED_PARENT = "77314699090fd3b0a19066363eab0589c3a0c89ac41aabbce49873c84b468172"


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


def run() -> dict[str, object]:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_implementation_and_scoring":
        raise RuntimeError("decision robustness protocol is not frozen")

    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    if parent.get("result_fingerprint") != EXPECTED_PARENT:
        raise RuntimeError("Phase-II parent result fingerprint mismatch")

    axes = ("A", "B", "M")
    truth_rows = []
    fiber_records = {}
    activation_roster = []

    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        activation = audit_system_activation(system)
        activation_roster.append(
            {
                "system_id": spec.system_id,
                "status": activation.status,
                "system_fingerprint": system.fingerprint,
                "activation_fingerprint": activation.fingerprint,
            }
        )
        if activation.status != "PASS":
            continue

        worlds = system.worlds
        source_id = f"r{system.landscape.height // 2}c0"
        eligible = tuple(
            world
            for world in worlds
            if len(world.occupied_ids) >= 2 and source_id in world.occupied_ids
        )
        by_G = {}
        for truth in eligible:
            by_G.setdefault(int(truth.occupied_mask), []).append(truth)

        for G, truths in sorted(by_G.items()):
            survivors = tuple(
                world.world_id for world in worlds if int(world.occupied_mask) == G
            )
            fiber_key = f"{spec.system_id}|G={G}"
            fiber_axis = {}
            for axis in axes:
                margin = survivor_fiber_completion_margin(
                    worlds, survivors, axis=axis
                )
                fiber_axis[axis] = {
                    "identified_in_declared_universe": margin.identified_in_declared_universe,
                    "current_decision": margin.current_decision,
                    "completion_flip_margin": margin.completion_flip_margin,
                    "full_completion_outcomes": sorted(margin.full_completion_outcomes),
                }
            fiber_records[fiber_key] = {
                "system_id": spec.system_id,
                "G_mask": G,
                "G_count": G.bit_count(),
                "node_count": len(system.landscape.node_ids),
                "truth_multiplicity": len(truths),
                "survivor_count": len(survivors),
                "axes": fiber_axis,
            }

        for truth in eligible:
            G = int(truth.occupied_mask)
            survivors = tuple(
                world.world_id for world in worlds if int(world.occupied_mask) == G
            )
            axis_rows = {}
            for axis in axes:
                margin = survivor_fiber_completion_margin(
                    worlds, survivors, axis=axis
                )
                axis_rows[axis] = {
                    "identified_in_declared_universe": margin.identified_in_declared_universe,
                    "current_decision": margin.current_decision,
                    "completion_flip_margin": margin.completion_flip_margin,
                    "full_completion_outcomes": sorted(margin.full_completion_outcomes),
                }
            truth_rows.append(
                {
                    "system_id": spec.system_id,
                    "truth_world_id": truth.world_id,
                    "G_mask": G,
                    "G_count": G.bit_count(),
                    "node_count": len(truth.node_ids),
                    "survivor_count": len(survivors),
                    "axes": axis_rows,
                }
            )

    if len(truth_rows) != 768:
        raise RuntimeError(f"expected 768 frozen truths, got {len(truth_rows)}")

    by_axis = {}
    theorem_violations = 0
    for axis in axes:
        identified = [row for row in truth_rows if row["axes"][axis]["identified_in_declared_universe"]]
        unresolved = [row for row in truth_rows if not row["axes"][axis]["identified_in_declared_universe"]]
        margins = [row["axes"][axis]["completion_flip_margin"] for row in identified]
        finite_margins = [int(v) for v in margins if v is not None]
        full_G_identified = [
            row for row in identified if row["G_count"] == row["node_count"]
        ]
        proper_G_identified = [
            row for row in identified if row["G_count"] < row["node_count"]
        ]
        if any(
            row["axes"][axis]["full_completion_outcomes"] != [False, True]
            for row in proper_G_identified
        ):
            theorem_violations += 1
        if any(
            row["axes"][axis]["completion_flip_margin"] is None
            for row in proper_G_identified
        ):
            theorem_violations += 1
        if any(
            row["axes"][axis]["completion_flip_margin"] != 0
            for row in unresolved
        ):
            theorem_violations += 1

        by_decision = {}
        for decision in (False, True):
            subset = [
                row for row in identified
                if row["axes"][axis]["current_decision"] is decision
            ]
            vals = [
                int(row["axes"][axis]["completion_flip_margin"])
                for row in subset
                if row["axes"][axis]["completion_flip_margin"] is not None
            ]
            by_decision[str(decision).lower()] = {
                "count": len(subset),
                "margin_distribution": _dist(vals),
                "median_margin": _median(vals),
                "mean_margin": _mean(vals),
                "max_margin": None if not vals else max(vals),
            }

        fiber_rows = [record for record in fiber_records.values()]
        fiber_identified = [
            record for record in fiber_rows
            if record["axes"][axis]["identified_in_declared_universe"]
        ]
        fiber_margins = [
            int(record["axes"][axis]["completion_flip_margin"])
            for record in fiber_identified
            if record["axes"][axis]["completion_flip_margin"] is not None
        ]

        by_axis[axis] = {
            "truth_weighted": {
                "identified_in_declared_universe": len(identified),
                "unresolved_in_declared_universe": len(unresolved),
                "proper_G_identified": len(proper_G_identified),
                "full_G_identified": len(full_G_identified),
                "completion_flip_margin_distribution": _dist(finite_margins),
                "margin_1_count": sum(v == 1 for v in finite_margins),
                "median_margin": _median(finite_margins),
                "mean_margin": _mean(finite_margins),
                "max_margin": None if not finite_margins else max(finite_margins),
                "by_current_decision": by_decision,
            },
            "unique_fiber": {
                "identified_fibers": len(fiber_identified),
                "completion_flip_margin_distribution": _dist(fiber_margins),
                "median_margin": _median(fiber_margins),
                "mean_margin": _mean(fiber_margins),
                "max_margin": None if not fiber_margins else max(fiber_margins),
            },
        }

    result = {
        "schema": "eog.bam_decision_robustness_margin.result.v1",
        "parent_result_fingerprint": EXPECTED_PARENT,
        "truth_count": len(truth_rows),
        "unique_E1_fiber_count": len(fiber_records),
        "activation_roster": activation_roster,
        "theorem_verification": {
            "complete_decomposition_closure_and_margin_violations": theorem_violations,
            "status": "PASS" if theorem_violations == 0 else "FAIL",
        },
        "by_axis": by_axis,
        "fiber_records": list(fiber_records.values()),
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
        "theorem_verification": result["theorem_verification"],
        "by_axis": result["by_axis"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
