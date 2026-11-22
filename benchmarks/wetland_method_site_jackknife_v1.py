"""Exhaustive site-deletion stability of the source-observation method lattice.

All 27 original Q1 sites are removed one at a time; all 15 previously fixed
recorded method panels and all 27 taxa/category contrasts are evaluated on
the SAME 26 remaining sites in each comparison. This is deterministic
post-exposure source robustness, not a jackknife SE or ecological occupancy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from benchmarks import wetland_method_channel_lattice_v1 as base

EXPECTED_AV_FIVE={
    ("intervention","control","Lissotriton vulgaris"),
    ("intervention","control","Bufo bufo"),
    ("intervention","artificial","Lissotriton vulgaris"),
    ("artificial","control","Lissotriton vulgaris"),
    ("artificial","control","Bufotes viridis"),
}
EXPECTED_TOTALS={"intervention":13,"control":6,"artificial":8}


def calc_contrast(support,sites,species,cat_a,cat_b):
    """Native source counts and signed fractions for exactly one pair of groups."""
    if cat_a==cat_b or cat_a not in base.CATS or cat_b not in base.CATS:
        raise ValueError("unknown or same source wetland category")
    na=sum(x==cat_a for x in sites.values())
    nb=sum(x==cat_b for x in sites.values())
    a=sum((site,species) in support for site,c in sites.items() if c==cat_a)
    b=sum((site,species) in support for site,c in sites.items() if c==cat_b)
    value,den=base.exact_difference(a,b,na,nb)
    return {
        "category_a_n":na, "category_b_n":nb,
        "category_a_positive_sites":a, "category_b_positive_sites":b,
        "numerator":value,"denominator":den,
        "signed_direction":base.sign(value),
        "difference_percentage_points":100*value/den,
    }


def pure_jackknife(sites,method_by_pair,species):
    """No model fit, random sampling, or statistical independence assumption."""
    if len(set(sites))!=len(sites) or not sites or len(set(species))!=len(species):
        raise ValueError("invalid source site/taxa roster")
    if set(sites.values())!=set(base.CATS) or any(
        sum(c==cat for c in sites.values())<2 for cat in base.CATS
    ):
        raise ValueError("source category needs >=2 sites for leave-one-site-out")
    if any(s not in sites or sp not in species or not methods
           or not methods <=set(base.METHODS)
           for (s,sp),methods in method_by_pair.items()):
        raise ValueError("native positive site/species/method witness invalid")
    panels=base.method_panels()
    labels={p:base.panel_name(p) for p in panels}
    supports={p:base.positive_witnesses(method_by_pair,p) for p in panels}
    full=supports[base.METHODS]
    original_direction={}
    baseline_flips={}
    for cat_a,cat_b in base.CONTRASTS:
        for sp in species:
            key=(cat_a,cat_b,sp)
            orig=calc_contrast(full,sites,sp,cat_a,cat_b)
            original_direction[key]=orig["signed_direction"]
    for panel in panels:
        baseline_flips[labels[panel]]=set()
        for cat_a,cat_b in base.CONTRASTS:
            for sp in species:
                k=(cat_a,cat_b,sp)
                a=calc_contrast(full,sites,sp,cat_a,cat_b)["numerator"]
                b=calc_contrast(supports[panel],sites,sp,cat_a,cat_b)["numerator"]
                if a*b<0: baseline_flips[labels[panel]].add(k)
    if len(sites)==27 and (
        Counter(sites.values())!=Counter(EXPECTED_TOTALS)
        or len(full)!=144
        or baseline_flips["acoustic+visual"]!=EXPECTED_AV_FIVE
    ):
        raise ValueError("previous Q1 fixed source five-reversal baseline changed")

    long=[]
    rows=[]
    five=[]
    per_key_per_panel={} # (panel, original contrast) -> number of leave-one-out strict reversals
    for panel in panels:
        panel_label=labels[panel]
        panel_support=supports[panel]
        for dropped in sorted(sites):
            remaining={s:c for s,c in sites.items() if s!=dropped}
            source_full={(s,sp) for s,sp in full if s!=dropped}
            source_panel={(s,sp) for s,sp in panel_support if s!=dropped}
            if not source_panel<=source_full:
                raise ValueError("subset added unsupported positive witness")
            flips=0;ties=0; baseline_sign_changed=0
            for cat_a,cat_b in base.CONTRASTS:
                for sp in species:
                    key=(cat_a,cat_b,sp)
                    full_contrast=calc_contrast(source_full,remaining,sp,cat_a,cat_b)
                    panel_contrast=calc_contrast(source_panel,remaining,sp,cat_a,cat_b)
                    full_sign=full_contrast["signed_direction"]
                    panel_sign=panel_contrast["signed_direction"]
                    flip=full_sign*panel_sign<0
                    tie_changed=(full_sign==0)!=(panel_sign==0)
                    raw_base_sign=original_direction[key]
                    changed_base=full_sign!=raw_base_sign
                    flips+=int(flip)
                    ties+=int(tie_changed)
                    baseline_sign_changed+=int(changed_base)
                    row={
                        "panel":panel_label,
                        "panel_method_count":len(panel),
                        "excluded_site":dropped,
                        "excluded_site_category":sites[dropped],
                        "category_a":cat_a,"category_b":cat_b,"species":sp,
                        "original_27_site_full_sign":raw_base_sign,
                        "remaining_26_full_numerator":full_contrast["numerator"],
                        "remaining_26_panel_numerator":panel_contrast["numerator"],
                        "remaining_category_a_n":full_contrast["category_a_n"],
                        "remaining_category_b_n":full_contrast["category_b_n"],
                        "remaining_full_category_a_positive_count":full_contrast["category_a_positive_sites"],
                        "remaining_full_category_b_positive_count":full_contrast["category_b_positive_sites"],
                        "remaining_panel_category_a_positive_count":panel_contrast["category_a_positive_sites"],
                        "remaining_panel_category_b_positive_count":panel_contrast["category_b_positive_sites"],
                        "remaining_full_difference_pp":full_contrast["difference_percentage_points"],
                        "remaining_panel_difference_pp":panel_contrast["difference_percentage_points"],
                        "remaining_full_direction":full_sign,
                        "remaining_panel_direction":panel_sign,
                        "method_subset_strict_reversal_after_site_drop":int(flip),
                        "method_subset_tie_transition_after_site_drop":int(tie_changed),
                        "full_source_original_27_sign_changed_after_site_drop":int(changed_base),
                        "was_strict_reversal_in_original_27":int(key in baseline_flips[panel_label])
                    }
                    long.append(row)
                    per_key_per_panel.setdefault((panel_label,key),[]).append(row)
                    if panel_label=="acoustic+visual" and key in EXPECTED_AV_FIVE:
                        five.append(row)
            rows.append({
                "panel":panel_label,"panel_method_count":len(panel),
                "excluded_site":dropped,
                "excluded_site_category":sites[dropped],
                "remaining_site_count":len(remaining),
                "remaining_full_positive_site_species":len(source_full),
                "remaining_subset_positive_site_species":len(source_panel),
                "native_positive_witnesses_lost_by_subset":len(source_full-source_panel),
                "strict_method_reversals_out_of_27":flips,
                "method_tie_transitions_out_of_27":ties,
                "full_original_baseline_sign_changes_out_of_27":baseline_sign_changed
            })
    n_panels=len(panels)
    expected=(n_panels*len(sites)*len(base.CONTRASTS)*len(species))
    if len(long)!=expected or len(rows)!=n_panels*len(sites):
        raise ValueError("missing fixed method/site/taxon contrast outcome")
    if len(sites)==27 and len(five)!=len(EXPECTED_AV_FIVE)*len(sites):
        raise ValueError("original five reversals not fully tracked")

    def aggregate(rows_for_panel):
        vec=[x["strict_method_reversals_out_of_27"] for x in rows_for_panel]
        return {
            "original_27_strict_reversals":len(baseline_flips[rows_for_panel[0]["panel"]]),
            "leave_one_site_out_cases":len(vec),
            "min":min(vec),"median":statistics.median(vec),"max":max(vec),
            "mean_descriptive":statistics.mean(vec),
            "deletions_with_zero_reversals":sum(x==0 for x in vec),
            "deletions_with_at_least_one_reversal":sum(x>0 for x in vec)
        }

    panel_summary={
        labels[p]:aggregate([x for x in rows if x["panel"]==labels[p]])
        for p in panels
    }
    five_summary=[]
    for k in sorted(EXPECTED_AV_FIVE):
        details=per_key_per_panel.get(("acoustic+visual",k),[])
        if not details: continue
        assert all(x["was_strict_reversal_in_original_27"]==1 for x in details)
        persists=sum(x["method_subset_strict_reversal_after_site_drop"]==1 for x in details)
        tie=sum(x["remaining_full_direction"]==0 or
                x["remaining_panel_direction"]==0 for x in details)
        same=sum(x["remaining_full_direction"]==x["remaining_panel_direction"] and
                 x["remaining_full_direction"]!=0 for x in details)
        if persists+tie+same!=len(sites):
            raise ValueError("unclassified original reversal after site deletion")
        five_summary.append({
            "comparison":f"{k[0]}_minus_{k[1]}","species":k[2],
            "original_27_strict_reversal":True,
            "leave_one_site_out_cases":len(details),
            "strict_reversal_persists_count":persists,
            "source_or_panel_tie_count":tie,
            "becomes_same_nonzero_sign_count":same,
            "original_full_source_sign_changed_or_tied_count":sum(
                x["full_source_original_27_sign_changed_after_site_drop"]==1
                for x in details
            ),
            "by_deleted_site_category":{
                cat:{
                    "number_of_deletions":sum(x["excluded_site_category"]==cat for x in details),
                    "reversal_persists":sum(x["excluded_site_category"]==cat and
                        x["method_subset_strict_reversal_after_site_drop"]==1 for x in details)
                }for cat in base.CATS
            },
            "deletion_sites_losing_strict_reversal":[
                x["excluded_site"] for x in details
                if not x["method_subset_strict_reversal_after_site_drop"]
            ]
        })
    if len(sites)==27 and len(five_summary)!=5:
        raise ValueError("expected five original acoustic/visual signs missing")
    if panel_summary[labels[base.METHODS]]["max"]!=0:
        raise ValueError("full panel should never be incompatible with itself")
    return {
        "source_site_count":len(sites),
        "native_full_positive_site_species":len(full),
        "method_panel_count":len(panels),
        "taxa_count":len(species),
        "contrast_count_per_panel_site_drop":len(base.CONTRASTS)*len(species),
        "site_deletion_cases":len(sites),
        "full_27_baseline_strict_reversals_by_panel":{
            k:len(v) for k,v in sorted(baseline_flips.items())
        },
        "panel_summary":panel_summary,
        "original_five_acoustic_visual_reversal_persistence":five_summary,
        "all_original_sites_deleted_once":True,
        "all_panel_comparisons_use_matched_remaining_26_native_sites":True,
        "outputs":{
            "method_panel_site_drop_summary":rows,
            "method_panel_site_drop_contrasts":long,
            "original_five_acoustic_visual_site_drop_details":five
        }
    }


def run(surveys_path,sites_path,outdir):
    base.sha_guard(surveys_path,base.SURVEY_SHA,"survey")
    base.sha_guard(sites_path,base.SITE_SHA,"sites")
    surveys,cols=base.read_csv(surveys_path)
    site_table,_=base.read_csv(sites_path)
    species=[x for x in cols if x not in base.META]
    source_sites,source_witnesses,by_day=base.validate_source(surveys,site_table,species)
    if len(by_day)!=117:
        raise ValueError("source Q1 calendar date roster drift")
    result=pure_jackknife(source_sites,source_witnesses,species)
    outputs=result.pop("outputs")
    d=Path(outdir);d.mkdir(parents=True,exist_ok=True)
    result["output_files"]={}
    for name,rows in outputs.items():
        path=d/f"{name}.csv"
        with path.open("w",encoding="utf-8",newline="") as fh:
            writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
        result["output_files"][name]={
            "filename":path.name, "rows":len(rows),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
    result["schema"]="eog.wetland_method_site_jackknife_v1.result"
    result["status"]="POST_EXPOSURE_SOURCE_SITE_DELETION_METHOD_REVERSAL_ROBUSTNESS_NOT_ECOLOGICAL_SE"
    result["role"]="DETERMINISTIC_REPEATED_SAME_SOURCE_SENSITIVITY"
    result["source_sha256"]={"survey":base.SURVEY_SHA,"site":base.SITE_SHA}
    result["original_occupancy_model_fitted"]=False
    result["latent_effect_confidence_interval_estimated"]=False
    result["biological_independence_certified"]=False
    result["limits"]=[
        "Exactly one of 27 observed source sites is omitted at a time; the 27 deletion results are dependent deterministic diagnostics, not 27 independent ecological tests.",
        "Both full and method-restricted contrasts are recomputed on the same 26 sites with exact changed group denominators; no biological species absences are certified.",
        "The original study categories were not randomized treatment assignments; no causal restoration effect is estimated.",
        "Missing method row is not proof of field nondeployment; method effort/detection probability, physical trap IDs and 91-day season closure remain unverified.",
        "No original unmarked occupancy coefficients, causal abiotic/biotic/movement A/B/M, ecological world-count proof, fresh EOG-WF endpoint or PR merge."
    ]
    result["fingerprint"]=hashlib.sha256(json.dumps(
        result,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--out-dir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("WETLAND_SITE_JACKKNIFE="+json.dumps({
        "fingerprint":r["fingerprint"],
        "sites":r["source_site_count"],
        "panel":r["method_panel_count"],
        "outcomes":r["output_files"],
        "AV_panel_summary":r["panel_summary"]["acoustic+visual"],
        "all_four_panel_summary":r["panel_summary"]["acoustic+visual+dipnet+bottletrap"],
        "original_five":r["original_five_acoustic_visual_reversal_persistence"]
    },sort_keys=True))
