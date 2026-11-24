#!/usr/bin/env python3
"""Source-only BBMM clock-link segmentation for the exact McKee 12h original.

Stage protocol was frozen before segmentation. Read ONLY previously authorized
DBF herd/animal/season/time fields from the exact publisher-SHA 12h source.
No geometry, dates/identifiers in output, 2h holdout, EOG score or BBMM fit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from replay_post_stop_time_interval_qc import _source_rows, SHA256
from replay_post_stop_global_time_windows import _windows, pair_possible

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_bbmm_clock_segmentation_protocol_v1.json"
SCENARIOS = ("T0_FULL_DAY_UNCERTAINTY", "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW")
ARMS = ("optimistic", "coherent", "conservative")
MAX_GAP = 45000
SIZE_BINS = ("1", "2", "3-5", "6-11", "12-23", "24+")


def _validate():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        protocol.get("schema") != "eog.mckee2024.source_only_clock_bridge_segmentation.v1"
        or protocol.get("status") != "FROZEN_BEFORE_NEW_SEGMENTATION_COMPUTATION"
        or protocol["source"]["sha256"] != SHA256
        or protocol["source"]["record_count"] != 28953
        or protocol["source"]["group_count"] != 421
        or protocol["published_gap_rule"]["max_seconds"] != MAX_GAP
        or tuple(row["id"] for row in protocol["scenarios"]) != SCENARIOS
        or protocol["data_access"]["dense_2hour_holdout"] is not False
    ):
        raise ValueError("Frozen source/12.5h segmentation contract changed")
    return protocol


def all_clock_assignments_admit_pair(a, b, max_gap=MAX_GAP) -> bool:
    """The entire cartesian time-window product admits a positive <=12.5h gap."""
    return b[0] - a[1] >= 1 and b[1] - a[0] <= max_gap


def split_sequence(windows, arm: str, max_gap=MAX_GAP):
    """Return segment *lengths* and cut indices for one frozen-order series.

    The coherent arm is earliest-infeasible greedy interval propagation;
    its longest-prefix segmentation minimizes number of contiguous blocks,
    since dropping a prefix cannot destroy feasibility of a suffix.
    Other arms use linkwise existence/robustness without enforcing a shared
    assignment of the interior timestamps across links.
    """
    if not windows or arm not in ARMS:
        raise ValueError("Nonempty timestamp sequence and known arm required")
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < 1:
        raise ValueError("Positive integer-second gap threshold required")
    if any(lo > hi for lo, hi in windows):
        raise ValueError("Invalid empty time interval")
    segment_lengths = []
    cuts = []
    current_length = 1
    possible_lower, possible_upper = windows[0]
    for index, next_window in enumerate(windows[1:], start=1):
        next_lower, next_upper = next_window
        if arm == "coherent":
            propagated_lower = max(next_lower, possible_lower + 1)
            propagated_upper = min(next_upper, possible_upper + max_gap)
            keep = propagated_lower <= propagated_upper
        elif arm == "optimistic":
            keep = pair_possible(windows[index - 1], next_window, max_gap)
        else:
            keep = all_clock_assignments_admit_pair(
                windows[index - 1], next_window, max_gap
            )
        if keep:
            current_length += 1
            if arm == "coherent":
                possible_lower, possible_upper = propagated_lower, propagated_upper
        else:
            segment_lengths.append(current_length)
            cuts.append(index)
            current_length = 1
            possible_lower, possible_upper = next_window
    segment_lengths.append(current_length)
    return tuple(segment_lengths), tuple(cuts)


def _bin(length: int) -> str:
    if length == 1:
        return "1"
    if length == 2:
        return "2"
    if length <= 5:
        return "3-5"
    if length <= 11:
        return "6-11"
    if length <= 23:
        return "12-23"
    return "24+"


def audit(groups: dict) -> dict:
    _validate()
    if len(groups) != 421 or sum(len(rows) for rows in groups.values()) != 28953:
        raise ValueError("Frozen source group and record denominator changed")
    output = {}
    for index, label in ((1, SCENARIOS[0]), (2, SCENARIOS[1])):
        arm_totals = Counter()
        affected_groups = Counter()
        length_bins = Counter()
        extra_cuts_per_group = Counter()
        for rows in groups.values():
            windows = _windows(rows, index)
            partitions = {
                arm: split_sequence(windows, arm, MAX_GAP) for arm in ARMS
            }
            cuts = {arm: set(partitions[arm][1]) for arm in ARMS}
            if not (
                cuts["optimistic"].issubset(cuts["coherent"])
                and cuts["coherent"].issubset(cuts["conservative"])
            ):
                raise AssertionError("Segmentation order violated exact time logic")
            for arm, (lengths, boundaries) in partitions.items():
                if sum(lengths) != len(windows) or len(lengths) != len(boundaries) + 1:
                    raise AssertionError("Contiguous partition did not cover original fixes")
                arm_totals[f"{arm}_cuts"] += len(boundaries)
                arm_totals[f"{arm}_segments"] += len(lengths)
                arm_totals[f"{arm}_segments_ge2"] += sum(n >= 2 for n in lengths)
                arm_totals[f"{arm}_records_in_segments_ge2"] += sum(
                    n for n in lengths if n >= 2
                )
                arm_totals[f"{arm}_max_length"] = max(
                    arm_totals[f"{arm}_max_length"], max(lengths)
                )
                for n in lengths:
                    length_bins[f"{arm}::{_bin(n)}"] += 1
                if not boundaries:
                    affected_groups[f"{arm}_groups_single_segment"] += 1
            added = len(cuts["coherent"] - cuts["optimistic"])
            arm_totals["additional_coherent_cuts_beyond_pairwise"] += added
            if added:
                affected_groups["groups_with_extra_coherent_cut"] += 1
                extra_cuts_per_group[added] += 1
            if not cuts["optimistic"]:
                affected_groups["groups_all_pairs_possible"] += 1
                if added:
                    affected_groups["groups_all_pairs_possible_but_need_extra_cut"] += 1
        for arm in ARMS:
            arm_totals[f"{arm}_retained_edges"] = 28532 - arm_totals[f"{arm}_cuts"]
            if arm_totals[f"{arm}_segments"] != 421 + arm_totals[f"{arm}_cuts"]:
                raise AssertionError("Segments must equal groups plus cut count")
        expected = (27739, 6327) if index == 1 else (27674, 17034)
        if (
            arm_totals["optimistic_retained_edges"],
            arm_totals["conservative_retained_edges"],
        ) != expected:
            raise ValueError("Pair-level invariance fails frozen PR #748 counts")
        if index == 1:
            if (
                arm_totals["additional_coherent_cuts_beyond_pairwise"] != 64
                or affected_groups["groups_with_extra_coherent_cut"] != 41
                or affected_groups["groups_all_pairs_possible_but_need_extra_cut"] != 14
            ):
                raise ValueError("Full-group coherence no longer matches PR #749")
        else:
            if arm_totals["additional_coherent_cuts_beyond_pairwise"] != 0:
                raise ValueError("Near-midnight source scenario unexpectedly gains splits")
        output[label] = {
            "total_groups": 421,
            "total_records": 28953,
            "total_adjacent_pairs": 28532,
            "arm_stats": dict(sorted(arm_totals.items())),
            "group_stats": dict(sorted(affected_groups.items())),
            "segment_length_bins": dict(sorted(length_bins.items())),
            "extra_cut_count_frequency_across_groups": {
                str(k): v for k, v in sorted(extra_cuts_per_group.items())
            },
        }
    return {
        "schema": "eog.mckee2024.post_stop_bbmm_clock_segmentation_receipt.v1",
        "status": "SOURCE_ONLY_CONDITIONAL_CLOCK_BBMM_LINK_AUDIT__STOPS_RETAINED",
        "source_sha256_verified": True,
        "source_sha256": SHA256,
        "source_file_bytes": 1539661,
        "source_records": 28953,
        "source_groups": 421,
        "max_gap_seconds": MAX_GAP,
        "scenario_results": output,
        "actual_BBMM_fitted": False,
        "author_clock_DST_verified": False,
        "author_source_CRS_verified": False,
        "2h_dense_holdout_opened": False,
        "raw_GPS_coordinates_individual_IDs_or_timestamps_exported": False,
        "EOG_prediction_scored": False,
        "EOG_WF_frozen_scored": 3,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    groups, _ = _source_rows(args.source_zip)
    result = audit(groups)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
