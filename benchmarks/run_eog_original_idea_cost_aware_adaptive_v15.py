#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
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
    _normalized_partition,
    _target_values,
)

PROTOCOL = ROOT / "validation/eog_original_idea_cost_aware_adaptive_v15/protocol_v15.json"

COST_WORLDS = {
    "equal": {"REL": 1, "FP": 1, "KO": 1},
    "KO_expensive": {"REL": 1, "FP": 1, "KO": 3},
    "FP_expensive": {"REL": 1, "FP": 3, "KO": 1},
    "REL_expensive": {"REL": 3, "FP": 1, "KO": 1},
}


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


def _family(action_id):
    if action_id.startswith("REL:"):
        return "REL"
    if action_id.startswith("FP:"):
        return "FP"
    if action_id.startswith("KO:"):
        return "KO"
    raise ValueError(f"unknown action family: {action_id}")


def _action_partitions(features):
    return {
        feature_id: _normalized_partition(spec["values"])
        for feature_id, spec in sorted(features.items())
    }


def _cost_canonical_partitions(features, family_costs):
    """Collapse globally outcome-equivalent actions to the cheapest representative."""

    by_partition = {}
    for feature_id, spec in sorted(features.items()):
        partition = _normalized_partition(spec["values"])
        candidate = (
            int(family_costs[spec["family"]]),
            feature_id,
        )
        incumbent = by_partition.get(partition)
        if incumbent is None or candidate < incumbent:
            by_partition[partition] = candidate
    return {
        feature_id: partition
        for partition, (_, feature_id) in by_partition.items()
    }


def _target_discordant_pairs(target_partition):
    return tuple(
        (i, j)
        for i in range(len(target_partition))
        for j in range(i + 1, len(target_partition))
        if target_partition[i] != target_partition[j]
    )


def _coverage_masks(features, target_partition):
    pairs = _target_discordant_pairs(target_partition)
    full_mask = (1 << len(pairs)) - 1
    masks = {}
    for action_id, spec in sorted(features.items()):
        mask = 0
        for bit, (i, j) in enumerate(pairs):
            if spec["values"][i] != spec["values"][j]:
                mask |= 1 << bit
        if mask:
            masks[action_id] = mask
    return pairs, full_mask, masks


def _weighted_fixed_minimum(
    features,
    target_partition,
    family_costs,
):
    pairs, full_mask, masks = _coverage_masks(features, target_partition)
    if full_mask == 0:
        return {
            "resolvable": True,
            "minimum_cost": 0,
            "minimum_measurement_count": 0,
            "canonical_action_ids": (),
        }

    union = 0
    for mask in masks.values():
        union |= mask
    if union != full_mask:
        return {
            "resolvable": False,
            "minimum_cost": None,
            "minimum_measurement_count": None,
            "canonical_action_ids": None,
        }

    # For identical coverage masks retain only the cheapest representative; ties are
    # lexicographic.  A more expensive identical mask can never improve any fixed set.
    by_mask = {}
    for action_id, mask in sorted(masks.items()):
        cost = int(family_costs[_family(action_id)])
        incumbent = by_mask.get(mask)
        candidate = (cost, action_id)
        if incumbent is None or candidate < incumbent:
            by_mask[mask] = candidate

    rows = tuple(
        sorted(
            (
                {
                    "action_id": action_id,
                    "mask": int(mask),
                    "cost": int(cost),
                }
                for mask, (cost, action_id) in by_mask.items()
            ),
            key=lambda row: row["action_id"],
        )
    )

    bit_to_rows = {}
    bit = 0
    while (1 << bit) <= full_mask:
        if full_mask & (1 << bit):
            indices = tuple(
                i for i, row in enumerate(rows)
                if row["mask"] & (1 << bit)
            )
            if not indices:
                raise RuntimeError("uncovered target-discordant pair")
            bit_to_rows[bit] = indices
        bit += 1

    @lru_cache(maxsize=None)
    def solve(covered):
        if covered == full_mask:
            return (0, 0, ())

        uncovered_bits = [
            bit
            for bit in bit_to_rows
            if not (covered & (1 << bit))
        ]
        chosen_bit = min(
            uncovered_bits,
            key=lambda b: (len(bit_to_rows[b]), b),
        )

        best = None
        for i in bit_to_rows[chosen_bit]:
            row = rows[i]
            updated = covered | row["mask"]
            if updated == covered:
                continue
            tail = solve(updated)
            ids = tuple(sorted((row["action_id"], *tail[2])))
            candidate = (
                row["cost"] + tail[0],
                1 + tail[1],
                ids,
            )
            if best is None or candidate < best:
                best = candidate

        if best is None:
            raise RuntimeError("weighted fixed target cover unexpectedly infeasible")
        return best

    cost, count, ids = solve(0)
    return {
        "resolvable": True,
        "minimum_cost": int(cost),
        "minimum_measurement_count": int(count),
        "canonical_action_ids": tuple(ids),
    }


