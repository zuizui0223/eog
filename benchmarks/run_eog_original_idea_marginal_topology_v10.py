#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_marginal_topology_v10/protocol_v10.json"
ACTIVE_SIZES = (6, 10, 14)
REPLICATES = 64
OUTSIDE_COUNT = 4
SEED_BASE = 20261201
TOPOLOGIES = ("chain", "star", "balanced_branching", "redundant")


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


def _rng(active_n, replicate):
    return np.random.default_rng(SEED_BASE + active_n * 1000 + replicate)


def _world_nodes(active_n, replicate):
    rng = _rng(active_n, replicate)
    source = "S"
    non_source = [f"N{i:02d}" for i in range(1, active_n)]
    shuffled = list(rng.permutation(non_source))
    active = (source, *shuffled)
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
    return active, outside, all_nodes, scores


def _chain_edges(active):
    return tuple((active[i], active[i + 1]) for i in range(len(active) - 1))


def _star_edges(active):
    source = active[0]
    return tuple((source, node) for node in active[1:])


def _balanced_edges(active):
    # Heap-style rooted binary tree in the shared shuffled active-node order.
    rows = []
    for i in range(1, len(active)):
        parent = (i - 1) // 2
        rows.append((active[parent], active[i]))
    return tuple(rows)


def _redundant_edges(active, replicate):
    source = active[0]
    rows = set(_balanced_edges(active))
    rows.update((source, node) for node in active[1:])

    # Add deterministic forward cross-branch edges.  These do not change the source
    # reachable mask but make internal route structure richer than the star/tree.
    rng = np.random.default_rng(SEED_BASE + 900000 + len(active) * 1000 + replicate)
    for i in range(1, len(active) - 1):
        for j in range(i + 1, len(active)):
            if rng.random() < 0.35:
                rows.add((active[i], active[j]))
    return tuple(sorted(rows))


def _edges(topology, active, replicate):
    if topology == "chain":
        return _chain_edges(active)
    if topology == "star":
        return _star_edges(active)
    if topology == "balanced_branching":
        return _balanced_edges(active)
    if topology == "redundant":
        return _redundant_edges(active, replicate)
    raise ValueError(topology)


def _graph(all_nodes, edges, removed=None):
    graph = {node: set() for node in all_nodes if node != removed}
    for a, b in edges:
        if a == removed or b == removed:
            continue
        graph[a].add(b)
    return {node: tuple(sorted(neighbours)) for node, neighbours in graph.items()}


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
    bits = []
    for source in active:
        reach = set(_distances(graph, source))
        for target in active:
            if source == target:
                continue
            bits.append(1 if target in reach else 0)
    return tuple(bits)


def _first_passage_signature(graph, active):
    dist = _distances(graph, active[0])
    return tuple(int(dist[node]) for node in active)


def _intervention_signature(all_nodes, active, edges):
    source = active[0]
    values = []
    for removed in active[1:]:
        graph = _graph(all_nodes, edges, removed=removed)
        reachable = set(_distances(graph, source))
        retained = sum(node in reachable for node in active if node != removed)
        values.append(int(retained))
    return tuple(values)


def _critical_node_count(all_nodes, active, edges):
    baseline = len(active)
    signature = _intervention_signature(all_nodes, active, edges)
    # Removing one non-source node necessarily removes that node itself.  It is
    # "critical" only if at least one additional active node becomes unreachable.
    return sum(retained < baseline - 1 for retained in signature)


def _mean_retained_fraction(active, intervention_signature):
    denom = len(active) - 1
    if denom <= 0:
        return 1.0
    return float(np.mean([value / denom for value in intervention_signature]))


def _hamming(left, right):
    if len(left) != len(right):
        raise ValueError("signatures must have equal length")
    return sum(a != b for a, b in zip(left, right, strict=True))


