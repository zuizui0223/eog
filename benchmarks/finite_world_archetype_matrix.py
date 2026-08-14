#!/usr/bin/env python3
"""Known-truth matrix for the integrated finite-world EOG core.

The matrix is deliberately small and qualitative. It tests whether the existing
reachability/world-reconstruction operators preserve distinctions that matter to the
active EOG mainline without adding a new public API or another empirical data line.

The scenarios separate geographic/IBD-like, environmental/IBE-like and barrier
constraints; retain alternative explanations; keep low support distinct from zero
support; detect branching/confluence; distinguish possible from robust basin merge
across analytical variants; and verify that a robust exclusion survives a declared
finite-universe expansion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    FiniteWorld,
    build_dynamic_transition_operator,
    build_monotone_relaxation_family,
    build_world_flow_set,
    infer_basin_merge,
    minimum_relaxation_frontier,
    propagate_dynamic_reachability,
    rank_positive_occurrence_candidates,
    reconstruct_compatible_worlds,
    summarize_first_passage,
)


def _operator(node_ids, edges, *, loss_support=1.0):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = []
    for edge in edges:
        source, target = edge[0], edge[1]
        geographic = edge[2] if len(edge) > 2 else 1.0
        environmental = edge[3] if len(edge) > 3 else 1.0
        barrier = edge[4] if len(edge) > 4 else 1.0
        declared.append(
            DynamicReachabilityEdge(
                source=index[source],
                target=index[target],
                geographic_support=float(geographic),
                environmental_support=float(environmental),
                barrier_support=float(barrier),
            )
        )
    return build_dynamic_transition_operator(node_ids, declared, loss_support=loss_support)


def _single_axis_frontier(worlds, occurrences, *, max_steps=4):
    reconstruction = reconstruct_compatible_worlds(worlds, occurrences, max_steps=max_steps)
    frontier = minimum_relaxation_frontier(reconstruction, worlds)
    return reconstruction, [
        {
            "world_id": point.world_id,
            "geographic_relaxation": point.geographic_relaxation,
            "environmental_relaxation": point.environmental_relaxation,
            "barrier_relaxation": point.barrier_relaxation,
        }
        for point in frontier.points
    ]


def _ibd_dominated():
    nodes = ("A", "X", "C")
    baseline = FiniteWorld(
        "baseline",
        _operator(nodes, (("A", "X", 0.0, 1.0, 1.0), ("X", "C", 1.0, 1.0, 1.0))),
        ("A",),
    )
    geo_relaxed = FiniteWorld(
        "geo_relaxed",
        _operator(nodes, (("A", "X", 0.8, 1.0, 1.0), ("X", "C", 0.8, 1.0, 1.0))),
        ("A",),
        geographic_relaxation=1.0,
    )
    reconstruction, frontier = _single_axis_frontier((baseline, geo_relaxed), ("A", "C"))
    return {
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "frontier": frontier,
        "axis_separated": frontier == [
            {
                "world_id": "geo_relaxed",
                "geographic_relaxation": 1.0,
                "environmental_relaxation": 0.0,
                "barrier_relaxation": 0.0,
            }
        ],
    }


def _ibe_dominated():
    nodes = ("A", "X", "C")
    baseline = FiniteWorld(
        "baseline",
        _operator(nodes, (("A", "X", 1.0, 0.0, 1.0), ("X", "C", 1.0, 1.0, 1.0))),
        ("A",),
    )
    env_relaxed = FiniteWorld(
        "env_relaxed",
        _operator(nodes, (("A", "X", 1.0, 0.8, 1.0), ("X", "C", 1.0, 0.8, 1.0))),
        ("A",),
        environmental_relaxation=1.0,
    )
    reconstruction, frontier = _single_axis_frontier((baseline, env_relaxed), ("A", "C"))
    return {
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "frontier": frontier,
        "axis_separated": frontier == [
            {
                "world_id": "env_relaxed",
                "geographic_relaxation": 0.0,
                "environmental_relaxation": 1.0,
                "barrier_relaxation": 0.0,
            }
        ],
    }


def _barrier_dominated():
    nodes = ("A", "X", "C")
    baseline = FiniteWorld(
        "baseline",
        _operator(nodes, (("A", "X", 1.0, 1.0, 1.0), ("X", "C", 1.0, 1.0, 0.0))),
        ("A",),
    )
    barrier_relaxed = FiniteWorld(
        "barrier_relaxed",
        _operator(nodes, (("A", "X", 1.0, 1.0, 1.0), ("X", "C", 1.0, 1.0, 0.8))),
        ("A",),
        barrier_relaxation=1.0,
    )
    reconstruction, frontier = _single_axis_frontier((baseline, barrier_relaxed), ("A", "C"))
    return {
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "frontier": frontier,
        "axis_separated": frontier == [
            {
                "world_id": "barrier_relaxed",
                "geographic_relaxation": 0.0,
                "environmental_relaxation": 0.0,
                "barrier_relaxation": 1.0,
            }
        ],
    }


def _niche_desert_tradeoff():
    nodes = ("A", "X", "C")
    baseline = FiniteWorld("baseline", _operator(nodes, (("A", "X", 1.0, 0.0, 1.0),)), ("A",))
    env_rescue = FiniteWorld(
        "env_rescue",
        _operator(nodes, (("A", "X", 1.0, 0.8, 1.0), ("X", "C", 1.0, 0.8, 1.0))),
        ("A",),
        environmental_relaxation=1.0,
    )
    jump_rescue = FiniteWorld(
        "jump_rescue",
        _operator(nodes, (("A", "C", 0.25, 1.0, 1.0),)),
        ("A",),
        geographic_relaxation=1.0,
    )
    reconstruction = reconstruct_compatible_worlds((baseline, env_rescue, jump_rescue), ("A", "C"), max_steps=4)
    frontier = minimum_relaxation_frontier(reconstruction, (baseline, env_rescue, jump_rescue))
    points = [
        {
            "world_id": point.world_id,
            "geographic_relaxation": point.geographic_relaxation,
            "environmental_relaxation": point.environmental_relaxation,
        }
        for point in frontier.points
    ]
    return {
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "frontier": points,
        "alternative_explanations_retained": {point["world_id"] for point in points} == {"env_rescue", "jump_rescue"},
    }


def _stepping_stone_reconstructability():
    nodes = ("A", "B", "C")
    stepping = FiniteWorld("stepping", _operator(nodes, (("A", "B"), ("B", "C"))), ("A",))
    direct = FiniteWorld("direct", _operator(nodes, (("A", "C"),)), ("A",))
    worlds = (stepping, direct)
    before = reconstruct_compatible_worlds(worlds, ("A", "C"), max_steps=3)
    ranking = rank_positive_occurrence_candidates(before, worlds, ("B",))
    after = reconstruct_compatible_worlds(worlds, ("A", "B", "C"), max_steps=3)
    row = ranking.rows[0]
    return {
        "before_world_ids": list(before.compatible_world_ids),
        "before_identifiable": before.identifiable,
        "candidate_status": row.status,
        "candidate_reachable_world_ids": list(row.reachable_world_ids),
        "positive_elimination_fraction": row.positive_elimination_fraction,
        "after_world_ids": list(after.compatible_world_ids),
        "after_identifiable": after.identifiable,
    }


def _rare_long_jump():
    nodes = ("A", "C")
    world = FiniteWorld(
        "rare_jump",
        _operator(nodes, (("A", "C", 1e-8, 1.0, 1.0),)),
        ("A",),
        geographic_relaxation=1.0,
    )
    reconstruction = reconstruct_compatible_worlds((world,), ("A", "C"), max_steps=1)
    passage = summarize_first_passage(world.operator, ("A",), "C", max_steps=1)
    return {
        "compatible": reconstruction.compatible_world_ids == ("rare_jump",),
        "support_positive": passage.horizon_support > 0.0,
        "support_below_1e-6": passage.horizon_support < 1e-6,
        "treated_as_impossible": passage.horizon_support <= 0.0,
    }


def _branch_and_confluence():
    nodes = ("A", "B", "C", "D")
    operator = _operator(nodes, (("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")))
    result = propagate_dynamic_reachability(operator, ("A",), max_steps=2)
    index = {node_id: i for i, node_id in enumerate(nodes)}
    branch_edges = (("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"))
    positive = [
        result.integrated_edge_flux[index[source], index[target]] > 0.0
        for source, target in branch_edges
    ]
    return {
        "all_declared_branch_edges_used": all(positive),
        "positive_branch_edge_count": sum(positive),
        "confluence_first_arrival_step": int(result.first_arrival_step[index["D"]]),
        "target_support_positive": bool(result.mass_by_step[2, index["D"]] > 0.0),
    }


def _analytical_ambiguity():
    nodes = ("A", "B", "C")

    def world(world_id, variant, level, edges):
        return FiniteWorld(
            world_id,
            _operator(nodes, edges),
            ("A",),
            environmental_relaxation=float(level),
            analytical_variant=variant,
        )

    family = build_monotone_relaxation_family(
        "analytical_ambiguity",
        {
            0.0: {
                "fine": world("fine-l0", "fine", 0.0, (("A", "B"),)),
                "coarse": world("coarse-l0", "coarse", 0.0, (("A", "B"),)),
            },
            1.0: {
                "fine": world("fine-l1", "fine", 1.0, (("A", "B"), ("B", "C"))),
                "coarse": world("coarse-l1", "coarse", 1.0, (("A", "B"),)),
            },
            2.0: {
                "fine": world("fine-l2", "fine", 2.0, (("A", "B"), ("B", "C"))),
                "coarse": world("coarse-l2", "coarse", 2.0, (("A", "B"), ("B", "C"))),
            },
        },
    )
    result = infer_basin_merge(family, {"source": ("A",), "target": ("C",)}, max_steps=3)
    return {
        "first_possible_level": result.first_possible_level,
        "first_robust_level": result.first_robust_level,
        "possible_but_variant_dependent": result.possible_but_variant_dependent,
        "coverage_certificate": result.coverage_certificate,
    }


def _robust_exclusion_under_universe_expansion():
    nodes = ("A", "C", "E")
    w1 = FiniteWorld("w1", _operator(nodes, (("A", "C", 0.8, 1.0, 1.0),)), ("A",))
    w2 = FiniteWorld("w2", _operator(nodes, (("A", "C", 1.0, 0.8, 1.0),)), ("A",))
    w3 = FiniteWorld(
        "w3_more_permissive",
        _operator(nodes, (("A", "C", 1.0, 1.0, 1.0), ("C", "E", 1.0, 1.0, 0.0))),
        ("A",),
        geographic_relaxation=1.0,
        environmental_relaxation=1.0,
        barrier_relaxation=1.0,
    )
    base_worlds = (w1, w2)
    expanded_worlds = (w1, w2, w3)
    base = reconstruct_compatible_worlds(base_worlds, ("A", "C"), max_steps=3)
    expanded = reconstruct_compatible_worlds(expanded_worlds, ("A", "C"), max_steps=3)
    base_flow = build_world_flow_set(base, base_worlds)
    expanded_flow = build_world_flow_set(expanded, expanded_worlds)
    return {
        "base_robustly_unreachable_ids": list(base_flow.robustly_unreachable_ids),
        "expanded_robustly_unreachable_ids": list(expanded_flow.robustly_unreachable_ids),
        "exclusion_survives_expansion": "E" in base_flow.robustly_unreachable_ids and "E" in expanded_flow.robustly_unreachable_ids,
        "expanded_world_count": len(expanded.compatible_world_ids),
    }


def run_archetype_matrix():
    return {
        "schema_version": 1,
        "claim_boundary": "known-truth structural benchmark; no empirical promotion",
        "scenarios": {
            "ibd_dominated": _ibd_dominated(),
            "ibe_dominated": _ibe_dominated(),
            "barrier_dominated": _barrier_dominated(),
            "niche_desert_tradeoff": _niche_desert_tradeoff(),
            "stepping_stone_reconstructability": _stepping_stone_reconstructability(),
            "rare_long_jump": _rare_long_jump(),
            "branch_and_confluence": _branch_and_confluence(),
            "analytical_ambiguity": _analytical_ambiguity(),
            "robust_exclusion_under_universe_expansion": _robust_exclusion_under_universe_expansion(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_archetype_matrix()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
