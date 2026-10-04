#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, deque
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_random_topology_v12/protocol_v12.json"

ACTIVE_SIZES = (8, 12, 16)
REPLICATES = 48
WORLDS_PER_ROW = 12
OUTSIDE_COUNT = 4
SEED_BASE = 20261212
EXTRA_P = (0.0, 0.10, 0.25, 0.50)


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


def _row_rng(active_n, replicate):
    return np.random.default_rng(SEED_BASE + active_n * 10000 + replicate)


def _world_rng(active_n, replicate, world_index):
    return np.random.default_rng(
        SEED_BASE
        + 2_000_000
        + active_n * 100000
        + replicate * 101
        + world_index
    )


def _static_state(active_n, replicate):
    rng = _row_rng(active_n, replicate)
    source = "S"
    labels = [f"N{i:02d}" for i in range(1, active_n)]
    shared_labels = list(rng.permutation(labels))
    active = (source, *shared_labels)
    outside = tuple(f"O{i:02d}" for i in range(OUTSIDE_COUNT))
    all_nodes = (*active, *outside)
    scores = {
        node: float(value)
        for node, value in zip(
            all_nodes,
            rng.uniform(0.05, 0.95, size=len(all_nodes)),
            strict=True,
        )
    }
    active_set = set(active)
    static = {
        "A_mask": tuple(1 for _ in all_nodes),
        "B_mask": tuple(1 for _ in all_nodes),
        "M_mask": tuple(1 if node in active_set else 0 for node in all_nodes),
        "G_mask": tuple(1 if node in active_set else 0 for node in all_nodes),
        "static_marginal_scores": tuple(scores[node] for node in all_nodes),
    }
    return active, outside, all_nodes, static


