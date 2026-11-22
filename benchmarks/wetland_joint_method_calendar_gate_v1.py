"""Source-authenticated simultaneous method×calendar-window observation gates.

The Boolean OR of site×species positives over original recorded rows must
NOT be distributed across independent marginal method and calendar gates:
there may be separately verified method/date witnesses on DIFFERENT rows.

Only source-observed positives, not true latent occupancy, species absence,
causal treatment response, EOG process worlds or detection probabilities.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from benchmarks import wetland_method_channel_lattice_v1 as source

HORIZONS = (7,14,21,30,45,60,91)
ANCHORS = ("first","last")
AV = frozenset(("acoustic","visual"))
METHODS = frozenset(source.METHODS)
CLASSES = (
    "joint_survives",
    "method_only_marginal",
    "time_only_marginal",
    "split_witness_interaction",
    "excluded_by_either_gate_alone",
)
EXPECTED_COHORTS={
    "published_q1":(27,351,117,144,104),
    "published_q2":(13,188,64,77,61),
}


def class_of(full_in_window, av_all_dates, av_in_window):
    """Five disjoint source-positive witness classes, no biological absence."""
    if type(full_in_window) is not bool or type(av_all_dates) is not bool or type(av_in_window) is not bool:
        raise ValueError("source-witness flags must be booleans")
    if av_in_window and (not full_in_window or not av_all_dates):
        raise ValueError("joint AV witness cannot exist outside either marginal mask")
    if av_in_window:
        return "joint_survives"
    if full_in_window and not av_all_dates:
        return "method_only_marginal"
    if av_all_dates and not full_in_window:
        return "time_only_marginal"
    if full_in_window and av_all_dates:
        return "split_witness_interaction"
    return "excluded_by_either_gate_alone"


def signed_contrast(positive_pairs, site_groups, sp, group_a, group_b):
    """Observed source-positive site-frequency contrast, never a causal effect."""
    na=sum(x==group_a for x in site_groups.values())
    nb=sum(x==group_b for x in site_groups.values())
    ka=sum((site,sp) in positive_pairs for site,g in site_groups.items() if g==group_a)
    kb=sum((site,sp) in positive_pairs for site,g in site_groups.items() if g==group_b)
    numerator, denominator=source.exact_difference(ka,kb,na,nb)
    return {
        "positive_a":ka,"positive_b":kb,"site_n_a":na,"site_n_b":nb,
        "numerator":numerator,"denominator":denominator,
        "direction":source.sign(numerator),"percentage_points":100*numerator/denominator
    }


def cohort_result(rows, sites, taxa, cohort):
    """Pure 14-window × two-method-panel original native source sensitivity."""
    if not rows or not sites or not taxa:
        raise ValueError("empty original source cohort")
    if len(set(taxa))!=len(taxa):
        raise ValueError("duplicate original taxon names")
    row_ids=set()
    by_site=defaultdict(list)
    for row in rows:
        if row["site"] not in sites:
            raise ValueError("native CSV row not in original selected site cohort")
        method=row["method"]
        if method not in METHODS:
            raise ValueError("unknown original recorded survey method")
        observation_date=date.fromisoformat(row["date"])
        if observation_date.timetuple().tm_yday!=int(row["doy"]):
            raise ValueError("original calendar date/doy mismatch")
        if row["surv"]!=f"{row['site']}:{method}:{row['doy']}":
            raise ValueError("original site:method:doy composite changed")
        if "_original_csv_line" not in row:
            raise ValueError("missing original recorded CSV row provenance")
        line=int(row["_original_csv_line"])
        if line in row_ids:
            raise ValueError("source CSV row reused")
        row_ids.add(line)
        for taxon in taxa:
            if int(row[taxon])<0:
                raise ValueError("negative original count")
        by_site[row["site"]].append(row)
    if set(by_site)!=set(sites):
        raise ValueError("original site cohort missing source rows")
    dates_by_site={
        site:sorted({r["date"] for r in by_site[site]})
        for site in sites
    }
    source_site_dates=sum(map(len,dates_by_site.values()))
    for site,site_rows in by_site.items():
        for d in dates_by_site[site]:
            recorded=[r["method"] for r in site_rows if r["date"]==d]
            counts=Counter(recorded)
            if counts["acoustic"]!=1 or counts["visual"]!=1:
                raise ValueError("one original acoustic plus one visual row per site/date violated")

    witness=defaultdict(list)
    for row in rows:
        for taxon in taxa:
            if int(row[taxon])>0:
                witness[(row["site"],taxon)].append({
                    "date":row["date"],"method":row["method"],
                    "source_line":int(row["_original_csv_line"])
                })
    full_all=set(witness)
    av_all={
        k for k,found in witness.items()
        if any(record["method"] in AV for record in found)
    }
    if not av_all<=full_all:
        raise ValueError("full source-positive witness set does not include AV")
    full_expected=EXPECTED_COHORTS[cohort]
    if (len(sites),len(rows),source_site_dates,len(full_all),len(av_all))!=full_expected:
        raise ValueError("frozen original cohort size or recorded positives drift")

    window_rows=[]
    pair_rows=[]
    contrast_rows=[]
    per_method_window={}
    baseline={}
    if cohort=="published_q1":
        for a,b in source.CONTRASTS:
            for sp in taxa:
                baseline[(a,b,sp)]=signed_contrast(full_all,sites,sp,a,b)

    for anchor in ANCHORS:
        for horizon in HORIZONS:
            window_dates={}
            for site,dates in dates_by_site.items():
                root=date.fromisoformat(dates[0] if anchor=="first" else dates[-1])
                window_dates[site]={
                    d for d in dates if abs((date.fromisoformat(d)-root).days)<=horizon
                }
                if not window_dates[site]:
                    raise ValueError("anchored source window lacks its native date")
            fw=set()
            aw=set()
            classes=Counter()
            present_methods=Counter()
            for (site,sp),records in sorted(witness.items()):
                available_in_window=[
                    x for x in records if x["date"] in window_dates[site]
                ]
                inside_full=bool(available_in_window)
                inside_av=any(x["method"] in AV for x in available_in_window)
                ever_av=(site,sp) in av_all
                klass=class_of(inside_full,ever_av,inside_av)
                classes[klass]+=1
                if inside_full:fw.add((site,sp))
                if inside_av:aw.add((site,sp))
                av_outside=[
                    x for x in records
                    if x["date"] not in window_dates[site] and x["method"] in AV
                ]
                extra_inside=[
                    x for x in available_in_window if x["method"] not in AV
                ]
                if klass=="split_witness_interaction" and (not av_outside or not extra_inside):
                    raise ValueError("cross-time method witness lacks both source row origins")
                for x in available_in_window:
                    present_methods[x["method"]]+=1
                pair_rows.append({
                    "cohort":cohort,"anchor":anchor,"horizon_days":horizon,
                    "site":site,"wetland_category":sites[site],
                    "species":sp,"witness_class":klass,
                    "full_all_period_recorded_positive":1,
                    "AV_all_period_recorded_positive":int(ever_av),
                    "full_window_recorded_positive":int(inside_full),
                    "AV_window_recorded_positive":int(inside_av),
                    "in_window_first_source_positive_date":
                        min((x["date"] for x in available_in_window),default=""),
                    "in_window_source_positive_methods":";".join(
                        m for m in source.METHODS if any(
                            x["method"]==m for x in available_in_window
                        )
                    ),
                    "in_window_original_positive_source_lines":";".join(
                        str(x["source_line"]) for x in available_in_window
                    ),
                    "AV_source_positive_outside_window_dates":";".join(
                        sorted({x["date"] for x in av_outside})
                    ),
                    "AV_source_positive_outside_window_source_lines":";".join(
                        str(x["source_line"]) for x in av_outside
                    ),
                    "additional_method_source_positive_inside_window_dates":";".join(
                        sorted({x["date"] for x in extra_inside})
                    ),
                    "additional_method_source_positive_inside_window_lines":";".join(
                        str(x["source_line"]) for x in extra_inside
                    ),
                    "split_witness_requires_distinct_original_rows":
                        int(klass=="split_witness_interaction")
                })

            if not aw<=fw or not aw<=av_all or not fw<=full_all:
                raise ValueError("method and calendar subset positive masks not nested")
            if sum(classes.values())!=len(full_all):
                raise ValueError("five-class partition does not exhaust native positives")
            if sum(classes[x] for x in CLASSES if x!="joint_survives")!=len(full_all-aw):
                raise ValueError("joint gate losses do not reconcile to original source")
            if classes["joint_survives"]!=len(aw):
                raise ValueError("joint surviving witnesses do not equal recorded AV window positives")
            selected_site_dates=sum(map(len,window_dates.values()))
            # Every native selected date has an acoustic and visual source row,
            # NOT evidence of equal observation time/physical effort.
            category_breakdown={
                cat:{class_name:sum(
                    1 for z in pair_rows[-len(full_all):]
                    if z["wetland_category"]==cat and z["witness_class"]==class_name)
                    for class_name in CLASSES}
                for cat in source.CATS if cat in sites.values()
            }
            window_rows.append({
                "cohort":cohort,"anchor":anchor,"horizon_calendar_days":horizon,
                "original_site_count":len(sites),
                "original_source_site_dates":source_site_dates,
                "site_dates_selected":selected_site_dates,
                "native_full_all_dates_positive_pairs":len(full_all),
                "native_AV_all_dates_positive_pairs":len(av_all),
                "native_full_window_positive_pairs":len(fw),
                "native_AV_window_positive_pairs":len(aw),
                "full_source_positive_lost_by_calendar_gate":len(full_all-fw),
                "full_source_positive_lost_by_method_gate_alone":len(full_all-av_all),
                "full_source_positive_lost_by_joint_gate":len(full_all-aw),
                "AV_loss_relative_to_same_window_all_methods":len(fw-aw),
                "method_time_split_witness_pairs":classes["split_witness_interaction"],
                **{f"class_{klass}":classes[klass] for klass in CLASSES},
                "by_wetland_category":category_breakdown,
                "all_original_date_rows_preserved_in_source":True
            })
            per_method_window[(anchor,horizon)]=(fw,aw)
            if cohort=="published_q1":
                for method_panel,positive in (("full_four",fw),("acoustic_visual",aw)):
                    for a,b in source.CONTRASTS:
                        for sp in taxa:
                            orig=baseline[(a,b,sp)]
                            now=signed_contrast(positive,sites,sp,a,b)
                            full_window=signed_contrast(fw,sites,sp,a,b)
                            num0=orig["numerator"]; num1=now["numerator"]
                            contrast_rows.append({
                                "cohort":cohort,"anchor":anchor,
                                "horizon_calendar_days":horizon,
                                "method_panel":method_panel,
                                "category_a":a,"category_b":b,"species":sp,
                                "category_a_site_denominator":now["site_n_a"],
                                "category_b_site_denominator":now["site_n_b"],
                                "original_full_all_A_positive":orig["positive_a"],
                                "original_full_all_B_positive":orig["positive_b"],
                                "current_method_window_A_positive":now["positive_a"],
                                "current_method_window_B_positive":now["positive_b"],
                                "original_full_all_contrast_pp":orig["percentage_points"],
                                "current_method_window_contrast_pp":now["percentage_points"],
                                "original_full_all_direction":orig["direction"],
                                "current_method_window_direction":now["direction"],
                                "matched_window_full_direction":full_window["direction"],
                                "strict_sign_reversal_from_original_full_all":
                                    int(num0*num1<0),
                                "tie_transition_from_original_full_all":
                                    int((num0==0)!=(num1==0)),
                                "strict_within_window_AV_vs_full_sign_reversal":
                                    int(method_panel=="acoustic_visual" and
                                        full_window["numerator"]*num1<0),
                                "within_window_AV_vs_full_tie_transition":
                                    int(method_panel=="acoustic_visual" and
                                        (full_window["numerator"]==0)!=(num1==0))
                            })

    # Each cumulative window is nested within larger same-anchor windows.
    for anchor in ANCHORS:
        for shorter,longer in zip(HORIZONS[:-1],HORIZONS[1:]):
            af,aa=per_method_window[(anchor,shorter)]
            bf,ba=per_method_window[(anchor,longer)]
            if not af<=bf or not aa<=ba:
                raise ValueError("calendar window support lost positives as horizon expanded")
        all_long,all_av=per_method_window[(anchor,91)]
        if all_long!=full_all or all_av!=av_all:
            raise ValueError("91-day window must reproduce all original positives")
    if len(window_rows)!=len(HORIZONS)*len(ANCHORS):
        raise ValueError("missing fixed calendar/window combinations")
    if len(pair_rows)!=len(full_all)*len(window_rows):
        raise ValueError("per-positive witness/window rows incomplete")
    if cohort=="published_q1" and len(contrast_rows)!=len(window_rows)*2*len(taxa)*len(source.CONTRASTS):
        raise ValueError("Q1 original wetland-category contrast cells incomplete")

    for row in window_rows:
        matching=[x for x in contrast_rows
                  if x["anchor"]==row["anchor"] and
                     x["horizon_calendar_days"]==row["horizon_calendar_days"]]
        if matching:
            full_reversals=sum(x["strict_sign_reversal_from_original_full_all"] for x in matching
                              if x["method_panel"]=="full_four")
            AV_reversals=sum(x["strict_sign_reversal_from_original_full_all"] for x in matching
                            if x["method_panel"]=="acoustic_visual")
            AV_vs_full=sum(x["strict_within_window_AV_vs_full_sign_reversal"] for x in matching)
            row["full_window_strict_reversals_vs_original_27"] = full_reversals
            row["AV_window_strict_reversals_vs_original_27"] = AV_reversals
            row["AV_vs_full_matched_window_strict_reversals"] = AV_vs_full
    return {
        "summary":{
            "source_site_count":len(sites),
            "original_csv_rows":len(rows),
            "source_site_calendar_dates":source_site_dates,
            "original_native_full_positive_pairs":len(full_all),
            "original_native_AV_positive_pairs":len(av_all),
            "anchor_horizon_combinations":len(window_rows),
            "per_source_positive_site_species_window_rows":len(pair_rows),
            "source_date_and_method_subset_nesting_verified":True,
            "source_full_91_day_positive_recovery_exact":True,
            "observed_true_biological_absence_certificates":0
        },
        "windows":window_rows,
        "positive_pair_window_detail":pair_rows,
        "species_group_contrasts":contrast_rows
    }


def run(surveys_path,sites_path,outdir):
    source.sha_guard(surveys_path,source.SURVEY_SHA,"surveys")
    source.sha_guard(sites_path,source.SITE_SHA,"sites")
    surveys,columns=source.read_csv(surveys_path)
    sites,_=source.read_csv(sites_path)
    if len(surveys)!=381 or len(sites)!=29:
        raise ValueError("native archive row or site dimensions changed")
    taxa=[c for c in columns if c not in source.META]
    if len(taxa)!=9 or len(set(taxa))!=9:
        raise ValueError("nine native source species changed")
    # Prior source verifier establishes original Q1 category and 144/104
    # original positive support and the exactly paired recorded AV rows.
    original_q1_sites,_,_=source.validate_source(surveys,sites,taxa)
    full_sites={z["site"]:z["ci"] for z in sites}
    cohorts={
        "published_q1":original_q1_sites,
        "published_q2":{site:cat for site,cat in original_q1_sites.items()
                        if cat=="intervention"}
    }
    indexed=[{**r,"_original_csv_line":str(i)}
             for i,r in enumerate(surveys,2)]
    output=Path(outdir);output.mkdir(parents=True,exist_ok=True)
    result={
        "schema":"eog.wetland_joint_method_calendar_gate_v1.result",
        "status":"SOURCE_PINNED_METHOD_TIME_JOINT_WITNESS_PARTITION_NOT_OCCUPANCY",
        "role":"POST_EXPOSURE_OBSERVATION_RECORD_FACTORIAL_GATES",
        "source_sha256":{"survey":source.SURVEY_SHA,"sites":source.SITE_SHA},
        "anchors":list(ANCHORS),"horizon_days":list(HORIZONS),
        "source_positive_recorded_method_pair":list(sorted(AV)),
        "cohorts":{},"outputs":{},
        "no_biological_absence_inferred":True,
        "no_occupancy_or_causal_model_fitted":True,
        "no_new_EOG_WF_scored_endpoint":True,
        "limitations":[
            "Joint gates use original source method/date recorded positive rows. Split witness means method and window marginal site×species positive labels do not imply a joint positive, not that row-level filters do not commute.",
            "A source-recorded zero does not establish true biological absence, and later source positives do not establish first-day biological presence.",
            "Method pair source-row completeness is not verified equal field effort, p(detection), independent traps, or closure across 91 days.",
            "The native dipnet method row is missing on many original source dates although the study describes dipnet surveying, so an absent row is not verified nondeployment.",
            "Q1 wetland group rates are descriptive records on 27 original non-randomized sites; repeated time windows are not independent ecological tests.",
            "No latent occupancy model, ecological world-count constraint fit, causal restoration effect, A/B/M attribution, fourth EOG-WF endpoint or Draft PR merge."
        ]
    }
    details_by_cohort={}
    for coh,site_groups in cohorts.items():
        scoped=[r for r in indexed if r["site"] in site_groups]
        entry=cohort_result(scoped,site_groups,taxa,coh)
        result["cohorts"][coh]=entry["summary"]
        details_by_cohort[coh]=entry
        for name,rows in (
            ("window_summary",entry["windows"]),
            ("positive_pair_window_detail",entry["positive_pair_window_detail"]),
        ):
            path=output/f"{coh}_{name}.csv"
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]))
                writer.writeheader();writer.writerows(rows)
            result["outputs"][f"{coh}_{name}"]={
                "filename":path.name,"rows":len(rows),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            }
        if coh=="published_q1":
            path=output/"published_q1_category_method_calendar_contrasts.csv"
            rows=entry["species_group_contrasts"]
            with path.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]))
                writer.writeheader();writer.writerows(rows)
            result["outputs"]["published_q1_category_method_calendar_contrasts"]={
                "filename":path.name,"rows":len(rows),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            }
        result["cohorts"][coh]["windows"] = entry["windows"]
    a=details_by_cohort["published_q1"]
    b=details_by_cohort["published_q2"]
    q1={ (r["anchor"],r["horizon_days"],r["site"],r["species"]):r
         for r in a["positive_pair_window_detail"]}
    q2={ (r["anchor"],r["horizon_days"],r["site"],r["species"]):r
         for r in b["positive_pair_window_detail"]}
    if not set(q2)<=set(q1):
        raise ValueError("Q2 source-positive site×species window witnesses not subset Q1")
    for key,v in q2.items():
        if {k:x for k,x in v.items() if k!="cohort"} != {
           k:x for k,x in q1[key].items() if k!="cohort"}:
            raise ValueError("Q2 recorded source witness differs from Q1 on shared site/taxon")
    result["original_intervention_Q2_witnesses_identical_to_Q1_source_subset"]=True
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
    result=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    key=lambda name,anchor,h:next(x for x in result["cohorts"][name]["windows"]
                              if x["anchor"]==anchor and x["horizon_calendar_days"]==h)
    print("WETLAND_JOINT_METHOD_CALENDAR_GATE="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{name:{
            "full_source_positives":v["original_native_full_positive_pairs"],
            "AV_source_positives":v["original_native_AV_positive_pairs"],
            "first14":key(name,"first",14),
            "last14":key(name,"last",14),
            "first30":key(name,"first",30),
            "last30":key(name,"last",30),
            "last91":key(name,"last",91)
        }for name,v in result["cohorts"].items()},
        "outputs":result["outputs"]
    },sort_keys=True))
