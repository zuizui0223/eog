"""Post-result exact finite-world minimum local-assay depth after one G omission.

Exhaustively search binary site queries in a worst-case adaptive decision tree.
This is a synthetic target-identification audit, not new field inference.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_one_missed_G_v1 as one_miss  # noqa: E402


def exact_min_queries(states, n_nodes, max_budget=3):
    if len({s["sign"] for s in states}) == 1:
        return 0
    n = len(states)
    # Collapse tests that induce the same unlabeled binary partition.
    partitions = {}
    for axis, node in one_miss.candidate_tests(states, n_nodes, one_miss.AXES):
        true = frozenset(i for i, s in enumerate(states)
                         if one_miss.bit(s, axis, node))
        false = frozenset(range(n)) - true
        if not true or not false:
            continue
        key = (true, false) if min(true) < min(false) else (false, true)
        partitions.setdefault(key, (axis, node))
    sign = tuple(s["sign"] for s in states)
    @lru_cache(None)
    def can_identify(indices, remaining_budget):
        if len({sign[i] for i in indices}) == 1:
            return True
        if remaining_budget == 0:
            return False
        indexset = frozenset(indices)
        for left, right in partitions:
            l, r = indexset & left, indexset & right
            if not l or not r:
                continue
            if (can_identify(tuple(sorted(l)), remaining_budget - 1)
                and can_identify(tuple(sorted(r)), remaining_budget - 1)):
                return True
        return False
    for budget in range(max_budget + 1):
        if can_identify(tuple(range(n)), budget):
            return budget
    return None


def audit(systems):
    rows = []
    per_original_G = defaultdict(dict)
    n_worlds = n_G = 0
    for system in systems:
        sid = system["system_id"]
        worlds, n_nodes = system["worlds"], system["width"] * system["height"]
        if len(worlds) != 64:
            raise AssertionError("canonical system not 64 worlds")
        by_G, possible_D = defaultdict(list), defaultdict(list)
        for world in worlds:
            by_G[int(world["G_bits"])].append(world)
        n_worlds += len(worlds)
        n_G += len(by_G)
        for G, group in by_G.items():
            for D in one_miss.enumerated_observations(G):
                possible_D[D].extend(group)
        _, signs, exact_baseline = one_miss.world_signs(system, "M")
        for D, compatible_worlds in sorted(possible_D.items()):
            states = one_miss.unique_states(compatible_worlds, signs)
            depth = exact_min_queries(states, n_nodes)
            if depth is None:
                raise AssertionError("no complete identification within 3 assays")
            row = {
                "system_id": sid, "observed_D": D, "exact_min_depth": depth,
                "candidate_true_G": len({r["G_bits"] for r in compatible_worlds}),
                "candidate_distinct_A_B_M": len(states),
                "n_original_parameter_labels": len(compatible_worlds),
            }
            rows.append(row)
            for G in {int(r["G_bits"]) for r in compatible_worlds}:
                per_original_G[(sid, G)][D] = depth
    if (len(systems), n_worlds, n_G, len(rows)) != (12, 768, 129, 2627):
        raise AssertionError("original denominators not preserved")
    frequencies = {
        str(b): sum(r["exact_min_depth"] == b for r in rows)
        for b in range(4)
    }
    robust_G = {
        str(b): sum(all(depth <= b for depth in d.values())
                    for d in per_original_G.values())
        for b in range(4)
    }
    result = {
        "schema": "eog.bam_one_missed_G_exact_query_depth_v1",
        "status": "POST_RESULT_EXHAUSTIVE_AUDIT_OF_EXPOSED_FINITE_UNIVERSE",
        "n_landscapes": len(systems),
        "n_original_worlds": n_worlds,
        "n_original_G": n_G,
        "n_possible_observed_D": len(rows),
        "minimal_worst_case_query_depth_per_D": frequencies,
        "original_G_uniform_robustness_at_budget": robust_G,
        "requires_three_queries": [
            {"system_id": r["system_id"], "observed_D": r["observed_D"]}
            for r in rows if r["exact_min_depth"] == 3
        ],
        "limits": [
            "Finite candidate masks and perfect binary A/B/M measurements.",
            "Up to one occupied cell missed in otherwise complete observed map.",
            "Exhaustive query optimality is conditional on this fixed candidate set.",
            "No field sample-size or biological mechanism inference.",
            "This exact lower-bound check was added AFTER the initial exploratory scores.",
        ],
    }
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()
    ).hexdigest()
    return result, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="previously frozen virtual-source fixture")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    systems = (
        json.loads(Path(args.fixture).read_text())
        if args.fixture else one_miss.parent.canonical_systems()
    )
    result, rows = audit(systems)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("EXACT_ONE_MISS_AUDIT=" + json.dumps({
        "depths": result["minimal_worst_case_query_depth_per_D"],
        "robust": result["original_G_uniform_robustness_at_budget"],
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
