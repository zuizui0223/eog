#!/usr/bin/env python3
"""Attest ONLY first physical header lines after two SHA-256-confirmed source files.

No source download, biological row decode, island-year absence inference or scores.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from audit_helgeland_2026_upstream_byte_parity_v1 import (
    FROZEN, TARGETS, UPSTREAM_COMMIT, audit as verify_bytes, file_path
)

REQUIRED = {
    "Data/presence_data_1994_2022.txt":
        {"ID", "Year", "date", "Island", "Location", "stage"},
    "Data/estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt":
        {"Location", "Island", "Year", "N_corr", ".lower", ".upper", ".width", "N_obs"},
}
COLUMN_NAME = re.compile(r"^[A-Za-z_.][A-Za-z0-9_.-]{0,127}$")
HEADER_BYTES_LIMIT = 4096
SCHEMA = "eog.helgeland.dryad2026.two_file_physical_headers.v1"


def read_first_physical_header(path: Path) -> tuple[list[str], str]:
    """No second line is ever decoded or passed to csv.reader."""
    with path.open("rb") as stream:
        raw = stream.readline(HEADER_BYTES_LIMIT + 1)
    if not raw.endswith(b"\n") or len(raw) > HEADER_BYTES_LIMIT or b"\x00" in raw:
        raise ValueError("Header exceeds byte limit, has no newline or contains NUL")
    decoded = raw.decode("utf-8-sig", errors="strict")
    fields = next(csv.reader([decoded], delimiter=";", quotechar='"', strict=True))
    if (not 1 <= len(fields) <= 200
            or len(set(fields)) != len(fields)
            or not all(COLUMN_NAME.fullmatch(name) for name in fields)):
        raise ValueError("Unsafe, duplicate or unparseable first-line column names")
    return fields, hashlib.sha256(raw).hexdigest()


def attest(root: Path, frozen: dict) -> dict:
    if set(REQUIRED) != set(TARGETS):
        raise ValueError("Header contract deviates from two source byte-parity targets")
    byte_result = verify_bytes(root, frozen)
    if byte_result["status"] != "MATCHES_TWO_FROZEN_DRYAD_V6_FILES":
        raise ValueError("Cannot attest header without complete exact SHA-256 byte parity")
    headers = []
    for upstream_path in TARGETS:
        tokens, line_sha256 = read_first_physical_header(file_path(root, upstream_path))
        if not REQUIRED[upstream_path].issubset(tokens):
            raise ValueError(f"{upstream_path}: required predeclared schema fields missing")
        matched_byte_record = next(
            x for x in byte_result["files"] if x["upstream_repo_path"] == upstream_path
        )
        if not matched_byte_record["upstream_sha256_matches_dryad_declared_digest"]:
            raise ValueError("Header's source file was not matched by byte SHA-256")
        headers.append({
            "github_path": upstream_path,
            "dryad_name": TARGETS[upstream_path],
            "dryad_file_id": matched_byte_record["dryad_file_metadata_id"],
            "delimiter": "SEMICOLON",
            "actual_first_line_column_names": tokens,
            "physical_first_line_sha256": line_sha256,
            "source_whole_byte_sha256_matches_dryad_v6": True,
            "biological_data_rows_decoded": False,
        })
    return {
        "schema": SCHEMA,
        "status": "TWO_DRYAD_V6_PHYSICAL_HEADERS_ATTESTED__ECOLOGY_HOLD",
        "dryad_version_id": 421942,
        "upstream_commit": UPSTREAM_COMMIT,
        "headers": headers,
        "files": 2,
        "whole_file_bytes_streamed_for_hash": True,
        "only_first_physical_lines_decoded": True,
        "biological_data_rows_decoded": False,
        "island_year_surveyed_zero_panel_verified": False,
        "same_id_first_recruit_movement_verified": False,
        "observation_available_as_of_t_verified": False,
        "heldout_benchmark_qualified": False,
        "ecological_endpoint_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    report = attest(args.upstream_checkout, frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "header_files": report["files"]}))


if __name__ == "__main__":
    main()
