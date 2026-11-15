"""Validate R 1..256 seed sensitivity of source-positive detection representations.

This is a fixed post-exposure analytical simulation of the *processing*
channel. Seeds are not biological/ecological replications. We do not fit
occupancy, assume physical independent survey occasions, or infer A/B/M.
"""
import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

SURVEY_SHA="45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA="93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
META={"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
COHORTS=("published_q1","published_q2")
SEEDS=tuple(range(1,257))
EXPECTED_POS={"published_q1":144,"published_q2":77}
EXPECTED_EXACT_MEANS={"published_q1":9.475863116344188,"published_q2":4.871441193156649}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        return list(reader),list(reader.fieldnames)


def prob_all_native_positives_dropped(n,k,reps=20):
    if not all(isinstance(v,int) for v in (n,k,reps)) or n<=0 or k<=0 or k>n or reps<=0:
        raise ValueError("invalid n/k/reps")
    if n<=reps:
        return ((n-k)/n)**reps
    if n-k<reps: return 0.0
    out=1.0
    for j in range(reps):
        out*= (n-k-j)/(n-j)
    return out


def sorted_quantile(values, q):
    """Deterministic linear-interpolation seed quantiles."""
    if not values or not 0<=q<=1:
        raise ValueError("empty seed values or invalid q")
    arr=sorted(values)
    at=(len(arr)-1)*q
    lo=math.floor(at);hi=math.ceil(at)
    return arr[lo]*(hi-at)+arr[hi]*(at-lo) if lo!=hi else float(arr[lo])


def describe_seed_values(values):
    """Monte Carlo seed dispersion, not field CI or inference."""
    return {
        "mean":statistics.mean(values),
        "median":statistics.median(values),
        "min":min(values),
        "max":max(values),
        "q05":sorted_quantile(values,0.05),
        "q95":sorted_quantile(values,0.95),
        "seed_sd":statistics.stdev(values),
        "descriptive_mc_se":statistics.stdev(values)/math.sqrt(len(values)),
    }


def study_positive_keys(survey_rows,site_rows,species,cohort):
    if cohort=="published_q1":
        ids={r["site"] for r in site_rows} - {"kis-banyato","vadasz-turjan"}
        expected=27
    elif cohort=="published_q2":
        ids={r["site"] for r in site_rows if r["ci"]=="intervention"}
        expected=13
    else: raise ValueError("unrecognized original analysis cohort")
    if len(ids)!=expected:
        raise ValueError("original field study site inclusion changed")
    raw=[r for r in survey_rows if r["site"] in ids]
    raw_by_site=defaultdict(list)
    for r in raw: raw_by_site[r["site"]].append(r)
    out={}
    for site in sorted(ids):
        for sp in species:
            k=sum(int(r[sp])>0 for r in raw_by_site[site])
            if k:
                out[(site,sp)]={
                    "raw_row_n":len(raw_by_site[site]),
                    "raw_positive_row_k":k,
                    "exact_seed_risk":prob_all_native_positives_dropped(len(raw_by_site[site]),k),
                }
    if len(out)!=EXPECTED_POS[cohort]:
        raise ValueError("raw source positive-site-species roster drift")
    exact_sum=sum(z["exact_seed_risk"] for z in out.values())
    if abs(exact_sum-EXPECTED_EXACT_MEANS[cohort])>1e-10:
        raise ValueError("original exact resampling risk changed")
    return out


def validate_and_summarize(summary_rows,pair_rows,survey_rows,site_rows,species):
    summary_by_seed={}
    for r in summary_rows:
        seed=int(r["seed"])
        if seed not in SEEDS or seed in summary_by_seed:
            raise ValueError("seed outside fixed 1..256 roster or duplicate")
        summary_by_seed[seed]={k:int(v) for k,v in r.items()}
    if set(summary_by_seed)!=set(SEEDS):
        raise ValueError("seed ensemble missing seed or added unregistered seed")

    truth={cohort:study_positive_keys(survey_rows,site_rows,species,cohort) for cohort in COHORTS}
    # No statistical independence assumption: every R row is one algorithmic
    # pseudo-observation originating from a known native CSV row.
    records=defaultdict(dict)
    for r in pair_rows:
        cohort=r["cohort"]; seed=int(r["seed"])
        key=(r["site"],r["species"])
        if cohort not in COHORTS or seed not in SEEDS or key not in truth[cohort]:
            raise ValueError("synthetic retained label not attached to authentic source-positive pair")
        val=int(r["retained_after_sampling"])
        if val not in (0,1) or key in records[(cohort,seed)]:
            raise ValueError("nonbinary or duplicate pseudo-detection label")
        records[(cohort,seed)][key]=val
    if len(pair_rows)!=256*(144+77) or len(records)!=512:
        raise ValueError("source×seed×species detail count drift")

    q2_common=set(truth["published_q2"])
    per_seed={cohort:[] for cohort in COHORTS}
    disagreement=[]
    per_pair_loss=defaultdict(list)
    for seed in SEEDS:
        s=summary_by_seed[seed]
        for cohort in COHORTS:
            d=records[(cohort,seed)]
            if set(d)!=set(truth[cohort]):
                raise ValueError("source-positive pair incomplete or extra in a seed")
            loss=sum(v==0 for v in d.values())
            q="q1" if cohort=="published_q1" else "q2"
            if s[f"{q}_lost_positive_site_species"]!=loss:
                raise ValueError("R and independent Python loss sums do not agree")
            if s[f"{q}_distinct_original_rows"]+s[f"{q}_repeated_row_positions"]!=(540 if q=="q1" else 260):
                raise ValueError("source row repetition decomposition inconsistent")
            per_seed[cohort].append(loss)
            for key,v in d.items(): per_pair_loss[(cohort,key)].append(1-v)
        q1=records[("published_q1",seed)]
        q2=records[("published_q2",seed)]
        overlap=sum(q1[k]!=q2[k] for k in q2_common)
        if overlap != s["overlap_pseudo_detection_disagreements"]:
            raise ValueError("cross-cohort same-native-source disagreement mismatch")
        q1shared=sum(q1[k]==0 for k in q2_common)
        if q1shared != s["q1_lost_among_shared13"]:
            raise ValueError("Q1 overlap loss mismatch")
        disagreement.append(overlap)

    s123=summary_by_seed[123]
    if (
        s123["q1_lost_positive_site_species"]!=3 or
        s123["q2_lost_positive_site_species"]!=6 or
        s123["q1_distinct_original_rows"]!=287 or
        s123["q2_distinct_original_rows"]!=153 or
        s123["overlap_pseudo_detection_disagreements"]!=7
    ):
        raise ValueError("original authenticated seed123 run not reproduced")

    cohorts={}
    for cohort in COHORTS:
        vals=per_seed[cohort]
        info=describe_seed_values(vals)
        info["exact_expected_lost_native_positive_site_species"]=EXPECTED_EXACT_MEANS[cohort]
        info["empirical_minus_exact_expected_lost"]=info["mean"]-EXPECTED_EXACT_MEANS[cohort]
        info["seed_count_with_any_positive_loss"]=sum(z>0 for z in vals)
        info["seed_count_with_zero_positive_loss"]=sum(z==0 for z in vals)
        freq=[]
        for key,data in sorted(truth[cohort].items()):
            nloss=sum(per_pair_loss[(cohort,key)])
            freq.append({
                "site":key[0],"species":key[1],
                "n_native_rows":data["raw_row_n"],"k_native_positive_rows":data["raw_positive_row_k"],
                "exact_conditional_drop_probability":data["exact_seed_risk"],
                "empirical_drop_frequency_256_seeds":nloss/len(SEEDS),
                "seeds_where_dropped":nloss,
            })
        info["per_pair_frequencies"]=freq
        info["top_exact_risk_pairs"]=sorted(
            freq,key=lambda x:(-x["exact_conditional_drop_probability"],x["site"],x["species"])
        )[:12]
        info["top_empirical_drop_pairs"]=sorted(
            freq,key=lambda x:(-x["seeds_where_dropped"],x["site"],x["species"])
        )[:12]
        cohorts[cohort]=info

    return {
        "schema":"eog.wetland_seed_ensemble_v1.result",
        "status":"PINNED_R_SEED_ROSTER_ALGORITHM_SENSITIVITY_NOT_BIOLOGICAL_REPLICATION",
        "source_sha256":{"survey":SURVEY_SHA,"sites":SITE_SHA},
        "seed_roster":[1,256],"seed_count":256,"includes_seed123":True,
        "R_kind":"R 4.4.3; Mersenne-Twister; Inversion; Rejection",
        "verified_historical_installation":False,
        "original_occupancy_model_fitted":False,
        "cohorts":cohorts,
        "paired_same_13_native_sites":{
            "disagreement_across_256_fixed_seed_paired_q1_q2_processes":describe_seed_values(disagreement),
            "seeds_with_any_pseudo_detection_disagreement":sum(z>0 for z in disagreement),
            "seed123_disagreements":7,
            "shared_native_positive_site_species":len(q2_common),
        },
        "limitations":[
            "Seed roster is a fixed post-exposure algorithmic sensitivity; seeds are NOT independent biological replicates.",
            "Empirical seed ranges are descriptive Monte Carlo processing variability, not a field population CI.",
            "Expected-loss values are analytic under public pinned survreps, not original historical realized occupancy outputs.",
            "Physical trap identity/effort and seasonal closure remain unverified; row copies are not extra field visits.",
            "Nothing in this run identifies causal abiotic A, biotic B, movement M or changes the frozen EOG-WF predictive endpoints."
        ]
    }


def run(survey_file,site_file,summary_file,pair_file):
    if hashlib.sha256(Path(survey_file).read_bytes()).hexdigest()!=SURVEY_SHA:
        raise ValueError("source surveys SHA mismatch")
    if hashlib.sha256(Path(site_file).read_bytes()).hexdigest()!=SITE_SHA:
        raise ValueError("source site SHA mismatch")
    surveys,cols=read_csv(survey_file); sites,_=read_csv(site_file)
    species=[z for z in cols if z not in META]
    if len(species)!=9 or len(surveys)!=381 or len(sites)!=29:
        raise ValueError("native source dimensions differ")
    summary_rows,_=read_csv(summary_file)
    pair_rows,_=read_csv(pair_file)
    out=validate_and_summarize(summary_rows,pair_rows,surveys,sites,species)
    out["source_artifact_checksums"]={
        "summary_csv_sha256":hashlib.sha256(Path(summary_file).read_bytes()).hexdigest(),
        "native_positive_pair_csv_sha256":hashlib.sha256(Path(pair_file).read_bytes()).hexdigest(),
    }
    out["fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--summary",required=True,type=Path)
    p.add_argument("--pairs",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    result=run(a.surveys,a.sites,a.summary,a.pairs)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("WETLAND_SEED_ENSEMBLE_RESULT="+json.dumps({
        "fingerprint":result["fingerprint"],"seeds":result["seed_count"],
        "cohorts":{k:{
            "mean":v["mean"],"median":v["median"],"range":[v["min"],v["max"]],
            "q05_95":[v["q05"],v["q95"]],
            "exact_expected":v["exact_expected_lost_native_positive_site_species"],
            "zero_loss_seeds":v["seed_count_with_zero_positive_loss"]
        }for k,v in result["cohorts"].items()},
        "paired_disagreement_mean":result["paired_same_13_native_sites"][
            "disagreement_across_256_fixed_seed_paired_q1_q2_processes"]["mean"]
    },sort_keys=True))