def _evaluate(active_n, replicate):
    active, outside, all_nodes, scores = _world_nodes(active_n, replicate)

    static = {
        "A_mask": tuple(1 for _ in all_nodes),
        "B_mask": tuple(1 for _ in all_nodes),
        "M_mask": tuple(1 if node in set(active) else 0 for node in all_nodes),
        "G_mask": tuple(1 if node in set(active) else 0 for node in all_nodes),
        "static_marginal_scores": tuple(scores[node] for node in all_nodes),
    }
    static_fp = _sha256(static)

    worlds = {}
    for topology in TOPOLOGIES:
        edges = _edges(topology, active, replicate)
        graph = _graph(all_nodes, edges)
        source_dist = _distances(graph, active[0])
        if set(source_dist) != set(active):
            raise RuntimeError(
                f"{topology} failed shared M mask for n={active_n}, rep={replicate}"
            )
        relation = _pairwise_signature(graph, active)
        first_passage = _first_passage_signature(graph, active)
        intervention = _intervention_signature(all_nodes, active, edges)
        worlds[topology] = {
            "edge_count": len(edges),
            "edge_fingerprint": _sha256(edges),
            "static_fingerprint": static_fp,
            "pairwise_relation_signature": relation,
            "pairwise_relation_fingerprint": _sha256(relation),
            "first_passage_signature": first_passage,
            "first_passage_fingerprint": _sha256(first_passage),
            "intervention_signature": intervention,
            "intervention_fingerprint": _sha256(intervention),
            "critical_node_count": _critical_node_count(
                all_nodes,
                active,
                edges,
            ),
            "mean_knockout_retained_fraction": _mean_retained_fraction(
                active,
                intervention,
            ),
        }

    static_fps = {row["static_fingerprint"] for row in worlds.values()}
    relation_fps = {
        row["pairwise_relation_fingerprint"] for row in worlds.values()
    }
    passage_fps = {
        row["first_passage_fingerprint"] for row in worlds.values()
    }
    intervention_fps = {
        row["intervention_fingerprint"] for row in worlds.values()
    }
    topology_fps = {row["edge_fingerprint"] for row in worlds.values()}

    relation_hamming = {}
    topology_list = list(TOPOLOGIES)
    for i, left in enumerate(topology_list):
        for right in topology_list[i + 1 :]:
            key = f"{left}__vs__{right}"
            relation_hamming[key] = _hamming(
                worlds[left]["pairwise_relation_signature"],
                worlds[right]["pairwise_relation_signature"],
            )

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "active_nodes": list(active),
        "outside_nodes": list(outside),
        "static_fingerprint_count": len(static_fps),
        "topology_fingerprint_count": len(topology_fps),
        "distinct_relation_signature_count": len(relation_fps),
        "distinct_first_passage_signature_count": len(passage_fps),
        "distinct_intervention_signature_count": len(intervention_fps),
        "redundant_minus_chain_knockout_retained_fraction": (
            worlds["redundant"]["mean_knockout_retained_fraction"]
            - worlds["chain"]["mean_knockout_retained_fraction"]
        ),
        "relation_refines_static": len(relation_fps) > 1,
        "pairwise_relation_hamming": relation_hamming,
        "worlds": worlds,
    }


