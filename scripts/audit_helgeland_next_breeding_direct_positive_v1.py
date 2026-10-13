#!/usr/bin/env python3
"""Post-exposure pre-2015 direct positives at next-calendar-year breeding season.

This deliberately DOES NOT identify recruitment, natal dispersal, settlement,
surveyed absence or a heldout EOG forecast. No source Year/age-derived fields
are accessed. Out-of-window rows are masked by physical date BEFORE identity.
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
    BASE, PATH, PROTOCOL as FIRST_PROTOCOL,
    strict_observed_date, verified_pre2015_qc,
)
from audit_helgeland_2026_upstream_byte_parity_v1 import file_path

PROTOCOL = BASE / "helgeland_next_breeding_direct_positive_protocol_v1.json"
PRIOR_FIRST = BASE / "helgeland_pre2015_first_direct_site_code_frozen_v1.json"
PRIOR_ANY = BASE / "helgeland_pre2015_followup_horizon_observed_frozen_v1.json"
AUTHOR_SHA = "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
PROTOCOL_SCHEMA = "eog.helgeland.pre2015.next_calendar_breeding_direct_positive.protocol.v1"
PROTOCOL_STATUS = (
    "FROZEN_AFTER_223_451_228_PRIOR_RESULTS_EXPOSED"
    "__BEFORE_NEXT_BREEDING_CLASSIFICATION_READ"
)
OUTPUT_SCHEMA = "eog.helgeland.pre2015.next_breeding_direct_positive.exploratory_receipt.v1"
DIRECT = frozenset(("nest", "capt", "obs"))
CLASSES = ("same", "different", "ambiguous")
FIELDS = (
    "whole_source_rows_date_checked", "pre1994_rows_masked",
    "post2014_rows_masked", "eligible_pre2015_rows",
    "unique_nest_source_ids", "ambiguous_nest_source_ids",
    "excluded_birth_year_2014", "excluded_birth_outside_may_aug",
    "eligible_birth_cohort_ids", "next_season_no_direct_positive",
    "next_season_direct_positive", "next_season_same",
    "next_season_different", "next_season_ambiguous",
    *(f"first_raw_{a}__next_{b}" for a in CLASSES for b in CLASSES),
    "first_raw_before_next_season_detection",
)
EXPECTED_BOUNDS = {
    "positive_detection_only": True,
    "next_breeding_record_does_not_prove_breeding_or_recruitment": True,
    "literal_Island_code_without_independent_cross_archive_dictionary": True,
    "detection_effort_and_surveyed_zero_unverified": True,
    "earliest_nest_date_does_not_prove_original_database_available_then": True,
    "source_published_in_2026_not_available_in_2014": True,
    "post_original_223_451_exposure_exploratory": True,
    "post2014_destination_identity_read": False,
    "biological_dispersal_rate_estimated": False,
    "independent_heldout_ecological_model_scored": False,
    "EOG_WF_denominator_modified": False,
}


def _policy_check(policy: dict) -> None:
    if (policy.get("schema") != PROTOCOL_SCHEMA or
            policy.get("status") != PROTOCOL_STATUS):
        raise ValueError("Missing pre-exposure seasonal analysis protocol")
    source = policy.get("source", {})
    if (source.get("doi") != "10.5061/dryad.rr4xgxdnq" or
            source.get("version_id") != 421942 or
            source.get("file_id") != 4576411 or
            source.get("author_commit") != AUTHOR_SHA or
            source.get("path") != PATH or
            source.get("public_at_forecast_cutoff_2014") is not False):
        raise ValueError("Changed original source or historical visibility")
    if policy.get("date_access_contract") != {
        "physical_date_min": "1994-01-01",
        "physical_date_max": "2014-12-31",
        "strictly_read_date_before_ID_Island_stage": True,
        "post2014_identity_never_read": True,
    }:
        raise ValueError("Observation date safety contract changed")
    if policy.get("permissible_fields_after_date_mask") != [
        "date", "ID", "Island", "stage"
    ]:
        raise ValueError("Unapproved source field access")
    if policy.get("scientific_bounds") != EXPECTED_BOUNDS:
        raise ValueError("Scientific inference boundary was promoted")
    cohort = policy.get("cohort", {})
    if (cohort.get("source_birth_months") != [5, 6, 7, 8] or
            cohort.get("birth_year_last_included") != 2013):
        raise ValueError("Frozen birth-cohort and seasonal calendar changed")
    if list(policy.get("outputs", {}).get("allowed_count_fields", [])) != list(FIELDS):
        raise ValueError("Undeclared aggregate count field")
    if policy["outputs"].get("output_only_counts_and_boolean_gates") is not True:
        raise ValueError("Aggregate-only output requirement changed")
    if policy["outputs"].get("no_raw_ID_Island_Location_or_event_dates_exported") is not True:
        raise ValueError("Individual data release forbidden")


def _which(codes: set[str], origin: str) -> str:
    if len(codes) != 1:
        return "ambiguous"
    return "same" if origin in codes else "different"


def inspect(records: Iterable[Mapping[str, str]], policy: dict) -> dict:
    """Return only counts. Supports invented unit-test records."""
    _policy_check(policy)
    counts = dict.fromkeys(FIELDS, 0)
    nests: dict[str, list[tuple[date, str]]] = defaultdict(list)
    followups: dict[str, list[tuple[date, str]]] = defaultdict(list)
    lo, hi = date(1994, 1, 1), date(2014, 12, 31)

    for row in records:
        counts["whole_source_rows_date_checked"] += 1
        # The first and ONLY out-of-period field read must be raw physical date.
        stamp = strict_observed_date(row["date"])
        if stamp < lo:
            counts["pre1994_rows_masked"] += 1
            continue
        if stamp > hi:
            counts["post2014_rows_masked"] += 1
            continue
        ident = (row["ID"] or "").strip()
        code = (row["Island"] or "").strip()
        stage = (row["stage"] or "").strip()
        if not ident or not code or stage not in DIRECT:
            raise ValueError("Invalid direct encounter inside frozen calendar")
        counts["eligible_pre2015_rows"] += 1
        if stage == "nest":
            nests[ident].append((stamp, code))
        else:
            followups[ident].append((stamp, code))

    prior = policy["pre_exposed_expected"]
    for field, expected in (
        ("whole_source_rows_date_checked", prior["whole_source_rows"]),
        ("pre1994_rows_masked", prior["pre1994_rows"]),
        ("post2014_rows_masked", prior["post2014_rows"]),
        ("eligible_pre2015_rows", prior["eligible_pre2015_rows"]),
    ):
        if counts[field] != expected:
            raise ValueError("Previously exposed whole-source denominator changed: " + field)

    for ident, nest_rows in nests.items():
        source_codes = {code for _, code in nest_rows}
        if len(source_codes) != 1:
            counts["ambiguous_nest_source_ids"] += 1
            continue
        counts["unique_nest_source_ids"] += 1
        origin = next(iter(source_codes))
        first_nest = min(t for t, _ in nest_rows)
        if first_nest.year > 2013:
            counts["excluded_birth_year_2014"] += 1
            continue
        if first_nest.month not in (5, 6, 7, 8):
            counts["excluded_birth_outside_may_aug"] += 1
            continue
        counts["eligible_birth_cohort_ids"] += 1
        after = [(t, site) for t, site in followups.get(ident, ())
                 if t > first_nest]
        next_year = [(t, site) for t, site in after
                     if t.year == first_nest.year + 1 and t.month in (5, 6, 7, 8)]
        if not next_year:
            counts["next_season_no_direct_positive"] += 1
            continue

        counts["next_season_direct_positive"] += 1
        next_first = min(t for t, _ in next_year)
        next_code = {site for t, site in next_year if t == next_first}
        nxt = _which(next_code, origin)
        counts["next_season_" + nxt] += 1

        raw_first = min(t for t, _ in after)
        raw_code = {site for t, site in after if t == raw_first}
        first = _which(raw_code, origin)
        counts[f"first_raw_{first}__next_{nxt}"] += 1
        if raw_first < next_first:
            counts["first_raw_before_next_season_detection"] += 1

    if counts["unique_nest_source_ids"] != prior["unique_nest_ids"]:
        raise ValueError("Previously exposed unique nest-source denominator changed")
    if counts["ambiguous_nest_source_ids"] != prior["ambiguous_nest_ids"]:
        raise ValueError("Previously exposed ambiguous nest-source denominator changed")
    if counts["eligible_birth_cohort_ids"] != (
        counts["unique_nest_source_ids"] -
        counts["excluded_birth_year_2014"] -
        counts["excluded_birth_outside_may_aug"]
    ):
        raise ValueError("Birth cohort partition changed")
    if counts["eligible_birth_cohort_ids"] != (
        counts["next_season_direct_positive"] +
        counts["next_season_no_direct_positive"]
    ):
        raise ValueError("Positive versus unseen partition changed")
    if counts["next_season_direct_positive"] != (
        counts["next_season_same"] +
        counts["next_season_different"] +
        counts["next_season_ambiguous"]
    ):
        raise ValueError("Next-season site-code partition changed")
    if counts["next_season_direct_positive"] != sum(
        counts[f"first_raw_{a}__next_{b}"] for a in CLASSES for b in CLASSES
    ):
        raise ValueError("First-versus-next seasonal matrix changed")
    if counts["first_raw_before_next_season_detection"] > counts[
        "next_season_direct_positive"
    ]:
        raise ValueError("Earlier encounter subset exceeds qualified followup")
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "NEXT_CALENDAR_BREEDING_SEASON_DIRECT_POSITIVE_ONLY__BIOLOGICAL_HOLD",
        "counts": counts,
        "source_pre2015_date_only_mask": True,
        "no_2015_2022_ID_Island_stage_read": True,
        "raw_individual_or_site_codes_exported": False,
        "next_breeding_positive_proves_recruitment": False,
        "observed_code_change_proves_dispersal": False,
        "surveyed_zero_or_detection_effort_verified": False,
        "independent_heldout_ecological_prediction_scored": False,
        "EOG_WF_3_31_3_changed": False,
    }


def run(checkout: Path) -> dict:
    policy = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    _policy_check(policy)

    original = verified_pre2015_qc(
        checkout, json.loads(FIRST_PROTOCOL.read_text(encoding="utf-8"))
    )
    frozen_first = json.loads(PRIOR_FIRST.read_text(encoding="utf-8"))
    if (original["counts"] != frozen_first["counts"] or
            original.get("original_complete_source_sha256_and_header_verified") is not True):
        raise ValueError("Previously exposed first-followup real-source receipt drifted")
    historical_any = json.loads(PRIOR_ANY.read_text(encoding="utf-8"))
    previous = policy["pre_exposed_expected"]
    cc = historical_any["counts"]
    if not (
        cc["any_later_different_site_id_count"] == previous["any_later_different"] == 451
        and cc["first_same_then_later_different_site_id_count"] ==
            previous["first_same_later_different"] == 228
        and cc["first_followup_different_site_id_count"] ==
            previous["first_different"] == 223
        and historical_any["source"]["source_bytes_and_firstline_independently_verified"] is True
    ):
        raise ValueError("Previously exposed first-versus-ever baseline changed")

    with file_path(checkout, PATH).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        reader = csv.DictReader(handle, delimiter=";", quotechar='"', strict=True)
        physical = json.loads(
            (BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json").read_text(
                encoding="utf-8"
            )
        )
        expected_header = next(
            h["column_names"] for h in physical["headers"]
            if h["github_path"] == PATH
        )
        if list(reader.fieldnames or ()) != expected_header:
            raise ValueError("Frozen physical source header changed")
        result = inspect(reader, policy)
    result["actual_source_sha256_and_header_reverified"] = True
    result["all_original_prior_results_reconciled"] = True
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-checkout", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.upstream_checkout)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite any existing receipt")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "status": result["status"],
        "eligible_birth_cohort_ids": result["counts"]["eligible_birth_cohort_ids"],
        "next_season_direct_positive": result["counts"]["next_season_direct_positive"],
        "ecological_prediction_authorized": False,
    }))


if __name__ == "__main__":
    main()
