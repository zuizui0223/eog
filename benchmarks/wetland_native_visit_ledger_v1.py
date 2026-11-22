"""Reconstruct original wetland survey date/method visit groups without pseudo-replication.

This is a post-exposure source/observation-grain ledger; *not* an occupancy
fit or proof of independent trapping, repeated-visit effort or season closure.
Preserve native source rows and the status of unrecorded methods as UNKNOWN.
"""
import argparse
import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA = "93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
METHODS = ("acoustic", "bottletrap", "dipnet", "visual")
META = {"doy", "surv", "site", "date", "method", "num", "0",
        "year", "month", "temp", "humid", "prec"}
COHORT_EXPECTED = {
    "archived_all": (29, 381, 129, 379, 153, 365),
    "published_q1": (27, 351, 117, 349, 144, 346),
    "published_q2": (13, 188, 64, 186, 77, 207),
}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames)


def check_sha256(path, expected, label):
    value = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if value != expected:
        raise ValueError(f"{label} source SHA drift: {value}")


def src_species(raw_fieldnames):
    if not set(META) <= set(raw_fieldnames):
        raise ValueError("missing original source metadata columns")
    species = [s for s in raw_fieldnames if s not in META]
    if len(species) != 9:
        raise ValueError("expected exactly 9 native species columns")
    return species


def select_cohort(surveys, sites, name):
    source_sites = {r["site"] for r in sites}
    if name == "archived_all":
        site_ids = source_sites
    elif name == "published_q1":
        site_ids = source_sites - {"kis-banyato", "vadasz-turjan"}
    elif name == "published_q2":
        site_ids = {r["site"] for r in sites if r["ci"] == "intervention"}
    else:
        raise ValueError("unrecognized original cohort")
    data = [r for r in surveys if r["site"] in site_ids]
    if set(r["site"] for r in data) != site_ids:
        raise ValueError("source survey/site roster mismatch")
    return data, site_ids


