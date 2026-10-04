#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
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
from benchmarks.run_eog_original_idea_cost_aware_adaptive_v15 import (
    COST_WORLDS,
)

PROTOCOL = ROOT / "validation/eog_original_idea_cost_uncertain_policy_v16/protocol_v16.json"
COST_NAMES = tuple(COST_WORLDS)
COST_INDEX = {name: i for i, name in enumerate(COST_NAMES)}


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


def _cost_vector(action_id):
    family = _family(action_id)
    return tuple(
        int(COST_WORLDS[name][family])
        for name in COST_NAMES
    )


@dataclass(frozen=True)
class PolicyOption:
    costs: tuple[int, ...]
    serialization: str
    first_action: str | None


def _dominates(left, right):
    return (
        all(a <= b for a, b in zip(left, right, strict=True))
        and any(a < b for a, b in zip(left, right, strict=True))
    )


def _prune(options):
    # Equal cost vectors keep only the lexicographically smallest exact tree.
    by_cost = {}
    for option in options:
        incumbent = by_cost.get(option.costs)
        if incumbent is None or option.serialization < incumbent.serialization:
            by_cost[option.costs] = option

    rows = tuple(
        sorted(
            by_cost.values(),
            key=lambda option: (option.costs, option.serialization),
        )
    )
    keep = []
    for candidate in rows:
        if any(
            _dominates(other.costs, candidate.costs)
            for other in rows
            if other is not candidate
        ):
            continue
        keep.append(candidate)
    return tuple(keep)


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


def _prune_vectors(vectors):
    rows = tuple(sorted(set(tuple(int(v) for v in row) for row in vectors)))
    keep = []
    for candidate in rows:
        if any(
            _dominates(other, candidate)
            for other in rows
            if other != candidate
        ):
            continue
        keep.append(candidate)
    return tuple(keep)


