"""Positive-only conditional identified bounds for wetland method-recorded masks.

This is a source-authenticated post-exposure *logical* calculation. It assumes
source-recorded positives are truly positive, treats all unrecorded site×taxon
statuses as unconstrained, and tests a hypothetical static binary site state.
Neither assumption establishes occupancy closure, detection probability,
ecological process-world counts, or true biological absence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from benchmarks import wetland_method_channel_lattice_v1 as source

FIXED_REVERSALS = {
    ("intervention", "control", "Lissotriton vulgaris"),
    ("intervention", "control", "Bufo bufo"),
    ("intervention", "artificial", "Lissotriton vulgaris"),
    ("artificial", "control", "Lissotriton vulgaris"),
    ("artificial", "control", "Bufotes viridis"),
}
STATUSES = (
    "two_sided_strict_signs_possible",
    "nonnegative_only",
    "nonpositive_only",
    "exact_zero"
)


def bound_counts(k_a:int,n_a:int,k_b:int,n_b:int) -> dict:
    """Exact finite binary-completion bounds under positive specificity alone.

    Hypothetical site-level 0/1 prevalence A and B can independently be any
    value between observed-positive fraction k/n and 1. Both extremal
    completions and the all-present (difference zero) completion are feasible.
    The integer numerators share denominator n_a*n_b to avoid sign rounding.
    """
    if any(type(x) is not int for x in (k_a,n_a,k_b,n_b)):
        raise ValueError("positive count and denominator inputs must be integers")
    if n_a <= 0 or n_b <= 0 or not 0 <= k_a <= n_a or not 0 <= k_b <= n_b:
        raise ValueError("invalid source positive/denominator")
    denom=n_a*n_b
    low_num=k_a*n_b-denom
    high_num=denom-k_b*n_a
    observed_num=k_a*n_b-k_b*n_a
    if low_num>0 or high_num<0 or not low_num<=observed_num<=high_num:
        raise ValueError("invalid positive-only identified bounds")
    if low_num<0 and high_num>0:
        status="two_sided_strict_signs_possible"
    elif low_num==0 and high_num>0:
        status="nonnegative_only"
    elif low_num<0 and high_num==0:
        status="nonpositive_only"
    elif low_num==0 and high_num==0:
        status="exact_zero"
    else:
        raise ValueError("unexpected logical identified-sign status")
    return {
        "observed_positive_a":k_a, "observed_positive_b":k_b,
        "group_a_sites":n_a, "group_b_sites":n_b,
        "group_a_positive_only_lower_fraction":k_a/n_a,
        "group_a_positive_only_upper_fraction":1.0,
        "group_b_positive_only_lower_fraction":k_b/n_b,
        "group_b_positive_only_upper_fraction":1.0,
        "contrast_denominator":denom,
        "observed_difference_numerator":observed_num,
        "identified_lower_numerator":low_num,
        "identified_upper_numerator":high_num,
        "observed_recorded_difference_percentage_points":100*observed_num/denom,
        "conditional_latent_lower_percentage_points":100*low_num/denom,
        "conditional_latent_upper_percentage_points":100*high_num/denom,
        "observed_recorded_direction":source.sign(observed_num),
        "conditional_negative_possible":low_num<0,
        "conditional_zero_possible":True,
        "conditional_positive_possible":high_num>0,
        "conditional_strict_nonzero_sign_identified":False,
        "conditional_identification_status":status,
        "lower_bound_completion_present_A":k_a,
        "lower_bound_completion_present_B":n_b,
        "upper_bound_completion_present_A":n_a,
        "upper_bound_completion_present_B":k_b,
        "zero_difference_completion_present_A":n_a,
        "zero_difference_completion_present_B":n_b,
    }


def original_q1_source(survey_path,sites_path):
    source.sha_guard(survey_path,source.SURVEY_SHA,"surveys")
    source.sha_guard(sites_path,source.SITE_SHA,"sites")
    observations,columns=source.read_csv(survey_path)
    site_rows,_=source.read_csv(sites_path)
    taxa=[name for name in columns if name not in source.META]
    sites,positive_by_method,dates=source.validate_source(observations,site_rows,taxa)
    if len(taxa)!=9 or len(sites)!=27 or len(positive_by_method)!=144 or len(dates)!=117:
        raise ValueError("original authenticated 27-site Q1 input changed")
    return sites,positive_by_method,taxa


def panel_contrasts(sites, positive_by_method, taxa):
    panels=source.method_panels()
    support={}
    by_name={}
    results=[]
    summaries=[]
    groups={}
    for panel in panels:
        label=source.panel_name(panel)
        selected=source.positive_witnesses(positive_by_method,panel)
        support[label]=selected
        by_name[label]=panel
        group_rows=[]
        for cat in source.CATS:
            group_size=sum(x==cat for x in sites.values())
            if group_size!=source.EXPECTED_COUNTS[cat]:
                raise ValueError("category native denominator drift")
            for sp in taxa:
                positive=sum((s,sp) in selected for s,c in sites.items() if c==cat)
                group_rows.append({
                    "panel":label,"category":cat,"species":sp,
                    "category_source_site_count":group_size,
                    "recorded_positive_site_count":positive,
                    "recorded_positive_site_fraction":positive/group_size,
                    "static_binary_site_count_not_recorded_positive":group_size-positive
                })
        groups[label]={(r["category"],r["species"]):r for r in group_rows}
        status_counts={s:0 for s in STATUSES}
        for a,b in source.CONTRASTS:
            for sp in taxa:
                x=groups[label][(a,sp)];y=groups[label][(b,sp)]
                row={
                    "panel":label,
                    "panel_method_count":len(panel),
                    "category_a":a,"category_b":b,"species":sp,
                    **bound_counts(x["recorded_positive_site_count"],x["category_source_site_count"],
                                   y["recorded_positive_site_count"],y["category_source_site_count"])
                }
                status_counts[row["conditional_identification_status"]]+=1
                results.append(row)
        count_free=27*9-len(selected)
        summaries.append({
            "panel":label,
            "panel_method_count":len(panel),
            "hypothetical_static_site_species_cells":27*9,
            "native_source_positive_site_species_recorded_in_panel":len(selected),
            "unfixed_binary_site_species_cells":count_free,
            "unconstrained_binary_completion_count_exact":str(1<<count_free),
            "unconstrained_binary_completion_log2_count":count_free,
            "is_ecological_EOG_transition_world_count":False,
            "source_positive_recorded_constraints_only":True,
            "contrasts":len(source.CONTRASTS)*len(taxa),
            "conditional_strict_direction_identified_count":0,
            **{"contrasts_"+key:status_counts[key] for key in STATUSES}
        })

    full_label=source.panel_name(source.METHODS)
    av_label=source.panel_name(("acoustic","visual"))
    full_support=support[full_label]
    av_support=support[av_label]
    if len(full_support)!=144 or len(av_support)!=104:
        raise ValueError("previous full vs paired AV positive source audit mismatch")
    if not av_support<=full_support:
        raise ValueError("recorded restricted positives unexpectedly exceed full source")

    by_contrast={(r["panel"],r["category_a"],r["category_b"],r["species"]):r
                 for r in results}
    av_flips=[]
    for a,b in source.CONTRASTS:
        for sp in taxa:
            f=by_contrast[(full_label,a,b,sp)]
            av=by_contrast[(av_label,a,b,sp)]
            if f["observed_recorded_direction"]*av["observed_recorded_direction"]<0:
                key=(a,b,sp)
                av_flips.append({
                    "category_a":a,"category_b":b,"species":sp,
                    "full_observed_difference_pp":f["observed_recorded_difference_percentage_points"],
                    "paired_av_observed_difference_pp":av["observed_recorded_difference_percentage_points"],
                    "full_lower_pp":f["conditional_latent_lower_percentage_points"],
                    "full_upper_pp":f["conditional_latent_upper_percentage_points"],
                    "paired_av_lower_pp":av["conditional_latent_lower_percentage_points"],
                    "paired_av_upper_pp":av["conditional_latent_upper_percentage_points"],
                    "full_bounds_identification_status":f["conditional_identification_status"],
                    "paired_av_bounds_identification_status":av["conditional_identification_status"],
                    "strict_paired_observed_sign_ruled_out_by_full_source_bounds":(
                        (av["observed_recorded_direction"]>0 and
                         f["identified_upper_numerator"]<=0) or
                        (av["observed_recorded_direction"]<0 and
                         f["identified_lower_numerator"]>=0)
                    ),
                    "full_constraints_imply_interval_inside_paired_av_interval":(
                        av["identified_lower_numerator"]<=f["identified_lower_numerator"] and
                        f["identified_upper_numerator"]<=av["identified_upper_numerator"])
                })
    if {(z["category_a"],z["category_b"],z["species"]) for z in av_flips}!=FIXED_REVERSALS:
        raise ValueError("original five recorded AV vs full sign reversals changed")
    for a in panels:
        for b in panels:
            if not set(a)<=set(b):continue
            lab_a=source.panel_name(a); lab_b=source.panel_name(b)
            if not support[lab_a]<=support[lab_b]:
                raise ValueError("positive source witness inclusion broken")
            for ca,cb in source.CONTRASTS:
                for sp in taxa:
                    lower=by_contrast[(lab_a,ca,cb,sp)]
                    upper=by_contrast[(lab_b,ca,cb,sp)]
                    if (lower["contrast_denominator"]!=upper["contrast_denominator"]
                            or lower["identified_lower_numerator"]>upper["identified_lower_numerator"]
                            or upper["identified_upper_numerator"]>lower["identified_upper_numerator"]):
                        raise ValueError("nested method conditional identified interval is not nested")
    # Source-positive records constrain any method-subset reading even if the
    # observed AV percentage point contrast changes sign.
    if len(results)!=405 or len(summaries)!=15 or len(av_flips)!=5:
        raise ValueError("method/taxon/contrast result table incomplete")

    # Enumerate all 243 possible Q1 site×taxon cell identifiers as provenance
    # so none of the unrecorded positives are silently converted into absences.
    per_site=[
        {
            "site":site,"category":sites[site],"species":sp,
            "original_full_recorded_positive":int((site,sp) in full_support),
            "paired_acoustic_visual_recorded_positive":int((site,sp) in av_support),
            "positive_recorded_in_which_methods":";".join(
                m for m in source.METHODS if m in positive_by_method.get((site,sp),set())),
            "not_recorded_positive_is_missing_true_status":int((site,sp) not in full_support)
        }for site in sorted(sites) for sp in taxa
    ]
    if len(per_site)!=243 or sum(r["original_full_recorded_positive"] for r in per_site)!=144:
        raise ValueError("original static site×taxon mask bookkeeping changed")
    full_row=next(r for r in summaries if r["panel"]==full_label)
    av_row=next(r for r in summaries if r["panel"]==av_label)
    if (full_row["unfixed_binary_site_species_cells"],
        av_row["unfixed_binary_site_species_cells"])!=(99,139):
        raise ValueError("site/taxon unknown cell denominator differs")
    if any(z["conditional_strict_nonzero_sign_identified"] for z in results):
        raise ValueError("positive-only data unexpectedly identified a strict sign")
    return {
        "schema":"eog.wetland_positive_only_partial_id_v1.result",
        "status":"CONDITIONAL_SOURCE_POSITIVE_PARTIAL_IDENTIFICATION_NOT_OCCUPANCY",
        "role":"POST_EXPOSURE_LOGICAL_STATIC_BINARY_STATUS_BOUNDS",
        "assumption":"Recorded positive counts are perfectly specific, non-positive records are unrestricted unknown; hypothetical closed binary site/species state is NOT field-verified.",
        "source_Q1_sites":len(sites),"taxa":len(taxa),
        "source_binary_site_species_cells":243,
        "full_source_positive_site_species":len(full_support),
        "paired_AV_positive_site_species":len(av_support),
        "full_source_unfixed_binary_status_cells":99,
        "AV_unfixed_binary_status_cells":139,
        "AV_vs_full_extra_unfixed_binary_status_cells":40,
        "hypothetical_completion_count_multiplier_AV_vs_full":"2^40",
        "completions_are_not_EOG_ecological_transition_worlds":True,
        "all_method_panels":list(map(list,panels)),
        "nested_method_panel_positive_constraints_and_intervals_verified":True,
        "all_conditional_identification_intervals_include_zero":True,
        "no_strict_biological_contrast_direction_identified_from_positive_only_data":True,
        "method_panel_summaries":summaries,
        "five_original_recorded_method_sign_reversals":av_flips,
        "outputs":{
            "method_panel_identification_intervals":results,
            "method_panel_positive_only_summary":summaries,
            "native_site_species_recording_mask":per_site,
            "five_method_reversals_identification_bounds":av_flips
        },
        "limitations":[
            "Source-positive validity (no false positives) is a conditional assumption, not independently audited biology.",
            "Hypothetical site×species binary status over an original up-to-91-day field period is not a proven closed biological state.",
            "No negative field observation or detection probability model has been authenticated. A recorded zero is not true ecological absence.",
            "The 2^n values count unconstrained static Boolean completions, not actual viable EOG transition worlds, process identification or information entropy.",
            "Five original method-induced descriptive sign reversals are not identified latent occupancy-rate sign reversals or causal restoration effects.",
            "No original occupancy model fitted, physical trap independence/effort/closure certified, A/B/M attributed, fourth EOG-WF scored endpoint or PR merge."
        ]
    }


def run(survey_path,site_path,out_dir):
    sites,positive_by_method,taxa=original_q1_source(survey_path,site_path)
    result=panel_contrasts(sites,positive_by_method,taxa)
    outputs=result.pop("outputs")
    folder=Path(out_dir);folder.mkdir(parents=True,exist_ok=True)
    result["output_files"]={}
    for name,rows in outputs.items():
        path=folder/f"{name}.csv"
        with path.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]))
            w.writeheader();w.writerows(rows)
        result["output_files"][name]={
            "filename":path.name,"rows":len(rows),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--surveys",type=Path,required=True)
    parser.add_argument("--sites",type=Path,required=True)
    parser.add_argument("--out-dir",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    out=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("WETLAND_POSITIVE_ONLY_PARTIAL_ID="+json.dumps({
        "fingerprint":out["fingerprint"],
        "native":out["full_source_positive_site_species"],
        "paired_AV":out["paired_AV_positive_site_species"],
        "full_unfixed":out["full_source_unfixed_binary_status_cells"],
        "AV_unfixed":out["AV_unfixed_binary_status_cells"],
        "panel_sign_status":[{
            "panel":r["panel"],
            "two_sided":r["contrasts_two_sided_strict_signs_possible"],
            "weak_positive":r["contrasts_nonnegative_only"],
            "weak_negative":r["contrasts_nonpositive_only"],
            "zero":r["contrasts_exact_zero"]
        }for r in out["method_panel_summaries"]],
        "five_original_reversals":out["five_original_recorded_method_sign_reversals"],
        "artifacts":out["output_files"]
    },sort_keys=True))