def build_cohort(scoped_rows, site_ids, species, cohort):
    """Build factual 3-state method history; OR is evidence union, not a fitted model."""
    if not scoped_rows or not site_ids:
        raise ValueError("empty source visit roster")
    by_date = defaultdict(list)
    by_method_date = defaultdict(list)
    by_site = defaultdict(list)
    source_positives = set()
    row_indices = set()
    for index, row in enumerate(scoped_rows):
        if row["site"] not in site_ids:
            raise ValueError("source row outside named cohort")
        day = date.fromisoformat(row["date"])
        if int(row["doy"]) != day.timetuple().tm_yday:
            raise ValueError("source day-of-year disagrees with date")
        if row["surv"] != f"{row['site']}:{row['method']}:{row['doy']}":
            raise ValueError("source composite method-day key drift")
        if row["method"] not in METHODS:
            raise ValueError("unexpected source detection method")
        if "_source_csv_line" not in row:
            raise ValueError("source CSV line identity missing")
        lineno = int(row["_source_csv_line"])
        if lineno in row_indices:
            raise ValueError("source CSV row used twice")
        row_indices.add(lineno)
        by_date[(row["site"],row["date"])].append(row)
        by_method_date[(row["site"],row["date"],row["method"])].append(row)
        by_site[row["site"]].append(row)
        for sp in species:
            value = int(row[sp])
            if value < 0:
                raise ValueError("negative native biological count")
            if value > 0:
                source_positives.add((row["site"],sp))
    if set(by_site) != site_ids:
        raise ValueError("not every source site has visit records")

    method_long = []
    day_long = []
    day_positive_site_species = set()
    methods_per_date = Counter()
    positive_date_by_pair = defaultdict(set)
    positive_method_by_pair = defaultdict(set)
    for (site,day),records in sorted(by_date.items()):
        present = {r["method"] for r in records}
        methods_per_date[len(present)] += 1
        for sp in species:
            method_support = 0
            for method in METHODS:
                source_group = by_method_date.get((site,day,method))
                if source_group is None:
                    # This is not a sampled-and-undetected zero.
                    status,detected = "METHOD_NOT_RECORDED", ""
                    n_positive = 0
                    source_lines = ""
                    n_rows = 0
                else:
                    n_positive = sum(int(r[sp]) > 0 for r in source_group)
                    status = ("RECORDED_POSITIVE" if n_positive
                              else "RECORDED_NONDETECTION")
                    detected = "1" if n_positive else "0"
                    source_lines = ";".join(str(r["_source_csv_line"]) for r in source_group)
                    n_rows = len(source_group)
                if n_positive:
                    method_support += 1
                    positive_method_by_pair[(site,sp)].add(method)
                method_long.append({
                    "cohort":cohort,"site":site,"date":day,"method":method,
                    "species":sp,"observation_status":status,"detected":detected,
                    "source_row_count":n_rows,"positive_source_row_count":n_positive,
                    "source_csv_lines":source_lines,
                })
            daily_detected = int(method_support > 0)
            if daily_detected:
                positive_date_by_pair[(site,sp)].add(day)
                day_positive_site_species.add((site,sp))
            day_long.append({
                "cohort":cohort,"site":site,"date":day,"species":sp,
                "recorded_positive":daily_detected,
                "recorded_method_count":len(present),
                "positive_method_count":method_support,
                "native_rows_on_visit_date":len(records)
            })
    if day_positive_site_species != source_positives:
        raise ValueError("date aggregation dropped or created site species positive evidence")
    if len(method_long) != len(by_date)*len(METHODS)*len(species):
        raise ValueError("not every method status retained per date")
    if len(day_long) != len(by_date)*len(species):
        raise ValueError("not every date×species represented")

    visit_dates_by_site = {
        site:sorted({row["date"] for row in rows})
        for site,rows in by_site.items()
    }
    spans = {site:(date.fromisoformat(days[-1])-date.fromisoformat(days[0])).days
             for site,days in visit_dates_by_site.items()}
    positive_one_date = sum(len(positive_date_by_pair[k])==1 for k in source_positives)
    positive_one_method = sum(len(positive_method_by_pair[k])==1 for k in source_positives)
    all_dates = sorted(day for _,day in by_date)
    method_day_counts = Counter(k[2] for k in by_method_date)
    method_rows = Counter(r["method"] for r in scoped_rows)
    per_species = {}
    for sp in species:
        keys = sorted(k for k in source_positives if k[1]==sp)
        per_species[sp] = {
            "native_positive_site_count":len(keys),
            "positive_at_exactly_one_recorded_date":sum(
                len(positive_date_by_pair[k])==1 for k in keys
            ),
            "positive_in_exactly_one_recorded_method":sum(
                len(positive_method_by_pair[k])==1 for k in keys
            ),
        }
    repeated_groups = [
        {"site":site,"date":day,"method":method,
         "source_csv_lines":[int(r["_source_csv_line"]) for r in records],
         "source_row_count":len(records)}
        for (site,day,method),records in sorted(by_method_date.items())
        if len(records)>1
    ]
    status_counts = Counter(r["observation_status"] for r in method_long)
    observed_method_days = len(by_method_date)
    if (status_counts["RECORDED_POSITIVE"]+status_counts["RECORDED_NONDETECTION"]
            != observed_method_days*len(species)):
        raise ValueError("method-day source coverage and observed statuses disagree")
    if status_counts["METHOD_NOT_RECORDED"] != (
            len(by_date)*len(METHODS)-observed_method_days)*len(species):
        raise ValueError("unrecorded method treated as observed zero")

    profile = {
        "native_csv_rows":len(scoped_rows),
        "sites":len(site_ids),
        "distinct_site_dates":len(by_date),
        "distinct_site_date_methods":len(by_method_date),
        "recorded_positive_site_species_pairs":len(source_positives),
        "positive_site_date_species_records":sum(int(r["recorded_positive"]) for r in day_long),
        "daily_union_preserves_every_native_site_species_positive":True,
        "unique_actual_calendar_days_across_cohort":len(set(all_dates)),
        "global_observation_date_first":all_dates[0],
        "global_observation_date_last":all_dates[-1],
        "recorded_visit_dates_per_site":{
            "min":min(map(len,visit_dates_by_site.values())),
            "median":statistics.median(map(len,visit_dates_by_site.values())),
            "max":max(map(len,visit_dates_by_site.values())),
        },
        "within_site_calendar_span_days":{
            "min":min(spans.values()),
            "median":statistics.median(spans.values()),
            "max":max(spans.values()),
            "sites_spanning_at_least_30_calendar_days":sum(x>=30 for x in spans.values()),
            "sites_spanning_at_least_60_calendar_days":sum(x>=60 for x in spans.values()),
        },
        "site_date_method_count_histogram":{
            str(k):methods_per_date.get(k,0) for k in range(1,len(METHODS)+1)
        },
        "native_site_species_positive_at_single_recorded_date":positive_one_date,
        "native_site_species_positive_in_single_recorded_method":positive_one_method,
        "source_method_rows":dict(sorted(method_rows.items())),
        "source_distinct_method_date_groups":dict(sorted(method_day_counts.items())),
        "duplicated_group_keys_not_resolved":repeated_groups,
        "source_method_species_status_cell_counts":dict(sorted(status_counts.items())),
        "per_species":per_species,
        "per_site":{
            site:{
                "recorded_visit_dates":days,
                "distinct_recorded_visit_count":len(days),
                "calendar_span_days":spans[site],
                "native_source_row_count":len(by_site[site]),
            } for site,days in sorted(visit_dates_by_site.items())
        },
    }
    return profile,method_long,day_long


