#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_original_idea_random_topology_v12 import (
    ACTIVE_SIZES,
    REPLICATES,
    _evaluate as evaluate_v12,
)
from benchmarks.run_eog_original_idea_random_relational_v13 import (
    TARGETS,
    _atomic_features,
    _minimum_design,
    _normalized_partition,
    _target_values,
)


PROTOCOL = ROOT / "validation/eog_original_idea_random_relational_v14/protocol_v14.json"


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


def _canonical_actions(features):
    by_partition = {}
    family_by_id = {}
    for feature_id, spec in sorted(features.items()):
        partition = _normalized_partition(spec["values"])
        incumbent = by_partition.get(partition)
        if incumbent is None or feature_id < incumbent:
            by_partition[partition] = feature_id
        family_by_id[feature_id] = spec["family"]

    action_partitions = {
        feature_id: partition
        for partition, feature_id in by_partition.items()
    }
    return action_partitions, family_by_id


def _target_adaptive_solver(target_partition, action_partitions):
    n_worlds = len(target_partition)
    if n_worlds != 12:
        raise RuntimeError("v14 requires exactly 12 worlds")
    full_mask = (1 << n_worlds) - 1
    action_ids = tuple(sorted(action_partitions))

    def members(mask):
        return tuple(i for i in range(n_worlds) if mask & (1 << i))

    @lru_cache(maxsize=None)
    def identified(mask):
        classes = {
            target_partition[i]
            for i in range(n_worlds)
            if mask & (1 << i)
        }
        return len(classes) <= 1

    @lru_cache(maxsize=None)
    def action_children(mask, action_id):
        groups = defaultdict(int)
        partition = action_partitions[action_id]
        for i in range(n_worlds):
            if mask & (1 << i):
                groups[partition[i]] |= 1 << i
        return tuple(
            child_mask
            for _, child_mask in sorted(groups.items(), key=lambda item: item[0])
        )

    @lru_cache(maxsize=None)
    def solve(mask):
        if identified(mask):
            return (True, 0, None, ())
        best_depth = None
        best_actions = []
        for action_id in action_ids:
            children = action_children(mask, action_id)
            if len(children) <= 1:
                continue
            child_depths = []
            valid = True
            for child in children:
                ok, depth, _, _ = solve(child)
                if not ok or depth is None:
                    valid = False
                    break
                child_depths.append(depth)
            if not valid:
                continue
            depth = 1 + max(child_depths)
            if best_depth is None or depth < best_depth:
                best_depth = depth
                best_actions = [action_id]
            elif depth == best_depth:
                best_actions.append(action_id)

        if best_depth is None:
            return (False, None, None, ())
        optimal = tuple(sorted(best_actions))
        return (True, best_depth, optimal[0], optimal)

    def child_for_truth(mask, action_id, truth_index):
        partition = action_partitions[action_id]
        truth_value = partition[truth_index]
        child = 0
        for i in range(n_worlds):
            if mask & (1 << i) and partition[i] == truth_value:
                child |= 1 << i
        return child

    def realized_path(truth_index):
        mask = full_mask
        path = []
        while not identified(mask):
            ok, depth, action_id, optimal = solve(mask)
            if not ok or depth is None or action_id is None:
                raise RuntimeError("adaptive policy unresolved on realized path")
            child = child_for_truth(mask, action_id, truth_index)
            if child == mask:
                raise RuntimeError("canonical adaptive action failed to contract state")
            path.append(
                {
                    "action_id": action_id,
                    "before_world_count": len(members(mask)),
                    "after_world_count": len(members(child)),
                    "remaining_worst_case_depth_before": depth,
                    "optimal_action_ids": list(optimal),
                }
            )
            mask = child
        return tuple(path), mask

    ok, worst_depth, first_action, optimal_first = solve(full_mask)
    if not ok or worst_depth is None:
        return {
            "resolvable": False,
            "worst_case_depth": None,
            "canonical_first_action": None,
            "optimal_first_actions": (),
            "mean_realized_depth": None,
            "realized_depth_distribution": {},
            "branching_second_action_count": 0,
            "branching_second_actions": (),
            "terminal_multiple_world_truth_count": None,
            "terminal_world_count_mean": None,
        }

    realized_depths = []
    terminal_counts = []
    for truth_index in range(n_worlds):
        path, terminal_mask = realized_path(truth_index)
        realized_depths.append(len(path))
        terminal_counts.append(len(members(terminal_mask)))

    second_actions = set()
    if first_action is not None:
        for child in action_children(full_mask, first_action):
            if identified(child):
                continue
            ok_child, _, second, _ = solve(child)
            if ok_child and second is not None:
                second_actions.add(second)

    return {
        "resolvable": True,
        "worst_case_depth": int(worst_depth),
        "canonical_first_action": first_action,
        "optimal_first_actions": tuple(optimal_first),
        "mean_realized_depth": float(np.mean(realized_depths)),
        "realized_depth_distribution": {
            str(key): int(value)
            for key, value in sorted(Counter(realized_depths).items())
        },
        "branching_second_action_count": len(second_actions),
        "branching_second_actions": tuple(sorted(second_actions)),
        "terminal_multiple_world_truth_count": sum(
            count > 1 for count in terminal_counts
        ),
        "terminal_world_count_mean": float(np.mean(terminal_counts)),
    }


