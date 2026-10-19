#!/usr/bin/env python3
"""v41: noisy source-of-first-arrival information about ecological-state TARGETS.

The latent data are exactly the three activation histories and 768 synthetic
graphs of v23/v26. Fixed q=.60, e=.10 noisy source-tag likelihood and site
policies are reused unchanged from v39. No real ancestry or field data.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import product
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.run_eog_imperfect_provenance_sampling_v39 import (
    AUTOCORR_LEVELS, BARRIER_LEVELS, NEIGHBOURHOODS, REPLICATES,
    DESIGNS, RULE, _generate_base, _outlet_corner, _truth_source,
    _candidate_sources, _source_sets, _graphs, _distances,
    _arrival_structure, ACTIVATION_HISTORIES, prepare_design,
    bayes_information as v39_exact_history_bayes,
    POLICIES, K,
)
from benchmarks.run_eog_original_idea_history_to_state_process_family_v26 import (
    PROCESS_IDS, _age_map, _process_map,
)

PROTOCOL=ROOT/"validation/eog_original_idea_provenance_ecological_state_v41/protocol_v41.json"
V23=ROOT/"validation/eog_original_idea_provenance_observability_v23/result_summary_v23.json"
V25=ROOT/"validation/eog_original_idea_age_dependent_present_state_v25/result_summary_v25.json"
V26=ROOT/"validation/eog_original_idea_history_to_state_process_family_v26/result_summary_v26.json"
V39=ROOT/"validation/eog_original_idea_imperfect_provenance_v39/result_frozen_v39.json"
V40=ROOT/"validation/eog_original_idea_provenance_placement_multiseed_v40/result_frozen_v40.json"
RESULT_SCHEMA="eog.original_idea.noisy_provenance_ecological_state_value.result.v41"
TARGETS=("exact_activation_history",)+tuple(PROCESS_IDS)
Q,E=0.6,0.1
EPS=1e-9
FINGERPRINTS={
"v23":"ab37b83de94fce5e6d35918b9f5730a63364cebf0bb00ec662eececc5ae85244",
"v25":"998c24e22e355f703c2a787780ced11abd01280c0ca5deb3b17e8848af3f7ad0",
"v26":"90096f149d2a3c71b4a00283cef2b1470a7501bbffc6ce39c79fac33540ce27e",
"v39":"eefbd3c2ef69e532d6efc5fef66fd7ec97def75e6dd6b74d533d042e78aaa865",
"v40":"e366c4945e2110bd6359c3db1ae86e4e01bb6df8741fc4370af6ae54b5792f91"
}
BOUNDARY={
"post_v39_v40_exposure_synthetic_result_not_independent_novel_ecological_replication":True,
"lag2_and_other_age_state_processes_are_preset_abstract_not_species_calibrated":True,
"ideal_earliest_source_tag_is_not_natal_genetic_assignment":True,
"source_tag_error_coverage_rates_not_estimated_from_2021_Dryad":True,
"no_original_2021_genotype_bird_survey_data_read":True,
"no_2026_helgeland_capt_obs_endpoint_rescored":True,
"no_actual_colonization_origin_or_survival_probability_inferred":True,
"no_fourth_EOG_WF_predictive_endpoint_or_submission_change":True
}
HYPOTHESES=(
"V1_noisy_provenance_adds_some_maturity_information",
"V2_history_information_without_maturity_information_exists",
"V3_transient_state_information_exceeds_lag2_maturity",
"V4_perfect_provenance_does_not_resolve_all_present_maturity",
"V5_source_tag_information_must_respect_target_compression",
)
SUBSETS=("all","occupancy_aliased","equal_budget_aliased")


def verify_sources(p:dict,source:dict)->None:
    if (p.get("schema")!="eog.original_idea.noisy_provenance_ecological_state_value.protocol.v41"
        or p.get("status")!="FROZEN_BEFORE_TARGET_SPECIFIC_NOISY_PROVENANCE_BENCHMARK_RESULTS__POST_V39_V40_EXPOSURE"):
        raise ValueError("Missing frozen v41 pre-result contract")
    prev=p.get("parent_sources",{})
    if not(
        prev.get("main_commit")=="3865d1fa98cb2031d567e34a290162d75f6536e0"
        and prev.get("v23_fingerprint")==FINGERPRINTS["v23"]
        and prev.get("v25_fingerprint")==FINGERPRINTS["v25"]
        and prev.get("v26_fingerprint")==FINGERPRINTS["v26"]
        and prev.get("v39_full_sha256")==FINGERPRINTS["v39"]
        and prev.get("v40_full_sha256")==FINGERPRINTS["v40"]):
        raise ValueError("v23-v40 fixed experiment provenance changed")
    if not(
        source["v23"]["result_fingerprint"]==FINGERPRINTS["v23"]
        and source["v25"]["result_fingerprint"]==FINGERPRINTS["v25"]
        and source["v26"]["result_fingerprint"]==FINGERPRINTS["v26"]
        and source["v39"]["authority"]["canonical_full_result_sha256"]==FINGERPRINTS["v39"]
        and source["v40"]["authority"]["full_canonical_json_sha256"]==FINGERPRINTS["v40"]
    ):
        raise ValueError("Actual frozen v23-v40 results changed")
    d=p.get("fixed_design",{})
    if not (
        d.get("ecological_world_rows")==384
        and d.get("source_geometries")==list(DESIGNS)
        and d.get("total_source_history_designs")==768
        and d.get("three_activation_histories")==len(ACTIVATION_HISTORIES)==3
        and d.get("full_non_source_occupancy_times")==[4,5,6,8]
        and d.get("parent_occupancy_exact_history_identified")==579
        and d.get("parent_occupancy_alias_designs")==189
        and d.get("perfect_combined_full_history_identified")==687
        and d.get("perfect_combined_exact_history_aliased")==81
        and d.get("perfect_combined_aliases_with_different_lag2_mature_target")==12
        and d.get("perfect_combined_aliases_with_different_transient_age1_2_target")==45
        and d.get("parent_lag2_age_sensitive_worlds")==726
        and d.get("parent_transient_age_sensitive_worlds")==726
        and d.get("parent_saturating_age_sensitive_worlds")==726
    ): raise ValueError("Parent ecology and maturity target denominators changed")
    a=p.get("source_tag_assay",{})
    if not (
        a.get("site_budget_max")==K==3
        and a.get("policies")==list(POLICIES)
        and a.get("coverage_q")==Q
        and a.get("miscall_e")==E
        and a.get("assay_likelihood_is_known_in_simulation") is True
        and a.get("no_real_SNP_or_sampling_coverage_calibration") is True
        and a.get("no_site_cost_model") is True
    ): raise ValueError("Frozen noisy source-tag observation model changed")
    target=p.get("present_state_targets",{})
    if not (
        target.get("actual_biological_maturity_survival_disease_or_fitness_measured") is False
        and set(target)==set(TARGETS)|{"common_present_Tstar","actual_biological_maturity_survival_disease_or_fitness_measured"}
        and target["common_present_Tstar"].startswith("maximum first-arrival")
    ): raise ValueError("Predicted ecological targets or frozen horizon changed")
    if tuple(h["id"] for h in p.get("falsifiable_predictions",()))!=HYPOTHESES:
        raise ValueError("Hypothesis protocol changed")
    if p.get("scientific_boundaries")!=BOUNDARY:
        raise ValueError("Ecological interpretation boundary changed")


def _entropy(weights:dict)->float:
    total=sum(weights.values())
    return -sum(w/total*math.log2(w/total) for w in weights.values() if w>0) if total>0 else 0.0


def target_bayes_information(
    occupancy:dict,
    target:dict,
    all_tags:dict,
    selected:tuple[str,...],
    coverage:float=Q,
    error:float=E
)->dict:
    """Exact conditional I(T;noisy source reports|O) and Bayes target accuracy.

    T is deterministic under a latent history H; noisy measurement Y depends
    on H, conditionally independent across selected assay nodes. Exact prior
    over the original three H values is uniform (1/3 each).
    """
    hist=tuple(sorted(occupancy))
    if len(hist)!=3 or set(target)!=set(hist):
        raise ValueError("All 3 latent activation histories require a target")
    if not (0<=coverage<=1 and 0<=error<=0.25):
        raise ValueError("Synthetic source-tag observation error outside contract")
    if len(selected)>K or any(s not in all_tags for s in selected):
        raise ValueError("Selected source tag is not in fixed assay library")
    groups=defaultdict(list)
    for h in hist: groups[occupancy[h]].append(h)
    prior_entropy=0.0
    base_correct=0.0
    for members in groups.values():
        count=Counter(target[h] for h in members)
        prior_entropy+=len(members)/3*_entropy(count)
        base_correct+=max(count.values())/3

    if not selected or coverage==0:
        return {
            "information_bits":0.0,"bayes_correct_target_gain":0.0,
            "base_conditional_entropy_bits":prior_entropy,
            "base_bayes_correct_target_probability":base_correct
        }

    report_domains=[]
    likelihood={}
    for site in selected:
        truth=all_tags[site]
        if set(truth)!=set(hist):
            raise ValueError("Incomplete synthetic earliest-source observations")
        unique=tuple(sorted(set(truth.values())))
        sentinel=("__synthetic_unseen__",)
        if sentinel in unique:
            raise ValueError("Noise report category collided")
        categories=unique+(sentinel,)
        report_domains.append((None,)+categories)
        for h in hist:
            dist={None:1-coverage}
            for cat in categories:
                dist[cat]=coverage*(
                    1-error if cat==truth[h]
                    else error/(len(categories)-1)
                )
            if abs(sum(dist.values())-1)>1e-12:
                raise ValueError("Unnormalized synthetic misassignment likelihood")
            likelihood[(site,h)]=dist

    expected_entropy=0.0
    after_correct=0.0
    for reports in product(*report_domains):
        for members in groups.values():
            by_target=defaultdict(float)
            for h in members:
                prob=1/3
                for site,rep in zip(selected,reports,strict=True):
                    prob*=likelihood[(site,h)][rep]
                by_target[target[h]]+=prob
            outcome_weight=sum(by_target.values())
            if outcome_weight<=0: continue
            expected_entropy+=outcome_weight*_entropy(by_target)
            after_correct+=max(by_target.values())
    info=prior_entropy-expected_entropy
    gain=after_correct-base_correct
    if info < -1e-8 or gain < -1e-8:
        raise ValueError("Correct noisy Bayes update unexpectedly increased entropy or error")
    return {
        "information_bits":0.0 if abs(info)<1e-11 else max(info,0.0),
        "bayes_correct_target_gain":0.0 if abs(gain)<1e-11 else max(gain,0.0),
        "base_conditional_entropy_bits":prior_entropy,
        "base_bayes_correct_target_probability":base_correct
    }


def _synthetic_present_targets(graph,sources):
    """Reuse precisely v26's predeclared common T* and age-to-state mappings."""
    distances=_distances(graph,sources)
    source_nodes=frozenset(sources)
    rows={}
    for h,activation in ACTIVATION_HISTORIES.items():
        eq,first,_=_arrival_structure(distances,sources,activation)
        rows[h]={"eq":eq,"first":first}
    unions={tuple(sorted(z["eq"])) for z in rows.values()}
    if len(unions)!=1:
        raise ValueError("Equilibrium nodes changed across histories")
    nodes=tuple(n for n in next(iter(unions)) if n not in source_nodes)
    common_T=(
        max(int(row["first"][n]) for row in rows.values() for n in nodes)
        if nodes else None
    )
    state={t:{} for t in TARGETS}
    for h,row in rows.items():
        state["exact_activation_history"][h]=h
        ages=_age_map(nodes,row["first"],common_T)
        for proc in PROCESS_IDS:
            state[proc][h]=_process_map(proc,ages)
    return state


