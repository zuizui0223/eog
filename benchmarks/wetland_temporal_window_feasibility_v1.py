"""Temporal-window feasibility from real site×date survey groups, without occupancy.

First/last anchored windows are declared before scoring. The analysis measures
source evidence retained if visits are restricted in calendar time. It DOES
NOT prove short-window closure, independent occasions, absence, or causality.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

SURVEY_SHA="45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA="93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
WINDOWS=(7,14,21,30,45,60,91)
COHORTS={"published_q1":(27,351,117,144),"published_q2":(13,188,64,77)}
META={"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rdr=csv.DictReader(f)
        return list(rdr),list(rdr.fieldnames)


def validate_sha(path,expected,label):
    h=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if h != expected:
        raise ValueError(f"{label} original source SHA mismatch: {h}")


def source_cohort(surveys,sites,cohort):
    if cohort=="published_q1":
        selected={r["site"] for r in sites}-{"kis-banyato","vadasz-turjan"}
    elif cohort=="published_q2":
        selected={r["site"] for r in sites if r["ci"]=="intervention"}
    else: raise ValueError("unrecognized cohort")
    data=[r for r in surveys if r["site"] in selected]
    if {r["site"] for r in data}!=selected:
        raise ValueError("site roster lacks source surveys")
    return data,selected


def reconstruct(records,site_ids,species,cohort,windows=WINDOWS):
    """Compute one fixed set of sensitivity windows; never alter original data."""
    if not records or not site_ids or not species or not windows:
        raise ValueError("empty native source/window universe")
    if (any(type(w)!=int or w<0 for w in windows)
            or tuple(sorted(set(windows)))!=tuple(windows)):
        raise ValueError("windows must be unique nonnegative sorted calendar day lengths")
    by_date=defaultdict(list)
    by_site=defaultdict(set)
    orig_pos=set()
    for row in records:
        site=row["site"]
        if site not in site_ids:
            raise ValueError("foreign source site")
        d=date.fromisoformat(row["date"])
        if d.timetuple().tm_yday!=int(row["doy"]):
            raise ValueError("native date/doy mismatch")
        if row["surv"]!=f"{site}:{row['method']}:{row['doy']}":
            raise ValueError("composite group key changed")
        key=(site,row["date"])
        by_date[key].append(row)
        by_site[site].add(row["date"])
        for sp in species:
            n=int(row[sp])
            if n<0:raise ValueError("negative native species count")
            if n>0:orig_pos.add((site,sp))
    if set(by_site)!=set(site_ids):
        raise ValueError("original source site roster incomplete")
    date_pos={}
    methods={}
    for (site,dt),obs in by_date.items():
        date_pos[(site,dt)]={
            sp for sp in species if any(int(row[sp])>0 for row in obs)
        }
        methods[(site,dt)]={row["method"] for row in obs}
    dates={site:sorted(dts) for site,dts in by_site.items()}
    orig_dates_pos=defaultdict(set)
    for (site,dt),taxa in date_pos.items():
        for sp in taxa:orig_dates_pos[(site,sp)].add(dt)
    if set(orig_dates_pos)!=orig_pos:
        raise ValueError("source-positive records altered by date aggregation")
    summary=[]
    detail=[]
    for window in windows:
        captured={}
        visits={}
        eligible={}
        methods_identical={}
        for anchor in ("first","last"):
            retained=set()
            eligible_sites=set()
            sampled_date_total=0
            per_site={}
            per_site_equal={}
            for site in sorted(site_ids):
                all_dates=dates[site]
                end=date.fromisoformat(all_dates[0] if anchor=="first" else all_dates[-1])
                selected_dates=[
                    d for d in all_dates
                    if abs((date.fromisoformat(d)-end).days)<=window
                ]
                if not selected_dates:
                    raise ValueError("anchored window missing its anchor date")
                sampled_date_total+=len(selected_dates)
                per_site[site]=selected_dates
                if len(selected_dates)>=2:
                    eligible_sites.add(site)
                    per_site_equal[site]=len({
                        frozenset(methods[(site,d)]) for d in selected_dates
                    })==1
                for d in selected_dates:
                    retained.update((site,sp) for sp in date_pos[(site,d)])
            if not retained<=orig_pos:
                raise ValueError("calendar restriction invented positive record")
            captured[anchor]=retained
            visits[anchor]={"site_dates_selected":sampled_date_total,
                            "date_groups_per_site":per_site}
            eligible[anchor]=eligible_sites
            methods_identical[anchor]=per_site_equal
        first,last=captured["first"],captured["last"]
        for anchor in ("first","last"):
            retained=captured[anchor]
            eligible_sites=eligible[anchor]
            relevant={p for p in orig_pos if p[0] in eligible_sites}
            relevant_retained=retained & relevant
            nvisits=[len(v) for v in visits[anchor]["date_groups_per_site"].values()]
            same_sets=methods_identical[anchor]
            by_species={
                sp:{
                    "source_positive_site_count":sum(p[1]==sp for p in orig_pos),
                    "retained_positive_site_count":sum(p[1]==sp for p in retained)
                } for sp in species
            }
            summary.append({
                "cohort":cohort,"window_calendar_days":window,"anchor":anchor,
                "source_sites":len(site_ids),
                "source_recorded_site_dates":len(by_date),
                "source_positive_site_species":len(orig_pos),
                "sites_with_two_or_more_selected_dates":len(eligible_sites),
                "sites_with_fewer_than_two_selected_dates":len(site_ids)-len(eligible_sites),
                "selected_site_dates":visits[anchor]["site_dates_selected"],
                "selected_visits_per_site_min":min(nvisits),
                "selected_visits_per_site_median":statistics.median(nvisits),
                "selected_visits_per_site_max":max(nvisits),
                "source_positive_pairs_retained":len(retained),
                "source_positive_pairs_not_seen_in_window":len(orig_pos-retained),
                "eligible_sites_source_positive_pairs":len(relevant),
                "eligible_sites_positive_pairs_retained":len(relevant_retained),
                "eligible_sites_positive_pairs_not_seen":len(relevant-relevant_retained),
                "eligible_sites_equal_method_sets_across_all_selected_dates":sum(same_sets.values()),
                "eligible_sites_nonidentical_method_sets":len(eligible_sites)-sum(same_sets.values()),
                "positive_only_window_is_subset_of_source":True,
                "by_species":by_species,
            })
        paired_elig=eligible["first"] & eligible["last"]
        for site,sp in sorted(orig_pos):
            detail.append({
                "cohort":cohort,"window_calendar_days":window,
                "site":site,"species":sp,
                "source_positive":1,
                "number_of_distinct_dates_originally_positive":len(orig_dates_pos[(site,sp)]),
                "first_window_recorded_date_count":len(visits["first"]["date_groups_per_site"][site]),
                "last_window_recorded_date_count":len(visits["last"]["date_groups_per_site"][site]),
                "first_window_eligible_two_recorded_dates":int(site in eligible["first"]),
                "last_window_eligible_two_recorded_dates":int(site in eligible["last"]),
                "both_anchors_eligible_two_recorded_dates":int(site in paired_elig),
                "first_window_positive_seen":int((site,sp) in first),
                "last_window_positive_seen":int((site,sp) in last),
                "paired_window_positive_disagreement":int(((site,sp) in first)!=((site,sp) in last)),
            })
        # Store paired comparisons directly adjacent to anchor summaries.
        for row in summary[-2:]:
            row.update({
                "paired_first_vs_last_positive_symmetric_difference":len(first^last),
                "paired_first_only_positive_pairs":len(first-last),
                "paired_last_only_positive_pairs":len(last-first),
                "sites_eligible_under_both_anchor_windows":len(paired_elig),
            })
        if window>=max((date.fromisoformat(dts[-1])-date.fromisoformat(dts[0])).days
                       for dts in dates.values()):
            if first!=orig_pos or last!=orig_pos:
                raise ValueError("full-span window does not reproduce native source evidence")
    return {
        "cohort":cohort,
        "source_site_count":len(site_ids),
        "source_native_date_count":len(by_date),
        "source_positive_site_species":len(orig_pos),
        "source_visit_date_min":min(d for _,d in by_date),
        "source_visit_date_max":max(d for _,d in by_date),
        "site_span_days_min":min((date.fromisoformat(dts[-1])-date.fromisoformat(dts[0])).days
                                 for dts in dates.values()),
        "site_span_days_median":statistics.median(
            (date.fromisoformat(dts[-1])-date.fromisoformat(dts[0])).days for dts in dates.values()
        ),
        "site_span_days_max":max((date.fromisoformat(dts[-1])-date.fromisoformat(dts[0])).days
                                 for dts in dates.values()),
        "window_summaries":summary,
    },detail


def run(survey_path,site_path,out_dir):
    validate_sha(survey_path,SURVEY_SHA,"survey")
    validate_sha(site_path,SITE_SHA,"sites")
    surveys,cols=read_csv(survey_path)
    sites,_=read_csv(site_path)
    if len(surveys)!=381 or len(sites)!=29:
        raise ValueError("native source dimensions changed")
    species=[c for c in cols if c not in META]
    if len(species)!=9:
        raise ValueError("original species roster changed")
    out={
        "schema":"eog.wetland_temporal_window_feasibility_v1.result",
        "status":"ORIGINAL_DATE_WINDOW_REPRESENTATION_SENSITIVITY_NOT_CLOSURE_CERTIFICATE",
        "source_sha256":{"surveys":SURVEY_SHA,"sites":SITE_SHA},
        "windows_days":list(WINDOWS),
        "anchors":["first","last"],
        "source_processing_note":"All native recorded dates retained in archive; restricted windows do not establish biological absence or occupancy model validity.",
        "cohorts":{},
        "detail_outputs":{},
        "historical_R_model_fitted":False,
        "source_row_deduplication_performed":False,
        "ecological_season_closure_verified":False,
        "field_effort_verified":False,
    }
    folder=Path(out_dir)
    folder.mkdir(parents=True,exist_ok=True)
    for cohort,expected in COHORTS.items():
        data,ids=source_cohort(surveys,sites,cohort)
        profile,detail=reconstruct(data,ids,species,cohort)
        if (profile["source_site_count"],len(data),
            profile["source_native_date_count"],profile["source_positive_site_species"])!=expected:
            raise ValueError("author original source cohort profile mismatch")
        path=folder/f"{cohort}_window_source_positive_detail.csv"
        with path.open("w",encoding="utf-8",newline="") as fh:
            writer=csv.DictWriter(fh,fieldnames=list(detail[0]))
            writer.writeheader()
            writer.writerows(detail)
        out["detail_outputs"][cohort]={
            "filename":path.name,"rows":len(detail),
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
        }
        out["cohorts"][cohort]=profile
    out["fingerprint"]=hashlib.sha256(json.dumps(
        out,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",type=Path,required=True)
    p.add_argument("--sites",type=Path,required=True)
    p.add_argument("--out-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=run(args.surveys,args.sites,args.out_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("WETLAND_TEMPORAL_WINDOW_FEASIBILITY="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{
          c:{
            "sites":profile["source_site_count"],
            "original_positives":profile["source_positive_site_species"],
            "horizons":{
              str(w):{
                a:{
                  "eligible_sites":next(s["sites_with_two_or_more_selected_dates"]
                      for s in profile["window_summaries"] if s["window_calendar_days"]==w and s["anchor"]==a),
                  "retained_positive_pairs":next(s["source_positive_pairs_retained"]
                      for s in profile["window_summaries"] if s["window_calendar_days"]==w and s["anchor"]==a),
                  "not_seen_positive_pairs":next(s["source_positive_pairs_not_seen_in_window"]
                      for s in profile["window_summaries"] if s["window_calendar_days"]==w and s["anchor"]==a)
                } for a in ("first","last")
              } for w in (7,14,21,30,91)
            }
          }for c,profile in result["cohorts"].items()
        }
    },sort_keys=True))
