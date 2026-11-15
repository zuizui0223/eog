"""Exhaustive 15-panel wetland observation-method source-record lattice.

One original 27-site Q1 cohort, 9 native species, 4 recorded method families.
This compares deterministic *recorded source-positive witness* masks and their
category contrasts. It is neither occupancy modeling nor ecological causality.
No physical trap identity, equal effort, detection probabilities, or closure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA = "93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
META = {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
METHODS = ("acoustic","visual","dipnet","bottletrap")
CATS = ("intervention","control","artificial")
CONTRASTS = (("intervention","control"),("intervention","artificial"),
             ("artificial","control"))
EXPECTED_COUNTS = {"intervention":13,"control":6,"artificial":8}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader),list(reader.fieldnames)


def sha_guard(path, expected, title):
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError(f"{title} source SHA256 mismatch")


def method_panels():
    return tuple(itertools.chain.from_iterable(
        itertools.combinations(METHODS,k) for k in range(1,len(METHODS)+1)
    ))


def panel_name(methods):
    if not methods or len(set(methods))!=len(methods) or not set(methods)<=set(METHODS):
        raise ValueError("invalid observation method panel")
    if tuple(m for m in METHODS if m in methods)!=tuple(methods):
        raise ValueError("method panel order not source-declared")
    return "+".join(methods)


def positive_witnesses(method_by_site_species, panel):
    selected=set(panel)
    if not selected or not selected<=set(METHODS):
        raise ValueError("unsupported method subset")
    return {pair for pair,detected_methods in method_by_site_species.items()
            if detected_methods & selected}


def exact_difference(a_count,b_count,a_n,b_n):
    if any(type(v)!=int for v in (a_count,b_count,a_n,b_n)):
        raise ValueError("fraction cross-product inputs must be integer")
    if a_n<=0 or b_n<=0 or not 0<=a_count<=a_n or not 0<=b_count<=b_n:
        raise ValueError("native category counts outside declared site denominator")
    return a_count*b_n-b_count*a_n, a_n*b_n


def sign(value):
    return (value>0)-(value<0)


def validate_source(surveys, site_records, species):
    if len(surveys)!=381 or len(site_records)!=29 or len(species)!=9 or len(set(species))!=9:
        raise ValueError("frozen original source dimensions or species changed")
    sites={row["site"]:row["ci"] for row in site_records
           if row["site"] not in {"kis-banyato","vadasz-turjan"}}
    if len(sites)!=27 or Counter(sites.values())!=Counter(EXPECTED_COUNTS):
        raise ValueError("original 27-site Q1 categories/denominators changed")
    if len({row["site"] for row in site_records})!=29:
        raise ValueError("original source site IDs not unique")
    scoped=[row for row in surveys if row["site"] in sites]
    if len(scoped)!=351 or {row["site"] for row in scoped}!=set(sites):
        raise ValueError("original Q1 native survey rows/sites changed")
    by_date=defaultdict(Counter)
    detected_by_pair=defaultdict(set)
    for row in scoped:
        site=row["site"]; method=row["method"]
        if method not in METHODS:
            raise ValueError("unexpected original source recording method")
        dt=date.fromisoformat(row["date"])
        if dt.timetuple().tm_yday!=int(row["doy"]):
            raise ValueError("native date/day-of-year mismatch")
        if row["surv"]!=f"{site}:{method}:{row['doy']}":
            raise ValueError("source group key mismatched site:method:doy")
        by_date[(site,row["date"])][method]+=1
        for sp in species:
            n=int(row[sp])
            if n<0:
                raise ValueError("negative native species count")
            if n>0:
                detected_by_pair[(site,sp)].add(method)
    if len(by_date)!=117:
        raise ValueError("actual site×date count drift")
    if any(row["acoustic"]!=1 or row["visual"]!=1 for row in by_date.values()):
        raise ValueError("frozen acoustic and visual recorded-pair coverage changed")
    if len(detected_by_pair)!=144:
        raise ValueError("native source-positive site×species baseline changed")
    if len(positive_witnesses(detected_by_pair,("acoustic","visual")))!=104:
        raise ValueError("previous source-pinned AV positive baseline changed")
    return sites,detected_by_pair,by_date


def compute_lattice(sites, method_by_pair, by_date, species):
    panels=method_panels()
    if len(panels)!=15 or panels[-1]!=METHODS:
        raise ValueError("fixed 15-method subset roster changed")
    if any(not s or not s<=set(METHODS) for s in method_by_pair.values()):
        raise ValueError("invalid or empty source-positive method witness")
    if len(sites)!=27 or len(method_by_pair)!=144:
        raise ValueError("actual source site and positive roster changed")
    full=set(method_by_pair)
    rows=[]
    contrast_rows=[]
    snapshots={}
    baseline_category_counts={}
    for cat in CATS:
        baseline_category_counts[cat]={
            sp:sum((site,sp) in full for site in sites if sites[site]==cat)
            for sp in species
        }
    full_dirs={}
    for a,b in CONTRASTS:
        for sp in species:
            val,_=exact_difference(baseline_category_counts[a][sp],
                                   baseline_category_counts[b][sp],
                                   EXPECTED_COUNTS[a],EXPECTED_COUNTS[b])
            full_dirs[(a,b,sp)]=sign(val)

    panel_name_for_3_exclusion={}
    for method in METHODS:
        remaining=tuple(m for m in METHODS if m!=method)
        panel_name_for_3_exclusion[method]=panel_name(remaining)
    one_method_exclusive={
        method:{pair for pair,ms in method_by_pair.items() if ms=={method}}
        for method in METHODS
    }
    core_seen=positive_witnesses(method_by_pair,("acoustic","visual"))
    for panel in panels:
        panel_set=set(panel)
        label=panel_name(panel)
        positives=positive_witnesses(method_by_pair,panel)
        if not positives<=full:
            raise ValueError("source-absent species became panel-positive")
        source_loss=full-positives
        cat_counts={
            cat:sum(site in sites and sites[site]==cat for site,sp in positives)
            for cat in CATS
        }
        if sum(cat_counts.values())!=len(positives):
            raise ValueError("category source-positive set was not partitioned")
        eligible_days=sum(
            all(method_count[m]>0 for m in panel)
            for method_count in by_date.values()
        )
        all_days=len(by_date)
        category_per_species={}
        for cat in CATS:
            category_per_species[cat]={
                sp:sum((site,sp) in positives for site in sites if sites[site]==cat)
                for sp in species
            }
        reversed_n=0
        ties_changed_n=0
        for a,b in CONTRASTS:
            for sp in species:
                native_num,den=exact_difference(
                    baseline_category_counts[a][sp],baseline_category_counts[b][sp],
                    EXPECTED_COUNTS[a],EXPECTED_COUNTS[b])
                current_num,_=exact_difference(
                    category_per_species[a][sp],category_per_species[b][sp],
                    EXPECTED_COUNTS[a],EXPECTED_COUNTS[b])
                reversed_flag=native_num*current_num<0
                tie_transition=(native_num==0)!=(current_num==0)
                reversed_n+=int(reversed_flag)
                ties_changed_n+=int(tie_transition)
                contrast_rows.append({
                    "subset":label,
                    "method_count":len(panel),
                    "category_A":a,
                    "category_B":b,
                    "species":sp,
                    "native_full_A_positive_sites":baseline_category_counts[a][sp],
                    "native_full_B_positive_sites":baseline_category_counts[b][sp],
                    "subset_A_positive_sites":category_per_species[a][sp],
                    "subset_B_positive_sites":category_per_species[b][sp],
                    "A_site_count":EXPECTED_COUNTS[a],
                    "B_site_count":EXPECTED_COUNTS[b],
                    "native_full_difference_pp":100*native_num/den,
                    "subset_difference_pp":100*current_num/den,
                    "difference_shift_pp":100*(current_num-native_num)/den,
                    "native_full_direction":sign(native_num),
                    "subset_direction":sign(current_num),
                    "strict_nonzero_direction_reversal":int(reversed_flag),
                    "tie_transition":int(tie_transition)
                })
        rows.append({
            "subset":label,
            "method_count":len(panel),
            "all_four_methods":int(panel==METHODS),
            "native_full_source_positive_pairs":len(full),
            "subset_recorded_positive_pairs":len(positives),
            "source_positive_pairs_not_seen":len(source_loss),
            "subset_fraction_of_native_positive_pairs":len(positives)/len(full),
            "intervention_positive_pairs":cat_counts["intervention"],
            "control_positive_pairs":cat_counts["control"],
            "artificial_positive_pairs":cat_counts["artificial"],
            "site_date_groups_with_every_selected_method_record":eligible_days,
            "total_source_site_date_groups":all_days,
            "strict_reversals_vs_native_27_contrasts":reversed_n,
            "tie_transitions_vs_native_27_contrasts":ties_changed_n,
            "entire_native_positive_pair_mask_preserved":int(positives==full),
            "all_27_category_contrast_directions_preserved":
                int(all(full_dirs[(a,b,sp)]==(
                    next(z["subset_direction"] for z in contrast_rows[-27:]
                         if z["category_A"]==a and z["category_B"]==b and z["species"]==sp)
                    ) for a,b in CONTRASTS for sp in species)),
        })
        snapshots[label]=positives
    if len(rows)!=15 or len(contrast_rows)!=405:
        raise ValueError("all method lattice outcomes not recorded")
    if snapshots[panel_name(METHODS)]!=full or snapshots[panel_name(("acoustic","visual"))]!=core_seen:
        raise ValueError("original full/AV source-positive masks altered")
    # Verify the complete Boolean lattice, not merely each mask's containment in full.
    for a in panels:
        for b in panels:
            if set(a)<=set(b) and not snapshots[panel_name(a)]<=snapshots[panel_name(b)]:
                raise ValueError("method-source positive monotonicity broken")
    # Source-positive witnesses that appear in only one method family are
    # necessarily removed when that family is dropped.
    loo={}
    for method in METHODS:
        label=panel_name_for_3_exclusion[method]
        panel_row=next(x for x in rows if x["subset"]==label)
        if panel_row["source_positive_pairs_not_seen"]!=len(one_method_exclusive[method]):
            raise ValueError("leave-one-method-out loss contradicts exclusive source witnesses")
        loo[method]={
            "subset":label,
            "exclusive_source_positive_site_species_lost":len(one_method_exclusive[method]),
            "strict_reversals_vs_full":panel_row["strict_reversals_vs_native_27_contrasts"],
            "all_source_positive_retained":bool(panel_row["entire_native_positive_pair_mask_preserved"]),
            "source_positives_after_removal":panel_row["subset_recorded_positive_pairs"],
            "exclusive_lost_by_category":{
                cat:sum(sites[site]==cat for site,sp in one_method_exclusive[method])
                for cat in CATS
            },
            "exclusive_lost_by_species":{
                sp:sum(p[1]==sp for p in one_method_exclusive[method])
                for sp in species
            }
        }

    minimal_witness_size=min(r["method_count"] for r in rows
                             if r["entire_native_positive_pair_mask_preserved"])
    minimal_sign_size=min(r["method_count"] for r in rows
                          if r["all_27_category_contrast_directions_preserved"])
    # Shapley value of a Boolean OR witness channel: with k methods recording
    # the source positive, the arithmetic 1/k share of its first contribution
    # is attributed to each method. Accounting only, never a biological effect.
    per_pair=[]
    allocation={cat:{method:0.0 for method in METHODS} for cat in CATS}
    for site,sp in sorted(full):
        m=method_by_pair[(site,sp)]
        val=1/len(m)
        for method in m:
            allocation[sites[site]][method]+=val
        row={
            "site":site, "species":sp, "category":sites[site],
            "native_full_recorded_positive":1,
            "number_of_methods_recording_positive":len(m),
            "methods_recording_positive":";".join(x for x in METHODS if x in m),
        }
        for method in METHODS:
            row[method+"_recorded_positive"]=int(method in m)
            row[method+"_boolean_or_allocation"]=val if method in m else 0.0
            row[method+"_exclusive_witness"]=int(m=={method})
        per_pair.append(row)
    all_share=sum(sum(vals.values()) for vals in allocation.values())
    if abs(all_share-len(full))>1e-9:
        raise ValueError("positive witness allocation not exhaustive")

    return {
        "schema":"eog.wetland_method_channel_lattice_v1.result",
        "status":"PINNED_SOURCE_EXHAUSTIVE_15_METHOD_SUBSETS_OBSERVATION_ONLY",
        "role":"POST_EXPOSURE_RECORDED_METHOD_EVIDENCE_LATTICE_NO_OCCUPANCY",
        "source_cohort":"published_q1_27_sites",
        "source_site_dates":len(by_date),
        "full_source_positive_site_species_pairs":len(full),
        "all_four_methods":list(METHODS),
        "full_q1_category_sites":EXPECTED_COUNTS,
        "method_panels":[list(x) for x in panels],
        "positive_evidence_monotone_over_every_nested_subset":True,
        "method_subsets":rows,
        "method_subset_contrasts":contrast_rows,
        "native_positive_site_species_witnesses":per_pair,
        "leave_one_method_out":loo,
        "minimal_full_source_positive_witness_panels":{
            "min_method_count":minimal_witness_size,
            "panels":[r["subset"] for r in rows
                      if r["method_count"]==minimal_witness_size
                      and r["entire_native_positive_pair_mask_preserved"]]
        },
        "minimal_all_27_signs_preserving_panels":{
            "min_method_count":minimal_sign_size,
            "panels":[r["subset"] for r in rows
                      if r["method_count"]==minimal_sign_size
                      and r["all_27_category_contrast_directions_preserved"]]
        },
        "boolean_or_witness_allocation_by_category":allocation,
        "boolean_or_witness_allocation_sum":all_share,
        "limitations":[
            "All 15 panels use the same original 2024 source sites/rows. Method subset choice is not independent ecological treatment or replication.",
            "The source has no verified equal method effort or latent occupancy. Missing dipnet or trap CSV row does not establish nondeployment.",
            "Method-only source-positive omissions are not recorded true species absences.",
            "Method OR allocation is a Shapley-style arithmetic accounting for co-detecting methods, not species biology, effort, field causal influence or detection probabilities.",
            "Original group denominators intervention=13, control=6, artificial=8 are small and observational, not randomized restoration assignments.",
            "No occupancy fitting, seasonal closure proof, model causal A/B/M, real EOG world enumeration, fourth EOG-WF scored predictive endpoint or PR merge."
        ]
    }


def run(survey_file,site_file,outdir):
    sha_guard(survey_file,SURVEY_SHA,"survey")
    sha_guard(site_file,SITE_SHA,"site")
    surveys,cols=read_csv(survey_file)
    sites,_=read_csv(site_file)
    species=[name for name in cols if name not in META]
    classes,detected,by_date=validate_source(surveys,sites,species)
    result=compute_lattice(classes,detected,by_date,species)
    output=Path(outdir)
    output.mkdir(parents=True,exist_ok=True)
    files={
        "method_subsets":result.pop("method_subsets"),
        "method_subset_contrasts":result.pop("method_subset_contrasts"),
        "native_positive_site_species_witnesses":result.pop("native_positive_site_species_witnesses")
    }
    result["output_files"]={}
    for key,rows in files.items():
        path=output/(key+".csv")
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        result["output_files"][key]={
            "name":path.name,
            "rows":len(rows),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
    # Summary rows retained inline for independent CI checks and review.
    result["subset_results"]=files["method_subsets"]
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
    args=ap.parse_args()
    out=run(args.surveys,args.sites,args.out_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("WETLAND_METHOD_CHANNEL_LATTICE="+json.dumps({
        "fingerprint":out["fingerprint"],
        "full_site_species":out["full_source_positive_site_species_pairs"],
        "leave_one_out":out["leave_one_method_out"],
        "minimal_full_evidence":out["minimal_full_source_positive_witness_panels"],
        "minimal_sign_preservation":out["minimal_all_27_signs_preserving_panels"],
        "panel_summary":[{
            "subset":x["subset"],
            "native_positives":x["subset_recorded_positive_pairs"],
            "strict_reversals":x["strict_reversals_vs_native_27_contrasts"],
            "complete_site_days":x["site_date_groups_with_every_selected_method_record"]
        }for x in out["subset_results"]]
    },sort_keys=True))
