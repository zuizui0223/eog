"""Whole-site heldout log predictive score for real deer constant vs beta detection."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.special import betaln
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import emammal_deer_detection_v1 as parent
from benchmarks import deer_site_detection_heterogeneity_v1 as site_model
SOURCE_SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
PROTOCOL="6bdd27ab9c27e1bc65ce9def9231b2a327640c5e"
SEED=20261111
BOOT_SEED=20261112
DRAWS=1999

def site_log_score_constant(psi,p,n,k):
    positive=k>0
    occupied=np.log(psi)+k*np.log(p)+(n-k)*np.log1p(-p)
    return np.where(positive,occupied,np.logaddexp(np.log1p(-psi),occupied))

def site_log_score_beta(psi,alpha,beta,n,k):
    occupied=np.log(psi)+betaln(alpha+k,beta+n-k)-betaln(alpha,beta)
    return np.where(k>0,occupied,np.logaddexp(np.log1p(-psi),occupied))

def run(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("source mismatch")
    history,ids=parent.read_history(path)
    if history.shape!=(87,22):raise AssertionError("source roster")
    rng=np.random.default_rng(SEED)
    shuffled=rng.permutation(87)
    folds=np.array_split(shuffled,5)
    scores=np.full((87,2),np.nan)
    records=[]
    for fold,test in enumerate(folds):
        train=np.setdiff1d(np.arange(87),test)
        x=history[train]
        constant=parent.fit(x,22)
        mixture=site_model.fit_mixture(x)
        h=history[test]
        n=np.isfinite(h).sum(axis=1)
        k=np.nansum(h,axis=1)
        a=site_log_score_constant(constant["psi_MLE"],constant["p_MLE"],n,k)
        b=site_log_score_beta(mixture["psi"],mixture["alpha"],mixture["beta"],n,k)
        scores[test,0]=a;scores[test,1]=b
        records.append({"fold":fold+1,"n_train":len(train),"n_test":len(test),
                        "train_psi_constant":constant["psi_MLE"],"train_p_constant":constant["p_MLE"],
                        "train_psi_beta":mixture["psi"],"train_p_beta_mean":mixture["p_mean"],
                        "heldout_constant_log_score":float(a.sum()),
                        "heldout_beta_log_score":float(b.sum())})
    if not np.isfinite(scores).all():raise AssertionError("unscored site")
    delta=scores[:,1]-scores[:,0]
    bootstrap=np.random.default_rng(BOOT_SEED)
    means=np.array([float(bootstrap.choice(delta,size=87,replace=True).mean())
                    for _ in range(DRAWS)])
    result={"schema":"eog.deer_site_heldout_prediction_v1.result",
            "status":"EXPLORATORY_WITHIN_DATASET_SITE_HELDOUT",
            "protocol_commit":PROTOCOL,"source_sha256":SOURCE_SHA,
            "sites":87,"folds":records,"fold_seed":SEED,
            "constant_total_log_score":float(scores[:,0].sum()),
            "beta_total_log_score":float(scores[:,1].sum()),
            "beta_minus_constant_total_log_score":float(delta.sum()),
            "beta_minus_constant_mean_site_log_score":float(delta.mean()),
            "beta_minus_constant_bootstrap_95pct_mean_site_interval":[float(x) for x in np.quantile(means,[.025,.975])],
            "bootstrap_seed":BOOT_SEED,"bootstrap_draws":DRAWS,
            "sites_beta_better":int((delta>0).sum()),
            "sites_constant_better":int((delta<0).sum()),
            "per_site":[{"site_id":ids[i],"constant_log_score":float(scores[i,0]),
                         "beta_log_score":float(scores[i,1]),"beta_minus_constant":float(delta[i])}
                        for i in range(87)],
            "limitations":["Cross-validation within one previously analyzed public example, not external confirmation.",
                           "Site folds assume sites independent; coordinates unavailable.",
                           "Site-level beta mixture may absorb effort, closure violations and temporal dependence.",
                           "No causal full A/B/M, no EOG geometry, no EOG-WF endpoint."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    r=run(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print("DEER_HELDOUT="+json.dumps({k:v for k,v in r.items() if k not in ("per_site",)},sort_keys=True))
