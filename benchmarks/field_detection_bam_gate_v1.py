"""Strict field-data readiness gate; not an ecological result or occupancy fit."""
from __future__ import annotations
import argparse,csv,datetime,hashlib,json,math
from collections import defaultdict
from pathlib import Path

REQUIRED=("site_id","visit_id","survey_date","detected","effort_minutes",
          "method_id","observer_id","latitude","longitude","A_measure",
          "B_measure","M_measure","A_method","B_method","M_method")

def check(rows):
    failures=[];sites=defaultdict(list);seen=set()
    if not rows:return {"status":"STOP","reasons":["EMPTY"],"rows":0,"sites":0}
    for index,row in enumerate(rows,1):
        missing=[k for k in REQUIRED if k not in row or str(row[k]).strip()==""]
        if missing:
            failures.append(f"row {index}: MISSING {','.join(missing)}")
            continue
        site=row["site_id"].strip();visit=row["visit_id"].strip()
        key=(site,visit)
        if key in seen:failures.append(f"row {index}: DUPLICATE_SITE_VISIT")
        seen.add(key)
        if row["detected"] not in ("0","1"):failures.append(f"row {index}: INVALID_DETECTION")
        try:
            date=datetime.date.fromisoformat(row["survey_date"])
            if date.isoformat()!=row["survey_date"]:raise ValueError
        except ValueError:
            failures.append(f"row {index}: INVALID_DATE");date=None
        for field,lower,upper,strict in (
            ("effort_minutes",0,float("inf"),True),
            ("latitude",-90,90,False),("longitude",-180,180,False),
            ("A_measure",-float("inf"),float("inf"),False),
            ("B_measure",-float("inf"),float("inf"),False),
            ("M_measure",-float("inf"),float("inf"),False)):
            try:
                value=float(row[field])
                if not math.isfinite(value) or value<lower or value>upper or (strict and value<=lower):raise ValueError
            except ValueError:failures.append(f"row {index}: INVALID_{field.upper()}")
        sites[site].append((visit,date))
    if len(sites)<2:failures.append("TOO_FEW_SITES")
    for site,records in sorted(sites.items()):
        if len(set(v for v,_ in records))<2:failures.append(f"NO_REPEATS:{site}")
        dates=[d for _,d in records if d is not None]
        if dates and (max(dates)-min(dates)).days>30:
            failures.append(f"CLOSURE_WINDOW_OVER_30_DAYS:{site}")
    return {"status":"PASS_SCHEMA_ONLY" if not failures else "STOP",
            "reasons":failures,"rows":len(rows),"sites":len(sites),
            "sites_with_repeated_visits":sum(len({v for v,_ in r})>=2 for r in sites.values()),
            "detected_rows":sum(r.get("detected")=="1" for r in rows)}

def read_csv(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames:return []
        return list(reader)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=check(read_csv(a.csv))
    result["source_sha256"]=hashlib.sha256(Path(a.csv).read_bytes()).hexdigest()
    output=Path(a.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"]!="PASS_SCHEMA_ONLY":raise SystemExit(2)

if __name__=="__main__":main()
