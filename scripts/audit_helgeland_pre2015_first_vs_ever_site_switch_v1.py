#!/usr/bin/env python3
"""Exploratory observed site-code changes after first followup, pre-2015 ONLY.

Actual 2026-published source rows are read, BUT pre-1994/post-2014 records
are excluded immediately by raw 'date' BEFORE accessing ID/site/stage.
This does not measure true dispersal or historical 2014-public predictors.
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
import json
from pathlib import Path
from typing import Iterable, Mapping

from audit_helgeland_pre2015_direct_site_code_switch_v1 import (
    strict_observed_date, PATH, FROZEN, HEADERS,
    validate_whole_file_bytes, read_first_physical_header, file_path
)

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
PROTOCOL = BASE / "helgeland_pre2015_first_vs_any_switch_contract_v1.json"
FROZEN_FIRST = BASE / "helgeland_pre2015_first_direct_site_code_frozen_v1.json"
DIRECT = frozenset(("nest", "capt", "obs"))


def analyze(records: Iterable[Mapping[str, str]], policy: dict) -> dict:
    if (policy.get("schema") != "eog.helgeland.pre2015.first_vs_any_later_site_switch.v1"
            or policy.get("status") !=
            "FROZEN_AFTER_FIRST_FOLLOWUP_223_EXPOSED__BEFORE_ANY_LATER_SWITCH_INSPECTION"):
        raise ValueError("Wrong previously frozen followup analysis contract")
    if policy["source_columns_accessible"] != ["date", "ID", "Island", "Location", "stage"]:
        raise ValueError("Disallowed source columns included")
    if set(policy["physical_direct_stages"]) != DIRECT:
        raise ValueError("Unexpected directly observed stages")
    if not all(v is True for v in policy["scientific_bounds"].values()):
        raise ValueError("Unqualified scientific claim was promoted")
    cutoff = policy["cutoff"]
    if (cutoff["min"], cutoff["max"]) != ("1994-01-01", "2014-12-31"):
        raise ValueError("Original cutoff was modified")
    lo = strict_observed_date(cutoff["min"])
    hi = strict_observed_date(cutoff["max"])
    allowed = policy["preregistered_metrics"]
    counts = dict.fromkeys(allowed, 0)
    nests: dict[str, list[tuple[date, str]]] = defaultdict(list)
    followups: dict[str, list[tuple[date, str]]] = defaultdict(list)

    for row in records:
        counts["whole_file_rows_date_checked"] += 1
        stamp = strict_observed_date(row["date"])
        # This ordering is tested using poisoned future rows.
        if stamp > hi:
            counts["post2014_date_masked"] += 1
            continue
        if stamp < lo:
            counts["pre1994_date_masked"] += 1
            continue

        ident = (row["ID"] or "").strip()
        code = (row["Island"] or "").strip()
        location = (row["Location"] or "").strip()
        stage = (row["stage"] or "").strip()
        if not ident or not code or not location or stage not in DIRECT:
            raise ValueError("Invalid pre2015 physical direct encounter")
        counts["eligible_pre2015_rows"] += 1
        if stage == "nest":
            nests[ident].append((stamp, code))
        else:
            followups[ident].append((stamp, code))

    for ident, nest_history in nests.items():
        source_codes = {c for _, c in nest_history}
        if len(source_codes) != 1:
            counts["ambiguous_nest_source_ids"] += 1
            continue
        counts["unique_nest_source_ids"] += 1
        natal_code = next(iter(source_codes))
        birth_observation = min(t for t, _ in nest_history)
        later = [(t, code) for t, code in followups.get(ident, ())
                 if t > birth_observation]
        if not later:
            counts["nest_ids_without_later_direct"] += 1
            continue
        counts["nest_ids_with_later_direct"] += 1
        first_date = min(t for t, _ in later)
        first_codes = {code for t, code in later if t == first_date}
        if len(first_codes) != 1:
            first_class = "ambiguous"
            counts["first_ambiguous"] += 1
        elif natal_code in first_codes:
            first_class = "same"
            counts["first_same"] += 1
        else:
            first_class = "different"
            counts["first_different"] += 1

        followup_days = len({t for t, _ in later})
        multi_day = followup_days >= 2
        counts["two_or_more_followup_days_count" if multi_day
               else "one_followup_day_count"] += 1

        has_diff = any(code != natal_code for _, code in later)
        if has_diff:
            counts["any_later_different"] += 1
            counts["any_later_different_with_two_or_more_followup_days"
                   if multi_day else
                   "any_later_different_with_only_one_followup_day"] += 1
        if first_class == "same" and has_diff:
            counts["first_same_then_later_different"] += 1
            counts["ever_different_among_first_same_two_or_more_followup_days"
                   if multi_day else
                   "ever_different_among_first_same_one_followup_day"] += 1
        if first_class == "different" and any(
                t > first_date and code == natal_code for t, code in later):
            counts["first_different_then_later_same"] += 1

    previous = policy["pre_exposed_expected"]
    for key, expected in previous.items():
        metric = ("whole_file_rows_date_checked" if key == "whole_source_rows" else key)
        if counts[metric] != expected:
            raise ValueError(f"New endpoint denominator changed from exposed #642: {key}")
    if not (counts["nest_ids_with_later_direct"] ==
            counts["first_same"] + counts["first_different"] +
            counts["first_ambiguous"] ==
            counts["one_followup_day_count"] +
            counts["two_or_more_followup_days_count"]):
        raise ValueError("Inconsistent direct followup denominators")
    if counts["any_later_different"] != (
            counts["any_later_different_with_only_one_followup_day"] +
            counts["any_later_different_with_two_or_more_followup_days"]):
        raise ValueError("Inconsistent ever-change followup-day partitions")
    if counts["any_later_different"] < counts["first_different"]:
        raise ValueError("Ever-different count cannot be below first-different count")
    if counts["first_same_then_later_different"] > counts["first_same"]:
        raise ValueError("Late-only transitions exceed first-same risk set")
    if counts["ever_different_among_first_same_one_followup_day"] != 0:
        raise ValueError("Single observed followup date cannot hide a later change")
    if counts["first_different_then_later_same"] > counts["first_different"]:
        raise ValueError("Later return count exceeds first-different group")
    return {
        "schema": "eog.helgeland.pre2015.first_vs_ever_site_code.exploratory_receipt.v1",
        "status": "OBSERVED_PRE2015_FOLLOWUP_DEPTH_SENSITIVITY__ECOLOGICAL_HOLD",
        "cutoff": "2014-12-31",
        "counts": counts,
        "original_historical_source_public_by_2014": False,
        "future_2015_2022_id_island_stage_inspected": False,
        "biological_natal_dispersal_rate_estimated": False,
        "new_independent_EOG_prediction_scored": False,
        "observation_effort_or_surveyed_zero_verified": False,
        "raw_ids_sites_and_dates_exported": False,
        "all_metric_choices_post_original_223_exposure": True,
    }


def run(root: Path) -> dict:
    policy = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    orig = json.loads(FROZEN_FIRST.read_text(encoding="utf-8"))
    if orig.get("counts") is None or not (
            orig["counts"]["first_followup_changed_island_code"] == 223
            and orig["counts"]["unique_nest_ids_with_first_later_direct_encounter"] == 4164):
        raise ValueError("Original first-followup study result is not frozen")
    source = policy["source"]
    pinned = json.loads(FROZEN.read_text(encoding="utf-8"))
    if (source["doi"] != pinned["source_doi"] or
        source["version_id"] != 421942 or source["file_id"] != 4576411 or
        source["path"] != PATH or
        source["github_commit"] != "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"):
        raise ValueError("Original 2026 source identity not matched")
    if validate_whole_file_bytes(root, pinned)["status"] != "MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Actual original whole-file SHA256 failed")
    full_path = file_path(root, PATH)
    header = json.loads(HEADERS.read_text(encoding="utf-8"))
    real_names, firstline_digest = read_first_physical_header(full_path)
    ref = next(x for x in header["headers"] if x["github_path"] == PATH)
    if (real_names != ref["column_names"] or
            firstline_digest != ref["first_line_sha256"]):
        raise ValueError("Physical first line changed from frozen source")
    with full_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=";", quotechar='"', strict=True)
        if list(reader.fieldnames or []) != real_names:
            raise ValueError("Actual physical source columns changed")
        result = analyze(reader, policy)
    result["source_whole_file_sha256_and_firstline_verified"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.upstream_checkout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, sort_keys=True, ensure_ascii=False)
        output.write("\n")
    print(json.dumps({"status": result["status"],
                      "eligible_ids": result["counts"]["nest_ids_with_later_direct"],
                      "ecological_forecast_authorized": False}))


if __name__ == "__main__":
    main()
