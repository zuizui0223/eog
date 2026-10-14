#!/usr/bin/env python3
"""Post-exposure, positive-only sensitivity to authors' excluded Island codes 0/33.

The frozen PR646 paired result is NEVER changed or reclassified. Flag paired
subjects with original, literal Island codes 0 or 33 before/by next-year first
positive and in all pre-2015 records. Only counts are exported. The result is
not breeding recruitment, true dispersal or prospective EOG validation.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date
import json
from pathlib import Path
from typing import Iterable, Mapping

from audit_helgeland_next_breeding_direct_positive_v1 import (
    PROTOCOL as BASELINE_PROTOCOL,
    run as original_source_verified_run,
    _which,
    CLASSES,
    OUTPUT_SCHEMA as BASELINE_OUTPUT_SCHEMA,
)
from audit_helgeland_pre2015_direct_site_code_switch_v1 import (
    BASE, PATH, strict_observed_date,
)
from audit_helgeland_2026_upstream_byte_parity_v1 import file_path

PROTOCOL = BASE / "helgeland_island_0_33_sensitivity_protocol_v1.json"
PRIOR_RECEIPT = BASE / "helgeland_next_breeding_direct_positive_observed_frozen_v1.json"
AUTHOR_SHA = "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
MAIN_SHA = "4aee2041644ad3159ac09c0aabe99e396a642c2f"
SCHEMA = "eog.helgeland.pre2015.island_0_33_paired_sensitivity.protocol.v1"
STATUS = "FROZEN_POST_PR646_EXPOSURE__BEFORE_0_33_REAL_SOURCE_SENSITIVITY"
RESULT_SCHEMA = "eog.helgeland.pre2015.island_0_33_sensitivity.exploratory_receipt.v1"
DIRECT = frozenset(("nest", "capt", "obs"))
EXCLUDED = frozenset(("0", "33"))
COLS = (
    "whole_rows_date_checked", "pre1994_rows_masked", "post2014_rows_masked",
    "eligible_pre2015_rows", "unique_nest_ids", "ambiguous_nest_ids",
    "eligible_birth_cohort_ids", "next_season_direct_positive",
    "raw_code_0_rows_pre2015", "raw_code_33_rows_pre2015",
    "distinct_ids_with_excluded_codes_pre2015",
    "eligible_cohort_source_code_excluded",
    "paired_source_code_excluded", "paired_first_raw_day_contains_excluded",
    "paired_next_day_contains_excluded",
    "paired_pre_target_excluded", "paired_ever_excluded",
    "paired_later_only_excluded", "paired_pre_target_clean",
    "paired_entire_history_clean",
    "paired_strict_pre_target_discordant",
    "paired_strict_entire_history_discordant",
)
MATRIX_NAMES = ("baseline_exact", "strict_pre_target", "strict_entire_history")
BOUNDARY = {
    "post_exposure_exploratory": True,
    "original_frozen_result_unmodified": True,
    "source_2026_not_historic_2014_predictors": True,
    "post2014_ID_Island_stage_unread": True,
    "no_raw_ID_Island_Location_date_output": True,
    "island_code_crosswalk_to_physical_named_sites_verified": False,
    "surveyed_zero_and_detection_effort_verified": False,
    "true_breeding_recruitment_verified": False,
    "biological_movement_rate_estimated": False,
    "independent_heldout_EOG_forecast_scored": False,
    "EOG_WF_3_31_3_unchanged": True,
}


def validate_contract(policy: dict) -> None:
    if policy.get("schema") != SCHEMA or policy.get("status") != STATUS:
        raise ValueError("Missing pre-committed post-exposure 0/33 protocol")
    src = policy.get("source", {})
    if not (
        src.get("doi") == "10.5061/dryad.rr4xgxdnq"
        and src.get("source_version_id") == 421942
        and src.get("source_file_id") == 4576411
        and src.get("author_git_commit") == AUTHOR_SHA
        and src.get("path") == PATH
        and src.get("raw_date_min") == "1994-01-01"
        and src.get("raw_date_max") == "2014-12-31"
        and src.get("date_mask_before_identity") is True
        and src.get("available_to_2014_forecasters") is False
    ):
        raise ValueError("Unapproved original source or date firewall")
    prior = policy.get("prior", {})
    if not (
        prior.get("main_commit") == MAIN_SHA
        and prior.get("frozen_receipt_path") == str(PRIOR_RECEIPT.relative_to(
            Path(__file__).resolve().parents[1]))
        and prior.get("cohort_id_count") == 10073
        and prior.get("paired_direct_positive_ids") == 1313
        and prior.get("first_same_next_same") == 1074
        and prior.get("first_same_next_different") == 124
        and prior.get("first_different_next_same") == 1
        and prior.get("first_different_next_different") == 114
        and prior.get("paired_discordance") == 125
    ):
        raise ValueError("Frozen prior paired-result identity changed")
    author = policy.get("author_exclusion", {})
    if not (
        author.get("file") == "R scripts/Main model of metapopulation dynamics.R"
        and author.get("source_revision") == AUTHOR_SHA
        and author.get("excluded_literal_island_codes") == ["0", "33"]
        and author.get("mapping_to_named_11_island_roster_established") is False
    ):
        raise ValueError("Authors' exclusion not fixed to literal 0 and 33")
    method = policy.get("methods", {})
    if not (
        method.get("event_exclusion_not_reclassification") is True
        and method.get("no_recruitment_or_dispersal_inference") is True
        and method.get("no_ratio_as_population_dispersal_rate") is True
        and "remove flagged IDs without recomputing" in
            method.get("repeat_paired_classes_not_refit", "")
    ):
        raise ValueError("Paired estimand changed to post-hoc refit")
    outputs = policy.get("outputs", {})
    if (
        outputs.get("scalar_counts") != list(COLS)
        or outputs.get("cross_tab_classes") != list(CLASSES)
        or outputs.get("matrices") != list(MATRIX_NAMES)
        or outputs.get("only_aggregates_no_identifiers") is not True
        or policy.get("scientific_bounds") != BOUNDARY
    ):
        raise ValueError("Changed aggregate output or ecological claim boundary")


def matrix_blank() -> dict[str, int]:
    return {
        f"first_raw_{first}__next_{next_season}": 0
        for first in CLASSES for next_season in CLASSES
    }


def analyze(
    records: Iterable[Mapping[str, str]],
    policy: dict,
    baseline_counts: dict,
) -> dict:
    """Analyze original literal direct codes; never export bird/site trajectories."""
    validate_contract(policy)
    c = dict.fromkeys(COLS, 0)
    matrices = {key: matrix_blank() for key in MATRIX_NAMES}
    nests: dict[str, list[tuple[date, str]]] = defaultdict(list)
    followups: dict[str, list[tuple[date, str]]] = defaultdict(list)
    full_history: dict[str, list[tuple[date, str]]] = defaultdict(list)
    ever_flagged_ids: set[str] = set()
    lo, hi = date(1994, 1, 1), date(2014, 12, 31)

    for row in records:
        c["whole_rows_date_checked"] += 1
        # Nothing except raw physical date can be read outside 1994–2014.
        stamp = strict_observed_date(row["date"])
        if stamp < lo:
            c["pre1994_rows_masked"] += 1
            continue
        if stamp > hi:
            c["post2014_rows_masked"] += 1
            continue
        ident = (row["ID"] or "").strip()
        site = (row["Island"] or "").strip()
        stage = (row["stage"] or "").strip()
        if not ident or not site or stage not in DIRECT:
            raise ValueError("Original direct encounter invalid")
        c["eligible_pre2015_rows"] += 1
        full_history[ident].append((stamp, site))
        if site in EXCLUDED:
            ever_flagged_ids.add(ident)
            c["raw_code_0_rows_pre2015" if site == "0"
              else "raw_code_33_rows_pre2015"] += 1
        if stage == "nest":
            nests[ident].append((stamp, site))
        else:
            followups[ident].append((stamp, site))

    c["distinct_ids_with_excluded_codes_pre2015"] = len(ever_flagged_ids)
    for field, prior_field in (
        ("whole_rows_date_checked", "whole_source_rows_date_checked"),
        ("pre1994_rows_masked", "pre1994_rows_masked"),
        ("post2014_rows_masked", "post2014_rows_masked"),
        ("eligible_pre2015_rows", "eligible_pre2015_rows"),
    ):
        if c[field] != baseline_counts[prior_field]:
            raise ValueError("Full original-source baseline count drifted: " + field)

    for ident, nest_events in nests.items():
        source_codes = {site for _, site in nest_events}
        if len(source_codes) != 1:
            c["ambiguous_nest_ids"] += 1
            continue
        c["unique_nest_ids"] += 1
        source = next(iter(source_codes))
        first_nest = min(stamp for stamp, _ in nest_events)
        if first_nest.year > 2013 or first_nest.month not in (5, 6, 7, 8):
            continue

        c["eligible_birth_cohort_ids"] += 1
        if source in EXCLUDED:
            c["eligible_cohort_source_code_excluded"] += 1
        later = [
            (stamp, site) for stamp, site in followups.get(ident, ())
            if stamp > first_nest
        ]
        next_year = [
            (stamp, site) for stamp, site in later
            if stamp.year == first_nest.year + 1
            and stamp.month in (5, 6, 7, 8)
        ]
        if not next_year:
            continue

        c["next_season_direct_positive"] += 1
        first_date = min(stamp for stamp, _ in later)
        next_date = min(stamp for stamp, _ in next_year)
        first_codes = {site for stamp, site in later if stamp == first_date}
        next_codes = {site for stamp, site in next_year if stamp == next_date}
        first = _which(first_codes, source)
        nxt = _which(next_codes, source)
        matrix_key = f"first_raw_{first}__next_{nxt}"
        matrices["baseline_exact"][matrix_key] += 1

        if source in EXCLUDED:
            c["paired_source_code_excluded"] += 1
        if first_codes & EXCLUDED:
            c["paired_first_raw_day_contains_excluded"] += 1
        if next_codes & EXCLUDED:
            c["paired_next_day_contains_excluded"] += 1

        pretarget = any(
            stamp <= next_date and site in EXCLUDED
            for stamp, site in full_history[ident]
        )
        ever = ident in ever_flagged_ids
        if pretarget:
            c["paired_pre_target_excluded"] += 1
        else:
            c["paired_pre_target_clean"] += 1
            matrices["strict_pre_target"][matrix_key] += 1
            if first != nxt:
                c["paired_strict_pre_target_discordant"] += 1
        if ever:
            c["paired_ever_excluded"] += 1
            if not pretarget:
                c["paired_later_only_excluded"] += 1
        else:
            c["paired_entire_history_clean"] += 1
            matrices["strict_entire_history"][matrix_key] += 1
            if first != nxt:
                c["paired_strict_entire_history_discordant"] += 1

    expected = baseline_counts
    for new_name, prior_name in (
        ("unique_nest_ids", "unique_nest_source_ids"),
        ("ambiguous_nest_ids", "ambiguous_nest_source_ids"),
        ("eligible_birth_cohort_ids", "eligible_birth_cohort_ids"),
        ("next_season_direct_positive", "next_season_direct_positive"),
    ):
        if c[new_name] != expected[prior_name]:
            raise ValueError("Previously frozen 1313 paired-cohort denominator drifted")

    if matrices["baseline_exact"] != {
        name: expected[name] for name in matrix_blank()
    }:
        raise ValueError("Frozen original paired classification matrix drifted")
    total = c["next_season_direct_positive"]
    if not (
        c["paired_pre_target_clean"] + c["paired_pre_target_excluded"] == total
        and c["paired_entire_history_clean"] + c["paired_ever_excluded"] == total
        and c["paired_later_only_excluded"] ==
            c["paired_ever_excluded"] - c["paired_pre_target_excluded"]
        and c["paired_entire_history_clean"] <= c["paired_pre_target_clean"]
        and c["paired_source_code_excluded"] <= c["paired_pre_target_excluded"]
        and c["paired_first_raw_day_contains_excluded"] <=
            c["paired_pre_target_excluded"]
        and c["paired_next_day_contains_excluded"] <=
            c["paired_pre_target_excluded"]
        and sum(matrices["strict_pre_target"].values()) ==
            c["paired_pre_target_clean"]
        and sum(matrices["strict_entire_history"].values()) ==
            c["paired_entire_history_clean"]
    ):
        raise ValueError("0/33 exclusion classifications are not a valid partition")
    if not (
        c["paired_strict_pre_target_discordant"] == sum(
            value for key, value in matrices["strict_pre_target"].items()
            if key.split("__next_")[0].removeprefix("first_raw_") !=
               key.split("__next_")[1]
        )
        and c["paired_strict_entire_history_discordant"] == sum(
            value for key, value in matrices["strict_entire_history"].items()
            if key.split("__next_")[0].removeprefix("first_raw_") !=
               key.split("__next_")[1]
        )
    ):
        raise ValueError("Discordant paired classes and matrices disagree")

    return {
        "schema": RESULT_SCHEMA,
        "status": "PRE2015_ISLAND_CODE_0_33_EXCLUSION_SENSITIVITY__ECOLOGICAL_HOLD",
        "counts": c,
        "matrices": matrices,
        "origin_0_33_rows_not_reclassified_or_removed": True,
        "same_frozen_1313_ID_population_considered": True,
        "author_source_exclusion_equal_to_rederived_11_island_membership": False,
        "full_source_SHA256_and_header_verified": False,
        "pre2015_date_only_identity_mask_enforced": True,
        "post2014_ID_Island_stage_inspected": False,
        "raw_individual_or_island_records_exported": False,
        "breeding_recruitment_or_true_dispersal_inferred": False,
        "surveyed_zero_and_effort_verified": False,
        "new_independent_EOG_forecast_scored": False,
        "EOG_WF_3_31_3_modified": False,
    }


def run(upstream_checkout: Path) -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    validate_contract(protocol)
    # Original source whole-file sha256, physical header and prior aggregate
    # gates are verified in the previously merged, unchanged script.
    prior = original_source_verified_run(upstream_checkout)
    frozen = json.loads(PRIOR_RECEIPT.read_text(encoding="utf-8"))
    if (
        frozen.get("schema") !=
            "eog.helgeland.pre2015.next_breeding_direct_positive.frozen_source_receipt.v1"
        or frozen.get("authority", {}).get("source_author_commit") != AUTHOR_SHA
        or frozen.get("authority", {}).get("original_source_sha256_and_header_verified")
            is not True
        or frozen.get("receipt", {}).get("schema") != BASELINE_OUTPUT_SCHEMA
        or prior != frozen.get("receipt")
    ):
        raise ValueError("Prior original-source PR646 frozen full receipt drifted")
    with file_path(upstream_checkout, PATH).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        reader = csv.DictReader(handle, delimiter=";", quotechar='"', strict=True)
        header = json.loads((
            BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json"
        ).read_text(encoding="utf-8"))
        physical = next(
            h["column_names"] for h in header["headers"] if h["github_path"] == PATH
        )
        if list(reader.fieldnames or ()) != physical:
            raise ValueError("Original source physical header drifted")
        result = analyze(reader, protocol, prior["counts"])
    result["full_source_SHA256_and_header_verified"] = True
    result["original_frozen_receipt_matched_exactly"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.upstream_checkout)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse output overwrite")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as writer:
        json.dump(result, writer, indent=2, sort_keys=True)
        writer.write("\n")
    print(json.dumps({
        "status": result["status"],
        "paired_n": result["counts"]["next_season_direct_positive"],
        "pretarget_clean_n": result["counts"]["paired_pre_target_clean"],
        "no_ecological_prediction_authorized": True,
    }))


if __name__ == "__main__":
    main()
