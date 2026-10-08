#!/usr/bin/env python3
"""Offline, bounded first-header-line extraction from locally supplied Dryad files.

No HTTP access or data download. Full source bytes are streamed for SHA-256
verification, but only the first physical line is decoded or parsed.
Never inspect biological records, merge bird IDs, or score an endpoint.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

from qualify_helgeland_header_attestations_v1 import qualification

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT = BASE / "helgeland_header_schema_contract_v1.json"
FROZEN = BASE / "helgeland_source_metadata_frozen_v1.json"
DELIMITERS = {"TAB": "\t", "COMMA": ",", "SEMICOLON": ";"}
HEADER_LIMIT = 4096


def delimiter_assignments(values: list[str], required: set[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for assignment in values:
        if "=" not in assignment:
            raise ValueError("Delimiter must be declared KEY=TAB|COMMA|SEMICOLON|WHITESPACE")
        key, value = assignment.rsplit("=", 1)
        if key not in required or key in result or value not in (*DELIMITERS, "WHITESPACE"):
            raise ValueError("Unknown, duplicate, or invalid declared delimiter")
        result[key] = value
    if set(result) != required:
        raise ValueError("All four source-file delimiters must be explicitly declared")
    return result


def source_file(root: Path, key: str) -> Path:
    # Never follow symlinks in the source directory hierarchy or to a source file.
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Source root must be a real directory")
    path = root
    for part in key.split("/"):
        if part in ("", ".", ".."):
            raise ValueError("Invalid frozen source key")
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinked source paths are forbidden")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Source is not a regular file")
    return path


def sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    # Raw bytes are hashed, never interpreted as bird records.
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tokenize_header(path: Path, declared: str) -> list[str]:
    # readline(size) returns no second logical line to the Python caller.
    with path.open("rb") as stream:
        line = stream.readline(HEADER_LIMIT + 1)
    if len(line) > HEADER_LIMIT or not line.endswith(b"\n"):
        raise ValueError("First physical line missing newline or exceeds 4096 bytes")
    if b"\x00" in line:
        raise ValueError("Binary-looking source header")
    decoded = line[:-1].removesuffix(b"\r").decode("utf-8", errors="strict")
    if declared == "WHITESPACE":
        if "\t" in decoded or "," in decoded or ";" in decoded:
            raise ValueError("Whitespace delimiter ambiguous with explicit separators")
        tokens = re.split(r" +", decoded.strip())
    else:
        sep = DELIMITERS[declared]
        if sep not in decoded:
            raise ValueError("Declared physical delimiter absent from header")
        tokens = decoded.split(sep)
    return tokens


def extract(root: Path, contract: dict, inventory: dict,
            declared: dict[str, str]) -> tuple[dict, dict]:
    required = contract["expected_header_roles"]
    if set(declared) != set(required):
        raise ValueError("Delimiter declaration set differs from frozen four-file contract")
    records = []
    checks = {}
    for key, role in required.items():
        source, filename = key.split("/", 1)
        dataset = inventory["inventories"][source]
        if dataset["doi"] != contract["source_doi_pins"][source]:
            raise ValueError("Frozen DOI differs from header contract")
        if dataset["dryad_version_id"] != contract["expected_source_version_ids"][source]:
            raise ValueError("Frozen Dryad version differs from header contract")
        item = next((f for f in dataset["files"] if f["name"] == filename), None)
        if item is None:
            raise ValueError("Frozen source file missing from inventory")
        path = source_file(root, key)
        if path.stat().st_size != item["size_bytes"]:
            raise ValueError(f"{key}: physical size differs from frozen Dryad metadata")
        independent_digest = sha256_bytes(path)
        if independent_digest != item["source_declared_sha256"]:
            raise ValueError(f"{key}: SHA256 bytes differ from frozen Dryad declaration")
        tokens = tokenize_header(path, declared[key])
        if not set(role["required_exact"]).issubset(tokens):
            raise ValueError(f"{key}: required published columns absent")
        records.append({
            "file_key": key,
            "doi": dataset["doi"],
            "dryad_version_id": dataset["dryad_version_id"],
            "dryad_file_id": item["file_metadata_id"],
            "header_tokens": tokens,
            "delimiter": declared[key],
            "first_line_only": True,
            "contains_response_values": False,
            "independent_extraction_reference": f"sha256-bytes-match-source:{independent_digest}",
        })
        checks[key] = {
            "source_declared_sha256_matched_by_local_byte_hash": True,
            "source_file_bytes_streamed_for_hash": item["size_bytes"],
            "only_first_physical_line_decoded": True,
            "biological_rows_parsed": False,
            "reported_header_token_count": len(tokens),
        }
    evidence = {"schema": "eog.helgeland.header_only_attestation.v1", "records": records}
    verdict = qualification(contract, inventory, evidence)
    if verdict["status"] != "HEADER_NAMES_ATTESTED_KEYS_STILL_UNJOINED":
        raise ValueError("Downstream header qualification did not attain header-only hold")
    receipt = {
        "schema": "eog.helgeland.local_header_byte_identity_receipt.v1",
        "status": "LOCAL_BYTES_MATCH_SOURCE_DIGEST__HEADER_ONLY__KEYS_UNJOINED",
        "extraction_mode": "OFFLINE_LOCAL_FILES_ONLY_NO_NETWORK",
        "checks": checks,
        "individual_id_and_island_values_joined": False,
        "source_loss_or_first_island_colonization_inferred": False,
        "biological_scoring_authorized": False,
        "note": "Four whole files were read as opaque bytes for SHA-256; only each first line was decoded. This does NOT establish cross-archive bird identities, island-code equivalence, detection or ecological effects.",
    }
    return evidence, receipt


def prepare_write_paths(source_root: Path, evidence: Path, receipt: Path
                        ) -> tuple[Path, Path, Path]:
    """Reject symlink redirection, in-source outputs, and any existing output."""
    root = source_root.absolute()
    if any(part.is_symlink() for part in (root, *root.parents)):
        raise ValueError("Raw source directory has a symlinked ancestor")
    if not root.is_dir():
        raise ValueError("Raw source root does not exist")
    canonical_root = root.resolve()
    repo_root = ROOT.resolve()
    if canonical_root == repo_root or repo_root in canonical_root.parents:
        raise ValueError("Raw Dryad source files must stay outside the Git repository")
    if not evidence.name.endswith(".header-only.json"):
        raise ValueError("Header evidence filename must end in .header-only.json")

    outputs = (evidence.absolute(), receipt.absolute())
    canonical_outputs = []
    for path in outputs:
        # Reject existing files including dangling symlinks: no source can be
        # overwritten merely by passing an unsafe output path.
        if path.exists() or path.is_symlink():
            raise ValueError("Refusing to overwrite an existing output or symlink")
        candidate = path.parent.resolve() / path.name
        if candidate == canonical_root or canonical_root in candidate.parents:
            raise ValueError("Output destination resolves inside raw-source directory")
        canonical_outputs.append(candidate)
    if canonical_outputs[0] == canonical_outputs[1]:
        raise ValueError("Header evidence and receipt must have different destinations")
    return root, outputs[0], outputs[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--delimiter", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root, evidence_path, receipt_path = prepare_write_paths(
        args.source_root, args.output, args.receipt
    )
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory = json.loads(FROZEN.read_text(encoding="utf-8"))
    declared = delimiter_assignments(args.delimiter, set(contract["expected_header_roles"]))
    evidence, receipt = extract(root, contract, inventory, declared)
    # Revalidate immediately before writes, including any paths that acquired a
    # symlink or file after the initial preflight. Exclusive open is the last guard.
    for path in (evidence_path, receipt_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    _, evidence_path, receipt_path = prepare_write_paths(root, evidence_path, receipt_path)
    created = []
    try:
        for path, data in ((evidence_path, evidence), (receipt_path, receipt)):
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                json.dump(data, stream, ensure_ascii=False, sort_keys=True, indent=2)
                stream.write("\n")
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    print(json.dumps({"status": receipt["status"], "files": len(evidence["records"])}))


if __name__ == "__main__":
    main()
