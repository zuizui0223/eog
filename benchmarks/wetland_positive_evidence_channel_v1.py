"""Source-anchored positive-evidence audit of 256 original R preprocessing seeds.

This is a post-exposure observation-channel diagnostic, not a new EOG
predictive endpoint. A pseudo-zero cannot override a native-source positive.
EOG's finite-world universe is NOT estimated or fitted here.
"""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SURVEY_SHA = "45146ee7a97c8086a53d13c3f19a060b51fe2ca1a42cb1aa9c42bbac67877ddd"
SITE_SHA = "93064521563b04d8c264639463abf9806eea7aa34f502d7d45bedd42ebec0319"
PAIR_SHA = "3ba582b5fbbdaa0e6c6f89cb70bb640cba9e56e50bc0ca187a223f81c0a45ae6"
SUMMARY_SHA = "0ed9b0f74ea4da5580a35ddfeada709cc6dfac5804bb1a9c916a71dd7b16b7cd"
META = {"doy","surv","site","date","method","num","0","year","month","temp","humid","prec"}
COHORTS = ("published_q1","published_q2")
SEEDS = tuple(range(1,257))
EXPECTED = {"published_q1": (27,144),"published_q2":(13,77)}


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        reader=csv.DictReader(handle)
        return list(reader), list(reader.fieldnames)


def check_sha(path, expected, label):
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if actual!=expected:
        raise ValueError(f"{label} SHA256 changed: {actual}")


def native_positive_keys(survey_rows, site_rows, species, cohort):
    if cohort=="published_q1":
        active={r["site"] for r in site_rows}-{"kis-banyato","vadasz-turjan"}
    elif cohort=="published_q2":
        active={r["site"] for r in site_rows if r["ci"]=="intervention"}
    else:
        raise ValueError("unexpected cohort")
    expected_sites,npositive=EXPECTED[cohort]
    if len(active)!=expected_sites:
        raise ValueError("published site roster changed")
    out={(r["site"],sp) for r in survey_rows if r["site"] in active
         for sp in species if int(r[sp])>0}
    if len(out)!=npositive:
        raise ValueError("native positive pairs changed")
    return out


def world_is_positive_compatible(world_positive, observed_positive):
    """Unit-testable EOG positive-only algebra; no empirical world construction.

    For a FIXED world universe with fixed source definitions, rules and
    positive-support masks, a world is admissible when every recorded
    positive is supported. A self-excluded-source reconstruction, in which
    observed occurrences also redefine the sources, is NOT certified by
    this monotonicity lemma.
    """
    return set(observed_positive).issubset(set(world_positive))


