#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
from benchmarks.run_eog_original_idea_expansion_direction_v7 import (
    _classify,
    _compatible,
)


PROTOCOL = ROOT / "validation/eog_original_idea_world_growth_v8/protocol_v8.json"
FRACTIONS = (0.10, 0.25, 0.50, 0.75, 1.00)
POOLS = (
    "restrictive_same_source",
    "permissive_same_source",
    "directional_same_source",
    "same_source_full",
    "all_source_full",
)


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


def _status(worlds, node):
    count = sum(node in world["reachable"] for world in worlds)
    if count == len(worlds):
        return "robust_reachable"
    if count == 0:
        return "robust_impossible"
    return "contingent"


def _threatens(certificate_type, world, node):
    if certificate_type == "robust_reachable":
        return node not in world["reachable"]
    if certificate_type == "robust_impossible":
        return node in world["reachable"]
    raise ValueError(f"unsupported certificate type {certificate_type!r}")


def _survival_probability(N, K, m):
    if N < 0 or K < 0 or K > N:
        raise ValueError("invalid N/K")
    if m < 0 or m > N:
        raise ValueError("invalid m")
    if K == 0:
        return 1.0
    if m > N - K:
        return 0.0
    return math.comb(N - K, m) / math.comb(N, m)


def _lifetime_summary(pool, certificate_type, node):
    N = len(pool)
    K = sum(_threatens(certificate_type, world, node) for world in pool)
    if N == 0 or K == 0:
        normalized = 1.0
        expected_draw = None if N == 0 else float(N + 1)
        survives_full = True
    else:
        expected_draw = (N + 1) / (K + 1)
        normalized = expected_draw / N
        survives_full = False

    survival = {}
    for fraction in FRACTIONS:
        if N == 0:
            m = 0
        else:
            m = min(N, int(math.ceil(fraction * N)))
        survival[f"{fraction:.2f}"] = {
            "draw_count": m,
            "survival_probability": _survival_probability(N, K, m),
        }

    return {
        "pool_size_N": N,
        "threat_count_K": K,
        "expected_first_failure_draw": expected_draw,
        "normalized_expected_lifetime": float(normalized),
        "survives_complete_pool": survives_full,
        "survival_by_growth_fraction": survival,
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    truth_source = _truth_source(base, outlet)
    _, truth_graph = _graphs(base, barrier_density, Q70, outlet)
    truth_dist = _bfs_distances(truth_graph, truth_source)
    truth_reachable = frozenset(truth_dist)
    pool = tuple(sorted(node for node in truth_reachable if node != truth_source))

    base_row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "truth_source": _node_id(truth_source),
        "truth_positive_pool_size": len(pool),
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {**base_row, "certificates": []}

    order = _dispersed_order(pool, truth_source)
    anchor_count = _coverage_count(len(pool), EVIDENCE_FRACTION)
    anchors = tuple(order[:anchor_count])

    full_worlds = _candidate_worlds(base, outlet, "directed")
    references = {
        world["source"]: world
        for world in full_worlds
        if world["barrier_density"] == barrier_density
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

    baseline_sources = {world["source"] for world in b0}
    same_source_compatible = tuple(
        world
        for world in full_worlds
        if world["source"] in baseline_sources and _compatible(world, anchors)
    )
    all_source_compatible = tuple(
        world for world in full_worlds if _compatible(world, anchors)
    )

    b0_ids = {world["world_id"] for world in b0}
    classified = {
        "restrictive": [],
        "permissive": [],
        "equivalent": [],
        "incomparable": [],
    }
    for world in same_source_compatible:
        if world["world_id"] in b0_ids:
            continue
        classified[_classify(world, references[world["source"]])].append(world)

    def unique(rows):
        by_id = {row["world_id"]: row for row in rows}
        return tuple(by_id[key] for key in sorted(by_id))

    pools = {
        "restrictive_same_source": unique(classified["restrictive"]),
        "permissive_same_source": unique(classified["permissive"]),
        "directional_same_source": unique(
            (*classified["restrictive"], *classified["permissive"])
        ),
        "same_source_full": unique(
            world for world in same_source_compatible
            if world["world_id"] not in b0_ids
        ),
        "all_source_full": unique(
            world for world in all_source_compatible
            if world["world_id"] not in b0_ids
        ),
    }

    cert_nodes = tuple(
        sorted(
            set(base["permissive"])
            .difference(anchors)
            .difference({truth_source})
        )
    )

    cert_rows = []
    for node in cert_nodes:
        cert_type = _status(b0, node)
        if cert_type == "contingent":
            continue
        per_pool = {
            name: _lifetime_summary(worlds, cert_type, node)
            for name, worlds in pools.items()
        }
        cert_rows.append({
            "node_id": _node_id(node),
            "certificate_type": cert_type,
            "truth_reachable": node in truth_reachable,
            "pools": per_pool,
        })

    return {
        **base_row,
        "anchor_count": len(anchors),
        "baseline_world_count": len(b0),
        "baseline_source_count": len(baseline_sources),
        "candidate_pool_sizes": {name: len(rows) for name, rows in pools.items()},
        "certificates": cert_rows,
    }


def _mean(values):
    values = [float(value) for value in values]
    return None if not values else float(np.mean(values))


def _median(values):
    values = [float(value) for value in values]
    return None if not values else float(np.median(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_world_growth_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v8 protocol is not frozen")

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

    eligible = [row for row in rows if row["eligible"]]
    certs = [
        cert
        for row in eligible
        for cert in row["certificates"]
    ]
    if not certs:
        raise RuntimeError("no baseline certificates")

    by_type_pool = {}
    for cert_type in ("robust_reachable", "robust_impossible"):
        by_type_pool[cert_type] = {}
        typed = [cert for cert in certs if cert["certificate_type"] == cert_type]
        for pool_name in POOLS:
            summaries = [cert["pools"][pool_name] for cert in typed]
            by_type_pool[cert_type][pool_name] = {
                "certificate_count": len(summaries),
                "K0_count": sum(row["threat_count_K"] == 0 for row in summaries),
                "K0_fraction": (
                    None if not summaries
                    else sum(row["threat_count_K"] == 0 for row in summaries)
                    / len(summaries)
                ),
                "mean_normalized_expected_lifetime": _mean(
                    row["normalized_expected_lifetime"] for row in summaries
                ),
                "median_normalized_expected_lifetime": _median(
                    row["normalized_expected_lifetime"] for row in summaries
                ),
                "mean_survival_probability": {
                    key: _mean(
                        row["survival_by_growth_fraction"][key]["survival_probability"]
                        for row in summaries
                    )
                    for key in ("0.10", "0.25", "0.50", "0.75", "1.00")
                },
            }

    l1_restrictive_violations = sum(
        cert["certificate_type"] == "robust_impossible"
        and cert["pools"]["restrictive_same_source"]["threat_count_K"] != 0
        for cert in certs
    )
    l1_permissive_violations = sum(
        cert["certificate_type"] == "robust_reachable"
        and cert["pools"]["permissive_same_source"]["threat_count_K"] != 0
        for cert in certs
    )

    l2_reach_vulnerable = sum(
        cert["certificate_type"] == "robust_reachable"
        and cert["pools"]["restrictive_same_source"]["threat_count_K"] > 0
        for cert in certs
    )
    l2_impossible_vulnerable = sum(
        cert["certificate_type"] == "robust_impossible"
        and cert["pools"]["permissive_same_source"]["threat_count_K"] > 0
        for cert in certs
    )

    full_reach = by_type_pool["robust_reachable"]["all_source_full"][
        "mean_normalized_expected_lifetime"
    ]
    full_impossible = by_type_pool["robust_impossible"]["all_source_full"][
        "mean_normalized_expected_lifetime"
    ]
    l3_contrast = (
        None
        if full_reach is None or full_impossible is None
        else full_impossible - full_reach
    )

    l4_count = 0
    l5_count = 0
    l6_violations = 0
    l7_violations = 0

    for cert in certs:
        directional = cert["pools"]["directional_same_source"]
        same_full = cert["pools"]["same_source_full"]
        all_full = cert["pools"]["all_source_full"]

        if (
            same_full["normalized_expected_lifetime"]
            < directional["normalized_expected_lifetime"] - 1e-15
        ):
            l4_count += 1

        if (
            all_full["normalized_expected_lifetime"]
            < same_full["normalized_expected_lifetime"] - 1e-15
        ):
            l5_count += 1

        for pool_name in POOLS:
            row = cert["pools"][pool_name]
            probs = [
                row["survival_by_growth_fraction"][key]["survival_probability"]
                for key in ("0.10", "0.25", "0.50", "0.75", "1.00")
            ]
            if any(a < b - 1e-15 for a, b in zip(probs[:-1], probs[1:], strict=True)):
                l6_violations += 1
            endpoint = probs[-1]
            expected_endpoint = 1.0 if row["threat_count_K"] == 0 else 0.0
            if abs(endpoint - expected_endpoint) > 1e-15:
                l6_violations += 1
            if bool(row["survives_complete_pool"]) != (row["threat_count_K"] == 0):
                l7_violations += 1

    verdicts = {
        "L1_directional_protection_is_lifetime_infinite_within_pool": (
            "SUPPORTED"
            if l1_restrictive_violations == 0 and l1_permissive_violations == 0
            else "REFUTED"
        ),
        "L2_opposite_direction_creates_finite_lifetimes": (
            "SUPPORTED"
            if l2_reach_vulnerable > 0 and l2_impossible_vulnerable > 0
            else "REFUTED"
        ),
        "L3_mixed_growth_reproduces_v6_asymmetry": (
            "SUPPORTED"
            if l3_contrast is not None and l3_contrast < 0
            else "REFUTED"
        ),
        "L4_incomparable_worlds_can_shorten_certificate_lifetime": (
            "SUPPORTED" if l4_count > 0 else "REFUTED"
        ),
        "L5_new_source_worlds_can_shorten_certificate_lifetime": (
            "SUPPORTED" if l5_count > 0 else "REFUTED"
        ),
        "L6_survival_curves_are_monotone": (
            "SUPPORTED" if l6_violations == 0 else "REFUTED"
        ),
        "L7_threat_count_exactly_predicts_endpoint_persistence": (
            "SUPPORTED" if l7_violations == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_world_growth_survival.result.v8",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "certificate_count": len(certs),
        "predeclared_verdicts": verdicts,
        "by_certificate_type_and_pool": by_type_pool,
        "L1_restrictive_impossibility_violation_count": l1_restrictive_violations,
        "L1_permissive_reachability_violation_count": l1_permissive_violations,
        "L2_restrictive_reachability_vulnerable_certificate_count": l2_reach_vulnerable,
        "L2_permissive_impossibility_vulnerable_certificate_count": l2_impossible_vulnerable,
        "L3_impossible_minus_reachable_mean_lifetime": l3_contrast,
        "L4_incomparable_or_equivalent_shortened_lifetime_count": l4_count,
        "L5_new_source_shortened_lifetime_count": l5_count,
        "L6_survival_curve_violation_count": l6_violations,
        "L7_endpoint_persistence_violation_count": l7_violations,
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
                "certificate_count": result["certificate_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "L3_impossible_minus_reachable_mean_lifetime": result[
                    "L3_impossible_minus_reachable_mean_lifetime"
                ],
                "L4_incomparable_or_equivalent_shortened_lifetime_count": result[
                    "L4_incomparable_or_equivalent_shortened_lifetime_count"
                ],
                "L5_new_source_shortened_lifetime_count": result[
                    "L5_new_source_shortened_lifetime_count"
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