def _policy_frontier(target_partition, action_partitions):
    n_worlds = len(target_partition)
    if n_worlds != 12:
        raise RuntimeError("v16 requires exactly 12 worlds")
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

    @lru_cache(maxsize=None)
    def representatives(mask):
        # Exact substitutes under every cost world are collapsed.
        by_key = {}
        for action_id in action_ids:
            state_children = children(mask, action_id)
            if len(state_children) <= 1:
                continue
            key = (state_children, _cost_vector(action_id))
            incumbent = by_key.get(key)
            if incumbent is None or action_id < incumbent:
                by_key[key] = action_id
        return tuple(sorted(by_key.values()))

    @lru_cache(maxsize=None)
    def frontier(mask):
        if identified(mask):
            return ((0, 0, 0, 0),)

        all_candidates = []
        for action_id in representatives(mask):
            state_children = children(mask, action_id)

            # The parent worst-case vector uses componentwise maxima over child
            # policy vectors. Carry only undominated max vectors while folding
            # children, avoiding policy-string Cartesian expansion.
            partial = ((0, 0, 0, 0),)
            feasible = True
            for child in state_children:
                child_frontier = frontier(child)
                if not child_frontier:
                    feasible = False
                    break
                combined = (
                    tuple(
                        max(a, b)
                        for a, b in zip(left, right, strict=True)
                    )
                    for left in partial
                    for right in child_frontier
                )
                partial = _prune_vectors(combined)
            if not feasible:
                continue

            action_cost = _cost_vector(action_id)
            all_candidates.extend(
                tuple(
                    a + b
                    for a, b in zip(action_cost, child_max, strict=True)
                )
                for child_max in partial
            )

        return _prune_vectors(all_candidates)

    root = frontier(full_mask)
    if not root:
        return {
            "resolvable": False,
            "frontier": (),
            "oracle_costs": None,
            "selected": None,
            "equal_commitment": None,
        }

    oracle_costs = tuple(
        min(vector[i] for vector in root)
        for i in range(len(COST_NAMES))
    )

    def regret(vector):
        return tuple(
            value - oracle
            for value, oracle in zip(
                vector,
                oracle_costs,
                strict=True,
            )
        )

    objective_prefix = min(
        (
            max(regret(vector)),
            sum(regret(vector)),
            max(vector),
        )
        for vector in root
    )
    selected_vectors = tuple(
        vector
        for vector in root
        if (
            max(regret(vector)),
            sum(regret(vector)),
            max(vector),
        )
        == objective_prefix
    )

    @lru_cache(maxsize=None)
    def reconstruct(mask, desired):
        desired = tuple(desired)
        if identified(mask):
            if desired != (0, 0, 0, 0):
                return None
            return ("STOP", None)

        candidates = []
        for action_id in representatives(mask):
            action_cost = _cost_vector(action_id)
            residual = tuple(
                value - cost
                for value, cost in zip(desired, action_cost, strict=True)
            )
            if any(value < 0 for value in residual):
                continue

            state_children = children(mask, action_id)
            child_frontiers = [frontier(child) for child in state_children]

            # Enumerate only child-vector combinations that do not exceed the
            # required componentwise maximum.  This is used for final tree
            # reconstruction only, not during the main frontier DP.
            choices = []

            def visit(index, current_max, selected):
                if index == len(state_children):
                    if current_max == residual:
                        choices.append(tuple(selected))
                    return
                for vector in child_frontiers[index]:
                    updated = tuple(
                        max(a, b)
                        for a, b in zip(current_max, vector, strict=True)
                    )
                    if any(
                        value > limit
                        for value, limit in zip(updated, residual, strict=True)
                    ):
                        continue
                    visit(index + 1, updated, [*selected, vector])

            visit(0, (0, 0, 0, 0), [])
            for vectors in choices:
                child_serials = []
                valid = True
                for child, vector in zip(
                    state_children,
                    vectors,
                    strict=True,
                ):
                    built = reconstruct(child, vector)
                    if built is None:
                        valid = False
                        break
                    child_serials.append((child, built[0]))
                if not valid:
                    continue
                serialization = (
                    f"{action_id}{{"
                    + "|".join(
                        f"{child}:{serial}"
                        for child, serial in child_serials
                    )
                    + "}"
                )
                candidates.append((serialization, action_id))

        if not candidates:
            return None
        return min(candidates)

    selected_options = []
    for vector in selected_vectors:
        built = reconstruct(full_mask, vector)
        if built is None:
            raise RuntimeError("could not reconstruct selected Pareto policy")
        selected_options.append(
            PolicyOption(
                costs=vector,
                serialization=built[0],
                first_action=built[1],
            )
        )
    selected = min(
        selected_options,
        key=lambda option: option.serialization,
    )

    # Reconstruct the canonical v15 equal-cost tree separately so the v16
    # comparator matches the original local lexicographic tie rule.
    equal_index = COST_INDEX["equal"]

    @lru_cache(maxsize=None)
    def equal_representatives(mask):
        by_children = {}
        for action_id in action_ids:
            state_children = children(mask, action_id)
            if len(state_children) <= 1:
                continue
            candidate = (
                _cost_vector(action_id)[equal_index],
                action_id,
            )
            incumbent = by_children.get(state_children)
            if incumbent is None or candidate < incumbent:
                by_children[state_children] = candidate
        return tuple(
            sorted(action_id for _, action_id in by_children.values())
        )

    @lru_cache(maxsize=None)
    def equal_minimum(mask):
        if identified(mask):
            return 0
        best = None
        for action_id in equal_representatives(mask):
            child_values = [equal_minimum(child) for child in children(mask, action_id)]
            if any(value is None for value in child_values):
                continue
            candidate = (
                _cost_vector(action_id)[equal_index]
                + max(child_values)
            )
            if best is None or candidate < best:
                best = candidate
        return best

    @lru_cache(maxsize=None)
    def equal_tree(mask):
        if identified(mask):
            return PolicyOption((0, 0, 0, 0), "STOP", None)

        optimum = equal_minimum(mask)
        if optimum is None:
            raise RuntimeError("equal-cost oracle unexpectedly unresolved")

        valid = []
        for action_id in equal_representatives(mask):
            state_children = children(mask, action_id)
            child_values = [equal_minimum(child) for child in state_children]
            if any(value is None for value in child_values):
                continue
            candidate_cost = (
                _cost_vector(action_id)[equal_index]
                + max(child_values)
            )
            if candidate_cost == optimum:
                valid.append(action_id)
        if not valid:
            raise RuntimeError("equal-cost canonical action missing")
        action_id = min(valid)

        child_options = [equal_tree(child) for child in children(mask, action_id)]
        child_max = tuple(
            max(option.costs[i] for option in child_options)
            for i in range(len(COST_NAMES))
        )
        costs = tuple(
            a + b
            for a, b in zip(
                _cost_vector(action_id),
                child_max,
                strict=True,
            )
        )
        serialization = (
            f"{action_id}{{"
            + "|".join(
                f"{child}:{option.serialization}"
                for child, option in zip(
                    children(mask, action_id),
                    child_options,
                    strict=True,
                )
            )
            + "}"
        )
        return PolicyOption(costs, serialization, action_id)

    equal_commitment = equal_tree(full_mask)

    if equal_commitment.costs[equal_index] != oracle_costs[equal_index]:
        raise RuntimeError("equal-cost canonical tree does not match root oracle")

    return {
        "resolvable": True,
        "frontier": root,
        "oracle_costs": oracle_costs,
        "selected": selected,
        "equal_commitment": equal_commitment,
    }