def make_padded_site_visit_history(profile, day_long, species, cohort):
    """Pad only absent *actual site visit dates* with NA, never fabricated zeros.

    Visit index is ordinal *within site*, not a shared calendar-time index or
    an assertion of independent/closed-season occupancy sampling units.
    """
    site_days={
        site:info["recorded_visit_dates"]
        for site,info in profile["per_site"].items()
    }
    if not site_days:
        raise ValueError("empty visit roster")
    maximum=max(len(dates) for dates in site_days.values())
    observed={}
    for row in day_long:
        key=(row["site"],row["date"],row["species"])
        if key in observed or row["recorded_positive"] not in (0,1):
            raise ValueError("duplicate or nonbinary observed daily evidence")
        observed[key]=row["recorded_positive"]
    output=[]
    reconstructed_positive=set()
    observed_day_cells=0
    for site,dates in sorted(site_days.items()):
        for j in range(maximum):
            available=j<len(dates)
            current_date=dates[j] if available else ""
            for sp in species:
                if available:
                    key=(site,current_date,sp)
                    if key not in observed:
                        raise ValueError("recorded native date not in day evidence")
                    result=int(observed[key])
                    detected=str(result)
                    if result:
                        reconstructed_positive.add((site,sp))
                    status="RECORDED_VISIT_DATE"
                    observed_day_cells+=1
                else:
                    detected=""
                    status="NO_VISIT_RECORDED"
                output.append({
                    "cohort":cohort,
                    "site":site,
                    "within_site_visit_ordinal":j+1,
                    "recorded_date":current_date,
                    "species":sp,
                    "recorded_detection":detected,
                    "visit_status":status,
                })
    if observed_day_cells!=len(day_long):
        raise ValueError("native day evidence not exactly represented")
    if len(output)!=len(site_days)*maximum*len(species):
        raise ValueError("padded visit history shape differs")
    if len(reconstructed_positive)!=profile["recorded_positive_site_species_pairs"]:
        raise ValueError("padded visit history lost native positive site-species")
    missing=sum(x["visit_status"]=="NO_VISIT_RECORDED" for x in output)
    return output,{
        "within_site_max_recorded_visit_dates":maximum,
        "padded_site_visit_species_cells":len(output),
        "recorded_site_visit_species_cells":observed_day_cells,
        "nonexistent_visit_cells_preserved_as_NA":missing,
        "site_species_positive_union_preserved":True,
        "ordinal_is_within_site_not_common_calendar":True,
    }