def _weighted_adaptive_solver(
    target_partition,
    action_partitions,
    family_costs,
):
    n_worlds = len(target_partition)
    if n_worlds != 12:
        raise RuntimeError("v15 requires exactly 12 worlds")
    full_mask = (1 << n_worlds) - 1
    action_ids = tuple(sorted(action_partitions))

    target_masks_by_class = defaultdict(int)
    for i, target_class in enumerate(target_partition):
        target_masks_by_class[target_class] |= 1 << i
    target_masks = tuple(target_masks_by_class.values())

    action_outcome_masks = {}
    for action_id in action_ids:
        groups = defaultdict(int)
        for i, outcome_class in enumerate(action_partitions[action_id]):
            groups[outcome_class] |= 1 << i
        action_outcome_masks[action_id] = tuple(groups.values())

    action_cost = {
        action_id: int(family_costs[_family(action_id)])
        for action_id in action_ids
    }

    def members(mask):
        return tuple(i for i in range(n_worlds) if mask & (1 << i))

    @lru_cache(maxsize=None)
    def identified(mask):
        return any((mask & ~target_mask) == 0 for target_mask in target_masks)

    @lru_cache(maxsize=None)
    def children(mask, action_id):
        return tuple(
            sorted(
                child
                for outcome_mask in action_outcome_masks[action_id]
                for child in (mask & outcome_mask,)
                if child
            )
        )

    @lru_cache(maxsize=None)
    def representatives(mask):
        # If two actions create the same state partition, the cheaper one dominates.
        # On equal cost use lexicographic action ID for deterministic replay.
        by_children = {}
        for action_id in action_ids:
            state_children = children(mask, action_id)
            if len(state_children) <= 1:
                continue
            candidate = (action_cost[action_id], action_id)
            incumbent = by_children.get(state_children)
            if incumbent is None or candidate < incumbent:
                by_children[state_children] = candidate
        return tuple(
            sorted(action_id for _, action_id in by_children.values())
        )

    @lru_cache(maxsize=None)
    def minimum_cost(mask):
        if identified(mask):
            return 0

        best = None
        for action_id in representatives(mask):
            child_costs = [minimum_cost(child) for child in children(mask, action_id)]
            if any(value is None for value in child_costs):
                continue
            candidate = action_cost[action_id] + max(child_costs)
            if best is None or candidate < best:
                best = candidate
        return best

    @lru_cache(maxsize=None)
    def optimal_actions(mask):
        optimum = minimum_cost(mask)
        if optimum is None or optimum == 0:
            return ()
        rows = []
        for action_id in representatives(mask):
            child_costs = [minimum_cost(child) for child in children(mask, action_id)]
            if any(value is None for value in child_costs):
                continue
            candidate = action_cost[action_id] + max(child_costs)
            if candidate == optimum:
                rows.append(action_id)
        return tuple(sorted(rows))

    def child_for_truth(mask, action_id, truth_index):
        truth_bit = 1 << truth_index
        for outcome_mask in action_outcome_masks[action_id]:
            if outcome_mask & truth_bit:
                return mask & outcome_mask
        raise RuntimeError("truth outcome missing")

    def realized_path(truth_index):
        mask = full_mask
        rows = []
        total_cost = 0
        while not identified(mask):
            optimum = minimum_cost(mask)
            actions = optimal_actions(mask)
            if optimum is None or not actions:
                raise RuntimeError("cost-aware adaptive policy unresolved")
            action_id = actions[0]
            child = child_for_truth(mask, action_id, truth_index)
            if child == mask:
                raise RuntimeError("chosen adaptive action failed to split state")
            cost = action_cost[action_id]
            total_cost += cost
            rows.append(
                {
                    "action_id": action_id,
                    "family": _family(action_id),
                    "cost": cost,
                    "before_world_count": len(members(mask)),
                    "after_world_count": len(members(child)),
                    "remaining_worst_case_cost_before": optimum,
                    "optimal_action_ids": list(actions),
                }
            )
            mask = child
        return tuple(rows), mask, total_cost

    worst_cost = minimum_cost(full_mask)
    if worst_cost is None:
        return {
            "resolvable": False,
            "worst_case_cost": None,
            "canonical_first_action": None,
            "canonical_first_family": None,
            "optimal_first_actions": (),
            "mean_realized_cost": None,
            "mean_realized_measurement_count": None,
            "branching_second_action_count": 0,
            "terminal_multiple_world_truth_count": None,
        }

    first_actions = optimal_actions(full_mask)
    first = first_actions[0] if first_actions else None

    realized_costs = []
    realized_counts = []
    terminal_counts = []
    for truth_index in range(n_worlds):
        path, terminal_mask, total_cost = realized_path(truth_index)
        realized_costs.append(total_cost)
        realized_counts.append(len(path))
        terminal_counts.append(len(members(terminal_mask)))

    second_actions = set()
    if first is not None:
        for child in children(full_mask, first):
            if identified(child):
                continue
            child_optimal = optimal_actions(child)
            if child_optimal:
                second_actions.add(child_optimal[0])

    return {
        "resolvable": True,
        "worst_case_cost": int(worst_cost),
        "canonical_first_action": first,
        "canonical_first_family": None if first is None else _family(first),
        "optimal_first_actions": tuple(first_actions),
        "mean_realized_cost": float(np.mean(realized_costs)),
        "mean_realized_measurement_count": float(np.mean(realized_counts)),
        "realized_cost_distribution": {
            str(k): int(v) for k, v in sorted(Counter(realized_costs).items())
        },
        "realized_measurement_count_distribution": {
            str(k): int(v) for k, v in sorted(Counter(realized_counts).items())
        },
        "branching_second_action_count": len(second_actions),
        "branching_second_actions": tuple(sorted(second_actions)),
        "terminal_multiple_world_truth_count": sum(
            value > 1 for value in terminal_counts
        ),
    }


