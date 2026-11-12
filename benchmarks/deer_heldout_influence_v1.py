"""Concentration audit for held-out site-level predictive gains, no refitting selection."""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import deer_site_heldout_prediction_v1 as upstream
PROTOCOL="a1803fb0e15126732df25a3b66082e13f6651ea2"
EXPECTED="78ce643a8418954e834300a4c6e56129839fc84de0375536d53bf296a6defe2f"

def audit(result):
    # Optimizer/library changes may alter a JSON fingerprint without substantive drift.
    if result.get("source_sha256")!="bcfeb04683e572d0ded79fd40917a546188b4e2df64c043d9e1ea8720d524e34":
        raise ValueError("source mismatch")
    if not np.isclose(result.get("beta_minus_constant_total_log_score",float("nan")),
                      95.57045328909554,atol=0.05,rtol=0):
        raise ValueError("upstream score drift beyond tolerance")
    rows=result["per_site"]
    if len(rows)!=87 or len({r["site_id"] for r in rows})!=87:
        raise ValueError("site roster mismatch")
    ranked=sorted(rows,key=lambda r:(-r["beta_minus_constant"],r["site_id"]))
    d=np.array([r["beta_minus_constant"] for r in ranked],float)
    if not np.isfinite(d).all():raise ValueError("nonfinite score")
    total=float(d.sum())
    if not np.isclose(total,result["beta_minus_constant_total_log_score"],atol=1e-7):
        raise ValueError("score sum mismatch")
    pos=float(d[d>0].sum());neg=float(d[d<0].sum())
    removal=[]
    for k in (1,3,5,10):
        remaining=d[k:]
        removal.append({"remove_top_k":k,"removed_site_ids":[r["site_id"] for r in ranked[:k]],
                        "removed_gain":float(d[:k].sum()),
                        "share_of_net_gain":float(d[:k].sum()/total) if total!=0 else None,
                        "remaining_total_gain":float(remaining.sum()),
                        "remaining_mean_gain":float(remaining.mean()),
                        "remaining_beta_wins":int((remaining>0).sum()),
                        "remaining_constant_wins":int((remaining<0).sum())})
    ascending=np.sort(d)
    trimmed=[]
    for pct in (.05,.10):
        k=int(np.floor(len(d)*pct))
        kept=ascending[k:len(d)-k]
        trimmed.append({"trim_fraction_each_tail":pct,"trim_each_tail_sites":k,
                        "n_remaining":len(kept),"mean_gain":float(kept.mean()),
                        "sum_gain":float(kept.sum())})
    fold_deltas=[{"fold":f["fold"],"delta_log_score":float(f["heldout_beta_log_score"]-f["heldout_constant_log_score"]),
                  "n_sites":f["n_test"]} for f in result["folds"]]
    out={"schema":"eog.deer_heldout_influence_v1.result",
         "status":"EXPLORATORY_SAME_DATASET_HELDOUT_INFLUENCE",
         "protocol_commit":PROTOCOL,"upstream_reference_fingerprint":EXPECTED,
         "upstream_recomputed_fingerprint":result.get("fingerprint"),
         "source_sha256":result["source_sha256"],"sites":len(rows),
         "total_gain":total,"positive_site_gain_sum":pos,
         "negative_site_gain_sum":neg,"median_site_gain":float(np.median(d)),
         "mean_site_gain":float(d.mean()),"beta_site_wins":int((d>0).sum()),
         "constant_site_wins":int((d<0).sum()),"top_site":{"site_id":ranked[0]["site_id"],"gain":float(d[0])},
         "bottom_site":{"site_id":ranked[-1]["site_id"],"gain":float(d[-1])},
         "top_k_removal":removal,"symmetric_trimmed":trimmed,"fold_gains":fold_deltas,
         "limitations":["Post hoc influence diagnostics on one already explored source.",
                        "Removing high-gain sites is a robustness diagnostic, not a new target population.",
                        "Site geography, effort, temporal closure and biological mechanism remain unverified.",
                        "No measured A/B/M, causal EOG geometry or new EOG-WF endpoint."]}
    out["fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    original=upstream.run(a.source)
    result=audit(original)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("DEER_HELDOUT_INFLUENCE="+json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
