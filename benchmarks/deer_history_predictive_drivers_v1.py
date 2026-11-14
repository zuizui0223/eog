"""Describe which observed camera histories drive held-out model score differences."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import deer_site_heldout_prediction_v1 as heldout
from benchmarks import emammal_deer_detection_v1 as source
SOURCE_SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
PROTOCOL="bf1c955ad27b5e10b1e5934603697d65e664799c"

def longest_zero_run(row):
    best=cur=0
    for v in row:
        if np.isfinite(v) and v==0:
            cur+=1;best=max(best,cur)
        else:cur=0
    return best

def adjacent_switches(row):
    left,right=row[:-1],row[1:]
    valid=np.isfinite(left)&np.isfinite(right)
    return int((left[valid]!=right[valid]).sum())

def feature(row):
    valid=np.isfinite(row)
    n=int(valid.sum());k=int(np.nansum(row))
    return {"observed_days":n,"missing_days":int(len(row)-n),
            "detected_days":k,"detection_fraction_valid":float(k/n) if n else None,
            "longest_zero_run":longest_zero_run(row),
            "adjacent_switches":adjacent_switches(row),
            "ever_detected":bool(k>0)}

def summary(rows):
    deltas=np.array([x["delta"] for x in rows],float)
    return {"sites":len(rows),"mean_delta":float(deltas.mean()),
            "total_delta":float(deltas.sum()),"median_delta":float(np.median(deltas)),
            "beta_wins":int((deltas>0).sum()),"constant_wins":int((deltas<0).sum())}

def group(rows,key,fn):
    keys=sorted({fn(r[key]) for r in rows},key=str)
    return [{"group":str(k),**summary([r for r in rows if fn(r[key])==k])} for k in keys]

def run(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("source mismatch")
    mat,ids=source.read_history(path)
    old=heldout.run(path)
    if abs(old["beta_minus_constant_total_log_score"]-95.57045328909554)>.05:
        raise ValueError("upstream score drift")
    scores={r["site_id"]:r["beta_minus_constant"] for r in old["per_site"]}
    if len(scores)!=87 or set(scores)!=set(ids):raise ValueError("site ID mismatch")
    rows=[]
    for sid,history in zip(ids,mat):
        rows.append({"site_id":sid,"delta":float(scores[sid]),**feature(history)})
    rho={}
    for key in ("observed_days","missing_days","detected_days",
                "detection_fraction_valid","longest_zero_run","adjacent_switches"):
        x=np.array([r[key] for r in rows],float)
        if np.unique(x).size<2:
            rho[key]={"rho":None,"p_exploratory":None}
        else:
            v,p=spearmanr(x,[r["delta"] for r in rows])
            rho[key]={"rho":float(v),"p_exploratory":float(p)}
    ranked=sorted(rows,key=lambda r:(-r["delta"],r["site_id"]))
    count_bin=lambda n:"0" if n==0 else ("1-2" if n<=2 else ("3-8" if n<=8 else "9+"))
    missing_bin=lambda n:"0" if n==0 else ("1-4" if n<=4 else "5+")
    result={"schema":"eog.deer_history_predictive_drivers_v1.result",
            "status":"EXPLORATORY_SAME_SOURCE_HISTORY_ASSOCIATIONS",
            "protocol_commit":PROTOCOL,"source_sha256":SOURCE_SHA,
            "upstream_fingerprint":old["fingerprint"],
            "overall":summary(rows),"spearman":rho,
            "groups":{"ever_detected":group(rows,"ever_detected",lambda x:x),
                      "detected_days":group(rows,"detected_days",count_bin),
                      "missing_days":group(rows,"missing_days",missing_bin)},
            "top_10_vs_other":{"top_10":summary(ranked[:10]),"other_77":summary(ranked[10:]),
                 "top_10_mean_features":{k:float(np.mean([r[k] for r in ranked[:10]])) for k in
                                         ("observed_days","missing_days","detected_days",
                                          "detection_fraction_valid","longest_zero_run","adjacent_switches")},
                 "other_77_mean_features":{k:float(np.mean([r[k] for r in ranked[10:]])) for k in
                                           ("observed_days","missing_days","detected_days",
                                            "detection_fraction_valid","longest_zero_run","adjacent_switches")}},
            "per_site":rows,
            "limitations":["Features and heldout score are functions of the same detection histories; associations are descriptive and may be mathematical.",
                           "No causal ecological mechanism or independent validation.",
                           "No effort, geographic coordinates, independently verified closure, or A/B/M measurements.",
                           "No new EOG-WF endpoint."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=run(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("DEER_HISTORY_DRIVERS="+json.dumps({k:v for k,v in r.items() if k!="per_site"},sort_keys=True))