def _random_world_edges(active, active_n, replicate, world_index):
    rng = _world_rng(active_n, replicate, world_index)
    source = active[0]
    non_source = list(active[1:])
    order = [source, *list(rng.permutation(non_source))]

    edges = set()
    # Rooted arborescence guarantees source reachability to every active node.
    for j in range(1, len(order)):
        parent_index = int(rng.integers(0, j))
        edges.add((order[parent_index], order[j]))

    p = EXTRA_P[world_index // 3]
    for i in range(len(order) - 1):
        for j in range(i + 1, len(order)):
            edge = (order[i], order[j])
            if edge in edges:
                continue
            if rng.random() < p:
                edges.add(edge)
    return tuple(sorted(edges)), float(p), tuple(order)


def _graph(all_nodes, edges, removed=None):
    graph = {node: set() for node in all_nodes if node != removed}
    for source, target in edges:
        if source == removed or target == removed:
            continue
        graph[source].add(target)
    return {
        node: tuple(sorted(neighbours))
        for node, neighbours in graph.items()
    }


def _distances(graph, source):
    if source not in graph:
        return {}
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt not in dist:
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
    return dist


def _pairwise_signature(graph, active):
    out = []
    for source in active:
        reach = set(_distances(graph, source))
        for target in active:
            if source == target:
                continue
            out.append(1 if target in reach else 0)
    return tuple(out)


def _first_passage_signature(graph, active):
    dist = _distances(graph, active[0])
    if set(dist) != set(active):
        raise RuntimeError("random topology failed shared M accessibility")
    return tuple(int(dist[node]) for node in active)


def _intervention_signature(all_nodes, active, edges):
    source = active[0]
    values = []
    for removed in active[1:]:
        graph = _graph(all_nodes, edges, removed=removed)
        reachable = set(_distances(graph, source))
        retained = sum(
            node in reachable
            for node in active
            if node != removed
        )
        values.append(int(retained))
    return tuple(values)


def _critical_node_count(active, intervention):
    baseline_after_one_removal = len(active) - 1
    return sum(value < baseline_after_one_removal for value in intervention)


def _mean_knockout_retained(active, intervention):
    denominator = len(active) - 1
    return float(np.mean([value / denominator for value in intervention]))


def _normalized_partition(values):
    labels = {}
    out = []
    for value in values:
        key = json.dumps(value, sort_keys=True, default=str)
        if key not in labels:
            labels[key] = len(labels)
        out.append(labels[key])
    return tuple(out)


def _rankdata(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[order[end]] == values[order[start]]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def _spearman(x, y):
    rx = _rankdata(x)
    ry = _rankdata(y)
    if np.std(rx) == 0 or np.std(ry) == 0:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def _evaluate(active_n, replicate):
    active, outside, all_nodes, static = _static_state(active_n, replicate)
    static_fp = _sha256(static)

    worlds = []
    for world_index in range(WORLDS_PER_ROW):
        edges, p, order = _random_world_edges(
            active,
            active_n,
            replicate,
            world_index,
        )
        graph = _graph(all_nodes, edges)
        relation = _pairwise_signature(graph, active)
        passage = _first_passage_signature(graph, active)
        intervention = _intervention_signature(all_nodes, active, edges)
        worlds.append(
            {
                "world_id": f"W{world_index:02d}",
                "extra_edge_probability": p,
                "topological_order": list(order),
                "edge_count": len(edges),
                "edge_fingerprint": _sha256(edges),
                "static_fingerprint": static_fp,
                "pairwise_relation_fingerprint": _sha256(relation),
                "pairwise_relation_signature": relation,
                "first_passage_fingerprint": _sha256(passage),
                "first_passage_signature": passage,
                "intervention_fingerprint": _sha256(intervention),
                "intervention_signature": intervention,
                "critical_node_count": _critical_node_count(active, intervention),
                "mean_knockout_retained_fraction": _mean_knockout_retained(
                    active,
                    intervention,
                ),
                "mean_first_passage_depth": float(
                    np.mean(passage[1:])
                ),
            }
        )

    static_count = len({world["static_fingerprint"] for world in worlds})
    topology_count = len({world["edge_fingerprint"] for world in worlds})
    relation_count = len(
        {world["pairwise_relation_fingerprint"] for world in worlds}
    )
    passage_count = len(
        {world["first_passage_fingerprint"] for world in worlds}
    )
    intervention_count = len(
        {world["intervention_fingerprint"] for world in worlds}
    )

    relation_partition = _normalized_partition(
        [world["pairwise_relation_signature"] for world in worlds]
    )
    passage_partition = _normalized_partition(
        [world["first_passage_signature"] for world in worlds]
    )
    intervention_partition = _normalized_partition(
        [world["intervention_signature"] for world in worlds]
    )

    quotient_partitions_differ = len(
        {relation_partition, passage_partition, intervention_partition}
    ) > 1

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "static_fingerprint_count": static_count,
        "distinct_edge_topology_count": topology_count,
        "duplicate_edge_topology_count": WORLDS_PER_ROW - topology_count,
        "distinct_relation_target_count": relation_count,
        "distinct_first_passage_target_count": passage_count,
        "distinct_intervention_target_count": intervention_count,
        "relation_quotient_compression": (
            None if relation_count == 0 else topology_count / relation_count
        ),
        "first_passage_quotient_compression": (
            None if passage_count == 0 else topology_count / passage_count
        ),
        "intervention_quotient_compression": (
            None if intervention_count == 0 else topology_count / intervention_count
        ),
        "target_partitions_differ": quotient_partitions_differ,
        "worlds": worlds,
    }


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def _median(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.median(vals))


def _dist(values):
    return {
        str(key): int(count)
        for key, count in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_random_topology_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v12 protocol is not frozen")

    rows = [
        _evaluate(active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    if len(rows) != len(ACTIVE_SIZES) * REPLICATES:
        raise RuntimeError("unexpected v12 row count")

    static_violations = sum(
        row["static_fingerprint_count"] != 1 for row in rows
    )
    relation_variable_rows = sum(
        row["distinct_relation_target_count"] > 1 for row in rows
    )
    passage_variable_rows = sum(
        row["distinct_first_passage_target_count"] > 1 for row in rows
    )
    intervention_variable_rows = sum(
        row["distinct_intervention_target_count"] > 1 for row in rows
    )
    partition_difference_rows = sum(
        row["target_partitions_differ"] for row in rows
    )
    topology_collapse_rows = sum(
        row["distinct_edge_topology_count"] < 2 for row in rows
    )

    all_worlds = [
        world
        for row in rows
        for world in row["worlds"]
    ]
    edge_counts = [world["edge_count"] for world in all_worlds]
    robustness = [
        world["mean_knockout_retained_fraction"] for world in all_worlds
    ]
    depths = [world["mean_first_passage_depth"] for world in all_worlds]
    rho_robustness = _spearman(edge_counts, robustness)
    rho_depth = _spearman(edge_counts, depths)

    by_p = {}
    for p in EXTRA_P:
        subset = [
            world
            for world in all_worlds
            if abs(world["extra_edge_probability"] - p) < 1e-15
        ]
        by_p[f"{p:.2f}"] = {
            "world_count": len(subset),
            "mean_edge_count": _mean(world["edge_count"] for world in subset),
            "mean_knockout_retained_fraction": _mean(
                world["mean_knockout_retained_fraction"] for world in subset
            ),
            "mean_first_passage_depth": _mean(
                world["mean_first_passage_depth"] for world in subset
            ),
            "mean_critical_node_count": _mean(
                world["critical_node_count"] for world in subset
            ),
        }

    by_size = {}
    for active_n in ACTIVE_SIZES:
        subset = [row for row in rows if row["active_node_count"] == active_n]
        by_size[str(active_n)] = {
            "row_count": len(subset),
            "distinct_topology_count_distribution": _dist(
                row["distinct_edge_topology_count"] for row in subset
            ),
            "distinct_relation_target_count_distribution": _dist(
                row["distinct_relation_target_count"] for row in subset
            ),
            "distinct_first_passage_target_count_distribution": _dist(
                row["distinct_first_passage_target_count"] for row in subset
            ),
            "distinct_intervention_target_count_distribution": _dist(
                row["distinct_intervention_target_count"] for row in subset
            ),
            "median_relation_quotient_compression": _median(
                row["relation_quotient_compression"] for row in subset
            ),
            "median_first_passage_quotient_compression": _median(
                row["first_passage_quotient_compression"] for row in subset
            ),
            "median_intervention_quotient_compression": _median(
                row["intervention_quotient_compression"] for row in subset
            ),
            "rows_with_duplicate_edge_topologies": sum(
                row["duplicate_edge_topology_count"] > 0 for row in subset
            ),
        }

    row_count = len(rows)
    verdicts = {
        "R1_static_nodewise_equivalence_is_exact": (
            "SUPPORTED" if static_violations == 0 else "REFUTED"
        ),
        "R2_random_topologies_usually_differ_in_pairwise_relations": (
            "SUPPORTED"
            if relation_variable_rows / row_count >= 0.95
            else "REFUTED"
        ),
        "R3_random_topologies_usually_differ_in_first_passage": (
            "SUPPORTED"
            if passage_variable_rows / row_count >= 0.95
            else "REFUTED"
        ),
        "R4_random_topologies_usually_differ_in_intervention_response": (
            "SUPPORTED"
            if intervention_variable_rows / row_count >= 0.95
            else "REFUTED"
        ),
        "R5_edge_richness_increases_knockout_robustness": (
            "SUPPORTED" if rho_robustness > 0 else "REFUTED"
        ),
        "R6_edge_richness_shortens_first_passage": (
            "SUPPORTED" if rho_depth < 0 else "REFUTED"
        ),
        "R7_relational_targets_induce_different_quotients": (
            "SUPPORTED"
            if partition_difference_rows / row_count >= 0.50
            else "REFUTED"
        ),
        "R8_complete_static_occurrence_map_does_not_identify_random_topology": (
            "SUPPORTED" if topology_collapse_rows == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_random_static_equivalent_topology.result.v12",
        "row_count": row_count,
        "world_count": len(all_worlds),
        "predeclared_verdicts": verdicts,
        "static_equivalence_violation_count": static_violations,
        "rows_with_multiple_relation_targets": relation_variable_rows,
        "rows_with_multiple_first_passage_targets": passage_variable_rows,
        "rows_with_multiple_intervention_targets": intervention_variable_rows,
        "rows_with_target_partition_disagreement": partition_difference_rows,
        "rows_with_only_one_edge_topology": topology_collapse_rows,
        "pooled_spearman": {
            "edge_count_vs_knockout_retained_fraction": rho_robustness,
            "edge_count_vs_mean_first_passage_depth": rho_depth,
        },
        "by_extra_edge_probability": by_p,
        "by_active_node_count": by_size,
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
                "world_count": result["world_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "pooled_spearman": result["pooled_spearman"],
                "by_extra_edge_probability": result[
                    "by_extra_edge_probability"
                ],
                "by_active_node_count": result["by_active_node_count"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
