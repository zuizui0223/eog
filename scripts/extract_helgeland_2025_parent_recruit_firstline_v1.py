#!/usr/bin/env python3
"""Offline validation of the four 2025-only Helgeland parent–recruit file headers.

Whole local files are read as opaque bytes for SHA-256, but ONLY their first
physical line is decoded. Never download source files or read bird data rows.
The output attests schema, NOT parentage, temporal direction or settlement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_helgeland_2025_parent_recruit_contract_v1 import (
    CONTRACT, FROZEN, qualify,
)
from extract_helgeland_verified_firstline_v1 import (
    delimiter_assignments, prepare_write_paths, sha256_bytes, source_file,
    tokenize_header,
)
from qualify_helgeland_header_attestations_v1 import SAFE_NAME


def extract_2025(root: Path, contract: dict, inventory: dict,
                 delimiters: dict[str, str]) -> tuple[dict, dict]:
    baseline = qualify(contract, inventory)
    if baseline["status"] != "HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED":
        raise ValueError("Parent–recruit original source-only HOLD changed")
    expected = contract["expected_headers"]
    if set(delimiters) != set(expected):
        raise ValueError("Four explicit declared delimiters are required")
    dataset = inventory["inventories"]["fitness_2025"]
    files = {record["name"]: record for record in dataset["files"]}
    records, checks = [], {}
    for name, expected_role in expected.items():
        archived = files[name]
        if archived["file_metadata_id"] != expected_role["dryad_file_id"]:
            raise ValueError("Frozen Dryad file identity mismatch")
        path = source_file(root, "fitness_2025/" + name)
        if path.stat().st_size != archived["size_bytes"]:
            raise ValueError(f"{name}: file size does not match Dryad v2 archive")
        checksum = sha256_bytes(path)
        if checksum != archived["source_declared_sha256"]:
            raise ValueError(f"{name}: independent SHA256 differs from pinned source digest")
        tokens = tokenize_header(path, delimiters[name])
        if (not 1 <= len(tokens) <= 200 or len(set(tokens)) != len(tokens)
                or not all(isinstance(t, str) and SAFE_NAME.fullmatch(t) for t in tokens)
                or sum(len(t.encode("utf-8")) for t in tokens) > 4096):
            raise ValueError(f"{name}: unsafe or duplicate physical header")
        if not set(expected_role["required_exact"]).issubset(tokens):
            raise ValueError(f"{name}: mandatory README roles missing in physical header")
        records.append({
            "file_name": name,
            "doi": dataset["doi"],
            "dryad_version_id": dataset["dryad_version_id"],
            "dryad_file_id": archived["file_metadata_id"],
            "header_tokens": tokens,
            "delimiter": delimiters[name],
            "first_physical_line_only": True,
            "source_sha256_byte_match": True,
            "observation_rows_parsed": False,
        })
        checks[name] = {
            "source_file_bytes_streamed_for_hash": archived["size_bytes"],
            "source_declared_sha256_matches_independent_local_bytes": True,
            "only_first_physical_line_decoded": True,
            "biological_values_scored": False,
        }

    attestation = {
        "schema": "eog.helgeland.2025_parent_recruit.firstline_attestation.v1",
        "status": "PHYSICAL_HEADERS_AND_BYTES_MATCH__KEY_VALUES_UNJOINED",
        "source_doi": dataset["doi"],
        "source_version_id": dataset["dryad_version_id"],
        "records": records,
    }
    receipt = {
        "schema": "eog.helgeland.2025_parent_recruit.firstline_receipt.v1",
        "status": "HEADER_ONLY_BYTE_IDENTITY_VERIFIED__TEMPORAL_HOLD",
        "files_checked": len(records),
        "checks": checks,
        "whole_source_file_bytes_read_for_hash": True,
        "biological_response_rows_parsed": False,
        "parent_recruit_key_values_joined": False,
        "parent_breeding_island_at_offspring_birth_verified": False,
        "offspring_first_settlement_time_and_island_verified": False,
        "independent_observation_effort_verified": False,
        "prospective_prediction_authorized": False,
        "first_island_colonization_or_source_loss_identified": False,
        "ecological_endpoint_authorized": False,
        "original_source_only_hold": baseline["status"],
    }
    return attestation, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--delimiter", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory = json.loads(FROZEN.read_text(encoding="utf-8"))
    declarations = delimiter_assignments(args.delimiter,
                                          set(contract["expected_headers"]))
    root, evidence_path, receipt_path = prepare_write_paths(
        args.source_root, args.output, args.receipt)
    attestation, receipt = extract_2025(root, contract, inventory, declarations)
    for path in (evidence_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    _, evidence_path, receipt_path = prepare_write_paths(
        root, evidence_path, receipt_path)
    created = []
    try:
        for path, value in ((evidence_path, attestation), (receipt_path, receipt)):
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=False)
                stream.write("\n")
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    print(json.dumps({"status": receipt["status"], "files": receipt["files_checked"]}))


if __name__ == "__main__":
    main()
