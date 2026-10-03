#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_virtual_worlds_v2 import (
    AUTOCORR_LEVELS,
    BARRIER_LEVELS,
    NEIGHBOURHOODS,
    REPLICATES,
    _bfs_distances,
    _generate_base,
    _node_id,
)
from benchmarks.run_eog_original_idea_occurrence_information_v4 import (
    _coverage_count,
    _dispersed_order,
)
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _candidate_worlds,
    _graphs,
    _outlet_corner,
    _truth_source,
)
from benchmarks.run_eog_original_idea_world_universe_v6 import (
    EVIDENCE_FRACTION,
    Q70,
)
from benchmarks.run_eog_original_idea_world_growth_v8 import (
    _lifetime_summary,
)


PROTOCOL = ROOT / "validation/eog_original_idea_future_proof_evidence_v9/protocol_v9.json"
ACTIONS = ("S_source", "B_barrier", "R_analyst")


def _sha256(payload):
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _truth_world_id(source, barrier_density):
    return f"{_node_id(source)}|b{barrier_density:.2f}|{Q70}"


def _compatible(world, anchors):
    return frozenset(anchors).issubset(world["reachable"])


def _status(worlds, node):
    n = len(worlds)
    count = sum(node in world["reachable"] for world in worlds)
    if count == n:
        return "robust_reachable"
    if count == 0:
        return "robust_impossible"
    return "contingent"


