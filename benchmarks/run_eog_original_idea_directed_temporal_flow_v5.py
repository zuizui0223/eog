#!/usr/bin/env python3
from __future__ import annotations

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
    GRID_N,
    NEIGHBOURHOODS,
    REPLICATES,
    SEED_BASE,
    _bfs_distances,
    _components,
    _generate_base,
    _graph_from_edges,
    _node_id,
)
from benchmarks.run_eog_original_idea_analyst_worlds_v3 import (
    RULES,
    _rule_threshold,
)
from benchmarks.run_eog_original_idea_occurrence_information_v4 import (
    COVERAGE,
    _coverage_count,
    _dispersed_order,
)


PROTOCOL = ROOT / "validation/eog_original_idea_directed_temporal_flow_v5/protocol_v5.json"


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


def _outlet_corner(replicate, autocorr, neighbourhood):
    corners = ((0, 0), (0, GRID_N - 1), (GRID_N - 1, 0), (GRID_N - 1, GRID_N - 1))
    payload = (
        f"{SEED_BASE}|flow_outlet|{replicate}|{autocorr}|{neighbourhood}"
    ).encode("utf-8")
    index = hashlib.sha256(payload).digest()[0] % len(corners)
    return corners[index]


def _potential(node, outlet):
    return float((node[0] - outlet[0]) ** 2 + (node[1] - outlet[1]) ** 2)


def _truth_source(base, outlet):
    comps = _components(base["geo_graph"], base["permissive"])
    if not comps:
        raise RuntimeError("no permissive geographic component")
    largest = comps[0]
    return sorted(
        largest,
        key=lambda node: (-_potential(node, outlet), _node_id(node)),
    )[0]


def _filtered_edges(base, barrier_density, rule):
    threshold = _rule_threshold(base, rule)
    return tuple(
        edge
        for edge in base["geo_edges"]
        if base["edge_uniform"][edge] >= barrier_density
        and abs(float(base["env"][edge[0]]) - float(base["env"][edge[1]]))
        <= threshold + 1e-15
    )


def _directed_graph(active, edges, outlet):
    graph = {node: set() for node in active}
    for a, b in edges:
        if a not in active or b not in active:
            continue
        pa = _potential(a, outlet)
        pb = _potential(b, outlet)
        if pa > pb:
            graph[a].add(b)
        elif pb > pa:
            graph[b].add(a)
        else:
            graph[a].add(b)
            graph[b].add(a)
    return {node: frozenset(sorted(nbrs)) for node, nbrs in graph.items()}


def _graphs(base, barrier_density, rule, outlet):
    edges = _filtered_edges(base, barrier_density, rule)
    return (
        _graph_from_edges(base["permissive"], edges),
        _directed_graph(base["permissive"], edges, outlet),
    )


def _candidate_worlds(base, outlet, regime):
    rows = []
    for rule in RULES:
        for barrier_density in BARRIER_LEVELS:
            undirected, directed = _graphs(base, barrier_density, rule, outlet)
            graph = directed if regime == "directed" else undirected
            for source in sorted(base["permissive"]):
                dist = _bfs_distances(graph, source)
                rows.append(
                    {
                        "world_id": (
                            f"{_node_id(source)}|b{barrier_density:.2f}|{rule}"
                        ),
                        "source": source,
                        "barrier_density": barrier_density,
                        "rule": rule,
                        "dist": dist,
                        "reachable": frozenset(dist),
                    }
                )
    expected = len(base["permissive"]) * len(BARRIER_LEVELS) * len(RULES)
    if len(rows) != expected:
        raise RuntimeError("candidate Cartesian product incomplete")
    return tuple(rows)


def _truth_world_id(source, barrier_density):
    return f"{_node_id(source)}|b{barrier_density:.2f}|relative_edge_q70"