def reconcile(source_sets, pair_rows, summary_rows):
    if set(source_sets)!=set(COHORTS):
        raise ValueError("exact Q1/Q2 original source cohorts required")
    pair_by_cohort_seed=defaultdict(dict)
    for row in pair_rows:
        cohort=row["cohort"]
        try:
            seed=int(row["seed"])
            indicator=int(row["retained_after_sampling"])
        except (ValueError,TypeError,KeyError) as exc:
            raise ValueError("invalid seed or binary indicator") from exc
        pair=(row["site"],row["species"])
        if cohort not in COHORTS or seed not in SEEDS:
            raise ValueError("outside frozen cohort or seed roster")
        if pair not in source_sets[cohort]:
            raise ValueError("pseudo-positive table includes non-source-positive key")
        if indicator not in (0,1) or pair in pair_by_cohort_seed[(cohort,seed)]:
            raise ValueError("duplicate or invalid indicator")
        pair_by_cohort_seed[(cohort,seed)][pair]=indicator
    if len(pair_rows)!=len(SEEDS)*sum(len(v) for v in source_sets.values()) or len(pair_by_cohort_seed)!=2*len(SEEDS):
        raise ValueError("incomplete source×seed×positive pair table")

    by_cohort_seed_summary=defaultdict(dict)
    for row in summary_rows:
        try:
            seed=int(row["seed"])
        except (ValueError,TypeError,KeyError) as exc:
            raise ValueError("invalid seed in summary") from exc
        if seed not in SEEDS or seed in by_cohort_seed_summary:
            raise ValueError("summary seed missing, duplicate or out of frozen roster")
        by_cohort_seed_summary[seed]=row
    if set(by_cohort_seed_summary)!=set(SEEDS):
        raise ValueError("summary does not cover exactly 1..256")

    outcome={}
    for cohort in COHORTS:
        raw=source_sets[cohort]
        source_count=len(raw)
        retained_by_seed={}
        lost_by_seed={}
        for seed in SEEDS:
            indicators=pair_by_cohort_seed[(cohort,seed)]
            if set(indicators)!=raw:
                raise ValueError("seed table does not cover all source positive keys")
            sampled={k for k,v in indicators.items() if v==1}
            if not sampled<=raw:
                raise ValueError("resampling fabricated an unsupported source positive")
            missing=raw-sampled
            if (sampled | missing)!=raw or sampled & missing:
                raise ValueError("source-positive evidence reconciliation invariant violated")
            q="q1" if cohort=="published_q1" else "q2"
            if len(missing)!=int(by_cohort_seed_summary[seed][f"{q}_lost_positive_site_species"]):
                raise ValueError("source-positive loss count disagrees with original R")
            retained_by_seed[seed]=sampled
            lost_by_seed[seed]=missing
        persistent=set.intersection(*(retained_by_seed[s] for s in SEEDS))
        union=set.union(*(retained_by_seed[s] for s in SEEDS))
        ever_lost=raw-persistent
        never_retained=raw-union
        variable=ever_lost-never_retained
        if persistent|variable|never_retained!=raw:
            raise ValueError("source evidence partition failed")
        by_species=defaultdict(list)
        for (site,sp) in sorted(raw):
            frequency=sum((site,sp) in lost_by_seed[s] for s in SEEDS)
            by_species[sp].append({"site":site,"lost_seeds":frequency,
                                  "lost_rate_256":frequency/256})
        taxa={}
        for sp,rows in sorted(by_species.items()):
            total_lost=sum(z["lost_seeds"] for z in rows)
            taxa[sp]={
                "native_positive_site_count":len(rows),
                "mean_seed_loss_rate_over_source_positive_sites":total_lost/(256*len(rows)),
                "always_retained_256_seed_sites":sum(z["lost_seeds"]==0 for z in rows),
                "variable_256_seed_sites":sum(0<z["lost_seeds"]<256 for z in rows),
                "never_retained_256_seed_sites":sum(z["lost_seeds"]==256 for z in rows)
            }
        per_seed=[{
            "seed":seed,
            "source_positive_pair_count":source_count,
            "processed_positive_pair_count":len(retained_by_seed[seed]),
            "omitted_native_positive_count":len(lost_by_seed[seed]),
            "source_recovered_positive_count":len(retained_by_seed[seed]|lost_by_seed[seed]),
            "potential_false_absence_contradictions_if_zeros_are_called_true_absence":len(lost_by_seed[seed]),
            "positive_only_compatibility_direction":"source_W_subseteq_sampled_W"
        } for seed in SEEDS]
        result={
            "source_positive_site_species_pairs":source_count,
            "retained_at_every_one_of_256_seeds":len(persistent),
            "variable_between_256_seed_inputs":len(variable),
            "omitted_at_all_256_seeds":len(never_retained),
            "omitted_at_least_once":len(ever_lost),
            "union_of_256_sampled_positive_pairs":len(union),
            "source_recovered_union_count":source_count,
            "source_positive_always_preserved_after_reconciliation":True,
            "max_potential_false_absence_contradictions":max(len(lost_by_seed[s]) for s in SEEDS),
            "seeds_with_any_native_positive_omission":sum(bool(lost_by_seed[s]) for s in SEEDS),
            "per_seed":per_seed,
            "by_species":taxa,
            "per_pair_seed_loss_frequency":[{
                "site":site,"species":sp,
                "loss_count":sum((site,sp) in lost_by_seed[s] for s in SEEDS)
            } for site,sp in sorted(raw)]
        }
        outcome[cohort]=result
    if not source_sets["published_q2"]<=source_sets["published_q1"]:
        raise ValueError("native Q2 source-positive evidence is not nested in Q1")
    return {
        "schema":"eog.wetland_positive_evidence_channel_v1.result",
        "status":"SOURCE_ANCHORED_POSITIVE_ONLY_MONOTONICITY_VERIFIED",
        "role":"POST_EXPOSURE_ANALYTICAL_OBSERVATION_CHANNEL_NOT_BIOLOGICAL_WORLD_RECONSTRUCTION",
        "cohorts":outcome,
        "finite_world_statement":{
            "given":"Any fixed declared world universe U with unchanged world-specific positive-support masks, source definitions and rules; source-confirmed positive O and resampled positive S subset of O",
            "positive_only_order":"W(O) subseteq W(S) for all 256 source-validated seeds",
            "reconciliation":"S union (O minus S) == O; restoring source positives returns W(O)",
            "not_inferred":"No actual count of ecological finite compatible worlds; zeros are not proven absences; monotonicity is not certified for self-excluded source policies that change the world support when the observed set changes",
            "if_untrusted_zero_is_misread_as_absence":"Each omitted source-positive pair creates a direct observation contradiction, not a verified count of excluded true ecological worlds"
        },
        "boundaries":[
            "All 256 seeds are processing choices and not field/ecological repetitions.",
            "The 256-seed intersection is not guaranteed to remain positive at other untested seeds.",
            "The union of 256 pseudo-observations is not a substitute for authentic source evidence.",
            "The world-set inclusion claim assumes fixed support masks and sources; it must not be applied when an evidence-dependent source policy changes world reachability.",
            "Original physical independent trap IDs, effort and seasonal closure are not identified.",
            "No ecological state, true absence, BAM axes, movement or EOG-WF scored endpoint was estimated.",
            "Original R/hunviphab installation at the authors' run is not certified."
        ]
    }


