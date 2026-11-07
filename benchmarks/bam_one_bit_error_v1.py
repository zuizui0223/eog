"""One-bit assay error tolerance via exact finite-world multicover.

At most ONE individual recorded A/B/M binary reading can be flipped per
nonadaptive panel. Repeating a test counts as another read. These are
previously exposed synthetic worlds, not ecological replicates.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_geometry_response_envelopes_v1 as parent  # noqa: E402

AXES = ("A", "B", "M")
BUDGETS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 12)
PROTOCOL_COMMIT = "31f0f391ebd2c818092dade2ef891d53dae5bc46"


def site_bit(state, test):
    axis, node = test
    return (int(state["masks"][AXES.index(axis)]) >> int(node)) & 1


def cross_pairs(states):
    return [
        (i, j) for i in range(len(states)) for j in range(i + 1, len(states))
        if int(states[i]["sign"]) != int(states[j]["sign"])
    ]


def check_error_correction(states, readings, errors=1):
    """Independently enumerate all true outcomes and <=1 flipped readout."""
    if errors not in (0, 1):
        raise ValueError("only zero or one error supported")
    tests = []
    for label in readings:
        axis, node = label.split(":")
        tests.append((axis, int(node)))
    patterns = [tuple(site_bit(s, t) for t in tests) for s in states]
    for i, truth in enumerate(states):
        observations = [patterns[i]]
        if errors:
            observations += [
                patterns[i][:k] + (1 - patterns[i][k],) + patterns[i][k + 1:]
                for k in range(len(tests))
            ]
        for observed in observations:
            eligible = [
                s["sign"] for s, p in zip(states, patterns)
                if sum(a != b for a, b in zip(observed, p)) <= errors
            ]
            if int(truth["sign"]) not in eligible or len(set(eligible)) != 1:
                return False
    return True


def exact_fixed_panel(states, n_nodes, errors=1):
    """Minimum nonadaptive multiset with target-code distance >= 2e+1.

    Integer multi-cover is globally optimal only within this fixed,
    equal-cost, repeatable-assay model. Every solution is independently
    certified by explicit error-string enumeration.
    """
    if errors not in (0, 1) or not isinstance(n_nodes, int) or n_nodes < 1:
        raise ValueError("invalid error limit or grid size")
    if not states:
        raise ValueError("empty candidate set")
    if any(
        s["sign"] not in (-1, 0, 1) or len(s["masks"]) != 3
        or any(int(m) < 0 or int(m) >> n_nodes for m in s["masks"])
        for s in states
    ):
        raise ValueError("invalid candidate mask or target sign")
    pairs = cross_pairs(states)
    if not pairs:
        return {
            "minimum_reads": 0, "unique_tests": 0, "readings": [],
            "discordant_pairs": 0, "error_limit": errors, "optimal": True
        }
    need = 2 * errors + 1
    # Equal pair-separation columns are interchangeable under this
    # particular individual-read error model; keep first axis/node.
    signature_map = {}
    for axis in AXES:
        for node in range(n_nodes):
            test = (axis, node)
            signature = tuple(
                int(site_bit(states[i], test) != site_bit(states[j], test))
                for i, j in pairs
            )
            if any(signature):
                signature_map.setdefault(signature, test)
    if not signature_map:
        raise ValueError("distinct signs without discriminating site")
    signatures = list(signature_map)
    matrix = np.asarray(signatures, dtype=float).T
    n_vars = len(signatures)
    result = milp(
        c=np.ones(n_vars),
        integrality=np.ones(n_vars),
        bounds=Bounds(np.zeros(n_vars), np.full(n_vars, need)),
        constraints=LinearConstraint(
            csc_matrix(matrix),
            np.full(len(pairs), need),
            np.full(len(pairs), np.inf)
        ),
        options={"mip_rel_gap": 0.0, "time_limit": 25.0},
    )
    if result.status != 0 or result.x is None:
        raise RuntimeError(f"nonoptimal source MILP: {result.message}")
    chosen = np.rint(result.x).astype(int)
    if (
        any(abs(a - b) > 1e-6 for a, b in zip(result.x, chosen))
        or (matrix @ chosen < need - 1e-8).any()
    ):
        raise AssertionError("invalid integer optimum certificate")
    readings = [
        f"{signature_map[s][0]}:{signature_map[s][1]}"
        for s, count in zip(signatures, chosen)
        for _ in range(count)
    ]
    if not check_error_correction(states, readings, errors):
        raise AssertionError("error-string enumeration rejected panel")
    return {
        "minimum_reads": int(sum(chosen)),
        "unique_tests": int(sum(chosen > 0)),
        "readings": readings, "discordant_pairs": len(pairs),
        "error_limit": errors, "optimal": True
    }


def observations(G):
    return (G,) + tuple(
        G & ~(1 << i) for i in range(G.bit_length()) if G & (1 << i)
    )


def states_with_signs(rows, signs):
    states = {}
    for row in rows:
        key = tuple(int(row[f"{a}_bits"]) for a in AXES)
        sign = int(signs[row["world_id"]])
        if key in states and states[key]["sign"] != sign:
            raise AssertionError("conflicting response for same BAM mask triple")
        states.setdefault(key, {"masks": key, "sign": sign, "n_labels": 0})
        states[key]["n_labels"] += 1
    return [states[k] for k in sorted(states)]


def signs_M(system):
    features = np.asarray(system["environment"], float)
    center = np.median(features, axis=0)
    scale = np.median(abs(features - center), axis=0) * 1.4826
    if not np.isfinite(features).all() or np.any(scale <= 0):
        raise ValueError("invalid frozen source environmental reference")
    z = (features - center) / scale
    groups, signs, cache = defaultdict(list), {}, {}
    for row in system["worlds"]:
        if int(row["A_bits"]) & int(row["B_bits"]) & int(row["M_bits"]) != int(row["G_bits"]):
            raise AssertionError("source G intersection changed")
        groups[int(row["G_bits"])].append(row)
    known = 0
    for G, rows in sorted(groups.items()):
        f = parent.fibre_summary(
            system["system_id"], rows, z, system["width"], system["height"],
            "M", cache
        )
        current = f["targets"]["span"]["current"]
        tolerance = parent.EPS * max(
            1., abs(current), *(abs(o["after"]["span"])
                               for o in f["world_outcomes"])
        )
        for outcome in f["world_outcomes"]:
            delta = outcome["changes"]["span"]
            signs[outcome["world_id"]] = (
                -1 if delta < -tolerance else 1 if delta > tolerance else 0
            )
        if (
            sorted({signs[row["world_id"]] for row in rows})
            != f["targets"]["span"]["directions"]
        ):
            raise AssertionError("parent response directions changed")
        known += int(f["targets"]["span"]["direction_identified"])
    return groups, signs, known


def analyze(systems):
    if len(systems) != 12:
        raise AssertionError("exact source 12 landscapes required")
    data, per_G = [], defaultdict(list)
    worlds = original_G = initial_known = 0
    for system in systems:
        sid, width, height = (
            system["system_id"], system["width"], system["height"]
        )
        n_nodes = width * height
        if len(system["worlds"]) != 64:
            raise AssertionError("exact parent 64 worlds per system required")
        groups, signs, known = signs_M(system)
        worlds += len(system["worlds"])
        original_G += len(groups)
        initial_known += known
        D_groups = defaultdict(list)
        for G, rows in groups.items():
            for D in observations(G):
                D_groups[D].extend(rows)
        for D, rows in sorted(D_groups.items()):
            states = states_with_signs(rows, signs)
            no_error = exact_fixed_panel(states, n_nodes, errors=0)
            one_error = exact_fixed_panel(states, n_nodes, errors=1)
            if one_error["minimum_reads"] > 3 * no_error["minimum_reads"]:
                raise AssertionError("triple-repeat upper bound violated")
            if one_error["minimum_reads"] in (1, 2):
                raise AssertionError("single-bit error cannot be corrected with <=2 reads")
            row = {
                "system_id": sid, "D": D,
                "possible_true_G": len({r["G_bits"] for r in rows}),
                "n_candidate_mask_triples": len(states),
                "n_parent_world_labels": len(rows),
                "n_discordant_pairs": one_error["discordant_pairs"],
                "zero_error_min_reads": no_error["minimum_reads"],
                "one_error_min_reads": one_error["minimum_reads"],
                "one_error_unique_tests": one_error["unique_tests"],
                "one_error_panel": ";".join(one_error["readings"]),
            }
            data.append(row)
            for G in {int(r["G_bits"]) for r in rows}:
                per_G[(sid, G)].append(row)
    if (worlds, original_G, len(data), len(per_G), initial_known) != (
        768, 129, 2627, 129, 121
    ):
        raise AssertionError("parent 12x64/129/2627/121 source roster drift")
    one_counts = Counter(r["one_error_min_reads"] for r in data)
    zero_counts = Counter(r["zero_error_min_reads"] for r in data)
    worst_G = {
        key: max(r["one_error_min_reads"] for r in rows)
        for key, rows in per_G.items()
    }
    result = {
        "schema": "eog.bam_assay_one_bit_error_v1.result",
        "scope": "KNOWN_TRUTH_POST_EXPOSURE_NONADAPTIVE_BINARY_ERROR_CORRECTION",
        "protocol_commit": PROTOCOL_COMMIT,
        "source": {
            "systems": 12, "worlds": 768,
            "exact_G_fibres": 129, "observed_D_fibres": 2627,
            "perfect_G_M_direction_known": initial_known,
        },
        "error_model": "At most one flipped individual assay reading across a fixed nonadaptive panel; repeats allowed",
        "budgets": list(BUDGETS),
        "one_error_reads_histogram": dict(sorted(one_counts.items())),
        "no_error_reads_histogram": dict(sorted(zero_counts.items())),
        "one_error_observation_fibres_by_budget": {
            str(b): sum(r["one_error_min_reads"] <= b for r in data)
            for b in BUDGETS
        },
        "one_error_robust_true_G_by_budget": {
            str(b): sum(v <= b for v in worst_G.values())
            for b in BUDGETS
        },
        "max_exact_nonadaptive_one_error_reads": max(one_counts),
        "n_positive_error_cost_D": sum(
            r["one_error_min_reads"] > r["zero_error_min_reads"] for r in data
        ),
        "limits": [
            "No actual field errors; bounded one wrong reading not one systematically wrong site.",
            "Exact optimum nonadaptive panel, not adaptive decision-tree complexity.",
            "All original worlds exposed; no independent ecological validation.",
            "Full current G except <=1 false-negative occupied cell, not general effort-limited occurrence.",
            "EOG span under ideal static M release, not a causal range forecast.",
        ],
    }
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False)
    result["fingerprint"] = sha256(raw.encode()).hexdigest()
    return result, data, worst_G


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, help="offline frozen fixture; original generator used if omitted")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    systems = (
        json.loads(args.fixture.read_text()) if args.fixture
        else parent.canonical_systems()
    )
    result, rows, worst = analyze(systems)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n",
        encoding="utf-8"
    )
    with (out / "observed_D_panels.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (out / "true_G_max_cost.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "system_id", "G", "worst_one_error_reads"
        ])
        writer.writeheader()
        writer.writerows(
            {"system_id": sid, "G": G, "worst_one_error_reads": count}
            for (sid, G), count in sorted(worst.items())
        )
    print("BAM_BIT_ERROR=" + json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
