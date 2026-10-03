#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
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
from benchmarks.run_eog_original_idea_directed_temporal_flow_v5 import (
    _candidate_worlds,
    _graphs,
    _outlet_corner,
    _truth_source,
    _truth_world_id,
)


PROTOCOL = ROOT / "validation/eog_original_idea_target_aware_evidence_planning_v7/protocol_v7.json"
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


def _target_key(world):
    return tuple(sorted(world["reachable"]))


def _action_outcome(world, action):
    if action == "S_source":
        return _node_id(world["source"])
    if action == "B_barrier":
        return f"{float(world['barrier_density']):.2f}"
    if action == "R_analyst":
        return str(world["rule"])
    raise ValueError(action)


def _build_planner(worlds):
    by_id = {world["world_id"]: world for world in worlds}
    if len(by_id) != len(worlds):
        raise RuntimeError("candidate world IDs are not unique")

    all_ids = tuple(sorted(by_id))

    def identified(state_ids, objective):
        if objective == "target":
            return len({_target_key(by_id[world_id]) for world_id in state_ids}) == 1
        if objective == "world":
            return len(state_ids) == 1
        raise ValueError(objective)

    def partitions(state_ids, action):
        groups = defaultdict(list)
        for world_id in state_ids:
            groups[_action_outcome(by_id[world_id], action)].append(world_id)
        return tuple(
            (outcome, tuple(sorted(ids)))
            for outcome, ids in sorted(groups.items(), key=lambda item: str(item[0]))
        )

    @lru_cache(maxsize=None)
    def solve(state_ids, remaining_actions, objective):
        state_ids = tuple(state_ids)
        remaining_actions = tuple(remaining_actions)
        if identified(state_ids, objective):
            return (0, None)
        if not remaining_actions:
            return (math.inf, None)

        best_depth = math.inf
        best_action = None
        for action in remaining_actions:
            rest = tuple(a for a in remaining_actions if a != action)
            child_depths = []
            for _, child_ids in partitions(state_ids, action):
                depth, _ = solve(child_ids, rest, objective)
                child_depths.append(depth)
            depth = 1 + max(child_depths)
            if depth < best_depth:
                best_depth = depth
                best_action = action
            elif depth == best_depth and best_action is not None:
                if ACTIONS.index(action) < ACTIONS.index(best_action):
                    best_action = action
        return (best_depth, best_action)

    def worst_case_target_class_count_after_action(state_ids, action):
        worst = 0
        for _, child_ids in partitions(tuple(state_ids), action):
            n = len({_target_key(by_id[world_id]) for world_id in child_ids})
            worst = max(worst, n)
        return worst

    def truth_path(initial_ids, truth_id, objective):
        state_ids = tuple(sorted(initial_ids))
        remaining = tuple(ACTIONS)
        sequence = []
        while not identified(state_ids, objective):
            depth, action = solve(state_ids, remaining, objective)
            if not math.isfinite(depth) or action is None:
                raise RuntimeError(f"{objective} planner failed to identify target")
            truth_outcome = _action_outcome(by_id[truth_id], action)
            child_map = dict(partitions(state_ids, action))
            if truth_outcome not in child_map:
                raise RuntimeError("truth outcome missing from action partition")
            state_ids = child_map[truth_outcome]
            sequence.append(
                {
                    "action": action,
                    "truth_outcome": truth_outcome,
                    "remaining_world_count": len(state_ids),
                    "remaining_source_count": len(
                        {by_id[world_id]["source"] for world_id in state_ids}
                    ),
                    "remaining_target_class_count": len(
                        {_target_key(by_id[world_id]) for world_id in state_ids}
                    ),
                }
            )
            remaining = tuple(a for a in remaining if a != action)

        return {
            "depth": len(sequence),
            "sequence": sequence,
            "final_world_count": len(state_ids),
            "final_source_count": len(
                {by_id[world_id]["source"] for world_id in state_ids}
            ),
            "final_target_class_count": len(
                {_target_key(by_id[world_id]) for world_id in state_ids}
            ),
        }

    return {
        "by_id": by_id,
        "all_ids": all_ids,
        "identified": identified,
        "partitions": partitions,
        "solve": solve,
        "worst_case_target_class_count_after_action": (
            worst_case_target_class_count_after_action
        ),
        "truth_path": truth_path,
    }


