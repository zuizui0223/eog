"""Exact prior/detection misspecification sensitivity for six-site EOG×BAM.

True generating prior is fixed uniform over distinct BAM masks. Alternative
priors are *assumed by decision rule only*, never treated as field estimates.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from benchmarks import bam_detection_effort_v1 as base

CONTRACT="03f995d699d1543143131781a51216e9b9312789"
TRUE_PS=(0.5,0.8)
ASSUMED_PS=(0.5,0.8)
PRIOR_FAMILIES=("uniform_mask","uniform_G","uniform_sign")
VISITS=3
THRESHOLD=0.95

def weights(states,family):
    n=len(states)
    if family=="uniform_mask":
        w=np.ones(n)
    elif family=="uniform_G":
        counts={}
        for s in states: counts[s["G"]]=counts.get(s["G"],0)+1
        w=np.array([1/counts[s["G"]] for s in states])
    elif family=="uniform_sign":
        counts={}
        for s in states: counts[s["sign"]]=counts.get(s["sign"],0)+1
        w=np.array([1/counts[s["sign"]] for s in states])
    else: raise ValueError("unknown prior")
    w=w/w.sum()
    if not np.isfinite(w).all() or (w<=0).any() or not np.isclose(w.sum(),1):
        raise ValueError("invalid prior")
    return w

def analyze_system(system):
    _,signs,known=base.prior.signs_M(system)
    triples={}
    for r in system["worlds"]:
        key=tuple(int(r[f"{a}_bits"]) for a in ("A","B","M"))
        sign=int(signs[r["world_id"]])
        if key in triples and triples[key]["sign"]!=sign:
            raise ValueError("duplicate triple contradictory")
        triples[key]={"G":int(r["G_bits"]),"sign":sign}
    states=[triples[k] for k in sorted(triples)]
    sites=base.choose_sites(system["worlds"],system["width"]*system["height"])
    true_weights=weights(states,"uniform_mask")
    signs_array=np.array([s["sign"] for s in states])
    out=[]
    for true_p in TRUE_PS:
        Ltrue=np.array([[base.likelihood(pattern,s["G"],sites,true_p,VISITS)
                         for s in states] for pattern in range(64)])
        if not np.allclose(Ltrue.sum(axis=0),1):raise AssertionError("true likelihood")
        true_joint=Ltrue*true_weights
        true_mass=true_joint.sum(axis=1)
        for assumed_p in ASSUMED_PS:
            Lassumed=np.array([[base.likelihood(pattern,s["G"],sites,assumed_p,VISITS)
                                for s in states] for pattern in range(64)])
            for family in PRIOR_FAMILIES:
                w=weights(states,family)
                joint=Lassumed*w
                total=joint.sum(axis=1)
                posterior=np.zeros((64,3))
                valid=total>0
                for j,sign in enumerate((-1,0,1)):
                    posterior[valid,j]=joint[valid][:,signs_array==sign].sum(axis=1)/total[valid]
                if not np.allclose(posterior[valid].sum(axis=1),1):raise AssertionError("posterior")
                decision=posterior.argmax(axis=1)
                accepted=valid&(posterior.max(axis=1)>=THRESHOLD-1e-12)
                true_sign_joint=np.stack([true_joint[:,signs_array==sign].sum(axis=1)
                                          for sign in (-1,0,1)],axis=1)
                correct=float(true_sign_joint[np.arange(64)[accepted],decision[accepted]].sum())
                wrong=float((true_mass[accepted]-true_sign_joint[np.arange(64)[accepted],decision[accepted]]).sum())
                abstain=float(true_mass[~accepted].sum())
                if not np.isclose(correct+wrong+abstain,1,atol=1e-12):
                    raise AssertionError("risk not conserved")
                truth_wrong=[float(Ltrue[accepted&(signs_array[i]!=np.array((-1,0,1))[decision]),i].sum())
                             for i in range(len(states))]
                out.append({"system_id":system["system_id"],"true_p":true_p,
                            "assumed_p":assumed_p,"assumed_prior":family,
                            "visits":VISITS,"n_distinct_masks":len(states),
                            "correct":correct,"wrong":wrong,"abstain":abstain,
                            "worst_truth_wrong":max(truth_wrong),
                            "decision_patterns":int(accepted.sum()),
                            "n_sites":len(sites),"full_G_known":known})
    return out

def run(systems):
    if len(systems)!=12 or sum(len(s["worlds"]) for s in systems)!=768:
        raise AssertionError("source roster")
    rows=[r for system in systems for r in analyze_system(system)]
    summary=[]
    for tp in TRUE_PS:
        for ap in ASSUMED_PS:
            for fam in PRIOR_FAMILIES:
                group=[r for r in rows if r["true_p"]==tp and r["assumed_p"]==ap and r["assumed_prior"]==fam]
                summary.append({"true_p":tp,"assumed_p":ap,"assumed_prior":fam,
                    "mean_correct":float(np.mean([r["correct"] for r in group])),
                    "mean_wrong":float(np.mean([r["wrong"] for r in group])),
                    "mean_abstain":float(np.mean([r["abstain"] for r in group])),
                    "worst_truth_wrong":max(r["worst_truth_wrong"] for r in group),
                    "n_landscapes":len(group)})
    original=next(x for x in summary if x["true_p"]==0.8 and x["assumed_p"]==0.8 and x["assumed_prior"]=="uniform_mask")
    expected=(0.353909726564504,0.0008133028898816199,0.6452769705456144)
    if not np.allclose([original["mean_correct"],original["mean_wrong"],original["mean_abstain"]],expected,rtol=1e-9,atol=1e-12):
        raise AssertionError("parent result changed")
    if sum(r["full_G_known"] for r in rows if r["true_p"]==0.8 and r["assumed_p"]==0.8 and r["assumed_prior"]=="uniform_mask")!=121:
        raise AssertionError("original full G denominator")
    result={"schema":"eog.bam_detection_prior_calibration_v1.result",
            "status":"POST_EXPOSURE_HYPOTHETICAL_SENSITIVITY",
            "protocol_commit":CONTRACT,"landscapes":12,"worlds":768,
            "rows":rows,"summary":summary,
            "limits":["True prior is hypothetical uniform mask, not an ecological population.",
                      "Assumed p and prior are sensitivity inputs, not fitted field estimates.",
                      "Six sites and 3 visits, no false positives or spatial heterogeneity.",
                      "No new EOG-WF endpoint or causal mechanism identification."]}
    result["fingerprint"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    result=run(base.prior.parent.canonical_systems())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("BAM_PRIOR_SENSITIVITY="+json.dumps({"summary":result["summary"],"fingerprint":result["fingerprint"]},sort_keys=True))
