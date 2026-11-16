"""Chronological source-positive discoveries, never a diagnosis of true first-day absence.

Site×calendar date is the source recording unit. We group all rows on an
original date with Boolean count>0, retain the two repeated bottletrap
group-key rows, and compare first versus strictly later recorded visits.
Later positives do NOT establish first-date false-negative errors, site
colonization, ecological closure or change in true occupancy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from benchmarks import wetland_method_channel_lattice_v1 as source

META=source.META
METHODS=source.METHODS
AV=("acoustic","visual")
HORIZONS=(7,14,21,30,45,60,91)
CATEGORIES=(
    "av_detected_first",
    "same_day_extra_method_only",
    "later_AV_first_discovery",
    "later_additional_only_discovery",
    "never_source_positive",
)
COHORT_EXPECTED={
    "published_q1":(27,351,117,144,104,243),
    "published_q2":(13,188,64,77,61,117),
}
TARGET_SITES=("nyarfas-turjan-laperdo","rachaz_2")
TARGET_TAXA=("Lissotriton vulgaris","Hyla arborea")


def source_row_identity_and_date(row):
    dt=date.fromisoformat(row["date"])
    if int(row["doy"])!=dt.timetuple().tm_yday:
        raise ValueError("source day-of-year mismatch")
    if row["method"] not in METHODS:
        raise ValueError("unexpected original source method")
    if row["surv"]!=f"{row['site']}:{row['method']}:{row['doy']}":
        raise ValueError("source grouping key drift")
    if "_csv_source_line" not in row:
        raise ValueError("missing auditable source CSV line")
    return dt


def reconstruct(scoped_rows, category_by_site, species, cohort):
    """Pure source-record chronology without claims about animal-level state."""
    if not scoped_rows or not category_by_site or not species:
        raise ValueError("empty original source cohort")
    if len(set(species))!=len(species):
        raise ValueError("duplicate species columns")
    by_site_day=defaultdict(list)
    src_ids=set()
    for row in scoped_rows:
        source_row_identity_and_date(row)
        site=row["site"]
        if site not in category_by_site:
            raise ValueError("source row outside original selected site roster")
        n=int(row["_csv_source_line"])
        if n in src_ids:
            raise ValueError("source CSV record used more than once")
        src_ids.add(n)
        by_site_day[(site,row["date"])].append(row)
        for sp in species:
            if int(row[sp])<0:
                raise ValueError("source native negative species count")
    if {s for s,d in by_site_day}!=set(category_by_site):
        raise ValueError("original cohort site roster incomplete")

    dates_by_site={
        site:sorted(d for (ss,d) in by_site_day if ss==site)
        for site in category_by_site
    }
    full_by_day={}
    av_by_day={}
    for (site,d),records in by_site_day.items():
        names=Counter(r["method"] for r in records)
        if names["acoustic"]!=1 or names["visual"]!=1:
            raise ValueError("original complete AV method-pair source status drift")
        full_by_day[(site,d)]={sp for sp in species if any(int(x[sp])>0 for x in records)}
        av_by_day[(site,d)]={sp for sp in species if any(
            x["method"] in AV and int(x[sp])>0 for x in records
        )}
        if not av_by_day[(site,d)]<=full_by_day[(site,d)]:
            raise ValueError("AV positive was not present in full source day")

    detail=[]
    horizon_rows=[]
    per_species={}
    category_counts=Counter()
    per_wetland=defaultdict(Counter)
    later_lags=[]
    for site in sorted(category_by_site):
        dts=dates_by_site[site]
        first=dts[0]
        first_date=date.fromisoformat(first)
        for sp in species:
            days_full=[d for d in dts if sp in full_by_day[(site,d)]]
            days_av=[d for d in dts if sp in av_by_day[(site,d)]]
            detected_ever=bool(days_full)
            av_ever=bool(days_av)
            first_full=sp in full_by_day[(site,first)]
            first_av=sp in av_by_day[(site,first)]
            if first_av and not first_full:
                raise ValueError("AV first-positive lacks native full positive")
            if not detected_ever:
                category="never_source_positive"
            elif first_av:
                category="av_detected_first"
            elif first_full:
                category="same_day_extra_method_only"
            elif av_ever:
                category="later_AV_first_discovery"
            else:
                category="later_additional_only_discovery"
            category_counts[category]+=1
            per_wetland[category_by_site[site]][category]+=1
            first_full_date=days_full[0] if detected_ever else ""
            first_av_date=days_av[0] if av_ever else ""
            lag_full=(date.fromisoformat(first_full_date)-first_date).days if detected_ever else None
            lag_av=(date.fromisoformat(first_av_date)-first_date).days if av_ever else None
            if detected_ever and not first_full:
                if lag_full is None or lag_full<=0:
                    raise ValueError("later discovery must follow earliest recorded date")
                later_lags.append(lag_full)
            native_positive_methods=set()
            for d in dts:
                for record in by_site_day[(site,d)]:
                    if int(record[sp])>0:
                        native_positive_methods.add(record["method"])
            full_first_witness=by_site_day[(site,first_full_date)] if detected_ever else []
            earliest_lines=[
                str(row["_csv_source_line"]) for row in full_first_witness
                if int(row[sp])>0
            ]
            earliest_methods=sorted({
                row["method"] for row in full_first_witness if int(row[sp])>0
            })
            detail.append({
                "cohort":cohort,"site":site,"category":category_by_site[site],
                "species":sp,
                "original_recorded_site_dates":len(dts),
                "first_native_site_date":first,
                "last_native_site_date":dts[-1],
                "original_site_date_calendar_span_days":
                    (date.fromisoformat(dts[-1])-first_date).days,
                "first_date_full_positive":int(first_full),
                "first_date_AV_positive":int(first_av),
                "ever_full_recorded_positive":int(detected_ever),
                "ever_AV_recorded_positive":int(av_ever),
                "full_first_positive_recorded_date":first_full_date,
                "AV_first_positive_recorded_date":first_av_date,
                "full_first_positive_lag_days":"" if lag_full is None else lag_full,
                "AV_first_positive_lag_days":"" if lag_av is None else lag_av,
                "earliest_positive_source_CSV_lines":";".join(earliest_lines),
                "earliest_positive_source_methods":";".join(earliest_methods),
                "all_positive_recorded_methods":";".join(
                    m for m in METHODS if m in native_positive_methods
                ),
                "source_chronology_partition":category,
                "first_full_nonpositive_but_later_full_positive":
                    int(not first_full and detected_ever),
                "first_AV_nonpositive_but_later_AV_positive":
                    int(not first_av and av_ever),
                "first_AV_nonpositive_but_same_date_extra_positive":
                    int(not first_av and first_full),
                "never_full_source_positive_is_UNKNOWN_not_absence":
                    int(not detected_ever)
            })
            for horizon in HORIZONS:
                horizon_rows.append({
                    "cohort":cohort,"site":site,"category":category_by_site[site],
                    "species":sp,"horizon_days_after_first_recorded_date":horizon,
                    "first_full_nonpositive":int(not first_full),
                    "first_AV_nonpositive":int(not first_av),
                    "later_full_positive_witness_by_horizon":
                        int(not first_full and detected_ever and lag_full<=horizon),
                    "later_AV_positive_witness_by_horizon":
                        int(not first_av and av_ever and lag_av<=horizon),
                    "ever_full_source_positive":int(detected_ever),
                    "first_native_site_date":first
                })

    if len(detail)!=len(category_by_site)*len(species):
        raise ValueError("original full site×taxon chronologies not exhaustive")
    if len(horizon_rows)!=len(detail)*len(HORIZONS):
        raise ValueError("seven frozen first-date horizons not exhaustive")
    source_full=sum(z["ever_full_recorded_positive"] for z in detail)
    source_av=sum(z["ever_AV_recorded_positive"] for z in detail)
    first_full=sum(z["first_date_full_positive"] for z in detail)
    first_av=sum(z["first_date_AV_positive"] for z in detail)
    later_full=sum(z["first_full_nonpositive_but_later_full_positive"] for z in detail)
    later_av=sum(z["first_AV_nonpositive_but_later_AV_positive"] for z in detail)
    if (sum(category_counts.values())!=len(detail)
            or (source_full+category_counts["never_source_positive"])!=len(detail)
            or first_full+later_full!=source_full
            or first_av+later_av!=source_av
            or category_counts["av_detected_first"]+category_counts["same_day_extra_method_only"]!=first_full
            or category_counts["later_AV_first_discovery"]+
               category_counts["later_additional_only_discovery"]!=later_full):
        raise ValueError("first-day/late chronological decomposition lost original source evidence")
    full_keys={(z["site"],z["species"]) for z in detail if z["ever_full_recorded_positive"]}
    av_keys={(z["site"],z["species"]) for z in detail if z["ever_AV_recorded_positive"]}
    if not av_keys<=full_keys:
        raise ValueError("AV source-positive keys exceed all original method positives")
    for sp in species:
        selected=[z for z in detail if z["species"]==sp]
        per_species[sp]={
            "sites":len(selected),
            "full_ever_positive_site_count":sum(z["ever_full_recorded_positive"] for z in selected),
            "AV_ever_positive_site_count":sum(z["ever_AV_recorded_positive"] for z in selected),
            "first_full_positive_site_count":sum(z["first_date_full_positive"] for z in selected),
            "first_AV_positive_site_count":sum(z["first_date_AV_positive"] for z in selected),
            "first_full_nonpositive_later_full_positive_count":sum(
                z["first_full_nonpositive_but_later_full_positive"] for z in selected
            ),
            "first_AV_nonpositive_later_AV_positive_count":sum(
                z["first_AV_nonpositive_but_later_AV_positive"] for z in selected
            ),
            "first_AV_nonpositive_same_date_extra_positive_count":sum(
                z["first_AV_nonpositive_but_same_date_extra_positive"] for z in selected
            ),
            "chronology_categories":{
                cat:sum(z["source_chronology_partition"]==cat for z in selected)
                for cat in CATEGORIES
            }
        }
    horizons={}
    for horizon in HORIZONS:
        hrs=[z for z in horizon_rows if z["horizon_days_after_first_recorded_date"]==horizon]
        horizons[str(horizon)]={
            "first_full_nonpositive_later_full_positive_by_horizon":
                sum(z["later_full_positive_witness_by_horizon"] for z in hrs),
            "first_AV_nonpositive_later_AV_positive_by_horizon":
                sum(z["later_AV_positive_witness_by_horizon"] for z in hrs),
            "source_site_species_universe":len(hrs)
        }
    if horizons["91"]["first_full_nonpositive_later_full_positive_by_horizon"]!=later_full:
        raise ValueError("91-day source history does not recover all delayed original positives")
    if horizons["91"]["first_AV_nonpositive_later_AV_positive_by_horizon"]!=later_av:
        raise ValueError("91-day AV history does not recover all delayed original positives")
    for earlier,later in zip(HORIZONS[:-1],HORIZONS[1:]):
        a=horizons[str(earlier)];b=horizons[str(later)]
        if (a["first_full_nonpositive_later_full_positive_by_horizon"]>
            b["first_full_nonpositive_later_full_positive_by_horizon"]
            or a["first_AV_nonpositive_later_AV_positive_by_horizon"]>
            b["first_AV_nonpositive_later_AV_positive_by_horizon"]):
            raise ValueError("source chronological evidence unexpectedly nonmonotone")

    target_rows=[
        {
            **{k:z[k] for k in (
                "cohort","site","category","species","original_recorded_site_dates",
                "first_native_site_date","last_native_site_date","source_chronology_partition",
                "first_date_full_positive","first_date_AV_positive",
                "ever_full_recorded_positive","ever_AV_recorded_positive"
            )},
            "original_source_has_NO_verified_biological_true_absence":True
        }for z in detail
        if z["site"] in TARGET_SITES and z["species"] in TARGET_TAXA
    ]
    if any(z["source_chronology_partition"]!="never_source_positive"
           for z in target_rows):
        raise ValueError("prior candidate negative-witness sites now contain a source positive")
    summary={
        "sites":len(category_by_site),
        "source_native_rows":len(scoped_rows),
        "site_dates":len(by_site_day),
        "site_species_slots":len(detail),
        "source_full_positive_site_species":source_full,
        "source_AV_positive_site_species":source_av,
        "first_full_date_positive_site_species":first_full,
        "first_AV_date_positive_site_species":first_av,
        "first_full_nonpositive_later_full_positive_site_species":later_full,
        "first_AV_nonpositive_later_AV_positive_site_species":later_av,
        "first_AV_nonpositive_same_day_additional_method_positive":
            category_counts["same_day_extra_method_only"],
        "full_source_positive_not_recorded_on_first_full_date_fraction":
            later_full/source_full,
        "chronology_categories":{cat:category_counts[cat] for cat in CATEGORIES},
        "horizon_first_later_positive_counts":horizons,
        "per_species":per_species,
        "per_source_wetland_category":{
            category:{
                "site_count":sum(v==category for v in category_by_site.values()),
                "chronology_categories":{cat:per_wetland[category][cat] for cat in CATEGORIES}
            }for category in ("intervention","control","artificial")
            if category in category_by_site.values()
        },
        "lag_after_first_date_for_later_full_positive":{
            "min":min(later_lags) if later_lags else None,
            "median":statistics.median(later_lags) if later_lags else None,
            "max":max(later_lags) if later_lags else None
        },
        "first_recorded_date_zero_is_NOT_a_true_biological_absence":True,
        "source_chronology_partition_reconciled":True,
        "counterfactual_witness_target_rows":len(target_rows),
        "counterfactual_witness_status_is_unknown_not_absence":True
    }
    return summary,detail,horizon_rows,target_rows


def run(survey_path,site_path,out_dir):
    source.sha_guard(survey_path,source.SURVEY_SHA,"survey")
    source.sha_guard(site_path,source.SITE_SHA,"site")
    surveys,columns=source.read_csv(survey_path)
    sites,_=source.read_csv(site_path)
    if len(surveys)!=381 or len(sites)!=29:
        raise ValueError("original archived source table dimensions drift")
    species=[sp for sp in columns if sp not in META]
    if len(species)!=9:
        raise ValueError("nine original source species roster drift")
    original=[{**row,"_csv_source_line":str(i)}
              for i,row in enumerate(surveys,2)]
    site_class={row["site"]:row["ci"] for row in sites}
    categories={
        "published_q1":{
            k:v for k,v in site_class.items()
            if k not in {"kis-banyato","vadasz-turjan"}
        },
        "published_q2":{
            k:v for k,v in site_class.items() if v=="intervention"
        }
    }
    result={
        "schema":"eog.wetland_chronological_discovery_v1.result",
        "status":"SOURCE_PINNED_FIRST_DATE_LATER_POSITIVE_RECORDS_NOT_BIOLOGICAL_FALSE_NEGATIVES",
        "analysis_role":"POST_EXPOSURE_SOURCE_DATE_METHOD_RECORD_HISTORY",
        "source_sha256":{"surveys":source.SURVEY_SHA,"sites":source.SITE_SHA},
        "date_horizons_days":list(HORIZONS),
        "cohorts":{},
        "outputs":{},
        "inferential_limits":[
            "Later source-recorded positives do not establish species presence on the first date: migration, reproduction phenology, emergence and detection variation are not separable.",
            "A first-date recorded zero is nondetection not biological absence. A site/species never source-positive is unknown rather than certified absence.",
            "AV method row completeness on first dates is not equivalent to equal field effort, method deployment or independent physical survey replicates.",
            "Surv is site×method×DOY grouping key and two bottletrap composite keys repeat; all raw rows are preserved without trap identity inference.",
            "No seasonal closure, actual ecological occupancy, field effect, original unmarked coefficients, A/B/M processes, fourth EOG-WF scored endpoint or PR merge."
        ]
    }
    root=Path(out_dir)
    root.mkdir(parents=True,exist_ok=True)
    evidence={}
    for cohort,selection in categories.items():
        selected=[r for r in original if r["site"] in selection]
        summary,detail,horizons,targets=reconstruct(selected,selection,species,cohort)
        actual=(summary["sites"],summary["source_native_rows"],summary["site_dates"],
                summary["source_full_positive_site_species"],
                summary["source_AV_positive_site_species"],summary["site_species_slots"])
        if actual!=COHORT_EXPECTED[cohort]:
            raise ValueError(f"original source cohort count/positive drift: {cohort}: {actual}")
        if cohort=="published_q1" and len(targets)!=4:
            raise ValueError("expected two native target sites by two source-unconfirmed species")
        if cohort=="published_q2" and len(targets)!=2:
            raise ValueError("Q2 intervention target-site count changed")
        result["cohorts"][cohort]=summary
        evidence[cohort]=(detail,horizons,targets)
        for name,rows in (("site_species_chronology",detail),
                          ("site_species_horizon",horizons),
                          ("candidate_site_species_chronology",targets)):
            path=root/f"{cohort}_{name}.csv"
            with path.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]))
                w.writeheader()
                w.writerows(rows)
            result["outputs"][f"{cohort}_{name}"]={
                "name":path.name,"rows":len(rows),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            }
    q1={r["site"]+"|"+r["species"]:r for r in evidence["published_q1"][0]}
    q2={r["site"]+"|"+r["species"]:r for r in evidence["published_q2"][0]}
    if not set(q2)<=set(q1):
        raise ValueError("original intervention Q2 native site×taxon not nested in Q1")
    for key,row in q2.items():
        if {k:v for k,v in row.items() if k!="cohort"} != {
           k:v for k,v in q1[key].items() if k!="cohort"}:
            raise ValueError("same original Q1/Q2 native visit history differs")
    result["original_Q2_intervention_history_exact_Q1_subset_verified"]=True
    result["fingerprint"]=hashlib.sha256(json.dumps(
        result,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--surveys",required=True,type=Path)
    ap.add_argument("--sites",required=True,type=Path)
    ap.add_argument("--out-dir",required=True,type=Path)
    ap.add_argument("--output",required=True,type=Path)
    a=ap.parse_args()
    result=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WETLAND_CHRONOLOGICAL_DISCOVERY="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{key:{
            "source_positive":v["source_full_positive_site_species"],
            "first_day_full":v["first_full_date_positive_site_species"],
            "later_day_full":v["first_full_nonpositive_later_full_positive_site_species"],
            "first_day_AV":v["first_AV_date_positive_site_species"],
            "later_day_AV":v["first_AV_nonpositive_later_AV_positive_site_species"],
            "five_class_partition":v["chronology_categories"],
            "after_first_horizon_counts":v["horizon_first_later_positive_counts"],
            "target_unknown_rows":v["counterfactual_witness_target_rows"]
        }for key,v in result["cohorts"].items()},
        "outputs":result["outputs"]
    },sort_keys=True))
