#!/usr/bin/env python3
"""Frozen paired random-graph generality test for source-uncertain minrelax v3.

Research-only synthetic test. Reuses v2's verified native EOG MRR on a
predeclared subset. The main sweep independently calculates shortest-hop
reachability at each finite geographic/environment/barrier breakpoint.
No observed movement, ecological source inference or field data is scored.
"""
from __future__ import annotations

import argparse
from collections import deque
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from statistics import mean
from typing import Any

from benchmarks.occurrence_conditioned_source_minrelax_v2 import (
    AXES, _pareto_min, run_source_universe,
)

PROTOCOL = Path("validation/occurrence_conditioned_source_minrelax_v3/protocol_v3.json")
MASK = 0xFFFFFFFF


class XorShift32:
    def __init__(self, seed: int) -> None:
        self.state = int(seed) & MASK
        if self.state == 0:
            raise ValueError("xorshift32 requires a nonzero seed")

    def draw(self) -> float:
        x = self.state
        x ^= (x << 13) & MASK
        x ^= x >> 17
        x ^= (x << 5) & MASK
        self.state = x & MASK
        return self.state / 4294967296.0


def _digest(value: object) -> str:
    return sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def generate_graph(
    generator: dict[str, Any], n_sources: int, density_index: int,
    seed_index: int, regime: str,
) -> dict[str, Any]:
    """Construct paired source cores with exactly matched optional edge draws."""
    if regime not in generator["source_core_regimes"]:
        raise ValueError("unknown source-core regime")
    if n_sources not in generator["source_counts"]:
        raise ValueError("source count outside frozen roster")
    if not 0 <= seed_index < generator["random_seeds"]:
        raise ValueError("random seed outside frozen roster")
    density = generator["source_to_target_optional_probabilities"][density_index]
    rng = XorShift32(20261120 + 10000 * n_sources + 1000 * density_index + 37 * seed_index)
    n_targets = generator["target_count"]
    sources = tuple(f"S{i}" for i in range(n_sources))
    targets = tuple(f"T{j}" for j in range(n_targets))
    original = [dict(edge) for edge in generator["guaranteed_anchor_outgoing_edges"]]
    optional: list[dict[str, Any]] = []

    def optional_edge(u: str, v: str, probability: float) -> None:
        if rng.draw() >= probability:
            return
        levels = generator["optional_edge_requirement_distributions"]
        optional.append({
            "source": u,
            "target": v,
            "geographic_km": levels["geographic_km"][int(rng.draw() * len(levels["geographic_km"]))],
            "environmental_units": levels["environmental_units"][int(rng.draw() * len(levels["environmental_units"]))],
            "barrier_permission": int(rng.draw() < levels["barrier_probability"]),
            "hard_unavailable": rng.draw() < levels["hard_unavailable_probability"],
        })

    for i in range(1, n_sources):
        for target in targets:
            optional_edge(sources[i], target, density)
    for i, node in enumerate(targets):
        for j, target in enumerate(targets):
            if i != j:
                optional_edge(node, target, generator["target_to_target_optional_probability"])

    core: list[dict[str, Any]] = []
    for i, source in enumerate(sources):
        for j, target in enumerate(sources):
            if i == j:
                continue
            if regime == "unidirectional_cycle_baseline" and j != (i + 1) % n_sources:
                continue
            core.append({
                "source": source, "target": target,
                "geographic_km": 8, "environmental_units": 0,
                "barrier_permission": 0, "hard_unavailable": False,
            })
    edges = original + optional + core
    pairs = [(e["source"], e["target"]) for e in edges]
    if len(set(pairs)) != len(pairs):
        raise AssertionError("duplicate directed edge in generator")
    return {
        "node_ids": sources + targets,
        "positive_occurrence_ids": sources + targets,
        "alternative_singleton_sources": [
            {"id": f"from_{s}", "source_ids": [s]} for s in sources
        ],
        "baseline": generator["baseline"],
        "max_breakpoint_worlds": generator["baseline_node_worlds_max"],
        "candidate_directed_edges": edges,
        "optional_edge_digest": _digest(optional),
    }


