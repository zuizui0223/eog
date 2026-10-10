#!/usr/bin/env python3
"""Post-exposure pre-2015 observed site-code follow-up sensitivity.

Reads site and ID ONLY after raw 'date' is verified within 1994..2014.
All 2015..2022 encounter IDs, sites, stages and destinations stay uninspected.
Outputs aggregate-only identification sensitivity, never inferred dispersal.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta
import json
from pathlib import Path

from audit_helgeland_2026_upstream_byte_parity_v1 import (
    FROZEN, audit as verify_byte_identity, file_path,
)
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header
from audit_helgeland_pre2015_direct_site_code_switch_v1 import strict_observed_date

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT = BASE / "helgeland_pre2015_followup_horizon_protocol_v1.json"
HEADERS = BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json"
SOURCE = "Data/presence_data_1994_2022.txt"
DIRECT = {"nest", "capt", "obs"}


def diagnose(rows, contract: dict) -> dict:
    if contract.get("schema") != "eog.helgeland.pre2015.followup_horizon_exploratory_protocol.v1":
        raise ValueError("Original horizon QC schema absent")
    if contract.get("status") != "FROZEN_AFTER_PR642_OUTCOME_EXPOSURE_BEFORE_ALL_LATER_SCAN":
        raise ValueError("Post-exposure classification protocol changed")
    if (contract.get("field_access") != ["date","ID","Island","Location","stage"] or
        contract.get("time_start") != "1994-01-01" or
        contract.get("time_end") != "2014-12-31" or
        contract.get("horizons_days") != [30,365] or
        any(flag is not True for flag in contract["stop_flags"].values())):
        raise ValueError("Forbidden source field, dates or inference boundary")
    before=date(1994,1,1)
    cutoff=date(2014,12,31)
    counts={key:0 for key in contract["allowed_aggregate_fields"]}
    nests=defaultdict(list)
    direct=defaultdict(list)
    for row in rows:
        counts["whole_file_rows_date_checked"]+=1
        observed=strict_observed_date(row["date"])
        # No individual/location/stage access before the date firewall.
        if observed>cutoff:
            counts["suppressed_post2014_rows"]+=1
            continue
        if observed<before:
            counts["suppressed_pre1994_rows"]+=1
            continue
        ident=(row["ID"] or "").strip()
        island=(row["Island"] or "").strip()
        location=(row["Location"] or "").strip()
        stage=(row["stage"] or "").strip()
        if not ident or not island or not location or stage not in DIRECT:
            raise ValueError("Eligible physical direct encounter incomplete")
        counts["eligible_pre2015_rows"]+=1
        if stage=="nest":
            nests[ident].append((observed,island))
        else:
            direct[ident].append((observed,island))

    for ident, recorded_nests in nests.items():
        natal_codes={site for _,site in recorded_nests}
        if len(natal_codes)!=1:
            counts["ambiguous_nest_site_id_count"]+=1
            continue
        counts["unique_nest_site_id_count"]+=1
        birthplace=next(iter(natal_codes))
        nest_date=min(d for d,_ in recorded_nests)
        visits=[(d,s) for d,s in direct.get(ident,()) if d>nest_date]
        first_date=min((d for d,_ in visits),default=None)
        if first_date is not None:
            counts["first_later_direct_observed_id_count"]+=1
            first_sites={s for d,s in visits if d==first_date}
            if len(first_sites)!=1:
                counts["first_followup_ambiguous_site_id_count"]+=1
            elif birthplace in first_sites:
                counts["first_followup_same_site_id_count"]+=1
                if any(s!=birthplace and d>first_date for d,s in visits):
                    counts["first_same_then_later_different_site_id_count"]+=1
                else:
                    counts["first_followup_same_never_observed_different_later_count"]+=1
            else:
                counts["first_followup_different_site_id_count"]+=1
                if any(s==birthplace and d>first_date for d,s in visits):
                    counts["first_different_then_later_source_site_id_count"]+=1
        if any(s!=birthplace for _,s in visits):
            counts["any_later_different_site_id_count"]+=1

        # Administrative CALENDAR follow-up only, no claim of complete survey effort.
        for days in (30,365):
            if nest_date+timedelta(days=days)>cutoff:
                continue
            counts[f"eligible_{days}d_full_window_nest_id_count"]+=1
            visits_within=[(d,s) for d,s in visits if d<=nest_date+timedelta(days=days)]
            if visits_within:
                counts[f"eligible_{days}d_direct_observed_id_count"]+=1
                if any(s!=birthplace for _,s in visits_within):
                    counts[f"eligible_{days}d_different_site_observed_id_count"]+=1

    baseline=contract["known_pr642"]
    for key,old in baseline.items():
        if counts[key]!=old:
            raise ValueError(f"Observed pre-2015 first-followup counts changed: {key}")
    if set(counts)!=set(contract["allowed_aggregate_fields"]):
        raise ValueError("Unauthorized output aggregate")
    if counts["first_followup_same_site_id_count"]!=(
        counts["first_same_then_later_different_site_id_count"]+
        counts["first_followup_same_never_observed_different_later_count"]):
        raise ValueError("First-same later-movement subsets do not reconcile")
    if counts["first_followup_ambiguous_site_id_count"]==0 and (
        counts["any_later_different_site_id_count"] !=
        counts["first_followup_different_site_id_count"]+
        counts["first_same_then_later_different_site_id_count"]):
        raise ValueError("Ever-different and first-followup classifications disagree")
    for days in (30,365):
        if not (counts[f"eligible_{days}d_different_site_observed_id_count"]<=
                counts[f"eligible_{days}d_direct_observed_id_count"]<=
                counts[f"eligible_{days}d_full_window_nest_id_count"]):
            raise ValueError("Fixed-window observation-subset denominator invalid")
    return {
        "schema":"eog.helgeland.pre2015.followup_horizon_exploratory_receipt.v1",
        "status":"FOLLOWUP_WINDOW_SENSITIVITY_OBSERVED__ECOLOGICAL_HOLD",
        "source_dryad_version_id":421942,"source_file_id":4576411,
        "calendar_cutoff":"2014-12-31",
        "counts":counts,
        "all_2015_2022_id_island_stage_outcomes_masked":True,
        "observed_site_code_changes_not_proven_dispersal":True,
        "followup_calendar_space_not_detection_effort":True,
        "post_exposure_exploratory":True,
        "individual_ids_island_codes_or_dates_exported":False,
        "independent_ecological_score_authorized":False,
    }


def run_source(upstream:Path,contract:dict)->dict:
    if (contract.get("version_id")!=421942 or contract.get("file_id")!=4576411 or
        contract.get("upstream_commit")!="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"):
        raise ValueError("Author archive pin changed")
    pinned=json.loads(FROZEN.read_text(encoding="utf-8"))
    if verify_byte_identity(upstream,pinned)["status"]!="MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("2026 source whole-file byte SHA256 mismatch")
    source=file_path(upstream,SOURCE)
    headers=json.loads(HEADERS.read_text(encoding="utf-8"))
    names,actual_sha=read_first_physical_header(source)
    expected=next(h for h in headers["headers"] if h["github_path"]==SOURCE)
    if (names!=expected["column_names"] or
        actual_sha!=expected["first_line_sha256"] or
        expected["dryad_file_metadata_id"]!=4576411):
        raise ValueError("Physical source header differs from attested v6")
    with source.open("r",encoding="utf-8-sig",newline="") as fh:
        rows=csv.DictReader(fh,delimiter=";",quotechar='"',strict=True)
        if list(rows.fieldnames or [])!=names:
            raise ValueError("Source CSV header parse mismatch")
        receipt=diagnose(rows,contract)
    receipt["source_byte_sha256_and_firstline_reverified"]=True
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse existing output file")
    result=run_source(args.upstream_checkout,
                      json.loads(CONTRACT.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as handle:
        json.dump(result,handle,ensure_ascii=False,indent=2,sort_keys=True)
        handle.write("\n")
    print(json.dumps({"status":result["status"],
                      "first_followup_changed":result["counts"]["first_followup_different_site_id_count"],
                      "independent_score_authorized":False}))


if __name__=="__main__":
    main()
