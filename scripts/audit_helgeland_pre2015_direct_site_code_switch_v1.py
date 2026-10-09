#!/usr/bin/env python3
"""Exploratory pre-2015 direct encounter site-CODE switch audit.

This reads the 2026-public Helgeland presence archive's raw observation rows,
but *before* using ID/stage/island it discards any dated outside 1994–2014.
Do not construe observed code switches as recruitment, natal dispersal,
founding, surveyed zeros or an out-of-time EOG forecast.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Mapping

from audit_helgeland_2026_upstream_byte_parity_v1 import (
    FROZEN, audit as validate_whole_file_bytes, file_path
)
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
PROTOCOL=BASE/"helgeland_pre2015_direct_code_switch_protocol_v1.json"
HEADERS=BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json"
PATH="Data/presence_data_1994_2022.txt"
ALLOWED={"nest","capt","obs"}


def strict_observed_date(text: str) -> date:
    if (not isinstance(text,str) or len(text)!=10 or text[4]!="-"
            or text[7]!="-" or not (text[:4]+text[5:7]+text[8:]).isdigit()):
        raise ValueError("Raw physical observation date must be yyyy-mm-dd")
    return date.fromisoformat(text)


def count_site_code_switches(records: Iterable[Mapping[str,str]],
                             policy: dict) -> dict:
    if (policy.get("schema")!="eog.helgeland.direct_site_code_switch_pre2015.exploratory_protocol.v1"
       or policy.get("status")!="EXPLORATORY_AFTER_FULL_2026_STRUCTURAL_QC__BEFORE_PRE2015_SITE_SWITCH_EXPOSURE"):
        raise ValueError("Original post-exposure exploratory protocol missing")
    if policy["input_columns"]!=["ID","Island","Location","date","stage"]:
        raise ValueError("Unexpected source variables allowed into identity history")
    if set(policy["physical_direct_stages"])!=ALLOWED or not all(
        v is True for k,v in policy["holds"].items()
        if k!="ecological_model_or_independent_heldout_benchmark_authorized"):
        raise ValueError("Observation-process HOLD or allowed direct-stages changed")
    if policy["holds"]["ecological_model_or_independent_heldout_benchmark_authorized"] is not False:
        raise ValueError("Cannot claim an ecological forecast")
    lo=strict_observed_date(policy["window"]["first_observation_date"])
    hi=strict_observed_date(policy["window"]["last_observation_date_inclusive"])
    if lo!=date(1994,1,1) or hi!=date(2014,12,31):
        raise ValueError("Pre-2015 exposure window altered")

    counts={k:0 for k in policy["allowed_aggregate_fields"]}
    first_source_nest_dates=defaultdict(list)
    observed_followups=defaultdict(list)
    all_ids=set()

    for row in records:
        counts["whole_file_rows_date_checked"]+=1
        # *** IMPORTANT: no access to individual/site/stage until after time mask ***
        stamp=strict_observed_date(row["date"])
        if stamp>hi:
            counts["post2014_rows_suppressed_by_date_only"]+=1
            continue
        if stamp<lo:
            counts["pre1994_rows_suppressed_by_date_only"]+=1
            continue
        ident=(row["ID"] or "").strip()
        site=(row["Island"] or "").strip()
        locality=(row["Location"] or "").strip()
        stage=(row["stage"] or "").strip()
        if not ident or not site or not locality or stage not in ALLOWED:
            raise ValueError("Empty/invalid directly observed pre-2015 encounter")
        all_ids.add(ident)
        counts["eligible_pre2015_rows"]+=1
        if stage=="nest":
            counts["eligible_nest_encounter_rows"]+=1
            first_source_nest_dates[ident].append((stamp,site))
        else:
            counts["eligible_capt_obs_encounter_rows"]+=1
            observed_followups[ident].append((stamp,site))
    counts["distinct_ids_observed_pre2015"]=len(all_ids)
    counts["ids_with_any_pre2015_nest_record"]=len(first_source_nest_dates)

    for ident,nest_obs in first_source_nest_dates.items():
        all_codes={site for _,site in nest_obs}
        if len(all_codes)!=1:
            counts["ids_with_ambiguous_pre2015_nest_code"]+=1
            continue
        counts["ids_with_unique_pre2015_nest_code"]+=1
        source_site=next(iter(all_codes))
        first_nest=min(stamp for stamp,_ in nest_obs)
        later=[(stamp,site) for stamp,site in observed_followups.get(ident,())
               if stamp>first_nest]
        if not later:
            counts["unique_nest_ids_without_later_direct_encounter"]+=1
            continue
        counts["unique_nest_ids_with_first_later_direct_encounter"]+=1
        first_date=min(stamp for stamp,_ in later)
        destination_codes={site for stamp,site in later if stamp==first_date}
        if len(destination_codes)!=1:
            counts["first_followup_ambiguous_island_code"]+=1
        elif source_site in destination_codes:
            counts["first_followup_same_island_code"]+=1
        else:
            counts["first_followup_changed_island_code"]+=1

    if not (counts["whole_file_rows_date_checked"]==
           counts["post2014_rows_suppressed_by_date_only"]+
           counts["pre1994_rows_suppressed_by_date_only"]+
           counts["eligible_pre2015_rows"]):
        raise ValueError("Date-only observation partition does not reconcile")
    if counts["eligible_pre2015_rows"]!=(
         counts["eligible_nest_encounter_rows"]+counts["eligible_capt_obs_encounter_rows"]):
        raise ValueError("Physical direct stage totals fail to reconcile")
    if counts["ids_with_any_pre2015_nest_record"]!=(
        counts["ids_with_ambiguous_pre2015_nest_code"]+
        counts["ids_with_unique_pre2015_nest_code"]):
        raise ValueError("Nest-source candidates fail to reconcile")
    if counts["ids_with_unique_pre2015_nest_code"]!=(
        counts["unique_nest_ids_without_later_direct_encounter"]+
        counts["unique_nest_ids_with_first_later_direct_encounter"]):
        raise ValueError("Pre-2015 first-followup pool incomplete")
    if counts["unique_nest_ids_with_first_later_direct_encounter"]!=(
        counts["first_followup_same_island_code"]+
        counts["first_followup_changed_island_code"]+
        counts["first_followup_ambiguous_island_code"]):
        raise ValueError("First-direct-island-code counts fail to reconcile")
    if counts["whole_file_rows_date_checked"]!=policy["expected_source_row_count_from_prior_qc"]:
        raise ValueError("Unexpected original 2026 v6 row count")

    return {
        "schema":"eog.helgeland.pre2015.direct_site_code_switch.exploratory_result.v1",
        "status":"OBSERVED_PRE2015_FIRST_FOLLOWUP_SITE_CODE_QC__NO_ECOLOGICAL_INFERENCE",
        "source_dryad_v6_file_id":4576411,
        "source_cutoff_date":"2014-12-31",
        "counts":counts,
        "scientific_boundaries":{
            "site_code_switch_is_proven_natal_dispersal":False,
            "direct_capt_or_obs_is_proven_recruitment":False,
            "surveyed_zero_denominator_observed":False,
            "future_2015_2022_destination_values_accessed":False,
            "future_outcomes_scored":False,
            "population_founding_or_source_sink_inferred":False,
            "numeric_site_code_dictionary_independently_verified":False,
            "independent_heldout_benchmark_qualified":False,
            "ecological_forecast_authorized":False,
        },
        "individual_ids_or_site_values_exported":False,
        "post_exposure_exploratory":True,
    }


def verified_pre2015_qc(root:Path,protocol:dict)->dict:
    frozen=json.loads(FROZEN.read_text(encoding="utf-8"))
    hdr=json.loads(HEADERS.read_text(encoding="utf-8"))
    if protocol["expected_source_row_count_from_prior_qc"]!=73593:
        raise ValueError("Previous 2026 source row count differs")
    if protocol["source"]["version_id"]!=421942 or protocol["source"]["file_id"]!=4576411:
        raise ValueError("Wrong original published source version")
    if protocol["source"]["github_commit"]!="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5":
        raise ValueError("Upstream author revision changed")
    if validate_whole_file_bytes(root,frozen)["status"]!="MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Original source byte SHA256 is not attested")
    p=file_path(root,PATH)
    names,header_sha=read_first_physical_header(p)
    pinned=next(x for x in hdr["headers"] if x["github_path"]==PATH)
    if names!=pinned["column_names"] or header_sha!=pinned["first_line_sha256"]:
        raise ValueError("First-line schema differs from verified original")
    if not set(protocol["input_columns"]).issubset(names):
        raise ValueError("Missing predeclared direct encounter fields")
    with p.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle,delimiter=";",quotechar='"',strict=True)
        if list(reader.fieldnames or [])!=names:
            raise ValueError("Source header changed")
        result=count_site_code_switches(reader,protocol)
    result["original_complete_source_sha256_and_header_verified"]=True
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-checkout",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    policy=json.loads(PROTOCOL.read_text(encoding="utf-8"))
    result=verified_pre2015_qc(args.upstream_checkout,policy)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,sort_keys=True,indent=2,ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status":result["status"],
                      "pre2015_eligible_rows":result["counts"]["eligible_pre2015_rows"],
                      "forecast_authorized":False}))


if __name__=="__main__":
    main()
