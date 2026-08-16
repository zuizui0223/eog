#!/usr/bin/env python3
"""Freeze the exact SIVFLORA source file without parsing incidence content.

This script is intentionally response-blind. It reads only the pre-outcome contract and
Zenodo record metadata, downloads the declared XLSX as opaque bytes, verifies its
published MD5, computes SHA-256, and writes a provenance manifest. It never opens the
spreadsheet workbook or inspects taxon/island incidence values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _digest(path: Path, algorithm: str) -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _json_sha256(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_url(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "EOG-SIVFLORA-source-freeze/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def _file_name(entry: dict[str, Any]) -> str:
    return str(entry.get("key") or entry.get("name") or entry.get("filename") or "")


def _metadata_md5(entry: dict[str, Any]) -> str | None:
    checksum = entry.get("checksum")
    if isinstance(checksum, str):
        value = checksum.strip()
        if value.lower().startswith("md5:"):
            return value.split(":", 1)[1].lower()
        if len(value) == 32:
            return value.lower()
    return None


def _download_url(entry: dict[str, Any]) -> str:
    links = entry.get("links") if isinstance(entry.get("links"), dict) else {}
    for key in ("content", "download", "self"):
        value = links.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    raise ValueError("Zenodo file metadata does not expose a downloadable content URL")


def freeze_source(contract_path: Path, output_dir: Path) -> dict[str, Any]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = contract["source"]
    if contract.get("status") != "pre_outcome":
        raise ValueError("source freeze requires a pre_outcome contract")

    record_id = int(source["zenodo_record_id"])
    expected_name = str(source["file_name"])
    expected_md5 = str(source["published_md5"]).lower()
    if len(expected_md5) != 32:
        raise ValueError("published_md5 must be a 32-character MD5 digest")

    metadata_url = f"https://zenodo.org/api/records/{record_id}"
    metadata = _load_json_url(metadata_url)
    files = metadata.get("files")
    if not isinstance(files, list):
        raise ValueError("Zenodo record metadata contains no file list")
    matches = [entry for entry in files if isinstance(entry, dict) and _file_name(entry) == expected_name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one Zenodo file named {expected_name!r}, found {len(matches)}")
    file_meta = matches[0]

    metadata_md5 = _metadata_md5(file_meta)
    if metadata_md5 is not None and metadata_md5 != expected_md5:
        raise ValueError(
            f"Zenodo metadata MD5 changed: expected {expected_md5}, metadata reports {metadata_md5}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / expected_name
    download_url = _download_url(file_meta)
    request = urllib.request.Request(download_url, headers={"User-Agent": "EOG-SIVFLORA-source-freeze/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response, raw_path.open("wb") as handle:
        shutil.copyfileobj(response, handle)

    actual_md5 = _digest(raw_path, "md5")
    if actual_md5 != expected_md5:
        raw_path.unlink(missing_ok=True)
        raise ValueError(f"downloaded MD5 mismatch: expected {expected_md5}, got {actual_md5}")

    actual_sha256 = _digest(raw_path, "sha256")
    metadata_block = metadata.get("metadata") if isinstance(metadata.get("metadata"), dict) else {}
    manifest = {
        "contract_version": contract["contract_version"],
        "contract_status_at_freeze": contract["status"],
        "contract_json_sha256": _json_sha256(contract),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "zenodo_record_id": record_id,
        "metadata_url": metadata_url,
        "zenodo_record_doi_declared": source["zenodo_record_doi"],
        "paper_cited_zenodo_doi": source["paper_cited_zenodo_doi"],
        "data_descriptor_doi": source["data_descriptor_doi"],
        "record_title": metadata_block.get("title") or metadata.get("title"),
        "record_version": metadata_block.get("version"),
        "record_created": metadata.get("created"),
        "record_updated": metadata.get("updated"),
        "file_name": expected_name,
        "published_md5": expected_md5,
        "metadata_md5": metadata_md5,
        "downloaded_md5": actual_md5,
        "downloaded_sha256": actual_sha256,
        "downloaded_bytes": raw_path.stat().st_size,
        "incidence_content_parsed": False,
        "spreadsheet_opened": False,
        "outcome_statistics_computed": False,
    }
    manifest_path = output_dir / "source_freeze_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze_source(args.contract, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