def _evaluate_row(active_n, replicate):
    v12 = evaluate_v12(active_n, replicate)
    features = _atomic_features(v12)

    target_partitions = {
        target: _normalized_partition(_target_values(v12, target))
        for target in TARGETS
    }

    cost_worlds = {}
    for cost_name, family_costs in COST_WORLDS.items():
        target_rows = {}
        adaptive_cache = {}
        fixed_cache = {}
        cost_partitions = _cost_canonical_partitions(
            features,
            family_costs,
        )

        for target in TARGETS:
            partition = target_partitions[target]
            cache_key = (partition, tuple(sorted(family_costs.items())))

            if cache_key not in fixed_cache:
                fixed_cache[cache_key] = _weighted_fixed_minimum(
                    features,
                    partition,
                    family_costs,
                )
            fixed = fixed_cache[cache_key]

            if cache_key not in adaptive_cache:
                adaptive_cache[cache_key] = _weighted_adaptive_solver(
                    partition,
                    cost_partitions,
                    family_costs,
                )
            adaptive = adaptive_cache[cache_key]

            if fixed["resolvable"] != adaptive["resolvable"]:
                raise RuntimeError("fixed/adaptive resolvability mismatch")

            target_rows[target] = {
                "fixed_resolvable": fixed["resolvable"],
                "fixed_minimum_cost": fixed["minimum_cost"],
                "fixed_measurement_count": fixed["minimum_measurement_count"],
                "fixed_canonical_action_ids": (
                    None
                    if fixed["canonical_action_ids"] is None
                    else list(fixed["canonical_action_ids"])
                ),
                "adaptive_resolvable": adaptive["resolvable"],
                "adaptive_worst_case_cost": adaptive["worst_case_cost"],
                "fixed_minus_adaptive_worst_case_cost": (
                    None
                    if fixed["minimum_cost"] is None
                    or adaptive["worst_case_cost"] is None
                    else fixed["minimum_cost"] - adaptive["worst_case_cost"]
                ),
                "canonical_first_action": adaptive["canonical_first_action"],
                "canonical_first_family": adaptive["canonical_first_family"],
                "optimal_first_actions": list(adaptive["optimal_first_actions"]),
                "mean_realized_cost": adaptive["mean_realized_cost"],
                "mean_realized_measurement_count": adaptive[
                    "mean_realized_measurement_count"
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
            }

        cost_worlds[cost_name] = {
            "family_costs": dict(family_costs),
            "targets": target_rows,
        }

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "cost_worlds": cost_worlds,
    }