def _action_matches(world, action, truth_source, truth_barrier):
    if action == "S_source":
        return world["source"] == truth_source
    if action == "B_barrier":
        return float(world["barrier_density"]) == float(truth_barrier)
    if action == "R_analyst":
        return str(world["rule"]) == Q70
    raise ValueError(action)


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    truth_source = _truth_source(base, outlet)
    _, truth_graph = _graphs(base, barrier_density, Q70, outlet)
    truth_dist = _bfs_distances(truth_graph, truth_source)
    truth_reachable = frozenset(truth_dist)
    pool = tuple(sorted(node for node in truth_reachable if node != truth_source))

    row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": _node_id(truth_source),
        "truth_positive_pool_size": len(pool),
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {**row, "actions": {}}

    order = _dispersed_order(pool, truth_source)
    anchor_count = _coverage_count(len(pool), EVIDENCE_FRACTION)
    anchors = tuple(order[:anchor_count])

    full_worlds = _candidate_worlds(base, outlet, "directed")
    references = {
        world["source"]: world
        for world in full_worlds
        if float(world["barrier_density"]) == float(barrier_density)
        and world["rule"] == Q70
    }
    b0 = tuple(
        world
        for world in references.values()
        if _compatible(world, anchors)
    )
    truth_id = _truth_world_id(truth_source, barrier_density)
    if truth_id not in {world["world_id"] for world in b0}:
        raise RuntimeError("truth world missing from B0")

    all_compatible = tuple(
        world for world in full_worlds if _compatible(world, anchors)
    )
    b0_ids = {world["world_id"] for world in b0}
    future_pool = tuple(
        world for world in all_compatible
        if world["world_id"] not in b0_ids
    )

    cert_nodes = tuple(
        sorted(
            set(base["permissive"])
            .difference(anchors)
            .difference({truth_source})
        )
    )
    certificates = []
    for node in cert_nodes:
        cert_type = _status(b0, node)
        if cert_type == "contingent":
            continue
        baseline_life = _lifetime_summary(future_pool, cert_type, node)
        certificates.append({
            "node": node,
            "node_id": _node_id(node),
            "certificate_type": cert_type,
            "baseline": baseline_life,
        })

    if not certificates:
        return {
            **row,
            "eligible": False,
            "reason": "no_baseline_universal_certificates",
            "actions": {},
        }

    action_rows = {}
    lifetime_violation_count = 0
    for action in ACTIONS:
        b0_after = tuple(
            world for world in b0
            if _action_matches(world, action, truth_source, barrier_density)
        )
        if not b0_after:
            raise RuntimeError(f"truth-consistent action eliminated all B0 worlds: {action}")
        if truth_id not in {world["world_id"] for world in b0_after}:
            raise RuntimeError(f"truth world eliminated by action {action}")

        compatible_after = tuple(
            world for world in all_compatible
            if _action_matches(world, action, truth_source, barrier_density)
        )
        b0_after_ids = {world["world_id"] for world in b0_after}
        future_after = tuple(
            world for world in compatible_after
            if world["world_id"] not in b0_after_ids
        )

        per_certificate = []
        for cert in certificates:
            after = _lifetime_summary(
                future_after,
                cert["certificate_type"],
                cert["node"],
            )
            gain = (
                after["normalized_expected_lifetime"]
                - cert["baseline"]["normalized_expected_lifetime"]
            )
            if gain < -1e-15:
                lifetime_violation_count += 1
            per_certificate.append({
                "node_id": cert["node_id"],
                "certificate_type": cert["certificate_type"],
                "baseline_threat_count_K": cert["baseline"]["threat_count_K"],
                "after_threat_count_K": after["threat_count_K"],
                "baseline_normalized_lifetime": cert["baseline"][
                    "normalized_expected_lifetime"
                ],
                "after_normalized_lifetime": after[
                    "normalized_expected_lifetime"
                ],
                "lifetime_gain": gain,
                "immortalized": (
                    cert["baseline"]["threat_count_K"] > 0
                    and after["threat_count_K"] == 0
                ),
            })

        current_contraction = 1.0 - len(b0_after) / len(b0)
        mean_after = _mean(
            item["after_normalized_lifetime"] for item in per_certificate
        )
        mean_gain = _mean(item["lifetime_gain"] for item in per_certificate)
        action_rows[action] = {
            "current_B0_world_count_before": len(b0),
            "current_B0_world_count_after": len(b0_after),
            "current_contraction_fraction": current_contraction,
            "future_growth_pool_size_before": len(future_pool),
            "future_growth_pool_size_after": len(future_after),
            "mean_future_lifetime_after": mean_after,
            "mean_future_lifetime_gain": mean_gain,
            "immortalized_certificate_count": sum(
                item["immortalized"] for item in per_certificate
            ),
            "certificate_details": per_certificate,
        }

    def choose_max(metric):
        best = None
        best_value = None
        for action in ACTIONS:
            value = action_rows[action][metric]
            if best is None or value > best_value + 1e-15:
                best = action
                best_value = value
            elif abs(value - best_value) <= 1e-15:
                if ACTIONS.index(action) < ACTIONS.index(best):
                    best = action
                    best_value = value
        return best, best_value

    current_best, current_best_value = choose_max("current_contraction_fraction")
    future_best, future_best_value = choose_max("mean_future_lifetime_after")

    return {
        **row,
        "anchor_count": len(anchors),
        "baseline_B0_world_count": len(b0),
        "baseline_source_count": len({world["source"] for world in b0}),
        "baseline_future_growth_pool_size": len(future_pool),
        "baseline_certificate_count": len(certificates),
        "baseline_mean_normalized_lifetime": _mean(
            cert["baseline"]["normalized_expected_lifetime"]
            for cert in certificates
        ),
        "actions": action_rows,
        "current_contraction_optimal_action": current_best,
        "current_contraction_optimal_value": current_best_value,
        "future_proof_optimal_action": future_best,
        "future_proof_optimal_value": future_best_value,
        "objectives_disagree": current_best != future_best,
        "lifetime_violation_count": lifetime_violation_count,
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_future_proof_evidence_implementation_and_scoring"
    ):
        raise RuntimeError("v9 protocol is not frozen")

    rows = []
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                for barrier_density in BARRIER_LEVELS:
                    rows.append(
                        _evaluate_row(
                            replicate,
                            autocorr,
                            neighbourhood,
                            barrier_density,
                        )
                    )
    if len(rows) != 384:
        raise RuntimeError(f"expected 384 rows, got {len(rows)}")

    eligible = [row for row in rows if row["eligible"] and row["actions"]]
    if not eligible:
        raise RuntimeError("no eligible v9 rows")

    lifetime_violations = sum(row["lifetime_violation_count"] for row in eligible)
    future_only_rows = sum(
        (
            row["actions"]["B_barrier"]["current_contraction_fraction"] == 0
            and row["actions"]["B_barrier"]["mean_future_lifetime_gain"] > 1e-15
        )
        or (
            row["actions"]["R_analyst"]["current_contraction_fraction"] == 0
            and row["actions"]["R_analyst"]["mean_future_lifetime_gain"] > 1e-15
        )
        for row in eligible
    )
    disagreement_rows = sum(row["objectives_disagree"] for row in eligible)
    optimal_counts = Counter(row["future_proof_optimal_action"] for row in eligible)
    immortalization_count = sum(
        row["actions"][action]["immortalized_certificate_count"]
        for row in eligible
        for action in ACTIONS
    )

    action_mean_gains = {
        action: _mean(
            row["actions"][action]["mean_future_lifetime_gain"]
            for row in eligible
        )
        for action in ACTIONS
    }
    action_mean_current_contraction = {
        action: _mean(
            row["actions"][action]["current_contraction_fraction"]
            for row in eligible
        )
        for action in ACTIONS
    }
    zero_current_future_optimal_rows = sum(
        row["future_proof_optimal_action"] in {"B_barrier", "R_analyst"}
        and row["actions"][row["future_proof_optimal_action"]][
            "current_contraction_fraction"
        ] == 0
        for row in eligible
    )

    verdicts = {
        "F1_truth_consistent_evidence_never_shortens_certificate_lifetime": (
            "SUPPORTED" if lifetime_violations == 0 else "REFUTED"
        ),
        "F2_future_only_evidence_value_exists": (
            "SUPPORTED" if future_only_rows > 0 else "REFUTED"
        ),
        "F3_current_contraction_and_future_proofing_choose_different_actions": (
            "SUPPORTED" if disagreement_rows > 0 else "REFUTED"
        ),
        "F4_barrier_or_analyst_validation_can_be_future_proof_optimal": (
            "SUPPORTED"
            if optimal_counts.get("B_barrier", 0) + optimal_counts.get("R_analyst", 0) > 0
            else "REFUTED"
        ),
        "F5_source_measurement_can_be_future_proof_optimal": (
            "SUPPORTED" if optimal_counts.get("S_source", 0) > 0 else "REFUTED"
        ),
        "F6_evidence_can_immortalize_threatened_certificates": (
            "SUPPORTED" if immortalization_count > 0 else "REFUTED"
        ),
        "F7_future_proof_action_is_not_one_fixed_measurement": (
            "SUPPORTED" if len(optimal_counts) >= 2 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_future_proof_evidence.result.v9",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "future_proof_optimal_action_counts": dict(sorted(optimal_counts.items())),
        "current_vs_future_objective_disagreement_row_count": disagreement_rows,
        "zero_current_contraction_positive_future_value_row_count": future_only_rows,
        "zero_current_effect_future_optimal_row_count": zero_current_future_optimal_rows,
        "immortalized_certificate_total": immortalization_count,
        "lifetime_monotonicity_violation_count": lifetime_violations,
        "mean_future_lifetime_gain_by_action": action_mean_gains,
        "mean_current_contraction_by_action": action_mean_current_contraction,
        "rows": rows,
    }
    result["fingerprint"] = _sha256(result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "row_count": result["row_count"],
                "eligible_row_count": result["eligible_row_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "future_proof_optimal_action_counts": result[
                    "future_proof_optimal_action_counts"
                ],
                "current_vs_future_objective_disagreement_row_count": result[
                    "current_vs_future_objective_disagreement_row_count"
                ],
                "zero_current_contraction_positive_future_value_row_count": result[
                    "zero_current_contraction_positive_future_value_row_count"
                ],
                "immortalized_certificate_total": result[
                    "immortalized_certificate_total"
                ],
                "mean_future_lifetime_gain_by_action": result[
                    "mean_future_lifetime_gain_by_action"
                ],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
