"""Counterfactual single-negative witness planning for 4 weakly one-sided bounds.

WARNING: this is a hypothetical INFORMATION DESIGN, not field observations.
Recorded non-detection remains UNKNOWN. A mathematically certified biological
absence requires independent evidence that these source data do not provide.
The static binary site state and perfect positive-specificity assumptions
are unverified over the source's up-to-91-day field period.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

from benchmarks import wetland_positive_only_partial_id_v1 as pid
from benchmarks import wetland_method_channel_lattice_v1 as base

CATEGORIES=("intervention","control","artificial")
EXPECTED_GROUP_SIZES={"intervention":13,"control":6,"artificial":8}


def bounds_with_certified_negatives(k_a,n_a,k_b,n_b,negative_a=0,negative_b=0):
    """Exact conditional bounds with source positives and HYPOTHETICAL true negatives.

    Exact source positive and independently certified-negative site statuses
    must be disjoint. All other status assignments remain unrestricted.
    """
    inputs=(k_a,n_a,k_b,n_b,negative_a,negative_b)
    if any(type(x) is not int for x in inputs):
        raise ValueError("source positive/negative counts must be integers")
    if n_a<=0 or n_b<=0 or not 0<=k_a<=n_a or not 0<=k_b<=n_b:
        raise ValueError("invalid site positivity/denominator")
    if not 0<=negative_a<=n_a-k_a or not 0<=negative_b<=n_b-k_b:
        raise ValueError("negative certificates contradict confirmed source positives")
    den=n_a*n_b
    low=k_a*n_b-(n_b-negative_b)*n_a
    high=(n_a-negative_a)*n_b-k_b*n_a
    if low>high or low>0 and high<0:
        raise ValueError("contradictory conditional binary completion bounds")
    strict=("strict_positive" if low>0 else
            "strict_negative" if high<0 else "strict_direction_not_identified")
    return {
        "lower_numerator":low,
        "upper_numerator":high,
        "denominator":den,
        "lower_percentage_points":100*low/den,
        "upper_percentage_points":100*high/den,
        "strict_sign_status":strict,
        "zero_still_feasible":low<=0<=high,
        "certified_true_negative_A":negative_a,
        "certified_true_negative_B":negative_b,
    }


def minimum_cover(candidates_by_target):
    """Enumerate all minimum distinct sites covering each weak-bound target.

    Coverage is conditional on a follow-up independently certifying each
    required species truly absent at the selected target site; it does not
    assume such an absence will actually be obtained.
    """
    if not candidates_by_target or any(not v for v in candidates_by_target.values()):
        raise ValueError("every target must have >=1 feasible source-unconfirmed site")
    goals=set(candidates_by_target)
    site_cover=defaultdict(set)
    certificate_cover=defaultdict(set)
    for target,items in candidates_by_target.items():
        for site,species in items:
            site_cover[site].add(target)
            certificate_cover[(site,species)].add(target)
    sites=sorted(site_cover)
    certs=sorted(certificate_cover)
    joint_site_solutions=[]
    for count in range(1,len(sites)+1):
        matches=[list(part) for part in itertools.combinations(sites,count)
                 if set.union(*(site_cover[site] for site in part))==goals]
        if matches:
            joint_site_solutions=matches
            break
    certificate_solutions=[]
    for count in range(1,len(certs)+1):
        matches=[list(part) for part in itertools.combinations(certs,count)
                 if set.union(*(certificate_cover[cert] for cert in part))==goals]
        if matches:
            certificate_solutions=matches
            break
    if not joint_site_solutions or not certificate_solutions:
        raise ValueError("candidate site/certificate cover impossible")
    return {
        "distinct_candidate_sites":len(sites),
        "candidate_site_species_records":len(certs),
        "target_count":len(goals),
        "minimum_distinct_site_visit_count_in_counterfactual_ideal":len(joint_site_solutions[0]),
        "all_minimum_site_visit_sets":joint_site_solutions,
        "minimum_independent_true_negative_site_species_certificates":len(certificate_solutions[0]),
        "all_minimum_certificate_sets":[
            [{"site":site,"species":sp}for site,sp in part]
            for part in certificate_solutions
        ],
        "single_visit_may_support_multi_species_certificates_only_if_independently_validated":True,
    }


def run(surveys_path, sites_path, out_dir):
    """Source-pinned Q1 original-sites witness plan, not an inference model."""
    sites,positive_by_method,taxa=pid.original_q1_source(surveys_path,sites_path)
    source_full=set(positive_by_method)
    if len(sites)!=27 or len(source_full)!=144 or set(sites.values())!=set(CATEGORIES):
        raise ValueError("native Q1 source identity failed")
    if {g:sum(v==g for v in sites.values()) for g in CATEGORIES}!=EXPECTED_GROUP_SIZES:
        raise ValueError("original wetland category denominators changed")
    survey_rows,_=base.read_csv(surveys_path)
    q1_rows=[r for r in survey_rows if r["site"] in sites]
    dates_by_site={site:sorted({r["date"] for r in q1_rows if r["site"]==site})
                   for site in sites}
    if len(q1_rows)!=351 or sum(map(len,dates_by_site.values()))!=117:
        raise ValueError("original source survey date structure changed")

    targets=[]
    source_unconfirmed=[]
    candidates_by_target={}
    for a,b in base.CONTRASTS:
        for sp in taxa:
            n_a=EXPECTED_GROUP_SIZES[a];n_b=EXPECTED_GROUP_SIZES[b]
            k_a=sum((site,sp) in source_full for site,c in sites.items() if c==a)
            k_b=sum((site,sp) in source_full for site,c in sites.items() if c==b)
            bound=pid.bound_counts(k_a,n_a,k_b,n_b)
            if bound["conditional_identification_status"] not in (
                "nonnegative_only","nonpositive_only"
            ):continue
            role=("B" if bound["conditional_identification_status"]=="nonnegative_only" else "A")
            negative_category=(b if role=="B" else a)
            expected_strict=("strict_positive" if role=="B" else "strict_negative")
            candidate_ids=sorted(site for site,c in sites.items()
                                 if c==negative_category and (site,sp) not in source_full)
            if not candidate_ids:
                raise ValueError("one-sided but no unconfirmed source site for strict witness")
            key=f"{a}_minus_{b}|{sp}"
            candidates_by_target[key]={(site,sp) for site in candidate_ids}
            target={
                "target_id":key,
                "species":sp,
                "category_a":a,"category_b":b,
                "site_count_a":n_a,"site_count_b":n_b,
                "source_recorded_positive_a":k_a,"source_recorded_positive_b":k_b,
                "current_weak_sign_status":bound["conditional_identification_status"],
                "conditional_original_lower_pp":bound["conditional_latent_lower_percentage_points"],
                "conditional_original_upper_pp":bound["conditional_latent_upper_percentage_points"],
                "category_where_an_independently_certified_absence_would_help":negative_category,
                "expected_strict_sign_if_one_certified_absence":expected_strict,
                "number_source_unconfirmed_candidate_sites":len(candidate_ids),
                "source_unconfirmed_candidate_sites":candidate_ids,
                "new_field_true_negative_certificates_currently_observed":0
            }
            for site in candidate_ids:
                hypothetical=bounds_with_certified_negatives(
                    k_a,n_a,k_b,n_b,
                    negative_a=int(role=="A"), negative_b=int(role=="B")
                )
                if hypothetical["strict_sign_status"]!=expected_strict:
                    raise ValueError("single hypothetical negative did not identify a strict sign")
                source_unconfirmed.append({
                    "target_id":key,"site":site,"category":negative_category,
                    "species":sp,
                    "original_native_site_date_groups":len(dates_by_site[site]),
                    "original_native_source_rows":sum(r["site"]==site for r in q1_rows),
                    "one_true_absence_status_is_hypothetical_not_observed":True,
                    "one_negative_lower_pp":hypothetical["lower_percentage_points"],
                    "one_negative_upper_pp":hypothetical["upper_percentage_points"],
                    "one_negative_strict_status":hypothetical["strict_sign_status"]
                })
            targets.append(target)

    if len(targets)!=4 or any(t["new_field_true_negative_certificates_currently_observed"]
                               for t in targets):
        raise ValueError("full-source weak one-sided target roster changed")
    plan=minimum_cover(candidates_by_target)
    if plan["target_count"]!=4:
        raise ValueError("not all one-sided source contrasts covered")
    if plan["minimum_distinct_site_visit_count_in_counterfactual_ideal"]>4:
        raise ValueError("counterfactual source design unexpectedly changed")
    site_coverage={}
    for c in source_unconfirmed:
        site_coverage.setdefault(c["site"],{
            "site":c["site"],"category":c["category"],
            "recorded_native_site_dates":c["original_native_site_date_groups"],
            "target_species":set(),"coverable_comparisons":set(),
        })
        site_coverage[c["site"]]["target_species"].add(c["species"])
        site_coverage[c["site"]]["coverable_comparisons"].add(c["target_id"])
    site_rows=[{
        "site":site, "category":d["category"],
        "recorded_native_site_dates":d["recorded_native_site_dates"],
        "number_target_species":len(d["target_species"]),
        "species_without_source_positives":";".join(sorted(d["target_species"])),
        "number_weak_category_comparisons_a_true_absence_could_resolve":len(d["coverable_comparisons"]),
        "weak_category_comparisons":";".join(sorted(d["coverable_comparisons"])),
        "true_negative_certificates_in_original_source":0
    }for site,d in sorted(site_coverage.items())]
    result={
        "schema":"eog.wetland_negative_witness_plan_v1.result",
        "status":"COUNTERFACTUAL_CERTIFIED_NEGATIVE_WITNESS_TARGETS_NOT_ACTUAL_FIELD_ABSENCES",
        "scope":"POST_EXPOSURE_LOGICAL_STATIC_SITE_STATUS_OBSERVATION_DESIGN",
        "source_sha256":{"surveys":base.SURVEY_SHA,"sites":base.SITE_SHA},
        "native_sites":len(sites),
        "source_positive_site_species":len(source_full),
        "original_full_source_weak_one_sided_contrast_targets":len(targets),
        "all_target_conditional_strict_directions_possible_with_one_valid_negative":True,
        "minimum_joint_counterfactual_design":plan,
        "target_records":targets,
        "candidate_site_records":site_rows,
        "source_unconfirmed_site_species_certificate_candidates":len(source_unconfirmed),
        "source_verified_biological_absence_certificates":0,
        "new_biological_data_collected":False,
        "no_causal_restoration_effect_estimated":True,
        "no_occupancy_likelihood_fitted":True,
        "hard_stop":[
            "A true-negative certificate is counterfactual, not an observed field result; even repeated nondetection cannot be treated as certified absence without detection and temporal assumptions.",
            "The two-site minimal cover is a best-case combinatorial plan conditional on obtaining independently validated negative results for TWO different amphibians per site. It is not a guarantee of successful field sampling or effect identification.",
            "Static site status and perfect specificity of archived positive counts are not independently confirmed over surveys spanning up to 91 days.",
            "Sites are original nonrandomized intervention/control/artificial observations; a strict prevalence sign would not imply causal restoration benefit.",
            "No actual EOG transition worlds, A/B/M mechanisms, occupancy coefficients, new EOG-WF scored endpoint or PR merge."
        ],
        "outputs":{
            "weak_one_sided_target_list":targets,
            "source_unconfirmed_candidate_site_species":source_unconfirmed,
            "site_visit_joint_target_coverage":site_rows
        }
    }
    return result


def produce(surveys_path,sites_path,outdir):
    result=run(surveys_path,sites_path,outdir)
    output=result.pop("outputs")
    path=Path(outdir);path.mkdir(parents=True,exist_ok=True)
    result["csv_artifacts"]={}
    for label,rows in output.items():
        out=path/(label+".csv")
        with out.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
        result["csv_artifacts"][label]={
            "filename":out.name,"rows":len(rows),
            "sha256":hashlib.sha256(out.read_bytes()).hexdigest()
        }
    result["fingerprint"]=hashlib.sha256(json.dumps(
        result,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--surveys",type=Path,required=True)
    ap.add_argument("--sites",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    r=produce(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("WETLAND_NEGATIVE_WITNESS_PLAN="+json.dumps({
        "fingerprint":r["fingerprint"],
        "weak_targets":r["original_full_source_weak_one_sided_contrast_targets"],
        "candidate_species_site_records":r["source_unconfirmed_site_species_certificate_candidates"],
        "optimal_joint_site_cover":r["minimum_joint_counterfactual_design"],
        "candidate_sites":r["candidate_site_records"],
        "csv_artifacts":r["csv_artifacts"]
    },sort_keys=True))
