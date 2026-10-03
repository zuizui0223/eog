#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, deque
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation/eog_original_idea_virtual_worlds_v2/protocol_v2.json"

GRID_N = 7
AUTOCORR_LEVELS = ("low", "high")
BARRIER_LEVELS = (0.05, 0.20, 0.35)
NEIGHBOURHOODS = ("rook", "queen")
REPLICATES = 32
SEED_BASE = 20261003


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


def _nodes():
    return tuple((r, c) for r in range(GRID_N) for c in range(GRID_N))


def _node_id(node):
    return f"r{node[0]}c{node[1]}"


def _geo_edges(neighbourhood):
    offsets = [(1, 0), (0, 1)]
    if neighbourhood == "queen":
        offsets.extend([(1, 1), (1, -1)])
    nodes = set(_nodes())
    edges = []
    for r, c in sorted(nodes):
        for dr, dc in offsets:
            other = (r + dr, c + dc)
            if other in nodes:
                edges.append(tuple(sorted(((r, c), other))))
    return tuple(sorted(set(edges)))


def _rook_neighbours(node):
    r, c = node
    out = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        other = (r + dr, c + dc)
        if 0 <= other[0] < GRID_N and 0 <= other[1] < GRID_N:
            out.append(other)
    return tuple(out)


def _smooth(field, passes=4):
    current = field.copy()
    for _ in range(passes):
        nxt = current.copy()
        for r in range(GRID_N):
            for c in range(GRID_N):
                vals = [current[r, c]]
                vals.extend(current[x, y] for x, y in _rook_neighbours((r, c)))
                nxt[r, c] = float(np.mean(vals))
        current = nxt
    return current


