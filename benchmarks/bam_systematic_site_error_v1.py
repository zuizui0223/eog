"""Exact site-distinct A/B/M panels robust to one systematic geographic-site error.

Reuses original 12x64 BAM known-truth worlds and original M-release EOG span
target. A physical site returns its A/B/M triple; at most one site can return
an arbitrarily wrong triple. Repeating any measurements *at the same site*
does not create an independent error-correcting observation.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csc_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from benchmarks import bam_one_bit_error_v1 as previous  # noqa: E402

BUDGETS = (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 15)
CONTRACT_COMMIT = "ea93275c5de2b86578f3eebf2d9a4123a8cf4905"


def site_profile(state, node):
    """Three local A/B/M Boolean values encoded as an integer from 0 to 7."""
    return sum(
        (((int(mask) >> node) & 1) << axis)
        for axis, mask in enumerate(state["masks"])
    )


def distinct_sign_pairs(states):
    return [
        (i, j)
        for i in range(len(states))
        for j in range(i + 1, len(states))
        if int(states[i]["sign"]) != int(states[j]["sign"])
    ]


def validate_all_site_corruptions(states, sites, corrupt_sites=1):
    """Independent finite decoder for all truth and all one-site corruptions.

    A wrong site can arbitrarily change its whole A/B/M triple (7 possible
    alternative three-bit profiles). This decoder is independent of the MILP
    separation constraints and refuses conflicting response signs.
    """
    if corrupt_sites not in (0, 1) or len(sites) != len(set(sites)):
        raise ValueError("only zero/one site corruption and unique sites supported")
    signatures = [
        tuple(site_profile(state, site) for site in sites)
        for state in states
    ]
    for truth, truth_signature in zip(states, signatures):
        possible_records = [truth_signature]
        if corrupt_sites:
            for site_index in range(len(sites)):
                for fake_profile in range(8):
                    if fake_profile == truth_signature[site_index]:
                        continue
                    possible_records.append(
                        truth_signature[:site_index] + (fake_profile,)
                        + truth_signature[site_index + 1:]
                    )
        for record in possible_records:
            compatible = [
                int(candidate["sign"])
                for candidate, signature in zip(states, signatures)
                if sum(a != b for a, b in zip(record, signature))
                <= corrupt_sites
            ]
            if (
                int(truth["sign"]) not in compatible
                or len(set(compatible)) != 1
            ):
                return False
    return True


def min_site_panel(states, n_nodes, corrupt_sites=1):
    """Exact min # distinct full-profile geographic sites, nonadaptive.

    Every pair of opposite-sign candidate worlds must differ at >=
    2*corrupt_sites+1 selected GEOGRAPHIC nodes. One node has 3 axis bits
    but counts as ONE site. Return IMPOSSIBLE if the whole grid cannot
    separate a pair at that distance. Do not interpret as solver failure.
    """
    if corrupt_sites not in (0, 1) or not isinstance(n_nodes, int) or n_nodes < 1:
        raise ValueError("invalid error limit / grid dimension")
    if not states:
        raise ValueError("candidate finite state set is empty")
    if any(
        s["sign"] not in (-1, 0, 1)
        or len(s["masks"]) != 3
        or any(
            not isinstance(mask, (int, np.integer))
            or int(mask) < 0 or int(mask) >> n_nodes
            for mask in s["masks"]
        )
        for s in states
    ):
        raise ValueError("invalid three-axis mask or target sign")
    signatures = [tuple(map(int, s["masks"])) for s in states]
    if len(signatures) != len(set(signatures)):
        raise ValueError("deduplicate identical BAM triples before site optimization")
    pairs = distinct_sign_pairs(states)
    if not pairs:
        return {
            "status":"OPTIMAL", "minimum_sites":0, "minimum_axis_readings":0,
            "sites":[], "discordant_pairs":0,
            "min_pairwise_separating_sites":None,
            "corrupt_sites":corrupt_sites,
        }
    separation_masks = []
    for i, j in pairs:
        left, right = signatures[i], signatures[j]
        separation_masks.append(
            (left[0] ^ right[0])
            | (left[1] ^ right[1])
            | (left[2] ^ right[2])
        )
    minimum_available = min(mask.bit_count() for mask in separation_masks)
    need = 2 * corrupt_sites + 1
    if minimum_available < need:
        return {
            "status":"IMPOSSIBLE", "minimum_sites":None,
            "minimum_axis_readings":None, "sites":None,
            "discordant_pairs":len(pairs),
            "min_pairwise_separating_sites":minimum_available,
            "corrupt_sites":corrupt_sites,
        }

    # Each binary decision variable represents one PHYSICAL node, never a
    # repeated read or one axis measurement. Do not deduplicate columns:
    # different geographic sites with the same separation pattern are
    # independent under this specific one-bad-site model.
    matrix = np.asarray([
        [(mask >> site) & 1 for site in range(n_nodes)]
        for mask in separation_masks
    ], dtype=float)
    result = milp(
        c=np.ones(n_nodes),
        integrality=np.ones(n_nodes),
        bounds=Bounds(np.zeros(n_nodes), np.ones(n_nodes)),
        constraints=LinearConstraint(
            csc_matrix(matrix),
            np.full(len(pairs), need, dtype=float),
            np.full(len(pairs), np.inf, dtype=float),
        ),
        options={"mip_rel_gap":0.0, "time_limit":25.0},
    )
    if result.status != 0 or result.x is None:
        raise RuntimeError(f"nonoptimal exact physical-site MILP: {result.message}")
    values = np.rint(result.x).astype(int)
    if (
        any(abs(actual - rounded) > 1e-6
            for actual, rounded in zip(result.x, values))
        or (matrix @ values < need - 1e-8).any()
    ):
        raise AssertionError("chosen geographic site set does not separate targets")
    sites = [int(i) for i in np.flatnonzero(values)]
    if not validate_all_site_corruptions(states, sites, corrupt_sites):
        raise AssertionError("independent site-block error decoder rejected panel")
    return {
        "status":"OPTIMAL", "minimum_sites":len(sites),
        "minimum_axis_readings":3 * len(sites),
        "sites":sites, "discordant_pairs":len(pairs),
        "min_pairwise_separating_sites":minimum_available,
        "corrupt_sites":corrupt_sites,
    }


def analyze(systems):
    if len(systems) != 12:
        raise AssertionError("must replay all original 12 landscapes")
    rows, per_G = [], defaultdict(list)
    n_worlds = n_true_G = original_exact_identified = 0
    for system in systems:
        sid = system["system_id"]
        n_nodes = int(system["width"] * system["height"])
        if len(system["worlds"]) != 64:
            raise AssertionError("source world roster not 64 in each landscape")
        by_G, labels, n_known = previous.signs_M(system)
        n_worlds += len(system["worlds"])
        n_true_G += len(by_G)
        original_exact_identified += n_known
        by_D = defaultdict(list)
        for G, candidates in by_G.items():
            for D in previous.observations(G):
                by_D[D].extend(candidates)
        for D, candidates in sorted(by_D.items()):
            states = previous.states_with_signs(candidates, labels)
            no_error = min_site_panel(states, n_nodes, corrupt_sites=0)
            robust = min_site_panel(states, n_nodes, corrupt_sites=1)
            if no_error["status"] != "OPTIMAL":
                raise AssertionError("zero-error complete site profile unexpectedly infeasible")
            if robust["status"] == "OPTIMAL" and (
                robust["minimum_sites"] < no_error["minimum_sites"]
                or robust["minimum_sites"] > 3 * no_error["minimum_sites"]
            ):
                raise AssertionError("site-corruption site-cost monotonicity failed")
            row = {
                "system_id":sid, "observed_D":D,
                "n_parameter_worlds":len(candidates),
                "n_distinct_mask_triples":len(states),
                "n_candidate_true_G":len({r["G_bits"] for r in candidates}),
                "target_discordant_pairs":robust["discordant_pairs"],
                "zero_error_min_distinct_sites":no_error["minimum_sites"],
                "systematic_one_bad_site_status":robust["status"],
                "systematic_one_bad_site_min_distinct_sites":robust["minimum_sites"],
                "systematic_one_bad_site_axis_reads":robust["minimum_axis_readings"],
                "systematic_one_bad_site_sites":(
                    "" if robust["sites"] is None
                    else ";".join(map(str, robust["sites"]))
                ),
                "least_available_separating_site_count":robust["min_pairwise_separating_sites"],
            }
            rows.append(row)
            for G in {int(x["G_bits"]) for x in candidates}:
                per_G[(sid, G)].append(row)
    if (
        n_worlds, n_true_G, len(rows), len(per_G), original_exact_identified
    ) != (768, 129, 2627, 129, 121):
        raise AssertionError("canonical 12x64/129/2627/121 source drift")
    counts = Counter(row["systematic_one_bad_site_status"] for row in rows)
    feasible = [
        row for row in rows if row["systematic_one_bad_site_status"] == "OPTIMAL"
    ]
    min_hist = Counter(
        row["systematic_one_bad_site_min_distinct_sites"] for row in feasible
    )
    impossible = [
        row for row in rows if row["systematic_one_bad_site_status"] == "IMPOSSIBLE"
    ]
    max_by_G = {
        key: (
            None if any(r["systematic_one_bad_site_status"] == "IMPOSSIBLE"
                        for r in group)
            else max(r["systematic_one_bad_site_min_distinct_sites"]
                     for r in group)
        )
        for key, group in per_G.items()
    }
    result = {
        "schema":"eog.bam_one_systematic_geographic_site_error_v1.result",
        "scope":"POST_EXPOSURE_EXPLORATORY_FINITE_WORLD_NONADAPTIVE",
        "protocol_commit":CONTRACT_COMMIT,
        "source":{
            "landscapes":12,"parameter_worlds":768,
            "true_G_classes":129,"observed_D_classes":2627,
            "perfect_G_M_sign_identified":121,
        },
        "error_model":"At most one complete geographic site's joint A/B/M triple is adversarially wrong; independent geographical sites, no same-site replication credit.",
        "site_budgets":list(BUDGETS),
        "status_counts":dict(sorted(counts.items())),
        "min_distinct_sites_histogram":{
            str(k):v for k,v in sorted(min_hist.items())
        },
        "impossible_observed_D":len(impossible),
        "impossible_true_G_classes":sum(v is None for v in max_by_G.values()),
        "max_site_cost_among_feasible_D":max(min_hist),
        "robust_observed_D_by_site_budget":{
            str(b):sum(r["systematic_one_bad_site_min_distinct_sites"] <= b
                       for r in feasible)
            for b in BUDGETS
        },
        "robust_true_G_by_site_budget":{
            str(b):sum(v is not None and v <= b for v in max_by_G.values())
            for b in BUDGETS
        },
        "zero_error_site_min_histogram":{
            str(k):v for k,v in sorted(Counter(
                r["zero_error_min_distinct_sites"] for r in rows
            ).items())
        },
        "impossibility_examples":[
            {"system_id":row["system_id"],
             "D":row["observed_D"],
             "available_separating_sites":row["least_available_separating_site_count"]}
            for row in impossible[:10]
        ],
        "limits":[
            "Same exposed 12 synthetic BAM landscapes; no independent ecological evidence.",
            "Each assay queries all three A/B/M bits at a geographic site; costs one site and three axis readings.",
            "At most one whole site block can be wrong; independent spatial locations assumed.",
            "IMPOSSIBLE means structurally unidentifiable under this candidate set and error bound, not impossible in nature.",
            "Nonadaptive optimal site set, not adaptive or realistic multivisit sampling.",
            "D has at most one missed occupied site; no probabilistic detection and no system-wide omission.",
            "Original full-census EOG M-release span, not actual dispersal or causal change.",
        ],
    }
    raw = json.dumps(result, sort_keys=True, separators=(",", ":"),
                     allow_nan=False)
    result["fingerprint"] = hashlib.sha256(raw.encode()).hexdigest()
    return result, rows, max_by_G


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--fixture", type=Path, help="preexisting frozen canonical worlds")
    a = p.parse_args()
    systems = (
        json.loads(a.fixture.read_text(encoding="utf-8"))
        if a.fixture else previous.parent.canonical_systems()
    )
    result, rows, max_by_G = analyze(systems)
    out = a.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "observed_D_site_panels.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (out / "true_G_site_costs.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=[
            "system_id", "G", "minimum_worst_site_cost", "status"
        ])
        writer.writeheader()
        for (sid, G), cost in sorted(max_by_G.items()):
            writer.writerow({
                "system_id":sid,"G":G,
                "minimum_worst_site_cost":cost if cost is not None else "",
                "status":"IMPOSSIBLE" if cost is None else "OPTIMAL",
            })
    print("BAM_SYSTEMATIC_SITE_ERROR=" + json.dumps({
        "status_counts":result["status_counts"],
        "min_sites_histogram":result["min_distinct_sites_histogram"],
        "robust_G":result["robust_true_G_by_site_budget"],
        "fingerprint":result["fingerprint"],
    },sort_keys=True,allow_nan=False))


if __name__ == "__main__":
    main()
