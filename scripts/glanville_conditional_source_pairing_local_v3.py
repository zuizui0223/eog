#!/usr/bin/env python3
"""Locally audit source-label pairing under a yearwise constrained permutation null.

Requires publisher-authenticated DiLeo 2022 CSV and locally decrypted original
Schulz 2019 survey. Never use in GitHub Actions on individual rows. The prior
v2 EOG genetic-world logic is replayed before scoring any new statistic.
Only aggregate permutation statistics are written; source/target/family IDs,
coordinates and genetic assignment records are not exported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import runpy
import numpy as np

YEARS=(2007,2008,2009,2010,2011)
ORIGINAL_SHA="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
SURVEY_SHA="c70f43544f61e7273afebfa42ed1d488c3b945efe4d5c68e6557030087ee7fd9"


class AuditStop(Exception):
    pass


def _host(row):
    return row is not None and row[1] is not None and row[2] is not None and 0<=row[1]<=3 and 0<=row[2]<=3


def _stat(distance,gap,groups):
    return (float(np.mean([np.median(np.log1p(distance[i])) for i in groups])),
            float(np.mean([np.median(gap[i]) for i in groups])))


def _null_summary(observed, draws, reps):
    return {"observed":float(observed),"null_mean":float(np.mean(draws)),
            "observed_minus_null_mean":float(observed-np.mean(draws)),
            "null_quantiles_2p5_50_97p5":[float(np.quantile(draws,p)) for p in (.025,.5,.975)],
            "one_sided_conditional_permutation_tail_p":float((1+np.sum(draws<=observed+1e-12))/(reps+1)),
            "null_draws":reps}


def permutation(assigned:list,survey:dict,network:dict,*,reps:int=1999,seed:int=20261120,max_attempts:int=500)->dict:
    """Annual source-label frequency fixed; targets and target row-count fixed."""
    if reps<2 or seed<0 or max_attempts<1:raise AuditStop("STOP_NULL_PROTOCOL_BAD")
    n=len(assigned)
    targets=[row["target"] for row in assigned]
    by_target=defaultdict(list)
    for index,target in enumerate(targets):by_target[target].append(index)
    groups=[np.array(indices,dtype=int) for _,indices in sorted(by_target.items())]
    index_by_year={year:np.array([i for i,row in enumerate(assigned) if row["year"]-1==year],dtype=int)
                   for year in YEARS}
    dist0=np.array([row["distance"] for row in assigned],dtype=float)
    host0=np.array([row["host_gap"] for row in assigned],dtype=float)
    observed_d,observed_h=_stat(dist0,host0,groups)
    dmat={};hmat={};source_by_year={};target_by_year={}
    for year,indices in index_by_year.items():
        src=np.array([assigned[i]["source"] for i in indices],dtype=object)
        dst=np.array([assigned[i]["target"][1] for i in indices],dtype=object)
        src_xy=np.asarray([network[p] for p in src],dtype=float)
        dst_xy=np.asarray([network[p] for p in dst],dtype=float)
        d=np.linalg.norm(dst_xy[:,None,:]-src_xy[None,:,:],axis=2)
        s_host=np.asarray([[survey[(year,p)][1],survey[(year,p)][2]] for p in src],dtype=float)
        t_host=np.asarray([[survey[(year,p)][1],survey[(year,p)][2]] for p in dst],dtype=float)
        h=np.max(np.abs(t_host[:,None,:]-s_host[None,:,:]),axis=2)
        if (np.any(src==dst) or np.max(np.abs(np.diag(d)-dist0[indices]))>1e-9
            or np.max(np.abs(np.diag(h)-host0[indices]))>1e-9):
            raise AuditStop("STOP_NULL_DIAGONAL_AND_YEAR_SOURCE_REPLAY")
        dmat[year]=d;hmat[year]=h;source_by_year[year]=src;target_by_year[year]=dst
    groups_year={year:[g for g in groups if assigned[int(g[0])]["year"]-1==year] for year in YEARS}
    observed_year={str(year):{
        "target_patch_years":len(groups_year[year]),
        "assignment_rows":len(index_by_year[year]),
        "observed_target_equal_mean_median_log1p_distance":_stat(dist0,host0,groups_year[year])[0],
        "observed_target_equal_mean_median_host_gap":_stat(dist0,host0,groups_year[year])[1],
    } for year in YEARS}
    year_null={year:{"distance":[],"host":[]} for year in YEARS}
    rng=np.random.default_rng(seed)
    nd=np.empty(reps);nh=np.empty(reps);trials=0;rejects=0
    for trial in range(reps):
        d=np.empty(n);h=np.empty(n)
        for year,indices in index_by_year.items():
            src=source_by_year[year];dst=target_by_year[year]
            for _ in range(max_attempts):
                order=rng.permutation(len(indices));trials+=1
                if not np.any(src[order]==dst):break
                rejects+=1
            else:raise AuditStop("STOP_YEARWISE_NO_VALID_OFFPATCH_PERMUTATION")
            if Counter(src[order])!=Counter(src):
                raise AuditStop("STOP_SOURCE_LABEL_FREQUENCY_NOT_PRESERVED")
            d[indices]=dmat[year][np.arange(len(indices)),order]
            h[indices]=hmat[year][np.arange(len(indices)),order]
        nd[trial],nh[trial]=_stat(d,h,groups)
        for year,g in groups_year.items():
            yd,yh=_stat(d,h,g)
            year_null[year]["distance"].append(yd)
            year_null[year]["host"].append(yh)
    for year in YEARS:
        entry=observed_year[str(year)]
        entry["conditional_null_mean_log1p_distance"]=float(np.mean(year_null[year]["distance"]))
        entry["conditional_null_mean_host_gap"]=float(np.mean(year_null[year]["host"]))
        entry["observed_minus_null_mean_log1p_distance"]=entry["observed_target_equal_mean_median_log1p_distance"]-entry["conditional_null_mean_log1p_distance"]
        entry["observed_minus_null_mean_host_gap"]=entry["observed_target_equal_mean_median_host_gap"]-entry["conditional_null_mean_host_gap"]
    return {
        "source_label_recombination":"exact yearwise empirical frequencies among SELECTED genetically assigned reference origins, target row multiplicity fixed, no same-patch routes",
        "replicates":reps,"seed":seed,"target_patch_years":len(groups),"assignment_rows":n,
        "distance_target_equal_mean_within_target_median_log1p_km":_null_summary(observed_d,nd,reps),
        "host_target_equal_mean_within_target_median_gap":_null_summary(observed_h,nh,reps),
        "per_year_descriptive":observed_year,
        "total_permutation_year_proposals":trials,"rejected_self_pairs":rejects,
        "limitation":"Conditional randomization under genetically preselected, sample-ascertained GENECLASS2 assignments; not a biological source-selection p-value"
    }


def matched_reference(genetic:list,assigned:list,survey:dict,network:dict,*,minimum:int=3)->dict:
    origin_sites={year:set() for year in YEARS}
    whole_sites={year:set() for year in YEARS}
    for year,yt,source,target,family,moved,d in genetic:
        if year in origin_sites:origin_sites[year].add(source)
    for (year,site),row in survey.items():
        if year in whole_sites and row[0] is not None and row[0]>0 and _host(row) and site in network:
            whole_sites[year].add(site)
    def score(pool):
        cap={year:float(np.quantile([survey[(year,s)][0] for s in sites],.90))
             for year,sites in pool.items() if sites}
        by_target=defaultdict(list)
        counts=[]
        annual={year:{"rows":0,"targets":set()} for year in YEARS}
        for entry in assigned:
            year=entry["year"]-1
            target=entry["target"][1]
            window=max(.5,.25*entry["distance"])
            tar=survey[(year,target)]
            candidates=[]
            for s in pool[year]:
                if s==target:continue
                if abs(math.dist(network[s],network[target])-entry["distance"])<=window+1e-10:
                    src=survey[(year,s)]
                    h=max(abs(src[1]-tar[1]),abs(src[2]-tar[2]))
                    candidates.append((s,h,min(src[0],cap[year])))
            if entry["source"] not in {t[0] for t in candidates}:
                raise AuditStop("STOP_ASSIGNED_SOURCE_NOT_PRESENT_IN_DISTANCE_MATCHED_POOL")
            if len(candidates)<minimum:continue
            counts.append(len(candidates))
            avg=float(np.mean([t[1] for t in candidates]))
            weighted=float(np.average([t[1] for t in candidates],weights=[t[2] for t in candidates]))
            by_target[entry["target"]].append((entry["host_gap"]-avg,entry["host_gap"]-weighted))
            annual[year]["rows"]+=1;annual[year]["targets"].add(entry["target"])
        return {
            "yearly_candidate_source_counts":{str(y):len(pool[y]) for y in YEARS},
            "assignment_rows_eligible":len(counts),
            "target_patch_years_eligible":len(by_target),
            "median_number_of_distance_matched_candidate_sources":float(np.median(counts)) if counts else None,
            "target_equal_mean_assigned_minus_uniform_gap":float(np.mean([np.mean([p[0] for p in v]) for v in by_target.values()])) if by_target else None,
            "target_equal_mean_assigned_minus_recorded_population_weighted_gap":float(np.mean([np.mean([p[1] for p in v]) for v in by_target.values()])) if by_target else None,
            "by_year":{str(y):{"eligible_rows":annual[y]["rows"],"eligible_targets":len(annual[y]["targets"])} for y in YEARS},
            "strict_caliper":"max(0.5 km, 0.25 * original source→target distance)",
            "minimum_distinct_candidate_sources":minimum,
            "status":"DESCRIPTIVE_ONLY_NO_ENVIRONMENTAL_CAUSAL_INFERENCE_OR_PVALUE"
        }
    ref={year:origin_sites[year]&whole_sites[year] for year in YEARS}
    if any(not pool for pool in ref.values()):raise AuditStop("STOP_EMPTY_ASSIGNED_REFERENCE_SOURCE_UNIVERSE")
    return {"assigned_source_site_roster_from_all_799_family_assignments":score(ref),
            "all_prior_year_positive_EOG_source_roster":score(whole_sites),
            "caution":"Origin-label roster from 799 rows is not the complete GENECLASS2 reference sampling design. Recorded-positive counts are NOT sampling effort, migrant probabilities or independent population size."}


def run(original:Path,survey_file:Path,output:Path,protocol_file:Path):
    policy=json.loads(protocol_file.read_text(encoding="utf-8"))
    gate=policy["predeclared_primary_conditional_recombination_null"]
    secondary=policy["predeclared_secondary_distance_matched_reference"]
    if (policy["status"]!="frozen_before_opportunity_null_scoring_and_2019_source_reacquisition"
            or gate["monte_carlo_replicates"]!=1999 or gate["seed"]!=20261120
            or secondary["min_distinct_candidate_sites"]!=3):
        raise AuditStop("STOP_PREDECLARED_PROTOCOL_CHANGED")
    if hashlib.sha256(original.read_bytes()).hexdigest()!=ORIGINAL_SHA:
        raise AuditStop("STOP_ORIGINAL_DRYAD_SHA")
    snapshot=json.loads(survey_file.read_text(encoding="utf-8"))
    v2=runpy.run_path("scripts/glanville_genetic_host_world_local_audit_v2.py")
    genetic=v2["read_local_published_family"](original)
    survey,network=v2["qualified_survey"](snapshot)
    eligible,worlds=v2["make_worlds"](genetic,survey,network,strict=True)
    archived=json.loads(Path("validation/glanville_genetic_host_world_v2/frozen_aggregate_summary_v2.json").read_text())
    frozen={(int(row["delta"]),int(row["r_km"])):row for row in archived["worlds"]}
    if len(frozen)!=8 or len(eligible)!=163 or len({x["target"] for x in eligible})!=100 or len({x["family"] for x in eligible})!=157:
        raise AuditStop("STOP_PARENT_GENETIC_GRAIN")
    for item in worlds:
        old=frozen[(item["host_gap_delta"],int(item["radius_km"]))]
        if (item["combined"]["EOG_any_source_within_r_distinct_destinations"]!=old["EOG_any_source_target_years"]
            or item["combined"]["at_least_one_assigned_source_within_r_distinct_destinations"]!=old["assigned_source_any_target_years"]):
            raise AuditStop("STOP_PARENT_EIGHT_WORLDS")
    if {str(delta):sum(x["host_gap"]==delta for x in eligible) for delta in range(4)}!={"0":29,"1":67,"2":52,"3":15}:
        raise AuditStop("STOP_ORIGINAL_HOST_GAP")
    paired=permutation(eligible,survey,network,reps=gate["monte_carlo_replicates"],
                       seed=gate["seed"],max_attempts=gate["max_rejection_attempts_per_year_rep"])
    reference=matched_reference(genetic,eligible,survey,network,
                                minimum=secondary["min_distinct_candidate_sites"])
    result={
        "schema_version":3,"status":"EXPLORATORY_CONDITIONAL_GENETIC_SOURCE_PAIRING_ANALYZED",
        "sources":{"genetic_SHA256":ORIGINAL_SHA,"Schulz2019_archive_SHA256":SURVEY_SHA,
                   "parent_genetic_world_fingerprint":policy["sources"]["parent_genetic_host_world"]},
        "original_163_assignments_100_targets_157_families_and_8_worlds_reproduced":True,
        "primary_conditional_permutation":paired,
        "secondary_distance_matched_host_gap":reference,
        "EOG_WF_fresh_endpoints_added":0,
        "site_family_or_genetic_row_ids_exported":0,
        "claim_boundary":"Post-exposure GENECLASS2 model-assignment pairing; conditional label exchangeability is not natural source availability or direct movement; genetic sampling and distance-sensitive assignment, spatial environmental autocorrelation and patch-year detection remain confounding factors."
    }
    raw=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    result["fingerprint_without_self_hash"]=hashlib.sha256(raw.encode()).hexdigest()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"status":result["status"],"target_years":paired["target_patch_years"],
                      "replicates":paired["replicates"],"fingerprint":result["fingerprint_without_self_hash"]},
                     sort_keys=True))
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--genetic-csv",type=Path,required=True)
    parser.add_argument("--decrypted-survey",type=Path,required=True)
    parser.add_argument("--protocol",type=Path,default=Path("validation/glanville_conditional_pairing_null_v3/protocol_v3.json"))
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    run(args.genetic_csv,args.decrypted_survey,args.output,args.protocol)


if __name__=="__main__":
    main()