def _connected_component(graph, source):
    seen = {source}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in graph.get(node, ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return frozenset(seen)


def _components(graph, active):
    remaining = set(active)
    rows = []
    while remaining:
        source = min(remaining)
        comp = _connected_component(graph, source)
        comp = frozenset(node for node in comp if node in active)
        rows.append(comp)
        remaining.difference_update(comp)
    return tuple(sorted(rows, key=lambda x: (-len(x), tuple(sorted(x)))))


def _graph_from_edges(active, edges):
    graph = {node: set() for node in active}
    for a, b in edges:
        if a not in active or b not in active:
            continue
        graph[a].add(b)
        graph[b].add(a)
    return {node: frozenset(sorted(nbrs)) for node, nbrs in graph.items()}


def _bfs_distances(graph, source, blocked_node=None):
    if source == blocked_node or source not in graph:
        return {}
    dist = {source: 0}
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt == blocked_node or nxt in dist:
                continue
            dist[nxt] = dist[node] + 1
            queue.append(nxt)
    return dist


def _edge_uniform(edge, replicate, neighbourhood):
    # Stable edge-specific pseudo-random number independent of barrier-density level.
    payload = (
        f"{SEED_BASE}|barrier|{replicate}|{neighbourhood}|"
        f"{edge[0][0]},{edge[0][1]}|{edge[1][0]},{edge[1][1]}"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float(2**64)


def _generate_base(replicate, autocorr, neighbourhood):
    env_rng = np.random.default_rng(SEED_BASE + replicate * 1009)
    raw = env_rng.normal(size=(GRID_N, GRID_N))
    env = raw if autocorr == "low" else _smooth(raw, passes=4)

    center = float(np.median(env))
    absdev = np.abs(env - center)
    a_threshold = float(np.quantile(absdev, 0.70, method="linear"))
    A = {
        (r, c)
        for r in range(GRID_N)
        for c in range(GRID_N)
        if abs(float(env[r, c]) - center) <= a_threshold + 1e-15
    }

    b_rng = np.random.default_rng(SEED_BASE + 500000 + replicate * 1013)
    b_field = b_rng.normal(size=(GRID_N, GRID_N))
    b_cut = float(np.quantile(b_field, 0.90, method="linear"))
    B = {
        (r, c)
        for r in range(GRID_N)
        for c in range(GRID_N)
        if float(b_field[r, c]) <= b_cut + 1e-15
    }
    permissive = A & B

    geo_edges = _geo_edges(neighbourhood)
    diffs = np.asarray(
        [abs(float(env[a]) - float(env[b])) for a, b in geo_edges],
        dtype=float,
    )
    env_cut = float(np.quantile(diffs, 0.70, method="linear"))
    env_edges = tuple(
        edge
        for edge in geo_edges
        if abs(float(env[edge[0]]) - float(env[edge[1]])) <= env_cut + 1e-15
    )

    geo_graph = _graph_from_edges(permissive, geo_edges)
    comps = _components(geo_graph, permissive)
    if not comps or len(comps[0]) < 2:
        raise RuntimeError("response-independent permissive component too small")
    largest = comps[0]

    source_rng = np.random.default_rng(
        SEED_BASE
        + 800000
        + replicate * 1019
        + (0 if autocorr == "low" else 17)
        + (0 if neighbourhood == "rook" else 31)
    )
    source = sorted(largest)[int(source_rng.integers(0, len(largest)))]

    edge_u = {edge: _edge_uniform(edge, replicate, neighbourhood) for edge in geo_edges}
    return {
        "env": env,
        "A": A,
        "B": B,
        "permissive": permissive,
        "geo_edges": geo_edges,
        "env_edges": env_edges,
        "geo_graph": geo_graph,
        "env_cut": env_cut,
        "source": source,
        "edge_uniform": edge_u,
    }


def _edge_subset(base, *, barrier_density, use_environment, use_barrier):
    edges = base["geo_edges"]
    if use_environment:
        allowed_env = set(base["env_edges"])
        edges = tuple(edge for edge in edges if edge in allowed_env)
    if use_barrier:
        edges = tuple(
            edge
            for edge in edges
            if base["edge_uniform"][edge] >= barrier_density
        )
    return edges


def _criticality(graph, source, truth_reachable):
    if len(truth_reachable) <= 1:
        return 0, 0.0, 1.0

    non_source = sorted(node for node in truth_reachable if node != source)
    critical_nodes = 0
    target_robust = {node: True for node in non_source}

    for blocked in non_source:
        after = _bfs_distances(graph, source, blocked_node=blocked)
        lost_other = [
            node
            for node in truth_reachable
            if node not in {source, blocked} and node not in after
        ]
        if lost_other:
            critical_nodes += 1
        for target in non_source:
            if target == blocked:
                continue
            if target not in after:
                target_robust[target] = False

    critical_fraction = critical_nodes / len(non_source)
    robust_fraction = (
        sum(target_robust.values()) / len(target_robust)
        if target_robust
        else 1.0
    )
    return critical_nodes, critical_fraction, robust_fraction


def _temporal_contraction(graph, source, truth_reachable):
    truth_dist = _bfs_distances(graph, source)
    alias_count = len(truth_reachable)
    if alias_count <= 1:
        return alias_count, None, 0, ()

    constraints = []
    for depth in (1, 2, 3):
        nodes = sorted(
            node
            for node in truth_reachable
            if truth_dist.get(node) == depth
        )
        if nodes:
            constraints.append((nodes[0], depth))
    if not constraints:
        return alias_count, None, 0, ()

    compatible = 0
    for candidate in sorted(truth_reachable):
        dist = _bfs_distances(graph, candidate)
        if all(
            node in dist and dist[node] <= max_depth
            for node, max_depth in constraints
        ):
            compatible += 1

    contraction = 1.0 - compatible / alias_count
    return alias_count, contraction, compatible, tuple(
        (_node_id(node), depth) for node, depth in constraints
    )


def _rescue_counts(
    permissive,
    truth_reachable,
    barrier_relaxed,
    env_relaxed,
    both_relaxed,
):
    counts = Counter()
    for target in permissive:
        if target in truth_reachable:
            continue
        rb = target in barrier_relaxed
        re = target in env_relaxed
        rall = target in both_relaxed
        if rb and not re:
            cat = "barrier_only"
        elif re and not rb:
            cat = "environment_only"
        elif rb and re:
            cat = "either_single_axis"
        elif (not rb) and (not re) and rall:
            cat = "both_barrier_and_environment"
        else:
            cat = "not_rescued_by_edge_relaxation"
        counts[cat] += 1
    return counts


def _replicate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    permissive = base["permissive"]
    source = base["source"]

    truth_edges = _edge_subset(
        base,
        barrier_density=barrier_density,
        use_environment=True,
        use_barrier=True,
    )
    barrier_relaxed_edges = _edge_subset(
        base,
        barrier_density=barrier_density,
        use_environment=True,
        use_barrier=False,
    )
    env_relaxed_edges = _edge_subset(
        base,
        barrier_density=barrier_density,
        use_environment=False,
        use_barrier=True,
    )
    both_relaxed_edges = _edge_subset(
        base,
        barrier_density=barrier_density,
        use_environment=False,
        use_barrier=False,
    )

    truth_graph = _graph_from_edges(permissive, truth_edges)
    barrier_relaxed_graph = _graph_from_edges(permissive, barrier_relaxed_edges)
    env_relaxed_graph = _graph_from_edges(permissive, env_relaxed_edges)
    both_relaxed_graph = _graph_from_edges(permissive, both_relaxed_edges)

    truth_dist = _bfs_distances(truth_graph, source)
    truth_reachable = frozenset(truth_dist)
    barrier_reachable = frozenset(_bfs_distances(barrier_relaxed_graph, source))
    env_reachable = frozenset(_bfs_distances(env_relaxed_graph, source))
    both_reachable = frozenset(_bfs_distances(both_relaxed_graph, source))

    if not truth_reachable.issubset(barrier_reachable):
        raise RuntimeError("barrier relaxation contracted reachability")
    if not truth_reachable.issubset(env_reachable):
        raise RuntimeError("environment relaxation contracted reachability")
    if not barrier_reachable.issubset(both_reachable):
        raise RuntimeError("joint relaxation failed to include barrier-relaxed set")
    if not env_reachable.issubset(both_reachable):
        raise RuntimeError("joint relaxation failed to include environment-relaxed set")

    viable_unreachable_fraction = (
        (len(permissive) - len(truth_reachable)) / len(permissive)
        if permissive
        else 0.0
    )

    source_env = float(base["env"][source])
    endpoint_similar_candidates = [
        node
        for node in env_reachable
        if node != source
        and abs(float(base["env"][node]) - source_env)
        <= base["env_cut"] + 1e-15
    ]
    pathwise_blocked = [
        node
        for node in endpoint_similar_candidates
        if node not in truth_reachable
    ]
    pathwise_blocked_fraction = (
        len(pathwise_blocked) / len(endpoint_similar_candidates)
        if endpoint_similar_candidates
        else 0.0
    )

    critical_count, critical_fraction, robust_target_fraction = _criticality(
        truth_graph,
        source,
        truth_reachable,
    )
    alias_count, temporal_contraction, temporal_remaining, constraints = (
        _temporal_contraction(truth_graph, source, truth_reachable)
    )
    rescue = _rescue_counts(
        permissive,
        truth_reachable,
        barrier_reachable,
        env_reachable,
        both_reachable,
    )

    return {
        "replicate": replicate,
        "environmental_autocorrelation": autocorr,
        "neighbourhood": neighbourhood,
        "barrier_density": barrier_density,
        "source": _node_id(source),
        "permissive_node_count": len(permissive),
        "truth_reachable_node_count": len(truth_reachable),
        "viable_unreachable_fraction": viable_unreachable_fraction,
        "endpoint_similar_candidate_count": len(endpoint_similar_candidates),
        "pathwise_blocked_count": len(pathwise_blocked),
        "pathwise_blocked_fraction": pathwise_blocked_fraction,
        "critical_stepping_node_count": critical_count,
        "critical_stepping_node_fraction": critical_fraction,
        "single_node_robust_target_fraction": robust_target_fraction,
        "static_source_history_alias_count": alias_count,
        "temporal_constraint_count": len(constraints),
        "temporal_compatible_source_count": temporal_remaining,
        "temporal_history_contraction_fraction": temporal_contraction,
        "temporal_constraints": [list(row) for row in constraints],
        "rescue_counts": dict(sorted(rescue.items())),
        "monotonicity_holds": True,
    }


def _mean(rows, field):
    return float(np.mean([float(row[field]) for row in rows]))


def _median_nonnull(rows, field):
    values = [
        float(row[field])
        for row in rows
        if row[field] is not None
    ]
    return None if not values else float(np.median(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != "frozen_before_randomized_generator_implementation_and_scoring":
        raise RuntimeError("v2 protocol is not frozen")

    rows = []
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            for replicate in range(REPLICATES):
                for barrier_density in BARRIER_LEVELS:
                    rows.append(
                        _replicate_row(
                            replicate,
                            autocorr,
                            neighbourhood,
                            barrier_density,
                        )
                    )

    if len(rows) != 384:
        raise RuntimeError(f"expected 384 rows, got {len(rows)}")

    g1_strata = {}
    g1_monotone = True
    for autocorr in AUTOCORR_LEVELS:
        for neighbourhood in NEIGHBOURHOODS:
            subset = [
                row
                for row in rows
                if row["environmental_autocorrelation"] == autocorr
                and row["neighbourhood"] == neighbourhood
            ]
            means = {
                str(level): _mean(
                    [row for row in subset if row["barrier_density"] == level],
                    "viable_unreachable_fraction",
                )
                for level in BARRIER_LEVELS
            }
            ordered = [means[str(level)] for level in BARRIER_LEVELS]
            monotone = ordered[0] <= ordered[1] + 1e-15 <= ordered[2] + 1e-15
            g1_monotone = g1_monotone and monotone
            g1_strata[f"{autocorr}|{neighbourhood}"] = {
                "means": means,
                "nondecreasing": monotone,
            }
    low_barrier = _mean(
        [row for row in rows if row["barrier_density"] == 0.05],
        "viable_unreachable_fraction",
    )
    high_barrier = _mean(
        [row for row in rows if row["barrier_density"] == 0.35],
        "viable_unreachable_fraction",
    )

    low_auto = _mean(
        [row for row in rows if row["environmental_autocorrelation"] == "low"],
        "pathwise_blocked_fraction",
    )
    high_auto = _mean(
        [row for row in rows if row["environmental_autocorrelation"] == "high"],
        "pathwise_blocked_fraction",
    )

    rook_critical = _mean(
        [row for row in rows if row["neighbourhood"] == "rook"],
        "critical_stepping_node_fraction",
    )
    queen_critical = _mean(
        [row for row in rows if row["neighbourhood"] == "queen"],
        "critical_stepping_node_fraction",
    )

    rook_robust = _mean(
        [row for row in rows if row["neighbourhood"] == "rook"],
        "single_node_robust_target_fraction",
    )
    queen_robust = _mean(
        [row for row in rows if row["neighbourhood"] == "queen"],
        "single_node_robust_target_fraction",
    )

    alias_median = float(
        np.median([row["static_source_history_alias_count"] for row in rows])
    )
    eligible_temporal = [
        row
        for row in rows
        if row["static_source_history_alias_count"] > 1
        and row["temporal_history_contraction_fraction"] is not None
    ]
    temporal_median = _median_nonnull(
        eligible_temporal,
        "temporal_history_contraction_fraction",
    )

    rescue_total = Counter()
    for row in rows:
        rescue_total.update(row["rescue_counts"])

    monotonicity_violations = sum(not row["monotonicity_holds"] for row in rows)

    verdicts = {
        "G1_barriers_increase_viable_unreachable_fraction": (
            "SUPPORTED"
            if g1_monotone and high_barrier > low_barrier
            else "REFUTED"
        ),
        "G2_low_autocorrelation_increases_pathwise_IBE_failures": (
            "SUPPORTED" if low_auto > high_auto else "REFUTED"
        ),
        "G3_sparse_neighbourhood_increases_critical_stepping_stones": (
            "SUPPORTED" if rook_critical > queen_critical else "REFUTED"
        ),
        "G4_wider_neighbourhood_increases_single_node_route_robustness": (
            "SUPPORTED" if queen_robust > rook_robust else "REFUTED"
        ),
        "G5_static_history_aliasing_is_common": (
            "SUPPORTED" if alias_median > 1 else "REFUTED"
        ),
        "G6_temporal_positive_evidence_contracts_source_history_aliases": (
            "SUPPORTED"
            if temporal_median is not None and temporal_median > 0
            else "REFUTED"
        ),
        "G7_impossibility_has_multiple_mechanistic_rescue_classes": (
            "SUPPORTED"
            if all(
                rescue_total[name] > 0
                for name in (
                    "barrier_only",
                    "environment_only",
                    "both_barrier_and_environment",
                )
            )
            else "REFUTED"
        ),
        "G8_world_expansion_monotonicity": (
            "SUPPORTED" if monotonicity_violations == 0 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_randomized_virtual_worlds.result.v2",
        "row_count": len(rows),
        "factorial": {
            "autocorrelation": list(AUTOCORR_LEVELS),
            "barrier_density": list(BARRIER_LEVELS),
            "neighbourhood": list(NEIGHBOURHOODS),
            "replicates_per_cell": REPLICATES,
        },
        "predeclared_verdicts": verdicts,
        "contrasts": {
            "G1": {
                "strata": g1_strata,
                "pooled_mean_barrier_0.05": low_barrier,
                "pooled_mean_barrier_0.35": high_barrier,
                "difference_high_minus_low": high_barrier - low_barrier,
            },
            "G2": {
                "low_autocorrelation_mean": low_auto,
                "high_autocorrelation_mean": high_auto,
                "difference_low_minus_high": low_auto - high_auto,
            },
            "G3": {
                "rook_mean": rook_critical,
                "queen_mean": queen_critical,
                "difference_rook_minus_queen": rook_critical - queen_critical,
            },
            "G4": {
                "rook_mean": rook_robust,
                "queen_mean": queen_robust,
                "difference_queen_minus_rook": queen_robust - rook_robust,
            },
            "G5": {
                "median_static_source_history_alias_count": alias_median,
            },
            "G6": {
                "eligible_replicate_count": len(eligible_temporal),
                "median_temporal_contraction_fraction": temporal_median,
            },
            "G7": {
                "rescue_category_counts": dict(sorted(rescue_total.items())),
            },
            "G8": {
                "monotonicity_violation_count": monotonicity_violations,
            },
        },
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
                "contrasts": result["contrasts"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