def _threshold_grid(edges: list[dict[str, Any]], base: tuple[float, ...]) -> tuple[tuple[float, ...], ...]:
    available = [edge for edge in edges if not edge["hard_unavailable"]]
    axes = [
        sorted({base[i]} | {
            float(edge[AXES[i]]) for edge in available if edge[AXES[i]] > base[i]
        })
        for i in range(3)
    ]
    return tuple(
        tuple(float(t[i] - base[i]) for i in range(3))
        for t in product(*axes)
    )


def _greatest_shortest_hops(
    nodes: tuple[str, ...], source: str, active_edges: list[dict[str, Any]],
) -> int:
    """Independent finite directed shortest-hop calculation."""
    adj: dict[str, list[str]] = {s: [] for s in nodes}
    for edge in active_edges:
        adj[edge["source"]].append(edge["target"])
    for row in adj.values():
        row.sort()
    distances = {source: 0}
    queue: deque[str] = deque([source])
    while queue:
        node = queue.popleft()
        for next_node in adj[node]:
            if next_node not in distances:
                distances[next_node] = distances[node] + 1
                queue.append(next_node)
    if len(distances) != len(nodes):
        return len(nodes) + 1  # unavailable for every tested H <= n_nodes-1
    return max(distances.values())


def _evaluate_graph(spec: dict[str, Any], horizons: tuple[int, ...]) -> dict[int, dict[str, Any]]:
    universe = spec["universe"]
    nodes = tuple(universe["node_ids"])
    edges = universe["candidate_directed_edges"]
    sources = tuple(row["source_ids"][0] for row in universe["alternative_singleton_sources"])
    baseline = tuple(float(universe["baseline"][name]) for name in AXES)
    grid = _threshold_grid(edges, baseline)
    if len(grid) > universe["max_breakpoint_worlds"]:
        raise ValueError("exceeded preregistered finite world budget")
    minimal_hops_by_world: dict[tuple[float, ...], dict[str, int]] = {}
    for delta in grid:
        threshold = tuple(delta[i] + baseline[i] for i in range(3))
        active = [
            edge for edge in edges if not edge["hard_unavailable"]
            and all(edge[AXES[i]] <= threshold[i] for i in range(3))
        ]
        minimal_hops_by_world[delta] = {
            s: _greatest_shortest_hops(nodes, s, active) for s in sources
        }
    rows = {}
    for H in horizons:
        by_source = {
            s: {point for point in grid if minimal_hops_by_world[point][s] <= H}
            for s in sources
        }
        possible = set().union(*by_source.values())
        universal = set.intersection(*(set(f) for f in by_source.values()))
        per_source_frontier = {f"from_{s}": [list(x) for x in _pareto_min(f)] for s, f in by_source.items()}
        rows[H] = {
            "horizon_steps": H,
            "worlds": len(grid),
            "source_count": len(sources),
            "per_source_compatible_counts": {f"from_{s}": len(f) for s, f in by_source.items()},
            "per_source_frontiers": per_source_frontier,
            "possible_worlds": len(possible),
            "source_robust_worlds": len(universal),
            "possible_frontier": [list(x) for x in _pareto_min(possible)],
            "source_robust_frontier": [list(x) for x in _pareto_min(universal)],
            "gap_worlds": len(possible) - len(universal),
            "gap_world_fraction": (len(possible) - len(universal)) / len(grid),
            "_possible_set": possible,
            "_robust_set": universal,
        }
    return rows