def _evaluate_row(active_n, replicate):
    v12 = evaluate_v12(active_n, replicate)
    features = _atomic_features(v12)
    action_partitions, family_by_id = _canonical_actions(features)

    fixed_cache = {}
    targets = {}
    for target in TARGETS:
        target_values = _target_values(v12, target)
        target_partition = _normalized_partition(target_values)
        fixed = _minimum_design(
            v12,
            target,
            features,
            fixed_cache,
        )
        adaptive = _target_adaptive_solver(
            target_partition,
            action_partitions,
        )
        if not adaptive["resolvable"]:
            fixed_min = fixed["minimum_size"]
            if fixed_min is not None:
                raise RuntimeError(
                    "adaptive planner unresolved despite sufficient fixed panel"
                )

        first = adaptive["canonical_first_action"]
        targets[target] = {
            "target_class_count": len(set(target_partition)),
            "fixed_minimum_size": fixed["minimum_size"],
            "adaptive_resolvable": adaptive["resolvable"],
            "adaptive_worst_case_depth": adaptive["worst_case_depth"],
            "fixed_minus_adaptive_worst_case": (
                None
                if fixed["minimum_size"] is None
                or adaptive["worst_case_depth"] is None
                else int(fixed["minimum_size"])
                - int(adaptive["worst_case_depth"])
            ),
            "canonical_first_action": first,
            "canonical_first_family": (
                None if first is None else family_by_id[first]
            ),
            "optimal_first_actions": list(adaptive["optimal_first_actions"]),
            "mean_realized_depth": adaptive["mean_realized_depth"],
            "fixed_minus_mean_realized_depth": (
                None
                if fixed["minimum_size"] is None
                or adaptive["mean_realized_depth"] is None
                else float(fixed["minimum_size"])
                - float(adaptive["mean_realized_depth"])
            ),
            "realized_depth_distribution": adaptive[
                "realized_depth_distribution"
            ],
            "branching_second_action_count": adaptive[
                "branching_second_action_count"
            ],
            "branching_second_actions": list(
                adaptive["branching_second_actions"]
            ),
            "terminal_multiple_world_truth_count": adaptive[
                "terminal_multiple_world_truth_count"
            ],
            "terminal_world_count_mean": adaptive[
                "terminal_world_count_mean"
            ],
        }

    full_depth = targets["full_topology_identity"]["adaptive_worst_case_depth"]
    for target in (
        "pairwise_relation",
        "first_passage",
        "intervention",
        "critical_node_count",
    ):
        depth = targets[target]["adaptive_worst_case_depth"]
        if depth is None or full_depth is None or depth > full_depth:
            raise RuntimeError(
                "target adaptive depth exceeded full topology adaptive depth"
            )

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "canonical_action_count": len(action_partitions),
        "targets": targets,
    }


