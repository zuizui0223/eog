#!/usr/bin/env python3
"""Metadata-only preflight of a distinct Swedish butterfly BAM candidate.

No field/response file bytes are read. One exact DOI version-list GET and
one derived version-file inventory GET are the maximum authorized requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eog.v2.dryad_metadata import (  # noqa: E402
    resolve_dryad_file_roster,
    select_latest_public_submitted_version,
)

PROTOCOL_PATH = ROOT / "validation/pyrgus_bam_metadata_gate_v1/protocol_v1.json"
PROTOCOL_COMMIT = "2d8bf050b1197b9c5e387264da2941d539a1a214"


def sha256(data: Any) -> str:
    if isinstance(data, bytes):
        raw = data
    else:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def fetch_json(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "datadryad.org":
        raise ValueError("SOURCE_STOP_UNAUTHORIZED_HOST")
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "EOG-BAM-MetadataGate/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        final_url = urllib.parse.urlsplit(response.geturl())
        if final_url.scheme != "https" or final_url.hostname != "datadryad.org":
            raise ValueError("SOURCE_STOP_REDIRECT_HOST")
        if response.status != 200:
            raise ValueError(f"SOURCE_STOP_HTTP_{response.status}")
        raw = response.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("SOURCE_STOP_METADATA_TOO_LARGE")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("SOURCE_STOP_NOT_JSON_OBJECT")
    return data


def evaluate(protocol: dict, fetch: Callable[[str], dict]) -> dict:
    source = protocol["dataset"]
    receipt = {
        "schema": "eog.pyrgus_bam_metadata_receipt.v1",
        "protocol_commit": PROTOCOL_COMMIT,
        "protocol_sha256": sha256(protocol),
        "dataset_doi": source["doi"],
        "status": "SOURCE_GATE_NOT_YET_FINISHED",
        "response_rows_opened": 0,
        "data_files_downloaded": 0,
        "scored_ecological_endpoints": 0,
        "requests_attempted": [],
        "version": None,
        "files": [],
    }
    def get(url):
        receipt["requests_attempted"].append(url)
        return fetch(url)

    try:
        versions = get(source["api_versions_url"])
        emb = versions.get("_embedded")
        if not isinstance(emb, dict):
            raise ValueError("SOURCE_STOP_VERSIONS_SCHEMA")
        array = emb.get("stash:versions")
        if not isinstance(array, list):
            raise ValueError("SOURCE_STOP_VERSIONS_SCHEMA")
        approved = [
            r for r in array
            if str(r.get("versionStatus", "")).casefold()=="submitted"
            and str(r.get("visibility", "public")).casefold() in {"public",""}
        ]
        if len(approved) != 1:
            raise ValueError("SOURCE_STOP_NOT_EXACTLY_ONE_PUBLIC_VERSION")
        v = select_latest_public_submitted_version(versions)
        file_url = "https://datadryad.org" + v.files_href
        files_doc = get(file_url)
        rows = files_doc.get("_embedded", {}).get("stash:files")
        if not isinstance(rows, list):
            raise ValueError("SOURCE_STOP_FILES_SCHEMA")
        identities = resolve_dryad_file_roster(
            rows, expected_version_id=v.version_id
        )
        expected = sorted(source["required_files"])
        if sorted(z.path for z in identities) != expected:
            raise ValueError("SOURCE_STOP_FILE_ROSTER_MISMATCH")
        if any(z.size <= 0 or z.size > source["max_file_size_bytes"] for z in identities):
            raise ValueError("SOURCE_STOP_SIZE_OUTSIDE_BOUND")
        receipt["version"] = {
            "version_id": v.version_id, "version_number": v.version_number,
            "fingerprint": v.fingerprint
        }
        receipt["files"] = [
            {"path": z.path, "file_id": z.file_id, "size": z.size,
             "digest_type": z.digest_type, "digest": z.digest,
             "identity_fingerprint": z.fingerprint}
            for z in identities
        ]
        receipt["status"] = "SOURCE_METADATA_QUALIFIED__BIOLOGICAL_ROWS_UNOPENED"
    except urllib.error.HTTPError as exc:
        receipt["status"] = f"SOURCE_STOP_HTTP_{exc.code}"
    except urllib.error.URLError:
        receipt["status"] = "SOURCE_STOP_NETWORK_TRANSPORT"
    except (ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        status = str(exc)
        receipt["status"] = (
            status if status.startswith("SOURCE_STOP_") else "SOURCE_STOP_SCHEMA"
        )
        receipt["diagnostic"] = type(exc).__name__
    receipt["fingerprint"] = sha256(receipt)
    return receipt


def run():
    raw = PROTOCOL_PATH.read_bytes()
    p = json.loads(raw)
    if p["schema"] != "eog.pyrgus_bam_metadata_gate.v1":
        raise ValueError("unrecognized frozen gate protocol")
    receipt = evaluate(p, fetch_json)
    # Bind the actual checked-in protocol bytes, not an approximately
    # reserialized JSON value, for the authoritative action receipt.
    receipt["protocol_sha256"] = sha256(raw)
    receipt["fingerprint"] = sha256({k:v for k,v in receipt.items() if k!="fingerprint"})
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    result = run()
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("PYRGUS_GATE="+json.dumps({
        "status":result["status"],
        "requests_attempted":len(result["requests_attempted"]),
        "file_metadata_verified":len(result["files"]),
        "response_rows_opened":result["response_rows_opened"],
        "fingerprint":result["fingerprint"],
    },sort_keys=True))


if __name__=="__main__":
    main()
