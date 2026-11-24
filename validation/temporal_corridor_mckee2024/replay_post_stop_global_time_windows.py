#!/usr/bin/env python3
"""Global time-window coherence for McKee's original SHA-matched 12h GPS.

Source-only and explicitly conditional; NO biological path inference.
Reads only prior-authorized 12h DBF grouping/time fields via the frozen
source decoder. Never reads .shp coordinates or withheld dense 2h GPS.
No individual ID or precise date/time leaves this process.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Sequence

from replay_post_stop_time_interval_qc import _source_rows, SHA256

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_global_time_window_coherence_protocol_v1.json"
WINDOW_LENGTHS = (2, 3, 4, 6, 12, 24)
MAX_GAP = 45000
SCENARIOS = ("T0_FULL_DAY_UNCERTAINTY", "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW")


def pair_possible(a: tuple[int, int], b: tuple[int, int], max_gap: int = MAX_GAP) -> bool:
    """There exists *some* pair-specific assignment with 1 <= gap <= max_gap."""
    return b[1] >= a[0] + 1 and b[0] <= a[1] + max_gap


def path_possible(
    windows: Sequence[tuple[int, int]],
    max_gap: int = MAX_GAP,
) -> bool:
    """Exact forward propagation of one shared reachable clock interval.

    No re-injection, no local clock substitution midway through the path,
    no swapping input scenarios and no implicit biological travel model.
    """
    if not windows:
        raise ValueError("At least one temporal window is required")
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < 1:
        raise ValueError("max_gap must be positive integer seconds")
    if any(lo > hi for lo, hi in windows):
        raise ValueError("Each timestamp interval must be a nonempty closed range")
    lo, hi = windows[0]
    for nxt_lo, nxt_hi in windows[1:]:
        lo, hi = max(nxt_lo, lo + 1), min(nxt_hi, hi + max_gap)
        if lo > hi:
            return False
    return True


def _windows(records, scenario_index: int) -> list[tuple[int, int]]:
    if scenario_index not in (1, 2):
        raise ValueError("Unknown frozen clock scenario")
    return [
        (
            row[0],
            row[scenario_index] - 1
            if scenario_index == 1 and row[3] == "date"
            else row[scenario_index],
        )
        for row in records
    ]


def _check_protocol():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        p.get("schema") != "eog.mckee2024.post_stop_full_segment_time_coherence.v1"
        or p.get("status") != "FROZEN_BEFORE_NEW_WINDOW_LENGTH_OR_GROUP_COHERENCE_COMPUTATION"
        or p["source"]["sha256"] != SHA256
        or p["source"]["source_records"] != 28953
        or p["source"]["groups"] != 421
        or tuple(p["window_lengths"]) != WINDOW_LENGTHS
        or p["permitted_gap_seconds"] != {"lower": 1, "upper": MAX_GAP}
        or p["historical_claim_boundary"]["dense_2h_holdout_sealed"] is not True
    ):
        raise ValueError("Source, window lengths or gap policy differs from precommitted protocol")
    return p


def audit(groups: dict, *, frozen=True) -> dict:
    if frozen:
        _check_protocol()
    if len(groups) != 421 or sum(map(len, groups.values())) != 28953:
        raise ValueError("Frozen source group denominator differs")
    by_scenario = {}
    full_group_summary = {}
    group_sizes = sorted(len(rows) for rows in groups.values())
    for scenario_index, label in ((1, SCENARIOS[0]), (2, SCENARIOS[1])):
        precomputed = [_windows(rows, scenario_index) for rows in groups.values()]
        lengths = []
        for width in WINDOW_LENGTHS:
            counts = Counter()
            groups_with_false = 0
            for sequence in precomputed:
                n = len(sequence)
                any_false = False
                for begin in range(n - width + 1):
                    chunk = sequence[begin:begin + width]
                    each_pair = all(
                        pair_possible(chunk[j], chunk[j+1])
                        for j in range(width - 1)
                    )
                    coherent = path_possible(chunk)
                    if coherent and not each_pair:
                        raise AssertionError("Whole-window coherence cannot precede its pair constraints")
                    counts["all_windows"] += 1
                    counts["every_pair_possible"] += int(each_pair)
                    counts["coherent_whole_window"] += int(coherent)
                    counts["pairwise_only_false_chain"] += int(each_pair and not coherent)
                    any_false = any_false or (each_pair and not coherent)
                groups_with_false += int(any_false)
            n_pairwise = counts["every_pair_possible"]
            lengths.append({
                "records_per_window": width,
                "all_windows": counts["all_windows"],
                "every_pair_possible": n_pairwise,
                "coherent_whole_window": counts["coherent_whole_window"],
                "pairwise_only_false_chain": counts["pairwise_only_false_chain"],
                "false_fraction_of_pairwise_possible": (
                    counts["pairwise_only_false_chain"] / n_pairwise
                    if n_pairwise else None
                ),
                "groups_with_any_false_chain_at_this_width": groups_with_false,
            })
        by_scenario[label] = lengths
        g_counts = Counter()
        for sequence in precomputed:
            pair_all = all(
                pair_possible(sequence[j], sequence[j + 1])
                for j in range(len(sequence) - 1)
            )
            coherent = path_possible(sequence)
            if coherent and not pair_all:
                raise AssertionError("Coherent group cannot have disallowed pair")
            g_counts["total_groups"] += 1
            g_counts["all_pairwise_possible_groups"] += int(pair_all)
            g_counts["globally_coherent_groups"] += int(coherent)
            g_counts["pairwise_only_false_chain_groups"] += int(pair_all and not coherent)
            g_counts["groups_with_any_pair_excluded"] += int(not pair_all)
        full_group_summary[label] = dict(g_counts)

    t0 = by_scenario[SCENARIOS[0]]
    t1 = by_scenario[SCENARIOS[1]]
    if (
        t0[0]["pairwise_only_false_chain"] != 0
        or t1[0]["pairwise_only_false_chain"] != 0
        or (t0[1]["every_pair_possible"], t0[1]["coherent_whole_window"],
            t0[1]["pairwise_only_false_chain"]) != (26764, 26700, 64)
        or (t1[1]["every_pair_possible"], t1[1]["coherent_whole_window"],
            t1[1]["pairwise_only_false_chain"]) != (26637, 26637, 0)
    ):
        raise ValueError("Source or algorithm fails frozen PR #748 pair/triple control")
    return {
        "schema": "eog.mckee2024.post_stop_global_time_window_coherence_receipt.v1",
        "status": "CONDITIONAL_LOCAL_CLOCK_PATH_COMPOSITION_ONLY__SOURCE_STOP_RETAINED",
        "protocol_precommitted": True,
        "source_sha256_verified": True,
        "source_sha256": SHA256,
        "source_12h_records": 28953,
        "source_12h_groups": 421,
        "group_record_count_min_median_max": [
            group_sizes[0], group_sizes[len(group_sizes)//2], group_sizes[-1]
        ],
        "max_gap_seconds": MAX_GAP,
        "clock_scenarios": list(SCENARIOS),
        "window_counts_by_scenario": by_scenario,
        "entire_group_counts_by_scenario": full_group_summary,
        "ordering_fixed_to_prior_T0_source_blind_rule": True,
        "UTC_or_DST_clock_alignment_verified": False,
        "source_author_CRS_verified": False,
        "ecological_movement_route_inferred": False,
        "2h_holdout_data_opened": False,
        "SHP_coordinates_opened": False,
        "raw_animal_IDs_times_or_locations_exported": False,
        "EOG_forecast_scored": False,
        "closed_EOG_WF_scored_endpoints": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    groups, _ = _source_rows(args.source_zip)
    result = audit(groups)
    result_text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(result_text, encoding="utf-8")
    else:
        print(result_text)


if __name__ == "__main__":
    main()