def _survivor_summary(
    worlds,
    anchors,
    truth_depth,
    permissive,
    truth_reachable,
    truth_world_id,
    *,
    temporal,
):
    anchors = tuple(anchors)
    if temporal:
        survivors = tuple(
            world
            for world in worlds
            if all(
                node in world["dist"]
                and int(world["dist"][node]) <= int(truth_depth[node])
                for node in anchors
            )
        )
    else:
        anchor_set = frozenset(anchors)
        survivors = tuple(
            world
            for world in worlds
            if anchor_set.issubset(world["reachable"])
        )

    if not survivors:
        raise RuntimeError("truth-generated evidence eliminated all worlds")
    if truth_world_id not in {world["world_id"] for world in survivors}:
        raise RuntimeError("truth world eliminated by truth-generated evidence")

    union_reachable = frozenset().union(
        *(world["reachable"] for world in survivors)
    )
    robust_unreachable = frozenset(permissive.difference(union_reachable))
    truth_unreachable = frozenset(permissive.difference(truth_reachable))
    false_exclusions = robust_unreachable.intersection(truth_reachable)
    recovery = (
        None
        if not truth_unreachable
        else len(robust_unreachable) / len(truth_unreachable)
    )
    return {
        "survivor_world_count": len(survivors),
        "survivor_world_fraction": len(survivors) / len(worlds),
        "surviving_source_count": len({world["source"] for world in survivors}),
        "robustly_unreachable_count": len(robust_unreachable),
        "truth_unreachable_count": len(truth_unreachable),
        "robust_impossibility_recovery_fraction": recovery,
        "false_robust_exclusion_count": len(false_exclusions),
        "truth_world_survives": True,
    }


def _asymmetry(truth_graph, truth_reachable):
    nodes = tuple(sorted(truth_reachable))
    if len(nodes) < 2:
        return 0, 0, 0.0
    reach = {
        source: frozenset(_bfs_distances(truth_graph, source))
        for source in nodes
    }
    total = 0
    asymmetric = 0
    for i, left in enumerate(nodes):
        for right in nodes[i + 1 :]:
            total += 1
            lr = right in reach[left]
            rl = left in reach[right]
            if bool(lr) ^ bool(rl):
                asymmetric += 1
    return asymmetric, total, (0.0 if total == 0 else asymmetric / total)


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    source = _truth_source(base, outlet)
    _, truth_graph = _graphs(
        base,
        barrier_density,
        "relative_edge_q70",
        outlet,
    )
    truth_depth = _bfs_distances(truth_graph, source)
    truth_reachable = frozenset(truth_depth)
    pool = tuple(sorted(node for node in truth_reachable if node != source))

    asym_count, pair_count, asym_fraction = _asymmetry(
        truth_graph,
        truth_reachable,
    )
    base_row = {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "truth_barrier_density": barrier_density,
        "outlet": _node_id(outlet),
        "truth_source": _node_id(source),
        "truth_reachable_node_count": len(truth_reachable),
        "truth_positive_pool_size": len(pool),
        "truth_asymmetric_pair_count": asym_count,
        "truth_pair_count": pair_count,
        "truth_asymmetric_pair_fraction": asym_fraction,
        "eligible": len(pool) >= 4,
    }
    if len(pool) < 4:
        return {**base_row, "coverage": {}}

    order = _dispersed_order(pool, source)
    undirected_worlds = _candidate_worlds(base, outlet, "undirected")
    directed_worlds = _candidate_worlds(base, outlet, "directed")
    truth_id = _truth_world_id(source, barrier_density)

    if truth_id not in {world["world_id"] for world in directed_worlds}:
        raise RuntimeError("truth directed world missing")

    coverage_rows = {}
    previous = {
        "undirected_static": len(undirected_worlds),
        "directed_static": len(directed_worlds),
        "directed_temporal": len(directed_worlds),
    }
    for fraction in COVERAGE:
        count = _coverage_count(len(pool), fraction)
        anchors = order[:count]

        u = _survivor_summary(
            undirected_worlds,
            anchors,
            truth_depth,
            base["permissive"],
            truth_reachable,
            truth_id,
            temporal=False,
        )
        ds = _survivor_summary(
            directed_worlds,
            anchors,
            truth_depth,
            base["permissive"],
            truth_reachable,
            truth_id,
            temporal=False,
        )
        dt = _survivor_summary(
            directed_worlds,
            anchors,
            truth_depth,
            base["permissive"],
            truth_reachable,
            truth_id,
            temporal=True,
        )
        current = {
            "undirected_static": u["survivor_world_count"],
            "directed_static": ds["survivor_world_count"],
            "directed_temporal": dt["survivor_world_count"],
        }
        for regime, value in current.items():
            if value > previous[regime]:
                raise RuntimeError(
                    f"nested evidence increased survivor worlds for {regime}"
                )
            previous[regime] = value

        if dt["survivor_world_count"] > ds["survivor_world_count"]:
            raise RuntimeError("temporal evidence expanded directed static survivors")

        coverage_rows[f"{fraction:.2f}"] = {
            "anchor_count": count,
            "anchors": [_node_id(node) for node in anchors],
            "undirected_static": u,
            "directed_static": ds,
            "directed_temporal": dt,
        }

    return {**base_row, "coverage": coverage_rows}