def _evaluate_row_from_args(args):
    return _evaluate_row(*args)


def _mean(values):
    vals = [float(v) for v in values]
    return None if not vals else float(np.mean(vals))


def _dist(values):
    return {
        str(k): int(v)
        for k, v in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_cost_aware_adaptive_implementation_and_scoring"
    ):
        raise RuntimeError("v15 protocol is not frozen")

    tasks = [
        (active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
    # Row evaluations are independent. executor.map preserves input order, so
    # parallel execution changes runtime only, not result ordering or fingerprint.
    with ProcessPoolExecutor(max_workers=4) as executor:
        rows = list(
            executor.map(
                _evaluate_row_from_args,
                tasks,
                chunksize=1,
            )
        )
    if len(rows) != 144:
        raise RuntimeError("expected 144 frozen rows")

    c1_violations = 0
    c5_violations = 0
    unresolved = 0
    strict_saving_by_cost = Counter()
    narrow_saving_by_cost = Counter()
    branching_by_cost = Counter()

    first_family_counts = {
        cost_name: Counter()
        for cost_name in COST_WORLDS
    }
    first_action_changes = 0

    for row in rows:
        equal_first = {
            target: row["cost_worlds"]["equal"]["targets"][target][
                "canonical_first_action"
            ]
            for target in TARGETS
        }

        for cost_name in COST_WORLDS:
            target_rows = row["cost_worlds"][cost_name]["targets"]
            full_cost = target_rows["full_topology_identity"][
                "adaptive_worst_case_cost"
            ]

            row_branching = False
            row_strict = False
            row_narrow = False

            for target in TARGETS:
                spec = target_rows[target]
                fixed = spec["fixed_minimum_cost"]
                adaptive = spec["adaptive_worst_case_cost"]
                if fixed is None or adaptive is None:
                    unresolved += 1
                    continue
                if adaptive > fixed:
                    c1_violations += 1
                if adaptive < fixed:
                    row_strict = True
                if spec["branching_second_action_count"] >= 2:
                    row_branching = True
                family = spec["canonical_first_family"]
                if family is not None:
                    first_family_counts[cost_name][family] += 1
                if (
                    cost_name != "equal"
                    and spec["canonical_first_action"]
                    != equal_first[target]
                ):
                    first_action_changes += 1

            for target in (
                "pairwise_relation",
                "first_passage",
                "intervention",
                "critical_node_count",
            ):
                value = target_rows[target]["adaptive_worst_case_cost"]
                if value is None or full_cost is None:
                    c5_violations += 1
                elif value > full_cost:
                    c5_violations += 1

            for target in ("intervention", "critical_node_count"):
                value = target_rows[target]["adaptive_worst_case_cost"]
                if (
                    value is not None
                    and full_cost is not None
                    and value < full_cost
                ):
                    row_narrow = True

            if row_strict:
                strict_saving_by_cost[cost_name] += 1
            if row_narrow:
                narrow_saving_by_cost[cost_name] += 1
            if row_branching:
                branching_by_cost[cost_name] += 1

    family_frequency_decrease = {}
    for family, expensive_world in (
        ("REL", "REL_expensive"),
        ("FP", "FP_expensive"),
        ("KO", "KO_expensive"),
    ):
        equal_count = first_family_counts["equal"][family]
        expensive_count = first_family_counts[expensive_world][family]
        family_frequency_decrease[family] = {
            "equal_count": equal_count,
            "expensive_count": expensive_count,
            "strict_decrease": expensive_count < equal_count,
        }

    verdicts = {
        "C1_adaptive_worst_case_cost_never_exceeds_fixed_cost": (
            "SUPPORTED" if c1_violations == 0 else "REFUTED"
        ),
        "C2_strict_adaptive_cost_saving_exists_in_every_cost_world": (
            "SUPPORTED"
            if all(strict_saving_by_cost[name] > 0 for name in COST_WORLDS)
            else "REFUTED"
        ),
        "C3_cost_world_changes_optimal_first_measurement": (
            "SUPPORTED" if first_action_changes > 0 else "REFUTED"
        ),
        "C4_expensive_family_is_used_less_often_first": (
            "SUPPORTED"
            if all(row["strict_decrease"] for row in family_frequency_decrease.values())
            else "REFUTED"
        ),
        "C5_target_specific_cost_never_exceeds_topology_identity_cost": (
            "SUPPORTED" if c5_violations == 0 else "REFUTED"
        ),
        "C6_narrow_target_cost_saving_vs_topology_exists": (
            "SUPPORTED"
            if all(narrow_saving_by_cost[name] > 0 for name in COST_WORLDS)
            else "REFUTED"
        ),
        "C7_cost_aware_policy_remains_outcome_adaptive": (
            "SUPPORTED"
            if all(branching_by_cost[name] > 0 for name in COST_WORLDS)
            else "REFUTED"
        ),
        "C8_all_targets_remain_exactly_resolvable": (
            "SUPPORTED" if unresolved == 0 else "REFUTED"
        ),
    }

    by_cost_world = {}
    for cost_name in COST_WORLDS:
        target_summary = {}
        for target in TARGETS:
            specs = [
                row["cost_worlds"][cost_name]["targets"][target]
                for row in rows
            ]
            target_summary[target] = {
                "fixed_cost_distribution": _dist(
                    spec["fixed_minimum_cost"] for spec in specs
                ),
                "adaptive_worst_case_cost_distribution": _dist(
                    spec["adaptive_worst_case_cost"] for spec in specs
                ),
                "mean_fixed_cost": _mean(
                    spec["fixed_minimum_cost"] for spec in specs
                ),
                "mean_adaptive_worst_case_cost": _mean(
                    spec["adaptive_worst_case_cost"] for spec in specs
                ),
                "mean_realized_adaptive_cost": _mean(
                    spec["mean_realized_cost"] for spec in specs
                ),
                "mean_realized_measurement_count": _mean(
                    spec["mean_realized_measurement_count"] for spec in specs
                ),
                "strict_fixed_cost_saving_rows": sum(
                    (spec["fixed_minus_adaptive_worst_case_cost"] or 0) > 0
                    for spec in specs
                ),
                "branching_policy_rows": sum(
                    spec["branching_second_action_count"] >= 2
                    for spec in specs
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

        by_cost_world[cost_name] = {
            "family_costs": COST_WORLDS[cost_name],
            "targets": target_summary,
            "rows_with_any_strict_worst_case_saving": strict_saving_by_cost[
                cost_name
            ],
            "rows_with_narrow_target_saving_vs_topology": narrow_saving_by_cost[
                cost_name
            ],
            "rows_with_branching_policy": branching_by_cost[cost_name],
        }

    result = {
        "schema": "eog.original_idea_cost_aware_adaptive.result.v15",
        "row_count": len(rows),
        "cost_worlds": COST_WORLDS,
        "predeclared_verdicts": verdicts,
        "C1_violation_count": c1_violations,
        "C3_first_action_change_count": first_action_changes,
        "C4_family_frequency_decrease": family_frequency_decrease,
        "C5_violation_count": c5_violations,
        "C8_unresolved_combination_count": unresolved,
        "by_cost_world": by_cost_world,
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
                "C1_violation_count": result["C1_violation_count"],
                "C3_first_action_change_count": result[
                    "C3_first_action_change_count"
                ],
                "C4_family_frequency_decrease": result[
                    "C4_family_frequency_decrease"
                ],
                "C5_violation_count": result["C5_violation_count"],
                "C8_unresolved_combination_count": result[
                    "C8_unresolved_combination_count"
                ],
                "by_cost_world": result["by_cost_world"],
                "fingerprint": result["fingerprint"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