def _perfect_alias_status(occupancy:dict,source_tags:dict,targets:dict)->dict:
    """Complete ideal source-tag readout is an upper IDENTIFIABILITY bound."""
    hist=tuple(sorted(occupancy))
    signatures={
        h:(occupancy[h],tuple(source_tags[node][h] for node in sorted(source_tags)))
        for h in hist
    }
    cohorts=defaultdict(list)
    for h,value in signatures.items():cohorts[value].append(h)
    unresolved=len(cohorts)<len(hist)
    differences={}
    for target in TARGETS:
        differences[target]=any(
            len(set(targets[target][h] for h in group))>1
            for group in cohorts.values() if len(group)>1
        )
    return {
        "history_unresolved":unresolved,
        "source_and_occupancy_equivalent_but_target_differs":differences,
    }


def run()->dict:
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source={
        "v23":json.loads(V23.read_text(encoding="utf-8")),
        "v25":json.loads(V25.read_text(encoding="utf-8")),
        "v26":json.loads(V26.read_text(encoding="utf-8")),
        "v39":json.loads(V39.read_text(encoding="utf-8")),
        "v40":json.loads(V40.read_text(encoding="utf-8"))
    }
    verify_sources(p,source)
    stats=defaultdict(list)
    geom=defaultdict(list)
    design_n=0
    occ_ident=0
    occ_aliased=0
    equal_budget_aliases=0
    full_ideal_history_ident=0
    age_memory=Counter()
    complete_alias_target_diff=Counter()
    complete_alias_n=0
    dpi_violations=0
    exact_history_reconciliation_violations=0
    zero_control_violations=0
    history_positive_maturity_zero=0
    history_positive_maturity_positive=0
    maturity_positive=0

    for autocorr in AUTOCORR_LEVELS:
      for neighbourhood in NEIGHBOURHOODS:
        for replicate in range(REPLICATES):
          base=_generate_base(replicate,autocorr,neighbourhood)
          outlet=_outlet_corner(replicate,autocorr,neighbourhood)
          anchor=_truth_source(base,outlet)
          candidates,_=_candidate_sources(base,outlet,anchor)
          sourcesets=_source_sets(candidates,anchor)
          if not sourcesets: raise ValueError("Expected v23 landscape eligible")
          for barrier in BARRIER_LEVELS:
            _,graph=_graphs(base,barrier,RULE,outlet)
            for design in DESIGNS:
              sources=sourcesets[design][3]
              scenario_key=f"{replicate}|{autocorr}|{neighbourhood}|{barrier}|{design}"
              x=prepare_design(graph,sources,scenario_key)
              targets=_synthetic_present_targets(graph,sources)
              design_n+=1
              aliased=not x["occupancy_exact_history_identifiable"]
              occ_aliased+=int(aliased)
              occ_ident+=int(not aliased)
              fair=aliased and x["equal_budget_eligible"]
              equal_budget_aliases+=int(fair)
              complete=_perfect_alias_status(x["occupancy"],x["provenance_tags"],targets)
              full_ideal_history_ident+=int(not complete["history_unresolved"])
              complete_alias_n+=int(complete["history_unresolved"])
              for t in TARGETS:
                complete_alias_target_diff[t]+=int(complete["source_and_occupancy_equivalent_but_target_differs"][t])
                if len(set(targets[t].values()))>1:
                    age_memory[t]+=1
              for policy in POLICIES:
                sites=tuple(x["selected"][policy])
                histor=target_bayes_information(
                    x["occupancy"],targets["exact_activation_history"],
                    x["provenance_tags"],sites
                )
                prev=v39_exact_history_bayes(
                    x["occupancy"],x["provenance_tags"],sites,Q,E
                )
                if abs(histor["information_bits"]-prev["additional_information_bits"])>1e-8 or \
                   abs(histor["bayes_correct_target_gain"]-prev["bayes_accuracy_gain"])>1e-8:
                    exact_history_reconciliation_violations+=1
                if policy=="unique_origin_negative_control" and histor["information_bits"]>EPS:
                    zero_control_violations+=1
                for t in TARGETS:
                  z=histor if t=="exact_activation_history" else target_bayes_information(
                      x["occupancy"],targets[t],x["provenance_tags"],sites
                  )
                  if z["information_bits"]>histor["information_bits"]+EPS:
                    dpi_violations+=1
                  if (policy=="unique_origin_negative_control" or t=="history_blind_occupancy") and (
                      z["information_bits"]>EPS or z["bayes_correct_target_gain"]>EPS):
                    zero_control_violations+=1
                  for subset in (("all",)+(("occupancy_aliased",) if aliased else ())+
                                 (("equal_budget_aliased",) if fair else ())+
                                 (("ideal_source_alias",) if complete["history_unresolved"] else ())):
                    stats[(policy,t,subset)].append(z)
                  if aliased:
                    geom[(design,policy,t)].append(z)
                  if t=="persistent_threshold_lag2" and aliased and policy=="confluence_targeted":
                    if z["information_bits"]>EPS: maturity_positive+=1
                    if histor["information_bits"]>EPS and z["information_bits"]<=EPS:
                      history_positive_maturity_zero+=1
                    if histor["information_bits"]>EPS and z["information_bits"]>EPS:
                      history_positive_maturity_positive+=1

    expected={
        "design_rows":768,"occupancy_identified":579,"occupancy_alias":189,
        "equal_budget_alias":88,"perfect_combined_identified":687,
        "perfect_combined_alias":81
    }
    actual={
        "design_rows":design_n,"occupancy_identified":occ_ident,
        "occupancy_alias":occ_aliased,"equal_budget_alias":equal_budget_aliases,
        "perfect_combined_identified":full_ideal_history_ident,
        "perfect_combined_alias":complete_alias_n
    }
    if actual!=expected:raise ValueError(f"Parent known-truth populations drifted: {actual}")
    if (
        age_memory["history_blind_occupancy"]!=0 or
        any(age_memory[t]!=726 for t in PROCESS_IDS if t!="history_blind_occupancy") or
        complete_alias_target_diff["persistent_threshold_lag2"]!=12 or
        complete_alias_target_diff["transient_window_age1_2"]!=45 or
        complete_alias_target_diff["saturating_age_class_cap3"]!=45 or
        complete_alias_target_diff["exact_activation_history"]!=81
    ):raise ValueError(f"v25/v26 present-state memory / alias target changed {dict(complete_alias_target_diff)}")
    if exact_history_reconciliation_violations or dpi_violations or zero_control_violations:
        raise ValueError("Independent Bayes likelihood, DPI or structural negative controls failed")

    summary=[]
    for policy in POLICIES:
      for t in TARGETS:
        for subset in ("all","occupancy_aliased","equal_budget_aliased","ideal_source_alias"):
          vals=stats[(policy,t,subset)]
          def avg(field):
            return None if not vals else sum(x[field] for x in vals)/len(vals)
          summary.append({
              "policy":policy,"target":t,"subset":subset,"n_designs":len(vals),
              "mean_target_information_bits":avg("information_bits"),
              "mean_target_bayes_accuracy_gain":avg("bayes_correct_target_gain"),
              "mean_target_baseline_conditional_entropy_bits":avg("base_conditional_entropy_bits"),
              "mean_target_baseline_bayes_correct_probability":avg("base_bayes_correct_target_probability"),
              "target_gain_positive_count":sum(x["information_bits"]>EPS for x in vals),
          })
    def avg(p,t,subset):
      result=next(v for v in summary if v["policy"]==p and v["target"]==t and v["subset"]==subset)
      return result["mean_target_information_bits"]
    confluence="confluence_targeted"
    geom_rows=[]
    for design in DESIGNS:
      for t in TARGETS:
        values=geom[(design,confluence,t)]
        geom_rows.append({
            "source_geometry":design,"target":t,"policy":confluence,
            "n_occupancy_aliased_designs":len(values),
            "mean_target_information_bits":sum(v["information_bits"] for v in values)/len(values) if values else None,
            "target_information_positive_count":sum(v["information_bits"]>EPS for v in values)
        })
    verdicts={
        HYPOTHESES[0]:"SUPPORTED" if maturity_positive>0 else "REFUTED",
        HYPOTHESES[1]:"SUPPORTED" if history_positive_maturity_zero>0 else "REFUTED",
        HYPOTHESES[2]:"SUPPORTED" if avg(confluence,"transient_window_age1_2","occupancy_aliased")>
                                     avg(confluence,"persistent_threshold_lag2","occupancy_aliased")+EPS else "REFUTED",
        HYPOTHESES[3]:"SUPPORTED" if complete_alias_target_diff["persistent_threshold_lag2"]==12 else "REFUTED",
        HYPOTHESES[4]:"SUPPORTED" if dpi_violations==0 else "REFUTED",
    }
    return {
        "schema":RESULT_SCHEMA,
        "status":"EXACT_TARGET_SPECIFIC_NOISY_SOURCE_READOUT_KNOWN_TRUTH__NO_GENETIC_DATA",
        "protocol":str(PROTOCOL.relative_to(ROOT)),
        "source_parent_fingerprints":FINGERPRINTS,
        "parent_population_counts":actual,
        "process_target_memory_row_counts":dict(age_memory),
        "perfect_full_source_alias_target_disagreement_counts":dict(complete_alias_target_diff),
        "primary_assay":{"coverage_q":Q,"miscall_e":E,"site_budget":K,"history_prior":"uniform across 3 activation schedules"},
        "summary_by_policy_target_subset":summary,
        "by_source_geometry_occupancy_aliased":geom_rows,
        "contrast_counts_on_189_occupancy_aliases":{
            "confluence_source_tags_improve_lag2_maturity_in_designs":maturity_positive,
            "confluence_source_tags_improve_history_but_not_lag2_maturity_in_designs":history_positive_maturity_zero,
            "confluence_source_tags_improve_both_history_and_lag2_maturity_in_designs":history_positive_maturity_positive,
        },
        "control_violation_counts":{
            "v39_exact_history_independent_bayes_mismatches":exact_history_reconciliation_violations,
            "target_information_data_processing_violations":dpi_violations,
            "history_blind_or_unique_origin_zero_information_violations":zero_control_violations
        },
        "predeclared_verdicts":verdicts,
        "scientific_boundaries":BOUNDARY
    }


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    r=run()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Do not overwrite frozen v41 result")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(r,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({
        "status":r["status"],"parent":r["parent_population_counts"],
        "verdicts":r["predeclared_verdicts"],"no_real_genetic_or_recruitment_data":True
    },sort_keys=True))


if __name__=="__main__":
    main()