def _mean(values):
    values = [float(v) for v in values]
    return None if not values else float(np.mean(values))


def _median(values):
    values = [float(v) for v in values]
    return None if not values else float(np.median(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_directed_temporal_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v5 protocol is not frozen")

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

    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise RuntimeError("no v5 eligible rows")

    asymmetry_rows = sum(
        row["truth_asymmetric_pair_count"] > 0 for row in eligible
    )
    asymmetry_row_fraction = asymmetry_rows / len(eligible)

    regime_recovery_means = {}
    regime_source_means = {}
    regime_survivor_means = {}
    for regime in (
        "undirected_static",
        "directed_static",
        "directed_temporal",
    ):
        regime_recovery_means[regime] = {}
        regime_source_means[regime] = {}
        regime_survivor_means[regime] = {}
        for fraction in COVERAGE:
            key = f"{fraction:.2f}"
            recoveries = [
                row["coverage"][key][regime][
                    "robust_impossibility_recovery_fraction"
                ]
                for row in eligible
                if row["coverage"][key][regime][
                    "robust_impossibility_recovery_fraction"
                ]
                is not None
            ]
            regime_recovery_means[regime][key] = _mean(recoveries)
            regime_source_means[regime][key] = _mean(
                row["coverage"][key][regime]["surviving_source_count"]
                for row in eligible
            )
            regime_survivor_means[regime][key] = _mean(
                row["coverage"][key][regime]["survivor_world_fraction"]
                for row in eligible
            )

    directed_recovery = [
        regime_recovery_means["directed_static"][f"{fraction:.2f}"]
        for fraction in COVERAGE
    ]
    d2_nondecreasing = all(
        a is not None and b is not None and a <= b + 1e-15
        for a, b in zip(
            directed_recovery[:-1],
            directed_recovery[1:],
            strict=True,
        )
    )
    d2_strict = (
        directed_recovery[0] is not None
        and directed_recovery[-1] is not None
        and directed_recovery[-1] > directed_recovery[0]
    )

    full = "1.00"
    d3_contrast = (
        regime_source_means["directed_static"][full]
        - regime_source_means["undirected_static"][full]
    )
    temporal_contract_rows = sum(
        row["coverage"][full]["directed_temporal"]["survivor_world_count"]
        < row["coverage"][full]["directed_static"]["survivor_world_count"]
        for row in eligible
    )
    d4_contrast = (
        regime_survivor_means["directed_temporal"][full]
        - regime_survivor_means["directed_static"][full]
    )
    d5_contrast = (
        regime_recovery_means["directed_temporal"][full]
        - regime_recovery_means["directed_static"][full]
    )
    d6_contrast = (
        regime_source_means["directed_temporal"][full]
        - regime_source_means["directed_static"][full]
    )

    false_exclusions = 0
    truth_retention_failures = 0
    monotonicity_violations = 0
    for row in eligible:
        for key in (f"{fraction:.2f}" for fraction in COVERAGE):
            for regime in (
                "undirected_static",
                "directed_static",
                "directed_temporal",
            ):
                item = row["coverage"][key][regime]
                false_exclusions += int(item["false_robust_exclusion_count"])
                truth_retention_failures += int(
                    not item["truth_world_survives"]
                )
        for regime in (
            "undirected_static",
            "directed_static",
            "directed_temporal",
        ):
            counts = [
                row["coverage"][f"{fraction:.2f}"][regime][
                    "survivor_world_count"
                ]
                for fraction in COVERAGE
            ]
            if any(
                a < b
                for a, b in zip(counts[:-1], counts[1:], strict=True)
            ):
                monotonicity_violations += 1

    full_medians = {}
    exact_source_counts = {}
    exact_world_counts = {}
    for regime in (
        "undirected_static",
        "directed_static",
        "directed_temporal",
    ):
        full_medians[regime] = {
            "survivor_world_count": _median(
                row["coverage"][full][regime]["survivor_world_count"]
                for row in eligible
            ),
            "surviving_source_count": _median(
                row["coverage"][full][regime]["surviving_source_count"]
                for row in eligible
            ),
        }
        exact_source_counts[regime] = sum(
            row["coverage"][full][regime]["surviving_source_count"] == 1
            for row in eligible
        )
        exact_world_counts[regime] = sum(
            row["coverage"][full][regime]["survivor_world_count"] == 1
            for row in eligible
        )

    verdicts = {
        "D1_truth_flow_creates_asymmetric_occurrence_relations": (
            "SUPPORTED" if asymmetry_row_fraction >= 0.80 else "REFUTED"
        ),
        "D2_direction_breaks_the_v4_impossibility_plateau": (
            "SUPPORTED" if d2_nondecreasing and d2_strict else "REFUTED"
        ),
        "D3_direction_reduces_source_aliasing": (
            "SUPPORTED" if d3_contrast < 0 else "REFUTED"
        ),
        "D4_temporal_order_contracts_directed_static_worlds": (
            "SUPPORTED"
            if temporal_contract_rows > 0 and d4_contrast < 0
            else "REFUTED"
        ),
        "D5_temporal_order_adds_robust_impossibility_information": (
            "SUPPORTED" if d5_contrast > 0 else "REFUTED"
        ),
        "D6_temporal_order_reduces_source_aliasing": (
            "SUPPORTED" if d6_contrast < 0 else "REFUTED"
        ),
        "D7_truth_retention_and_impossibility_soundness": (
            "SUPPORTED"
            if (
                false_exclusions == 0
                and truth_retention_failures == 0
                and monotonicity_violations == 0
            )
            else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_directed_temporal_flow.result.v5",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "truth_flow_asymmetry": {
            "rows_with_any_asymmetric_pair": asymmetry_rows,
            "eligible_row_fraction": asymmetry_row_fraction,
            "mean_asymmetric_pair_fraction": _mean(
                row["truth_asymmetric_pair_fraction"] for row in eligible
            ),
        },
        "robust_impossibility_recovery_means": regime_recovery_means,
        "surviving_source_means": regime_source_means,
        "survivor_world_fraction_means": regime_survivor_means,
        "D2_nondecreasing": d2_nondecreasing,
        "D2_full_minus_10pct": (
            None
            if directed_recovery[0] is None or directed_recovery[-1] is None
            else directed_recovery[-1] - directed_recovery[0]
        ),
        "D3_directed_minus_undirected_full_source_count": d3_contrast,
        "D4_temporal_contract_row_count": temporal_contract_rows,
        "D4_temporal_minus_static_full_survivor_fraction": d4_contrast,
        "D5_temporal_minus_static_full_recovery": d5_contrast,
        "D6_temporal_minus_static_full_source_count": d6_contrast,
        "D7_false_robust_exclusion_count": false_exclusions,
        "D7_truth_retention_failure_count": truth_retention_failures,
        "D7_monotonicity_violation_count": monotonicity_violations,
        "full_coverage_medians": full_medians,
        "full_coverage_exact_source_recovery_count": exact_source_counts,
        "full_coverage_exact_world_recovery_count": exact_world_counts,
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
                "truth_flow_asymmetry": result["truth_flow_asymmetry"],
                "robust_impossibility_recovery_means": result[
                    "robust_impossibility_recovery_means"
                ],
                "surviving_source_means": result["surviving_source_means"],
                "D2_full_minus_10pct": result["D2_full_minus_10pct"],
                "D3_directed_minus_undirected_full_source_count": result[
                    "D3_directed_minus_undirected_full_source_count"
                ],
                "D4_temporal_contract_row_count": result[
                    "D4_temporal_contract_row_count"
                ],
                "D5_temporal_minus_static_full_recovery": result[
                    "D5_temporal_minus_static_full_recovery"
                ],
                "D6_temporal_minus_static_full_source_count": result[
                    "D6_temporal_minus_static_full_source_count"
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
