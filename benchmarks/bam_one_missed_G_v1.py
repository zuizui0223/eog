"""One false-negative occupied cell and local BAM-assay robustness.

Explore exact finite-world identified sets; not a detection probability model,
empirical causal test, or replacement of frozen EOG-WF and parent BAM outputs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_geometry_response_envelopes_v1 as parent  # noqa: E402

AXES = ("A", "B", "M")
SEEDS = tuple(range(20261107, 20261123))
BUDGETS = (0, 1, 2, 3)
POLICIES = ("greedy_all", "greedy_B", "greedy_A")
PROTOCOL_COMMIT = "cc89f3ac67cf05bd9a42a3a0d17644f10bca4f42"


def enumerated_observations(G: int):
    """Exact G, and each observation with one occupied cell undetected."""
    if not isinstance(G, int) or G < 0:
        raise ValueError("G must be a nonnegative integer mask")
    return (G,) + tuple(
        G & ~(1 << i) for i in range(G.bit_length()) if G & (1 << i)
    )


def compatible(D: int, G: int):
    return D >= 0 and G >= 0 and (G & D) == D and (G ^ D).bit_count() <= 1


def bit(state, axis, node):
    return (state["masks"][AXES.index(axis)] >> node) & 1


def unique_states(rows, signs):
    states = {}
    for row in rows:
        k = tuple(int(row[f"{a}_bits"]) for a in AXES)
        s = int(signs[row["world_id"]])
        if k in states and states[k]["sign"] != s:
            raise ValueError("same A/B/M triple has conflicting target sign")
        if k not in states:
            states[k] = {"masks": k, "sign": s, "n_labels": 0}
        states[k]["n_labels"] += 1
    return [states[k] for k in sorted(states)]


def candidate_tests(states, n_nodes, allowed):
    for axis in AXES:
        if axis not in allowed:
            continue
        for node in range(n_nodes):
            vals = {bit(s, axis, node) for s in states}
            if vals == {0, 1}:
                yield axis, node


def test_score(states, axis, node):
    zeros = Counter(s["sign"] for s in states if bit(s, axis, node) == 0)
    ones = Counter(s["sign"] for s in states if bit(s, axis, node) == 1)
    return sum(v * w for k, v in zeros.items() for j, w in ones.items() if j != k)


def choose(states, n_nodes, used, policy, seed, sid, D, target):
    if len({s["sign"] for s in states}) <= 1:
        return None
    allowed = {
        "greedy_all": AXES,
        "greedy_B": ("B",),
        "greedy_A": ("A",),
        "hash_all": AXES,
    }[policy]
    tests = [t for t in candidate_tests(states, n_nodes, allowed) if t not in used]
    if not tests:
        return None
    if policy == "hash_all":
        return min(tests, key=lambda t: (
            hashlib.sha256(
                f"{seed}|{sid}|{D}|{target}|{t[0]}|{t[1]}".encode()
            ).hexdigest(), t
        ))
    scored = [(test_score(states, *t), t) for t in tests]
    top = max(score for score, _ in scored)
    return next(t for score, t in scored if score == top) if top else None


def simulate(states, n_nodes, sid, D, target, policy, seed, truth):
    living, used, states_at_budget = list(states), [], []
    for budget in BUDGETS:
        if truth not in living:
            raise AssertionError("true state eliminated")
        states_at_budget.append((len({s["sign"] for s in living}) == 1, len(living)))
        if budget == BUDGETS[-1]:
            break
        query = choose(living, n_nodes, used, policy, seed, sid, D, target)
        if query is None:
            continue
        outcome = bit(truth, *query)
        refined = [s for s in living if bit(s, *query) == outcome]
        if not refined or len(refined) > len(living):
            raise AssertionError("posterior candidate set failed contraction")
        living = refined
        used.append(query)
    flags = [known for known, _ in states_at_budget]
    if flags != sorted(flags):
        raise AssertionError("target identification was lost")
    return states_at_budget


def world_signs(system, axis):
    features = np.asarray(system["environment"], dtype=float)
    median = np.median(features, axis=0)
    scale = np.median(np.abs(features - median), axis=0) * 1.4826
    if not np.isfinite(features).all() or np.any(scale <= 0):
        raise ValueError("invalid frozen parent reference")
    z = (features - median) / scale
    groups = defaultdict(list)
    for w in system["worlds"]:
        if int(w["G_bits"]) != (
            int(w["A_bits"]) & int(w["B_bits"]) & int(w["M_bits"])
        ):
            raise ValueError("parent G is not A&B&M")
        groups[int(w["G_bits"])].append(w)
    signs, known, cache = {}, 0, {}
    for G, rows in sorted(groups.items()):
        result = parent.fibre_summary(
            system["system_id"], rows, z, system["width"], system["height"],
            axis, cache
        )
        current = result["targets"]["span"]["current"]
        tolerance = parent.EPS * max(
            1., abs(current), *(abs(r["after"]["span"])
                                for r in result["world_outcomes"])
        )
        for outcome in result["world_outcomes"]:
            delta = outcome["changes"]["span"]
            signs[outcome["world_id"]] = (
                -1 if delta < -tolerance else 1 if delta > tolerance else 0
            )
        observed_signs = sorted({signs[r["world_id"]] for r in rows})
        if observed_signs != result["targets"]["span"]["directions"]:
            raise AssertionError("parent target sign classification drift")
        known += int(result["targets"]["span"]["direction_identified"])
    return groups, signs, known


def evaluate(systems):
    if len(systems) != 12:
        raise AssertionError("exact original 12 landscapes required")
    observations, true_G, provenance = [], [], []
    source_worlds = G_classes = 0
    for system in systems:
        sid = system["system_id"]
        n_nodes = system["width"] * system["height"]
        if len(system["worlds"]) != 64:
            raise AssertionError("exact original 64 worlds per landscape required")
        original = defaultdict(list)
        for world in system["worlds"]:
            original[int(world["G_bits"])].append(world)
        G_classes += len(original)
        source_worlds += len(system["worlds"])
        observed = defaultdict(list)
        for G, group in original.items():
            for D in enumerated_observations(G):
                observed[D].extend(group)
        for D, group in observed.items():
            if (
                not group
                or any(not compatible(D, int(w["G_bits"])) for w in group)
                or len({w["world_id"] for w in group}) != len(group)
            ):
                raise AssertionError("invalid one-miss observation equivalence class")
        for axis in AXES:
            original_groups, labels, perfect_known = world_signs(system, axis)
            for D, group in sorted(observed.items()):
                states = unique_states(group, labels)
                unanimous = len({s["sign"] for s in states}) == 1
                policies = [
                    (policy, 0) for policy in POLICIES
                ] + [("hash_all", seed) for seed in SEEDS]
                outcomes_by_policy = {}
                for policy, seed in policies:
                    if unanimous:
                        outcomes_by_policy[(policy, seed)] = [True] * 4
                    else:
                        outcomes = [
                            simulate(states, n_nodes, sid, D, axis, policy,
                                     seed, truth)
                            for truth in states
                        ]
                        outcomes_by_policy[(policy, seed)] = [
                            all(path[b][0] for path in outcomes)
                            for b in BUDGETS
                        ]
                row = {
                    "system_id": sid, "observed_D": D,
                    "release_axis": axis,
                    "d_is_exact_G_in_source": int(D in original),
                    "n_true_G_candidates": len({w["G_bits"] for w in group}),
                    "n_distinct_mask_triples": len(states),
                    "n_parameter_world_labels": len(group),
                    "sign_ambiguous_before_assays": int(not unanimous),
                }
                for policy in POLICIES:
                    for budget in BUDGETS:
                        row[f"{policy}_uniform_budget{budget}"] = int(
                            outcomes_by_policy[(policy, 0)][budget]
                        )
                for seed in SEEDS:
                    for budget in BUDGETS:
                        row[f"hash_{seed}_uniform_budget{budget}"] = int(
                            outcomes_by_policy[("hash_all", seed)][budget]
                        )
                observations.append(row)
            lookup = {
                row["observed_D"]: row for row in observations
                if row["system_id"] == sid and row["release_axis"] == axis
            }
            for G, group in sorted(original_groups.items()):
                cases = enumerated_observations(G)
                row = {
                    "system_id": sid, "original_G": G,
                    "release_axis": axis,
                    "n_candidate_masks_in_original_G": len(group),
                    "possible_D_variants": len(cases),
                    "exact_G_direction_identified": int(
                        len({labels[w["world_id"]] for w in group}) == 1
                    ),
                }
                for policy in POLICIES:
                    for budget in BUDGETS:
                        row[f"{policy}_robust_budget{budget}"] = int(all(
                            lookup[D][f"{policy}_uniform_budget{budget}"]
                            for D in cases
                        ))
                for seed in SEEDS:
                    for budget in BUDGETS:
                        row[f"hash_{seed}_robust_budget{budget}"] = int(all(
                            lookup[D][f"hash_{seed}_uniform_budget{budget}"]
                            for D in cases
                        ))
                true_G.append(row)
            provenance.append({
                "system_id": sid, "release_axis": axis,
                "n_exact_G": len(original),
                "perfect_G_direction_known": perfect_known,
                "n_observed_D": len(observed),
                "n_cross_G_observed_D": sum(
                    len({w["G_bits"] for w in group}) > 1
                    for group in observed.values()
                ),
            })
    if source_worlds != 768 or G_classes != 129:
        raise AssertionError("original finite-world roster changed")
    summaries = []
    for axis in AXES:
        obs = [r for r in observations if r["release_axis"] == axis]
        truths = [r for r in true_G if r["release_axis"] == axis]
        if len(truths) != 129:
            raise AssertionError("original G denominator drift")
        result = {
            "release_axis": axis,
            "unique_observation_fibres": len(obs),
            "fibre_has_multiple_possible_G": sum(
                r["n_true_G_candidates"] > 1 for r in obs
            ),
            "fibre_direction_ambiguous": sum(
                r["sign_ambiguous_before_assays"] for r in obs
            ),
            "exact_G_baseline_known": sum(
                r["exact_G_direction_identified"] for r in truths
            ),
        }
        for policy in POLICIES:
            result[f"{policy}_uniform_D_by_budget"] = [
                sum(r[f"{policy}_uniform_budget{b}"] for r in obs)
                for b in BUDGETS
            ]
            result[f"{policy}_robust_true_G_by_budget"] = [
                sum(r[f"{policy}_robust_budget{b}"] for r in truths)
                for b in BUDGETS
            ]
        for field, rows, suffix in (
            ("hash_uniform_D_by_budget", obs, "uniform"),
            ("hash_robust_true_G_by_budget", truths, "robust"),
        ):
            per_budget = [
                [sum(r[f"hash_{seed}_{suffix}_budget{b}"] for r in rows)
                 for seed in SEEDS]
                for b in BUDGETS
            ]
            result[field] = {
                "median": [float(np.median(v)) for v in per_budget],
                "min": [min(v) for v in per_budget],
                "max": [max(v) for v in per_budget],
            }
        summaries.append(result)
    assert {r["release_axis"]: r["exact_G_baseline_known"]
            for r in summaries} == {"A": 119, "B": 124, "M": 121}
    report = {
        "schema": "eog.bam_one_missed_G_v1.result",
        "status": "RETROSPECTIVE_EXPLORATORY_FINITE_WORLD_SINGLE_FALSE_NEGATIVE",
        "protocol_commit": PROTOCOL_COMMIT,
        "systems": 12, "original_worlds": 768,
        "original_exact_G_fibres": 129,
        "observation_model": "at most one missed occupied cell in otherwise complete map; no false positives",
        "assay": "perfect local A/B/M binary measurements, budgets 0..3",
        "results": summaries,
        "limits": [
            "Assumes otherwise complete reliable landscape census with <=1 missed positive; not unconstrained presence-only records.",
            "Previously constructed worlds and exposed outcomes; not independent ecology or confirmatory p values.",
            "Equal-cost perfect local A/B/M assays and fixed candidate universe; omitted mechanisms can invalidate certainty.",
            "Observed-D patterns and exact-G classes nested in 12 synthetic landscapes, not independent field replicates.",
            "Full-census original EOG span under static idealised axis release, not actual niche breadth or dispersal.",
        ],
    }
    report["fingerprint"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()
    ).hexdigest()
    return report, observations, true_G, provenance


def write_csv(path, rows):
    if not rows:
        raise ValueError("empty audit table")
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="previously frozen offline virtual-world fixture")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    systems = (
        json.loads(Path(args.fixture).read_text())
        if args.fixture else parent.canonical_systems()
    )
    report, observations, true_G, provenance = evaluate(systems)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_csv(output / "observed_fibres.csv", observations)
    write_csv(output / "original_G_robustness.csv", true_G)
    write_csv(output / "system_summary.csv", provenance)
    print("ONE_MISS_SUMMARY=" + json.dumps({
        "results": report["results"],
        "fingerprint": report["fingerprint"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
