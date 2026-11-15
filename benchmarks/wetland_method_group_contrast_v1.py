"""Audit source-observed wetland category contrasts under a method-only filter.

Post-exposure descriptive analysis. Original 2024 site categories are not
randomized treatment arms. No occupancy, causal A/B/M, true absence, method
deployment inference, or new EOG-WF empirical scored endpoint.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA = "93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
METHODS = ("acoustic","visual","dipnet","bottletrap")
CORE = ("acoustic","visual")
CATS = ("intervention","control","artificial")
CONTRASTS = (("intervention","control"),
             ("intervention","artificial"),
             ("artificial","control"))
META = {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        return list(reader),list(reader.fieldnames)


def verify_sha(path,sha,label):
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if digest!=sha:
        raise ValueError(f"{label} source SHA256 mismatch")


def sign(number):
    return (number>0)-(number<0)


def describe(surveys,sites,species):
    """Produce source-verified descriptive prevalence and signed contrasts."""
    if len(set(species))!=9 or not species:
        raise ValueError("expected nine unique source species")
    q1={r["site"]:r["ci"] for r in sites
        if r["site"] not in {"kis-banyato","vadasz-turjan"}}
    if len(q1)!=27 or Counter(q1.values())!={"intervention":13,"control":6,"artificial":8}:
        raise ValueError("original author Q1 roster/category denominator drift")
    if len({s["site"] for s in sites})!=len(sites):
        raise ValueError("duplicate original site category IDs")
    source=[r for r in surveys if r["site"] in q1]
    if len(source)!=351 or {r["site"] for r in source}!=set(q1):
        raise ValueError("source survey original Q1 row counts drift")
    by_day=defaultdict(list)
    by_site=defaultdict(list)
    for row in source:
        site=row["site"]
        dt=date.fromisoformat(row["date"])
        if int(row["doy"])!=dt.timetuple().tm_yday:
            raise ValueError("native calendar date DOY drift")
        if row["surv"]!=f"{site}:{row['method']}:{row['doy']}":
            raise ValueError("source group key drift")
        if row["method"] not in METHODS:
            raise ValueError("unsupported source method")
        for sp in species:
            if int(row[sp])<0:
                raise ValueError("negative native count")
        by_site[site].append(row)
        by_day[(site,row["date"])].append(row)
    if len(by_day)!=117:
        raise ValueError("source site×date count drift")
    core_row_total=0
    by_cat_method_dates=defaultdict(Counter)
    for (site,dt),data in by_day.items():
        cnt=Counter(r["method"] for r in data)
        if cnt["acoustic"]!=1 or cnt["visual"]!=1:
            raise ValueError("native site-date paired core not exactly one row per method")
        core_row_total+=2
        for method in METHODS:
            if cnt[method]>0: by_cat_method_dates[q1[site]][method]+=1
    if core_row_total!=234:
        raise ValueError("paired method core row identity drift")

    site_detail=[]
    positive_sets={}
    method_positive_sets=defaultdict(set)
    for site in sorted(q1):
        src=by_site[site]
        full={sp for sp in species if any(int(row[sp])>0 for row in src)}
        av={sp for sp in species if any(int(row[sp])>0 and row["method"] in CORE for row in src)}
        if not av<=full: raise ValueError("core evidence created a source-negative positive")
        positive_sets[site]=(full,av)
        for sp in species:
            for method in METHODS:
                if any(int(row[sp])>0 and row["method"]==method for row in src):
                    method_positive_sets[(site,sp)].add(method)
        site_detail.append({
            "site":site,"category":q1[site],
            "native_site_date_count":len({r["date"] for r in src}),
            "source_native_row_count":len(src),
            "full_recorded_species_richness":len(full),
            "paired_acoustic_visual_recorded_species_richness":len(av),
            "recorded_species_lost_if_only_paired_core":len(full-av),
            "omitted_native_species_list":";".join(sorted(full-av)),
        })
    full_total=sum(len(v[0]) for v in positive_sets.values())
    av_total=sum(len(v[1]) for v in positive_sets.values())
    if (full_total,av_total)!=(144,104):
        raise ValueError("original Q1 full/core positive source baseline drift")

    summary={}
    category_species={}
    for cat in CATS:
        selected=[row for row in site_detail if row["category"]==cat]
        n=len(selected)
        full=sum(row["full_recorded_species_richness"] for row in selected)
        av=sum(row["paired_acoustic_visual_recorded_species_richness"] for row in selected)
        dates=sum(row["native_site_date_count"] for row in selected)
        if n!=Counter(q1.values())[cat]:
            raise ValueError("category count drift")
        summary[cat]={
            "site_count":n,
            "site_date_groups":dates,
            "native_full_source_positive_site_species":full,
            "paired_core_positive_site_species":av,
            "source_positive_site_species_unseen_in_core":full-av,
            "source_positive_retention_fraction_core_vs_full":av/full,
            "mean_full_recorded_species_richness_per_site":full/n,
            "mean_paired_core_recorded_species_richness_per_site":av/n,
            "mean_recorded_richness_change_core_minus_full":(av-full)/n,
            "site_dates_with_native_method_row":{
                method:by_cat_method_dates[cat][method] for method in METHODS
            },
            "site_dates_without_native_method_row":{
                method:dates-by_cat_method_dates[cat][method] for method in METHODS
            },
        }
        for sp in species:
            full_sp=sum(sp in positive_sets[s][0] for s in q1 if q1[s]==cat)
            av_sp=sum(sp in positive_sets[s][1] for s in q1 if q1[s]==cat)
            category_species[(cat,sp)]={
                "category":cat,"species":sp,"category_site_denominator":n,
                "native_full_positive_site_count":full_sp,
                "paired_core_positive_site_count":av_sp,
                "native_positive_site_count_unseen_in_core":full_sp-av_sp,
                "source_observed_full_positive_site_fraction":full_sp/n,
                "source_observed_paired_core_positive_site_fraction":av_sp/n,
            }

    if [(c,summary[c]["site_count"]) for c in CATS] != [
        ("intervention",13),("control",6),("artificial",8)]:
        raise ValueError("site category model changed")
    if (sum(v["native_full_source_positive_site_species"] for v in summary.values()),
        sum(v["paired_core_positive_site_species"] for v in summary.values()))!=(144,104):
        raise ValueError("category positives do not exhaust native source evidence")
    contrasts=[]
    for a,b in CONTRASTS:
        na,nb=summary[a]["site_count"],summary[b]["site_count"]
        for sp in species:
            a0=category_species[(a,sp)]["native_full_positive_site_count"]
            b0=category_species[(b,sp)]["native_full_positive_site_count"]
            a1=category_species[(a,sp)]["paired_core_positive_site_count"]
            b1=category_species[(b,sp)]["paired_core_positive_site_count"]
            numerator_native=a0*nb-b0*na
            numerator_core=a1*nb-b1*na
            denominator=na*nb
            contrasts.append({
                "comparison":f"{a}_minus_{b}",
                "category_a":a,"category_b":b,
                "species":sp,
                "native_full_difference_fraction":numerator_native/denominator,
                "paired_core_difference_fraction":numerator_core/denominator,
                "difference_shift_core_minus_native_percentage_points":
                    100*(numerator_core-numerator_native)/denominator,
                "native_full_difference_percentage_points":
                    100*numerator_native/denominator,
                "paired_core_difference_percentage_points":
                    100*numerator_core/denominator,
                "native_full_direction":sign(numerator_native),
                "paired_core_direction":sign(numerator_core),
                "strict_direction_reversal":numerator_native*numerator_core<0,
                "ties_in_either_source_representation":
                    numerator_native==0 or numerator_core==0,
            })
    summary_of_reversals={
        "total_species_by_category_contrasts":len(contrasts),
        "strict_nonzero_direction_reversals":sum(x["strict_direction_reversal"] for x in contrasts),
        "nonzero_to_zero_or_zero_to_nonzero":sum(
            x["ties_in_either_source_representation"] and
            x["native_full_direction"]!=x["paired_core_direction"] for x in contrasts
        ),
        "strict_reversals_by_comparison":{
            f"{a}_minus_{b}":sum(x["strict_direction_reversal"] for x in contrasts
                                 if x["category_a"]==a and x["category_b"]==b)
            for a,b in CONTRASTS
        },
        "explicit_strict_reversals":[{
            "comparison":x["comparison"],"species":x["species"],
            "native_percentage_points":x["native_full_difference_percentage_points"],
            "paired_core_percentage_points":x["paired_core_difference_percentage_points"],
            "shift_percentage_points":x["difference_shift_core_minus_native_percentage_points"],
        }for x in contrasts if x["strict_direction_reversal"]],
    }
    return {
        "schema":"eog.wetland_method_group_contrast_v1.result",
        "status":"OBSERVATIONAL_CATEGORY_CONTRAST_SENSITIVE_TO_RECORDED_METHOD_RESTRICTION_NOT_CAUSAL",
        "role":"POST_EXPOSURE_DESCRIPTIVE_SOURCE_METHOD_FILTER_NOT_OCCUPANCY_OR_EFFECT_ESTIMATE",
        "source_q1_rows":len(source),
        "source_site_days":len(by_day),
        "source_original_species":list(species),
        "paired_core_methods":list(CORE),
        "category_summary":summary,
        "species_by_category":[category_species[(cat,sp)] for cat in CATS for sp in species],
        "contrasts":contrasts,
        "direction_reversal_diagnostics":summary_of_reversals,
        "site_rows":site_detail,
        "limits":[
            "Source-recorded positive site fraction is not latent occupancy, ecological absence or treatment response.",
            "The sites were not randomly assigned to treatment categories. Changes in observed category differences are deterministic views of the same sites, not causal method effects.",
            "Same acoustic and visual row presence at every date is not proof of equal method effort, deployment or detection probability.",
            "The paper reports dipnet used in regular surveys, whereas method rows are missing from many archived site×dates. Missing CSV row is not confirmed method nondeployment.",
            "Small group sizes (13/6/8) and taxa-specific detection create unstable descriptive percentage-point differences; no p-values or significance claims.",
            "No original unmarked model fitted, A/B/M estimated, new EOG-WF scored endpoint or PR merge."
        ],
    }


def run(survey_path,site_path,out_dir):
    verify_sha(survey_path,SURVEY_SHA,"survey")
    verify_sha(site_path,SITE_SHA,"site")
    original,cols=read_csv(survey_path)
    sites,_=read_csv(site_path)
    if (len(original),len(sites))!=(381,29):
        raise ValueError("original source rows/sites drifted")
    species=[sp for sp in cols if sp not in META]
    if len(species)!=9:
        raise ValueError("original source species roster changed")
    outcome=describe(original,sites,species)
    folder=Path(out_dir);folder.mkdir(parents=True,exist_ok=True)
    outputs={
        "source_site_richness":outcome.pop("site_rows"),
        "source_species_by_category":outcome.pop("species_by_category"),
        "source_category_species_contrasts":outcome.pop("contrasts"),
    }
    outcome["source_detail_files"]={}
    for name,rows in outputs.items():
        path=folder/f"{name}.csv"
        with path.open("w",encoding="utf-8",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        outcome["source_detail_files"][name]={
            "filename":path.name,"rows":len(rows),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
    outcome["fingerprint"]=hashlib.sha256(json.dumps(
        outcome,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return outcome


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--surveys",type=Path,required=True)
    ap.add_argument("--sites",type=Path,required=True)
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    out=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("WETLAND_METHOD_GROUP_CONTRAST="+json.dumps({
        "fingerprint":out["fingerprint"],
        "category_summary":out["category_summary"],
        "direction_reversals":out["direction_reversal_diagnostics"],
        "detail_files":out["source_detail_files"],
    },sort_keys=True))
