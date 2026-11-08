"""Real deer temporal persistence diagnostic with within-site fixed-count null.

No causal proof of serial dependence: effort, season, closure and detection
heterogeneity remain unmeasured.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'src'))
from benchmarks import emammal_deer_detection_v1 as parent

PROTOCOL_COMMIT="6646c777305e1ee7259825b5e73d003ec852a203"
SOURCE_SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
DRAWS=1999
SEED=20261108

def transitions(mat):
    left,right=mat[:,:-1],mat[:,1:]
    valid=np.isfinite(left)&np.isfinite(right)
    l,r=left[valid].astype(int),right[valid].astype(int)
    return {"pairs":int(valid.sum()),"same":int((l==r).sum()),
            "11":int(((l==1)&(r==1)).sum()),
            "00":int(((l==0)&(r==0)).sum()),
            "switch":int((l!=r).sum())}

def permute_within_site(mat,rng):
    result=mat.copy()
    for row in result:
        observed=np.flatnonzero(np.isfinite(row))
        row[observed]=rng.permutation(row[observed])
    return result

def analyze(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError("source SHA changed")
    mat,sites=parent.read_history(path)
    if len(sites)!=87:raise AssertionError("site count")
    full=parent.fit(mat,22)
    if not np.allclose([full["p_MLE"],full["psi_MLE"]],
                       [0.3679060046359003,0.720139945903844],atol=2e-5):
        raise AssertionError("parent MLE drift")
    observed=transitions(mat)
    rng=np.random.default_rng(SEED)
    null=[transitions(permute_within_site(mat,rng)) for _ in range(DRAWS)]
    keys=("same","11","00","switch")
    tests={}
    for key in keys:
        vals=np.array([x[key] for x in null])
        value=observed[key]
        low=(1+int((vals<=value).sum()))/(DRAWS+1)
        high=(1+int((vals>=value).sum()))/(DRAWS+1)
        tests[key]={"observed":value,"null_mean":float(vals.mean()),
                    "null_q025":float(np.quantile(vals,.025)),
                    "null_q975":float(np.quantile(vals,.975)),
                    "exploratory_two_sided_mc_p":min(1.,2*min(low,high))}
    thinned={}
    for name,columns in (("odd_days",slice(0,22,2)),("even_days",slice(1,22,2))):
        # fit() uses first N columns, so supply a newly sliced 11-column matrix.
        thinned[name]=parent.fit(mat[:,columns],11)
    result={"schema":"eog.emammal_deer_temporal_dependence_v1.result",
            "status":"EXPLORATORY_REAL_DATA_DEPENDENCE_DIAGNOSTIC",
            "source_sha256":SOURCE_SHA,"protocol_commit":PROTOCOL_COMMIT,
            "n_sites":87,"draws":DRAWS,"seed":SEED,
            "observed_transitions":observed,"permutation_tests":tests,
            "fits":{"all_22":full,**thinned},
            "limitations":["Within-site permutation removes temporal order but does not account for day effects, heterogeneous effort or closure changes.",
                           "Daily cameras are not independent visits merely because days differ.",
                           "Odd/even thinning changes observation effort and cannot prove closure.",
                           "No independent A/B/M measurements or causal EOG response.",
                           "Exploratory use of public example; no new EOG-WF endpoint."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--source",type=Path,required=True)
    a.add_argument("--output",type=Path,required=True)
    args=a.parse_args()
    result=analyze(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DEER_TEMPORAL_DEPENDENCE="+json.dumps(result,sort_keys=True))