def _mean(values):
    values = list(values)
    return None if not values else float(np.mean(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_topology_equivalence_benchmark_implementation_and_scoring"
    ):
        raise RuntimeError("v10 protocol is not frozen")

    rows = [
        _evaluate(active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    expected = len(ACTIVE_SIZES) * REPLICATES
    if len(rows) != expected:
        raise RuntimeError(f"expected {expected} rows, got {len(rows)}")

    m1_violations = sum(row["static_fingerprint_count"] != 1 for row in rows)
    m2_failures = sum(row["distinct_relation_signature_count"] < 2 for row in rows)
    m3_failures = sum(
        row["distinct_first_passage_signature_count"] < 2 for row in rows
    )
    m4_failures = sum(
        row["distinct_intervention_signature_count"] < 2 for row in rows
    )
    m5_failures = sum(
        row["redundant_minus_chain_knockout_retained_fraction"] <= 0
        for row in rows
    )
    m6_relation_failures = m2_failures
    m6_passage_failures = m3_failures
    m6_intervention_failures = m4_failures
    m7_failures = sum(
        row["static_fingerprint_count"] != 1
        or row["topology_fingerprint_count"] < 2
        for row in rows
    )
    m8_failures = sum(not row["relation_refines_static"] for row in rows)

    by_size = {}
    for active_n in ACTIVE_SIZES:
        subset = [row for row in rows if row["active_node_count"] == active_n]
        by_size[str(active_n)] = {
            "row_count": len(subset),
            "mean_distinct_relation_signatures": _mean(
                row["distinct_relation_signature_count"] for row in subset
            ),
            "relation_signature_count_distribution": {
                str(value): sum(
                    row["distinct_relation_signature_count"] == value
                    for row in subset
                )
                for value in sorted(
                    {row["distinct_relation_signature_count"] for row in subset}
                )
            },
            "mean_pairwise_relation_hamming": {
                pair: _mean(
                    row["pairwise_relation_hamming"][pair] for row in subset
                )
                for pair in sorted(subset[0]["pairwise_relation_hamming"])
            },
            "mean_distinct_first_passage_signatures": _mean(
                row["distinct_first_passage_signature_count"] for row in subset
            ),
            "mean_distinct_intervention_signatures": _mean(
                row["distinct_intervention_signature_count"] for row in subset
            ),
            "mean_redundant_minus_chain_knockout_retained_fraction": _mean(
                row["redundant_minus_chain_knockout_retained_fraction"]
                for row in subset
            ),
            "mean_critical_node_count": {
                topology: _mean(
                    row["worlds"][topology]["critical_node_count"]
                    for row in subset
                )
                for topology in TOPOLOGIES
            },
            "mean_knockout_retained_fraction": {
                topology: _mean(
                    row["worlds"][topology]["mean_knockout_retained_fraction"]
                    for row in subset
                )
                for topology in TOPOLOGIES
            },
            "mean_first_passage_depth": {
                topology: _mean(
                    np.mean(
                        row["worlds"][topology]["first_passage_signature"][1:]
                    )
                    for row in subset
                )
                for topology in TOPOLOGIES
            },
        }

    verdicts = {
        "M1_static_BAM_and_marginal_maps_are_exactly_identical": (
            "SUPPORTED" if m1_violations == 0 else "REFUTED"
        ),
        "M2_pairwise_relation_structure_is_not_identified_by_the_static_map": (
            "SUPPORTED" if m2_failures == 0 else "REFUTED"
        ),
        "M3_first_passage_structure_is_not_identified_by_the_static_map": (
            "SUPPORTED" if m3_failures == 0 else "REFUTED"
        ),
        "M4_knockout_response_is_not_identified_by_the_static_map": (
            "SUPPORTED" if m4_failures == 0 else "REFUTED"
        ),
        "M5_redundant_topology_is_more_knockout_robust_than_chain": (
            "SUPPORTED" if m5_failures == 0 else "REFUTED"
        ),
        "M6_static_representation_collapses_target_distinct_worlds": (
            "SUPPORTED"
            if (
                m6_relation_failures == 0
                and m6_passage_failures == 0
                and m6_intervention_failures == 0
            )
            else "REFUTED"
        ),
        "M7_static_occurrence_completeness_does_not_resolve_topology": (
            "SUPPORTED" if m7_failures == 0 else "REFUTED"
        ),
        "M8_relational_information_strictly_refines_the_static_equivalence_class": (
            "SUPPORTED" if m8_failures == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_marginal_topology_equivalence.result.v10",
        "row_count": len(rows),
        "active_node_counts": list(ACTIVE_SIZES),
        "replicates_per_size": REPLICATES,
        "predeclared_verdicts": verdicts,
        "failure_counts": {
            "M1": m1_violations,
            "M2": m2_failures,
            "M3": m3_failures,
            "M4": m4_failures,
            "M5": m5_failures,
            "M6_relation": m6_relation_failures,
            "M6_first_passage": m6_passage_failures,
            "M6_intervention": m6_intervention_failures,
            "M7": m7_failures,
            "M8": m8_failures,
        },
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
                "predeclared_verdicts": result["predeclared_verdicts"],
                "failure_counts": result["failure_counts"],
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
