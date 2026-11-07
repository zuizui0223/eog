"""Post-result exhaustive single-site lower-bound audit for the M-release target.

This checks *every* variable one-node A/B/M binary assay in each ambiguous
current-G fibre. A two-query greedy path provides an achievable upper bound.
The proof applies only to fixed finite synthetic worlds, not field ecology.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_partial_local_assays_v1 as local  # noqa: E402


def one_site_sufficiency(states, n_nodes):
    if len({s["sign"] for s in states}) <= 1:
        return {"sufficient": True, "example_site": None, "n_tested_sites": 0}
    sites = list(local.candidate_queries(states, n_nodes))
    for test in sites:
        classes = defaultdict(set)
        for state in states:
            classes[local.query_bit(state, test)].add(state["sign"])
        if all(len(signs) == 1 for signs in classes.values()):
            return {
                "sufficient": True,
                "example_site": f"{test[0]}:{test[1]}",
                "n_tested_sites": len(sites),
            }
    return {
        "sufficient": False,
        "example_site": None,
        "n_tested_sites": len(sites),
    }


def audit(systems):
    rows, G_count, world_count = [], 0, 0
    for system in systems:
        sid = system["system_id"]
        env = np.asarray(system["environment"], float)
        median = np.median(env, axis=0)
        scale = np.median(abs(env - median), axis=0) * 1.4826
        if np.any(scale <= 0):
            raise AssertionError("zero MAD in source reference")
        z = (env - median) / scale
        width, height = system["width"], system["height"]
        masks, cache = defaultdict(list), {}
        for world in system["worlds"]:
            masks[int(world["G_bits"])].append(world)
        for G, world_rows in sorted(masks.items()):
            G_count += 1
            world_count += len(world_rows)
            _, target_labels = local.signs_from_parent(
                sid, world_rows, z, width, height, "M", cache
            )
            states = local.deduplicate_states(world_rows, target_labels)
            if len({s["sign"] for s in states}) < 2:
                continue
            one = one_site_sufficiency(states, width * height)
            all_two = all(
                local.simulate_policy(
                    states, truth=state, n_nodes=width * height,
                    policy="greedy_all", seed=0, system_id=sid, G=G,
                    target_axis="M", budget=2,
                )["steps"][2]["identified"]
                for state in states
            )
            if not all_two:
                raise AssertionError("two-site constructive upper bound failed")
            rows.append({
                "system_id": sid, "G_bits": G,
                "possible_signs": sorted({s["sign"] for s in states}),
                "distinct_mask_triples": len(states),
                "original_parameter_world_labels": len(world_rows),
                "all_informative_sites_tested": one["n_tested_sites"],
                "one_site_sufficient": one["sufficient"],
                "one_site_example": one["example_site"],
                "greedy_two_sites_guaranteed": all_two,
                "exact_minimum_worst_case_ideal_assays": (
                    1 if one["sufficient"] else 2
                ),
            })
    if (len(systems), world_count, G_count, len(rows)) != (12, 768, 129, 8):
        raise AssertionError("canonical parent source changed")
    distribution = {
        str(n): sum(
            row["exact_minimum_worst_case_ideal_assays"] == n
            for row in rows
        ) for n in (1, 2)
    }
    if distribution != {"1": 5, "2": 3}:
        raise AssertionError("exhaustive single-site audit disagrees with replay")
    report = {
        "schema": "eog.bam_local_assay_exact_lower_bound_v1",
        "scope": "POST_RESULT_EXPLORATORY_EXACT_AUDIT_OF_FIXED_FINITE_UNIVERSE",
        "systems": len(systems), "parent_worlds": world_count,
        "parent_current_G_fibres": G_count,
        "ambiguous_M_fibres": len(rows),
        "exact_minimum_worst_case_queries_counts": distribution,
        "rows": rows,
        "interpretation": (
            "Exhaustively considered every variable one-node A/B/M "
            "binary assay in each M-response-ambiguous current-G fibre. "
            "For three fibres one assay is insufficient; the independently "
            "verified adaptive greedy two-assay policy gives an achievable "
            "upper bound. All results conditional on the finite source."
        ),
    }
    report["fingerprint"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(":"),
                   allow_nan=False).encode()
    ).hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="frozen offline source fixture")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    systems = (
        json.loads(Path(args.fixture).read_text())
        if args.fixture else local.parent.canonical_systems()
    )
    result = audit(systems)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("EXACT_MIN_ASSAYS=" + json.dumps({
        "counts": result["exact_minimum_worst_case_queries_counts"],
        "fingerprint": result["fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
