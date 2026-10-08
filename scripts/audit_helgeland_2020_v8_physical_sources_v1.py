#!/usr/bin/env python3
"""Read-only, bounded Dryad 2020 v8 source byte/hash + first-line shape audit.

Explicitly downloads THREE public, historically pinned small source files.
All bytes are hashed as opaque chunks, only each first physical line is decoded,
and neither individual nor island-year observation rows are interpreted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FROZEN = (ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
          / "helgeland_historical_public_vintages_frozen_v1.json")
VERSION = 78498
DOI = "10.5061/dryad.m0cfxpp10"
HEADER_LIMIT = 4096
# Explicitly frozen names / IDs, not fuzzy web searches or latest DOI version.
SELECTED_NAMES = frozenset((
    "Dryad_readme.txt",
    "Pop_size_1997_2012.csv",
    "Pop_size_1998_2013.csv",
))


def opaque_file_download(file_id: int, max_bytes: int) -> tuple[str, int, bytes]:
    """Never interpret after the first physical line; discard all raw body chunks."""
    if file_id not in (358962, 358961, 358957):
        raise ValueError("File ID not in preselected 2020 Dryad v8 source set")
    url = f"https://datadryad.org/api/v2/files/{file_id}/download"
    request = urllib.request.Request(
        url, headers={"User-Agent": "EOG-public-vintage-header-byte-audit/1.0"})
    digest = hashlib.sha256()
    count = 0
    first = bytearray()
    first_complete = False
    with urllib.request.urlopen(request, timeout=30) as stream:
        if not stream.geturl().startswith("https://"):
            raise ValueError("Unsafe source redirect scheme")
        for block in iter(lambda: stream.read(65536), b""):
            count += len(block)
            if count > max_bytes:
                raise ValueError("Source bytes exceed registered file size")
            digest.update(block)
            if not first_complete:
                piece = block.split(b"\n", 1)
                first.extend(piece[0][:HEADER_LIMIT + 1 - len(first)])
                first_complete = len(piece) == 2
                if first_complete:
                    first.extend(b"\n")
                if len(first) > HEADER_LIMIT + 1:
                    raise ValueError("First physical line too long")
    if not first_complete or not first.endswith(b"\n"):
        raise ValueError("First line absent or unterminated")
    return digest.hexdigest(), count, bytes(first)


def firstline_shape(raw: bytes) -> dict:
    if not raw.endswith(b"\n") or len(raw) > HEADER_LIMIT + 1 or b"\x00" in raw:
        raise ValueError("Invalid bounded first line")
    line = raw.decode("utf-8-sig", errors="strict").rstrip("\r\n")
    separators = {x: line.count(x) for x in (";", ",", "\t")}
    candidates = [x for x, n in separators.items() if n]
    if len(candidates) != 1:
        return {
            "delimiter": "HOLD_AMBIGUOUS_PHYSICAL_SEPARATOR",
            "firstline_field_count": None,
            "firstline_sha256": hashlib.sha256(raw).hexdigest(),
            "physical_semantic_header_attested": False,
        }
    chosen = candidates[0]
    values = next(csv.reader([line], delimiter=chosen, quotechar='"', strict=True))
    return {
        "delimiter": {";": "SEMICOLON", ",": "COMMA", "\t": "TAB"}[chosen],
        "firstline_field_count": len(values),
        "firstline_sha256": hashlib.sha256(raw).hexdigest(),
        "physical_semantic_header_attested": False,  # values NOT output or classified
    }


def audit(frozen: dict, fetch=opaque_file_download) -> dict:
    if frozen.get("schema") != "eog.helgeland.historical_public_dryad_versions.frozen_observed_v1":
        raise ValueError("Unrecognized historical frozen source schema")
    source = frozen["archives"]["niskanen_2020"]
    if (source["doi"] != DOI or source["version_id"] != VERSION or
        source["version_number"] != 8 or
        source["published_date"] != "2020-08-19" or
        source["cutoff"] != "2020-12-31"):
        raise ValueError("Wrong historically published Dryad version")
    catalog = {x["name"]: x for x in source["critical_files"]}
    if set(catalog) != SELECTED_NAMES:
        raise ValueError("Unexpected historical source-file set")
    entries = []
    for name in sorted(SELECTED_NAMES):
        item = catalog[name]
        if (item["source_digest_type"] != "sha-256" or
            not isinstance(item["source_digest"], str) or
            len(item["source_digest"]) != 64):
            raise ValueError("Registered 2020 SHA-256 missing or unsupported")
        digest, count, physical = fetch(item["file_id"], item["size_bytes"])
        if count != item["size_bytes"] or digest.lower() != item["source_digest"].lower():
            raise ValueError(f"{name}: independent actual source bytes differ from public v8")
        shape = firstline_shape(physical)
        entries.append({
            "dryad_name": name,
            "dryad_file_id": item["file_id"],
            "source_byte_count": count,
            "whole_file_sha256_verified": True,
            **shape,
            "firstline_values_emitted": False,
            "other_physical_lines_decoded": False,
            "data_records_parsed": False,
        })
    return {
        "schema": "eog.helgeland.niskanen2020_v8.firstline_byte_attestation.v1",
        "status": "THREE_2020_V8_SOURCE_SHA256S_MATCH__FIRSTLINE_SHAPE_ONLY",
        "historically_published_date": source["published_date"],
        "source_doi": DOI,
        "source_version_id": VERSION,
        "records": entries,
        "entire_three_source_files_streamed_for_hash": True,
        "biological_data_rows_parsed": False,
        "firstline_values_emitted": False,
        "observation_model_baseline_constructed": False,
        "island_name_crosswalk_verified": False,
        "surveyed_absence_coverage_verified": False,
        "future_2021_2022_outcomes_read": False,
        "ecological_forecast_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    report = audit(frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "files": len(report["records"])}))


if __name__ == "__main__":
    main()
