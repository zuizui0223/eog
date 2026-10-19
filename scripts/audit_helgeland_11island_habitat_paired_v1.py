#!/usr/bin/env python3
"""Eleven-named-island direct re-detection comparison, NOT a dispersal estimate.

The post-exposure contrast uses all eleven source-internal Island codes, including
Lurøy-Onøy = 33. Only literal 0 ("other helgeland") is excluded for the primary
paired comparison. The entire original PR646 matched cohort is reconstructed and
the PR647 0+33 filtered matrix must reproduce exactly. Full original public file
is 2026-vintage, not a historically held-out 2014 predictor archive.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import date
import json
from pathlib import Path
from typing import Iterable, Mapping

from audit_helgeland_2026_upstream_byte_parity_v1 import file_path
from audit_helgeland_next_breeding_direct_positive_v1 import (
    CLASSES, OUTPUT_SCHEMA as PR646_SCHEMA, run as verify_original_pr646, _which,
)
from audit_helgeland_pre2015_direct_site_code_switch_v1 import (
    BASE, PATH, strict_observed_date,
)
from audit_helgeland_pre2015_island_location_crosswalk_v1 import normalize_label

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = BASE / "helgeland_11island_habitat_paired_protocol_v1.json"
PR646 = BASE / "helgeland_next_breeding_direct_positive_observed_frozen_v1.json"
PR647 = BASE / "helgeland_island_0_33_sensitivity_observed_frozen_v1.json"
PR648 = BASE / "helgeland_pre2015_island_location_crosswalk_observed_frozen_v1.json"
LITERATURE = BASE / "helgeland_2020_2021_island_literature_crosswalk_v1.json"
HEADERS = BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json"

SCHEMA = "eog.helgeland.11island_positive_habitat_paired.protocol.v1"
STATUS = (
    "FROZEN_AFTER_PR646_647_648_EXPOSURE"
    "__BEFORE_NAMED_11_ISLAND_PAIRED_OUTCOME_CLASSIFICATION"
)
RESULT_SCHEMA = "eog.helgeland.11island_positive_habitat_paired.exploratory_receipt.v1"
AUTHOR_SHA = "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
MAIN_SHA = "c7bd38290ddd2c47afdbdc53590985cacf48838b"
DIRECT = frozenset(("nest", "capt", "obs"))
HABITATS = ("farm", "nonfarm")
GROUPS = ("farm_to_farm", "farm_to_nonfarm", "nonfarm_to_farm", "nonfarm_to_nonfarm")
OUTPUTS = (
    "whole_source_rows_date_checked", "pre1994_rows_masked", "post2014_rows_masked",
    "eligible_pre2015_rows", "unique_nest_source_ids", "ambiguous_nest_source_ids",
    "eligible_birth_cohort_ids", "paired_next_year_positive",
    "code_0_direct_rows", "code_33_direct_rows",
    "paired_0_before_or_at_target", "paired_33_before_or_at_target",
    "paired_0_and_33_before_or_at_target", "paired_0_anytime", "paired_0_later_only",
    "named_11_primary_positive", "named_11_full_history_positive",
    "model_0_33_primary_positive", "named_11_primary_discordant",
    "named_11_full_history_discordant", "model_0_33_primary_discordant",
    "named_11_primary_next_different_codes", "named_11_primary_next_same_codes",
    "named_11_primary_33_origin", "named_11_primary_33_next",
    "named_11_primary_33_in_origin_or_target",
)
MATRIX_NAMES = (
    "original_all", "named_11_0_only_pretarget",
    "named_11_0_only_all_history", "model_0_and_33_pretarget",
)
PREVIOUS = {
    "source_raw_rows": 73593, "source_pre2015_rows": 51162,
    "pre1994_rows": 1070, "post2014_rows": 21361,
    "unique_nest_source_IDs": 10737, "eligible_birth_cohort": 10073,
    "paired_IDs": 1313, "paired_original_same_same": 1074,
    "paired_original_same_different": 124,
    "paired_original_different_same": 1,
    "paired_original_different_different": 114,
    "model_0_33_pretarget_clean_n": 1260,
    "model_0_33_pretarget_discordant": 112,
    "model_0_33_same_same": 1047,
    "model_0_33_same_different": 111,
    "model_0_33_different_same": 1,
    "model_0_33_different_different": 101,
}
BOUNDARIES = {
    "post_exposure_exploratory": True,
    "original_1313_and_125_receipts_unchanged": True,
    "post2014_identity_stage_site_unread": True,
    "2026_source_not_contemporaneous_2014_predictors": True,
    "11_island_internal_named_roster_not_independent_2020_code_crosswalk": True,
    "farm_nonfarm_from_published_site_classification_not_proven_individual_mechanism": True,
    "no_dispersal_rate_or_true_recruitment": True,
    "no_survey_effort_detection_correction": True,
    "no_population_founding_or_source_sink_inference": True,
    "no_causal_habitat_preference_inference": True,
    "no_independent_heldout_EOG_score": True,
    "EOG_WF_3_31_3_unchanged": True,
}


def matrix_zero() -> dict[str, int]:
    return {
        f"first_raw_{a}__next_{b}": 0
        for a in CLASSES for b in CLASSES
    }


def _discordant(matrix: dict[str, int]) -> int:
    return sum(
        v for key, v in matrix.items()
        if key.split("__next_")[0].removeprefix("first_raw_")
        != key.split("__next_")[1]
    )


def _validate_protocol(p: dict) -> None:
    if p.get("schema") != SCHEMA or p.get("status") != STATUS:
        raise ValueError("Missing the frozen before-exposure eleven-island contract")
    b = p.get("freeze_basis", {})
    if b != {
        "main_commit": MAIN_SHA,
        "pr646_first_next_paired_frozen": str(PR646.relative_to(ROOT)),
        "pr647_0_33_frozen": str(PR647.relative_to(ROOT)),
        "pr648_code_location_frozen": str(PR648.relative_to(ROOT)),
        "ranke_2021_11_island_habitat_literature": str(LITERATURE.relative_to(ROOT)),
    }:
        raise ValueError("Previously exposed PR646-648 source receipts changed")
    if p.get("source") != {
        "doi": "10.5061/dryad.rr4xgxdnq",
        "dryad_version": 421942,
        "file_id": 4576411,
        "author_commit": AUTHOR_SHA,
        "path": PATH,
        "source_public_since_2026_not_2014": True,
    }:
        raise ValueError("Frozen 2026 source identity or chronology changed")
    if p.get("permitted_observations") != {
        "earliest": "1994-01-01",
        "last": "2014-12-31",
        "inspect_raw_date_before_ID_or_Island": True,
        "read_only_date_on_2015_2022_and_pre1994_rows": True,
        "eligible_raw_fields": ["date", "ID", "Island", "stage"],
        "eligible_direct_stages": ["nest", "capt", "obs"],
        "do_not_read_Year_age_genetics_sex_or_Location": True,
    }:
        raise ValueError("Out-of-time field restriction has changed")
    roster = p.get("study_roster", {})
    if not (
        roster.get("allowed_codes") ==
            ["20", "22", "23", "24", "26", "27", "28", "33", "34", "35", "38"]
        and roster.get("extra_code") == "0"
        and roster.get("extra_code_location") == "other helgeland"
        and roster.get("retained_code") == "33"
        and roster.get("retained_code_location") == "Lurøy-Onøy"
        and roster.get("farm_codes") == ["20", "26", "27", "28", "33", "38"]
        and roster.get("nonfarm_codes") == ["22", "23", "24", "34", "35"]
        and roster.get("habitat_island_class_not_measured_bird_preference") is True
        and roster.get("derive_actual_code_name_and_habitat_from_existing_frozen_receipts") is True
    ):
        raise ValueError("Named 11-island and farm/nonfarm roster changed")
    endpoints = p.get("fixed_paired_endpoint", {})
    if not (
        endpoints.get("same_ID_endpoint_pairs_from_pr646_retained") is True
        and endpoints.get("no_reclassification_after_exclusion") is True
        and endpoints.get("no_detection_denominator_claim") is True
        and "code 0" in endpoints.get("primary_11_island", "")
        and "allow code 33" in endpoints.get("primary_11_island", "")
        and "code 0" in endpoints.get("secondary_full_history", "")
        and "both-0-and-33" in endpoints.get("comparison_10island_model_filtered", "")
    ):
        raise ValueError("Frozen 0-only exposure-time paired-classification rules changed")
    o = p.get("outputs", {})
    if not (
        o.get("permitted_scalar_fields") == list(OUTPUTS)
        and o.get("classification_matrix_names") == list(MATRIX_NAMES)
        and o.get("class_levels") == list(CLASSES)
        and o.get("max_public_code_counts") == 11
        and o.get("only_aggregate_no_ID_raw_dates_or_individual_trajectories") is True
    ):
        raise ValueError("Aggregate-only output or matrix contract changed")
    if p.get("previous_exposed_counts") != PREVIOUS or p.get("scientific_boundaries") != BOUNDARIES:
        raise ValueError("Previously exposed counts or scientific claim bounds changed")


def resolve_site_habitats(p: dict) -> dict[str, dict[str, str]]:
    """Only map 2026 source internal code labels + separately published 2021 habitat labels."""
    _validate_protocol(p)
    frozen_names = json.loads(PR648.read_text(encoding="utf-8"))
    literature = json.loads(LITERATURE.read_text(encoding="utf-8"))
    if not (
        frozen_names.get("schema") ==
            "eog.helgeland.pre2015.island_location_crosswalk.frozen_source_receipt.v1"
        and frozen_names["authority"]["original_dryad_v6_sha256_and_header_verified"] is True
        and frozen_names["receipt"]["counts"]["distinct_code_location_pairs"] == 12
        and frozen_names["receipt"]["counts"]["published_2021_named_labels_observed"] == 11
        and frozen_names["receipt"]["counts"]["codes_with_multiple_normalized_labels"] == 0
        and frozen_names["receipt"]["counts"]["normalized_labels_with_multiple_codes"] == 0
        and literature["counts"]["ranke_2021_named"] == 11
    ):
        raise ValueError("Source code/name or published roster not independently frozen")
    from_literature: dict[str, tuple[str, str]] = {}
    for item in literature["islands"]:
        name = normalize_label(item["name"])
        habitat = item["habitat"]
        if habitat not in HABITATS or name in from_literature:
            raise ValueError("Ambiguous/invalid Ranke 2021 published habitat labels")
        from_literature[name] = (item["name"], habitat)
    resolved = {}
    code_zero_found = False
    for pair in frozen_names["receipt"]["code_location_pairs"]:
        code = pair["island_code_raw"]
        label = pair["location_normalized"]
        if code == "0":
            if label != "other helgeland" or pair["published_2021_name_exact_text"] is not None:
                raise ValueError("Unverified scope of source-internal extra area")
            code_zero_found = True
            continue
        if (
            label not in from_literature
            or pair["published_2021_name_exact_text"] != from_literature[label][0]
            or code in resolved
        ):
            raise ValueError("Code↔site-name↔habitat does not reconcile")
        name, habitat = from_literature[label]
        resolved[code] = {"name": name, "habitat": habitat}
    if not code_zero_found or set(resolved) != set(p["study_roster"]["allowed_codes"]):
        raise ValueError("Named study Island code roster incomplete")
    for code in p["study_roster"]["farm_codes"]:
        if resolved[code]["habitat"] != "farm":
            raise ValueError("Named farm code mismatch")
    for code in p["study_roster"]["nonfarm_codes"]:
        if resolved[code]["habitat"] != "nonfarm":
            raise ValueError("Named nonfarm code mismatch")
    if resolved["33"]["name"] != "Lurøy-Onøy" or resolved["33"]["habitat"] != "farm":
        raise ValueError("Lurøy-Onøy cannot be removed as an unknown code")
    return resolved


def inspect(
    records: Iterable[Mapping[str, str]],
    policy: dict,
    baseline_counts: dict,
    site_habitats: dict[str, dict[str, str]],
    *,
    actual_source: bool = True,
) -> dict:
    """Computes positive-only aggregates. Synthetic fixtures may skip physical-file totals."""
    _validate_protocol(policy)
    if (
        set(site_habitats) != set(policy["study_roster"]["allowed_codes"])
        or site_habitats["33"] != {"name": "Lurøy-Onøy", "habitat": "farm"}
    ):
        raise ValueError("Must use all eleven frozen island codes including 33")
    counts = dict.fromkeys(OUTPUTS, 0)
    matrices = {name: matrix_zero() for name in MATRIX_NAMES}
    habitat_all = dict.fromkeys(GROUPS, 0)
    habitat_different = dict.fromkeys(GROUPS, 0)
    habitat_discordant_sources = dict.fromkeys(HABITATS, 0)
    origin_audit = {
        code: {"code": code, "name": info["name"], "habitat": info["habitat"],
               "paired_positive": 0, "next_same": 0, "next_different": 0,
               "first_same_next_different": 0}
        for code, info in site_habitats.items()
    }
    nest_by_id: dict[str, list[tuple[date, str]]] = defaultdict(list)
    later_by_id: dict[str, list[tuple[date, str]]] = defaultdict(list)
    all_by_id: dict[str, list[tuple[date, str]]] = defaultdict(list)
    lo, hi = date(1994, 1, 1), date(2014, 12, 31)

    for row in records:
        counts["whole_source_rows_date_checked"] += 1
        stamp = strict_observed_date(row["date"])
        if stamp < lo:
            counts["pre1994_rows_masked"] += 1
            continue
        if stamp > hi:
            counts["post2014_rows_masked"] += 1
            continue
        ident = (row["ID"] or "").strip()
        site = (row["Island"] or "").strip()
        stage = (row["stage"] or "").strip()
        if not ident or site not in {*site_habitats, "0"} or stage not in DIRECT:
            raise ValueError("Unexpected direct event, stage, or internal Island roster")
        counts["eligible_pre2015_rows"] += 1
        if site == "0":
            counts["code_0_direct_rows"] += 1
        elif site == "33":
            counts["code_33_direct_rows"] += 1
        all_by_id[ident].append((stamp, site))
        if stage == "nest":
            nest_by_id[ident].append((stamp, site))
        else:
            later_by_id[ident].append((stamp, site))

    for ident, nest_events in nest_by_id.items():
        origins = {s for _, s in nest_events}
        if len(origins) != 1:
            counts["ambiguous_nest_source_ids"] += 1
            continue
        counts["unique_nest_source_ids"] += 1
        source = next(iter(origins))
        birth = min(d for d, _ in nest_events)
        if birth.year > 2013 or birth.month not in (5, 6, 7, 8):
            continue
        counts["eligible_birth_cohort_ids"] += 1
        postnest = [(d, s) for d, s in later_by_id.get(ident, ()) if d > birth]
        next_season = [
            (d, s) for d, s in postnest
            if d.year == birth.year + 1 and d.month in (5, 6, 7, 8)
        ]
        if not next_season:
            continue

        counts["paired_next_year_positive"] += 1
        first_date = min(d for d, _ in postnest)
        next_date = min(d for d, _ in next_season)
        first_codes = {s for d, s in postnest if d == first_date}
        next_codes = {s for d, s in next_season if d == next_date}
        first_class = _which(first_codes, source)
        next_class = _which(next_codes, source)
        matrix_key = f"first_raw_{first_class}__next_{next_class}"
        matrices["original_all"][matrix_key] += 1

        zero_before = any(
            s == "0" and d <= next_date for d, s in all_by_id[ident]
        )
        thirtythree_before = any(
            s == "33" and d <= next_date for d, s in all_by_id[ident]
        )
        zero_ever = any(s == "0" for _, s in all_by_id[ident])
        if zero_before:
            counts["paired_0_before_or_at_target"] += 1
        if thirtythree_before:
            counts["paired_33_before_or_at_target"] += 1
        if zero_before and thirtythree_before:
            counts["paired_0_and_33_before_or_at_target"] += 1
        if zero_ever:
            counts["paired_0_anytime"] += 1
            if not zero_before:
                counts["paired_0_later_only"] += 1

        if not (zero_before or thirtythree_before):
            counts["model_0_33_primary_positive"] += 1
            matrices["model_0_and_33_pretarget"][matrix_key] += 1
            if first_class != next_class:
                counts["model_0_33_primary_discordant"] += 1

        if zero_ever is False:
            counts["named_11_full_history_positive"] += 1
            matrices["named_11_0_only_all_history"][matrix_key] += 1
            if first_class != next_class:
                counts["named_11_full_history_discordant"] += 1

        if zero_before:
            continue
        counts["named_11_primary_positive"] += 1
        matrices["named_11_0_only_pretarget"][matrix_key] += 1
        if first_class != next_class:
            counts["named_11_primary_discordant"] += 1
        if first_class == "ambiguous" or next_class == "ambiguous":
            raise ValueError("Cannot map multiply observed code destinations to habitat")

        target = next(iter(next_codes))
        if source not in site_habitats or target not in site_habitats:
            raise ValueError("After zero-only screening, source/target must be named islands")
        origin_habitat = site_habitats[source]["habitat"]
        target_habitat = site_habitats[target]["habitat"]
        group = f"{origin_habitat}_to_{target_habitat}"
        habitat_all[group] += 1
        origin_audit[source]["paired_positive"] += 1
        if next_class == "same":
            counts["named_11_primary_next_same_codes"] += 1
            origin_audit[source]["next_same"] += 1
        elif next_class == "different":
            counts["named_11_primary_next_different_codes"] += 1
            origin_audit[source]["next_different"] += 1
            habitat_different[group] += 1
        if first_class == "same" and next_class == "different":
            habitat_discordant_sources[origin_habitat] += 1
            origin_audit[source]["first_same_next_different"] += 1
        if source == "33":
            counts["named_11_primary_33_origin"] += 1
        if target == "33":
            counts["named_11_primary_33_next"] += 1
        if source == "33" or target == "33":
            counts["named_11_primary_33_in_origin_or_target"] += 1

    if actual_source:
        expected_physical = {
            "whole_source_rows_date_checked": PREVIOUS["source_raw_rows"],
            "eligible_pre2015_rows": PREVIOUS["source_pre2015_rows"],
            "pre1994_rows_masked": PREVIOUS["pre1994_rows"],
            "post2014_rows_masked": PREVIOUS["post2014_rows"],
            "code_0_direct_rows": 2613,
            "code_33_direct_rows": 1738,
        }
        for key, n in expected_physical.items():
            if counts[key] != n:
                raise ValueError("Whole original source/0/33 count changed: " + key)
    for key, counterpart in (
        ("whole_source_rows_date_checked", "whole_source_rows_date_checked"),
        ("pre1994_rows_masked", "pre1994_rows_masked"),
        ("post2014_rows_masked", "post2014_rows_masked"),
        ("eligible_pre2015_rows", "eligible_pre2015_rows"),
        ("unique_nest_source_ids", "unique_nest_source_ids"),
        ("ambiguous_nest_source_ids", "ambiguous_nest_source_ids"),
        ("eligible_birth_cohort_ids", "eligible_birth_cohort_ids"),
        ("paired_next_year_positive", "next_season_direct_positive"),
    ):
        if counts[key] != baseline_counts[counterpart]:
            raise ValueError("Original PR646 ID cohort/cutoff/matrix denominator drifted")
    expected_original = {k: baseline_counts[k] for k in matrix_zero()}
    if matrices["original_all"] != expected_original:
        raise ValueError("Original PR646 paired original matrix drifted")
    if (
        counts["named_11_primary_positive"] + counts["paired_0_before_or_at_target"]
            != counts["paired_next_year_positive"]
        or counts["named_11_full_history_positive"] + counts["paired_0_anytime"]
            != counts["paired_next_year_positive"]
        or counts["paired_0_later_only"] !=
            counts["paired_0_anytime"] - counts["paired_0_before_or_at_target"]
        or counts["model_0_33_primary_positive"] +
           counts["paired_0_before_or_at_target"] +
           counts["paired_33_before_or_at_target"] -
           counts["paired_0_and_33_before_or_at_target"] !=
           counts["paired_next_year_positive"]
        or counts["named_11_primary_next_different_codes"] +
           counts["named_11_primary_next_same_codes"] !=
           counts["named_11_primary_positive"]
    ):
        raise ValueError("Cannot reconcile nested original, 0-only and 0+33 screens")
    for name, expected_n in (
        ("original_all", counts["paired_next_year_positive"]),
        ("named_11_0_only_pretarget", counts["named_11_primary_positive"]),
        ("named_11_0_only_all_history", counts["named_11_full_history_positive"]),
        ("model_0_and_33_pretarget", counts["model_0_33_primary_positive"]),
    ):
        if sum(matrices[name].values()) != expected_n:
            raise ValueError("Paired matrix does not reconcile: " + name)
    for name, discordant_n in (
        ("named_11_0_only_pretarget", counts["named_11_primary_discordant"]),
        ("named_11_0_only_all_history", counts["named_11_full_history_discordant"]),
        ("model_0_and_33_pretarget", counts["model_0_33_primary_discordant"]),
    ):
        if _discordant(matrices[name]) != discordant_n:
            raise ValueError("Paired classification discordance mismatch: " + name)
    if not (
        sum(habitat_all.values()) == counts["named_11_primary_positive"]
        and sum(habitat_different.values()) == counts["named_11_primary_next_different_codes"]
        and sum(habitat_discordant_sources.values()) ==
            matrices["named_11_0_only_pretarget"]["first_raw_same__next_different"]
        and sum(item["paired_positive"] for item in origin_audit.values()) ==
            counts["named_11_primary_positive"]
        and sum(item["first_same_next_different"] for item in origin_audit.values()) ==
            matrices["named_11_0_only_pretarget"]["first_raw_same__next_different"]
    ):
        raise ValueError("Public 11-island habitat category aggregation incomplete")
    return {
        "schema": RESULT_SCHEMA,
        "status": "POSTEXPOSURE_NAMED_11_ISLAND_POSITIVE_HABITAT_DIAGNOSTIC__BIOLOGY_HOLD",
        "counts": counts,
        "paired_matrices": matrices,
        "habitat_next_positive": habitat_all,
        "habitat_different_code_positive": habitat_different,
        "first_same_next_different_by_origin_habitat": habitat_discordant_sources,
        "per_origin_named_island_positive_counts": [
            origin_audit[code] for code in sorted(origin_audit)
        ],
        "scientific_boundaries": BOUNDARIES,
        "original_source_SHA256_and_header_verified": False,
        "original_PR646_and_PR647_receipts_exactly_reconciled": False,
        "named_11_internal_code_dictionary_and_habitat_list_verified": True,
        "post2014_bird_identity_or_destination_inspected": False,
        "bird_IDs_or_individual_history_exported": False,
        "breeding_recruitment_dispersal_or_colonization_inferred": False,
        "survey_effort_detection_adjusted": False,
        "independent_EOG_forecast_scored": False,
    }


def run(checkout: Path) -> dict:
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    resolved = resolve_site_habitats(p)
    original = verify_original_pr646(checkout)
    previous_646 = json.loads(PR646.read_text(encoding="utf-8"))
    previous_647 = json.loads(PR647.read_text(encoding="utf-8"))
    if not (
        previous_646["receipt"] == original
        and previous_646["authority"]["original_source_sha256_and_header_verified"] is True
        and previous_646["receipt"]["schema"] == PR646_SCHEMA
        and previous_647["authority"]["source_original_sha256_and_header_reverified"] is True
    ):
        raise ValueError("Frozen original PR646 or 647 source identity no longer matches")
    with file_path(checkout, PATH).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        reader = csv.DictReader(handle, delimiter=";", quotechar='"', strict=True)
        frozen_header = json.loads(HEADERS.read_text(encoding="utf-8"))
        expected_header = next(
            entry["column_names"] for entry in frozen_header["headers"]
            if entry["github_path"] == PATH
        )
        if list(reader.fieldnames or ()) != expected_header:
            raise ValueError("Original physical source header changed")
        result = inspect(reader, p, original["counts"], resolved)
    previous_647_matrix = previous_647["receipt"]["matrices"]["strict_pre_target"]
    if not (
        result["paired_matrices"]["model_0_and_33_pretarget"] == previous_647_matrix
        and result["counts"]["model_0_33_primary_positive"] == 1260
        and result["counts"]["model_0_33_primary_discordant"] == 112
    ):
        raise ValueError("Author-model 0+33 prior paired receipt did not reconcile")
    result["original_source_SHA256_and_header_verified"] = True
    result["original_PR646_and_PR647_receipts_exactly_reconciled"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.upstream_checkout)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite original source aggregate")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({
        "status": result["status"],
        "named_11_paired_positive": result["counts"]["named_11_primary_positive"],
        "original_1313_exactly_reconciled": True,
        "ecological_dispersal_rate_authorized": False,
    }))


if __name__ == "__main__":
    main()
