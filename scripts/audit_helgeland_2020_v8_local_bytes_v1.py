#!/usr/bin/env python3
"""Verify *locally provided* 2020 Dryad v8 bytes, first physical line ONLY.

Never contacts Dryad or reads a biological row as data. All three raw files
must be placed outside the repo and supplied explicitly by the user. Full
files are streamed as opaque SHA256 byte blocks. Only the physical first line
is decoded for shape checks, never emitted as values.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from extract_helgeland_verified_firstline_v1 import (
    prepare_write_paths, source_file
)

ROOT = Path(__file__).resolve().parents[1]
FROZEN = (ROOT / "validation/eog_virtual_world_ecology_synthesis_v1" /
          "helgeland_historical_public_vintages_frozen_v1.json")
SOURCE = "niskanen_2020"
DOI = "10.5061/dryad.m0cfxpp10"
VERSION = 78498
HEADER_LIMIT = 4096

# Fixed 2020 v8 records, deliberately NOT v10 / 2023 files.
PINS = {
    "Dryad_readme.txt": (358962, 4137,
        "277c05bb0a676ace6e84df339ac886a033f8426b6b86dc622a792b96bacd5a95"),
    "Pop_size_1997_2012.csv": (358961, 1234,
        "0a47f69ba049b7035bc4d77e4015c0ae2cbdea968f8efbf7368ca34f5ccce638"),
    "Pop_size_1998_2013.csv": (358957, 1266,
        "19c0e551ff754bba10f0f0b19af7ff2598e3ea91968ad2a0b0bdbb0c6ca3a51b"),
}


def opaque_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def firstline_shape(path: Path, name: str) -> dict:
    # Physical first line only; all subsequent content stays unparsed.
    with path.open("rb") as source:
        raw = source.readline(HEADER_LIMIT + 1)
    if len(raw) > HEADER_LIMIT or not raw.endswith(b"\n") or b"\x00" in raw:
        raise ValueError("First physical line missing newline, too long or contains NUL")
    text = raw.decode("utf-8-sig", errors="strict").removesuffix("\n").removesuffix("\r")
    result = {
        "first_physical_line_sha256": hashlib.sha256(raw).hexdigest(),
        "line_length_bytes": len(raw),
        "firstline_values_emitted": False,
        "semantic_header_confirmed": False,
        "other_lines_decoded": False,
    }
    if name.endswith(".csv"):
        possibilities = []
        for sep, label in ((",", "COMMA"), (";", "SEMICOLON"), ("\t", "TAB")):
            try:
                fields = next(csv.reader([text], delimiter=sep, strict=True))
            except csv.Error:
                continue
            if len(fields) > 1 and len(fields) <= 100:
                possibilities.append((label, len(fields)))
        if len(possibilities) != 1:
            raise ValueError("CSV first-line delimiter unqualified or ambiguous")
        result["delimiter"] = possibilities[0][0]
        result["firstline_field_count"] = possibilities[0][1]
    else:
        result["delimiter"] = "UNCLASSIFIED_TEXT"
        result["firstline_field_count"] = None
    return result


def audit(root: Path, frozen: dict) -> tuple[dict, dict]:
    if (frozen.get("schema") !=
        "eog.helgeland.historical_public_dryad_versions.frozen_observed_v1"):
        raise ValueError("Unrecognized historical source evidence")
    inventory = frozen["archives"][SOURCE]
    if (inventory["doi"] != DOI or inventory["version_id"] != VERSION or
        inventory["version_number"] != 8 or
        inventory["published_date"] != "2020-08-19" or
        inventory["cutoff"] != "2020-12-31" or
        inventory["file_count"] != 22):
        raise ValueError("Wrong historic 2020-available source version")
    rows = {entry["name"]: entry for entry in inventory["critical_files"]}
    if set(rows) != set(PINS):
        raise ValueError("Historic 2020 source file set altered")
    evidence = []
    for name, (file_id, size, digest) in PINS.items():
        registered = rows[name]
        if (registered["file_id"] != file_id or
            registered["size_bytes"] != size or
            registered["source_digest_type"] != "sha-256" or
            registered["source_digest"].lower() != digest):
            raise ValueError("Frozen source metadata differs from independent pin")
        source = source_file(root, name)
        if source.stat().st_size != size:
            raise ValueError(f"{name}: v8 source byte size mismatch")
        if opaque_sha256(source) != digest:
            raise ValueError(f"{name}: SHA256 did not match original 2020 v8")
        shape = firstline_shape(source, name)
        evidence.append({
            "file_name": name,
            "dryad_v8_file_id": file_id,
            "size_bytes": size,
            "independent_sha256_matches_2020_v8": True,
            "first_physical_line_only_decoded": True,
            "biological_rows_parsed": False,
            **shape,
        })
    result = {
        "schema": "eog.helgeland.2020_v8.local_byte_header_shape.v1",
        "status": "THREE_LOCALLY_PROVIDED_V8_FILES_HASH_MATCH__ECOLOGY_HOLD",
        "doi": DOI,
        "published_date": "2020-08-19",
        "dryad_version_id": VERSION,
        "records": evidence,
    }
    receipt = {
        "schema": "eog.helgeland.2020_v8.local_byte_attestation_receipt.v1",
        "status": result["status"],
        "mode": "OFFLINE_SOURCE_FILES_ONLY__NO_HTTP",
        "whole_three_source_files_streamed_for_hash": True,
        "physical_headers_semantically_verified": False,
        "other_source_lines_decoded": False,
        "actual_biological_rows_parsed": False,
        "source_files_committed_or_uploaded": False,
        "eight_to_eleven_island_crosswalk_verified": False,
        "surveyed_zero_coverage_verified": False,
        "2021_2022_biological_outcomes_read": False,
        "ecological_forecast_authorized": False,
    }
    return result, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    root, evidence_path, receipt_path = prepare_write_paths(
        args.source_root, args.output, args.receipt
    )
    result, receipt = audit(root, json.loads(FROZEN.read_text(encoding="utf-8")))
    for path in (evidence_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    root, evidence_path, receipt_path = prepare_write_paths(
        root, evidence_path, receipt_path
    )
    created = []
    try:
        for path, value in ((evidence_path, result), (receipt_path, receipt)):
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.write("\n")
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    print(json.dumps({"status": receipt["status"], "files": len(result["records"])}))


if __name__ == "__main__":
    main()
