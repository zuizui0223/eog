#!/usr/bin/env python3
"""Source-only McKee 12h link necessity under one extra allowed cut.

This is an input-clock optimization sensitivity, not an ungulate movement
or BBMM forecast. Only the exact SHA-verified original sparse 12h DBF
group/time columns may be read. The dense 2h holdout remains sealed.
Individual IDs, exact clock values, and source GPS points are not exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
from heapq import heappop, heappush
import json
from pathlib import Path

from replay_post_stop_time_interval_qc import _source_rows, SHA256
from replay_post_stop_dst_union_coherence import allowed_instants, advance

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "post_stop_one_extra_cut_budget_protocol_v1.json"
PREVIOUS_RECEIPT = HERE / "post_stop_optimal_cut_necessity_receipt_v1.json"
GAP = 45000
WORLDS = (
    ("T0_FULL_DAY_UNCERTAINTY", "NAIVE_MOUNTAIN_LOCAL"),
    ("T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW", "NAIVE_MOUNTAIN_LOCAL"),
    ("T0_FULL_DAY_UNCERTAINTY", "AMERICA_DENVER_IANA"),
    ("T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW", "AMERICA_DENVER_IANA"),
)
SHORT_NAMES = ("T0_NAIVE", "T1_NAIVE", "T0_IANA", "T1_IANA")
DELTAS = (0, 1, 2)


def _validate():
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        p.get("schema") != "eog.mckee2024.source_only_optimality_slack_link_identifiability.v1"
        or p.get("status") != "FROZEN_BEFORE_ANY_NEW_12H_LINK_RETENTION_BUDGET_ANALYSIS"
        or p["source"]["sha256"] != SHA256
        or p["source"]["size_bytes"] != 1539661
        or p["source"]["records"] != 28953
        or p["source"]["groups"] != 421
        or p["source"]["adjacent_pairs"] != 28532
        or p["partition_budget"]["delta_allowed_cuts_per_group"] != [0, 1, 2]
        or [(w["id"], w["scenario"], w["clock"]) for w in p["worlds"]]
            != [(n, s, c) for n, (s,c) in zip(SHORT_NAMES, WORLDS)]
        or p["frozen_EOG_WF"] != {"scored": 3, "favorable": 2, "adverse": 1,
                                    "scientific_stops": 31, "admin_exclusions": 3}
    ):
        raise ValueError("Precommitted source/clock/cut-budget gate was changed")
    return p


def _edge_dag(time_windows, max_gap):
    """List all contiguous source clock-compatible segments as DAG edges."""
    if not time_windows or not all(time_windows):
        raise ValueError("Every source time window must be nonempty")
    if isinstance(max_gap, bool) or not isinstance(max_gap, int) or max_gap < 1:
        raise ValueError("Maximum gap must be a positive integer second")
    n = len(time_windows)
    adj = [[] for _ in range(n)]
    for i in range(n):
        reachable = time_windows[i]
        adj[i].append(i+1)
        for j in range(i+2, n+1):
            reachable = advance(reachable, time_windows[j-1], max_gap)
            if not reachable:
                break
            adj[i].append(j)
    return adj


def classify_budget_links(time_windows, *, max_gap=GAP, deltas=DELTAS):
    """Each source link is C=forced cut, O=optional, or R=forced retained.

    A budget delta allows <= delta extra cuts beyond that group's
    separately measured minimum cut count. No exact-budget obligation.
    The shortest prefix+suffix path through boundary k gives min segments
    to CUT k. The shortest path using any segment spanning k gives min
    segments to RETAIN k. Evaluate both costs against S+delta.
    """
    if tuple(deltas) != tuple(sorted(set(deltas))) or not deltas or min(deltas)<0:
        raise ValueError("Deltas must be sorted unique nonnegative integers")
    adj = _edge_dag(time_windows, max_gap)
    n=len(time_windows)
    # Use real infinity. With an all-singleton group, n+2 may equal
    # minimum_blocks+2 and create a false retaining block at budget +2.
    inf=float("inf")
    prefix=[inf]*(n+1)
    prefix[0]=0
    for i in range(n):
        for j in adj[i]:
            prefix[j]=min(prefix[j],prefix[i]+1)
    suffix=[inf]*(n+1)
    suffix[n]=0
    for i in range(n-1,-1,-1):
        suffix[i]=min(1+suffix[j] for j in adj[i])
    optimum=prefix[n]
    if optimum!=suffix[0]:
        raise AssertionError("DAG shortest-prefix and suffix counts mismatch")

    # Optimal retain cost at each boundary: min path using a block that
    # strictly spans the adjacent source link. A heap sweep processes
    # arbitrary nonconvex allowed UTC clock unions without enumerating
    # source GPS coordinates or individual movement trajectories.
    starts=[[] for _ in range(n+1)]
    for i in range(n):
        for j in adj[i]:
            if j>=i+2:
                starts[i+1].append((prefix[i]+1+suffix[j],j-1))
    min_retain=[inf]*(n+1)
    heap=[]
    for k in range(1,n):
        for item in starts[k]:
            heappush(heap,item)
        while heap and heap[0][1]<k:
            heappop(heap)
        if heap:
            min_retain[k]=heap[0][0]

    classes={}
    for delta in deltas:
        flags=[]
        for k in range(1,n):
            cut_cost=prefix[k]+suffix[k]
            retain_cost=min_retain[k]
            cut=cut_cost<=optimum+delta
            retain=retain_cost!=inf and retain_cost<=optimum+delta
            if not (cut or retain):
                raise AssertionError("Source link has no within-budget partition")
            flags.append("O" if cut and retain else "C" if cut else "R")
        classes[delta]=tuple(flags)
    pair_impossible=tuple(
        not bool(advance(time_windows[k-1],time_windows[k],max_gap))
        for k in range(1,n)
    )
    # General constructive one-extra-cut theorem, independently validated
    # on synthetic finite worlds in tests.
    if 1 in classes:
        if any(flag=="R" for flag in classes[1]):
            raise AssertionError("+1 cut leaves a forced-retained link")
        if any((flag=="C") != impossible
               for flag,impossible in zip(classes[1],pair_impossible)):
            raise AssertionError("+1 forced cuts must be exactly impossible pairs")
    if 2 in classes and 1 in classes and classes[1]!=classes[2]:
        raise AssertionError("+2 cuts cannot change theorem's +1 classes")
    return {
        "minimum_cut_count":optimum-1,
        "class_by_delta":classes,
        "pair_impossible":pair_impossible,
    }


def audit(groups: dict) -> dict:
    _validate()
    previous=json.loads(PREVIOUS_RECEIPT.read_text(encoding="utf-8"))
    if previous["source_sha256"]!=SHA256:
        raise ValueError("Prior source receipt is not the same frozen file")
    if len(groups)!=421 or sum(len(x) for x in groups.values())!=28953:
        raise ValueError("Original 12h group/record counts drifted")
    counts={d: {w:Counter() for w in SHORT_NAMES} for d in DELTAS}
    joint_patterns={d:Counter() for d in DELTAS}
    affected_groups={d: {w:0 for w in SHORT_NAMES} for d in DELTAS}
    changed_from_optimum={w:Counter() for w in SHORT_NAMES}
    original_pair_impossible={w:Counter() for w in SHORT_NAMES}
    for rows in groups.values():
        by_world=[]
        for name,(scenario,clock) in zip(SHORT_NAMES,WORLDS):
            windows=[allowed_instants(row,scenario,clock) for row in rows]
            report=classify_budget_links(windows)
            by_world.append(report)
            original_pair_impossible[name]["links"]+=len(report["pair_impossible"])
            original_pair_impossible[name]["impossible"]+=sum(report["pair_impossible"])
            original_pair_impossible[name]["possible"]+=sum(not x for x in report["pair_impossible"])
            for d in DELTAS:
                flags=report["class_by_delta"][d]
                for letter,field in (("C","forced_cut"),("O","optional"),("R","forced_retain")):
                    counts[d][name][field]+=flags.count(letter)
                counts[d][name]["groups"]+=1
                counts[d][name]["minimum_cuts"]+=report["minimum_cut_count"]
                affected_groups[d][name]+=int("O" in flags)
            for before,after in zip(report["class_by_delta"][0],report["class_by_delta"][1]):
                if before!=after:
                    changed_from_optimum[name][before+"=>"+after]+=1
        for d in DELTAS:
            classifications=[data["class_by_delta"][d] for data in by_world]
            if len({len(x) for x in classifications})!=1:
                raise AssertionError("Clock models changed source record/link cardinality")
            for link in zip(*classifications):
                joint_patterns[d]["".join(link)]+=1

    prev_counts=list(previous["per_world"].values())
    # JSON keys can be serialized/sorted differently; compare by explicit labels.
    previous_labels=previous["world_order"]
    if len(previous_labels)!=4:
        raise ValueError("Prior output world roster drifted")
    for i,(name,oldkey) in enumerate(zip(SHORT_NAMES,previous_labels)):
        old=previous["per_world"][oldkey]
        now=counts[0][name]
        for k in ("forced_cut","optional","forced_retain"):
            if now[k]!=old[k]:
                raise ValueError("delta=0 source class result disagrees with pre-frozen PR753")
        if now["minimum_cuts"]!=old["minimum_cuts"]:
            raise ValueError("delta=0 source optimization objective drifted")
        for d in DELTAS:
            if sum(counts[d][name][x] for x in ("forced_cut","optional","forced_retain"))!=28532:
                raise AssertionError("Budget class counts must partition source links")
    for d in DELTAS:
        if sum(joint_patterns[d].values())!=28532:
            raise AssertionError("Four-world joint roster has wrong source denominator")
    if joint_patterns[0]!=Counter(previous["joint_forced_optional_class_patterns"]):
        raise ValueError("delta=0 joint link class table differs from precommitted PR753")
    if joint_patterns[1]!=joint_patterns[2]:
        raise ValueError("One-cut slack theorem contradicted by two-cut slack")
    return {
        "schema":"eog.mckee2024.post_stop_one_extra_cut_budget_receipt.v1",
        "status":"PLUS_ONE_CUT_COLLAPSES_OPTIMIZATION_CONDITIONAL_RETENTION__SOURCE_STOP",
        "source_sha256_verified":True,
        "source_sha256":SHA256,
        "source_bytes":1539661,
        "records":28953,
        "groups":421,
        "links":28532,
        "source_time_scenarios":[x["scenario"]+":"+x["clock"] for x in _validate()["worlds"]],
        "per_delta_per_world":{
            str(d):{name:dict(sorted(counts[d][name].items())) for name in SHORT_NAMES}
            for d in DELTAS
        },
        "joint_class_patterns":{
            str(d):dict(sorted(joint_patterns[d].items())) for d in DELTAS
        },
        "joint_all_world_mandatory":{
            str(d):{
                "forced_cut_in_all_four":joint_patterns[d]["CCCC"],
                "forced_retain_in_all_four":joint_patterns[d]["RRRR"],
                "not_universally_fixed":28532-joint_patterns[d]["CCCC"]-joint_patterns[d]["RRRR"]
            } for d in DELTAS
        },
        "groups_with_any_optional_cut":{
            str(d):affected_groups[d] for d in DELTAS
        },
        "previous_optimum_to_plus_one_class_transitions":{
            name:dict(sorted(changed_from_optimum[name].items()))
            for name in SHORT_NAMES
        },
        "local_pair_feasibility_counts":{
            name:dict(sorted(original_pair_impossible[name].items()))
            for name in SHORT_NAMES
        },
        "source_author_timestamp_semantics_verified":False,
        "source_author_CRS_verified":False,
        "IANA_DST_is_conditional":True,
        "dense_2h_holdout_opened":False,
        "SHP_geometry_accessed":False,
        "raw_ids_times_coordinates_or_link_indices_exported":False,
        "ecological_prediction_scored":False,
        "original_EOG_WF_scored_endpoints":3,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip",type=Path,required=True)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    _validate()
    groups,_=_source_rows(args.source_zip)
    result=audit(groups)
    payload=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.write_text(payload,encoding="utf-8")
    else:
        print(payload)


if __name__=="__main__":
    main()
