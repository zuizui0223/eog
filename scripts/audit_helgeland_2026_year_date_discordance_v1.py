#!/usr/bin/env python3
"""Exploratory Year/date discordance QC; not ecological or prospective validation.

Reads only Year/date values from source-verified full presence file; the CSV
reader necessarily tokenizes complete rows, but no other field is inspected,
retained or emitted. Previous QC counts have already been exposed.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path

from audit_helgeland_2026_upstream_byte_parity_v1 import FROZEN, file_path, audit as byte_audit
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT=BASE/"helgeland_2026_year_date_exploratory_contract_v1.json"
HEADERS=BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json"


def year_delta_bin(delta: int) -> str:
    if delta <= -2:
        return "<=-2"
    if delta == -1:
        return "-1"
    if delta == 0:
        return "0"
    if delta == 1:
        return "+1"
    return ">=+2"


def analyze(root: Path, contract: dict, frozen: dict, headers: dict) -> dict:
    if (contract.get("schema") !=
        "eog.helgeland.2026.observation_year_date_discordance.exploratory_contract.v1"
        or contract.get("status") !=
        "FROZEN_AFTER_STRUCTURAL_QC_RESULT_EXPOSURE__BEFORE_THIS_FOLLOWUP"):
        raise ValueError("Missing explicit post-exposure exploratory contract")
    p=contract["source"]
    if (p["doi"] != frozen["source_doi"] or p["dryad_version_id"] != 421942 or
        p["dryad_file_id"] != 4576411 or
        p["file_path"] != "Data/presence_data_1994_2022.txt"):
        raise ValueError("Unrecognized pinned original source")
    if contract["read_only_columns"] != ["Year", "date"]:
        raise ValueError("Unexpected fields authorized for inspection")
    if any(v is not False for v in contract["flags"].values()):
        raise ValueError("Exploratory diagnostic may not authorize ecological claims")
    upstream_commit="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
    if p["github_commit"] != upstream_commit:
        raise ValueError("Source revision not frozen")
    status=byte_audit(root,frozen)
    if status["status"]!="MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Two-file Dryad v6 SHA256 parity not established")
    path=file_path(root,p["file_path"])
    physical, physical_hash=read_first_physical_header(path)
    hdr=next(x for x in headers["headers"] if x["github_path"]==p["file_path"])
    if (physical != hdr["column_names"] or physical_hash != hdr["first_line_sha256"]
            or hdr["dryad_file_metadata_id"] != 4576411):
        raise ValueError("Physical header differs from frozen verified source")

    months=contract["month_bins"]
    bins=contract["year_minus_calendar_year_bins"]
    if (months != [f"{m:02}" for m in range(1,13)]
            or bins != ["<=-2","-1","0","+1",">=+2"]):
        raise ValueError("Unfrozen bin boundaries")
    offsets={key:0 for key in bins}
    discord_month={m:0 for m in months}
    joint={m:{key:0 for key in bins if key!="0"} for m in months}
    outside={k:0 for k in contract["outside_year_bins"]}
    total=bad_year=bad_date=consistent_outside=0
    with path.open("r",encoding="utf-8-sig",newline="") as handle:
        reader=csv.DictReader(handle,delimiter=";",quotechar='"',strict=True)
        if list(reader.fieldnames or []) != physical:
            raise ValueError("Header parser mismatch")
        for row in reader:
            total+=1
            if None in row:
                raise ValueError("Unexpected malformed row")
            try:
                year=int((row["Year"] or "").strip())
            except (TypeError, ValueError):
                bad_year+=1
                continue
            try:
                observed=date.fromisoformat((row["date"] or "").strip())
            except (TypeError, ValueError):
                bad_date+=1
                continue
            if year < 1994: outside["Year<1994"]+=1
            if year > 2022: outside["Year>2022"]+=1
            if observed.year < 1994: outside["date.year<1994"]+=1
            if observed.year > 2022: outside["date.year>2022"]+=1
            key=year_delta_bin(year-observed.year)
            offsets[key]+=1
            if key!="0":
                month=f"{observed.month:02}"
                discord_month[month]+=1
                joint[month][key]+=1
            elif year < 1994 or year > 2022:
                consistent_outside+=1

    previous=contract["prior_exposed_counts"]
    if (total != previous["row_count"] or
            sum(offsets.values())+bad_year+bad_date != total or
            total-offsets["0"] != previous["year_date_disagreement_count"] or
            consistent_outside != previous["year_date_matching_outside_1994_2022_count"] or
            sum(discord_month.values()) != previous["year_date_disagreement_count"] or
            sum(sum(v.values()) for v in joint.values()) !=
            previous["year_date_disagreement_count"]):
        raise ValueError("Aggregate results differ from previously frozen structural QC")
    return {
        "schema":"eog.helgeland.2026.observation_year_date_postexposure_receipt.v1",
        "status":"YEAR_DATE_DISCREPANCY_DESCRIBED__MEANING_UNRESOLVED",
        "source_dryad_version":421942,
        "source_file_id":4576411,
        "total_rows":total,
        "invalid_year":bad_year,
        "invalid_date":bad_date,
        "all_year_delta_bin_counts":offsets,
        "discordant_by_calendar_month":discord_month,
        "discordant_by_year_delta_and_calendar_month":joint,
        "consistent_year_outside_window":consistent_outside,
        "out_of_range_year_value_counts":{
            "before_1994":outside["Year<1994"],"after_2022":outside["Year>2022"]},
        "out_of_range_date_year_counts":{
            "before_1994":outside["date.year<1994"],
            "after_2022":outside["date.year>2022"]},
        "row_ids_locations_or_observations_exported":False,
        "exploratory_after_first_QC_exposure":True,
        "source_year_date_semantics_resolved":False,
        "date_correction_authorized":False,
        "as_of_t_predictors_verified":False,
        "surveyed_zero_panel_verified":False,
        "ecological_endpoint_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    x=analyze(args.upstream_checkout,json.loads(CONTRACT.read_text()),
              json.loads(FROZEN.read_text()),json.loads(HEADERS.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as out:
        json.dump(x,out,sort_keys=True,ensure_ascii=False,indent=2)
        out.write("\n")
    print(json.dumps({"status":x["status"],"rows":x["total_rows"]}))


if __name__=="__main__":
    main()
