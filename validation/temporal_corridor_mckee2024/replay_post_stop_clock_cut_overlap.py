#!/usr/bin/env python3
"""Pairwise structural comparison of two conditional source-clock cut masks.

From the original publisher-SHA-verified 12h McKee ZIP only. Reuses the
precommitted T0 full-day and T1 near-midnight scenarios and deterministic
within-individual-season ordering. This is NOT a biological corridor result.
Never exports per-record or per-animal cut positions, timestamps or IDs.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from replay_post_stop_time_interval_qc import _source_rows, SHA256
from replay_post_stop_global_time_windows import _windows
from replay_post_stop_bbmm_clock_segmentation import (
    split_sequence, pair_possible, all_clock_assignments_admit_pair
)

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_clock_cut_overlap_protocol_v1.json"
SOURCE_LINKS = 28532


def _check_protocol():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        p.get("schema") != "eog.mckee2024.post_stop_clock_cut_location_overlap.v1"
        or p.get("status") != "FROZEN_BEFORE_CROSS_SCENARIO_CUT_LOCATION_COMPARISON"
        or p["source"]["sha256"] != SHA256
        or p["source"]["within_group_adjacent_links"] != SOURCE_LINKS
        or p["source"]["groups"] != 421
        or p["heldout_2h_access"] is not False
    ):
        raise ValueError("Frozen source or cut-mask comparison protocol changed")
    return p


def compare_cut_sets(a, b, n_links):
    """Exact 2x2 paired table: both cut, A-only, B-only, both retained."""
    a, b = set(a), set(b)
    if isinstance(n_links, bool) or not isinstance(n_links, int) or n_links < 0:
        raise ValueError("n_links must be a nonnegative integer")
    if any(not isinstance(k, int) or isinstance(k, bool) or k < 1 or k > n_links for k in a | b):
        raise ValueError("Cut index outside allowed consecutive source pair range")
    common = len(a & b)
    exclusive_a = len(a - b)
    exclusive_b = len(b - a)
    both_keep = n_links - len(a | b)
    return {
        "cut_both": common,
        "cut_T0_only": exclusive_a,
        "cut_T1_only": exclusive_b,
        "retained_both": both_keep,
    }


def _t0_status(left, right):
    if all_clock_assignments_admit_pair(left, right):
        return "robust"
    if pair_possible(left, right):
        return "contingent"
    return "excluded"


def audit(groups):
    _check_protocol()
    if len(groups) != 421 or sum(len(group) for group in groups.values()) != 28953:
        raise ValueError("Original source cohort changed")
    counts, groups_counts = Counter(), Counter()
    status0, status1 = Counter(), Counter()
    for records in groups.values():
        t0 = _windows(records, 1)
        t1 = _windows(records, 2)
        assert len(t0) == len(t1) == len(records)
        cut0 = set(split_sequence(t0, "coherent")[1])
        cut1 = set(split_sequence(t1, "coherent")[1])
        # The previous source gate independently certified T1's
        # pairwise and globally coherent cuts as identical.
        if cut1 != set(split_sequence(t1, "optimistic")[1]):
            raise AssertionError("Source T1 coherent and optimistic cuts differ")
        table = compare_cut_sets(cut0, cut1, len(records)-1)
        counts.update(table)
        counts["groups_total"] += 1
        counts["links_total"] += len(records)-1
        groups_counts["groups_with_cut_disagreement"] += int(cut0 != cut1)
        groups_counts["groups_with_T0_only_cut"] += int(bool(cut0 - cut1))
        groups_counts["groups_with_T1_only_cut"] += int(bool(cut1 - cut0))
        for index in cut0 - cut1:
            status0[_t0_status(t0[index-1], t0[index])] += 1
        for index in cut1 - cut0:
            status1[_t0_status(t0[index-1], t0[index])] += 1

    n0 = counts["cut_both"] + counts["cut_T0_only"]
    n1 = counts["cut_both"] + counts["cut_T1_only"]
    if n0 != 857 or n1 != 858 or counts["links_total"] != SOURCE_LINKS:
        raise ValueError("Frozen PR #750 cross-scenario cut denominator mismatch")
    if sum(counts[k] for k in ("cut_both", "cut_T0_only", "cut_T1_only", "retained_both")) != SOURCE_LINKS:
        raise AssertionError("Cut/retention table does not partition original source links")

    bothcut = counts["cut_both"]
    unioncut = bothcut + counts["cut_T0_only"] + counts["cut_T1_only"]
    retainedunion = SOURCE_LINKS - bothcut
    return {
        "schema": "eog.mckee2024.post_stop_clock_cut_location_overlap_receipt.v1",
        "status": "CONDITIONAL_TWO_CLOCK_SCENARIO_CUT_OVERLAP__SOURCE_STOPS_RETAINED",
        "source_sha256_verified": True,
        "source_sha256": SHA256,
        "source_file_bytes": 1539661,
        "source_records": 28953,
        "source_groups": counts["groups_total"],
        "consecutive_link_count": counts["links_total"],
        "T0_full_day_coherent_cuts": n0,
        "T1_near_midnight_coherent_and_optimistic_cuts": n1,
        "link_cut_retention_table": {
            key: counts[key] for key in (
                "cut_both", "cut_T0_only", "cut_T1_only", "retained_both"
            )
        },
        "cut_jaccard": bothcut / unioncut if unioncut else None,
        "retained_link_jaccard": counts["retained_both"] / retainedunion
        if retainedunion else None,
        "groups_with_any_cut_disagreement": groups_counts["groups_with_cut_disagreement"],
        "groups_with_T0_only_cut": groups_counts["groups_with_T0_only_cut"],
        "groups_with_T1_only_cut": groups_counts["groups_with_T1_only_cut"],
        "T0_only_cuts_by_T0_pair_status": dict(sorted(status0.items())),
        "T1_only_cuts_by_T0_pair_status": dict(sorted(status1.items())),
        "actual_BBMM_or_movement_path_fitted": False,
        "author_exact_date_only_clock_verified": False,
        "source_CRS_author_verified": False,
        "dense_2h_GPS_accessed": False,
        "SHP_geometry_or_coordinates_accessed": False,
        "individual_IDs_exact_times_or_links_exported": False,
        "EOG_predictive_score_computed": False,
        "EOG_WF_scored_count_unchanged": 3,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    groups, _ = _source_rows(args.source_zip)
    result = audit(groups)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
