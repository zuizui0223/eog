#!/usr/bin/env python3
"""Neckera Gate 0: prospective estimability + ZIP member/header inventory only."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)

TEXT_EXT = {".csv", ".tsv", ".txt", ".tab", ".dat"}
DOC_NAMES = ("readme", "codebook", "metadata", "variable")


@dataclass(frozen=True)
class ZipFirstRecord:
    data: bytes
    terminator: str
    bytes_consumed: int


def read_zip_first_record(stream, *, max_record_bytes: int = 16_384) -> ZipFirstRecord:
    """Read one ZIP member byte-by-byte and stop at its first physical CR/LF."""
    if isinstance(max_record_bytes, bool) or not isinstance(max_record_bytes, int) or max_record_bytes <= 0:
        raise ValueError("max_record_bytes must be a positive integer")
    buffer = bytearray()
    while len(buffer) < max_record_bytes:
        value = stream.read(1)
        if value == b"":
            raise ValueError("physical record terminator not found before EOF")
        if value == b"\r":
            return ZipFirstRecord(bytes(buffer), "CR", len(buffer) + 1)
        if value == b"\n":
            return ZipFirstRecord(bytes(buffer), "LF", len(buffer) + 1)
        buffer.extend(value)
    raise ValueError("physical first record exceeds frozen byte bound")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=10,
        calibration_non_events=40,
        heldout_events=10,
        heldout_non_events=40,
        heldout_outer_units_with_both_classes=1,
    )
    evidence = AggregateEstimabilityEvidence(
        source_label="published Neckera repeated-survey aggregates fixed before SND row access",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=38),
            "calibration_non_events": AggregateCountInterval(lower=1039),
            "heldout_events": AggregateCountInterval(lower=32, upper=32),
            "heldout_non_events": AggregateCountInterval(lower=152, upper=152),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=1, upper=1),
        },
        note="1997-2001 classic survey and published 2001-2008 temporal resurvey aggregate",
    )
    est = evaluate_prospective_estimability(declaration, evidence)

    manifest = []
    headers = []
    doc_members = []
    with zipfile.ZipFile(args.archive) as zf:
        for info in zf.infolist():
            name = str(PurePosixPath(info.filename))
            manifest.append({
                "name": name,
                "size": info.file_size,
                "compressed_size": info.compress_size,
                "crc32": f"{info.CRC:08x}",
                "is_dir": info.is_dir(),
            })
            if info.is_dir():
                continue
            base = PurePosixPath(name).name.lower()
            suffix = PurePosixPath(name).suffix.lower()
            if any(term in base for term in DOC_NAMES) and suffix in {".txt", ".md", ".csv"}:
                data = zf.read(info)
                text = data.decode("utf-8-sig", errors="replace")
                target = args.output / f"doc_{len(doc_members):02d}_{PurePosixPath(name).name}"
                target.write_text(text, encoding="utf-8")
                doc_members.append(name)
            elif suffix in TEXT_EXT:
                with zf.open(info, "r") as stream:
                    bounded = read_zip_first_record(stream, max_record_bytes=16_384)
                text = bounded.data.decode("utf-8-sig", errors="replace")
                headers.append({
                    "name": name,
                    "header": text,
                    "terminator": bounded.terminator,
                    "bytes_consumed": bounded.bytes_consumed,
                })

    result = {
        "status": "gate0_inventory_complete",
        "archive": {
            "name": args.archive.name,
            "size": args.archive.stat().st_size,
            "sha256": sha256(args.archive),
            "member_count": len(manifest),
        },
        "prospective_estimability": {
            "status": est.status,
            "failing_keys": list(est.failing_keys),
            "unresolved_keys": list(est.unresolved_keys),
            "fingerprint": est.fingerprint,
        },
        "response_rows_opened": False,
        "response_values_parsed": False,
        "data_rows_after_first_physical_record_opened": False,
        "manifest": manifest,
        "headers": headers,
        "documentation_members": doc_members,
        "next": "role-adjudicate headers/documentation for a complete response-free tree geometry or distance registry",
    }
    result["fingerprint"] = canonical_sha(result)
    (args.output / "gate0_inventory_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "estimability": est.status,
        "member_count": len(manifest),
        "header_members": [row["name"] for row in headers],
        "documentation_members": doc_members,
        "response_rows_opened": False,
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