def run(survey_path,site_path,output_dir):
    for label,path,sha in (("survey",survey_path,SURVEY_SHA),
                           ("site",site_path,SITE_SHA)):
        check_sha256(path,sha,label)
    surveys,columns = read_csv(survey_path)
    sites,_ = read_csv(site_path)
    if (len(surveys),len(sites))!=(381,29):
        raise ValueError("original native table size drift")
    species = src_species(columns)
    original = [{**r, "_source_csv_line":n} for n,r in enumerate(surveys,2)]
    out={
        "schema":"eog.wetland_native_visit_ledger_v1.result",
        "status":"ORIGINAL_VISIT_DATE_AND_METHOD_GRAIN_RECONSTRUCTED_NOT_OCCUPANCY",
        "scientific_role":"POST_EXPOSURE_SOURCE_GRAIN_OBSERVATION_LEDGER",
        "source_sha256":{"survey":SURVEY_SHA,"site":SITE_SHA},
        "cohorts":{},
        "outputs":{},
        "limits":[
            "Site×calendar date is an observed group, not a validated statistically independent occupancy occasion.",
            "Recorded no-detection is not a confirmed biological absence.",
            "Methods not recorded for a site×date are NA, not zero.",
            "Original two same-key bottletrap groups are not deduplicated or presumed independent physical traps.",
            "Effort and within-breeding-season closure cannot be certified from the native fields.",
            "No occupancy, authors' model coefficient, causal A/B/M, inferred movement, or fourth EOG-WF endpoint."
        ],
    }
    folder=Path(output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    for cohort in COHORT_EXPECTED:
        data,site_ids=select_cohort(original,sites,cohort)
        profile,method_long,day_long=build_cohort(data,site_ids,species,cohort)
        padded_long,padded_summary=make_padded_site_visit_history(profile,day_long,species,cohort)
        profile["padded_date_history"]=padded_summary
        counts=(profile["sites"],profile["native_csv_rows"],
                profile["distinct_site_dates"],profile["distinct_site_date_methods"],
                profile["recorded_positive_site_species_pairs"],
                profile["positive_site_date_species_records"])
        if counts != COHORT_EXPECTED[cohort]:
            raise ValueError(f"source cohort fingerprint drift: {cohort} {counts}")
        for suffix,values in (("method_status",method_long),("daily_detected",day_long),("padded_history",padded_long)):
            path=folder/f"{cohort}_{suffix}.csv"
            with path.open("w",encoding="utf-8",newline="") as fh:
                w=csv.DictWriter(fh,fieldnames=list(values[0]))
                w.writeheader()
                w.writerows(values)
            out["outputs"][f"{cohort}_{suffix}"]={
                "name":path.name,"row_count":len(values),
                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()
            }
        out["cohorts"][cohort]=profile
    if not set(out["cohorts"]["published_q2"]["per_site"]) <= set(
            out["cohorts"]["published_q1"]["per_site"]):
        raise ValueError("published Q2 site roster not nested in Q1")
    out["fingerprint"]=hashlib.sha256(json.dumps(
        out,sort_keys=True,separators=(",",":")
    ).encode()).hexdigest()
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--out-dir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    result=run(args.surveys,args.sites,args.out_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WETLAND_NATIVE_VISIT_LEDGER="+json.dumps({
        "fingerprint":result["fingerprint"],
        "cohorts":{name:{
            "sites":c["sites"],"native_rows":c["native_csv_rows"],
            "site_dates":c["distinct_site_dates"],
            "method_days":c["distinct_site_date_methods"],
            "source_positive":c["recorded_positive_site_species_pairs"],
            "single_date_positives":c["native_site_species_positive_at_single_recorded_date"],
            "max_site_span":c["within_site_calendar_span_days"]["max"],
            "method_missing_status_cells":c["source_method_species_status_cell_counts"]["METHOD_NOT_RECORDED"],
            "no_visit_NA_cells":c["padded_date_history"]["nonexistent_visit_cells_preserved_as_NA"]
        } for name,c in result["cohorts"].items()}
    },sort_keys=True))
