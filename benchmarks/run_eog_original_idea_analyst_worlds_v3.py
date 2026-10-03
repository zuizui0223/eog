#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from benchmarks.run_eog_original_idea_virtual_worlds_v2 import (
    AUTOCORR_LEVELS,
    BARRIER_LEVELS,
    NEIGHBOURHOODS,
    REPLICATES,
    _bfs_distances,
    _generate_base,
    _graph_from_edges,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_analyst_worlds_v3/protocol_v3.json"
RULES = ("relative_edge_q70", "absolute_raw_0.5", "standardized_sd_1.0")


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


def _rule_threshold(base, rule):
    env = base["env"]
    if rule == "relative_edge_q70":
        return float(base["env_cut"])
    if rule == "absolute_raw_0.5":
        return 0.5
    if rule == "standardized_sd_1.0":
        sd = float(np.std(env))
        if not np.isfinite(sd) or sd <= 0:
            raise RuntimeError("environmental SD must be positive")
        return sd
    raise ValueError(rule)


def _reachable_for_rule(base, barrier_density, rule):
    threshold = _rule_threshold(base, rule)
    edges = []
    for edge in base["geo_edges"]:
        if base["edge_uniform"][edge] < barrier_density:
            continue
        if abs(float(base["env"][edge[0]]) - float(base["env"][edge[1]])) > threshold + 1e-15:
            continue
        edges.append(edge)
    graph = _graph_from_edges(base["permissive"], tuple(edges))
    return frozenset(_bfs_distances(graph, base["source"])), threshold


def _barrier_only_reachable(base, barrier_density):
    edges = tuple(
        edge
        for edge in base["geo_edges"]
        if base["edge_uniform"][edge] >= barrier_density
    )
    graph = _graph_from_edges(base["permissive"], edges)
    return frozenset(_bfs_distances(graph, base["source"]))


def _row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    permissive = base["permissive"]
    source = base["source"]
    source_env = float(base["env"][source])
    barrier_only = _barrier_only_reachable(base, barrier_density)

    rule_rows = {}
    reach_sets = {}
    for rule in RULES:
        reachable, threshold = _reachable_for_rule(base, barrier_density, rule)
        reach_sets[rule] = reachable
        candidates = [
            node
            for node in barrier_only
            if node != source
            and abs(float(base["env"][node]) - source_env) <= threshold + 1e-15
        ]
        blocked = [node for node in candidates if node not in reachable]
        rule_rows[rule] = {
            "threshold": threshold,
            "reachable_count": len(reachable),
            "viable_unreachable_fraction": (
                (len(permissive) - len(reachable)) / len(permissive)
                if permissive
                else 0.0
            ),
            "endpoint_similar_candidate_count": len(candidates),
            "pathwise_blocked_count": len(blocked),
            "pathwise_blocked_fraction": (
                len(blocked) / len(candidates) if candidates else 0.0
            ),
        }

    q70 = reach_sets["relative_edge_q70"]
    union = frozenset().union(*reach_sets.values())
    intersection = set(permissive)
    for reachable in reach_sets.values():
        intersection.intersection_update(reachable)
    intersection = frozenset(intersection)
    robust_impossible = frozenset(permissive.difference(union))

    targets = [node for node in permissive if node != source]
    contingent = []
    for node in targets:
        n = sum(node in reach_sets[rule] for rule in RULES)
        if 0 < n < len(RULES):
            contingent.append(node)

    violations = 0
    if not q70.issubset(union):
        violations += 1
    if not intersection.issubset(q70):
        violations += 1
    if not robust_impossible.issubset(permissive.difference(q70)):
        violations += 1

    return {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "barrier_density": barrier_density,
        "permissive_target_count": len(targets),
        "rules": rule_rows,
        "contingent_target_count": len(contingent),
        "contingent_target_fraction": (
            len(contingent) / len(targets) if targets else 0.0
        ),
        "robust_reachable_target_count": sum(
            node in intersection for node in targets
        ),
        "robust_impossible_target_count": sum(
            node in robust_impossible for node in targets
        ),
        "gained_possible_vs_q70_count": len(union.difference(q70)),
        "lost_q70_robust_reachable_count": len(q70.difference(intersection)),
        "lost_q70_robust_impossible_count": len(
            (permissive.difference(q70)).difference(robust_impossible)
        ),
        "analyst_universe_monotonicity_violations": violations,
    }


def _mean(rows, getter):
    return float(np.mean([float(getter(row)) for row in rows]))


