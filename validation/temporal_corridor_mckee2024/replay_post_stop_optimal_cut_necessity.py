#!/usr/bin/env python3
"""Identify cut positions forced by *all* minimum-block clock partitions.

McKee original 12h sparse GPS only. The published 12.5h gap rule is used
as a conditional source-time predicate; this is not an animal-movement,
BBMM or EOG prediction. Neither raw group IDs, clocks nor link locations
are exported. No 2h dense GPS or SHP geometry is ever opened.

A shortest-path DAG represents every possible contiguous temporal block.
Links in every optimal partition are distinguished from those selected
only by the old longest-prefix greedy tie-breaking strategy.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from replay_post_stop_time_interval_qc import _source_rows, SHA256
from replay_post_stop_dst_union_coherence import (
    allowed_instants, advance, segmentation, _system_tzdb_version
)

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_optimal_cut_necessity_protocol_v1.json"
WORLD_ORDER = (
    ("T0_FULL_DAY_UNCERTAINTY", "NAIVE_MOUNTAIN_LOCAL"),
    ("T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW", "NAIVE_MOUNTAIN_LOCAL"),
    ("T0_FULL_DAY_UNCERTAINTY", "AMERICA_DENVER_IANA"),
    ("T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW", "AMERICA_DENVER_IANA"),
)
EXPECTED_GREEDY_CUTS = (857, 858, 889, 890)
GAP = 45000
COUNT_CAP = 1_000_001


def _check_protocol():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        p.get("schema") != "eog.mckee2024.source_only_optimal_cut_necessity.v1"
        or p.get("status") != "FROZEN_BEFORE_MINIMUM_PARTITION_ENSEMBLE_SOURCE_ANALYSIS"
        or p["source"]["sha256"] != SHA256
        or p["source"]["bytes"] != 1539661
        or p["source"]["records"] != 28953
        or p["source"]["groups"] != 421
        or p["source"]["links"] != 28532
        or p["model"]["gap_seconds"] != [1, GAP]
        or tuple((w["id"],w["cut_expected"]) for w in p["worlds"])
            != tuple(zip(("T0_NAIVE","T1_NAIVE","T0_IANA","T1_IANA"), EXPECTED_GREEDY_CUTS))
    ):
        raise ValueError("Frozen source/world/clock DAG protocol changed")
    return p


def optimal_partition_links(time_windows, gap: int = GAP):
    """Return every link's class across ALL min-cut contiguous partitions.

    C: every minimum-cut partition cuts this original adjacent link;
    O: some optimal partitions cut this link and some retain it;
    R: every optimal partition retains this link.

    DAG nodes are gaps between records, 0..N. An edge i->j means
    records i..j-1 form one globally feasible segment. Each directed
    0->N path is a valid contiguous partition; shortest paths enumerate
    every min-block partition without exponential materialization.
    """
    if not time_windows or any(not u for u in time_windows):
        raise ValueError("At least one nonempty allowed time-window union required")
    if isinstance(gap, bool) or not isinstance(gap, int) or gap < 1:
        raise ValueError("Positive integral max-gap seconds required")
    n=len(time_windows)
    adjacent=[[] for _ in range(n)]
    for i in range(n):
        reachable=time_windows[i]
        adjacent[i].append(i+1)
        for j in range(i+2,n+1):
            reachable=advance(reachable,time_windows[j-1],gap)
            if not reachable:
                break  # infeasible prefix cannot become feasible by extension
            adjacent[i].append(j)
    infinity=n+2
    prefix=[infinity]*(n+1)
    prefix[0]=0
    for i in range(n):
        for j in adjacent[i]:
            prefix[j]=min(prefix[j],prefix[i]+1)
    suffix=[infinity]*(n+1)
    suffix[n]=0
    for i in range(n-1,-1,-1):
        suffix[i]=min(1+suffix[j] for j in adjacent[i])
    shortest=prefix[n]
    if shortest != suffix[0]:
        raise AssertionError("Shortest-partition dynamic programming disagreement")

    can_cut=[False]*(n+1)
    for k in range(1,n):
        can_cut[k]=prefix[k]+suffix[k]==shortest
    # All optimal DAG block-edges crossing boundary k permit retaining k.
    cover_diff=[0]*(n+2)
    ways=[0]*(n+1)
    ways[0]=1
    for i in range(n):
        for j in adjacent[i]:
            if prefix[i]+1+suffix[j]!=shortest:
                continue
            ways[j]=min(COUNT_CAP,ways[j]+ways[i])
            if j>=i+2:
                cover_diff[i+1]+=1
                cover_diff[j]-=1
    can_retain=[False]*(n+1)
    coverage=0
    for k in range(1,n):
        coverage+=cover_diff[k]
        can_retain[k]=coverage>0
    classification=[]
    for k in range(1,n):
        c,retain=can_cut[k],can_retain[k]
        if not(c or retain):
            raise AssertionError("Link has no possible optimal cut or retention")
        classification.append(
            "C" if c and not retain else
            "R" if retain and not c else "O"
        )
    # The previous greedy strategy keeps each longest feasible prefix.
    # Implement the same rule with an explicit argument so a tiny-clock
    # independent oracle can test arbitrary maximum positive gaps.
    cut_set=set()
    reachable=time_windows[0]
    for k,allowed in enumerate(time_windows[1:],start=1):
        nxt=advance(reachable,allowed,gap)
        if not nxt:
            cut_set.add(k)
            reachable=allowed
        else:
            reachable=nxt
    if gap == GAP and cut_set != segmentation(time_windows)[0]:
        raise AssertionError("Greedy cut choice differs from prior source replay")
    if len(cut_set)!=shortest-1:
        raise AssertionError("Previously frozen greedy has nonoptimal cut count")
    if any(classification[k-1]=="R" for k in cut_set):
        raise AssertionError("Greedy cut a provably forced-retained link")
    if any(classification[k-1]=="C" and k not in cut_set for k in range(1,n)):
        raise AssertionError("Greedy omitted a forced cut")
    return {
        "minimum_cuts":shortest-1,
        "classification":tuple(classification),
        "greedy_cut_indices":frozenset(cut_set),
        "minimum_partition_count_capped":ways[n],
    }


def audit(groups):
    _check_protocol()
    if len(groups)!=421 or sum(map(len,groups.values()))!=28953:
        raise ValueError("Original exact-source group and record count changed")
    per_world={world:Counter() for world in WORLD_ORDER}
    nonunique_groups=Counter()
    greedy_optional_groups=Counter()
    pattern=Counter()
    selected_mask=Counter()
    class_different_groups=0
    negative_mst_groups=0
    total_original_links=0
    for rows in groups.values():
        analyses=[]
        for scenario,clock in WORLD_ORDER:
            permitted=[
                allowed_instants(rec,scenario,clock) for rec in rows
            ]
            result=optimal_partition_links(permitted)
            analyses.append(result)
            stat=per_world[(scenario,clock)]
            stat["minimum_cuts"]+=result["minimum_cuts"]
            stat["n_links"]+=len(result["classification"])
            for flag in ("C","O","R"):
                stat[{"C":"forced_cut","O":"optional","R":"forced_retain"}[flag]]+=result["classification"].count(flag)
            stat["greedy_selected_forced_cuts"]+=sum(
                result["classification"][k-1]=="C"
                for k in result["greedy_cut_indices"]
            )
            stat["greedy_selected_optional_cuts"]+=sum(
                result["classification"][k-1]=="O"
                for k in result["greedy_cut_indices"]
            )
            if result["minimum_partition_count_capped"]>1:
                nonunique_groups[(scenario,clock)]+=1
            if any(
                result["classification"][k-1]=="O"
                for k in result["greedy_cut_indices"]
            ):
                greedy_optional_groups[(scenario,clock)]+=1
        # Fixed MST is only a constant offset of naive local seconds, so
        # it must yield exactly the same *set* of minimum partitions.
        for index,scenario in enumerate((
            "T0_FULL_DAY_UNCERTAINTY","T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"
        )):
            mst=optimal_partition_links([
                allowed_instants(rec,scenario,"FIXED_MST_UTC_MINUS_07")
                for rec in rows
            ])
            if (
                mst["minimum_cuts"]!=analyses[index]["minimum_cuts"]
                or mst["classification"]!=analyses[index]["classification"]
                or mst["greedy_cut_indices"]!=analyses[index]["greedy_cut_indices"]
            ):
                raise AssertionError("Fixed MST translation changed time-optimal partitions")
        negative_mst_groups+=1
        if len({len(a["classification"]) for a in analyses})!=1:
            raise AssertionError("Clock worlds changed original link ordering")
        changed=False
        for k in range(len(analyses[0]["classification"])):
            cls="".join(a["classification"][k] for a in analyses)
            greedy="".join(
                "1" if k+1 in a["greedy_cut_indices"] else "0"
                for a in analyses
            )
            pattern[cls]+=1
            selected_mask[greedy]+=1
            changed |= len(set(cls))>1
        class_different_groups+=int(changed)
        total_original_links+=len(rows)-1

    if total_original_links!=28532 or negative_mst_groups!=421:
        raise ValueError("Frozen original link denominator or MST control changed")
    for world,expected in zip(WORLD_ORDER,EXPECTED_GREEDY_CUTS):
        stat=per_world[world]
        if stat["minimum_cuts"]!=expected:
            raise ValueError("Frozen T0/T1×local/IANA greedy minimum cuts drifted")
        if sum(stat[k] for k in ("forced_cut","optional","forced_retain"))!=28532:
            raise AssertionError("Three optimal link statuses do not partition every link")
        if stat["greedy_selected_forced_cuts"]+stat["greedy_selected_optional_cuts"]!=expected:
            raise AssertionError("Greedy cut status count does not reconcile")
    if sum(pattern.values())!=28532 or sum(selected_mask.values())!=28532:
        raise AssertionError("Joint model status record count does not reconcile")
    if selected_mask["1111"]!=857:
        raise ValueError("Previously frozen 857 greedy cuts common to 4 worlds changed")

    return {
        "schema":"eog.mckee2024.source_only_optimal_cut_necessity_receipt.v1",
        "status":"GREEDY_OVERLAP_NOT_EQUAL_TO_MANDATORY_OPTIMAL_CUTS__TIME_SOURCE_STOP",
        "source_sha256_verified":True,
        "source_sha256":SHA256,
        "record_count":28953,
        "group_count":421,
        "original_within_group_link_count":total_original_links,
        "world_order":[scenario+":"+clock for scenario,clock in WORLD_ORDER],
        "per_world":{
            scenario+":"+clock:dict(sorted(per_world[(scenario,clock)].items()))
            for scenario,clock in WORLD_ORDER
        },
        "groups_with_multiple_minimum_cut_partitions":{
            scenario+":"+clock:nonunique_groups[(scenario,clock)]
            for scenario,clock in WORLD_ORDER
        },
        "groups_with_greedy_selected_optional_cut":{
            scenario+":"+clock:greedy_optional_groups[(scenario,clock)]
            for scenario,clock in WORLD_ORDER
        },
        "joint_forced_optional_class_patterns":dict(sorted(pattern.items())),
        "joint_greedy_cut_mask_patterns":dict(sorted(selected_mask.items())),
        "joint":{
            "selected_cut_by_all_4_greedy":selected_mask["1111"],
            "forced_cut_in_all_4_optimal_ensembles":pattern["CCCC"],
            "forced_retain_in_all_4_optimal_ensembles":pattern["RRRR"],
            "not_universally_forced_either_way":28532-pattern["CCCC"]-pattern["RRRR"],
            "optional_in_at_least_one_world":sum(n for p,n in pattern.items() if "O" in p),
            "forced_cut_in_some_and_forced_retain_in_another_world":sum(
                n for p,n in pattern.items() if "C" in p and "R" in p
            ),
            "groups_with_any_link_class_difference_across_worlds":class_different_groups,
            "fixed_MST_negative_control_groups":negative_mst_groups,
        },
        "IANA_timezone_db_version":_system_tzdb_version(),
        "source_timestamp_semantics_author_confirmed":False,
        "source_CRS_author_confirmed":False,
        "source_QC_STOP_retained":True,
        "dense_2h_GPS_opened":False,
        "source_point_geometry_read":False,
        "raw_IDs_timestamps_coordinates_or_link_locations_exported":False,
        "BBMM_or_EOG_predictive_score_computed":False,
        "original_EOG_WF_scored_endpoints":3,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source-zip",type=Path,required=True)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    # Reject source access before the precommitted contract is present.
    _check_protocol()
    groups,_=_source_rows(args.source_zip)
    receipt=audit(groups)
    rendered=json.dumps(receipt,indent=2,sort_keys=True)+"\n"
    if args.output is None:
        print(rendered)
    else:
        args.output.write_text(rendered,encoding="utf-8")


if __name__=="__main__":
    main()
