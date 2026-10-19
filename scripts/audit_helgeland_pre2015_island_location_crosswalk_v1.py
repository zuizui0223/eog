#!/usr/bin/env python3
"""Read only aggregate 1994–2014 Island CODE ↔ Location LABEL combinations.

The data are a retrospective 2026-published source, NOT historic forecast
features. No bird IDs, individual transitions, stage/age derivatives, late
2015–2022 site values, inferred absences or movement events are produced.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import date
import json
from pathlib import Path
import unicodedata
from typing import Iterable, Mapping

from audit_helgeland_pre2015_direct_site_code_switch_v1 import (
    BASE, PATH, PROTOCOL as FIRST_PROTOCOL,
    strict_observed_date, verified_pre2015_qc,
)
from audit_helgeland_2026_upstream_byte_parity_v1 import file_path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = BASE / "helgeland_pre2015_island_location_crosswalk_protocol_v1.json"
PREVIOUS = BASE / "helgeland_pre2015_first_direct_site_code_frozen_v1.json"
PREVIOUS_033 = BASE / "helgeland_island_0_33_sensitivity_observed_frozen_v1.json"
HEADER = BASE / "helgeland_2026_two_file_physical_headers_frozen_v1.json"

OUTPUT_SCHEMA = "eog.helgeland.pre2015.island_location_crosswalk.exploratory_receipt.v1"
FROZEN_STATUS = "FROZEN_BEFORE_DIRECT_ISLAND_LOCATION_VALUE_AGGREGATION_POST_EXPOSURE"
DIRECT = ("nest", "capt", "obs")
PERIODS = (
    ("1994-2003", date(1994, 1, 1), date(2003, 12, 31)),
    ("2004-2014", date(2004, 1, 1), date(2014, 12, 31)),
)
STUDY_NAMES = (
    "Aldra", "Gjerøy", "Hestmannøy", "Indre Kvarøy", "Lurøy-Onøy",
    "Lovund", "Myken", "Nesøy", "Selvær", "Sleneset", "Træna",
)
NON_SYNONYMS = ("Ytre Kvarøy", "Sundøy")
PREEXPOSED = {
    "total_file_rows": 73593,
    "eligible_rows_pre2015": 51162,
    "rows_before_1994": 1070,
    "rows_after_2014": 21361,
    "raw_island_code_0_eligible_rows": 2613,
    "raw_island_code_33_eligible_rows": 1738,
}
BOUNDS = {
    "source_internal_2026_mapping_only": True,
    "post_exposure_exploratory": True,
    "no_pre2015_year_island_population_effort_certification": True,
    "no_2020_v8_code_crosswalk_certification": True,
    "no_external_geographic_coordinate_verification": True,
    "no_breeding_recruitment_validation": True,
    "no_island_colonization_or_natal_dispersal_inference": True,
    "no_independent_heldout_EOG_predictive_endpoint": True,
    "EOG_WF_denominator_3_31_3_unchanged": True,
}
EXPECTED_EVIDENCE_RULES = {
    "within_2026_file_code_unique_only_if_one_normalized_location_label": True,
    "stable_across_time_bins_only_if_code_observed_in_both_bins_and_same_label": True,
    "a_location_name_may_have_more_than_one_raw_code_and_must_be_reported": True,
    "2021_named_island_label_match_is_text_only_not_geographic_authorization": True,
    "2020_Niskanen_numeric_cross_archive_equivalence_never_inferred": True,
    "zero_observation_in_year_not_absence_or_no_effort": True,
    "source_code_0_33_is_not_automatically_bad_or_not_island": True,
}
EXPECTED_OUTPUT_CONTRACT = {
    "rows_per_code_location_pair_with_time_bins": True,
    "observed_raw_location_variants_per_normalized_label": True,
    "normalized_label_exact_membership_in_2021_names": True,
    "code_to_location_and_location_to_code_cardinalities": True,
    "both_period_mapping_stability_for_codes_observed_twice": True,
    "0_33_location_labels_and_counts_explicit": True,
    "maximum_category_pairs": 80,
    "maximum_unique_raw_codes": 80,
    "maximum_unique_normalized_labels": 80,
    "only_aggregate_public_location_labels_and_raw_codes": True,
    "no_bird_ID_or_individual_sequences": True,
}


def normalize_label(label: str) -> str:
    """NFKC/case/whitespace only; DO NOT collapse spelling or island synonyms."""
    return " ".join(unicodedata.normalize("NFKC", label).split()).casefold()


def verify_protocol(policy: dict) -> None:
    if (
        policy.get("schema") !=
            "eog.helgeland.pre2015.code_location_crosswalk.protocol.v1"
        or policy.get("status") != FROZEN_STATUS
    ):
        raise ValueError("Missing frozen pre-code-label-reading protocol")
    if policy.get("source") != {
        "doi": "10.5061/dryad.rr4xgxdnq",
        "version_id": 421942,
        "file_id": 4576411,
        "author_commit": "a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5",
        "path": PATH,
        "complete_Dryad_v6_SHA256_and_header_first_verified_in_previous_main": True,
        "source_published_in_2026_not_available_to_2014_predictor": True,
    }:
        raise ValueError("Original 2026 source identity or historical scope drifted")
    if policy.get("window") != {
        "min_date": "1994-01-01",
        "max_date": "2014-12-31",
        "read_raw_date_before_any_Island_Location_stage": True,
        "outside_date_window_read_only_date": True,
        "pre2015_direct_stages": list(DIRECT),
        "mapping_time_bins": [
            {"name": label, "first": str(a), "last": str(b)}
            for label, a, b in PERIODS
        ],
    }:
        raise ValueError("Frozen date or time-bin contract drifted")
    if policy.get("raw_access") != {
        "inside_window_allowed": ["date", "Island", "Location", "stage"],
        "ID_never_accessed_by_new_mapping_pass": True,
        "year_age_genotype_imputation_never_accessed": True,
        "case_normalization": (
            "Unicode NFKC, trim outer whitespace, collapse internal spaces, "
            "casefold for comparison only; original literal labels preserved separately"
        ),
        "no_inferred_synonym_or_transliteration": True,
        "raw_code_string_not_recoded_to_model_factor": True,
    }:
        raise ValueError("Illegal raw-data field or normalization change")
    if (
        policy.get("frozen_preexposed_checks") != PREEXPOSED
        or policy.get("published_2021_names") != list(STUDY_NAMES)
        or policy.get("non_synonyms") != list(NON_SYNONYMS)
        or policy.get("strict_evidence_rules") != EXPECTED_EVIDENCE_RULES
        or policy.get("output") != EXPECTED_OUTPUT_CONTRACT
        or policy.get("claim_bounds") != BOUNDS
    ):
        raise ValueError("Frozen 2021 name/crosswalk or scientific claims changed")


def audit(
    records: Iterable[Mapping[str, str]],
    policy: dict,
    *,
    check_real_preexposed: bool = True,
) -> dict:
    """Aggregate public place *labels*, never inspect ID or individual history.

    The override is restricted to fabricated unit fixtures: it keeps all
    scientific protocol constants and outputs fixed, only skips actual-data
    source counts when rows are invented.
    """
    verify_protocol(policy)
    counts = Counter()
    codes = Counter()
    names = Counter()
    bins = Counter()
    pairs = Counter()
    raw_variants: dict[str, set[str]] = defaultdict(set)
    stage_counts = Counter()
    lo, hi = date(1994, 1, 1), date(2014, 12, 31)
    canonical_names = {normalize_label(s): s for s in STUDY_NAMES}
    false_synonyms = {normalize_label(s) for s in NON_SYNONYMS}

    for row in records:
        counts["total_file_rows"] += 1
        stamp = strict_observed_date(row["date"])
        if stamp < lo:
            counts["rows_before_1994"] += 1
            continue
        if stamp > hi:
            counts["rows_after_2014"] += 1
            continue

        # No ID or individual trajectory is ever accessed by this pass.
        code = row["Island"]
        location = row["Location"]
        stage = row["stage"]
        if (
            not isinstance(code, str) or not code.strip() or
            not isinstance(location, str) or not location.strip() or
            not isinstance(stage, str) or stage not in DIRECT or
            len(code) > 30 or len(location) > 120
        ):
            raise ValueError("Bad literal Island/Location or raw direct stage")
        # Literal strings are preserved in output, including codes 0 and 33.
        code, location = code.strip(), location.strip()
        label = normalize_label(location)
        period = PERIODS[0][0] if stamp.year <= 2003 else PERIODS[1][0]
        counts["eligible_rows_pre2015"] += 1
        if code == "0":
            counts["raw_island_code_0_eligible_rows"] += 1
        if code == "33":
            counts["raw_island_code_33_eligible_rows"] += 1
        stage_counts[stage] += 1
        codes[code] += 1
        names[label] += 1
        bins[period] += 1
        pairs[(code, label, period)] += 1
        raw_variants[label].add(location)

    if counts["total_file_rows"] != sum((
        counts["rows_before_1994"], counts["rows_after_2014"],
        counts["eligible_rows_pre2015"]
    )):
        raise ValueError("Inconsistent raw physical-date partition")
    if check_real_preexposed:
        if any(counts[key] != value for key, value in PREEXPOSED.items()):
            raise ValueError("Actual data differ from frozen source/0-33 totals")

    pairs_collapsed = Counter()
    for (code, label, _period), n in pairs.items():
        pairs_collapsed[(code, label)] += n

    if (
        len(pairs_collapsed) > policy["output"]["maximum_category_pairs"]
        or len(codes) > policy["output"]["maximum_unique_raw_codes"]
        or len(names) > policy["output"]["maximum_unique_normalized_labels"]
    ):
        raise ValueError("Excess category cardinality: no public output")

    code_to_names: dict[str, set[str]] = defaultdict(set)
    name_to_codes: dict[str, set[str]] = defaultdict(set)
    for (code, label), _n in pairs_collapsed.items():
        code_to_names[code].add(label)
        name_to_codes[label].add(code)

    mapping = []
    for (code, label), n in sorted(pairs_collapsed.items()):
        mapping.append({
            "island_code_raw": code,
            "location_normalized": label,
            "location_raw_variants": sorted(raw_variants[label]),
            "pair_direct_row_count": n,
            "1994_2003_direct_rows": pairs[(code, label, PERIODS[0][0])],
            "2004_2014_direct_rows": pairs[(code, label, PERIODS[1][0])],
            "published_2021_name_exact_text": canonical_names.get(label),
            "explicit_non_synonym": label in false_synonyms,
        })

    code_status = []
    for code in sorted(codes):
        labels = sorted(code_to_names[code])
        before = {label for label in labels if pairs[(code, label, PERIODS[0][0])]}
        after = {label for label in labels if pairs[(code, label, PERIODS[1][0])]}
        stable = (len(before | after) == 1) if before and after else None
        code_status.append({
            "island_code_raw": code,
            "direct_row_count": codes[code],
            "normalized_location_labels": labels,
            "single_location_label_internal": len(labels) == 1,
            "observed_in_both_time_bins": bool(before and after),
            "same_label_in_both_bins": stable,
            "matches_one_2021_named_label_text_only": (
                len(labels) == 1 and labels[0] in canonical_names
            ),
        })

    location_status = []
    for label in sorted(names):
        location_status.append({
            "location_normalized": label,
            "raw_location_variants": sorted(raw_variants[label]),
            "raw_island_codes": sorted(name_to_codes[label]),
            "direct_row_count": names[label],
            "single_code_internal": len(name_to_codes[label]) == 1,
            "published_2021_name_exact_text": canonical_names.get(label),
            "explicit_non_synonym": label in false_synonyms,
        })

    observed_2021 = sorted(
        [name for label, name in canonical_names.items() if label in names]
    )
    missing_2021 = sorted(set(STUDY_NAMES) - set(observed_2021))
    ambiguous_codes = [x["island_code_raw"] for x in code_status
                       if not x["single_location_label_internal"]]
    ambiguous_locations = [x["location_normalized"] for x in location_status
                           if not x["single_code_internal"]]
    result = {
        "schema": OUTPUT_SCHEMA,
        "status": "RETROSPECTIVE_SOURCE_INTERNAL_CODE_LOCATION_DICTIONARY__ECOLOGICAL_HOLD",
        "source": {
            "dryad_version_id": 421942, "file_id": 4576411,
            "date_mask": "1994-01-01..2014-12-31",
            "2026_source_not_2014_public_predictor": True,
        },
        "counts": {
            **{key: counts[key] for key in PREEXPOSED},
            "nest_rows": stage_counts["nest"],
            "capt_rows": stage_counts["capt"],
            "obs_rows": stage_counts["obs"],
            "period_1994_2003_rows": bins[PERIODS[0][0]],
            "period_2004_2014_rows": bins[PERIODS[1][0]],
            "distinct_raw_island_codes": len(codes),
            "distinct_normalized_location_labels": len(names),
            "distinct_code_location_pairs": len(pairs_collapsed),
            "codes_with_multiple_normalized_labels": len(ambiguous_codes),
            "normalized_labels_with_multiple_codes": len(ambiguous_locations),
            "published_2021_named_labels_observed": len(observed_2021),
            "published_2021_named_labels_not_observed": len(missing_2021),
        },
        "code_location_pairs": mapping,
        "per_code": code_status,
        "per_location": location_status,
        "observed_2021_named_labels": observed_2021,
        "unobserved_2021_named_labels": missing_2021,
        "literal_0_33_rows": {
            x["island_code_raw"]: {
                "row_count": x["direct_row_count"],
                "normalized_location_labels": x["normalized_location_labels"],
            }
            for x in code_status if x["island_code_raw"] in ("0", "33")
        },
        "strict_scope": BOUNDS,
        "individual_IDs_or_trajectories_exported": False,
        "source_code_to_physical_coordinates_verified": False,
        "external_2020_code_equivalence_verified": False,
        "surveyed_zero_or_recruitment_verified": False,
        "independent_EOG_forecast_scored": False,
    }
    return result


def run(source_checkout: Path) -> dict:
    policy = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    verify_protocol(policy)
    previous = json.loads(PREVIOUS.read_text(encoding="utf-8"))
    orig = verified_pre2015_qc(
        source_checkout, json.loads(FIRST_PROTOCOL.read_text(encoding="utf-8"))
    )
    if (
        orig["counts"] != previous["counts"] or
        orig.get("original_complete_source_sha256_and_header_verified") is not True
    ):
        raise ValueError("Original SHA256/header/first-detection counts no longer reproduce")
    sensitivity = json.loads(PREVIOUS_033.read_text(encoding="utf-8"))
    from_033 = sensitivity["receipt"]["counts"]
    if (
        sensitivity.get("authority", {}).get("source_original_sha256_and_header_reverified")
            is not True or
        from_033["raw_code_0_rows_pre2015"] != PREEXPOSED["raw_island_code_0_eligible_rows"] or
        from_033["raw_code_33_rows_pre2015"] != PREEXPOSED["raw_island_code_33_eligible_rows"]
    ):
        raise ValueError("Frozen real original 0/33 source counts inconsistent")

    with file_path(source_checkout, PATH).open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        reader = csv.DictReader(handle, delimiter=";", quotechar='"', strict=True)
        headers = json.loads(HEADER.read_text(encoding="utf-8"))
        expected = next(
            d["column_names"] for d in headers["headers"] if d["github_path"] == PATH
        )
        if list(reader.fieldnames or ()) != expected:
            raise ValueError("Original Dryad-equivalent physical header changed")
        result = audit(reader, policy, check_real_preexposed=True)
    result["frozen_original_sha256_header_first_events_rechecked"] = True
    result["frozen_0_33_row_counts_reconciled"] = True
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-checkout", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    result = run(args.upstream_checkout)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite existing aggregate audit")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")
    print(json.dumps({
        "status": result["status"],
        "category_pairs": result["counts"]["distinct_code_location_pairs"],
        "source_internal_dictionary_only": True,
        "ecological_forecast_authorized": False,
    }))


if __name__ == "__main__":
    main()
