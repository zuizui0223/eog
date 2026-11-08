"""Real eMammal deer camera-trap detection-history audit and exploratory MLE.

Input is a fixed-commit external CSV. Missing NA visits are not zeros.
No independent site closure or repeated-visit independence verification.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

SOURCE_COMMIT="f65b220d1c84240fa81cb457bf27522424fe1666"
PROTOCOL_COMMIT="4c7d7ada3c527f2da541ab10609dbe4839ab14b5"

def read_history(path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f)
        names=reader.fieldnames
        expected=["site"]+[f"o{i}" for i in range(1,23)]
        if names!=expected:raise ValueError("unexpected source schema")
        rows=list(reader)
    if len(rows)!=87 or len({r["site"] for r in rows})!=87:
        raise ValueError("source roster differs from 87 unique sites")
    mat=np.full((87,22),np.nan)
    for i,r in enumerate(rows):
        for j,name in enumerate(expected[1:]):
            val=r[name].strip()
            if val=="NA":continue
            if val not in ("0","1"):raise ValueError(f"unexpected detection at {i},{j}")
            mat[i,j]=int(val)
    if (np.isfinite(mat).sum(axis=1)<2).any():raise ValueError("site lacks repeated occasions")
    if not np.nansum(mat)>0:raise ValueError("no detections")
    return mat, [r["site"] for r in rows]

def log_likelihood(params,n,k):
    psi,p=params
    if not (0<psi<1 and 0<p<1):return -np.inf
    positive=k>0
    ll=np.zeros(len(n))
    ll[positive]=np.log(psi)+k[positive]*np.log(p)+(n[positive]-k[positive])*np.log1p(-p)
    # log((1-psi)+psi*(1-p)^n), numerically stable
    zero=~positive
    ll[zero]=np.logaddexp(np.log1p(-psi),np.log(psi)+n[zero]*np.log1p(-p))
    return float(ll.sum())

def fit(mat,max_days):
    x=mat[:,:max_days]
    n=np.isfinite(x).sum(axis=1)
    k=np.nansum(x,axis=1)
    use=n>=2
    if use.sum()<5 or not (k[use]>0).any():raise ValueError("not enough informative sites")
    n=n[use];k=k[use]
    starts=((0.5,0.5),(0.8,0.2),(0.3,0.8),(0.9,0.05))
    opts=[]
    for initial in starts:
        res=minimize(lambda a:-log_likelihood(a,n,k),initial,method="L-BFGS-B",
                     bounds=[(1e-8,1-1e-8)]*2,
                     options={"ftol":1e-12,"maxiter":2000})
        if res.success and np.isfinite(res.fun):opts.append(res)
    if not opts:raise RuntimeError("occupancy/detection MLE failed")
    best=min(opts,key=lambda r:r.fun)
    if any(not np.isfinite(z) for z in best.x):raise RuntimeError("invalid MLE")
    return {
        "days":max_days,"n_sites_at_least_2_visits":int(use.sum()),
        "n_valid_site_days":int(n.sum()),
        "n_detected_site_days":int(k.sum()),
        "n_sites_ever_detected":int((k>0).sum()),
        "naive_detected_site_fraction":float((k>0).mean()),
        "psi_MLE":float(best.x[0]),"p_MLE":float(best.x[1]),
        "log_likelihood":float(-best.fun),
        "multistart_successes":len(opts),
        "assumptions":"single-season closure, constant ψ and p, independent observed days, no false positives",
    }

def analyze(path):
    mat,sites=read_history(path)
    models=[fit(mat,days) for days in (7,14,22)]
    result={
        "schema":"eog.emammal_deer_repeated_detection_v1.result",
        "status":"EXPLORATORY_REAL_CAMERA_TRAP_DETECTION_ONLY",
        "source":{"repo":"BrentPease1/single-season-occupancy",
                  "commit":SOURCE_COMMIT,"path":"deer_detection_history.csv",
                  "sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                  "sites":len(sites),"daily_columns":22},
        "protocol_commit":PROTOCOL_COMMIT,
        "qc":{"observed_site_days":int(np.isfinite(mat).sum()),
              "missing_site_days":int(np.isnan(mat).sum()),
              "detected_site_days":int(np.nansum(mat)),
              "zero_detected_sites":int((np.nansum(mat,axis=1)==0).sum()),
              "observed_sites":len(sites)},
        "fits":models,
        "limits":["No actual daily effort, coordinates or full independent A/B/M measures in original CSV.",
                  "Daily visits may be temporally correlated; 22-day site closure unverified.",
                  "Deer species not independently verified; source's simulated covariates excluded.",
                  "Occupancy is a latent-model estimate, not observed truth or EOG geometry.",
                  "Not a confirmatory ecological replication or EOG-WF endpoint."]
    }
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    r=analyze(a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print("EMAMMAL_DEER_DETECTION="+json.dumps(r,sort_keys=True))
