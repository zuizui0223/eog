"""EOG external stage-specific experimental witness audit (predeclared model).

Primary endpoint: paired-station germination fraction protected minus unprotected.
This does NOT identify natural dispersal histories, A/B/M masks, or causal
vertebrate effects from observational absences. No EOG-WF endpoint is added.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

DOI="10.5061/dryad.t1g1jwtg3"
KEY=("species","site","year","microhabitat","station","site_type")
REQUIRED=set(KEY)|{"treatment","germ"}
PAIR_TREATMENTS=("protected","unprotected")
EXPECTED_FILE="sowing_experiment.csv"
TOL=0.025

def outcome(row):
    val=(row.get("germ","") or "").strip()
    if val in ("0","1"):return int(val)
    if val.upper() in ("","NA","NAN"):return None
    raise ValueError("SCHEMA_STOP_UNKNOWN_GERMINATION_CODE:"+val[:40])

def parse_rows(source:Path):
    with source.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not REQUIRED.issubset(set(reader.fieldnames or [])):
            raise ValueError("SCHEMA_STOP_MISSING_HEADERS")
        out=[]
        for row in reader:
            for k in KEY:
                if not str(row[k]).strip():raise ValueError("SCHEMA_STOP_EMPTY_ID:"+k)
            treatment=row["treatment"].strip().lower()
            if treatment not in PAIR_TREATMENTS:
                raise ValueError("SCHEMA_STOP_BAD_TREATMENT:"+treatment)
            st=row["site_type"].strip().lower()
            if st not in ("present","absent"):
                raise ValueError("SCHEMA_STOP_BAD_NATURAL_STATUS:"+st)
            record={k:row[k].strip() for k in KEY}
            record["treatment"]=treatment
            record["site_type"]=st
            record["germ"]=outcome(row)
            out.append(record)
    if not out:raise ValueError("SCHEMA_STOP_NO_SEED_ROWS")
    return out

def station_statistics(records):
    """One row is one sown seed; no seed ever counted as a site replicate."""
    groups=defaultdict(list)
    for r in records:
        key=tuple(r[k] for k in KEY)+(r["treatment"],)
        groups[key].append(r["germ"])
    stats={}
    for key,vs in groups.items():
        n=len(vs);pos=sum(v==1 for v in vs);miss=sum(v is None for v in vs)
        stats[key]={"n":n,"known_positive":pos,"missing":miss,
                    "lower":pos/n,"upper":(pos+miss)/n}
    return stats

def paired_data(stats):
    pair=defaultdict(dict)
    for key,s in stats.items():
        id_=key[:-1];arm=key[-1]
        pair[id_][arm]=s
    complete=[]
    reasons=defaultdict(int)
    for key,arms in pair.items():
        if set(arms)!=set(PAIR_TREATMENTS):
            reasons["unmatched_arm"]+=1
            continue
        a,b=arms["protected"],arms["unprotected"]
        low=a["lower"]-b["upper"];high=a["upper"]-b["lower"]
        if low>high+1e-12:raise ValueError("integrity wrong bounds")
        complete.append({
          "species":key[0],"site":key[1],"year":key[2],
          "microhabitat":key[3],"station":key[4],"site_type":key[5],
          "n_protected":a["n"],"n_unprotected":b["n"],
          "germ_protected":a["known_positive"],"germ_unprotected":b["known_positive"],
          "missing_protected":a["missing"],"missing_unprotected":b["missing"],
          "effect_low":low,"effect_high":high
        })
    return complete,dict(reasons),len(pair)

def classify(low,high):
    if low>TOL:return "positive"
    if high<-TOL:return "negative"
    if low>=-TOL and high<=TOL:return "operational_zero"
    return "unresolved"

def grouped_effects(paired):
    groups=defaultdict(list)
    for r in paired:
        groups[(r["site"],r["species"],r["year"],r["site_type"])].append(r)
    out=[]
    for key,rows in sorted(groups.items()):
        count=len(rows)
        low=sum(r["effect_low"] for r in rows)/count
        high=sum(r["effect_high"] for r in rows)/count
        out.append({
            "site":key[0],"species":key[1],"year":key[2],"site_type":key[3],
            "n_matched_physical_station_pairs":count,
            "germination_protection_diff_lower":low,
            "germination_protection_diff_upper":high,
            "direction":classify(low,high) if count>=3 else "ineligible_too_few_pairs",
            "unprotected_germination_witnesses":sum(r["germ_unprotected"]>0 for r in rows),
            "protected_germination_witnesses":sum(r["germ_protected"]>0 for r in rows),
            "missing_any":any(r["missing_protected"] or r["missing_unprotected"] for r in rows)
        })
    return out

def analyse(records):
    station=station_statistics(records)
    paired,stop_reasons,total=paired_data(station)
    units=grouped_effects(paired)
    eligible=[r for r in units if r["direction"]!="ineligible_too_few_pairs"]
    by_status={}
    for category in ("absent","present"):
        sub=[r for r in eligible if r["site_type"]==category]
        by_status[category]={
            "site_species_year_units":len(sub),
            "geographic_sites":len({r["site"] for r in sub}),
            "different_species":len({r["species"] for r in sub}),
            "sign_counts":{k:sum(r["direction"]==k for r in sub)
                           for k in ("positive","negative","operational_zero","unresolved")},
            "units_with_unprotected_germination_witness":sum(r["unprotected_germination_witnesses"]>0 for r in sub),
            "units_with_protected_germination_witness":sum(r["protected_germination_witnesses"]>0 for r in sub)
        }
    return {
       "schema":"eog.mediterranean_sowing_witness.result.v1",
       "status":"RETROSPECTIVE_EXPERIMENTAL_WITNESS_NOT_A_B_M_CAUSAL_IDENTIFICATION",
       "source_doi":DOI,
       "response_measure":"Paired-station germination fraction, treatment protected minus unprotected",
       "primary_units":"species×site×year; station pairing is within the same species/site/year/microhabitat/station",
       "sign_tolerance":TOL,
       "n_sown_seed_rows":len(records),
       "n_station_treatment_groups":len(station),
       "n_unique_potential_station_pairs":total,
       "n_complete_station_pairs":len(paired),
       "pair_missingness":stop_reasons,
       "n_species_site_year_type_units":len(units),
       "n_geographic_sites":len({r["site"] for r in records}),
       "n_species":len({r["species"] for r in records}),
       "n_positive_germination_seed_rows":sum(r["germ"]==1 for r in records),
       "n_missing_germination_seed_rows":sum(r["germ"] is None for r in records),
       "natural_status_summaries":by_status,
       "unit_results":units,
       "interpretation":"Natural absence with observed germination contradicts strict inability to germinate under sowing; it does not prove a complete abiotic niche, natural dispersal limitation, later establishment, or population persistence.",
       "evidence_limits":[
           "Author source methods and results publicly known; no prospective novelty",
           "Seeds and cross-species units are not independent geographic site replicates",
           "Protection may modify abiotic microclimate in addition to vertebrate exposure",
           "Outcome interval is a deterministic missing-data bound, not a confidence interval",
           "Missing success never establishes impossibility; no EOG-WF fourth endpoint"
       ]
    }

def run(source_dir:Path,output:Path):
    receipt=json.loads((source_dir/"source_gate.json").read_text())
    if receipt.get("status")!="SOURCE_BYTES_VERIFIED_NOT_SCORED":
        return {"status":"SOURCE_STOP_NO_SCORE","reason":receipt.get("status")}
    s=receipt.get("source_files",{}).get(EXPECTED_FILE,{})
    raw=(source_dir/EXPECTED_FILE).read_bytes()
    if s.get("status")!="VERIFIED" or hashlib.sha256(raw).hexdigest()!=s.get("sha256"):
        raise ValueError("SOURCE_STOP_CHANGED_SOWING_BYTES")
    result=analyse(parse_rows(source_dir/EXPECTED_FILE))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=run(a.source_dir,a.output)
    print(json.dumps({k:v for k,v in result.items() if k in
          ("status","n_sown_seed_rows","n_geographic_sites","n_complete_station_pairs",
           "natural_status_summaries","pair_missingness")},indent=2))

if __name__=="__main__":main()
