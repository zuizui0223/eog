#!/usr/bin/env python3
"""Response-blind STRUCTURAL QC on byte-verified Helgeland 2026 presence rows.

This intentionally reads individual rows for aggregate data quality only. It
does not score dispersal, island occupancy, model predictions or biological effects.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path

from audit_helgeland_2026_upstream_byte_parity_v1 import (
    FROZEN, TARGETS, audit as byte_audit, file_path
)
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
PROTOCOL = BASE / "helgeland_2026_direct_observation_qc_protocol_v1.json"
FROZEN_HEADERS = BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json"
UPSTREAM_PRESENCE = "Data/presence_data_1994_2022.txt"


def structural_qc(root: Path, dryad: dict, header_receipt: dict,
                  protocol: dict) -> dict:
    if protocol["schema"] != "eog.helgeland.2026.direct_observation_qc_protocol.v1":
        raise ValueError("Wrong preregistered QC schema")
    if protocol["status"] != "FROZEN_BEFORE_READING_2026_PRESENCE_RECORD_ROWS":
        raise ValueError("Source-row exposure gate was modified")
    pinned = protocol["source"]
    if not (pinned["dataset_id"] == 177360 and pinned["version_id"] == 421942
            and pinned["file_metadata_id"] == 4576411
            and pinned["github_path"] == UPSTREAM_PRESENCE
            and pinned["doi"] == dryad["source_doi"]):
        raise ValueError("Frozen source identity differs from preregistration")
    if protocol["claim_boundary"]["biological_scoring_authorized"] is not False:
        raise ValueError("Biological scoring must stay explicitly unauthorized")
    match = byte_audit(root, dryad)
    if match["status"] != "MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Source byte identity is not verified")
    path = file_path(root, UPSTREAM_PRESENCE)
    actual_header, actual_hash = read_first_physical_header(path)
    if header_receipt["schema"] != "eog.helgeland.dryad2026.two_file_physical_headers.frozen_observed_v1":
        raise ValueError("Unrecognized frozen physical header")
    pinned_header = next((h for h in header_receipt["headers"]
                          if h["github_path"] == UPSTREAM_PRESENCE), None)
    if (pinned_header is None or pinned_header["first_line_sha256"] != actual_hash
            or pinned_header["column_names"] != actual_header
            or pinned_header["dryad_file_metadata_id"] != 4576411):
        raise ValueError("Physical header differs from frozen v6 first-line evidence")
    if actual_header != protocol["required_exact_columns"] and set(actual_header) != set(protocol["required_exact_columns"]):
        raise ValueError("Preregistered observation columns differ from physical header")

    summary = {name: 0 for name in protocol["allowed_output_aggregates"]}
    nest_islands: dict[str, set[str]] = {}
    nest_dates: dict[str, list[date]] = {}
    direct_dates: dict[str, list[date]] = {}
    id_values: set[str] = set()
    unique_events: set[tuple[str, str, str, str, str]] = set()
    for_min = int(protocol["retained_record_window"]["first_year"])
    for_max = int(protocol["retained_record_window"]["last_year"])
    stages_direct = frozenset(protocol["direct_later_observation_stage_candidates"])
    stage_nest = protocol["direct_nest_stage"]
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = csv.DictReader(stream, delimiter=";", quotechar='"', strict=True)
        if list(rows.fieldnames or []) != actual_header:
            raise ValueError("Physical header and CSV parser are not in agreement")
        for row in rows:
            summary["row_count"] += 1
            if None in row:
                summary["column_count_mismatch_rows"] = summary.get("column_count_mismatch_rows", 0) + 1
                continue
            ident = (row.get("ID") or "").strip()
            island = (row.get("Island") or "").strip()
            location = (row.get("Location") or "").strip()
            stage = (row.get("stage") or "").strip()
            year_text = (row.get("Year") or "").strip()
            date_text = (row.get("date") or "").strip()
            if not ident or not island or not location or not stage or not year_text or not date_text:
                summary["missing_key_count"] += 1
                continue
            summary["nonempty_id_count"] += 1
            id_values.add(ident)
            key = (ident, date_text, stage, island, location)
            if key in unique_events:
                summary["duplicate_exact_observation_count"] += 1
            unique_events.add(key)
            try:
                when = date.fromisoformat(date_text)
                year = int(year_text)
            except ValueError:
                summary["unparseable_date_count"] += 1
                continue
            if year != when.year:
                summary["date_year_disagreement_count"] += 1
                continue
            if year < for_min or year > for_max:
                summary["out_of_window_count"] += 1
                continue
            if stage == stage_nest:
                summary["nest_stage_row_count"] += 1
                nest_islands.setdefault(ident, set()).add(island)
                nest_dates.setdefault(ident, []).append(when)
            elif stage in stages_direct:
                summary["direct_later_stage_row_count"] += 1
                direct_dates.setdefault(ident, []).append(when)
            else:
                summary["unrecognized_stage_count"] += 1

    summary["distinct_id_count"] = len(id_values)
    summary["multi_nest_island_id_count"] = sum(len(v) > 1 for v in nest_islands.values())
    summary["ids_with_one_nest_island_and_any_later_direct_observation"] = sum(
        len(nest_islands[ident]) == 1 and
        any(capture > min(nest_dates[ident]) for capture in direct_dates.get(ident, ()))
        for ident in nest_dates
    )
    if not set(summary).issubset(set(protocol["allowed_output_aggregates"]) | {"column_count_mismatch_rows"}):
        raise ValueError("Unapproved aggregate emitted")
    return {
        "schema": "eog.helgeland.2026.structural_positive_record_qc_receipt.v1",
        "status": "STRUCTURAL_QC_ONLY__TEMPORAL_AND_ECOLOGICAL_HOLD",
        "dryad_version_id": 421942,
        "source_file_metadata_id": 4576411,
        "author_source_byte_and_firstline_identical_to_dryad_v6": True,
        "counts": summary,
        "reader_scope": "Individual rows temporarily parsed for aggregate structural QC only",
        "individual_ids_or_row_values_exported": False,
        "surveyed_zero_panel_verified": False,
        "as_of_t_predictor_availability_verified": False,
        "directed_colonization_or_migration_scored": False,
        "independent_heldout_benchmark_qualified": False,
        "ecological_endpoint_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dryad = json.loads(FROZEN.read_text(encoding="utf-8"))
    header = json.loads(FROZEN_HEADERS.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    report = structural_qc(args.upstream_checkout, dryad, header, protocol)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": report["status"],
                      "rows": report["counts"]["row_count"],
                      "ecological_endpoint_authorized": False}))


if __name__ == "__main__":
    main()