def run(survey_path,site_path,pair_path,summary_path):
    for label,p,sha in (
        ("survey",survey_path,SURVEY_SHA),
        ("sites",site_path,SITE_SHA),
        ("positive_pair_seeds",pair_path,PAIR_SHA),
        ("seed_summary",summary_path,SUMMARY_SHA)
    ):
        check_sha(p,sha,label)
    survey,columns=read_csv(survey_path)
    sites,_=read_csv(site_path)
    pairs,_=read_csv(pair_path)
    summaries,_=read_csv(summary_path)
    species=[s for s in columns if s not in META]
    if (len(survey),len(sites),len(species))!=(381,29,9):
        raise ValueError("original source dimensions changed")
    sources={c:native_positive_keys(survey,sites,species,c) for c in COHORTS}
    out=reconcile(sources,pairs,summaries)
    out["source_sha256"]={"surveys":SURVEY_SHA,"sites":SITE_SHA,
                          "seed_ensemble_pairs":PAIR_SHA,"seed_ensemble_summary":SUMMARY_SHA}
    out["fingerprint"]=hashlib.sha256(json.dumps(out,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--surveys",required=True,type=Path)
    p.add_argument("--sites",required=True,type=Path)
    p.add_argument("--pairs",required=True,type=Path)
    p.add_argument("--summary",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    out=run(a.surveys,a.sites,a.pairs,a.summary)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print("WETLAND_POSITIVE_CHANNEL="+json.dumps({
        "status":out["status"],"fingerprint":out["fingerprint"],
        "cohorts":{k:{
            "source_positive":v["source_positive_site_species_pairs"],
            "core_in_all_256":v["retained_at_every_one_of_256_seeds"],
            "variable":v["variable_between_256_seed_inputs"],
            "never_retained":v["omitted_at_all_256_seeds"],
            "seeds_with_loss":v["seeds_with_any_native_positive_omission"],
            "top_sensitive_species":sorted(v["by_species"],key=lambda s:
                -v["by_species"][s]["mean_seed_loss_rate_over_source_positive_sites"])[:3]
        }for k,v in out["cohorts"].items()}
    },sort_keys=True))
