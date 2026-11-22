"""Bridge authentic wetland observation gates to EOG source-policy counterexample.

Native wetland CSV: records real source-positive witnesses split across date
and method, but supplies neither an actual transition graph nor a true
geographic source policy for EOG inference. The three EOG operators below are
purely SYNTHETIC A/B/C graph objects. Exact EOG native APIs are used for both
fixed-source world reconstruction and self-excluded peer-source diagnostics.

A filtered occurrence set can contract the self-excluded compatible rule set:
this does not contradict fixed-source positive-only monotonicity, since the
peer-source envelope changes when an occurrence is filtered out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from eog.v2.occurrence_constraints import evaluate_occurrence_rule_compatibility
from eog.v2.world_reconstruction import (
    FiniteWorld, compare_reconstructions, reconstruct_compatible_worlds,
)

from benchmarks import wetland_joint_method_calendar_gate_v1 as joint
from benchmarks import wetland_method_channel_lattice_v1 as source

NODE_IDS=("A","B","C")
OBSERVATION_SETS={"all_three":("A","B","C"),"gated_two":("A","B")}
SYNTHETIC_EDGES={
    "hub":(("A","C"),("C","A"),("B","C"),("C","B")),
    "isolated_C":(("A","B"),("B","A")),
    "complete":(
        ("A","B"),("B","A"),("A","C"),("C","A"),
        ("B","C"),("C","B")
    ),
}
SOURCE_SITE="orditoi-zsilip"
SOURCE_SPECIES="Hyla arborea"
ORIGINAL_WITNESS_EXPECTED={
    ("2024-03-24","visual",6),
    ("2024-05-30","dipnet",368),
}


def synthetic_worlds():
    """Frozen toy graph universe: nodes are never geographic wetland sites."""
    worlds=[]
    for name in sorted(SYNTHETIC_EDGES):
        edges=SYNTHETIC_EDGES[name]
        operator=build_dynamic_transition_operator(
            NODE_IDS,
            [DynamicReachabilityEdge(
                source=NODE_IDS.index(a),target=NODE_IDS.index(b),
                geographic_support=1.0
            )for a,b in edges],
            loss_support=1.0
        )
        worlds.append(FiniteWorld(name,operator,("A",)))
    if len(worlds)!=3 or any(w.operator.node_ids!=NODE_IDS for w in worlds):
        raise ValueError("finite synthetic graph universe changed")
    return tuple(worlds)


def target_details(result):
    return [{
        "target":x.target_id,
        "source_ids":list(x.source_ids),
        "first_passage_support":x.first_passage_support,
        "first_positive_step":x.first_positive_step
    }for x in result.targets]


def evaluate_source_policies(worlds):
    """Use actual EOG APIs, with unchanged world operator fingerprints."""
    all_obs=OBSERVATION_SETS["all_three"]
    gated=OBSERVATION_SETS["gated_two"]
    # Fixed declared source A remains in both occurrence lists.
    all_fixed=reconstruct_compatible_worlds(worlds,all_obs,max_steps=1)
    gated_fixed=reconstruct_compatible_worlds(worlds,gated,max_steps=1)
    update=compare_reconstructions(gated_fixed,all_fixed)
    fixed={
        label:{
            "observed_positive_nodes":list(obs),
            "compatible_world_ids":list(result.compatible_world_ids),
            "incompatible_world_ids":list(result.incompatible_world_ids),
            "world_compatibility":{
                x.world_id:{
                    "compatible":x.compatible,
                    "unsupported_occurrence_ids":list(x.occurrence_result.unsupported_occurrence_ids),
                    "source_policy":x.occurrence_result.source_policy,
                    "fixed_source_ids":list(x.occurrence_result.fixed_source_ids),
                    "targets":target_details(x.occurrence_result)
                }for x in result.world_results
            },
            "reconstruction_fingerprint":result.fingerprint,
            "coverage_certificate":result.coverage_certificate
        } for label,obs,result in (
            ("all_three",all_obs,all_fixed),
            ("gated_two",gated,gated_fixed)
        )
    }
    if (tuple(all_fixed.compatible_world_ids)!=("complete",)
        or tuple(gated_fixed.compatible_world_ids)!=("complete","isolated_C")
        or tuple(update.retained_world_ids)!=("complete",)
        or tuple(update.eliminated_world_ids)!=("isolated_C",)):
        raise ValueError("fixed-source EOG monotone positive compatibility witness changed")
    if not set(all_fixed.compatible_world_ids)<=set(gated_fixed.compatible_world_ids):
        raise ValueError("fixed-source compatible world set violated frozen positive monotonicity")

    peer_results={}
    for name,obs in OBSERVATION_SETS.items():
        peer_results[name]={}
        for world in worlds:
            result=evaluate_occurrence_rule_compatibility(
                world.operator,obs,
                rule_id=world.world_id,max_steps=1,
                fixed_source_ids=None
            )
            if result.source_policy!="self_excluded" or result.fixed_source_ids:
                raise ValueError("self-excluded target sources incorrectly held fixed")
            peer_results[name][world.world_id]={
                "compatible":not result.unsupported_occurrence_ids,
                "unsupported_occurrence_ids":list(result.unsupported_occurrence_ids),
                "coverage_fraction":result.coverage_fraction,
                "targets":target_details(result),
                "occurrence_fingerprint":result.fingerprint,
                "operator_fingerprint":result.operator_fingerprint,
                "source_policy":result.source_policy
            }
    self_sets={
        label:sorted(world_id for world_id,v in results.items() if v["compatible"])
        for label,results in peer_results.items()
    }
    if self_sets!={
        "all_three":["complete","hub"],
        "gated_two":["complete","isolated_C"]
    }:
        raise ValueError(f"self-excluded nonmonotone counterexample changed: {self_sets}")
    gains=sorted(set(self_sets["gated_two"])-set(self_sets["all_three"]))
    losses=sorted(set(self_sets["all_three"])-set(self_sets["gated_two"]))
    if gains!=["isolated_C"] or losses!=["hub"]:
        raise ValueError("self-excluded gated compatible world switch not reproduced")

    fingerprints={
        w.world_id:w.fingerprint for w in worlds
    }
    return {
        "graph_universe_status":"SYNTHETIC_DECLARED_ABSTRACT_ABC_NOT_ECOLOGICAL_WETLAND_WORLDS",
        "observed_nodes":{
            k:list(v) for k,v in OBSERVATION_SETS.items()
        },
        "declared_sources_always_fixed_in_world_definitions":["A"],
        "world_definitions":[{
            "world_id":w.world_id,
            "operator_fingerprint":w.operator.fingerprint,
            "world_fingerprint":w.fingerprint,
            "directed_edges":[list(pair) for pair in SYNTHETIC_EDGES[w.world_id]],
            "source_ids":list(w.source_ids)
        } for w in worlds],
        "world_operator_fingerprints_frozen_across_both_observation_sets":True,
        "max_steps":1,
        "fixed_source":{
            "evaluation_API":"eog.v2.world_reconstruction.reconstruct_compatible_worlds",
            "results":fixed,
            "compatibility_before_all_occurrences":list(all_fixed.compatible_world_ids),
            "compatibility_after_dropping_C":list(gated_fixed.compatible_world_ids),
            "positive_constraint_loss_expands_compatible_set":True,
            "added_positive_EOG_native_compare_reconstructions_update":{
                "retained_world_ids":list(update.retained_world_ids),
                "eliminated_world_ids":list(update.eliminated_world_ids),
                "contraction_fraction":update.contraction_fraction,
                "after_addition_compatible_set_narrowed":True,
                "fingerprint":update.fingerprint
            }
        },
        "self_excluded":{
            "evaluation_API":"eog.v2.occurrence_constraints.evaluate_occurrence_rule_compatibility",
            "results":peer_results,
            "compatible_sets":self_sets,
            "gained_compatible_worlds_after_dropping_C":gains,
            "lost_compatible_worlds_after_dropping_C":losses,
            "both_sets_have_equal_compatible_world_count_but_different_membership":True,
            "self_excluded_monotone_world_set_inclusion_claim_valid":False,
            "NOT_eligible_for_EOG_fixed_source_compare_reconstructions":True
        },
        "real_wetland_nodes_mapped_to_synthetic_ABC":False
    }


def authenticate_wetland_split(surveys_path,sites_path):
    """Actual raw witness truth is separate from the toy graph experiment."""
    source.sha_guard(surveys_path,source.SURVEY_SHA,"surveys")
    source.sha_guard(sites_path,source.SITE_SHA,"sites")
    data,cols=source.read_csv(surveys_path)
    sites,_=source.read_csv(sites_path)
    taxa=[c for c in cols if c not in source.META]
    q1,_,_=source.validate_source(data,sites,taxa)
    if len(q1)!=27 or SOURCE_SITE not in q1:
        raise ValueError("pinned Q1 site source changed")
    indexed=[{**r,"_original_csv_line":str(i)} for i,r in enumerate(data,2)]
    rows=[r for r in indexed if r["site"]==SOURCE_SITE]
    original_dates=sorted({r["date"] for r in rows})
    if len(original_dates)<2:
        raise ValueError("authentic witness site no longer has multiple dates")
    last_day=date.fromisoformat(original_dates[-1])
    last_14={d for d in original_dates
             if (last_day-date.fromisoformat(d)).days<=14}
    positive=[r for r in rows if int(r[SOURCE_SPECIES])>0]
    if {(r["date"],r["method"],int(r["_original_csv_line"])) for r in positive}!=ORIGINAL_WITNESS_EXPECTED:
        raise ValueError("original 2-row cross-method calendar witness changed")
    av_all=[r for r in positive if r["method"] in ("acoustic","visual")]
    full_inside=[r for r in positive if r["date"] in last_14]
    av_inside=[r for r in av_all if r["date"] in last_14]
    if not av_all or not full_inside or av_inside:
        raise ValueError("original wetland split-method/time observation witness vanished")
    all_q1=[r for r in indexed if r["site"] in q1]
    q2={site:cat for site,cat in q1.items() if cat=="intervention"}
    first=joint.cohort_result(all_q1,q1,taxa,"published_q1")
    second=joint.cohort_result(
        [r for r in all_q1 if r["site"] in q2],q2,taxa,"published_q2"
    )
    def last14(record):
        return next(w for w in record["windows"]
                    if w["anchor"]=="last" and w["horizon_calendar_days"]==14)
    q1_row=last14(first)
    q2_row=last14(second)
    if (q1_row["class_split_witness_interaction"],
        q2_row["class_split_witness_interaction"],
        q1_row["native_AV_window_positive_pairs"],
        q2_row["native_AV_window_positive_pairs"])!=(16,9,48,25):
        raise ValueError("previous original-source 16/9 crossed witness benchmark changed")
    example=next(r for r in first["positive_pair_window_detail"]
        if r["anchor"]=="last" and r["horizon_days"]==14
           and r["site"]==SOURCE_SITE and r["species"]==SOURCE_SPECIES)
    if (example["witness_class"]!="split_witness_interaction"
        or example["AV_window_recorded_positive"]!=0
        or example["full_window_recorded_positive"]!=1):
        raise ValueError("original row-level witness and joint panel disagree")
    return {
        "source_record_status":"ACTUAL_PUBLISHED_SURVEY_ROWS_NOT_ECOLOGICAL_WORLD_NODES",
        "site":SOURCE_SITE,"species":SOURCE_SPECIES,
        "original_site_dates":original_dates,
        "actual_last14_calendar_dates":sorted(last_14),
        "original_source_full_positive":True,
        "original_source_AV_all_dates_positive":True,
        "original_source_full_last14_positive":True,
        "original_source_AV_last14_positive":False,
        "source_positive_rows":[{
            "date":r["date"],
            "method":r["method"],
            "native_original_CSV_line":int(r["_original_csv_line"]),
            "inside_site_last14":r["date"] in last_14
        }for r in positive],
        "last14_site_species_witness_class":example["witness_class"],
        "full_Q1_144_positive_pairs_last14_AV_retained":q1_row["native_AV_window_positive_pairs"],
        "Q1_last14_split_witness_pairs":q1_row["class_split_witness_interaction"],
        "Q2_last14_split_witness_pairs":q2_row["class_split_witness_interaction"],
        "source_method_row_absence_not_verified_field_non_deployment":True,
        "source_no_true_biological_absence_certified":True
    }


def run(surveys_path,sites_path):
    wetland=authenticate_wetland_split(surveys_path,sites_path)
    graph=evaluate_source_policies(synthetic_worlds())
    result={
        "schema":"eog.wetland_observation_source_policy_bridge_v1.result",
        "status":"PINNED_ORIGINAL_WETLAND_WITNESS_AND_REAL_EOG_FINITE_SYNTHETIC_POLICY_CONTRAST",
        "analysis_scope":"POST_EXPOSURE_SOURCE_OBSERVATION_GATE_PLUS_SYNTHETIC_EOG_COUNTEREXAMPLE",
        "source_sha256":{"surveys":source.SURVEY_SHA,"sites":source.SITE_SHA},
        "original_wetland_positive_witness":wetland,
        "native_EOG_policy_counterexample":graph,
        "observed_field_world_mapping_or_geographic_graph_constructed":False,
        "real_ecological_movement_worlds_evaluated":False,
        "original_R_unmarked_occupancy_model_fitted":False,
        "new_EOG_WF_scored_empirical_endpoint_added":False,
        "limits":[
            "The original wetland positive record is REAL; A,B,C synthetic nodes/edges are not fitted observed wetland distributions or sources and are never mapped to real sites.",
            "Fixed-source compatibility is monotone under positive evidence accumulation only when the finite world universe, declared world sources and reachability contracts remain identical.",
            "Self-excluded peer-source compatibility has an evidence-dependent source set; its compatible world-set membership can both expand and contract when an observed occurrence is removed.",
            "The fixed-source world reconstruction native comparison must NOT be applied to self-excluded occurrence-rule compatibility outcomes.",
            "Dropping a wetland source-positive under method×calendar filtering is a recording loss, NOT biological site absence, ecological movement or restoration treatment effect.",
            "No new ecological A/B/M, independent field validation, true negative, actual ecological finite-world enumeration, or fourth EOG-WF scored endpoint."
        ]
    }
    result["fingerprint"]=hashlib.sha256(json.dumps(
        result,sort_keys=True,separators=(",",":"),allow_nan=False
    ).encode()).hexdigest()
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--surveys",type=Path,required=True)
    ap.add_argument("--sites",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    output=run(args.surveys,args.sites)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print("EOG_WETLAND_OBSERVATION_SOURCE_POLICY_BRIDGE="+json.dumps({
        "fingerprint":output["fingerprint"],
        "real_split_witness":output["original_wetland_positive_witness"],
        "fixed_compatible_full":output["native_EOG_policy_counterexample"]["fixed_source"]["compatibility_before_all_occurrences"],
        "fixed_compatible_gated":output["native_EOG_policy_counterexample"]["fixed_source"]["compatibility_after_dropping_C"],
        "self_compatible_sets":output["native_EOG_policy_counterexample"]["self_excluded"]["compatible_sets"],
        "self_gained_on_gating":output["native_EOG_policy_counterexample"]["self_excluded"]["gained_compatible_worlds_after_dropping_C"],
        "self_lost_on_gating":output["native_EOG_policy_counterexample"]["self_excluded"]["lost_compatible_worlds_after_dropping_C"],
        "real_ecological_worlds":output["real_ecological_movement_worlds_evaluated"]
    },sort_keys=True))
