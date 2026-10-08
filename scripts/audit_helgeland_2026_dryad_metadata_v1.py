#!/usr/bin/env python3
"""Metadata-only Dryad 2026 Helgeland source-identity qualification.

This tool cannot download source files, inspect bird rows, or score EOG.
Only the public DOI JSON and version-specific file-list JSON are permitted.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
from pathlib import Path

from audit_helgeland_dryad_api_inventory_v1 import api_json, VERSION_RE, SHA256_RE

DOI = "10.5061/dryad.rr4xgxdnq"
API = "https://datadryad.org"
EXPECTED = frozenset({
    "Analyses_in_brms_ECY25-1341.R",
    "brm2table_short_ECY25-1341.R",
    "cleaned_density_dependence_data_ECY25-1341.txt",
    "CMR_juvenile_to_adult_one_ind_per_isl_full_model_ECY25-1341.stan",
    "CMR_nest_to_ad_dispersers_ELASTICITY_gen_quant_block_ECY25-1341.stan",
    "CMR2table_adults_ECY25-1341.R",
    "CMR2table_juveniles_ECY25-1341.R",
    "estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy_ECY25-1341.txt",
    "Functions_to_generate_tables_and_figures_from_stan_and_brms_outputs_ECY25-1341.R",
    "Juvenile_mark-recapture_ECY25-1341.R",
    "juvenile_to_ad_surival_histories_long_ECY25-1341.txt",
    "Main_model_of_metapopulation_dynamics_ECY25-1341.R",
    "nestling_producers_2007_2014_ECY25-1341.txt",
    "Parameter_to_latex_ECY25-1341.csv",
    "presence_data_1994_2022_ECY25-1341.txt",
    "README.md",
    "sex_genetically_corrected_ECY25-1341.txt",
    "Tables_and_figures_submission_2_ECY25-1341.R",
})
SCHEMA = "eog.helgeland.dryad_2026.public_json_metadata.v1"


def qualify(dataset: dict, files: dict) -> dict:
    if dataset.get("identifier", "").lower() != ("doi:" + DOI).lower():
        raise ValueError("Dryad 2026 DOI does not match pinned intended source")
    link = dataset.get("_links", {}).get("stash:version", {}).get("href")
    if not isinstance(link, str) or not VERSION_RE.fullmatch(link):
        raise ValueError("Dryad dataset lacks a canonical numeric version link")
    version_id = int(VERSION_RE.fullmatch(link).group(1))
    if files.get("_links", {}).get("self", {}).get("href") != f"/api/v2/versions/{version_id}/files":
        raise ValueError("File-list self link does not match dataset version")
    entries = files.get("_embedded", {}).get("stash:files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("No version-scoped public file metadata")
    if files.get("count") != len(entries) or files.get("total") != len(entries):
        raise ValueError("Dryad metadata inventory incomplete or paginated")
    names = [x.get("path") for x in entries]
    if len(names) != len(set(names)) or set(names) != EXPECTED:
        raise ValueError("2026 inventory differs from the predeclared public 18-file list")
    reported = []
    for item in entries:
        name = item["path"]
        if not isinstance(name, str) or name.startswith(".") or "/" in name or "\\" in name:
            raise ValueError("Unsafe archive file name")
        size = item.get("size")
        file_link = item.get("_links", {}).get("self", {}).get("href")
        digest = item.get("digest")
        digest_type = item.get("digestType")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            raise ValueError("Missing/invalid source file size")
        if not isinstance(file_link, str) or not re.fullmatch(r"/api/v2/files/[0-9]+", file_link):
            raise ValueError("Missing/invalid immutable Dryad file metadata ID")
        reported.append({
            "name": name,
            "file_metadata_id": int(file_link.rsplit("/", 1)[1]),
            "size_bytes": size,
            "source_declared_digest": digest if isinstance(digest, str) else None,
            "source_declared_digest_type": digest_type,
            "source_declared_sha256_well_formed": bool(
                digest_type in ("sha-256", "sha256") and
                isinstance(digest, str) and SHA256_RE.fullmatch(digest)
            ),
            "file_bytes_downloaded": False,
            "physical_header_read": False,
            "biological_rows_read": False,
            "digest_verified_against_file_bytes": False,
        })
    if len({x["file_metadata_id"] for x in reported}) != len(reported):
        raise ValueError("Duplicate source file metadata ID")
    return {
        "schema": SCHEMA,
        "status": ("PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED"
                   if all(x["source_declared_sha256_well_formed"] for x in reported)
                   else "HOLD_SOURCE_DIGEST_INCOMPLETE"),
        "source_doi": DOI,
        "dryad_dataset_id": dataset.get("id"),
        "dryad_version_id": version_id,
        "dryad_version_number": dataset.get("versionNumber"),
        "file_count": len(reported),
        "files": sorted(reported, key=lambda x: x["name"]),
        "source_metadata_only": True,
        "source_reported_digest_is_independent_byte_verification": False,
        "raw_bird_data_downloaded": False,
        "individual_or_population_observations_read": False,
        "surveyed_zero_panel_verified": False,
        "as_of_t_processing_verified": False,
        "ecological_endpoint_authorized": False,
        "original_eog_wf_denominator_unchanged": True,
    }


def audit(fetch=api_json) -> dict:
    url = API + "/api/v2/datasets/" + urllib.parse.quote("doi:" + DOI, safe="")
    try:
        dataset = fetch(url)
        link = dataset.get("_links", {}).get("stash:version", {}).get("href")
        if not isinstance(link, str) or not VERSION_RE.fullmatch(link):
            raise ValueError("Invalid canonical version link")
        observed = qualify(dataset, fetch(API + link + "/files"))
        return observed
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError,
            json.JSONDecodeError) as e:
        return {
            "schema": SCHEMA,
            "status": "HOLD_SOURCE_METADATA_UNVERIFIED",
            "source_doi": DOI,
            "error_type": type(e).__name__,
            "error_summary": str(e)[:160],
            "source_metadata_only": True,
            "raw_bird_data_downloaded": False,
            "individual_or_population_observations_read": False,
            "surveyed_zero_panel_verified": False,
            "as_of_t_processing_verified": False,
            "ecological_endpoint_authorized": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": result["status"],
                      "dryad_version_id": result.get("dryad_version_id"),
                      "file_count": result.get("file_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
