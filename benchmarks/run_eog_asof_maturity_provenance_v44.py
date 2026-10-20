#!/usr/bin/env python3
"""v44: prevent information after Tstar entering synthetic maturity-state inference.

The target Tstar and three activation histories are ORIGINAL v26/v41 models.
This is retrospective-vs-as-of-time theoretical evidence accounting, not a
prospectively evaluated ecological field model; Tstar itself is model-aided.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from benchmarks import run_eog_provenance_ecological_state_v41 as old
from benchmarks.run_eog_provenance_uncertainty_v42 import deterministic_risk

PROTOCOL=ROOT/"validation/eog_original_idea_asof_maturity_v44/protocol_v44.json"
V42=ROOT/"validation/eog_provenance_uncertainty_decomposition_v42/result_locked_v42.json"
V43=ROOT/"validation/eog_original_idea_temporal_evidence_v43/result_locked_v43.json"
SOURCE_V41="34f6f2bd94b9b22854eb699c97607ec2b9408f0ea55bcd6d5103a4019581125d"
SOURCE_V42="32887217c613ea92fd20e32d60d0a7e93ef8355c628ea955f968bec98436e273"
SOURCE_V43="04f24a88911b76da4c112a827dd4df4694152ff92dd350d413056f007ef05446"
CENSUSES=(4,5,6,8)
TARGET="persistent_threshold_lag2"
SUBSETS=("all","target_age_defined","Tstar_lt8","Tstar_ge8",
         "retro_occupancy_history_alias","asof_occupancy_maturity_ambiguous",
         "retrospective_12_perfect_source_aliases")
EPS=1e-9
PREDICTIONS=(
    "AS1_retrospective_occupancy_uses_later_than_target_data",
    "AS2_asof_cutoff_exposes_more_uncertain_maturity_worlds",
    "AS3_full_provenance_does_not_close_all_asof_maturity_aliases",
    "AS4_noisy_source_tags_retain_asof_target_information",
    "AS5_forbidden_future_occupancy_cannot_improve_asof_result",
)
SCHEMA="eog.original_idea.asof_time_maturity_provenance.result.v44"
SAFETY={
    "individual_real_genetic_recruitment_or_2026_camera_data_read":False,
    "actual_prospective_field_validation":False,
    "maturity_fitness_or_survival_empirically_measured":False,
    "Tstar_predicted_independently_of_candidate_models":False,
    "this_is_post_v43_design_sensitivity_not_independent_replication":True,
    "original_v41_to_v43_protocols_and_12_realization_unmodified":True,
    "no_fourth_EOG_WF_predictive_endpoint":True,
    "EOG_WF_3_scored_31_STOP_3_administrative_unchanged":True
}


def canonical(v)->bytes:
    return json.dumps(v,sort_keys=True,separators=(',',':'),
                      ensure_ascii=False,allow_nan=False).encode('utf-8')


def verify_frozen(p:dict,v42:dict,v43:dict)->None:
    if (
        p.get("schema")!="eog.original_idea.asof_time_maturity_provenance.protocol.v44"
        or p.get("status")!="FROZEN_BEFORE_ASOF_TIME_RESCORING__AFTER_V43_CHRONOLOGY_EXPOSED"
        or p["parent"].get("base_commit")!="8d9b83888be491764a51978802ccafd2fda3e3d1"
        or p["parent"]["v41_complete_canonical_sha256"]!=SOURCE_V41
        or p["parent"]["v42_complete_canonical_sha256"]!=SOURCE_V42
        or p["parent"]["v43_complete_canonical_sha256"]!=SOURCE_V43
        or v42["canonical_result_sha256"]!=SOURCE_V42
        or v43["authority"]["complete_result_sha256"]!=SOURCE_V43
        or v43["verified_counts"]["past_state_conditioned_on_later_t8_snapshot"]!=12
    ):
        raise ValueError("Frozen original v41-v43 source or as-of-time protocol changed")
    design=p.get("design",{})
    if not (
        design.get("full_occupancy_observation_times")==list(CENSUSES)
        and design.get("no_real_genetic_or_survey_data") is True
        and design.get("no_refit_of_source_graph_or_mature_target") is True
        and "only those original occupancy snapshots whose timestamp <= Tstar"
            in design.get("asof_information","")
        and "after target" in design.get("original_retrospective_information","")
        and design.get("source_assay","").startswith("identical original v39")
    ):
        raise ValueError("As-of cutoff, frozen maturity target or source channel altered")
    if (
        tuple(x["id"] for x in p.get("predeclared_predictions",[]))!=PREDICTIONS
        or p.get("safety")!=SAFETY
        or p.get("outcomes",{}).get("sampling_strata")!=list(SUBSETS)
        or p.get("outcomes",{}).get("never_leak_Tstar_future_readings") is not True
    ):
        raise ValueError("v44 predeclared targets, safeguards or denominators changed")


def filter_snapshots(occ:dict, present_t:int|None,
                     times:tuple=CENSUSES)->dict:
    """Select only original timestamps <= the candidate-model target horizon."""
    if len(times)!=4 or tuple(times)!=CENSUSES:
        raise ValueError("Cannot change original four observation dates")
    allowed=tuple(i for i,t in enumerate(times) if present_t is not None and t<=present_t)
    return {h:tuple(occ[h][i] for i in allowed) for h in occ}


def source_augmented(occ:dict, tags:dict)->dict:
    sites=tuple(sorted(tags))
    return {h:(occ[h],tuple(tags[site][h] for site in sites)) for h in occ}


def compare_world(
    retro_occ:dict, asof_occ:dict, target:dict, tags:dict, selected:dict,
    *,
    target_time:int|None
)->dict:
    """Exact conditional risks under strictly nested original data sets."""
    retro=deterministic_risk(retro_occ,target)
    asof=deterministic_risk(asof_occ,target)
    retro_full=deterministic_risk(source_augmented(retro_occ,tags),target)
    asof_full=deterministic_risk(source_augmented(asof_occ,tags),target)
    for metric in ("entropy_bits","bayes_error"):
        if (
            asof[metric]+EPS<retro[metric]
            or asof_full[metric]+EPS<retro_full[metric]
            or retro_full[metric]>retro[metric]+EPS
            or asof_full[metric]>asof[metric]+EPS
        ):
            raise ValueError("Some future relative-to-Tstar evidence was treated as old information")
    policies={}
    for policy,sites in selected.items():
        earlier=old.target_bayes_information(retro_occ,target,tags,tuple(sites),0.6,0.1)
        cutoff=old.target_bayes_information(asof_occ,target,tags,tuple(sites),0.6,0.1)
        for sub,base in ((earlier,retro),(cutoff,asof)):
            if (
                abs(sub["base_conditional_entropy_bits"]-base["entropy_bits"])>EPS
                or abs(1-sub["base_bayes_correct_target_probability"]-base["bayes_error"])>EPS
            ):
                raise ValueError("Changed original uniform-three-history target conditioning")
        policies[policy]={
            "retrospective_added_information_bits":earlier["information_bits"],
            "asof_added_information_bits":cutoff["information_bits"],
            "retrospective_bayes_target_accuracy_gain":earlier["bayes_correct_target_gain"],
            "asof_bayes_target_accuracy_gain":cutoff["bayes_correct_target_gain"],
        }
    return {
        "retrospective_baseline":retro,
        "asof_baseline":asof,
        "retrospective_complete_source_upper_bound":retro_full,
        "asof_complete_source_upper_bound":asof_full,
        "policies":policies,
        "asof_original_census_count":sum(t<=target_time for t in CENSUSES) if target_time is not None else 0,
        "target_is_directly_measured_by_an_original_asof_census":
            target_time is not None and (target_time-2) in CENSUSES
    }


def _avg(xs):
    return sum(xs)/len(xs) if xs else None


def summarize(rows:list[dict])->list[dict]:
    out=[]
    for policy in old.POLICIES:
        for subset in SUBSETS:
            selected=[r for r in rows if r["strata"][subset]]
            def avg(key):
                return _avg([r["policies"][policy][key] for r in selected])
            out.append({
                "policy":policy,"subset":subset,"world_count":len(selected),
                "retrospective_mean_information_bits":avg("retrospective_added_information_bits"),
                "asof_mean_information_bits":avg("asof_added_information_bits"),
                "retrospective_mean_bayes_target_accuracy_gain":
                    avg("retrospective_bayes_target_accuracy_gain"),
                "asof_mean_bayes_target_accuracy_gain":
                    avg("asof_bayes_target_accuracy_gain")
            })
    return out


def run()->tuple[dict,list[dict]]:
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    v42=json.loads(V42.read_text(encoding="utf-8"))
    v43=json.loads(V43.read_text(encoding="utf-8"))
    verify_frozen(p,v42,v43)
    full_original_v41=old.run()
    if hashlib.sha256(canonical(full_original_v41)).hexdigest()!=SOURCE_V41:
        raise ValueError("Complete original v41 source result changed")
    rows=[]
    counts=Counter({
        "all_design_rows":0,"target_age_defined":0,"target_age_undefined":0,
        "retro_occupancy_history_aliased":0,
        "retrospective_maturity_ambiguous":0,
        "asof_maturity_ambiguous":0,
        "retrospective_complete_source_maturity_ambiguous":0,
        "asof_complete_source_maturity_ambiguous":0,
        "late_census_t8_after_target":0,
        "asof_original_census_direct_target_identity":0,
        "negative_monotonicity_violations":0
    })
    census_counts=Counter({str(k):0 for k in range(5)})
    for autocorr in old.AUTOCORR_LEVELS:
      for neighbourhood in old.NEIGHBOURHOODS:
        for replicate in range(old.REPLICATES):
          base=old._generate_base(replicate,autocorr,neighbourhood)
          outlet=old._outlet_corner(replicate,autocorr,neighbourhood)
          anchor=old._truth_source(base,outlet)
          candidates,_=old._candidate_sources(base,outlet,anchor)
          sourcesets=old._source_sets(candidates,anchor)
          if not sourcesets:
              raise ValueError("A fixed original source-world design has become ineligible")
          for barrier in old.BARRIER_LEVELS:
            _,graph=old._graphs(base,barrier,old.RULE,outlet)
            for geometry in old.DESIGNS:
              src=sourcesets[geometry][3]
              key=f"{replicate}|{autocorr}|{neighbourhood}|{barrier}|{geometry}"
              design=old.prepare_design(graph,src,key)
              targets=old._synthetic_present_targets(graph,src)
              mature=targets[TARGET]
              distances=old._distances(graph,src)
              firsts={}
              nodes=None
              for h,activation in old.ACTIVATION_HISTORIES.items():
                  eq,first,_=old._arrival_structure(distances,src,activation)
                  non_source=frozenset(eq)-frozenset(src)
                  if nodes is None:
                      nodes=non_source
                  elif nodes!=non_source:
                      raise ValueError("Original v23 non-source equilibrium union was not common")
                  firsts[h]=first
              Tstar=(max(firsts[h][n] for h in firsts for n in nodes)
                     if nodes else None)
              retro_occ=design["occupancy"]
              asof_occ=filter_snapshots(retro_occ,Tstar)
              result=compare_world(retro_occ,asof_occ,mature,design["provenance_tags"],
                                   design["selected"],target_time=Tstar)
              retro_unsure=result["retrospective_baseline"]["entropy_bits"]>EPS
              asof_unsure=result["asof_baseline"]["entropy_bits"]>EPS
              retro_full_unsure=result["retrospective_complete_source_upper_bound"]["entropy_bits"]>EPS
              asof_full_unsure=result["asof_complete_source_upper_bound"]["entropy_bits"]>EPS
              counts["all_design_rows"]+=1
              counts["target_age_defined"]+=int(Tstar is not None)
              counts["target_age_undefined"]+=int(Tstar is None)
              counts["late_census_t8_after_target"]+=int(Tstar is not None and Tstar<8)
              counts["retro_occupancy_history_aliased"]+=int(not design["occupancy_exact_history_identifiable"])
              counts["retrospective_maturity_ambiguous"]+=int(retro_unsure)
              counts["asof_maturity_ambiguous"]+=int(asof_unsure)
              counts["retrospective_complete_source_maturity_ambiguous"]+=int(retro_full_unsure)
              counts["asof_complete_source_maturity_ambiguous"]+=int(asof_full_unsure)
              counts["asof_original_census_direct_target_identity"]+=int(
                  result["target_is_directly_measured_by_an_original_asof_census"])
              census_counts[str(result["asof_original_census_count"])]+=1
              strata={
                "all":True,
                "target_age_defined":Tstar is not None,
                "Tstar_lt8":Tstar is not None and Tstar<8,
                "Tstar_ge8":Tstar is not None and Tstar>=8,
                "retro_occupancy_history_alias":not design["occupancy_exact_history_identifiable"],
                "asof_occupancy_maturity_ambiguous":asof_unsure,
                "retrospective_12_perfect_source_aliases":retro_full_unsure
              }
              rows.append({
                "design_key":key,"geometry":geometry,"neighborhood":neighbourhood,
                "target_Tstar":Tstar,"non_source_node_count":len(nodes),
                "strata":strata,
                "retrospective_maturity_ambiguous":retro_unsure,
                "asof_maturity_ambiguous":asof_unsure,
                "retrospective_full_source_maturity_ambiguous":retro_full_unsure,
                "asof_full_source_maturity_ambiguous":asof_full_unsure,
                **result
              })
    expected={"all_design_rows":768,"retro_occupancy_history_aliased":189,
              "retrospective_maturity_ambiguous":48,
              "retrospective_complete_source_maturity_ambiguous":12}
    if any(counts[k]!=v for k,v in expected.items()):
        raise ValueError(f"Exact original v41-v43 population drifted: {dict(counts)}")
    if (
        sum(census_counts.values())!=768
        or counts["asof_maturity_ambiguous"]<48
        or counts["asof_complete_source_maturity_ambiguous"]<12
        or sum(r["strata"]["retrospective_12_perfect_source_aliases"] for r in rows)!=12
        or any(r["target_Tstar"] not in (3,4) for r in rows if r["strata"]["retrospective_12_perfect_source_aliases"])
    ):
        raise ValueError("As-of and retrospective nested target information inconsistent")
    primary=[r for r in rows if r["strata"]["asof_occupancy_maturity_ambiguous"]]
    # No pass/fail conditioning on new effect sizes.
    summary=summarize(rows)
    confluence=next(s for s in summary if s["policy"]=="confluence_targeted"
                   and s["subset"]=="asof_occupancy_maturity_ambiguous")
    verdicts={
        PREDICTIONS[0]:"SUPPORTED" if counts["late_census_t8_after_target"]>=12 else "REFUTED",
        PREDICTIONS[1]:"SUPPORTED" if counts["asof_maturity_ambiguous"]>48 else "REFUTED",
        PREDICTIONS[2]:"SUPPORTED" if counts["asof_complete_source_maturity_ambiguous"]>=12 else "REFUTED",
        PREDICTIONS[3]:"SUPPORTED" if confluence["asof_mean_information_bits"] is not None and
            any(r["policies"]["confluence_targeted"]["asof_added_information_bits"]>EPS for r in primary)
            else "REFUTED",
        PREDICTIONS[4]:"SUPPORTED" if counts["negative_monotonicity_violations"]==0 else "REFUTED"
    }
    pscount=[r for r in rows if r["strata"]["retrospective_12_perfect_source_aliases"]]
    return {
        "schema":SCHEMA,
        "status":"SOURCE_AUTHENTICATED_ASOF_VS_RETROSPECTIVE_SYNTHETIC_MATURITY__NO_FIELD_FORECAST",
        "parent_complete_v41_sha256":SOURCE_V41,
        "base_main_commit":p["parent"]["base_commit"],
        "counts":dict(counts),
        "asof_available_original_census_count_distribution":dict(census_counts),
        "retro_12_audit":{
            "world_count":len(pscount),
            "original_last_census_after_target_count":sum(r["target_Tstar"] is not None and r["target_Tstar"]<8 for r in pscount),
            "asof_maturity_ambiguous_count":sum(r["asof_maturity_ambiguous"] for r in pscount),
            "asof_complete_source_maturity_ambiguous_count":sum(r["asof_full_source_maturity_ambiguous"] for r in pscount),
            "non_source_node_count_distribution":dict(Counter(str(r["non_source_node_count"]) for r in pscount))
        },
        "summary_by_policy_and_cutoff_subset":summary,
        "predeclared_verdicts":verdicts,
        "scientific_boundary":SAFETY,
        "model_based_target_horizon_is_not_a_preannounced_field_forecast_time":True,
        "individual_bird_genotypes_or_actual_maturity_read":False,
        "new_EOG_WF_endpoint_scored":False
    },rows


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise ValueError("Refuse to overwrite as-of evidence")
    out,rows=run()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    (args.output_dir/"scenario_768.json").write_text(
        json.dumps(rows,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    out["complete_768_world_diagnostic_canonical_sha256"]=hashlib.sha256(canonical(rows)).hexdigest()
    (args.output_dir/"result_v44.json").write_text(
        json.dumps(out,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",
        encoding="utf-8")
    print(json.dumps({
        "status":out["status"],
        "target_maturity_ambiguity_retro":out["counts"]["retrospective_maturity_ambiguous"],
        "target_maturity_ambiguity_asof":out["counts"]["asof_maturity_ambiguous"],
        "verdicts":out["predeclared_verdicts"]
    }))


if __name__=="__main__":
    main()
