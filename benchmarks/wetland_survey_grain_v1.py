"""Source-only native survey grain audit: grouping key is not a row ID.

Check the exact archived CSV identity before profiling the compositional
surv key. A repeated group key does not prove repeated measurements
are errors or independent physical trap sampling units.
"""
import argparse
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from benchmarks import wetland_duplicate_gate_v1 as native

def describe_grain(surveys, columns):
    if not {"surv","site","method","doy"} <= set(columns):
        raise ValueError("source grouping-key columns missing")
    groups=defaultdict(list)
    for ordinal,row in enumerate(surveys,2):
        intended=f"{row['site']}:{row['method']}:{row['doy']}"
        if row["surv"] != intended:
            raise ValueError(f"surv does not match site:method:doy at CSV line {ordinal}")
        groups[row["surv"]].append((ordinal,row))
    repeats=[]
    methods=sorted({r["method"] for r in surveys})
    for key,entries in sorted(groups.items()):
        if len(entries)>1:
            repeats.append({
                "group_key":key,
                "native_rows":len(entries),
                "csv_lines":[n for n,_ in entries],
                "site":entries[0][1]["site"],
                "method":entries[0][1]["method"],
                "date":entries[0][1]["date"],
                "shared_num_field":len({r["num"] for _,r in entries})==1,
            })
    return {
        "native_rows":len(surveys),
        "rows_matching_site_method_doy_composite_key":len(surveys),
        "distinct_composite_occasion_keys":len(groups),
        "repeated_occasion_keys":len(repeats),
        "rows_in_repeated_occasion_keys":sum(r["native_rows"] for r in repeats),
        "by_method":{
            method:{
                "native_rows":sum(r["method"]==method for r in surveys),
                "distinct_occasion_keys":sum(v[0][1]["method"]==method for v in groups.values()),
            } for method in methods
        },
        "repeated_groups":repeats,
        "inference":(
            "surv is a site:method:day-of-year group identifier, not a unique "
            "physical-observation-row key. Multiple bottle-trap rows under "
            "one identifier could reflect distinct traps, corrections, or "
            "recording issues; field sampling metadata are needed."
        ),
    }


def run(surveys_path,sites_path):
    if hashlib.sha256(Path(surveys_path).read_bytes()).hexdigest()!=native.SURVEY_SHA:
        raise ValueError("survey source SHA drift")
    if hashlib.sha256(Path(sites_path).read_bytes()).hexdigest()!=native.SITE_SHA:
        raise ValueError("site source SHA drift")
    surveys,fields=native.load(surveys_path)
    sites,_=native.load(sites_path)
    if len(sites)!=29:
        raise ValueError("source wetland roster drift")
    out={
        "schema":"eog.wetland_survey_composite_key_grain_v1",
        "status":"COMPOSITE_OCCASION_KEY_NOT_PHYSICAL_ROW_ID",
        "role":"POST_EXPOSURE_SOURCE_GRAIN_DIAGNOSTIC",
        "source_sha256":{"surveys":native.SURVEY_SHA,"sites":native.SITE_SHA},
        "profile":describe_grain(surveys,fields),
        "limits":[
            "Repeated group keys are not, by themselves, evidence of duplicate field observations or data corruption.",
            "Original article reports 15–50 bottle traps per site and multiple survey methods per visit, but individual physical trap ID is absent from this CSV.",
            "Do not delete, sum or impute any repeated rows without a field-supported unit rule.",
            "No occupancy likelihood, ecological effect, causal A/B/M or new EOG-WF endpoint.",
        ]
    }
    out["fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    r=run(a.surveys,a.sites)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("WETLAND_SURVEY_GRAIN="+json.dumps({
        "status":r["status"],
        "matches":r["profile"]["rows_matching_site_method_doy_composite_key"],
        "rows":r["profile"]["native_rows"],
        "unique_occasion_keys":r["profile"]["distinct_composite_occasion_keys"],
        "duplicate_group_keys":r["profile"]["repeated_occasion_keys"],
        "by_method":r["profile"]["by_method"],
        "fingerprint":r["fingerprint"],
    },sort_keys=True))