def _evaluate_row(active_n, replicate):
    v12 = evaluate_v12(active_n, replicate)
    features = _atomic_features(v12)
    action_partitions = {
        feature_id: _normalized_partition(spec["values"])
        for feature_id, spec in sorted(features.items())
    }

    cache = {}
    targets = {}
    for target in TARGETS:
        target_partition = _normalized_partition(
            _target_values(v12, target)
        )
        if target_partition not in cache:
            cache[target_partition] = _policy_frontier(
                target_partition,
                action_partitions,
            )
        solved = cache[target_partition]
        if not solved["resolvable"]:
            targets[target] = {"resolvable": False}
            continue

        selected = solved["selected"]
        equal = solved["equal_commitment"]
        oracle = solved["oracle_costs"]
        selected_regret = tuple(
            value - lower
            for value, lower in zip(
                selected.costs,
                oracle,
                strict=True,
            )
        )
        equal_regret = tuple(
            value - lower
            for value, lower in zip(
                equal.costs,
                oracle,
                strict=True,
            )
        )
        targets[target] = {
            "resolvable": True,
            "pareto_frontier_size": len(solved["frontier"]),
            "oracle_costs": {
                name: oracle[i] for i, name in enumerate(COST_NAMES)
            },
            "minimax_policy_costs": {
                name: selected.costs[i]
                for i, name in enumerate(COST_NAMES)
            },
            "minimax_policy_regrets": {
                name: selected_regret[i]
                for i, name in enumerate(COST_NAMES)
            },
            "minimum_max_regret": max(selected_regret),
            "sum_regret": sum(selected_regret),
            "canonical_first_action": selected.first_action,
            "canonical_first_family": (
                None
                if selected.first_action is None
                else _family(selected.first_action)
            ),
            "equal_commitment_costs": {
                name: equal.costs[i]
                for i, name in enumerate(COST_NAMES)
            },
            "equal_commitment_regrets": {
                name: equal_regret[i]
                for i, name in enumerate(COST_NAMES)
            },
            "equal_commitment_max_regret": max(equal_regret),
            "equal_commitment_first_action": equal.first_action,
            "first_action_changed_vs_equal": (
                selected.first_action != equal.first_action
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
        "frozen_before_cost_uncertain_policy_implementation_and_scoring"
    ):
        raise RuntimeError("v16 protocol is not frozen")

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

    unresolved = 0
    negative_regret = 0
    positive_regret = 0
    zero_regret = 0
    strict_vs_equal = 0
    changed_first = 0
    first_actions = Counter()
    first_families = Counter()
    narrow_saving_rows = 0

    target_summary = {}
    for target in TARGETS:
        specs = [row["targets"][target] for row in rows]
        unresolved += sum(not spec["resolvable"] for spec in specs)
        resolved = [spec for spec in specs if spec["resolvable"]]

        for spec in resolved:
            regrets = spec["minimax_policy_regrets"].values()
            negative_regret += sum(value < 0 for value in regrets)
            positive_regret += int(spec["minimum_max_regret"] > 0)
            zero_regret += int(spec["minimum_max_regret"] == 0)
            strict_vs_equal += int(
                spec["minimum_max_regret"]
                < spec["equal_commitment_max_regret"]
            )
            changed_first += int(spec["first_action_changed_vs_equal"])
            if spec["canonical_first_action"] is not None:
                first_actions[spec["canonical_first_action"]] += 1
            if spec["canonical_first_family"] is not None:
                first_families[spec["canonical_first_family"]] += 1

        target_summary[target] = {
            "minimum_max_regret_distribution": _dist(
                spec["minimum_max_regret"] for spec in resolved
            ),
            "mean_minimum_max_regret": _mean(
                spec["minimum_max_regret"] for spec in resolved
            ),
            "zero_regret_rows": sum(
                spec["minimum_max_regret"] == 0 for spec in resolved
            ),
            "strict_improvement_vs_equal_commitment_rows": sum(
                spec["minimum_max_regret"]
                < spec["equal_commitment_max_regret"]
                for spec in resolved
            ),
            "first_action_change_vs_equal_rows": sum(
                spec["first_action_changed_vs_equal"]
                for spec in resolved
            ),
            "mean_pareto_frontier_size": _mean(
                spec["pareto_frontier_size"] for spec in resolved
            ),
        }

    for row in rows:
        full = row["targets"]["full_topology_identity"]
        if not full["resolvable"]:
            continue
        full_max_cost = max(full["minimax_policy_costs"].values())
        if any(
            row["targets"][target]["resolvable"]
            and max(
                row["targets"][target]["minimax_policy_costs"].values()
            )
            < full_max_cost
            for target in ("intervention", "critical_node_count")
        ):
            narrow_saving_rows += 1

    verdicts = {
        "U1_cost_blind_policy_resolves_all_targets_exactly": (
            "SUPPORTED" if unresolved == 0 else "REFUTED"
        ),
        "U2_cost_specific_oracles_are_lower_bounds": (
            "SUPPORTED" if negative_regret == 0 else "REFUTED"
        ),
        "U3_irreducible_cost_world_regret_exists": (
            "SUPPORTED" if positive_regret > 0 else "REFUTED"
        ),
        "U4_zero_regret_common_policies_also_exist": (
            "SUPPORTED" if zero_regret > 0 else "REFUTED"
        ),
        "U5_minimax_regret_beats_equal_cost_commitment_somewhere": (
            "SUPPORTED" if strict_vs_equal > 0 else "REFUTED"
        ),
        "U6_cost_uncertainty_changes_first_measurement": (
            "SUPPORTED" if changed_first > 0 else "REFUTED"
        ),
        "U7_narrow_targets_can_be_cheaper_under_cost_uncertainty": (
            "SUPPORTED" if narrow_saving_rows > 0 else "REFUTED"
        ),
        "U8_no_universal_first_action_under_cost_uncertainty": (
            "SUPPORTED" if len(first_actions) > 1 else "REFUTED"
        ),
    }

    result = {
        "schema": "eog.original_idea_cost_uncertain_policy.result.v16",
        "row_count": len(rows),
        "predeclared_verdicts": verdicts,
        "unresolved_row_target_count": unresolved,
        "negative_regret_count": negative_regret,
        "positive_irreducible_regret_row_target_count": positive_regret,
        "zero_regret_row_target_count": zero_regret,
        "strict_minimax_improvement_vs_equal_commitment_count": strict_vs_equal,
        "first_action_change_vs_equal_count": changed_first,
        "narrow_target_max_cost_saving_row_count": narrow_saving_rows,
        "canonical_first_action_count": len(first_actions),
        "canonical_first_actions": dict(sorted(first_actions.items())),
        "canonical_first_family_counts": dict(sorted(first_families.items())),
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
                "positive_irreducible_regret_row_target_count": result[
                    "positive_irreducible_regret_row_target_count"
                ],
                "zero_regret_row_target_count": result[
                    "zero_regret_row_target_count"
                ],
                "strict_minimax_improvement_vs_equal_commitment_count": result[
                    "strict_minimax_improvement_vs_equal_commitment_count"
                ],
                "first_action_change_vs_equal_count": result[
                    "first_action_change_vs_equal_count"
                ],
                "narrow_target_max_cost_saving_row_count": result[
                    "narrow_target_max_cost_saving_row_count"
                ],
                "canonical_first_family_counts": result[
                    "canonical_first_family_counts"
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
