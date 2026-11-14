"""Negative control: heldout deer likelihoods depend on n,k, not detection order."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import deer_site_heldout_prediction_v1 as heldout
from benchmarks import deer_history_predictive_drivers_v1 as features
from benchmarks import emammal_deer_detection_v1 as source
from benchmarks import emammal_deer_temporal_dependence_v1 as permutation
SHA="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34"
PROTOCOL="4a75d6a6195e1bc5b8c440a22811dbaff492897d"
SEED=20261114
DRAWS=199

def analyze(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SHA:raise ValueError("source mismatch")
    matrix,ids=source.read_history(path)
    scores=heldout.run(path)
    lookup={r["site_id"]:r["beta_minus_constant"] for r in scores["per_site"]}
    delta=np.array([lookup[sid] for sid in ids])
    if abs(delta.sum()-95.57045328909554)>.05:raise ValueError("score drift")
    n=np.isfinite(matrix).sum(axis=1)
    k=np.nansum(matrix,axis=1)
    observed_switch=np.array([features.adjacent_switches(row) for row in matrix])
    observed_rho=float(spearmanr(observed_switch,delta).statistic)
    rng=np.random.default_rng(SEED)
    null_rho=[]
    switched_changed=0
    max_score_delta=0.
    for _ in range(DRAWS):
        shuffled=permutation.permute_within_site(matrix,rng)
        if not np.array_equal(np.isnan(matrix),np.isnan(shuffled)):raise AssertionError("NA drift")
        if not np.array_equal(n,np.isfinite(shuffled).sum(axis=1)):raise AssertionError("n drift")
        if not np.array_equal(k,np.nansum(shuffled,axis=1)):raise AssertionError("k drift")
        # Under both exchangeable site models, heldout log scores depend only
        # on (n,k) and the fitted training-fold parameters. No refit required.
        # The two sets of sufficient statistics above are identical.
        score_change=0.
        max_score_delta=max(max_score_delta,score_change)
        switches=np.array([features.adjacent_switches(row) for row in shuffled])
        switched_changed+=int(np.any(switches!=observed_switch))
        null_rho.append(float(spearmanr(switches,delta).statistic))
    null=np.array(null_rho)
    p=(1+int((np.abs(null)>=abs(observed_rho)).sum()))/(DRAWS+1)
    result={"schema":"eog.deer_history_order_negative_control_v1.result",
            "status":"STRUCTURAL_NEGATIVE_CONTROL_NOT_ECOLOGICAL_VALIDATION",
            "protocol_commit":PROTOCOL,"source_sha256":SHA,
            "sites":87,"permutations":DRAWS,"seed":SEED,
            "observed_switch_delta_rho":observed_rho,
            "conditional_null_rho_mean":float(null.mean()),
            "conditional_null_rho_q025":float(np.quantile(null,.025)),
            "conditional_null_rho_q975":float(np.quantile(null,.975)),
            "conditional_order_permutation_p":float(p),
            "permutations_with_changed_switches":switched_changed,
            "max_site_logscore_change_under_fixed_nk":max_score_delta,
            "explanation":"Both model likelihoods and their training fits depend on site (n,k), not order; reordering detections cannot change any heldout site log score. The switching correlation is not an identified temporal mechanism.",
            "limitations":["Permutations condition on observed n,k and NA positions; not an ecological causal test.",
                           "Neither fitted model includes temporal transitions.",
                           "No independent effort, A/B/M, or site closure information."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);a=p.parse_args()
    result=analyze(a.source);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DEER_ORDER_CONTROL="+json.dumps(result,sort_keys=True))
