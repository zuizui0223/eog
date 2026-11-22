#!/usr/bin/env python3
"""McKee 2024 Dryad SOURCE METADATA ONLY gate.

Only fetches the official dataset JSON and its canonical version-specific
file-inventory JSON. No GPS shapefile, README payload, ZIP archive, fix row,
animal ID or ecological response is requested, read, parsed or scored.

Frozen source contract: source_gate0_protocol_v1.json (committed before access).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

from eog.v2.dryad_metadata import resolve_dryad_file_roster


PROTOCOL_PATH = Path(__file__).with_name("source_gate0_protocol_v1.json")
SCHEMA = "eog.temporal_corridor_mckee2024.gate0_metadata_receipt.v1"
VERSION_RE = re.compile(r"^/api/v2/versions/([1-9][0-9]*)$")
FILES_RE = re.compile(r"^https://datadryad\.org/api/v2/versions/[1-9][0-9]*/files$")


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("Refusing unexpected Dryad API redirect")


def _fetch_official_json(url: str, *, pinned_dataset_url: str) -> dict:
    if url != pinned_dataset_url and FILES_RE.fullmatch(url) is None:
        raise ValueError("Refusing non-metadata endpoint")
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "EOG-McKee-2024-GATE0-METADATA-ONLY/1.0",
        },
    )
    with opener.open(request, timeout=25) as stream:
        if "json" not in stream.headers.get("Content-Type", "").lower():
            raise ValueError("Dryad returned a non-JSON content type")
        raw = stream.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Dryad metadata response exceeded 2 MB")
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise TypeError("Dryad public API response must be an object")
    return obj


def qualify_documents(protocol: dict, dataset: dict, files: dict) -> dict:
    """Resolve only the official metadata identity, never source bytes."""
    if protocol.get("schema") != "eog.temporal_corridor_mckee2024.source_gate.v1":
        raise ValueError("Source gate protocol schema was altered")
    if protocol.get("status") != "FROZEN_PRE_PUBLIC_API_METADATA_ACCESS__NO_TRACK_ROWS":
        raise ValueError("Source gate must have frozen-before-access status")
    fixed = protocol["fixed_source"]
    if fixed.get("doi") != "10.5061/dryad.15dv41p51":
        raise ValueError("Unexpected Dryad DOI in frozen protocol")
    if dataset.get("identifier", "").casefold() != "doi:10.5061/dryad.15dv41p51":
        raise ValueError("Publisher DOI does not match frozen source")
    link = (dataset.get("_links") or {}).get("stash:version")
    if not isinstance(link, dict):
        raise ValueError("Publisher does not declare a canonical version")
    match = VERSION_RE.fullmatch(str(link.get("href") or ""))
    if match is None:
        raise ValueError("Publisher version href is not canonical")
    version_id = int(match.group(1))
    expected_self = f"/api/v2/versions/{version_id}/files"
    if (files.get("_links") or {}).get("self", {}).get("href") != expected_self:
        raise ValueError("File inventory points at a different publisher version")

    rows = (files.get("_embedded") or {}).get("stash:files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("No complete public file metadata")
    if files.get("count") != len(rows) or files.get("total") != len(rows):
        raise ValueError("Dryad metadata inventory incomplete or paginated")
    if len(rows) != len(fixed["expected_files"]):
        raise ValueError("Dryad file roster size has changed")

    identities = resolve_dryad_file_roster(rows, expected_version_id=version_id)
    expected_ids = {
        row["name"]: row["source_landing_file_id"]
        for row in fixed["expected_files"]
    }
    observed_ids = {row.path: row.file_id for row in identities}
    if observed_ids != expected_ids:
        raise ValueError("Dryad file paths or IDs differ from frozen landing identity")
    if any(row.size <= 0 for row in identities):
        raise ValueError("Dryad file has empty declared byte size")
    if any("/" in row.path or "\\" in row.path or row.path.startswith(".") for row in identities):
        raise ValueError("Unexpected unsafe Dryad file path")

    output_files = [
        {
            "name": row.path,
            "file_id": row.file_id,
            "version_id": row.version_id,
            "size_bytes": row.size,
            "source_declared_digest_type": row.digest_type,
            "source_declared_digest": row.digest,
            "metadata_fingerprint": row.fingerprint,
            "source_file_bytes_opened": False,
            "source_declared_hash_verified_against_bytes": False,
        }
        for row in identities
    ]
    result = {
        "schema": SCHEMA,
        "status": "SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS",
        "doi": fixed["doi"],
        "publisher_dataset_id": dataset.get("id"),
        "version_id": version_id,
        "publisher_version_number": dataset.get("versionNumber"),
        "files": output_files,
        "dataset_json_fingerprint": _canonical_hash(dataset),
        "file_roster_json_fingerprint": _canonical_hash(files),
        "protocol_fingerprint": _canonical_hash(protocol),
        "source_metadata_only": True,
        "file_payloads_downloaded": False,
        "README_payload_opened": False,
        "sparse_12h_tracks_opened": False,
        "dense_2h_holdout_opened": False,
        "GPS_records_read": False,
        "ecological_score_computed": False,
        "followup_payload_access_authorized": False,
        "EOG_WF_frozen_three_endpoint_denominator_unchanged": True,
    }
    return result


def verify_frozen_metadata(observed: dict, frozen: dict) -> dict:
    """Require publisher's metadata to match the post-Gate0 source receipt.

    This is *not* independently verifying source file bytes; it only rejects
    metadata drift from the first successful authorized publisher API audit.
    """
    if observed.get("schema") != SCHEMA or observed.get("status") != "SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS":
        raise ValueError("Cannot verify frozen source without successful public metadata audit")
    if frozen.get("schema") != "eog.temporal_corridor_mckee2024.gate0_publisher_metadata_frozen.v1":
        raise ValueError("Unexpected frozen publisher metadata schema")
    if frozen.get("status") != "SOURCE_DECLARED_METADATA_FROZEN__NO_GPS_FILE_BYTES":
        raise ValueError("Frozen source receipt has wrong evidence level")
    pinned = {
        "doi": frozen["source_doi"],
        "publisher_dataset_id": frozen["publisher_dataset_id"],
        "version_id": frozen["publisher_version_id"],
        "publisher_version_number": frozen["publisher_version_number"],
        "dataset_json_fingerprint": frozen["publisher_dataset_json_fingerprint"],
        "file_roster_json_fingerprint": frozen["publisher_file_roster_json_fingerprint"],
        "protocol_fingerprint": frozen["protocol_fingerprint"],
    }
    for key, expected in pinned.items():
        if observed.get(key) != expected:
            raise ValueError(f"Frozen publisher metadata identity drift: {key}")
    expected_files = sorted(
        (
            item["name"], item["file_id"], item["version_id"],
            item["size_bytes"], item["digest_type"],
            item["publisher_declared_sha256"],
            item["metadata_fingerprint"],
        )
        for item in frozen["files"]
    )
    incoming_files = sorted(
        (
            item["name"], item["file_id"], item["version_id"],
            item["size_bytes"], item["source_declared_digest_type"],
            item["source_declared_digest"],
            item["metadata_fingerprint"],
        )
        for item in observed["files"]
    )
    if expected_files != incoming_files:
        raise ValueError("Frozen publisher file roster size/hash/identity drift")
    if (
        frozen.get("all_binary_payloads_downloaded") is not False
        or frozen.get("dense_2h_tracks_read") is not False
        or frozen.get("GPS_rows_read") is not False
        or observed.get("file_payloads_downloaded") is not False
        or observed.get("dense_2h_holdout_opened") is not False
        or observed.get("GPS_records_read") is not False
    ):
        raise ValueError("Frozen gate cannot certify any raw GPS file access")
    return {"status": "MATCHES_FROZEN_GATE0_PUBLISHER_METADATA", "source_file_bytes_verified": False}


def audit(*, fetch=None, protocol_path: Path = PROTOCOL_PATH, frozen_path: Path | None = None) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    pinned_url = protocol["fixed_source"]["api_dataset_url"]
    def api(url):
        if url != pinned_url and FILES_RE.fullmatch(url) is None:
            raise ValueError("Refusing non-metadata endpoint")
        return (
            _fetch_official_json(url, pinned_dataset_url=pinned_url)
            if fetch is None else fetch(url)
        )
    try:
        dataset = api(pinned_url)
        if not isinstance(dataset, dict):
            raise TypeError("Dryad dataset metadata must be an object")
        link = (dataset.get("_links") or {}).get("stash:version") or {}
        match = VERSION_RE.fullmatch(str(link.get("href") or ""))
        if match is None:
            raise ValueError("Dryad canonical version metadata unavailable")
        files_url = f"https://datadryad.org/api/v2/versions/{int(match.group(1))}/files"
        files = api(files_url)
        if not isinstance(files, dict):
            raise TypeError("Dryad file metadata must be an object")
        result = qualify_documents(protocol, dataset, files)
        if frozen_path is not None:
            frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
            result["frozen_identity_check"] = verify_frozen_metadata(result, frozen)
        return result
    except (OSError, urllib.error.URLError, TimeoutError, TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return {
            "schema": SCHEMA,
            "status": "HOLD_SOURCE_METADATA_UNVERIFIED",
            "doi": protocol["fixed_source"]["doi"],
            "protocol_fingerprint": _canonical_hash(protocol),
            "error_type": type(exc).__name__,
            "error_summary": str(exc)[:180],
            "source_metadata_only": True,
            "file_payloads_downloaded": False,
            "sparse_12h_tracks_opened": False,
            "dense_2h_holdout_opened": False,
            "GPS_records_read": False,
            "ecological_score_computed": False,
            "followup_payload_access_authorized": False,
            "EOG_WF_frozen_three_endpoint_denominator_unchanged": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-frozen", type=Path, default=None)
    args = parser.parse_args()
    result = audit(frozen_path=args.verify_frozen)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_gate_status": result["status"],
        "doi": result["doi"],
        "file_count": len(result.get("files", [])),
        "file_payloads_downloaded": result["file_payloads_downloaded"],
        "GPS_records_read": result["GPS_records_read"],
        "ecological_score_computed": result["ecological_score_computed"],
        "error_type": result.get("error_type"),
        "error_summary": result.get("error_summary"),
    }, sort_keys=True))
    if result["status"] != "SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
