#!/usr/bin/env python3
"""Post-STOP test of possible R >=4.3 midnight text truncation in McKee GPS.

Does NOT assert that the McKee source was exported with R 4.3, or that
date-only values truly mean midnight. The exact SHA-locked original 12h
DBF grouping/time decoder is reused. No geometry, animal IDs, exact
timestamp strings or dense 2h holdout are exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import timedelta
import json
from pathlib import Path

from replay_post_stop_time_interval_qc import _source_rows, EPOCH, SHA256
from replay_post_stop_dst_union_coherence import (
    allowed_instants,
    segmentation,
    valid_utc_folds,
)

HERE = Path(__file__).resolve().parent
PROTOCOL_PATTERNS = HERE / "post_stop_midnight_serialization_protocol_v1.json"
PROTOCOL_H3 = HERE / "post_stop_exact_midnight_candidate_cut_protocol_v1.json"
N = 28953
GROUPS = 421
LINKS = 28532
T0 = "T0_FULL_DAY_UNCERTAINTY"
T1 = "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"
CLOCKS = ("NAIVE_MOUNTAIN_LOCAL", "AMERICA_DENVER_IANA")
EXPECTED_SOURCE = {("NAIVE_MOUNTAIN_LOCAL", T0):857,
                   ("NAIVE_MOUNTAIN_LOCAL", T1):858,
                   ("AMERICA_DENVER_IANA", T0):889,
                   ("AMERICA_DENVER_IANA", T1):890}


def _verify(stage):
    path = PROTOCOL_PATTERNS if stage == "patterns" else PROTOCOL_H3
    p = json.loads(path.read_text(encoding="utf-8"))
    if stage == "patterns":
        if (p.get("schema") != "eog.mckee2024.post_stop_midnight_string_serialization_diagnostic.v1"
            or p.get("status") != "FROZEN_BEFORE_NEW_PHYSICAL_TIMESTAMP_PATTERN_INSPECTION"
            or p["source"]["sha256"] != SHA256
            or p["source"]["n"] != N):
            raise ValueError("Original pre-timestamp source protocol mismatch")
    else:
        if (p.get("schema") != "eog.mckee2024.post_stop_exact_midnight_serializer_candidate.v1"
            or p.get("status") != "FROZEN_BEFORE_ANY_NEW_SOURCE_CUT_COMPARISON_FOR_MIDNIGHT_CANDIDATE"
            or p["source"]["sha256"] != SHA256
            or p["source"]["adjacent_links"] != LINKS):
            raise ValueError("Original pre-H3 source comparison protocol mismatch")
    return p


def _source_group_check(groups):
    if len(groups) != GROUPS or sum(map(len, groups.values())) != N:
        raise ValueError("Original GPS source groups/rows changed")


def audit_patterns(groups):
    _verify("patterns")
    _source_group_check(groups)
    shapes = Counter()
    hours = Counter()
    precision = Counter()
    features = Counter()
    mixed = Counter()
    neighbours = Counter()
    for rows in groups.values():
        kinds = set()
        for j, row in enumerate(rows):
            civil = EPOCH + timedelta(seconds=row[0])
            kind = row[3]
            kinds.add(kind)
            if kind == "date":
                shapes["date_only"] += 1
                for name, other in (
                    ("preceding", rows[j-1] if j else None),
                    ("following", rows[j+1] if j+1 < len(rows) else None),
                ):
                    if other and other[3] == "full":
                        neighbours[name+"_full_adjacent"] += 1
                        clock_gap = abs(row[0]-other[0]) / 3600
                        if 10 <= clock_gap <= 14:
                            neighbours[name+"_full_within_10_to_14h"] += 1
            elif kind == "full":
                shapes["full_datetime"] += 1
                hours[f"{civil.hour:02d}"] += 1
                features["complete_exact_midnight_00_00_00"] += (
                    civil.hour == civil.minute == civil.second == 0
                )
                features["full_time_minute_and_second_zero"] += (
                    civil.minute == 0 and civil.second == 0
                )
                features["full_time_minute_or_second_nonzero"] += (
                    civil.minute != 0 or civil.second != 0
                )
                for hour in (1, 12, 13):
                    features[f"complete_exact_{hour:02d}_00_00"] += (
                        civil.hour == hour and civil.minute == civil.second == 0
                    )
            else:
                raise ValueError("Unexpected original clock precision")
            if j:
                dh = (row[0] - rows[j-1][0]) / 3600
                features["original_adjacent_pairs"] += 1
                if 10 <= dh <= 14:
                    features["H3_midnight_hypothetical_gap_10_to_14h"] += 1
                if dh == 0:
                    features["H3_midnight_hypothetical_duplicates"] += 1
        mixed["groups_total"] += 1
        mixed["groups_mixed_date_and_full"] += kinds == {"date","full"}
        mixed["groups_with_date_only"] += "date" in kinds
        mixed["groups_with_full"] += "full" in kinds

    if shapes != Counter({"date_only":10835,"full_datetime":18118}):
        raise ValueError("Original exact source timestamp pattern totals differ")
    if features["complete_exact_midnight_00_00_00"] != 0:
        # It would not be correct to call the source exact R 4.3 pattern
        # in a file with explicit complete midnight strings.
        return_status = "STRICT_R43_MIDNIGHT_CHAR_PATTERN_NOT_EXCLUSIVE"
    else:
        return_status = "CONSISTENT_WITH_R43_MIDNIGHT_STRING_SHORTENING_NOT_PROVEN"
    return {
        "schema":"eog.mckee2024.post_stop_midnight_serialization_replay.v1",
        "status":return_status,
        "source_sha256_verified":True,
        "source_sha256":SHA256,
        "records":N,"groups":GROUPS,
        "timestamp_shapes":dict(shapes),
        "full_hour_histogram":dict(sorted(hours.items())),
        "full_clock_aggregate":dict(features),
        "group_mixture":dict(mixed),
        "date_full_neighbour_aggregates":dict(neighbours),
        "upstream_exporter_for_Dryad_proven":False,
        "date_only_values_corrected_or_source_overwritten":False,
        "dense_2hour_holdout_opened":False,
        "raw_animal_ids_dates_or_coordinates_exported":False,
        "ecological_prediction_scored":False
    }


def conditional_H3_domain(row, clock):
    """Interpret a date-only source string as exactly local midnight IF H3.

    Exact complete local clock readings on an autumn repeated 01:xx hour
    remain two possible UTC *instants* under IANA until source authority
    confirms the actual timestamp UTC offset.
    """
    if clock not in ("NAIVE_MOUNTAIN_LOCAL","AMERICA_DENVER_IANA","FIXED_MST_UTC_MINUS_07"):
        raise ValueError("Only declared local clock models permitted")
    civil = EPOCH + timedelta(seconds=row[0])
    if clock == "NAIVE_MOUNTAIN_LOCAL":
        return ((row[0],row[0]),)
    if clock == "FIXED_MST_UTC_MINUS_07":
        return ((row[0]+25200,row[0]+25200),)
    valid = valid_utc_folds(civil)
    if not valid:
        raise ValueError("Nonexistent local clock source instant under H3")
    if row[3] == "date" and len(valid) != 1:
        raise ValueError("Exact local midnight ambiguous under H3")
    return tuple((t,t) for t in valid)


def audit_candidate(groups):
    _verify("h3")
    _source_group_check(groups)
    cases = {}
    masks = {}
    for clock in CLOCKS:
        for scenario in (T0, T1, "H3"):
            count=Counter()
            cut_masks=[]
            for rows in groups.values():
                world = [
                    conditional_H3_domain(row,clock) if scenario=="H3"
                    else allowed_instants(row,scenario,clock)
                    for row in rows
                ]
                cut, pair = segmentation(world)
                cut_masks.append(cut)
                count["coherent_cuts"] += len(cut)
                count["pairwise_cuts"] += len(pair)
                count["additional_coherent_cuts"] += len(cut-pair)
                count["groups"] += 1
            key=clock+":"+scenario
            masks[key]=cut_masks
            cases[key]=dict(count)
            if scenario!="H3" and count["coherent_cuts"] != EXPECTED_SOURCE[(clock,scenario)]:
                raise ValueError("Source cut mask differs from frozen prior result")
    # Fixed MST must be a constant translation; no altered clock differences.
    fixed = Counter()
    for rows,naive_mask in zip(groups.values(),masks["NAIVE_MOUNTAIN_LOCAL:H3"]):
        windows=[conditional_H3_domain(row,"FIXED_MST_UTC_MINUS_07") for row in rows]
        cut,_=segmentation(windows)
        if cut != naive_mask:
            raise AssertionError("Fixed MST changed the exact-midnight clock mask")
        fixed["negative_control_groups"] += 1
    compares={}
    for clock in CLOCKS:
        for parent in (T0,T1):
            diff=Counter()
            for baseline,h3 in zip(masks[clock+":"+parent], masks[clock+":H3"]):
                diff["common_cuts"] += len(baseline & h3)
                diff["previous_only"] += len(baseline - h3)
                diff["H3_only"] += len(h3 - baseline)
                diff["groups_with_any_difference"] += baseline != h3
            diff["both_retained"] = LINKS-sum(diff[k] for k in (
                "common_cuts","previous_only","H3_only"
            ))
            compares[clock+":H3_vs_"+parent]=dict(diff)
    return {
        "schema":"eog.mckee2024.post_stop_exact_midnight_cuts_replay.v1",
        "status":"EXACT_MIDNIGHT_CANDIDATE_ONLY__AUTHOR_EXPORT_UNVERIFIED",
        "source_sha256_verified":True,"source_sha256":SHA256,
        "record_count":N,"group_count":GROUPS,"adjacent_pair_count":LINKS,
        "per_clock_cut_policy":cases,
        "H3_paired_cut_comparisons":compares,
        "fixed_MST_negative_control":dict(fixed),
        "date_only_exact_midnight_is_hypothesis":True,
        "author_true_time_zone_and_export_code_unknown":True,
        "dense_2h_holdout_opened":False,
        "SHP_geometry_read":False,
        "raw_ids_times_coordinates_exported":False,
        "BBMM_and_EOG_scores_computed":False
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip",required=True,type=Path)
    parser.add_argument("--stage",required=True,choices=("patterns","h3"))
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    _verify(args.stage)
    groups,_ = _source_rows(args.source_zip)
    result = audit_patterns(groups) if args.stage=="patterns" else audit_candidate(groups)
    payload=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(payload,encoding="utf-8")
    else:
        print(payload)


if __name__=="__main__":
    main()