def _dist(values):
    return {
        str(key): int(value)
        for key, value in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_adaptive_relational_implementation_and_scoring"
    ):
        raise RuntimeError("v14 protocol is not frozen")

    rows = [
        _evaluate_row(active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    if len(rows) != 144:
        raise RuntimeError("expected 144 frozen v12 rows")

    violation_a1 = 0
    violation_a4 = 0
    unresolved_topology = 0
    strict_worst_saving_rows = 0
    target_realized_saving_rows = Counter()
    narrow_vs_topology_saving_rows = 0
    branching_rows = 0
    first_actions = set()

    for row in rows:
        full_depth = row["targets"]["full_topology_identity"][
            "adaptive_worst_case_depth"
        ]
        if full_depth is None:
            unresolved_topology += 1

        row_branching = False
        for target in TARGETS:
            spec = row["targets"][target]
            fixed = spec["fixed_minimum_size"]
            adaptive = spec["adaptive_worst_case_depth"]
            if fixed is not None and adaptive is not None:
                if adaptive > fixed:
                    violation_a1 += 1
                if adaptive < fixed:
                    strict_worst_saving_rows += 1
            if (
                target
                in ("pairwise_relation", "first_passage", "intervention")
                and spec["fixed_minus_mean_realized_depth"] is not None
                and spec["fixed_minus_mean_realized_depth"] > 1e-15
            ):
                target_realized_saving_rows[target] += 1
            if spec["branching_second_action_count"] >= 2:
                row_branching = True
            if spec["canonical_first_action"] is not None:
                first_actions.add(spec["canonical_first_action"])

        if row_branching:
            branching_rows += 1

        for target in (
            "pairwise_relation",
            "first_passage",
            "intervention",
            "critical_node_count",
        ):
            depth = row["targets"][target]["adaptive_worst_case_depth"]
            if depth is None or full_depth is None or depth > full_depth:
                violation_a4 += 1

        intervention = row["targets"]["intervention"]["adaptive_worst_case_depth"]
        critical = row["targets"]["critical_node_count"]["adaptive_worst_case_depth"]
        if full_depth is not None and (
            (intervention is not None and intervention < full_depth)
            or (critical is not None and critical < full_depth)
        ):
            narrow_vs_topology_saving_rows += 1

    verdicts = {
        "A1_adaptive_worst_case_never_exceeds_fixed_minimum": (
            "SUPPORTED" if violation_a1 == 0 else "REFUTED"
        ),
        "A2_strict_adaptive_worst_case_saving_exists": (
            "SUPPORTED" if strict_worst_saving_rows > 0 else "REFUTED"
        ),
        "A3_adaptive_realized_paths_save_measurements": (
            "SUPPORTED"
            if all(
                target_realized_saving_rows[target] > 0
                for target in (
                    "pairwise_relation",
                    "first_passage",
                    "intervention",
                )
            )
            else "REFUTED"
        ),
        "A4_target_adaptive_depth_never_exceeds_full_topology_depth": (
            "SUPPORTED" if violation_a4 == 0 else "REFUTED"
        ),
        "A5_narrow_target_adaptive_saving_vs_topology_exists": (
            "SUPPORTED" if narrow_vs_topology_saving_rows > 0 else "REFUTED"
        ),
        "A6_outcome_dependent_replanning_exists": (
            "SUPPORTED" if branching_rows > 0 else "REFUTED"
        ),
        "A7_no_universal_first_relational_measurement": (
            "SUPPORTED" if len(first_actions) > 1 else "REFUTED"
        ),
        "A8_full_topology_remains_exactly_adaptively_resolvable": (
            "SUPPORTED" if unresolved_topology == 0 else "REFUTED"
        ),
    }

    by_target = {}
    for target in TARGETS:
        specs = [row["targets"][target] for row in rows]
        by_target[target] = {
            "fixed_minimum_distribution": _dist(
                spec["fixed_minimum_size"] for spec in specs
            ),
            "adaptive_worst_case_distribution": _dist(
                spec["adaptive_worst_case_depth"] for spec in specs
            ),
            "fixed_minus_adaptive_distribution": _dist(
                spec["fixed_minus_adaptive_worst_case"] for spec in specs
            ),
            "mean_fixed_minimum": _mean(
                spec["fixed_minimum_size"] for spec in specs
            ),
            "mean_adaptive_worst_case": _mean(
                spec["adaptive_worst_case_depth"] for spec in specs
            ),
            "mean_canonical_policy_realized_depth": _mean(
                spec["mean_realized_depth"] for spec in specs
            ),
            "strict_worst_case_saving_rows": sum(
                (spec["fixed_minus_adaptive_worst_case"] or 0) > 0
                for spec in specs
            ),
            "strict_mean_realized_saving_rows": sum(
                spec["fixed_minus_mean_realized_depth"] is not None
                and spec["fixed_minus_mean_realized_depth"] > 1e-15
                for spec in specs
            ),
            "branching_policy_rows": sum(
                spec["branching_second_action_count"] >= 2
                for spec in specs
            ),
            "rows_terminal_with_multiple_worlds_for_some_truth": sum(
                (spec["terminal_multiple_world_truth_count"] or 0) > 0
                for spec in specs
            ),
            "canonical_first_action_count_distribution": dict(
                sorted(
                    Counter(
                        spec["canonical_first_action"]
                        for spec in specs
                        if spec["canonical_first_action"] is not None
                    ).items()
                )
            ),
            "canonical_first_family_distribution": dict(
                sorted(
                    Counter(
                        spec["canonical_first_family"]
                        for spec in specs
                        if spec["canonical_first_family"] is not None
                    ).items()
                )
            ),
        }

    by_size = {}
    for active_n in ACTIVE_SIZES:
        subset = [row for row in rows if row["active_node_count"] == active_n]
        by_size[str(active_n)] = {
            target: {
                "mean_fixed_minimum": _mean(
                    row["targets"][target]["fixed_minimum_size"]
                    for row in subset
                ),
                "mean_adaptive_worst_case": _mean(
                    row["targets"][target]["adaptive_worst_case_depth"]
                    for row in subset
                ),
                "mean_realized_depth": _mean(
                    row["targets"][target]["mean_realized_depth"]
                    for row in subset
                ),
            }
            for target in TARGETS
        }

    result = {
        "schema": "eog.original_idea_random_relational_adaptive.result.v14",
        "row_count": len(rows),
        "predeclared_verdicts": verdicts,
        "A1_violation_count": violation_a1,
        "A2_strict_worst_case_saving_row_target_count": strict_worst_saving_rows,
        "A3_realized_saving_rows": dict(sorted(target_realized_saving_rows.items())),
        "A4_violation_count": violation_a4,
        "A5_narrow_target_saving_row_count": narrow_vs_topology_saving_rows,
        "A6_branching_policy_row_count": branching_rows,
        "A7_distinct_canonical_first_action_count": len(first_actions),
        "A7_distinct_canonical_first_actions": sorted(first_actions),
        "A8_unresolved_topology_row_count": unresolved_topology,
        "by_target": by_target,
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
                "A2_strict_worst_case_saving_row_target_count": result[
                    "A2_strict_worst_case_saving_row_target_count"
                ],
                "A3_realized_saving_rows": result["A3_realized_saving_rows"],
                "A5_narrow_target_saving_row_count": result[
                    "A5_narrow_target_saving_row_count"
                ],
                "A6_branching_policy_row_count": result[
                    "A6_branching_policy_row_count"
                ],
                "A7_distinct_canonical_first_action_count": result[
                    "A7_distinct_canonical_first_action_count"
                ],
                "by_target": result["by_target"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