def _assert_native_agrees(spec: dict[str, Any], H: int, independent: dict[str, Any]) -> None:
    """Audit the frozen deterministic seed=0 panel using original EOG operators."""
    result = run_source_universe(spec, horizon=H)
    for expected_key, native_key in (
        ("worlds", "worlds_per_source"),
        ("possible_worlds", "possible_compatible_world_count"),
        ("source_robust_worlds", "source_robust_compatible_world_count"),
    ):
        if independent[expected_key] != result[native_key]:
            raise AssertionError(f"native-v2 mismatch {expected_key} at H={H}")
    if independent["per_source_compatible_counts"] != result["compatible_world_counts_by_source"]:
        raise AssertionError("native-v2 source-specific compatible counts differ")
    for name, frontier in independent["per_source_frontiers"].items():
        if {tuple(x) for x in frontier} != {tuple(x) for x in result["source_frontiers"][name]}:
            raise AssertionError("native-v2 source-specific antichain differs")
    for key, native_key in (
        ("possible_frontier", "possible_frontier"),
        ("source_robust_frontier", "source_robust_frontier"),
    ):
        if {tuple(x) for x in independent[key]} != {tuple(x) for x in result[native_key]}:
            raise AssertionError("native-v2 possible/robust antichain differs")


def run_protocol(protocol: dict[str, Any]) -> dict[str, Any]:
    G = protocol["generator"]
    all_rows: list[dict[str, Any]] = []
    paired: dict[tuple[int, int, int, str, int], dict[str, Any]] = {}
    horizon_checks = 0
    terminal_checks = 0
    native_checks = 0
    identical_two_source_pairs = 0
    for n_sources in G["source_counts"]:
        Hs = tuple(sorted({1, 2, 3, n_sources + G["target_count"] - 1}))
        for density_index in range(len(G["source_to_target_optional_probabilities"])):
            for seed_index in range(G["random_seeds"]):
                for regime in G["source_core_regimes"]:
                    universe = generate_graph(G, n_sources, density_index, seed_index, regime)
                    spec = {"universe": universe}
                    rows = _evaluate_graph(spec, Hs)
                    previous = None
                    for H in Hs:
                        values = rows[H]
                        if previous is not None:
                            horizon_checks += 1
                            if (not previous["_possible_set"].issubset(values["_possible_set"])
                                or not previous["_robust_set"].issubset(values["_robust_set"])):
                                raise AssertionError("source feasible sets shrank when hop horizon grew")
                        previous = values
                        if H == len(universe["node_ids"]) - 1:
                            terminal_checks += 1
                            if values["_possible_set"] != values["_robust_set"]:
                                raise AssertionError("strong source-core SCC terminal convergence failure")
                        if seed_index == 0 and H in (n_sources - 1, len(universe["node_ids"]) - 1):
                            _assert_native_agrees(spec, H, values)
                            native_checks += 1
                        row = {
                            key: value for key, value in values.items() if not key.startswith("_")
                        }
                        row.update({
                            "n_sources": n_sources,
                            "density_index": density_index,
                            "source_to_target_optional_probability": G["source_to_target_optional_probabilities"][density_index],
                            "seed_index": seed_index,
                            "source_core_regime": regime,
                            "optional_edge_digest": universe["optional_edge_digest"],
                        })
                        all_rows.append(row)
                        paired[n_sources, density_index, seed_index, regime, H] = row

                if n_sources == 2:
                    for H in Hs:
                        a = paired[n_sources, density_index, seed_index, G["source_core_regimes"][0], H]
                        b = paired[n_sources, density_index, seed_index, G["source_core_regimes"][1], H]
                        identical_two_source_pairs += 1
                        comparable = (
                            "worlds", "possible_worlds", "source_robust_worlds",
                            "per_source_frontiers", "possible_frontier", "source_robust_frontier",
                            "gap_world_fraction", "optional_edge_digest"
                        )
                        if any(a[k] != b[k] for k in comparable):
                            raise AssertionError("two-source cycle and complete baselines differ")
    primary: list[dict[str, Any]] = []
    for n_sources in (3, 4):
        H = n_sources - 1
        for di in range(len(G["source_to_target_optional_probabilities"])):
            for si in range(G["random_seeds"]):
                a = paired[n_sources, di, si, G["source_core_regimes"][0], H]
                b = paired[n_sources, di, si, G["source_core_regimes"][1], H]
                if a["optional_edge_digest"] != b["optional_edge_digest"] or a["worlds"] != b["worlds"]:
                    raise AssertionError("regime comparison changed optional candidate graph or threshold grid")
                primary.append({
                    "n_sources": n_sources,
                    "density_index": di,
                    "seed_index": si,
                    "H": H,
                    "complete_gap_fraction": a["gap_world_fraction"],
                    "cycle_gap_fraction": b["gap_world_fraction"],
                    "cycle_minus_complete": b["gap_world_fraction"] - a["gap_world_fraction"],
                })
    if len(primary) != 96 or len(all_rows) != 1152 or native_checks != 24:
        raise AssertionError("frozen protocol denominator mismatch")
    contrasts = [r["cycle_minus_complete"] for r in primary]
    positive = sum(v > 0 for v in contrasts)
    negative = sum(v < 0 for v in contrasts)
    equal = sum(v == 0 for v in contrasts)
    by_n_source_density = []
    for n in (3, 4):
        for di in range(2):
            cases = [r for r in primary if r["n_sources"] == n and r["density_index"] == di]
            by_n_source_density.append({
                "n_sources": n,
                "density_index": di,
                "paired_graphs": len(cases),
                "cycle_mean_gap_fraction": mean(r["cycle_gap_fraction"] for r in cases),
                "complete_mean_gap_fraction": mean(r["complete_gap_fraction"] for r in cases),
                "cycle_advantage_positive": sum(r["cycle_minus_complete"] > 0 for r in cases),
                "cycle_advantage_negative": sum(r["cycle_minus_complete"] < 0 for r in cases),
            })
    world_counts = sorted({row["worlds"] for row in all_rows})
    result = {
        "schema": "eog.source_uncertain_minrelax_random_generality_v3.result",
        "pre_score_protocol_commit": "32626e5a5726d8f33083163c2e2dfc31b7eb2f46",
        "scope": "synthetic directed graph generator; no field movement or verified actual source",
        "outcomes": {
            "G1_cycle_gap_strictly_larger_mean_than_complete": (
                "SUPPORTED_WITHIN_FROZEN_SYNTHETIC_GENERATOR"
                if mean(contrasts) > 0 else "REFUTED_OR_NOT_SUPPORTED"
            ),
            "G2_horizon_monotonicity": "IMPLEMENTATION_CONTRACT_PASSED",
            "G3_terminal_source_core_convergence": "IMPLEMENTATION_CONTRACT_PASSED",
            "G4_two_source_regime_identity": "NEGATIVE_CONTROL_PASSED",
            "G5_native_EOG_vs_independent_BFS": "INDEPENDENT_CHECK_PASSED",
        },
        "summary": {
            "rows": len(all_rows),
            "unique_source_count_density_seed_graphs": len(all_rows) // 4,
            "matched_regime_graph_pairs": len(all_rows) // 8,
            "primary_paired_graphs": len(primary),
            "primary_cycle_minus_complete_mean_gap_fraction": mean(contrasts),
            "primary_direction_counts": {
                "cycle_larger": positive,
                "equal": equal,
                "complete_larger": negative,
            },
            "terminal_source_core_checks": terminal_checks,
            "horizon_monotonicity_pair_checks": horizon_checks,
            "two_source_equivalent_regime_checks": identical_two_source_pairs,
            "native_EOG_v2_cross_checks": native_checks,
            "world_count_distribution": {
                str(w): sum(row["worlds"] == w for row in all_rows)
                for w in world_counts
            },
            "primary_by_source_count_and_density": by_n_source_density,
        },
        "primary_paired_rows": primary,
        "all_synthetic_panels": all_rows,
        "independent_ecological_replications": 0,
        "new_EOG_WF_empirical_endpoints": 0,
    }
    result["sha256_without_self_hash"] = _digest(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = run_protocol(protocol)
    content = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(json.dumps({k: v for k, v in result.items() if k not in ("all_synthetic_panels", "primary_paired_rows")}, indent=2))
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