def _sign(value, tol=1e-12):
    if value > tol:
        return 1
    if value < -tol:
        return -1
    return 0


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_analyst_rule_benchmark_implementation_and_scoring":
        raise RuntimeError("v3 protocol is not frozen")

    rows = []
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                for barrier_density in BARRIER_LEVELS:
                    rows.append(
                        _row(replicate, autocorr, neighbourhood, barrier_density)
                    )
    if len(rows) != 384:
        raise RuntimeError(f"expected 384 rows, got {len(rows)}")

    total_contingent = sum(row["contingent_target_count"] for row in rows)
    monotonicity_violations = sum(
        row["analyst_universe_monotonicity_violations"] for row in rows
    )
    total_robust_reachable = sum(row["robust_reachable_target_count"] for row in rows)
    total_robust_impossible = sum(row["robust_impossible_target_count"] for row in rows)

    autocorr_contrasts = {}
    barrier_contrasts = {}
    for rule in RULES:
        low = _mean(
            [row for row in rows if row["environmental_autocorrelation"] == "low"],
            lambda row, r=rule: row["rules"][r]["pathwise_blocked_fraction"],
        )
        high = _mean(
            [row for row in rows if row["environmental_autocorrelation"] == "high"],
            lambda row, r=rule: row["rules"][r]["pathwise_blocked_fraction"],
        )
        autocorr_contrasts[rule] = {
            "low_mean": low,
            "high_mean": high,
            "low_minus_high": low - high,
            "sign": _sign(low - high),
        }

        lo_barrier = _mean(
            [row for row in rows if row["barrier_density"] == 0.05],
            lambda row, r=rule: row["rules"][r]["viable_unreachable_fraction"],
        )
        hi_barrier = _mean(
            [row for row in rows if row["barrier_density"] == 0.35],
            lambda row, r=rule: row["rules"][r]["viable_unreachable_fraction"],
        )
        barrier_contrasts[rule] = {
            "barrier_0.05_mean": lo_barrier,
            "barrier_0.35_mean": hi_barrier,
            "high_minus_low": hi_barrier - lo_barrier,
        }

    signs = {
        row["sign"]
        for row in autocorr_contrasts.values()
        if row["sign"] != 0
    }

    verdicts = {
        "A1_analyst_rule_disagreement_exists": (
            "SUPPORTED" if total_contingent > 0 else "REFUTED"
        ),
        "A2_analyst_universe_expansion_weakens_certificates_monotonically": (
            "SUPPORTED" if monotonicity_violations == 0 else "REFUTED"
        ),
        "A3_autocorrelation_conclusion_is_rule_sensitive": (
            "SUPPORTED" if len(signs) >= 2 else "REFUTED"
        ),
        "A4_barrier_effect_is_robust_across_analyst_rules": (
            "SUPPORTED"
            if all(row["high_minus_low"] > 0 for row in barrier_contrasts.values())
            else "REFUTED"
        ),
        "A5_some_relations_remain_robust_despite_analyst_uncertainty": (
            "SUPPORTED"
            if total_robust_reachable > 0 and total_robust_impossible > 0
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_analyst_worlds.result.v3",
        "row_count": len(rows),
        "analyst_rules": list(RULES),
        "predeclared_verdicts": verdicts,
        "aggregate": {
            "total_contingent_target_classifications": total_contingent,
            "mean_contingent_target_fraction": _mean(
                rows, lambda row: row["contingent_target_fraction"]
            ),
            "total_robust_reachable_target_classifications": total_robust_reachable,
            "total_robust_impossible_target_classifications": total_robust_impossible,
            "total_gained_possible_vs_q70": sum(
                row["gained_possible_vs_q70_count"] for row in rows
            ),
            "total_lost_q70_robust_reachable": sum(
                row["lost_q70_robust_reachable_count"] for row in rows
            ),
            "total_lost_q70_robust_impossible": sum(
                row["lost_q70_robust_impossible_count"] for row in rows
            ),
            "analyst_universe_monotonicity_violations": monotonicity_violations,
        },
        "autocorrelation_contrasts_by_rule": autocorr_contrasts,
        "barrier_contrasts_by_rule": barrier_contrasts,
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
                "predeclared_verdicts": result["predeclared_verdicts"],
                "aggregate": result["aggregate"],
                "autocorrelation_contrasts_by_rule": result[
                    "autocorrelation_contrasts_by_rule"
                ],
                "barrier_contrasts_by_rule": result[
                    "barrier_contrasts_by_rule"
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
