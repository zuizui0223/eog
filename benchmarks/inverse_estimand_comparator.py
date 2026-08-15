#!/usr/bin/env python3
"""Known-truth comparator for EOG's inverse, set-valued estimand.

This benchmark does **not** claim superiority over full dynamic occupancy, circuit,
least-cost, or mechanistic range models.  It asks a narrower prerequisite question:
when endpoint observations are identical, does the EOG inverse layer retain temporal
and axis-specific constraint information that deliberately simpler summaries discard?

The benchmark compares four representations of one frozen finite temporal-world
universe:

1. endpoint-only positive-occurrence identity (time discarded);
2. final-horizon temporal compatibility (earlier timing discarded);
3. one scalar sum of geographic/environmental/barrier relaxation (axis identity
   discarded);
4. EOG's time-constrained compatible-world set plus Pareto relaxation frontier.

If EOG cannot distinguish the known-truth cases below, there is no reason to proceed
to heavier empirical or external-method comparator work.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalRelaxationDeclaration,
    TemporalWorld,
    build_dynamic_transition_operator,
    minimum_temporal_relaxation_frontier,
    reconstruct_temporal_worlds,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    declared = [
        DynamicReachabilityEdge(
            source=index[source],
            target=index[target],
            geographic_support=float(support),
        )
        for source, target, support in edges
    ]
    return build_dynamic_transition_operator(node_ids, declared, loss_support=1.0)


def _empty(node_ids):
    return build_dynamic_transition_operator(node_ids, (), loss_support=1.0)


def _worlds_and_relaxations():
    nodes = ("A", "D", "B", "C")
    ab = _operator(nodes, (("A", "B", 1.0),))
    bc = _operator(nodes, (("B", "C", 1.0),))
    ad = _operator(nodes, (("A", "D", 1.0),))
    db = _operator(nodes, (("D", "B", 1.0),))
    empty = _empty(nodes)

    slow = TemporalWorld(
        "slow_baseline",
        ("t0", "t1", "t2", "t3"),
        (ad, db, bc),
        ("A",),
    )
    # The three fast worlds deliberately share the same route geometry here.  Their
    # ecological interpretations differ only through predeclared relaxation metadata;
    # this isolates the information loss caused by scalarizing those axes.
    fast_geo = TemporalWorld(
        "fast_geo",
        ("t0", "t1", "t2", "t3"),
        (ab, bc, empty),
        ("A",),
    )
    fast_env = TemporalWorld(
        "fast_env",
        ("t0", "t1", "t2", "t3"),
        (ab, bc, empty),
        ("A",),
    )
    fast_barrier = TemporalWorld(
        "fast_barrier",
        ("t0", "t1", "t2", "t3"),
        (ab, bc, empty),
        ("A",),
    )
    dominated = TemporalWorld(
        "dominated",
        ("t0", "t1", "t2", "t3"),
        (ab, bc, empty),
        ("A",),
    )
    worlds = (slow, fast_geo, fast_env, fast_barrier, dominated)
    declarations = (
        TemporalRelaxationDeclaration("slow_baseline"),
        TemporalRelaxationDeclaration("fast_geo", geographic_relaxation=1.0),
        TemporalRelaxationDeclaration("fast_env", environmental_relaxation=1.0),
        TemporalRelaxationDeclaration("fast_barrier", barrier_relaxation=1.0),
        TemporalRelaxationDeclaration(
            "dominated",
            geographic_relaxation=1.0,
            environmental_relaxation=1.0,
            barrier_relaxation=1.0,
        ),
    )
    return worlds, declarations


def _axis_signature(point):
    return (
        point.geographic_relaxation,
        point.environmental_relaxation,
        point.barrier_relaxation,
    )


def _endpoint_only_signature(observations):
    """Deliberately discard time and return only observed endpoint identities."""

    return tuple(sorted({node_id for node_id, _ in observations}))


def _scalar_relaxation_summary(frontier):
    """Deliberately collapse the three ecological axes into an unweighted scalar."""

    rows = [
        (
            point.world_id,
            point.geographic_relaxation
            + point.environmental_relaxation
            + point.barrier_relaxation,
        )
        for point in frontier.points
    ]
    if not rows:
        return {"minimum_score": None, "tied_world_ids": [], "tie_count": 0}
    minimum = min(score for _, score in rows)
    tied = sorted(world_id for world_id, score in rows if score == minimum)
    return {
        "minimum_score": minimum,
        "tied_world_ids": tied,
        "tie_count": len(tied),
    }


def run_inverse_estimand_comparator():
    worlds, declarations = _worlds_and_relaxations()

    late_observations = (("C", "t3"),)
    early_observations = (("C", "t2"),)
    late = reconstruct_temporal_worlds(worlds, late_observations)
    early = reconstruct_temporal_worlds(worlds, early_observations)
    late_frontier = minimum_temporal_relaxation_frontier(late, declarations)
    early_frontier = minimum_temporal_relaxation_frontier(early, declarations)

    late_endpoint_signature = _endpoint_only_signature(late_observations)
    early_endpoint_signature = _endpoint_only_signature(early_observations)
    early_scalar = _scalar_relaxation_summary(early_frontier)
    early_axis_signatures = sorted(_axis_signature(point) for point in early_frontier.points)

    expected_axis_signatures = sorted(
        (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        )
    )

    return {
        "schema_version": 1,
        "claim_boundary": (
            "known-truth estimand-separation benchmark; not external-method superiority"
        ),
        "endpoint_only_baseline": {
            "late_signature": list(late_endpoint_signature),
            "early_signature": list(early_endpoint_signature),
            "cannot_distinguish_t2_from_t3": (
                late_endpoint_signature == early_endpoint_signature
            ),
        },
        "final_horizon_reachability_baseline": {
            "compatible_world_ids_at_C_t3": list(late.compatible_world_ids),
            "retains_slow_and_fast_worlds": (
                set(late.compatible_world_ids)
                == {world.world_id for world in worlds}
            ),
        },
        "scalar_relaxation_baseline": early_scalar,
        "eog_inverse": {
            "compatible_world_ids_at_C_t2": list(early.compatible_world_ids),
            "slow_world_eliminated_by_timing": "slow_baseline" not in early.compatible_world_ids,
            "identifiable": early.identifiable,
            "frontier_world_ids": [point.world_id for point in early_frontier.points],
            "frontier_axis_signatures": [list(row) for row in early_axis_signatures],
            "preserves_three_axis_specific_rescues": (
                early_axis_signatures == expected_axis_signatures
            ),
            "dominated_world_removed": (
                "dominated" not in {point.world_id for point in early_frontier.points}
            ),
            "keeps_history_set_valued": (
                len(early_frontier.points) == 3 and not early.identifiable
            ),
        },
        "separation_checks": {
            "timing_adds_information_beyond_endpoint_identity": (
                late_endpoint_signature == early_endpoint_signature
                and "slow_baseline" in late.compatible_world_ids
                and "slow_baseline" not in early.compatible_world_ids
            ),
            "axis_identity_is_lost_by_scalarization": (
                early_scalar["minimum_score"] == 1.0
                and early_scalar["tie_count"] == 3
                and early_axis_signatures == expected_axis_signatures
            ),
            "single_history_would_require_extra_tie_break": (
                early_scalar["tie_count"] > 1 and not early.identifiable
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_inverse_estimand_comparator()
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
