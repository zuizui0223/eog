"""Real deer site-level latent detection heterogeneity; exploratory beta mixture."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,betaln
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import emammal_deer_detection_v1 as parent
SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
PROTOCOL="534951d03ba42feb02358e245a6492317ddf9269"

def mixture_loglike(theta,n,k):
    psi=float(expit(theta[0]))
    alpha,beta=np.exp(theta[1:])
    logocc=betaln(k+alpha,n-k+beta)-betaln(alpha,beta)
    has=k>0
    terms=np.where(has,np.log(psi)+logocc,
                   np.logaddexp(np.log1p(-psi),np.log(psi)+logocc))
    return float(terms.sum())

def fit_mixture(history):
    n=np.isfinite(history).sum(axis=1)
    k=np.nansum(history,axis=1)
    starts=((1.,0.,0.),(1.,2.,2.),(1.,-1.,-1.),(0.,3.,3.),(2.,0.,2.))
    results=[]
    for init in starts:
        r=minimize(lambda x:-mixture_loglike(x,n,k),init,method="L-BFGS-B",
                   bounds=[(-10,10),(-6,9),(-6,9)],
                   options={"maxiter":3000,"ftol":1e-12})
        if r.success and np.isfinite(r.fun):results.append(r)
    if not results:raise RuntimeError("no converged beta-mixture")
    best=min(results,key=lambda x:x.fun)
    psi=float(expit(best.x[0]))
    alpha,beta=np.exp(best.x[1:])
    mean=float(alpha/(alpha+beta))
    sd=float(np.sqrt(alpha*beta/((alpha+beta)**2*(alpha+beta+1))))
    params=3;sites=len(history)
    aic=2*params+2*best.fun
    return {"model":"beta_site_detection","psi":psi,"p_mean":mean,
            "p_between_site_sd":sd,"alpha":float(alpha),"beta":float(beta),
            "log_likelihood":float(-best.fun),"AIC":float(aic),
            "AICc":float(aic+2*params*(params+1)/(sites-params-1)),
            "successful_starts":len(results),"parameters":params}

def analyze(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SHA:
        raise ValueError("source SHA mismatch")
    history,_=parent.read_history(path)
    baseline=parent.fit(history,22)
    k=2;sites=len(history)
    aic=2*k-2*baseline["log_likelihood"]
    base={"model":"constant_detection","psi":baseline["psi_MLE"],
          "p_mean":baseline["p_MLE"],"p_between_site_sd":0.,
          "log_likelihood":baseline["log_likelihood"],"AIC":aic,
          "AICc":aic+2*k*(k+1)/(sites-k-1),"parameters":k}
    mix=fit_mixture(history)
    if not np.allclose([base["p_mean"],base["psi"]],
                       [.3679060046359003,.720139945903844],atol=2e-5):
        raise AssertionError("parent regression")
    result={"schema":"eog.deer_site_detection_heterogeneity_v1.result",
            "status":"EXPLORATORY_REAL_DETECTION_LATENT_SITE_MIXTURE",
            "protocol_commit":PROTOCOL,"source_sha256":SHA,
            "observations":{"sites":87,"valid_site_days":int(np.isfinite(history).sum()),
                            "missing_site_days":int(np.isnan(history).sum()),
                            "detected_site_days":int(np.nansum(history))},
            "models":[base,mix],
            "delta_AICc_mixture_minus_constant":float(mix["AICc"]-base["AICc"]),
            "delta_psi_mixture_minus_constant":float(mix["psi"]-base["psi"]),
            "limitations":["Beta mixture is a statistical representation, not independently observed site-level detectability.",
                           "Site heterogeneity can absorb temporal correlation, occupancy nonclosure, effort or availability variation.",
                           "AICc assumes site independence and does not verify ecological mechanisms.",
                           "No independent abiotic/biotic/movement measures or EOG geometric response.",
                           "No fourth EOG-WF endpoint."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);args=p.parse_args()
    r=analyze(args.source);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("DEER_SITE_DETECTION="+json.dumps(r,sort_keys=True))
