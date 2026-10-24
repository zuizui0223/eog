#!/usr/bin/env python3
"""Post-exposure, source-verified v44 *observation opportunity vs diagnosticity* audit.

Only inspects archived v44 18,432-row aggregate scenario CSV and result JSON;
does NOT simulate new worlds, alter a source network, score empirical field
endpoints, read real bird records, or generate a new EOG-WF predictor.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"validation/eog_original_idea_source_opportunity_v45/protocol_v45.json"
V44_FROZEN=ROOT/"validation/eog_original_idea_asof_time_source_v44/result_frozen_v44.json"
EPS=1e-9
SCHEMA="eog.original_idea.cutoff_opportunity_target_diagnosticity.audit_result.v45"
LEVELS=("target_known_from_cutoff","target_uncertain_no_available_tag",
        "target_uncertain_available_tag_not_diagnostic",
        "target_uncertain_available_tag_diagnostic")
SOURCE_COLS=(
    "design_key","source_geometry","panel","cutoff_time",
    "future_target_time","target","policy",
    "target_ambiguous_from_cutoff_occupancy",
    "baseline_target_conditional_entropy_bits",
    "baseline_target_bayes_accuracy",
    "added_source_information_bits",
    "added_target_bayes_accuracy_gain",
    "perfect_cutoff_tag_information_bits",
    "perfect_cutoff_tag_accuracy_gain",
    "mean_nominal_selected_sites",
    "mean_cutoff_occupied_selected_sites",
)
NUMERIC_FIELDS=(
    "baseline_target_conditional_entropy_bits",
    "baseline_target_bayes_accuracy",
    "added_source_information_bits",
    "added_target_bayes_accuracy_gain",
    "perfect_cutoff_tag_information_bits",
    "perfect_cutoff_tag_accuracy_gain",
    "mean_nominal_selected_sites",
    "mean_cutoff_occupied_selected_sites",
)
PRIOR="validation/eog_original_idea_asof_time_source_v44/result_frozen_v44.json"


def _canonical(x):
    return json.dumps(x,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf-8")


def verify_protocol(p:dict,frozen:dict)->None:
    if (p.get("schema")!="eog.original_idea.cutoff_source_opportunity_diagnosticity.audit_protocol.v45"
        or p.get("status")!="POSTEXPOSURE_V44_SOURCE_ONLY_DIAGNOSTIC__CLASSIFICATIONS_FROZEN_BEFORE_REPLAY"):
        raise ValueError("v45 postexposure audit protocol identity changed")
    src=p.get("source",{})
    source_fields={
        "repo_main_commit":"98d655741def5d2f4f3b0e4e86617fbc5b855ab8",
        "v44_frozen_receipt":PRIOR,
        "v44_actions_run_id":39452406392,
        "original_artifact_id":12279172589,
        "original_csv_sha256":"5f7ca0e158f23cc9d479bdb51539458bf6ce4da3dced11a64bd310e80aee5b8e",
    }
    # The source metadata key is "original_per_world_csv_sha256", not a
    # newly guessed alias: all exact identities must match the frozen receipt.
    for field,wanted in source_fields.items():
        key="original_per_world_csv_sha256" if field=="original_csv_sha256" else field
        if src.get(key)!=wanted:
            raise ValueError("Archived original v44 source identity changed: "+key)
    if (src.get("original_canonical_result_json_sha256") !=
        frozen["authority"]["full_canonical_result_sha256"]
        or src.get("original_zip_sha256")!=frozen["authority"]["artifact_zip_sha256"]
        or src.get("physical_rows")!=18432
        or frozen["population"]["unique_world_panel_target_policy_rows"]!=18432
        or frozen["population"]["base_worlds"]!=768):
        raise ValueError("Archived 18,432-row integrity provenance changed")
    checks=p.get("fixed_diagnostic_rules",{})
    if not (
        checks.get("available_at_cutoff")==
        "mean_cutoff_occupied_selected_sites > 1e-9; this is nonzero EXPECTED occupancy of at least one selected site over latent 3-history prior, not actual observation of a tag"
        and checks.get("informative_for_target")==
        "added_source_information_bits > 1e-9 under original v44 q=0.60/e=0.10 noisy tag likelihood, conditional on cutoff occupancy"
        and checks.get("classes")==list(LEVELS)
        and checks.get("no_new_samples_likelihood_or_worlds") is True
        and checks.get("fail_closed_if_informative_but_no_available_tag") is True
        and p["interpretation_and_stop"]["post_v44_counts_exposed_before_this_protocol"] is True
        and p["interpretation_and_stop"]["no_new_EOG_WF_scored_endpoint"] is True
    ):
        raise ValueError("Fixed opportunity/diagnosticity semantics or scope altered")


def load_authenticated_source(source:Path,p:dict)->tuple[list[dict],dict]:
    """Accept exact original artifact ZIP or its officially extracted contents."""
    file_names=("per_world_asof_v44.csv","result_v44.json")
    if source.is_file() and zipfile.is_zipfile(source):
        blob=source.read_bytes()
        if hashlib.sha256(blob).hexdigest()!=p["source"]["original_zip_sha256"]:
            raise ValueError("Source artifact ZIP SHA256 mismatch")
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            if set(z.namelist())!=set(file_names):
                raise ValueError("Unexpected archived original artifact files")
            contents={name:z.read(name) for name in file_names}
    elif source.is_dir():
        contents={name:(source/name).read_bytes() for name in file_names}
    else:
        raise ValueError("Use verified original artifact ZIP or official extracted directory")
    actual_csv=hashlib.sha256(contents[file_names[0]]).hexdigest()
    if actual_csv!=p["source"]["original_per_world_csv_sha256"]:
        raise ValueError("Original source CSV byte SHA256 mismatch")
    original=json.loads(contents[file_names[1]].decode("utf-8"))
    if (hashlib.sha256(_canonical(original)).hexdigest()!=
        p["source"]["original_canonical_result_json_sha256"]):
        raise ValueError("Original full 18,432-row result canonical SHA256 mismatch")
    with io.StringIO(contents[file_names[0]].decode("utf-8"),newline="") as stream:
        reader=csv.DictReader(stream)
        if tuple(reader.fieldnames or ())!=SOURCE_COLS:
            raise ValueError("Original exact per-world grain/header changed")
        rows=list(reader)
    return rows,original


def classify(row:dict)->str:
    ambiguous=row["target_ambiguous_from_cutoff_occupancy"]
    if ambiguous not in ("True","False"):
        raise ValueError("Cutoff target ambiguity must be literal True/False")
    entropy=float(row["baseline_target_conditional_entropy_bits"])
    mi=float(row["added_source_information_bits"])
    occupied=float(row["mean_cutoff_occupied_selected_sites"])
    nominal=float(row["mean_nominal_selected_sites"])
    if not all(math.isfinite(float(row[k])) for k in NUMERIC_FIELDS):
        raise ValueError("Numeric source value is nonfinite")
    if min(mi,occupied,nominal,entropy)<-EPS or occupied>nominal+EPS or nominal>3+EPS:
        raise ValueError("Impossible opportunity/census budget or negative MI")
    if ambiguous=="False":
        if entropy>EPS or mi>EPS:
            raise ValueError("Target known from cutoff but source label changed it")
        return LEVELS[0]
    if entropy<=EPS:
        raise ValueError("Ambiguous target with zero baseline conditional entropy")
    if occupied<=EPS:
        if mi>EPS:
            raise ValueError("No selected site cutoff-occupied yet positive tag MI")
        return LEVELS[1]
    if mi<=EPS:
        return LEVELS[2]
    return LEVELS[3]


def _mean(rows: list[dict],field:str)->float|None:
    return sum(float(r[field]) for r in rows)/len(rows) if rows else None


def summarize(rows: list[dict], panel:str,target:str,policy:str,
              geometry:str)->dict:
    sample=[r for r in rows if r["panel"]==panel and
            r["target"]==target and r["policy"]==policy and
            (geometry=="all_geometries" or r["source_geometry"]==geometry)]
    cls=Counter(classify(r) for r in sample)
    n=len(sample)
    uncertain=[r for r in sample if r["target_ambiguous_from_cutoff_occupancy"]=="True"]
    available=[r for r in uncertain if float(r["mean_cutoff_occupied_selected_sites"])>EPS]
    info=[r for r in available if float(r["added_source_information_bits"])>EPS]
    return {
        "panel":panel,"target":target,"policy":policy,"source_geometry":geometry,
        "n_worlds":n,
        "n_target_uncertain":len(uncertain),
        "n_target_known":cls[LEVELS[0]],
        "n_target_uncertain_no_tag_opportunity":cls[LEVELS[1]],
        "n_target_uncertain_tag_opportunity_but_no_information":cls[LEVELS[2]],
        "n_target_uncertain_tag_opportunity_with_information":cls[LEVELS[3]],
        "n_tag_opportunity_given_target_uncertain":len(available),
        "opportunity_fraction_of_target_uncertain":(
            len(available)/len(uncertain) if uncertain else None),
        "target_diagnostic_fraction_given_tag_opportunity":(
            len(info)/len(available) if available else None),
        "mean_tag_MI_bits_over_target_uncertain":_mean(uncertain,"added_source_information_bits"),
        "mean_tag_MI_bits_given_tag_opportunity":_mean(available,"added_source_information_bits"),
        "mean_expected_cutoff_occupied_sites_over_target_uncertain":
            _mean(uncertain,"mean_cutoff_occupied_selected_sites"),
        "mean_nominal_sites_over_target_uncertain":
            _mean(uncertain,"mean_nominal_selected_sites"),
        "mean_tag_bayes_correct_target_gain_over_target_uncertain":
            _mean(uncertain,"added_target_bayes_accuracy_gain"),
    }


def audit(rows:list[dict],original:dict,p:dict)->dict:
    if (len(rows)!=18432 or original["populations"]["world_panel_target_policy_rows"]!=18432):
        raise ValueError("Original v44 source row census is incomplete")
    src=p["source"]
    panels=src["panels"]
    targets=src["target_names"]
    policies=src["policy_names"]
    geometries=src["source_geometries"]
    keyset=set()
    worldset=set()
    original_agg={
        (x["panel"],x["target"],x["policy"],x["subset"]):x
        for x in original["summary_by_panel_target_policy"]
    }
    if len(original_agg)!=len(original["summary_by_panel_target_policy"])!=48:
        raise ValueError("Source v44 summary grain duplicates or missing")
    for row in rows:
        key=tuple(row[k] for k in ("design_key","panel","target","policy"))
        if key in keyset:
            raise ValueError("Duplicate source world/panel/target/policy")
        keyset.add(key)
        worldset.add(row["design_key"])
        if (row["panel"] not in panels or row["target"] not in targets or
            row["policy"] not in policies or row["source_geometry"] not in geometries or
            not row["design_key"].endswith("|"+row["source_geometry"])):
            raise ValueError("Unrecognized original panel/policy, source geometry, or key")
        if int(row["future_target_time"])<=int(row["cutoff_time"]):
            raise ValueError("Source v44 future target at/before cutoff")
        classify(row)
    if len(worldset)!=768:
        raise ValueError("Base landscape/source geometry 768 universe changed")
    records=[]
    for panel in panels:
        for target in targets:
            for policy in policies:
                for geometry in ("all_geometries",*geometries):
                    z=summarize(rows,panel,target,policy,geometry)
                    if z["n_worlds"]!=(768 if geometry=="all_geometries" else 384):
                        raise ValueError("Missing fixed world/scenario stratum")
                    if (z["n_target_known"]+
                        z["n_target_uncertain_no_tag_opportunity"]+
                        z["n_target_uncertain_tag_opportunity_but_no_information"]+
                        z["n_target_uncertain_tag_opportunity_with_information"]!=
                        z["n_worlds"]):
                        raise ValueError("Four classifications do not partition source rows")
                    if geometry=="all_geometries":
                        parent=original_agg[(panel,target,policy,"target_ambiguous")]
                        if (z["n_target_uncertain"]!=parent["n_world_designs"] or
                            z["n_target_uncertain_tag_opportunity_with_information"]!=
                            parent["worlds_with_positive_source_info"]):
                            raise ValueError("Published v44 target-uncertain denominators drifted")
                        if z["n_target_uncertain"]:
                            if (abs(z["mean_tag_MI_bits_over_target_uncertain"]-
                                    parent["mean_added_source_information_bits"])>1e-10 or
                                abs(z["mean_expected_cutoff_occupied_sites_over_target_uncertain"]-
                                    parent["mean_mean_cutoff_occupied_selected_sites"])>1e-10):
                                raise ValueError("Original v44 numeric conditional MI/site means differ")
                    records.append(z)
    def result(panel,target,policy,geometry="all_geometries"):
        return next(z for z in records if (z["panel"],z["target"],z["policy"],
                                      z["source_geometry"])==(panel,target,policy,geometry))
    primary={
        policy:result("primary_early","persistent_threshold_lag2",policy)
        for policy in policies
    }
    near={
        policy:result("secondary_near","persistent_threshold_lag2",policy)
        for policy in policies
    }
    if (primary["cutoff_occupied_confluence_top3"]["n_target_uncertain"]!=126 or
        primary["cutoff_occupied_confluence_top3"]["n_target_uncertain_tag_opportunity_with_information"]!=8 or
        near["cutoff_occupied_confluence_top3"]["n_target_uncertain"]!=59 or
        near["cutoff_occupied_confluence_top3"]["n_target_uncertain_tag_opportunity_with_information"]!=51):
        raise ValueError("Original frozen v44 126/8/59/51 scientific denominators changed")
    return {
        "schema":SCHEMA,
        "status":"POST_EXPOSURE_AUTHENTICATED_18K_SOURCE_OPPORTUNITY_VS_TARGET_DIAGNOSTICITY__NO_NEW_ENDPOINT",
        "source":{
            "original_v44_actions_run_id":src["v44_actions_run_id"],
            "original_artifact_id":src["original_artifact_id"],
            "original_per_world_csv_sha256":src["original_per_world_csv_sha256"],
            "original_complete_result_canonical_sha256":
                src["original_canonical_result_json_sha256"],
            "source_grain_unique":True,
            "rows_exact":len(rows),
            "base_worlds_exact":len(worldset),
            "no_new_source_data_or_model_fits":True,
        },
        "audit_rules":{
            "opportunity":"expected selected-site occupancy > 1e-9 among true-current occupancy candidates",
            "information":"original v44 target-conditional noisy source MI > 1e-9",
            "warning":"Opportunity is potential cutoff availability under a known-history candidate model, NOT an observed tag, detection probability or actual genetic sample",
        },
        "n_summary_groups":len(records),
        "primary_early_t2_future_t5_maturity":primary,
        "secondary_near_t4_future_t5_maturity":near,
        "primary_geometry_cutoff_aware":{
            geometry:result("primary_early","persistent_threshold_lag2",
                            "cutoff_occupied_confluence_top3",geometry)
            for geometry in geometries
        },
        "summary_all_original_panel_targets_and_policies":records,
        "scientific_boundaries":p["interpretation_and_stop"]
    }


def run(source:Path)->dict:
    p=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    frozen=json.loads(V44_FROZEN.read_text(encoding="utf-8"))
    verify_protocol(p,frozen)
    records,original=load_authenticated_source(source,p)
    return audit(records,original,p)


def main()->None:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source",type=Path,required=True,
                     help="verified original v44 Actions ZIP or downloaded artifact directory")
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite existing postexposure audit receipt")
    outcome=run(args.source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(outcome,indent=2,sort_keys=True,
                           ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    p=outcome["primary_early_t2_future_t5_maturity"]
    print(json.dumps({
        "status":outcome["status"],
        "primary":{k:{
            "uncertain":v["n_target_uncertain"],
            "opportunity":v["n_tag_opportunity_given_target_uncertain"],
            "diagnostic":v["n_target_uncertain_tag_opportunity_with_information"],
        } for k,v in p.items()},
        "source_validated":True,"new_ecological_endpoint":False,
    },ensure_ascii=False))


if __name__=="__main__":
    main()
