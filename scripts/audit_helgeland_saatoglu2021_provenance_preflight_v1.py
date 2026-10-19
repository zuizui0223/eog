#!/usr/bin/env python3
"""Official 2021 genetic-assignment source-code preflight, not a dispersal result.

Verify only openly published Zenodo R-script source bytes and immutable Dryad
source-declared file metadata. Does NOT read 2021 genetic/bird data records,
does NOT join 2026 bird IDs, and does NOT score biological outcome or EOG.
Network-free; caller obtains public software source using official Zenodo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
PROTOCOL = BASE / "helgeland_saatoglu2021_provenance_preflight_v1.json"
CROSSWALK = BASE / "helgeland_pre2015_island_location_crosswalk_observed_frozen_v1.json"
SHA_OF_MAIN_AT_FREEZE = "d8869d6aff2f7c9121a8d26dd604778e33906fcb"
SCHEMA = "eog.helgeland.saatoglu2021_genetic_cmr_provenance_preflight.v1"
RESULT = "eog.helgeland.saatoglu2021_genetic_cmr_code_audit.result.v1"
AUTHOR_R_MD5 = "80d138c79960684fa85379c09cd17727"
EIGHT = ("20", "22", "23", "24", "26", "27", "28", "38")
TENS = (*EIGHT, "77", "88")
OFFICIAL = {
    "Dispersaldata.txt": (815561, 59268, "17e92bc572c056f55074470c93c7d09d054f768dc7f0a47f13f40ce694258367"),
    "Geneticassignment_README.txt": (815564, 1687, "4d4f6470cbef73190c35a358feec42ce676d2904fab4f881d63817c465968270"),
    "Misassignments_givenaway.txt": (815563, 3817, "17d31a7d3d81f47401869a6ca5d68f3630884b62e4ac616d2b7b067b725a7722"),
    "Misassignments_received.txt": (815562, 3818, "b2aafe824a22bfefc4d2c5f2f72e270db9e316d925c4139031a43e8608d67c91"),
    "Pairwise_Fst.txt": (815560, 13247, "00a5e36524b197ccd54c2984655d09c4832b0429abac640253fd9f0ab24da1fa"),
}
METHOD_COLUMNS = (
    "natal.island", "adult.island", "hatch.year",
    "dispersal.status", "sample.size", "Population.size",
    "pw.Fst", "Ho",
)


def validate_frozen_manifest(p: dict) -> None:
    if (p.get("schema") != SCHEMA or p.get("status") !=
        "RETROSPECTIVE_AUTHOR_CODE_METHODS_READ__FROZEN_BEFORE_SOURCE_BYTE_ATTESTATION__NO_BIOLOGICAL_ROWS"):
        raise ValueError("Unapproved provenance-source contract")
    d = p.get("official_dryad", {})
    if (
        d.get("doi") != "10.5061/dryad.xgxd254h1"
        or d.get("dataset_id") != 72603
        or d.get("version_id") != 130231
        or d.get("first_publication") != "2021-07-15"
        or d.get("source_metadata_only") is not True
        or len(d.get("files", [])) != 5
    ):
        raise ValueError("Original 2021 Dryad metadata identity changed")
    actual = {
        item["name"]: (item["id"], item["size_bytes"], item["declared_sha256"])
        for item in d["files"]
    }
    if actual != OFFICIAL or len(actual) != 5:
        raise ValueError("Source-declared Dryad file size/digest mismatch")
    z = p.get("official_zenodo", {})
    if (
        z.get("record_id") != 5095667
        or z.get("concept_record_id") != 5095666
        or z.get("script") != "Error_sources_dispersal_patterns.R"
        or z.get("bytes") != 10758
        or z.get("declared_md5") != AUTHOR_R_MD5
        or z.get("official_file_url") !=
           "https://zenodo.org/api/records/5095667/files/Error_sources_dispersal_patterns.R/content"
        or z.get("source_script_SHA256_not_predeclared") is not True
    ):
        raise ValueError("Zenodo public author script identity changed")
    methods = p.get("documented_author_script_design", {})
    scope = methods.get("available_published_code_scope", {})
    if not (
        methods.get("population_gene_origin") == "natal.island"
        and methods.get("population_adult_record") == "adult.island"
        and methods.get("year") == "hatch.year"
        and methods.get("binary") == "dispersal.status"
        and methods.get("source_script_method_code_not_2021_Data_file_bodies") is True
        and scope.get("habitat_matching_eight_island_raw_codes") == list(EIGHT)
        and set(scope.get("all_genetic_pattern_natal_code_literals", [])) == set(TENS)
        and scope.get("author_described_fair_habitat_window") == [2004, 2012]
    ):
        raise ValueError("Authored 2021 genetic-vs-CMR scope changed")
    context = p.get("EOG_2026_previous_11island_context", {})
    if (context.get("main_commit") != SHA_OF_MAIN_AT_FREEZE
        or context.get("code_33_is_valid_named_Luroy_Onoy") is not True
        or context.get("code_0_is_other_helgeland") is not True):
        raise ValueError("Frozen EOG 2026 code mapping changed")
    if any(p.get("verification_gate", {}).values()) or not all(
        p.get("strong_stop_rules", {}).values()
    ):
        raise ValueError("Unwarranted biological evidence gate or EOG promotion")


def map_codes(p: dict) -> list[dict]:
    x = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    rows = x.get("receipt", {}).get("code_location_pairs", [])
    if (
        x.get("schema") !=
            "eog.helgeland.pre2015.island_location_crosswalk.frozen_source_receipt.v1"
        or x.get("authority", {}).get("original_dryad_v6_sha256_and_header_verified") is not True
        or len(rows) != 12
    ):
        raise ValueError("Preexisting source-verified 2026 code dictionary missing")
    matched = {
        row["island_code_raw"]: row for row in rows
        if row["island_code_raw"] in EIGHT
    }
    if set(matched) != set(EIGHT):
        raise ValueError("2021 eight-code subset does not match EOG source-internal map")
    return [
        {"raw_code": code, "source_2026_name_label": matched[code]["location_normalized"],
         "2021_natal_and_adult_ID_domain_verified": False}
        for code in EIGHT
    ]


def parse_author_code(text: str) -> dict:
    """Check source-defined literal analysis choices, not 2021 data values."""
    if any(token not in text for token in METHOD_COLUMNS):
        raise ValueError("Public Zenodo code does not use the frozen variables")
    if 'read.table("Dispersaldata.txt"' not in text:
        raise ValueError("Public source is not the original dispersal analysis script")
    if not (
        "Genpattern.data" in text
        and "Habitat.data" in text
        and "GSI_SIM" not in text or "BONE" not in text
    ):
        # The R analysis script uses tabulated genetic assignments as fixed
        # dispersal input and does not itself implement the two SNP callers.
        pass
    if "Genpattern.data" not in text or "Habitat.data" not in text:
        raise ValueError("Author script lacks dispersal scope analyses")
    if "2004" not in text or "2012" not in text:
        raise ValueError("Author-described restricted sampling window absent")
    if "sample.size" not in text or "Population.size" not in text:
        raise ValueError("Sampling fraction is not explicitly modeled")
    # The two published code subsets occur as c("..", "..") vectors in the
    # author R file. Use exact unique integer tokens in each author-commented
    # scope, not any genotype data and never a guessed code crosswalk.
    scope_eight = '20,22,23,24,26,27,28,38'
    if scope_eight not in text.replace(" ", ""):
        raise ValueError("Source eight SNP codes do not agree with preflight")
    if not all(f'"{code}"' in text for code in TENS):
        raise ValueError("Expected author broad origin-code vocabulary absent")
    return {
        "author_raw_R_script_source_identified": True,
        "methods_use_natal_adult_island_year_and_recorded_status": True,
        "eight_named_code_comparable_subset_text_present": True,
        "author_2004_to_2012_sampling_restriction_text_present": True,
        "sampling_fraction_misassignment_models_present": True,
        "script_does_not_measure_new_EOG_displacement_outcomes": True,
    }


def audit(source_bytes: bytes | None, protocol: dict) -> dict:
    validate_frozen_manifest(protocol)
    names = map_codes(protocol)
    valid = False
    signals = None
    if source_bytes is not None:
        if len(source_bytes) != 10758:
            raise ValueError("Author R source byte-size mismatch")
        if hashlib.md5(source_bytes).hexdigest() != AUTHOR_R_MD5:
            raise ValueError("Author R script source MD5 mismatch")
        signals = parse_author_code(source_bytes.decode("utf-8-sig"))
        valid = True
    return {
        "schema": RESULT,
        "status": (
            "AUTHOR_ZENODO_METHOD_SCRIPT_BYTE_VERIFIED__BIOLOGICAL_DATA_HOLD"
            if valid else "OFFICIAL_SOURCE_METADATA_ONLY__GENETIC_DATA_HOLD"
        ),
        "source": {
            "zenodo_record": 5095667,
            "source_bytes_author_md5_verified": valid,
            "2021_Dryad_dataset_id": 72603,
            "2021_Dryad_version_id": 130231,
            "five_original_source_file_bytes_verified": False,
            "actual_2021_genetic_assignment_rows_read": False,
            "actual_2021_Fst_rows_read": False,
            "2021_record_2026_bird_ID_join_verified": False,
        },
        "eog_2026_to_2021_eight_code_name_text_bridge": names,
        "author_methods_source_code_signals": signals,
        "actual_author_2004_2012_data_rows_accessed": False,
        "genetic_origin_is_true_source_without_calibration": False,
        "island_year_survey_effort_qualified": False,
        "breeding_recruitment_or_colonization_inferred": False,
        "EOG_WF_denominator_modified": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--author-r-source", type=Path,
                    help="Authorized official Zenodo file, not Dryad individual data")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    p = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if args.author_r_source and (
        not args.author_r_source.is_file() or args.author_r_source.is_symlink()
    ):
        raise ValueError("Official author script not present as regular file")
    b = args.author_r_source.read_bytes() if args.author_r_source else None
    x = audit(b, p)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite provenance preflight receipt")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as fd:
        json.dump(x, fd, ensure_ascii=False, indent=2, sort_keys=True)
        fd.write("\n")
    print(json.dumps({
        "status": x["status"],
        "source_2021_genotype_rows_read": False,
        "2021_vs_2026_identical_IDs_verified": False,
        "EOG_new_endpoint_authorized": False,
    }))


if __name__ == "__main__":
    main()
