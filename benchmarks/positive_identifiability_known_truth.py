"""Exhaustive, synthetic positive-observation identifiability check.

The hand-declared support sets are an oracle independent of EOG propagation.
All available positives are an information ceiling, not a detection model.
"""

from __future__ import annotations

import json
from itertools import combinations

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    rank_positive_temporal_occurrence_candidates,
    reconstruct_temporal_worlds,
)

NODES = ("A", "B", "C", "X")
INITIAL = (("A", "t0"),)


def _world(name, support, weight=1.0):
    operator = build_dynamic_transition_operator(
        NODES,
        tuple(
            DynamicReachabilityEdge(
                source=0, target=NODES.index(node), geographic_support=weight
            )
            for node in sorted(support)
        ),
        loss_support=1.0,
    )
    return TemporalWorld(name, ("t0", "t1"), (operator,), ("A",))


def run_benchmark():
    # Each tuple fixes model support, available survey nodes, and generating truth.
    cases = (
        ("disjoint", {"left": {"B"}, "right": {"C"}}, {"B", "C"}, None),
        ("nested", {"narrow": {"B"}, "broad": {"B", "C"}}, {"B", "C"}, None),
        ("same_support", {"fast": {"B"}, "slow": {"B"}}, {"B", "C"}, None),
        ("restricted_survey", {"left": {"B"}, "right": {"C"}}, {"X"}, None),
        (
            "omitted_truth",
            {"left": {"B"}, "right": {"C"}},
            {"B", "C", "X"},
            {"outside": {"X"}},
        ),
        (
            "omitted_truth_hidden",
            {"left": {"B"}, "right": {"C"}},
            {"B"},
            {"outside": {"B", "X"}},
        ),
    )
    rows = []
    checked = 0
    for case, supports, available, external_truth in cases:
        worlds = tuple(
            _world(name, support, 0.25 if name == "slow" else 1.0)
            for name, support in supports.items()
        )
        before = reconstruct_temporal_worlds(worlds, INITIAL)
        ranking = rank_positive_temporal_occurrence_candidates(
            before, worlds, tuple((node, "t1") for node in sorted(available))
        )
        # Check every counterfactual positive, including universe challenges.
        for candidate in ranking.rows:
            expected = {name for name, s in supports.items() if candidate.node_id in s}
            if set(candidate.reachable_world_ids) != expected:
                raise AssertionError((case, "ranking disagrees with support oracle"))
        for truth, truth_support in (external_truth or supports).items():
            observable = sorted(truth_support & available)
            survivors_at_ceiling = None
            minimum = None
            for size in range(len(observable) + 1):
                for subset in combinations(observable, size):
                    expected = {
                        name for name, s in supports.items() if set(subset) <= s
                    }
                    after = reconstruct_temporal_worlds(
                        worlds, INITIAL + tuple((node, "t1") for node in subset)
                    )
                    actual = set(after.compatible_world_ids)
                    checked += 1
                    if actual != expected:
                        raise AssertionError((case, truth, subset, expected, actual))
                    if truth in supports and truth not in actual:
                        raise AssertionError(
                            "valid positive evidence eliminated generating truth"
                        )
                    if actual == {truth} and minimum is None:
                        minimum = size
                    if size == len(observable):
                        survivors_at_ceiling = sorted(actual)
            if not survivors_at_ceiling:
                status = "declared_universe_falsified"
            elif truth not in supports and len(survivors_at_ceiling) == 1:
                status = "unique_compatible_world_with_omitted_truth"
            elif survivors_at_ceiling == [truth]:
                status = "identifiable_at_positive_ceiling"
            else:
                status = "not_identifiable_at_positive_ceiling"
            rows.append(
                {
                    "case": case,
                    "generating_truth": truth,
                    "truth_in_declared_universe": truth in supports,
                    "observable_positives": observable,
                    "survivors_at_positive_ceiling": survivors_at_ceiling,
                    "minimum_positive_count_for_truth_identification": minimum,
                    "status": status,
                    "world_fingerprints": dict(before.world_fingerprints),
                }
            )
    return {
        "schema": "eog.positive_identifiability_known_truth.v1",
        "scope": "synthetic necessary reachability constraints; no occupancy or detection model",
        "claim_ceiling": "finite declared worlds and survey menu only; no empirical validation",
        "subsets_checked": checked,
        "results": rows,
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), sort_keys=True, indent=2))
