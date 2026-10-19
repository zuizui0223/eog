#!/usr/bin/env python3
"""Compare already-published 2021 recruit aggregates to frozen EOG positive detections.

This is a documented **estimand mismatch**, not an empirical prediction,
independent replication or validation of natal dispersal. The original 2021
Dryad file bodies were NOT downloaded; the offline optional hash checker only
accepts legitimately obtained, exact SHA256/size-attested raw files and never
parses, uploads or exports their content. No HTTP access or credential bypass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
SOURCE = BASE / "helgeland_ranke2021_published_recruit_comparator_source_v1.json"
FROZEN = BASE / "helgeland_11island_habitat_paired_observed_frozen_v1.json"
FROZEN_SCHEMA = "eog.helgeland.ranke2021_external_recruit_aggregate_comparator_v1"
OUTPUT_SCHEMA = "eog.helgeland.ranke2021_published_recruit_comparator.evidence_boundary_v1"
FILE_IDS = {
    "description.txt": (913633, 3266, "a8dbce0f8d9f84dbf13b0a1197143cfde83feefb2ff93518655dbcb1959aaa4f"),
    "emigration.txt": (913631, 43464, "f97a7b6b776d8e4c09b4529af77722b1506177f06443b802c6ea71d07254db9b"),
    "immigration.txt": (913632, 43527, "166364424d601955f1220b317d60b404d84675f7c5a14e498fb8de4d6a1dd2e6"),
    "island-pairs.txt": (913634, 527964, "c5d4f44a3f3f0987ad2202d66737754238cf199a51eca07d31af46ee48e2226e"),
}
CAT = ("farm_to_farm", "farm_to_nonfarm", "nonfarm_to_farm", "nonfarm_to_nonfarm")
EXPECTED_PUBLISHED = {
    "total_second_calendar_year_recruits": 2192,
    "confirmed_interisland_dispersers": 376,
    "recorded_in_recruitment_year": 357,
    "recorded_later_year": 19,
    "farm_to_farm": 99,
    "farm_to_nonfarm": 19,
    "nonfarm_to_farm": 31,
    "nonfarm_to_nonfarm": 227,
    "published_study_1993_to_2014": True,
    "recruits_in_second_calendar_year_or_later_observed": True,
    "historically_incomplete_nest_searches_and_detection_coverage": True,
}
EXPECTED_PROXY = {
    "main_sha": "946f6108a72d738f976af2a4bf6f08f86c25d897",
    "receipt": "validation/eog_virtual_world_ecology_synthesis_v1/helgeland_11island_habitat_paired_observed_frozen_v1.json",
    "positive_detected_next_calendar_may_aug_ids": 1272,
    "different_island_code_positive_ids": 219,
    "farm_to_farm": 62,
    "farm_to_nonfarm": 7,
    "nonfarm_to_farm": 21,
    "nonfarm_to_nonfarm": 129,
    "first_raw_vs_next_calendar_class_discordant": 118,
    "only_first_same_next_different": 117,
    "original_2026_dryad_source_public_after_2014_cutoff": True,
}
EXPECTED_ACCESS = {
    "2021_raw_file_bodies_sha256_verified": False,
    "2021_description_physical_header_verified": False,
    "2021_year_island_recruit_values_read": False,
    "2021_file_body_download_requires_authorized_access_or_fails": True,
    "earlier_official_download_http_status": 401,
    "alternate_page_antibot_no_data": True,
    "no_auth_bypass_permitted": True,
    "no_file_content_committed": True,
}
EXPECTED_BOUNDS = {
    "aggregate_prevalence_or_habitat_share_agreement_is_NOT_validated_measurement_equivalence": True,
    "2021_recruit_membership_cannot_be_joined_to_2026_raw_ID_cohort_without_shared_key": True,
    "2021_reference_is_published_overlap_not_independent_heldout_confirmation": True,
    "2021_data_unavailable_as_2014_continuous_predictors": True,
    "no_surveyed_zero_or_detection_effort_claim": True,
    "no_recruitment_causal_process_or_true_colonization_fitted": True,
    "no_extra_EOG_WF_scored_endpoint": True,
}


def validate_manifest(m: dict) -> None:
    src = m.get("source", {})
    if (
        m.get("schema") != FROZEN_SCHEMA
        or m.get("status") !=
            "OFFICIAL_2021_DRYAD_METADATA_VERIFIED__RAW_DATA_NOT_ACCESSIBLE__PUBLISHED_RESULTS_ONLY"
        or src.get("study_doi") != "10.1111/1365-2656.13580"
        or src.get("dataset_doi") != "10.5061/dryad.v41ns1rx1"
        or src.get("dataset_id") != 74465 or src.get("version_id") != 136299
        or src.get("first_published") != "2021-08-24"
        or src.get("official_api") != "https://datadryad.org/api/v2/versions/136299/files"
        or m.get("published_recruit_results") != EXPECTED_PUBLISHED
        or m.get("EOG_frozen_proxy") != EXPECTED_PROXY
        or m.get("access_gate") != EXPECTED_ACCESS
        or m.get("scientific_bounds") != EXPECTED_BOUNDS
    ):
        raise ValueError("Official/source/estimand contract changed: STOP")
    files = m.get("files", [])
    if not isinstance(files, list) or len(files) != len(FILE_IDS):
        raise ValueError("Official inventory is not exactly four files")
    observed = {}
    for f in files:
        name = f.get("name")
        if name not in FILE_IDS or name in observed:
            raise ValueError("Unknown/duplicate official filename")
        observed[name] = (
            f.get("file_id"), f.get("size_bytes"), f.get("declared_sha256")
        )
    if observed != FILE_IDS:
        raise ValueError("Official 2021 file ids, sizes, or declared digests changed")


def hash_locally_authorized_files(directory: Path, m: dict) -> dict:
    """Hash-only; never open a body for parsing or access networks.

    The user supplies originals legitimately, e.g. after authorized Dryad login.
    This is an attestation of exact source bytes only, not a scientific data audit.
    """
    files = m.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("No fixed file inventory")
    records = []
    for f in files:
        name = f["name"]
        # Restrict to leaf filenames; disallow symlinks to surprising sources.
        if not name.endswith(".txt") or Path(name).name != name:
            raise ValueError("Unexpected source path")
        path = directory / name
        if not path.is_file() or path.is_symlink():
            raise FileNotFoundError("Required authorized original is missing: " + name)
        size = path.stat().st_size
        if size != f["size_bytes"]:
            raise ValueError("Original source byte-size mismatch: " + name)
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        digest = h.hexdigest()
        if digest != f["declared_sha256"]:
            raise ValueError("Original source SHA256 mismatch: " + name)
        records.append({"name": name, "file_id": f["file_id"], "sha256_matched": True})
    return {
        "status": "FOUR_ORIGINAL_2021_DRYAD_FILE_BYTES_VERIFIED__NO_HEADERS_OR_ROWS_PARSED",
        "files": records,
        "all_four_authorized_source_bytes_sha256_verified": True,
        "file_rows_or_columns_read": False,
        "surveyed_zero_or_2021_2014_forecast_authorized": False,
    }


def compare(m: dict, frozen: dict) -> dict:
    validate_manifest(m)
    if not (
        frozen.get("schema") ==
            "eog.helgeland.11island_positive_habitat_paired.frozen_source_receipt.v1"
        and frozen.get("authority", {}).get(
            "original_sha256_physical_header_and_PR646_647_receipts_reverified"
        ) is True
        and frozen.get("receipt", {}).get("schema") ==
            "eog.helgeland.11island_positive_habitat_paired.exploratory_receipt.v1"
        and frozen.get("receipt", {}).get("scientific_boundaries", {}).get(
            "no_dispersal_rate_or_true_recruitment"
        ) is True
    ):
        raise ValueError("Original EOG 11-island positive-only source receipt invalid")
    rc = frozen["receipt"]["counts"]
    proxy_n = rc["named_11_primary_positive"]
    proxy_diff = rc["named_11_primary_next_different_codes"]
    proxy_first_second = rc["named_11_primary_discordant"]
    habitat = frozen["receipt"]["habitat_different_code_positive"]
    proxy = m["EOG_frozen_proxy"]
    published = m["published_recruit_results"]
    if not (
        proxy_n == proxy["positive_detected_next_calendar_may_aug_ids"] == 1272
        and proxy_diff == proxy["different_island_code_positive_ids"] == 219
        and proxy_first_second == proxy["first_raw_vs_next_calendar_class_discordant"] == 118
        and frozen["receipt"]["paired_matrices"]["named_11_0_only_pretarget"][
            "first_raw_same__next_different"
        ] == proxy["only_first_same_next_different"] == 117
        and all(habitat[k] == proxy[k] for k in CAT)
        and sum(habitat.values()) == proxy_diff
        and sum(published[k] for k in CAT) ==
            published["confirmed_interisland_dispersers"] == 376
        and published["recorded_in_recruitment_year"] +
            published["recorded_later_year"] == 376
    ):
        raise ValueError("Published-vs-frozen EOG aggregate reconciliation failed")
    published_n = published["total_second_calendar_year_recruits"]
    published_d = published["confirmed_interisland_dispersers"]
    proxy_within = habitat["farm_to_farm"] + habitat["nonfarm_to_nonfarm"]
    published_within = published["farm_to_farm"] + published["nonfarm_to_nonfarm"]
    total_variation = (
        0.5 * sum(abs(habitat[k] / proxy_diff - published[k] / published_d)
                  for k in CAT)
    )
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "PUBLISHED_RECRUIT_VS_DIRECT_POSITIVE_AGGREGATE_CONCORDANCE__ESTIMANDS_DIFFER",
        "sources": {
            "published_recruit_2021_doi": m["source"]["study_doi"],
            "published_dataset_doi": m["source"]["dataset_doi"],
            "2021_source_raw_bodies_verified": False,
            "EOG_2026_author_source_receipt_verified": True,
            "individual_or_year_row_join_performed": False,
        },
        "published_confirmed_recruit": {
            "numerator": published_d, "denominator": published_n,
            "different_island_proportion": published_d / published_n,
            "within_habitat_positive_count": published_within,
            "within_habitat_fraction_given_different_island": published_within / published_d,
            "recruits_recorded_after_recruitment_year": published["recorded_later_year"],
        },
        "EOG_next_year_direct_positive": {
            "numerator": proxy_diff, "denominator": proxy_n,
            "different_island_code_proportion": proxy_diff / proxy_n,
            "within_habitat_positive_count": proxy_within,
            "within_habitat_fraction_given_different_island": proxy_within / proxy_diff,
            "first_followup_vs_next_year_discordant_count": proxy_first_second,
            "first_followup_vs_next_year_discordant_fraction": proxy_first_second / proxy_n,
        },
        "descriptive_aggregate_only": {
            "difference_in_proportion_percentage_points": 100 * (
                proxy_diff / proxy_n - published_d / published_n),
            "difference_in_within_habitat_percentage_points": 100 * (
                proxy_within / proxy_diff - published_within / published_d),
            "habitat_transition_distribution_total_variation": total_variation,
            "caveat": "Same geography, largely overlapping periods, different case definitions and sampling; NOT independent replicate or individual-level validation.",
        },
        "published_category_counts": {k: published[k] for k in CAT},
        "proxy_category_counts": {k: habitat[k] for k in CAT},
        "scientific_bounds": m["scientific_bounds"],
        "independent_recruitment_or_movement_validation": False,
        "individual_level_concordance_evaluable": False,
        "claim_of_new_biological_effect": False,
        "EOG_WF_denominator_modified": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--authorized-source-dir", type=Path)
    args = ap.parse_args()
    m = json.loads(SOURCE.read_text(encoding="utf-8"))
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    result = compare(m, frozen)
    result["authenticated_2021_files"] = (
        hash_locally_authorized_files(args.authorized_source_dir, m)
        if args.authorized_source_dir is not None
        else {"status": "2021_ORIGINAL_BYTES_NOT_PRESENT", "all_four_authorized_source_bytes_sha256_verified": False}
    )
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite comparator evidence")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({
        "status": result["status"],
        "individual_level_concordance_evaluable": False,
        "original_2021_source_byte_status": result["authenticated_2021_files"]["status"],
    }))


if __name__ == "__main__":
    main()
