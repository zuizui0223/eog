"""Qualify NEON native small-mammal sampling files, fail closed.

Requires downloaded NEON mam_perplotnight and mam_pertrapnight tables.
Does not infer occupancy or biological A/B/M from missing captures.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

def load(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f)
        if not r.fieldnames:raise ValueError("empty CSV header")
        return r.fieldnames,list(r)

def check(plot_file,trap_file):
    plotcols,plots=load(plot_file)
    trapcols,traps=load(trap_file)
    required_plot=("nightuid","eventID","namedLocation","collectDate")
    required_trap=("nightuid","trapCoordinate","trapStatus")
    errors=[]
    for table,cols,required in (("plot",plotcols,required_plot),("trap",trapcols,required_trap)):
        missing=[x for x in required if x not in cols]
        if missing:errors.append(f"{table}:missing_columns:{','.join(missing)}")
    if errors:return {"status":"STOP","errors":errors}
    pkeys=Counter(r["nightuid"] for r in plots)
    if any(not k for k in pkeys):errors.append("plot:empty_nightuid")
    if any(v!=1 for v in pkeys.values()):errors.append("plot:duplicate_nightuid")
    unmatched=sum(r["nightuid"] not in pkeys for r in traps)
    if unmatched:errors.append(f"trap:unmatched_nightuid:{unmatched}")
    # Only source evidence for repeat effort. Do not synthesize
    # nondetections from missing trap rows.
    per_trap=defaultdict(set)
    per_bout=defaultdict(set)
    for r in traps:
        uid=r["nightuid"]
        if uid not in pkeys or pkeys[uid]!=1:continue
        p=next((x for x in plots if x["nightuid"]==uid),None)
        if p is None:continue
        key=(p["namedLocation"],p["eventID"],r["trapCoordinate"])
        per_trap[key].add(p["collectDate"])
        per_bout[(p["namedLocation"],p["eventID"])].add(p["collectDate"])
    repeated=sum(len(v)>=2 for v in per_trap.values())
    if repeated==0:errors.append("no_repeated_trap_nights")
    if not plots or not traps:errors.append("empty_tables")
    result={
      "status":"STOP" if errors else "PASS_SOURCE_STRUCTURE_ONLY",
      "errors":errors,"plot_night_rows":len(plots),
      "trap_night_rows":len(traps),"unique_plot_nights":len(pkeys),
      "unmatched_trap_nights":unmatched,
      "trap_bout_keys":len(per_trap),"repeated_trap_bout_keys":repeated,
      "multi_night_bouts":sum(len(v)>=2 for v in per_bout.values()),
      "plot_sha256":hashlib.sha256(Path(plot_file).read_bytes()).hexdigest(),
      "trap_sha256":hashlib.sha256(Path(trap_file).read_bytes()).hexdigest(),
      "caveats":[
        "This gate does not classify capture vs non-capture trapStatus codes.",
        "Missing trap records are not valid nondetection rows.",
        "Check samplingImpractical, deployment and duplicate capture records separately.",
        "No independent abiotic/biotic/movement measures are established.",
        "Plot coordinates cannot be treated as exact trap coordinates.",
      ]
    }
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--perplotnight",required=True)
    a.add_argument("--pertrapnight",required=True)
    a.add_argument("--output",required=True)
    args=a.parse_args()
    r=check(args.perplotnight,args.pertrapnight)
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
    if r["status"]!="PASS_SOURCE_STRUCTURE_ONLY":raise SystemExit(2)

if __name__=="__main__":main()
