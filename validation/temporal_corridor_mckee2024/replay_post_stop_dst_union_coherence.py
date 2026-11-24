#!/usr/bin/env python3
"""Union-of-UTC-time-windows DST audit for the exact original McKee 12h GPS.

Frozen protocol must preexist original source timestamp access. Reuses the
SHA-locked DBF-only decoder; never reads source SHP geometry, animal
coordinates, 2h holdout or biological response. Exports aggregate counts
only. America/Denver is a *conditional* interpretation, not author truth.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from replay_post_stop_time_interval_qc import _source_rows, EPOCH, SHA256

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_dst_fold_coherence_protocol_v1.json"
H = 45000
SCENARIOS = ("T0_FULL_DAY_UNCERTAINTY", "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW")
CLOCKS = ("NAIVE_MOUNTAIN_LOCAL", "FIXED_MST_UTC_MINUS_07", "AMERICA_DENVER_IANA")
DENVER = ZoneInfo("America/Denver")
UTC = timezone.utc


def _seconds_naive(d: datetime) -> int:
    return int((d - EPOCH).total_seconds())


def valid_utc_folds(naive: datetime) -> tuple[int, ...]:
    """All real UTC instants mapping *back* to the specified civil second."""
    possible = set()
    for fold in (0, 1):
        aware = naive.replace(tzinfo=DENVER, fold=fold)
        absolute = aware.astimezone(UTC)
        if absolute.astimezone(DENVER).replace(tzinfo=None) == naive:
            possible.add(int(absolute.timestamp()))
    return tuple(sorted(possible))


def canonical_union(intervals) -> tuple[tuple[int, int], ...]:
    """Sorted nonoverlapping inclusive integer-second intervals."""
    merged = []
    for lo, hi in sorted(intervals):
        if lo > hi:
            raise ValueError("Empty allowed UTC time interval")
        if merged and lo <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return tuple(merged)


def allowed_instants(record, scenario: str, clock: str):
    """Preserve distinct fall-back folds; never convexify an excluded gap."""
    if scenario not in SCENARIOS or clock not in CLOCKS:
        raise ValueError("Unknown frozen scenario or clock interpretation")
    lower, _, _, precision, _ = record
    local = EPOCH + timedelta(seconds=lower)
    if clock != CLOCKS[2]:
        base = _seconds_naive(local) + (25200 if clock == CLOCKS[1] else 0)
        if precision == "full":
            return ((base, base),)
        if precision != "date":
            raise ValueError("Unrecognized source timestamp precision")
        return ((base, base + (86399 if scenario == SCENARIOS[0] else 3600)),)
    if precision == "full":
        values = valid_utc_folds(local)
        if not values:
            raise ValueError("Nonexistent source civil-clock instant")
        return tuple((instant, instant) for instant in values)
    if precision != "date":
        raise ValueError("Unrecognized source timestamp precision")
    midnight = valid_utc_folds(local)
    if len(midnight) != 1:
        raise ValueError("Midnight cannot be interpreted unambiguously")
    if scenario == SCENARIOS[0]:
        next_midnight = valid_utc_folds(local + timedelta(days=1))
        if len(next_midnight) != 1:
            raise ValueError("Next-midnight cannot be interpreted unambiguously")
        return ((midnight[0], next_midnight[0] - 1),)
    one_am = valid_utc_folds(local + timedelta(hours=1))
    if not one_am:
        raise ValueError("01:00 boundary does not exist in IANA zone")
    return canonical_union(
        [(midnight[0], one_am[0])] +
        [(instant, instant) for instant in one_am[1:]]
    )


def advance(reachable, next_allowed, max_gap: int = H):
    """Exact shared-clock propagation, including disjoint UTC subwindows."""
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < 1:
        raise ValueError("Positive integer-second maximum gap required")
    return canonical_union(
        (max(lo + 1, target_lo), min(hi + max_gap, target_hi))
        for lo, hi in reachable
        for target_lo, target_hi in next_allowed
        if max(lo + 1, target_lo) <= min(hi + max_gap, target_hi)
    )


def segmentation(windows):
    if not windows or not all(windows):
        raise ValueError("Nonempty list of legal time interval unions required")
    possible = set()
    coherent = set()
    reachable = windows[0]
    for idx, nxt in enumerate(windows[1:], start=1):
        if not advance(windows[idx - 1], nxt):
            possible.add(idx)
        nxt_reach = advance(reachable, nxt)
        if not nxt_reach:
            coherent.add(idx)
            reachable = nxt
        else:
            reachable = nxt_reach
    if not possible.issubset(coherent):
        raise AssertionError("A globally coherent segment cannot retain an impossible pair")
    return coherent, possible


def _check_protocol():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        p.get("schema") != "eog.mckee2024.post_stop_local_clock_vs_timezone_gap_audit.v1"
        or p.get("status") != "FROZEN_PRE_SOURCE_TIMESTAMP_TO_UTC_CONVERSION"
        or p["source"]["sha256"] != SHA256
        or p["source"]["records"] != 28953
        or p["source"]["groups"] != 421
        or p["common_eligibility"]["max_gap_seconds"] != H
        or p["common_eligibility"]["min_gap_seconds"] != 1
        or tuple(x["id"] for x in p["alternative_time_interpretations"]) != CLOCKS
        or p["original_EOG_WF"]["scored"] != 3
    ):
        raise ValueError("Frozen timezone/source identity, gap or stop changed")
    return p


def audit(groups: dict) -> dict:
    _check_protocol()
    if len(groups) != 421 or sum(len(v) for v in groups.values()) != 28953:
        raise ValueError("Source record/group count changed")
    diagnostics = Counter()
    results = {}
    paired = {}
    # A date-only source record is one uncertain local day, not one UTC instant.
    for group in groups.values():
        for row in group:
            civil = EPOCH + timedelta(seconds=row[0])
            if row[3] == "full":
                folds = valid_utc_folds(civil)
                diagnostics["exact_full_ambiguous_folds"] += len(folds) == 2
                diagnostics["exact_full_nonexistent_times"] += len(folds) == 0
            elif row[3] == "date":
                a = valid_utc_folds(civil)
                b = valid_utc_folds(civil + timedelta(days=1))
                if len(a) != 1 or len(b) != 1:
                    raise ValueError("Unexpected DST midnight ambiguity")
                duration = b[0] - a[0]
                if duration == 25 * 3600:
                    diagnostics["date_only_fall_transition_records"] += 1
                elif duration == 23 * 3600:
                    diagnostics["date_only_spring_transition_records"] += 1
                elif duration != 24 * 3600:
                    raise ValueError("Unexpected source local-day UTC duration")
            else:
                raise ValueError("Unknown timestamp precision")
    if diagnostics["exact_full_nonexistent_times"]:
        raise ValueError("Nonexistent complete civil timestamps; source STOP")
    for scenario in SCENARIOS:
        clock_stats = {label: Counter() for label in CLOCKS}
        cut_masks = {label: [] for label in CLOCKS}
        for group in groups.values():
            for label in CLOCKS:
                allowed = [allowed_instants(row, scenario, label) for row in group]
                cuts, optimistic = segmentation(allowed)
                cut_masks[label].append(cuts)
                clock_stats[label]["coherent_cuts"] += len(cuts)
                clock_stats[label]["optimistic_cuts"] += len(optimistic)
                clock_stats[label]["additional_coherent_cuts"] += len(cuts - optimistic)
                clock_stats[label]["groups_with_additional_coherent_cut"] += bool(cuts - optimistic)
                clock_stats[label]["groups_with_any_coherent_cut"] += bool(cuts)
        if cut_masks[CLOCKS[0]] != cut_masks[CLOCKS[1]]:
            raise ValueError("Fixed UTC-7 negative control unexpectedly differs from naive clock")
        expected = (857, 793) if scenario == SCENARIOS[0] else (858, 858)
        if tuple(clock_stats[CLOCKS[0]][field] for field in ("coherent_cuts", "optimistic_cuts")) != expected:
            raise ValueError("Naive source time-gap result diverges from frozen PR #750")
        results[scenario] = {key: dict(value) for key, value in clock_stats.items()}
        table = Counter()
        for naive, denver in zip(cut_masks[CLOCKS[0]], cut_masks[CLOCKS[2]]):
            table["cut_both"] += len(naive & denver)
            table["naive_only"] += len(naive - denver)
            table["denver_only"] += len(denver - naive)
            table["affected_groups"] += naive != denver
        table["retained_both"] = 28532 - sum(table[k] for k in ("cut_both", "naive_only", "denver_only"))
        paired[scenario] = dict(table)
    return {
        "schema": "eog.mckee2024.post_stop_iana_dst_union_clock_receipt.v1",
        "status": "CONDITIONAL_IANA_DST_TIME_WINDOW_SENSITIVITY__SOURCE_STOPS_RETAINED",
        "source_sha256_verified": True,
        "source_sha256": SHA256,
        "records": 28953, "groups": 421, "adjacent_links": 28532,
        "naive_local_vs_fixed_MST_masks_identical": True,
        "zone": "America/Denver",
        "fold_and_date_only_transition_counts": dict(diagnostics),
        "clock_gap_arm_counts": results,
        "naive_vs_iana_coherent_cut_paired_counts": paired,
        "time_interpretations_author_verified": False,
        "physical_elapsed_hours_or_DST_source_verified": False,
        "original_CRS_QC_STOP_retained": True,
        "original_date_only_clock_QC_STOP_retained": True,
        "dense_2h_GPS_opened": False,
        "source_geometry_opened": False,
        "raw_record_times_animal_IDs_coordinates_exported": False,
        "ecological_or_EOG_prediction_scored": False,
        "frozen_EOG_WF_scored_count": 3,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    groups, _ = _source_rows(args.source_zip)
    result = audit(groups)
    result_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(result_text)
    else:
        args.output.write_text(result_text, encoding="utf-8")


if __name__ == "__main__":
    main()
