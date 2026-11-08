"""Exact six-site imperfect-detection sensitivity for original EOG×BAM.

No new field data. Site selection is target-blind; posterior uses a
hypothetical uniform prior on distinct BAM masks, never world labels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
from collections import defaultdict
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"src"))
from benchmarks import bam_one_bit_error_v1 as prior

PROTOCOL_COMMIT="e415f55e0e3109d8c36e02aa91dd581a6ac98865"
SCENARIOS=((0.5,1),(0.5,3),(0.5,6),(0.8,1),(0.8,3),(0.8,6),(1.0,1))
SITES=6
THRESHOLD=0.95


def choose_sites(rows,n_nodes,n_sites=SITES):
    """Only occupancy variation, no EOG target labels or observed outcomes."""
    if n_sites>n_nodes:raise ValueError("not enough sites")
    unique={tuple(int(r[f"{a}_bits"]) for a in ("A","B","M")):int(r["G_bits"]) for r in rows}
    masks=list(unique.values())
    scores=[]
    for node in range(n_nodes):
        present=sum((mask>>node)&1 for mask in masks)
        scores.append((present*(len(masks)-present),-node,node))
    return tuple(x[2] for x in sorted(scores,reverse=True)[:n_sites])


def likelihood(pattern,mask,sites,p,k):
    if not 0<p<=1 or k<1:raise ValueError("invalid detection model")
    q=1-(1-p)**k
    result=1.0
    for j,node in enumerate(sites):
        occupied=(mask>>node)&1
        detected=(pattern>>j)&1
        if detected and not occupied:return 0.
        if occupied:result*=q if detected else (1-q)
    return result


def evaluate_system(system):
    sid=system["system_id"]
    n_nodes=system["width"]*system["height"]
    if len(system["worlds"])!=64:raise ValueError("source roster changed")
    _,signs,known=prior.signs_M(system)
    triples={}
    for row in system["worlds"]:
        triple=tuple(int(row[f"{a}_bits"]) for a in ("A","B","M"))
        sign=signs[row["world_id"]]
        if triple in triples and triples[triple]["sign"]!=sign:
            raise AssertionError("same masks different target")
        triples[triple]={"G":int(row["G_bits"]),"sign":int(sign)}
    states=list(triples.values())
    sites=choose_sites(system["worlds"],n_nodes)
    n=len(states)
    result=[]
    for p,k in SCENARIOS:
        # pattern x truth, each row of conditional likelihoods.
        L=np.array([[likelihood(pattern,s["G"],sites,p,k) for s in states]
                    for pattern in range(1<<SITES)],float)
        if not np.allclose(L.sum(axis=0),1,atol=1e-12):
            raise AssertionError("conditional detection patterns do not sum to one")
        mass=L.mean(axis=1)
        sign_probs=np.zeros((len(L),3))
        for j,sign in enumerate((-1,0,1)):
            sign_probs[:,j]=L[:,[i for i,s in enumerate(states) if s["sign"]==sign]].sum(axis=1)/n
        valid=mass>0
        posterior=np.zeros_like(sign_probs)
        posterior[valid]=sign_probs[valid]/mass[valid,None]
        if not np.allclose(posterior[valid].sum(axis=1),1):
            raise AssertionError("posterior normalization")
        maxprob=posterior.max(axis=1)
        decide=valid&(maxprob>=THRESHOLD-1e-12)
        choice=np.argmax(posterior,axis=1)
        correct=float(sign_probs[np.arange(len(L))[decide],choice[decide]].sum())
        wrong=float((mass[decide]-sign_probs[np.arange(len(L))[decide],choice[decide]]).sum())
        abstain=float(mass[~decide].sum())
        if not np.isclose(correct+wrong+abstain,1):
            raise AssertionError("risk decomposition")
        truth_wrong=[]
        for i,state in enumerate(states):
            mismatch=np.array([(-1,0,1)[j]!=state["sign"] for j in choice])
            truth_wrong.append(float(L[decide&mismatch,i].sum()))
        logical_unanimous=sum(valid&(np.count_nonzero(sign_probs>0.0,axis=1)==1))
        result.append({
            "system_id":sid,"p":p,"visits":k,"n_sites":SITES,
            "n_distinct_mask_triples":n,
            "perfect_full_G_direction_known_fibres":known,
            "site_ids":list(sites),
            "positive_probability_patterns":int(valid.sum()),
            "logically_unanimous_patterns":int(logical_unanimous),
            "expected_correct_decision":correct,
            "expected_wrong_decision":wrong,
            "expected_abstention":abstain,
            "worst_truth_wrong_decision":max(truth_wrong),
            "prior":"uniform distinct BAM mask triples; model sensitivity only",
        })
    return result


def run(systems):
    if len(systems)!=12 or sum(len(s["worlds"]) for s in systems)!=768:
        raise AssertionError("parent known truth drift")
    rows=[row for system in systems for row in evaluate_system(system)]
    if sum(r["perfect_full_G_direction_known_fibres"] for r in rows if r["p"]==0.8 and r["visits"]==3)!=121:
        raise AssertionError("parent exact full-G sign baseline drift")
    summary=[]
    for p,k in SCENARIOS:
        selected=[r for r in rows if r["p"]==p and r["visits"]==k]
        summary.append({
            "p":p,"visits":k,"landscapes":len(selected),
            "mean_correct":float(np.mean([r["expected_correct_decision"] for r in selected])),
            "mean_wrong":float(np.mean([r["expected_wrong_decision"] for r in selected])),
            "mean_abstain":float(np.mean([r["expected_abstention"] for r in selected])),
            "max_truth_wrong_across_landscapes":max(r["worst_truth_wrong_decision"] for r in selected),
            "mean_logically_unanimous_patterns":float(np.mean([r["logically_unanimous_patterns"] for r in selected])),
        })
    report={
        "schema":"eog.bam_detection_effort_v1.result",
        "status":"EXPLORATORY_FINITE_WORLD_HYPOTHETICAL_PRIOR_NOT_FIELD_ESTIMATE",
        "protocol_commit":PROTOCOL_COMMIT,
        "source":{"systems":12,"worlds":768,"full_G_M_response_known_fibres":121},
        "survey":{"sites_per_system":6,"target_blind_site_selection":"occupancy variance only",
                  "no_false_positives":True,"detection_probability_if_occupied":[0.5,0.8,1.0],
                  "visits":[1,3,6],"decision_posterior_threshold":0.95},
        "results":summary,"per_system":rows,
        "limitations":["No empirical detection rate or survey effort was measured.",
                       "Six selected nodes, not full map, and uniform hypothetical mask-triple prior.",
                       "No true absence can be deduced from nondetection at p<1.",
                       "Twelve constructed landscapes, not independent natural replications.",
                       "No causal BAM inference, EOG predictive superiority or new EOG-WF endpoint."]
    }
    report["fingerprint"]=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return report


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--output",required=True,type=Path)
    args=a.parse_args()
    report=run(prior.parent.canonical_systems())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("DETECTION_EFFORT_RESULT="+json.dumps({"fingerprint":report["fingerprint"],"results":report["results"]},sort_keys=True))


if __name__=="__main__":
    main()
