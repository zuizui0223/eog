"""Exploratory deer detection heterogeneity by observation column (not calendar date)."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logsumexp
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import emammal_deer_detection_v1 as parent
SOURCE_SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
PROTOCOL="dedb58c851162f4c382517faeba075baf20def99"

def design(model):
    j=np.arange(22)
    if model=="constant":return np.ones((22,1))
    if model=="linear":return np.column_stack([np.ones(22),(j-10.5)/10.5])
    if model=="early_late":return np.column_stack([np.ones(22),(j>=11).astype(float)])
    raise ValueError(model)

def loglike(theta,history,X):
    psi=expit(theta[0])
    p=expit(X@theta[1:])
    obs=np.isfinite(history)
    detected=(history==1)&obs
    nondetected=(history==0)&obs
    ll_occ=(detected*np.log(p)+(nondetected)*np.log1p(-p)).sum(axis=1)
    has_detection=detected.any(axis=1)
    ll=np.where(has_detection,np.log(psi)+ll_occ,
                np.logaddexp(np.log1p(-psi),np.log(psi)+ll_occ))
    return float(ll.sum())

def fit(history,model):
    X=design(model)
    starts=[np.array([.8,-.5]+[0.]*(X.shape[1]-1)),
            np.array([0.,0.]+[0.]*(X.shape[1]-1)),
            np.array([2.,-2.]+[0.]*(X.shape[1]-1))]
    fits=[]
    for start in starts:
        r=minimize(lambda theta:-loglike(theta,history,X),start,
                   method="L-BFGS-B",bounds=[(-10,10)]*(1+X.shape[1]),
                   options={"maxiter":1500,"ftol":1e-12})
        if r.success and np.isfinite(r.fun):fits.append(r)
    if not fits:raise RuntimeError(f"fit failed {model}")
    r=min(fits,key=lambda x:x.fun)
    psi=float(expit(r.x[0]));daily=expit(X@r.x[1:])
    n=len(history);k=len(r.x);aic=2*k+2*r.fun
    return {"model":model,"psi":psi,"daily_p":[float(v) for v in daily],
            "p_first":float(daily[0]),"p_last":float(daily[-1]),
            "p_mean":float(daily.mean()),"log_likelihood":float(-r.fun),
            "n_sites":n,"parameters":k,"AIC":float(aic),
            "AICc":float(aic+2*k*(k+1)/(n-k-1)),
            "successful_starts":len(fits),"coefficients":[float(v) for v in r.x]}

def run(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise ValueError("source sha drift")
    history,sites=parent.read_history(path)
    if history.shape!=(87,22):raise AssertionError("roster drift")
    fits=[fit(history,m) for m in ("constant","linear","early_late")]
    old=parent.fit(history,22)
    if not np.allclose([fits[0]["psi"],fits[0]["p_mean"]],
                       [old["psi_MLE"],old["p_MLE"]],atol=2e-5):
        raise AssertionError("constant model mismatch")
    for f in fits:f["delta_AICc"]=float(f["AICc"]-min(x["AICc"] for x in fits))
    report={"schema":"eog.deer_day_detection_heterogeneity_v1.result",
            "status":"EXPLORATORY_REAL_DETECTION_TIME_INDEX_SENSITIVITY",
            "protocol_commit":PROTOCOL,"source_sha256":SOURCE_SHA,
            "observations":{"sites":87,"valid_site_days":int(np.isfinite(history).sum()),
                            "missing_site_days":int(np.isnan(history).sum()),
                            "detected_site_days":int(np.nansum(history))},
            "models":fits,"reference_constant_parent":old,
            "limitations":["Day columns are ordered occasions, not independently verified calendar dates.",
                           "Temporal p heterogeneity may reflect effort, weather, individual movement, closure violations or unmeasured factors.",
                           "AICc comparison is exploratory and does not establish biological cause.",
                           "No independent full A/B/M measures or causal EOG response.",
                           "No new EOG-WF endpoint."]}
    report["fingerprint"]=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);a=p.parse_args()
    result=run(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DEER_DAY_HETEROGENEITY="+json.dumps(result,sort_keys=True))
