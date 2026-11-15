"""Complete recorded acoustic+visual daily core: source-based evidence audit.

This is a post-exposure *observed-data* representation diagnostic. A source
method row is not proof of constant effort; no row does not prove the method
was never deployed. Missing a positive under the paired core is not an
observed biological absence. No occupancy or EOG-WF fitting.
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
META = {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
CORE = ("acoustic","visual")
ADDITIONAL = ("bottletrap","dipnet")
METHODS = CORE + ADDITIONAL
COHORT_EXPECTED = {
    "archived_all":(29,381,129,153,110,365,249),
    "published_q1":(27,351,117,144,104,346,234),
    "published_q2":(13,188,64,77,61,207,148),
}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader), list(reader.fieldnames)


def validate_sha(path, expected, label):
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError(f"{label}: raw source SHA256 drift")


def choose(rows, site_rows, name):
    if name=="archived_all":
        ids={r["site"] for r in site_rows}
    elif name=="published_q1":
        ids={r["site"] for r in site_rows}-{"kis-banyato","vadasz-turjan"}
    elif name=="published_q2":
        ids={r["site"] for r in site_rows if r["ci"]=="intervention"}
    else:
        raise ValueError("unknown original published cohort")
    scoped=[r for r in rows if r["site"] in ids]
    if {r["site"] for r in scoped}!=ids:
        raise ValueError("native site roster incomplete")
    return scoped,ids


def profile(cohort, rows, site_ids, species):
    """Check complete paired-method recorded row coverage and source evidence."""
    if not rows or not site_ids or not species:
        raise ValueError("source cohort empty")
    by_day=defaultdict(list)
    source_lines=set()
    full_site_positive=set()
    for r in rows:
        site=r["site"]
        if site not in site_ids:
            raise ValueError("native row outside selected original cohort")
        dt=date.fromisoformat(r["date"])
        if dt.timetuple().tm_yday!=int(r["doy"]):
            raise ValueError("calendar DOY drift")
        if r["surv"]!=f"{site}:{r['method']}:{r['doy']}":
            raise ValueError("site-method-date grouping-key drift")
        if r["method"] not in METHODS:
            raise ValueError("unsupported native recorded method")
        if "_source_csv_line" not in r:
            raise ValueError("source line identity missing")
        lineno=int(r["_source_csv_line"])
        if lineno in source_lines:
            raise ValueError("native input source row counted twice")
        source_lines.add(lineno)
        by_day[(site,r["date"])].append(r)
        for sp in species:
            if int(r[sp])<0:
                raise ValueError("negative recorded native count")
            if int(r[sp])>0:
                full_site_positive.add((site,sp))
    if {s for s,_ in by_day} != set(site_ids):
        raise ValueError("source date groups not aligned with site roster")

    daily=[]
    per_pair=defaultdict(lambda:{
        "full":False,"core":False,"acoustic":False,"visual":False,
        "dipnet":False,"bottletrap":False,"noncore":False,
        "core_positive_dates":0,"full_positive_dates":0,
    })
    methods_seen=Counter()
    raw_rows_by_method=Counter(r["method"] for r in rows)
    core_rows_used=[]
    core_daily_positive=set()
    all_daily_positive=set()
    method_missing_by_day=Counter()

    for (site,day),visit in sorted(by_day.items()):
        groups=defaultdict(list)
        for r in visit:
            groups[r["method"]].append(r)
        for m in CORE:
            if len(groups[m])!=1:
                raise ValueError(f"paired {m} method not exactly once for {site} {day}")
        core_rows_used.extend(groups["acoustic"]+groups["visual"])
        for m in METHODS:
            if groups[m]:
                methods_seen[m]+=1
            else:
                method_missing_by_day[m]+=1
        for sp in species:
            ac=int(groups["acoustic"][0][sp])
            vi=int(groups["visual"][0][sp])
            dip=int(any(int(r[sp])>0 for r in groups["dipnet"]))
            bottle=int(any(int(r[sp])>0 for r in groups["bottletrap"]))
            ac_pos=ac>0
            vi_pos=vi>0
            core=ac_pos or vi_pos
            noncore=bool(dip or bottle)
            all_pos=core or noncore
            if all_pos:
                all_daily_positive.add((site,day,sp))
            if core:
                core_daily_positive.add((site,day,sp))
            p=per_pair[(site,sp)]
            p["full"]|=all_pos
            p["core"]|=core
            p["acoustic"]|=ac_pos
            p["visual"]|=vi_pos
            p["dipnet"]|=bool(dip)
            p["bottletrap"]|=bool(bottle)
            p["noncore"]|=noncore
            p["core_positive_dates"]+=int(core)
            p["full_positive_dates"]+=int(all_pos)
            daily.append({
                "cohort":cohort,"site":site,"date":day,"species":sp,
                "acoustic_source_line":groups["acoustic"][0]["_source_csv_line"],
                "visual_source_line":groups["visual"][0]["_source_csv_line"],
                "acoustic_count":ac,"visual_count":vi,
                "acoustic_positive":int(ac_pos),"visual_positive":int(vi_pos),
                "paired_core_positive":int(core),
                "dipnet_row_represented_in_csv":int(bool(groups["dipnet"])),
                "bottletrap_row_represented_in_csv":int(bool(groups["bottletrap"])),
                "dipnet_positive_if_csv_row":dip,
                "bottletrap_positive_if_csv_row":bottle,
                "full_source_positive":int(all_pos),
                "positive_exclusive_to_additional_methods_on_day":int(noncore and not core),
            })

    if {key for key,val in per_pair.items() if val["full"]}!=full_site_positive:
        raise ValueError("paired-method full-source OR reconciliation failed")
    core_site_pos={p for p,v in per_pair.items() if v["core"]}
    if not core_site_pos<=full_site_positive:
        raise ValueError("paired method introduced unsupported native positivity")
    aquatic_site_pos={p for p,v in per_pair.items() if v["noncore"]}
    if (core_site_pos|aquatic_site_pos)!=full_site_positive:
        raise ValueError("recorded source four-method positivity union violated")

    per_species={}
    for sp in species:
        f={x for x in full_site_positive if x[1]==sp}
        c=f&core_site_pos
        noncore=f&aquatic_site_pos
        per_species[sp]={
            "native_full_positive_sites":len(f),
            "paired_core_positive_sites":len(c),
            "positive_sites_undetected_by_paired_core":len(f-c),
            "paired_core_capture_fraction_of_native_positive_sites":len(c)/len(f) if f else None,
            "additional_method_positive_sites":len(noncore),
            "exclusively_additional_method_positive_sites":len(f-c),
            "acoustic_positive_sites":sum(per_pair[k]["acoustic"] for k in f),
            "visual_positive_sites":sum(per_pair[k]["visual"] for k in f),
            "dipnet_positive_sites":sum(per_pair[k]["dipnet"] for k in f),
            "bottletrap_positive_sites":sum(per_pair[k]["bottletrap"] for k in f),
        }
    source_pairs=[]
    for (site,sp) in sorted(full_site_positive):
        v=per_pair[(site,sp)]
        source_pairs.append({
            "cohort":cohort,"site":site,"species":sp,
            "original_source_positive":1,
            "paired_acoustic_visual_positive":int(v["core"]),
            "only_additional_methods_detect_positive":int(not v["core"]),
            "acoustic_any_date_positive":int(v["acoustic"]),
            "visual_any_date_positive":int(v["visual"]),
            "dipnet_any_date_positive":int(v["dipnet"]),
            "bottletrap_any_date_positive":int(v["bottletrap"]),
            "core_positive_recorded_dates":v["core_positive_dates"],
            "full_positive_recorded_dates":v["full_positive_dates"],
        })

    result={
        "source_sites":len(site_ids),
        "source_native_rows":len(rows),
        "source_site_dates":len(by_day),
        "paired_recorded_core_methods":list(CORE),
        "paired_method_native_rows":len(core_rows_used),
        "paired_method_dates_with_exactly_one_row_each":len(by_day),
        "all_site_dates_have_paired_acoustic_visual_record":True,
        "native_positive_site_species":len(full_site_positive),
        "paired_core_positive_site_species":len(core_site_pos),
        "native_positive_site_species_unseen_by_paired_core":len(full_site_positive-core_site_pos),
        "paired_core_capture_fraction":len(core_site_pos)/len(full_site_positive),
        "daily_full_method_positive_site_date_species":len(all_daily_positive),
        "daily_paired_core_positive_site_date_species":len(core_daily_positive),
        "daily_source_positive_unseen_by_paired_core":len(all_daily_positive-core_daily_positive),
        "native_recorded_method_rows":dict(sorted(raw_rows_by_method.items())),
        "site_date_groups_with_method_row":dict(sorted(methods_seen.items())),
        "site_date_groups_without_method_row":dict(sorted(method_missing_by_day.items())),
        "method_row_absence_is_not_field_method_absence":True,
        "two_core_methods_same_recorded_coverage_not_equal_effort":True,
        "per_species":per_species,
        "per_pair_source_registry_preserves_all_native_positives":len(source_pairs)==len(full_site_positive),
    }
    return result,daily,source_pairs


def run(survey_path, site_path, out_dir):
    validate_sha(survey_path,SURVEY_SHA,"survey")
    validate_sha(site_path,SITE_SHA,"sites")
    surveys,cols=read_csv(survey_path)
    sites,_=read_csv(site_path)
    if (len(surveys),len(sites))!=(381,29):
        raise ValueError("original source table dimensions changed")
    species=[x for x in cols if x not in META]
    if len(species)!=9:
        raise ValueError("native species roster changed")
    source=[{**r,"_source_csv_line":i} for i,r in enumerate(surveys,2)]
    results={
        "schema":"eog.wetland_paired_method_core_v1.result",
        "status":"COMPLETE_RECORDED_PAIRED_METHOD_COVERAGE_WITH_TAXON_BIASED_POSITIVE_LOSS",
        "scope":"POST_EXPOSURE_SOURCE_METHOD_REPRESENTATION_NOT_ECOLOGICAL_OCCUPANCY",
        "source_sha256":{"surveys":SURVEY_SHA,"sites":SITE_SHA},
        "historical_R_occupancy_model_fitted":False,
        "equal_field_effort_verified":False,
        "recorded_method_not_present_equals_not_deployed":False,
        "cohorts":{},"output_files":{},
        "limits":[
            "Acoustic and visual one row each per site-date proves source-recording completeness, not equal effort.",
            "The original paper states dipnet used in every regular field session, yet many dipnet method rows are not represented in the CSV.",
            "A paired-core zero is source-recorded nondetection by two methods, not ecological absence.",
            "Paired core omits some aquatic-method-only recorded positive evidence disproportionately across taxa.",
            "No 20-row sampling, no physical trap effort, closure, occupancy likelihood, treatment effect, biotic B, movement M, or fourth EOG-WF endpoint.",
        ],
    }
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    for cohort, expected in COHORT_EXPECTED.items():
        sub,ids=choose(source,sites,cohort)
        pr,daily,pairs=profile(cohort,sub,ids,species)
        measured=(pr["source_sites"],pr["source_native_rows"],pr["source_site_dates"],
                  pr["native_positive_site_species"],pr["paired_core_positive_site_species"],
                  pr["daily_full_method_positive_site_date_species"],
                  pr["daily_paired_core_positive_site_date_species"])
        if measured!=expected:
            raise ValueError(f"frozen source profile drift for {cohort}: {measured}")
        for suffix,rows in (("site_date_species",daily),("site_species_positive_registry",pairs)):
            path=out_dir/f"{cohort}_paired_core_{suffix}.csv"
            with path.open("w",encoding="utf-8",newline="") as fh:
                writer=csv.DictWriter(fh,fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            results["output_files"][f"{cohort}_{suffix}"]={
                "name":path.name,
                "rows":len(rows),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        results["cohorts"][cohort]=pr
    results["fingerprint"]=hashlib.sha256(json.dumps(results,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return results


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--out-dir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=run(a.surveys,a.sites,a.out_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("WETLAND_PAIRED_METHOD_CORE="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{name:{
            "site_dates":z["source_site_dates"],
            "paired_days":z["paired_method_dates_with_exactly_one_row_each"],
            "full_positive_pairs":z["native_positive_site_species"],
            "paired_core_positive_pairs":z["paired_core_positive_site_species"],
            "core_omitted_pairs":z["native_positive_site_species_unseen_by_paired_core"],
            "full_daily_positives":z["daily_full_method_positive_site_date_species"],
            "core_daily_positives":z["daily_paired_core_positive_site_date_species"],
            "dipnet_csv_days":z["site_date_groups_with_method_row"]["dipnet"]
        }for name,z in result["cohorts"].items()}
    },sort_keys=True))
