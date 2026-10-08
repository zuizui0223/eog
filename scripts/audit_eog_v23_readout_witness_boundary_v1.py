#!/usr/bin/env python3
"""Inspect which frozen v23 observation witnesses support mixed-only history ID.

Post-result forensic audit only. Reads the checksum-verified original v23 ZIP,
the frozen crossover receipt, and the previous five-class decomposition.
Never reruns a landscape, queries a biological response or changes the action library.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from audit_eog_history_readout_crossover_v1 import V23, load_v23

CLASSES=("000","001","011","101","111")
LAYOUTS=("clustered","dispersed")


def summarize(rows: dict, parent: dict, five_class: dict) -> dict:
    if len(rows)!=384 or parent["matched_landscapes"]!=384:
        raise ValueError("The originally frozen v23 landscape panel must remain 384")
    if parent["original_artifact_zip_sha256"]["v23"]!=V23["sha256"]:
        raise ValueError("The original source ZIP was substituted")
    if five_class["original_v23_sha256"]!=V23["sha256"]:
        raise ValueError("The original five-class receipt was substituted")
    if five_class["status"]!="POST_RESULT_DESCRIPTIVE_NOT_PREREGISTERED":
        raise ValueError("Post-result status was silently promoted")

    phase_counts={}
    mixed_action_times=Counter()
    total_mixed=0
    total_full_target_observation_mismatch=0
    for layout in LAYOUTS:
        classes=Counter()
        labels=Counter()
        class3_prov_failed=Counter()
        mixed_min_two_family_count=0
        mixed_confluence_informative=0
        mixed_count_target3_but_P_insufficient=0
        for key,row in rows.items():
            d=row["designs"][layout]
            if d["history_count"]!=3:
                raise ValueError(f"{key}: exactly three original histories required")
            p=d["plans"]
            outcome=tuple(p[x]["full_history"]["identified"]
                          for x in ("occupancy_only","provenance_only","combined"))
            if any(type(x) is not bool for x in outcome):
                raise ValueError("Identification must be boolean")
            classification="".join("1" if f else "0" for f in outcome)
            if classification not in CLASSES:
                raise ValueError(f"{key}: invalid exact identification class")
            classes[classification]+=1
            nclasses=d["provenance_class_count"]
            if nclasses not in (1,2,3):
                raise ValueError("Invalid frozen provenance-target equivalence count")
            labels[nclasses]+=1
            if nclasses==3 and not p["provenance_only"]["full_history"]["identified"]:
                class3_prov_failed[classification]+=1
                # The target covers ALL occupied nodes whereas provenance actions
                # deliberately exclude SOURCE nodes, so P non-identifiability
                # does NOT contradict 3 classes in the unobserved full target.
                total_full_target_observation_mismatch+=1
            if classification!="001":
                continue

            total_mixed+=1
            witness=p["combined"]["full_history"]["minimum_action_ids"]
            size=p["combined"]["full_history"]["minimum_size"]
            if size!=2 or len(witness)!=2:
                raise ValueError("Mixed-only history ID requires an exact pair of actions")
            occupation=[x for x in witness if x.startswith("O_")]
            provenance=[x for x in witness if x.startswith("P_")]
            if len(occupation)!=1 or len(provenance)!=1:
                raise ValueError("Mixed-only minimum must contain both action families")
            mixed_action_times[occupation[0]]+=1
            mixed_min_two_family_count+=1
            if d["informative_unique_origin_provenance_action_count"]!=0:
                raise ValueError("Unique-origin provenance action unexpectedly history-informative")
            if d["informative_confluence_provenance_action_count"]<1:
                raise ValueError("Selected provenance tag has no eligible confluence location")
            mixed_confluence_informative+=1
            if nclasses==3 and not p["provenance_only"]["full_history"]["identified"]:
                mixed_count_target3_but_P_insufficient+=1

        if sum(classes.values())!=384:
            raise ValueError("Layout lost rows")
        if dict(classes)!={k:v for k,v in five_class["layouts"][layout]["truth_table"].items() if v}:
            raise ValueError("Five-class v23 decomposition changed")
        phase_counts[layout]={
            "n":384,
            "strict_mixed_only":classes["001"],
            "strict_mixed_exactly_one_occupancy_and_one_provenance":mixed_min_two_family_count,
            "strict_mixed_has_history_informative_confluence":mixed_confluence_informative,
            "strict_mixed_full_provenance_target3_but_non_source_P_unresolved":
                mixed_count_target3_but_P_insufficient,
            "original_provenance_target_class_distribution":
                {str(k):labels[k] for k in (1,2,3)},
            "full_provenance_target3_but_non_source_provenance_library_fails":{
                k:class3_prov_failed[k] for k in CLASSES if class3_prov_failed[k]
            },
            "full_provenance_target3_but_non_source_provenance_library_fails_total":
                sum(class3_prov_failed.values()),
        }
    if total_mixed!=five_class["true_mixed_library_synergy_designs"]:
        raise ValueError("18-case original synergy amount changed")
    if set(mixed_action_times)!={"O_t4"}:
        raise ValueError("The canonical mixed-only observation time is no longer t4")
    if sum(mixed_action_times.values())!=total_mixed:
        raise ValueError("Mixed witness count does not reconcile")

    return {
        "schema":"eog.virtual_worlds.v23_readout_witness_boundary.v1",
        "status":"POST_RESULT_FORENSIC_NO_NEW_SIMULATION",
        "source_artifact_id":V23["id"],
        "source_artifact_sha256":V23["sha256"],
        "source_result_fingerprint":V23["fingerprint"],
        "matched_landscapes":384,
        "paired_layouts_per_landscape":2,
        "mixed_only_total_layout_cases":total_mixed,
        "mixed_witness_occupancy_action_counts":dict(mixed_action_times),
        "mixed_witnesses_all_exactly_one_snapshot_plus_one_provenance_tag":True,
        "full_target3_but_non_source_P_library_nonidentifiable_layout_cases":
            total_full_target_observation_mismatch,
        "by_layout":phase_counts,
        "reason_for_target_observation_gap":(
            "provenance_class_count classifies complete equilibrium provenance maps "
            "including source nodes, whereas all P_node measurements exclude source nodes. "
            "A full-target three-class difference may therefore remain unresolved by "
            "the narrower non-source provenance observation library."
        ),
        "formal_three_history_boundary":(
            "When neither observation family distinguishes all three histories but "
            "a two-action O+P witness does, the two actions must separate different "
            "history pairs. This is a finite partition fact, not a biological causal discovery."
        ),
        "source_node_exclusion_is_the_only_inferred_reason_in_some_cases":(
            "Only the target-class versus observed-library scope mismatch is established. "
            "The frozen v23 per-row summary does not expose raw action signatures or "
            "identify the precise hidden source-node contrast for each pair."
        ),
        "claim_boundary":[
            "Original v23 protocols and virtual-world outcomes are unchanged.",
            "No novel biological dispersal, extinction, history-storage or memory mechanism is identified.",
            "The O_t4 witness is in structural propagation steps, not a field census time.",
            "A synthetic earliest-source tag at a confluence node is not observed ancestry or calibrated gene flow.",
            "A post-result exact witness count is not an independent confirmatory replication.",
            "Do not reopen the consumed EOG-WF/Glanville/NEON response programmes or the existing article claims."
        ],
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v23",required=True,type=Path)
    parser.add_argument("--parent",required=True,type=Path)
    parser.add_argument("--five-class",required=True,type=Path)
    parser.add_argument("--assert-frozen",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    report=summarize(
        load_v23(args.v23),
        json.loads(args.parent.read_text(encoding="utf-8")),
        json.loads(args.five_class.read_text(encoding="utf-8")),
    )
    expect=json.loads(args.assert_frozen.read_text(encoding="utf-8"))
    if report!=expect:
        raise ValueError("Result disagrees with frozen forensic summary")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({"status":report["status"],"mixed_only":report["mixed_only_total_layout_cases"],
                      "target_observation_gap":report["full_target3_but_non_source_P_library_nonidentifiable_layout_cases"]},sort_keys=True))


if __name__=="__main__":
    main()
