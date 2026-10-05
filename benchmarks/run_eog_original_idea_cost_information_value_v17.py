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
from benchmarks.run_eog_original_idea_cost_aware_adaptive_v15 import COST_WORLDS

PROTOCOL = ROOT / "validation/eog_original_idea_cost_information_value_v17/protocol_v17.json"
COST_NAMES = tuple(COST_WORLDS)

DIAGNOSTICS = {
    "is_FP_expensive": ("equal", "KO_expensive", "REL_expensive"),
    "is_KO_expensive": ("equal", "FP_expensive", "REL_expensive"),
    "is_REL_expensive": ("equal", "KO_expensive", "FP_expensive"),
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


def _cost(action_id, cost_name):
    return int(COST_WORLDS[cost_name][_family(action_id)])


def _target_masks(target_partition):
    rows = defaultdict(int)
    for i, target_class in enumerate(target_partition):
        rows[target_class] |= 1 << i
    return tuple(rows.values())


def _action_outcome_masks(action_partitions):
    out = {}
    for action_id, partition in action_partitions.items():
        groups = defaultdict(int)
        for i, outcome_class in enumerate(partition):
            groups[outcome_class] |= 1 << i
        out[action_id] = tuple(groups.values())
    return out


def _build_solver(target_partition, action_partitions):
    n_worlds = len(target_partition)
    if n_worlds != 12:
        raise RuntimeError("v17 requires exactly 12 ecological worlds")
    full_mask = (1 << n_worlds) - 1
    target_masks = _target_masks(target_partition)
    action_outcomes = _action_outcome_masks(action_partitions)
    action_ids = tuple(sorted(action_outcomes))

    @lru_cache(maxsize=None)
    def identified(mask):
        return any((mask & ~target_mask) == 0 for target_mask in target_masks)

    @lru_cache(maxsize=None)
    def children(mask, action_id):
        return tuple(
            sorted(
                child
                for outcome_mask in action_outcomes[action_id]
                for child in (mask & outcome_mask,)
                if child
            )
        )

    def representatives(mask, cost_names):
        by_key = {}
        for action_id in action_ids:
            state_children = children(mask, action_id)
            if len(state_children) <= 1:
                continue
            cost_vector = tuple(_cost(action_id, name) for name in cost_names)
            key = (state_children, cost_vector)
            incumbent = by_key.get(key)
            if incumbent is None or action_id < incumbent:
                by_key[key] = action_id
        return tuple(sorted(by_key.values()))

    def scalar_oracle(cost_name):
        @lru_cache(maxsize=None)
        def solve(mask):
            if identified(mask):
                return 0
            best = None
            for action_id in representatives(mask, (cost_name,)):
                child_values = [solve(child) for child in children(mask, action_id)]
                if any(value is None for value in child_values):
                    continue
                value = _cost(action_id, cost_name) + max(child_values)
                if best is None or value < best:
                    best = value
            return best

        value = solve(full_mask)
        if value is None:
            raise RuntimeError(f"target unresolved in cost world {cost_name}")
        return int(value)

    oracle = {name: scalar_oracle(name) for name in COST_NAMES}

    def minimum_max_regret(cost_names):
        names = tuple(cost_names)
        if not names:
            raise ValueError("cost_names must be non-empty")
        oracle_vector = tuple(oracle[name] for name in names)

        @lru_cache(maxsize=None)
        def feasible(mask, budgets):
            if identified(mask):
                return True
            for action_id in representatives(mask, names):
                costs = tuple(_cost(action_id, name) for name in names)
                if any(cost > budget for cost, budget in zip(costs, budgets, strict=True)):
                    continue
                remaining = tuple(
                    budget - cost
                    for budget, cost in zip(budgets, costs, strict=True)
                )
                if all(feasible(child, remaining) for child in children(mask, action_id)):
                    return True
            return False

        # With 12 ecological worlds, any exact decision tree needs at most 11
        # informative actions on a worst-case path. Each frozen action costs at most 3.
        max_regret_ceiling = 33
        for regret in range(max_regret_ceiling + 1):
            budgets = tuple(value + regret for value in oracle_vector)
            if feasible(full_mask, budgets):
                return int(regret)
        raise RuntimeError("no exact cost-blind policy found within finite ceiling")

    return {
        "oracle": oracle,
        "minimum_max_regret": minimum_max_regret,
    }


def _evaluate_row(active_n, replicate):
    v12 = evaluate_v12(active_n, replicate)
    features = _atomic_features(v12)
    action_partitions = {
        feature_id: _normalized_partition(spec["values"])
        for feature_id, spec in sorted(features.items())
    }

    target_cache = {}
    targets = {}
    for target in TARGETS:
        target_partition = _normalized_partition(_target_values(v12, target))
        if target_partition not in target_cache:
            target_cache[target_partition] = _build_solver(
                target_partition,
                action_partitions,
            )
        solver = target_cache[target_partition]

        baseline = solver["minimum_max_regret"](COST_NAMES)
        if baseline <= 0:
            raise RuntimeError(
                "v17 parent contract expected positive v16 irreducible regret"
            )

        diagnostic_rows = {}
        for diagnostic, no_branch_names in sorted(DIAGNOSTICS.items()):
            residual = solver["minimum_max_regret"](no_branch_names)
            if residual > baseline:
                raise RuntimeError("cost information increased minimax regret")
            diagnostic_rows[diagnostic] = {
                "post_information_worst_residual_regret": residual,
                "gross_information_value": baseline - residual,
                "fraction_of_perfect_information_value": (
                    (baseline - residual) / baseline
                ),
            }

        best_id = min(
            diagnostic_rows,
            key=lambda diagnostic: (
                diagnostic_rows[diagnostic][
                    "post_information_worst_residual_regret"
                ],
                diagnostic,
            ),
        )
        best = diagnostic_rows[best_id]

        targets[target] = {
            "baseline_minimum_max_regret": baseline,
            "perfect_information_post_regret": 0,
            "perfect_information_gross_value": baseline,
            "perfect_information_break_even_calibration_cost": baseline,
            "binary_diagnostics": diagnostic_rows,
            "canonical_best_binary_diagnostic": best_id,
            "best_binary_post_residual_regret": best[
                "post_information_worst_residual_regret"
            ],
            "best_binary_gross_value": best["gross_information_value"],
            "best_binary_fraction_of_perfect_value": best[
                "fraction_of_perfect_information_value"
            ],
            "best_binary_recovers_all_perfect_value": (
                best["post_information_worst_residual_regret"] == 0
            ),
            "all_binary_diagnostics_incomplete": all(
                row["post_information_worst_residual_regret"] > 0
                for row in diagnostic_rows.values()
            ),
        }

    return {
        "active_node_count": active_n,
        "replicate": replicate,
        "targets": targets,
    }


def _evaluate_row_from_args(args):
    return _evaluate_row(*args)


def _mean(values):
    vals = [float(value) for value in values]
    return None if not vals else float(np.mean(vals))


def _dist(values):
    return {
        str(k): int(v)
        for k, v in sorted(Counter(values).items(), key=lambda item: str(item[0]))
    }


def run():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if protocol["status"] != (
        "frozen_before_cost_information_value_implementation_and_scoring"
    ):
        raise RuntimeError("v17 protocol is not frozen")

    tasks = [
        (active_n, replicate)
        for active_n in ACTIVE_SIZES
        for replicate in range(REPLICATES)
    ]
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

    negative_value = 0
    zero_perfect = 0
    positive_binary = 0
    binary_full_recovery = 0
    binary_incomplete = 0
    best_diagnostic_counts = Counter()
    best_diagnostic_by_target = {}
    target_summary = {}

    for target in TARGETS:
        specs = [row["targets"][target] for row in rows]

        perfect_values = [spec["perfect_information_gross_value"] for spec in specs]
        zero_perfect += sum(value == 0 for value in perfect_values)

        diag_counts = Counter(
            spec["canonical_best_binary_diagnostic"]
            for spec in specs
        )
        best_diagnostic_by_target[target] = dict(sorted(diag_counts.items()))
        best_diagnostic_counts.update(diag_counts)

        positive_binary += sum(spec["best_binary_gross_value"] > 0 for spec in specs)
        binary_full_recovery += sum(
            spec["best_binary_recovers_all_perfect_value"] for spec in specs
        )
        binary_incomplete += sum(
            spec["all_binary_diagnostics_incomplete"] for spec in specs
        )

        for spec in specs:
            for row in spec["binary_diagnostics"].values():
                negative_value += int(row["gross_information_value"] < 0)

        target_summary[target] = {
            "mean_perfect_information_value": _mean(perfect_values),
            "perfect_information_value_distribution": _dist(perfect_values),
            "mean_best_binary_information_value": _mean(
                spec["best_binary_gross_value"] for spec in specs
            ),
            "mean_best_binary_fraction_of_perfect_value": _mean(
                spec["best_binary_fraction_of_perfect_value"] for spec in specs
            ),
            "best_binary_full_recovery_rows": sum(
                spec["best_binary_recovers_all_perfect_value"] for spec in specs
            ),
            "all_binary_diagnostics_incomplete_rows": sum(
                spec["all_binary_diagnostics_incomplete"] for spec in specs
            ),
            "canonical_best_binary_diagnostic_counts": dict(
                sorted(diag_counts.items())
            ),
        }

    target_signatures = {
        (
            target_summary[target]["mean_perfect_information_value"],
            tuple(
                sorted(
                    target_summary[target][
                        "canonical_best_binary_diagnostic_counts"
                    ].items()
                )
            ),
        )
        for target in TARGETS
    }

    verdicts = {
        "V1_perfect_cost_information_has_positive_value_everywhere": (
            "SUPPORTED" if zero_perfect == 0 else "REFUTED"
        ),
        "V2_one_binary_cost_diagnostic_has_positive_value_somewhere": (
            "SUPPORTED" if positive_binary > 0 else "REFUTED"
        ),
        "V3_no_single_binary_cost_diagnostic_is_universally_best": (
            "SUPPORTED" if len(best_diagnostic_counts) > 1 else "REFUTED"
        ),
        "V4_partial_cost_information_can_recover_all_perfect_information_value": (
            "SUPPORTED" if binary_full_recovery > 0 else "REFUTED"
        ),
        "V5_partial_information_is_strictly_incomplete_somewhere": (
            "SUPPORTED" if binary_incomplete > 0 else "REFUTED"
        ),
        "V6_cost_information_value_depends_on_ecological_target": (
            "SUPPORTED" if len(target_signatures) > 1 else "REFUTED"
        ),
        "V7_information_never_has_negative_gross_value": (
            "SUPPORTED" if negative_value == 0 else "REFUTED"
        ),
        "V8_cost_information_subseries_stop": "SUPPORTED",
    }

    result = {
        "schema": "eog.original_idea_cost_information_value.result.v17",
        "row_count": len(rows),
        "row_target_count": len(rows) * len(TARGETS),
        "predeclared_verdicts": verdicts,
        "negative_information_value_count": negative_value,
        "zero_perfect_information_value_count": zero_perfect,
        "row_targets_with_positive_best_binary_value": positive_binary,
        "row_targets_with_binary_full_perfect_value_recovery": binary_full_recovery,
        "row_targets_with_all_binary_diagnostics_incomplete": binary_incomplete,
        "canonical_best_binary_diagnostic_counts": dict(
            sorted(best_diagnostic_counts.items())
        ),
        "by_target": target_summary,
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
                "row_targets_with_positive_best_binary_value": result[
                    "row_targets_with_positive_best_binary_value"
                ],
                "row_targets_with_binary_full_perfect_value_recovery": result[
                    "row_targets_with_binary_full_perfect_value_recovery"
                ],
                "row_targets_with_all_binary_diagnostics_incomplete": result[
                    "row_targets_with_all_binary_diagnostics_incomplete"
                ],
                "canonical_best_binary_diagnostic_counts": result[
                    "canonical_best_binary_diagnostic_counts"
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
