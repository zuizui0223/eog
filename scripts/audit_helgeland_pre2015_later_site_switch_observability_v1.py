#!/usr/bin/env python3
"""Exploratory later positive site-code detection after FIRST direct followup.

This rechecks the already frozen pre-2015 first-encounter counts before any
additional outcomes. All ID/site/stage values after 2014 are masked by DATE
prior to inspection. Original Year, derived ages/sex, genetic, inferred
locations and 2015-2022 destinations are never consulted or emitted.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date
import json
from pathlib import Path
from typing import Iterable, Mapping

from audit_helgeland_pre2015_direct_site_code_switch_v1 import (
    BASE, PATH, strict_observed_date, verified_pre2015_qc
)
from audit_helgeland_2026_upstream_byte_parity_v1 import file_path

PROTOCOL=BASE/"helgeland_pre2015_later_site_switch_protocol_v1.json"
ORIGINAL_PROTOCOL=BASE/"helgeland_pre2015_direct_code_switch_protocol_v1.json"
PRIOR_RECEIPT=BASE/"helgeland_pre2015_first_direct_site_code_frozen_v1.json"
PRIOR_ANY_LATER_RECEIPT=BASE/"helgeland_pre2015_followup_horizon_observed_frozen_v1.json"
UPSTREAM_SHA="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
OUTPUT_SCHEMA="eog.helgeland.pre2015_later_site_switch_observability.v1"
STAGES=frozenset(("nest","capt","obs"))


def quality_check_policy(policy:dict)->None:
    if (policy.get("schema")!="eog.helgeland.pre2015_later_site_code_exposure.exploratory_v1"
        or policy.get("status")!="FROZEN_AFTER_FIRST_FOLLOWUP_COUNTS_EXPOSED_BEFORE_LATER_CODE_RESULTS"):
        raise ValueError("Not the preregistered post-exposure later-code protocol")
    source=policy["source"]
    if (source.get("doi")!="10.5061/dryad.rr4xgxdnq" or
        source.get("version_id")!=421942 or source.get("file_id")!=4576411 or
        source.get("upstream_commit")!=UPSTREAM_SHA or source.get("path")!=PATH or
        policy["window"]!=["1994-01-01","2014-12-31"]):
        raise ValueError("Changed original source, code or fixed observation dates")
    if policy["bounds"]!={
        "post_exposure_exploratory":True,
        "post2014_identity_never_read":True,
        "original_sha256_and_header_required":True,
        "output_no_individual_or_island_values":True,
        "code_change_not_natal_dispersal":True,
        "denominator_selection_by_detection":True,
        "observed_lag_not_true_movement_time":True,
        "surveyed_zero_verified":False,
        "2020_v8_actual_input_available":False,
        "site_code_crosswalk_verified":False,
        "heldout_scoring_authorized":False,
        "colonization_or_fitness_claim_authorized":False,
    }:
        raise ValueError("Source inference claim gates must stay frozen")


def group_later(dated_sites:list[tuple[date,str]],first_date:date,
                origin:str,looking_for_origin:bool)->tuple[str,int|None,bool]:
    later=defaultdict(set)
    for stamp,site in dated_sites:
        if stamp>first_date:
            later[stamp].add(site)
    ambiguous=any(len(sites)>1 for sites in later.values())
    matches=[stamp for stamp,sites in later.items()
             if len(sites)==1 and ((origin in sites)==looking_for_origin)]
    if matches:
        return "observed",min((t-first_date).days for t in matches),bool(later)
    if ambiguous:
        return "ambiguous",None,bool(later)
    return "not_observed",None,bool(later)


def reconcile_exposed_followup_counts(counts:dict,prior:dict)->None:
    """Require semantic agreement with already exposed PR #643 observations.

    PR #643 counted any different-code record, including same-day conflicts.
    This PR requires an unambiguous single site on a calendar day, so its
    observed and ambiguity-only subclasses must sum to the older count.
    Never force the stricter count alone to equal 228.
    """
    if (prior.get("schema")!="eog.helgeland.pre2015.followup_horizon.frozen_observed_v1"
        or prior.get("status")!="FOLLOWUP_WINDOW_SENSITIVITY_OBSERVED__ECOLOGICAL_HOLD"
        or prior.get("source",{}).get("source_bytes_and_firstline_independently_verified") is not True
        or prior.get("source",{}).get("calendar_cutoff")!="2014-12-31"):
        raise ValueError("Frozen PR643 receipt source or status invalid")
    old=prior["counts"]
    if not (
        counts["first_same_later_different"]+counts["first_same_later_ambiguous_only"]
            ==old["first_same_then_later_different_site_id_count"]
        and counts["first_same_later_no_different"]
            ==old["first_followup_same_never_observed_different_later_count"]
        and counts["first_changed_later_return"]
            <=old["first_different_then_later_source_site_id_count"]
        and counts["first_same_later_different"]+
            counts["first_same_later_ambiguous_only"]+
            counts["first_same_later_no_different"]
            ==old["first_followup_same_site_id_count"]
    ):
        raise ValueError("New strict-date classifications contradict exposed PR643 aggregates")


def inspect(records:Iterable[Mapping[str,str]],policy:dict)->dict:
    quality_check_policy(policy)
    old=policy["known_prior_counts"]
    counts={name:0 for name in policy["allowed_output"]}
    nest=defaultdict(list)
    follows=defaultdict(list)
    total=excluded_early=excluded_future=eligible=0
    lo=date(1994,1,1)
    hi=date(2014,12,31)
    for row in records:
        total+=1
        # Date is the *only* source field accessed if row is outside window.
        stamp=strict_observed_date(row["date"])
        if stamp<lo:
            excluded_early+=1
            continue
        if stamp>hi:
            excluded_future+=1
            continue
        eligible+=1
        ident=(row["ID"] or "").strip()
        island=(row["Island"] or "").strip()
        locality=(row["Location"] or "").strip()
        stage=(row["stage"] or "").strip()
        if not ident or not island or not locality or stage not in STAGES:
            raise ValueError("Bad original direct-encounter row")
        if stage=="nest":
            nest[ident].append((stamp,island))
        else:
            follows[ident].append((stamp,island))

    if not (total==old["total_rows"] and eligible==old["window_rows"] and
            excluded_early==old["prewindow"] and excluded_future==old["postwindow"]):
        raise ValueError("Observation date mask or original row total drifted")

    eligible_sources=first_same=first_different=first_ambiguous=no_followup=0
    for ident,nested in nest.items():
        codes={site for _,site in nested}
        if len(codes)!=1:
            continue
        eligible_sources+=1
        origin=next(iter(codes))
        first_nest=min(day for day,_ in nested)
        direct=[(day,site) for day,site in follows.get(ident,()) if day>first_nest]
        if not direct:
            no_followup+=1
            continue
        first_date=min(day for day,_ in direct)
        first_codes={site for day,site in direct if day==first_date}
        if len(first_codes)!=1:
            first_ambiguous+=1
            continue
        first_code=next(iter(first_codes))
        if first_code==origin:
            first_same+=1
            state,lag,additional=group_later(direct,first_date,origin,False)
            counts["first_same_with_additional_date" if additional
                   else "first_same_no_additional_date"]+=1
            if state=="observed":
                counts["first_same_later_different"]+=1
                if lag<=30: counts["lag_1_to_30_days"]+=1
                elif lag<=365: counts["lag_31_to_365_days"]+=1
                else: counts["lag_gt365_days"]+=1
            elif state=="ambiguous":
                counts["first_same_later_ambiguous_only"]+=1
            else:
                counts["first_same_later_no_different"]+=1
        else:
            first_different+=1
            state,_lag,_additional=group_later(direct,first_date,origin,True)
            if state=="observed": counts["first_changed_later_return"]+=1
            elif state=="ambiguous": counts["first_changed_later_ambiguous_only"]+=1
            else: counts["first_changed_later_no_return"]+=1

    if not (eligible_sources==old["nest_ids_unique"] and
            first_same==old["first_same"] and
            first_different==old["first_different"] and
            first_ambiguous==old["first_ambiguous"] and
            no_followup==old["no_followup"] and
            first_same+first_different+first_ambiguous==old["first_direct_followup_ids"]):
        raise ValueError("First-followup result fails frozen exact original reconciliation")
    if not (
        counts["first_same_no_additional_date"]+
        counts["first_same_with_additional_date"]==first_same and
        counts["first_same_later_different"]+
        counts["first_same_later_no_different"]+
        counts["first_same_later_ambiguous_only"]==first_same and
        counts["first_changed_later_return"]+
        counts["first_changed_later_no_return"]+
        counts["first_changed_later_ambiguous_only"]==first_different and
        counts["lag_1_to_30_days"]+
        counts["lag_31_to_365_days"]+
        counts["lag_gt365_days"]==counts["first_same_later_different"] and
        counts["first_same_later_different"]<=counts["first_same_with_additional_date"]):
        raise ValueError("Later observation categories do not partition first encounters")
    return {
        "schema":OUTPUT_SCHEMA,
        "status":"EXPLORATORY_PRE2015_LATER_DIFFERENT_SITE_CODE_REOBSERVATION__NO_DISPERSAL_RATE",
        "source_dryad_version_id":421942,
        "source_date_max":"2014-12-31",
        "counts":counts,
        "original_first_followup_counts_reconciled":True,
        "post2014_id_island_stage_inspected":False,
        "individual_data_exported":False,
        "site_code_changed_means_natal_adult_dispersal":False,
        "later_first_detection_lag_is_true_movement_time":False,
        "selection_bias_from_reobservation_corrected":False,
        "surveyed_zero_verified":False,
        "2020_v8_source_available":False,
        "heldout_predictive_benchmark_authorized":False,
        "colonization_or_fitness_claim_authorized":False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-checkout",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    contract=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    # Verify authentic full source-file bytes/physical header, AND reproduce
    # the *already exposed* 1994–2014 first-followup counts, before new analysis.
    prior=json.loads(PRIOR_RECEIPT.read_text(encoding="utf-8"))
    previous=verified_pre2015_qc(
        args.upstream_checkout,json.loads(ORIGINAL_PROTOCOL.read_text(encoding="utf-8")))
    if previous["counts"]!=prior["counts"]:
        raise ValueError("Original real first-followup frozen evidence no longer reproducible")
    with file_path(args.upstream_checkout,PATH).open("r",encoding="utf-8-sig",newline="") as handle:
        rows=csv.DictReader(handle,delimiter=";",quotechar='"',strict=True)
        report=inspect(rows,contract)
    earlier=json.loads(PRIOR_ANY_LATER_RECEIPT.read_text(encoding="utf-8"))
    reconcile_exposed_followup_counts(report["counts"],earlier)
    report["previous_any_later_observation_counts_reconciled"]=True
    if set(report["counts"])!=set(contract["allowed_output"]):
        raise ValueError("Undeclared output aggregate field")
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse output overwrite")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as out:
        json.dump(report,out,sort_keys=True,indent=2)
        out.write("\n")
    print(json.dumps({"status":report["status"],
                      "first_same_later_different":report["counts"]["first_same_later_different"],
                      "ecological_inference":False}))


if __name__=="__main__":
    main()
