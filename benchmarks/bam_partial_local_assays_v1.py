"""Response-blind local BAM assays for geometric-response identification.

Exploratory finite-world reuse; not field inference or a biological intervention.
Protocol: validation/bam_partial_local_assay_v1/protocol_v1.json.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_geometry_response_envelopes_v1 as parent  # noqa: E402

AXES = ("A", "B", "M")
SEEDS = tuple(range(20261107, 20261123))
MAX_BUDGET = 3
CONTRACT_COMMIT = "95cd3ca57041983f2c8037768a3f75d8dfe8438c"


def deduplicate_states(rows, labels):
    grouped = {}
    for row in rows:
        key = tuple(int(row[f"{a}_bits"]) for a in AXES)
        value = int(labels[row["world_id"]])
        if value not in (-1, 0, 1):
            raise ValueError("unexpected target sign")
        if key not in grouped:
            grouped[key] = {"mask": key, "sign": value, "world_ids": []}
        elif grouped[key]["sign"] != value:
            raise ValueError("conflicting target sign for identical BAM masks")
        grouped[key]["world_ids"].append(str(row["world_id"]))
    for value in grouped.values():
        value["world_ids"].sort()
    return [grouped[k] for k in sorted(grouped)]


def query_bit(state, test):
    axis, node = test
    return (state["mask"][AXES.index(axis)] >> node) & 1


def disagreement_pairs(states, test):
    left = Counter(s["sign"] for s in states if query_bit(s, test) == 0)
    right = Counter(s["sign"] for s in states if query_bit(s, test) == 1)
    return sum(v * n for k, v in left.items() for j, n in right.items() if k != j)


def candidate_queries(states, n_nodes, allowed=AXES):
    for axis in allowed:
        for node in range(n_nodes):
            test = (axis, node)
            if len({query_bit(s, test) for s in states}) > 1:
                yield test


def choose_greedy(states, n_nodes, allowed=AXES, used=()):
    if len({s["sign"] for s in states}) <= 1:
        return None
    used = set(used)
    best, maximum = None, 0
    for test in candidate_queries(states, n_nodes, allowed):
        if test in used:
            continue
        score = disagreement_pairs(states, test)
        # The fixed axis and row-major order breaks ties without truth lookahead.
        if score > maximum:
            best, maximum = test, score
    return best


def choose_hash(states, n_nodes, seed, system_id, G, target_axis, used=()):
    if len({s["sign"] for s in states}) <= 1:
        return None
    used = set(used)
    possible = [test for test in candidate_queries(states, n_nodes) if test not in used]
    return min(
        possible,
        key=lambda test: (
            hashlib.sha256(
                f"{seed}|{system_id}|{G}|{target_axis}|{test[0]}|{test[1]}".encode()
            ).hexdigest(),
            test,
        ),
    ) if possible else None


def simulate_policy(states, *, truth, n_nodes, policy, seed, system_id, G,
                    target_axis, budget=3):
    if budget < 0:
        raise ValueError("negative budget")
    if truth["mask"] not in [s["mask"] for s in states]:
        raise ValueError("truth not within current-G fibre")
    living = list(states)
    used, steps = [], []
    for b in range(budget + 1):
        if truth["mask"] not in [s["mask"] for s in living]:
            raise AssertionError("observed test eliminated simulated truth")
        identified = len({s["sign"] for s in living}) == 1
        test = None
        if b < budget and not identified:
            if policy == "greedy_all":
                test = choose_greedy(living, n_nodes, AXES, used)
            elif policy == "greedy_A":
                test = choose_greedy(living, n_nodes, ("A",), used)
            elif policy == "greedy_B":
                test = choose_greedy(living, n_nodes, ("B",), used)
            elif policy == "hash_all":
                test = choose_hash(living, n_nodes, seed, system_id, G, target_axis, used)
            else:
                raise ValueError("unknown assay selection policy")
        steps.append({
            "budget": b,
            "identified": identified,
            "n_remaining": len(living),
            "test": None if test is None else f"{test[0]}:{test[1]}",
            "candidate_signs": tuple(sorted({s["sign"] for s in living})),
        })
        if test is not None:
            observed_bit = query_bit(truth, test)
            revised = [s for s in living if query_bit(s, test) == observed_bit]
            if not revised or len(revised) > len(living):
                raise AssertionError("invalid posterior finite-world contraction")
            living = revised
            used.append(test)
    flags = [s["identified"] for s in steps]
    if flags != sorted(flags):
        raise AssertionError("direction identification lost after evidence")
    return {"steps": steps, "used_sites": [f"{a}:{node}" for a, node in used]}


def signs_from_parent(sid, rows, z, width, height, axis, cache):
    result = parent.fibre_summary(sid, rows, z, width, height, axis, cache)
    deltas = {r["world_id"]: r["changes"]["span"] for r in result["world_outcomes"]}
    current = result["targets"]["span"]["current"]
    tolerance = parent.EPS * max(
        1.0, abs(current), *(abs(current + delta) for delta in deltas.values())
    )
    labels = {
        key: -1 if delta < -tolerance else 1 if delta > tolerance else 0
        for key, delta in deltas.items()
    }
    if sorted(set(labels.values())) != result["targets"]["span"]["directions"]:
        raise AssertionError("parent target direction classification changed")
    return result, labels


def run(systems, *, seeds=SEEDS, budget=MAX_BUDGET):
    if budget != 3 or tuple(seeds) != SEEDS:
        raise ValueError("precommitted budget or seed roster changed")
    records, trajectories, aggregates = [], [], []
    n_fibres = n_worlds = n_mask_ambiguous = n_M_ambiguous = n_M_opposite = 0
    for system in systems:
        sid = system["system_id"]
        env = np.asarray(system["environment"], dtype=float)
        median = np.median(env, axis=0)
        scale = np.median(np.abs(env - median), axis=0) * 1.4826
        if np.any(scale <= 0):
            raise ValueError("unqualified frozen MAD reference")
        z = (env - median) / scale
        width, height = system["width"], system["height"]
        n_nodes = width * height
        groups, metric_cache = defaultdict(list), {}
        for row in system["worlds"]:
            if int(row["G_bits"]) != (
                int(row["A_bits"]) & int(row["B_bits"]) & int(row["M_bits"])
            ):
                raise ValueError("original BAM intersection changed")
            groups[int(row["G_bits"])].append(row)
        for G, rows in sorted(groups.items()):
            n_fibres += 1
            n_worlds += len(rows)
            n_unique = len({tuple(r[f"{a}_bits"] for a in AXES) for r in rows})
            n_mask_ambiguous += int(n_unique > 1)
            for release_axis in AXES:
                outcome, labels = signs_from_parent(
                    sid, rows, z, width, height, release_axis, metric_cache
                )
                states = deduplicate_states(rows, labels)
                if len(states) != n_unique:
                    raise AssertionError("mask signature deduplication mismatch")
                ambiguous = len({s["sign"] for s in states}) > 1
                if release_axis == "M":
                    n_M_ambiguous += int(ambiguous)
                    n_M_opposite += int(
                        -1 in {s["sign"] for s in states}
                        and 1 in {s["sign"] for s in states}
                    )
                policies = (
                    [("greedy_all", 0), ("greedy_B", 0), ("greedy_A", 0)]
                    + [("hash_all", seed) for seed in SEEDS]
                )
                for policy, seed in policies:
                    traces = [
                        simulate_policy(
                            states, truth=state, n_nodes=n_nodes, policy=policy,
                            seed=seed, system_id=sid, G=G,
                            target_axis=release_axis, budget=budget,
                        )
                        for state in states
                    ]
                    for b in range(budget + 1):
                        resolved = [
                            trace["steps"][b]["identified"] for trace in traces
                        ]
                        records.append({
                            "system_id": sid, "G_bits": G,
                            "release_axis": release_axis,
                            "initially_ambiguous": ambiguous,
                            "policy": policy, "seed": seed, "budget": b,
                            "n_mask_triples": len(states),
                            "n_original_world_labels": len(rows),
                            "uniformly_resolved": all(resolved),
                            "resolved_triples": sum(resolved),
                            "resolved_world_labels": sum(
                                len(state["world_ids"])
                                for state, yes in zip(states, resolved) if yes
                            ),
                        })
                    if ambiguous:
                        for state, trace in zip(states, traces):
                            for b, item in enumerate(trace["steps"]):
                                trajectories.append({
                                    "system_id": sid, "G_bits": G,
                                    "release_axis": release_axis,
                                    "truth_A_bits": state["mask"][0],
                                    "truth_B_bits": state["mask"][1],
                                    "truth_M_bits": state["mask"][2],
                                    "truth_sign": state["sign"],
                                    "n_parameter_labels": len(state["world_ids"]),
                                    "policy": policy, "seed": seed, "budget": b,
                                    "identified": item["identified"],
                                    "n_remaining": item["n_remaining"],
                                    "next_site": item["test"],
                                    "possible_signs": "/".join(
                                        map(str, item["candidate_signs"])
                                    ),
                                })
    if (
        len(systems) != 12 or n_fibres != 129
        or n_worlds != 768 or n_mask_ambiguous != 69
    ):
        raise AssertionError("parent 12x64 / 129 current G source drift")
    if n_M_ambiguous != 8 or n_M_opposite != 5:
        raise AssertionError("parent M-response ambiguity denominator drift")

    for axis in AXES:
        for policy in ("greedy_all", "greedy_B", "greedy_A", "hash_all"):
            for b in range(budget + 1):
                rows = [
                    r for r in records
                    if r["release_axis"] == axis
                    and r["policy"] == policy and r["budget"] == b
                ]
                by_seed = defaultdict(list)
                for row in rows:
                    by_seed[row["seed"]].append(row)
                tallies = []
                for seed, group in sorted(by_seed.items()):
                    tallies.append({
                        "seed": seed,
                        "uniform_all": sum(r["uniformly_resolved"] for r in group),
                        "uniform_initially_ambiguous": sum(
                            r["uniformly_resolved"]
                            for r in group if r["initially_ambiguous"]
                        ),
                        "resolved_unique_signatures": sum(
                            r["resolved_triples"] for r in group
                        ),
                        "resolved_world_labels": sum(
                            r["resolved_world_labels"] for r in group
                        ),
                        "initial_ambiguous": sum(
                            r["initially_ambiguous"] for r in group
                        ),
                    })
                aggregates.append({
                    "release_axis": axis, "policy": policy, "budget": b,
                    "uniform_all_median": float(
                        np.median([x["uniform_all"] for x in tallies])
                    ),
                    "uniform_all_min": min(x["uniform_all"] for x in tallies),
                    "uniform_all_max": max(x["uniform_all"] for x in tallies),
                    "uniform_initial_ambiguous_median": float(np.median([
                        x["uniform_initially_ambiguous"] for x in tallies
                    ])),
                    "resolved_unique_signatures_median": float(np.median([
                        x["resolved_unique_signatures"] for x in tallies
                    ])),
                    "original_world_labels_resolved_median": float(np.median([
                        x["resolved_world_labels"] for x in tallies
                    ])),
                    "n_seed_replays": len(tallies),
                    "initially_ambiguous_fibres": tallies[0]["initial_ambiguous"],
                })
    result = {
        "schema": "eog.bam_partial_local_assay_v1.result",
        "status": "POST_RESULT_EXPLORATORY_KNOWN_TRUTH_NOT_ECOLOGICAL_CONFIRMATION",
        "contract_commit": CONTRACT_COMMIT, "landscapes": len(systems),
        "worlds": n_worlds, "G_fibres": n_fibres,
        "mask_ambiguous_fibres": n_mask_ambiguous,
        "initial_M_sign_ambiguous": n_M_ambiguous,
        "initial_M_opposite_sign": n_M_opposite,
        "seed_roster": list(SEEDS), "max_budget": budget,
        "policy_by_budget": aggregates,
        "notes": [
            "Complete current G and noiseless A/B/M assays assumed; not measured in Charaxes.",
            "Site choice uses finite candidate target labels, never hidden true-world response.",
            "Sixteen deterministic hashes and 768 parameter labels are not natural replicates.",
            "Full-census mask release differs from earlier matched-size contrasts.",
        ],
    }
    result["fingerprint"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode()
    ).hexdigest()
    return result, records, trajectories


def write_csv(path, rows):
    if not rows:
        raise ValueError("empty audit output")
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", help="frozen offline prior source fixture")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    systems = (
        json.loads(Path(args.fixture).read_text())
        if args.fixture else parent.canonical_systems()
    )
    result, rows, trajectories = run(systems)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    write_csv(out / "fibre_budget.csv", rows)
    write_csv(out / "paths.csv", trajectories)
    (out / "summary_sha256.txt").write_text(
        hashlib.sha256((out / "summary.json").read_bytes()).hexdigest() + "\n"
    )
    print("BAM_PARTIAL_ASSAY_SUMMARY=" + json.dumps({
        "worlds": result["worlds"], "G_fibres": result["G_fibres"],
        "initial_M_sign_ambiguous": result["initial_M_sign_ambiguous"],
        "M_primary": [
            r for r in result["policy_by_budget"] if r["release_axis"] == "M"
        ],
        "fingerprint": result["fingerprint"],
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
