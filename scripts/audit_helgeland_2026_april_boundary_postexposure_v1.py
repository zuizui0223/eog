#!/usr/bin/env python3
"""Post-exposure April boundary fit audit, not a proof of annual-field semantics.

Actual source rows are parsed, but ONLY the Year and date fields are consulted,
and only twelve monthly totals plus coarse boundary-match counts are emitted.
No row or individual identifiers, islands, stages, or ecological scores leave CI.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path

from audit_helgeland_2026_upstream_byte_parity_v1 import (
    audit as verify_bytes, FROZEN, file_path
)
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT=BASE/"helgeland_2026_april_boundary_postexposure_contract_v1.json"
FROZEN_HEADERS=BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json"
PREVIOUS=BASE/"helgeland_2026_year_date_discordance_frozen_v1.json"
UPSTREAM="Data/presence_data_1994_2022.txt"


def inspect(root: Path, protocol: dict, frozen: dict, headers: dict, previous: dict) -> dict:
    if (protocol.get("schema")!="eog.helgeland.2026.april_boundary_postexposure_qc.v1"
        or protocol.get("status")!="POST_EXPOSURE_DIAGNOSTIC__NOT_AUTHOR_CONFIRMED__NO_ECOLOGICAL_SCORE"):
        raise ValueError("Pre-registered exploratory contract missing")
    p=protocol["source"]
    if (p["doi"]!=frozen["source_doi"] or p["version_id"]!=421942 or
        p["source_file_id"]!=4576411 or p["upstream_path"]!=UPSTREAM or
        p["upstream_commit"]!="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"):
        raise ValueError("Source DOI/version/file/commit mismatch")
    if protocol["input_columns_read"]!=["date","Year"] or any(
        v is not False for v in protocol["claims"].values()
    ):
        raise ValueError("Unexpected field or elevated claim")
    if verify_bytes(root,frozen)["status"]!="MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Opaque source SHA-256 does not match Dryad v6")
    source=file_path(root,UPSTREAM)
    actual,header_hash=read_first_physical_header(source)
    pinned=next((r for r in headers["headers"] if r["github_path"]==UPSTREAM),None)
    if not pinned or pinned["column_names"]!=actual or pinned["first_line_sha256"]!=header_hash:
        raise ValueError("Source physical header differs from frozen first-line evidence")
    if not {"Year","date"}.issubset(actual):
        raise ValueError("Year and date columns missing")
    if previous["schema"]!="eog.helgeland.2026.observation_year_date_postexposure.frozen_observed_v1":
        raise ValueError("Previous post-exposure record missing")
    if previous["source"]["dryad_version_id"]!=421942 if "source" in previous else previous["total_rows"]!=73593:
        raise ValueError("Previous source receipt changed")

    months={f"{month:02d}":0 for month in range(1,13)}
    jan_prev=jan_same=jan_other=other_same=other_bad=0
    rows=0
    with source.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream,delimiter=";",quotechar='"',strict=True)
        if list(reader.fieldnames or [])!=actual:
            raise ValueError("CSV header unexpectedly changed")
        for record in reader:
            if None in record:
                raise ValueError("Malformed field count")
            rows+=1
            try:
                year=int((record["Year"] or "").strip())
                observed=date.fromisoformat((record["date"] or "").strip())
            except (TypeError,ValueError) as exc:
                raise ValueError("Unparseable source observation timing") from exc
            month=observed.month
            months[f"{month:02d}"]+=1
            delta=year-observed.year
            if month<=3:
                if delta==-1: jan_prev+=1
                elif delta==0: jan_same+=1
                else: jan_other+=1
            else:
                if delta==0: other_same+=1
                else: other_bad+=1
    prior=protocol["prior_exposed_qc"]
    if not (rows==prior["rows"]==previous["total_rows"] and
        jan_prev==prior["delta_minus_one"]==previous["all_year_delta_bin_counts"]["-1"] and
        jan_prev+jan_same+jan_other+other_same+other_bad==rows and
        other_bad==prior["april_december_mismatches"]==0 and
        jan_other==0 and sum(months.values())==rows):
        raise ValueError("Source data changed from established exploratory QC")
    candidate_mismatch=jan_same+jan_other+other_bad
    return {
        "schema":"eog.helgeland.2026.april_boundary_postexposure_receipt.v1",
        "status":"APRIL_CANDIDATE_MONTHLY_DIAGNOSTIC__AUTHOR_SEMANTICS_HOLD",
        "total_rows":rows,
        "monthly_total_rows":months,
        "jan_mar_minus_one":jan_prev,
        "jan_mar_same_year":jan_same,
        "jan_mar_other_delta":jan_other,
        "apr_dec_same_year":other_same,
        "apr_dec_any_mismatch":other_bad,
        "overall_candidate_mapping_disagreements":candidate_mismatch,
        "candidate_mapping_exact_on_all_rows":candidate_mismatch==0,
        "observed_year_rule_confirmed_by_authors":False,
        "post_exposure_exploratory":True,
        "date_or_Year_values_recoded":False,
        "row_level_values_exported":False,
        "as_of_t_predictors_qualified":False,
        "surveyed_zero_panel_verified":False,
        "ecological_endpoint_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    report=inspect(
        args.upstream_checkout,
        json.loads(CONTRACT.read_text(encoding="utf-8")),
        json.loads(FROZEN.read_text(encoding="utf-8")),
        json.loads(FROZEN_HEADERS.read_text(encoding="utf-8")),
        json.loads(PREVIOUS.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,sort_keys=True,ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"status":report["status"],"candidate_mismatches":report["overall_candidate_mapping_disagreements"]}))


if __name__=="__main__":
    main()