def _evaluate_row(replicate, autocorr, neighbourhood, barrier_density):
    base = _generate_base(replicate, autocorr, neighbourhood)
    outlet = _outlet_corner(replicate, autocorr, neighbourhood)
    truth_source = _truth_source(base, outlet)
    _, truth_graph = _graphs(
        base,
        barrier_density,
        "relative_edge_q70",
        outlet,
    )
    truth_depth = _bfs_distances(truth_graph, truth_source)
    truth_reachable = frozenset(truth_depth)
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
    if not row["eligible"]:
        return {
            **row,
            "baseline_world_count": None,
            "baseline_target_class_count": None,
        }

    worlds = _candidate_worlds(base, outlet, "directed")
    truth_id = _truth_world_id(truth_source, barrier_density)
    positive_set = frozenset(pool)
    survivors = tuple(
        world
        for world in worlds
        if positive_set.issubset(world["reachable"])
    )
    survivor_ids = tuple(sorted(world["world_id"] for world in survivors))
    if truth_id not in set(survivor_ids):
        raise RuntimeError("truth world missing from full-positive survivor fiber")

    planner = _build_planner(survivors)
    target_depth, target_first = planner["solve"](
        survivor_ids,
        tuple(ACTIONS),
        "target",
    )
    world_depth, world_first = planner["solve"](
        survivor_ids,
        tuple(ACTIONS),
        "world",
    )
    if not math.isfinite(target_depth) or not math.isfinite(world_depth):
        raise RuntimeError("complete three-action library failed planning")

    if target_depth > world_depth:
        raise RuntimeError("target-optimal depth exceeded full-world depth")
    if target_depth > 3 or world_depth > 3:
        raise RuntimeError("adaptive depth exceeded three-action library")

    target_path = planner["truth_path"](
        survivor_ids,
        truth_id,
        "target",
    )
    world_path = planner["truth_path"](
        survivor_ids,
        truth_id,
        "world",
    )

    target_class_count = len({_target_key(world) for world in survivors})
    first_action_scores = {
        action: planner["worst_case_target_class_count_after_action"](
            survivor_ids,
            action,
        )
        for action in ACTIONS
    }

    first_actions_differ = (
        target_first is not None
        and world_first is not None
        and target_first != world_first
    )
    target_first_strictly_better_for_target = (
        first_actions_differ
        and first_action_scores[target_first] < first_action_scores[world_first]
    )

    return {
        **row,
        "baseline_world_count": len(survivors),
        "baseline_source_count": len({world["source"] for world in survivors}),
        "baseline_target_class_count": target_class_count,
        "target_already_identified": target_class_count == 1,
        "world_already_identified": len(survivors) == 1,
        "target_optimal_worst_case_depth": int(target_depth),
        "world_optimal_worst_case_depth": int(world_depth),
        "target_optimal_first_action": target_first,
        "world_optimal_first_action": world_first,
        "first_actions_differ": first_actions_differ,
        "target_first_strictly_better_for_target": (
            target_first_strictly_better_for_target
        ),
        "first_action_worst_case_target_class_counts": first_action_scores,
        "target_truth_path": target_path,
        "world_truth_path": world_path,
        "target_stops_with_multiple_worlds": (
            target_path["final_world_count"] > 1
        ),
        "target_stops_with_multiple_sources": (
            target_path["final_source_count"] > 1
        ),
        "target_stops_with_multiple_worlds_and_sources": (
            target_path["final_world_count"] > 1
            and target_path["final_source_count"] > 1
        ),
    }


def _dist(values):
    return {
        str(key): int(value)
        for key, value in sorted(Counter(values).items())
    }


def _mean(values):
    values = [float(value) for value in values]
    return None if not values else float(np.mean(values))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_adaptive_planner_implementation_and_scoring"
    ):
        raise RuntimeError("v7 protocol is not frozen")

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
        raise RuntimeError("no v7 eligible rows")

    depth_violations = sum(
        row["target_optimal_worst_case_depth"]
        > row["world_optimal_worst_case_depth"]
        for row in eligible
    )
    strict_saving_rows = sum(
        row["target_optimal_worst_case_depth"]
        < row["world_optimal_worst_case_depth"]
        for row in eligible
    )
    unresolved_both = [
        row
        for row in eligible
        if not row["target_already_identified"]
        and not row["world_already_identified"]
    ]
    differing_first = sum(row["first_actions_differ"] for row in unresolved_both)
    target_superior_first = sum(
        row["target_first_strictly_better_for_target"]
        for row in unresolved_both
    )
    target_first_counts = Counter(
        row["target_optimal_first_action"]
        for row in eligible
        if row["target_optimal_first_action"] is not None
    )
    unresolved_target_failures = sum(
        row["target_truth_path"]["final_target_class_count"] != 1
        for row in eligible
    )
    stops_multi = sum(
        row["target_stops_with_multiple_worlds_and_sources"]
        for row in eligible
    )

    verdicts = {
        "P1_target_planning_depth_never_exceeds_world_planning_depth": (
            "SUPPORTED" if depth_violations == 0 else "REFUTED"
        ),
        "P2_strict_adaptive_target_saving_exists": (
            "SUPPORTED" if strict_saving_rows > 0 else "REFUTED"
        ),
        "P3_target_and_world_planners_choose_different_first_actions": (
            "SUPPORTED" if differing_first > 0 else "REFUTED"
        ),
        "P4_target_planner_first_action_is_target_superior_somewhere": (
            "SUPPORTED" if target_superior_first > 0 else "REFUTED"
        ),
        "P5_target_planning_is_not_one_fixed_measurement_order": (
            "SUPPORTED" if len(target_first_counts) >= 2 else "REFUTED"
        ),
        "P6_complete_three_action_library_resolves_every_target": (
            "SUPPORTED" if unresolved_target_failures == 0 else "REFUTED"
        ),
        "P7_target_planner_can_stop_with_history_unresolved": (
            "SUPPORTED" if stops_multi > 0 else "REFUTED"
        ),
    }

    target_depths = [
        row["target_optimal_worst_case_depth"] for row in eligible
    ]
    world_depths = [
        row["world_optimal_worst_case_depth"] for row in eligible
    ]
    target_truth_depths = [
        row["target_truth_path"]["depth"] for row in eligible
    ]
    world_truth_depths = [
        row["world_truth_path"]["depth"] for row in eligible
    ]

    result = {
        "schema": "eog.original_idea_target_aware_evidence_planning.result.v7",
        "row_count": len(rows),
        "eligible_row_count": len(eligible),
        "non_estimable_row_count": len(rows) - len(eligible),
        "predeclared_verdicts": verdicts,
        "adaptive_depths": {
            "target_worst_case_distribution": _dist(target_depths),
            "world_worst_case_distribution": _dist(world_depths),
            "target_truth_path_distribution": _dist(target_truth_depths),
            "world_truth_path_distribution": _dist(world_truth_depths),
            "mean_target_worst_case_depth": _mean(target_depths),
            "mean_world_worst_case_depth": _mean(world_depths),
            "strict_target_saving_rows": strict_saving_rows,
            "target_gt_world_violation_count": depth_violations,
        },
        "first_action": {
            "target_optimal_counts": dict(sorted(target_first_counts.items())),
            "rows_with_different_target_vs_world_first_action": differing_first,
            "rows_where_target_first_has_strictly_better_target_split": (
                target_superior_first
            ),
        },
        "target_stopping": {
            "rows_stopping_with_multiple_worlds": sum(
                row["target_stops_with_multiple_worlds"]
                for row in eligible
            ),
            "rows_stopping_with_multiple_sources": sum(
                row["target_stops_with_multiple_sources"]
                for row in eligible
            ),
            "rows_stopping_with_multiple_worlds_and_sources": stops_multi,
            "target_resolution_failures": unresolved_target_failures,
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
                "eligible_row_count": result["eligible_row_count"],
                "predeclared_verdicts": result["predeclared_verdicts"],
                "adaptive_depths": result["adaptive_depths"],
                "first_action": result["first_action"],
                "target_stopping": result["target_stopping"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
