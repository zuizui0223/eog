#!/usr/bin/env python3
"""Attempt strictly public, read-only, checksum-gated Dryad file acquisition.

Only official Dryad-published download URLs, no credentials, no attempts to
evade HTTP 401/403 or challenge pages. No biological rows are parsed, logged,
stored or uploaded. The source-file binary is held only in memory for SHA256.
The public README is a gate: if it cannot be verified, stop immediately.
"""
from __future__ import annotations
import argparse
import hashlib
from http.client import HTTPException
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1/helgeland_saatoglu2021_provenance_preflight_v1.json"
SCHEMA = "eog.helgeland.saatoglu2021.official_dryad_public_byte_probe.v1"
EXPECTED_VERSION_ID = 130231
OFFICIAL_ROUTES = (
    "https://datadryad.org/downloads/file_stream/{id}",
    "https://datadryad.org/api/v2/files/{id}/download",
)
README = "Geneticassignment_README.txt"


def classify_bytes(raw: bytes, expected_size: int, expected_hash: str, media: str = "") -> str:
    """Never label HTML/security pages or arbitrary bytes as original science."""
    if media.split(";")[0].strip().lower() in ("text/html", "application/xhtml+xml"):
        return "CHALLENGE_OR_HTML_NOT_SOURCE"
    if len(raw) != expected_size:
        return "ORIGINAL_BYTES_SIZE_MISMATCH"
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        return "ORIGINAL_BYTES_SHA256_MISMATCH"
    return "ORIGINAL_BYTES_SHA256_VERIFIED"


def inspect_http_file(file: dict, get) -> dict:
    """Dependency-injected HTTP client; output contains no raw data or URLs with tokens."""
    fid = file["id"]
    expected_size = file["size_bytes"]
    digest = file["declared_sha256"]
    log = []
    for template in OFFICIAL_ROUTES:
        url = template.format(id=fid)
        try:
            status, mime, raw = get(url, expected_size + 1)
        except HTTPError as e:
            status, mime, raw = e.code, "", b""
        except (OSError, HTTPException, URLError) as e:
            log.append({
                "route": template.split("datadryad.org/")[1].split("{id}")[0],
                "outcome": "TRANSPORT_ERROR",
                "http_status": None,
                "exception_class": type(e).__name__,
            })
            continue
        safe_route = "file_stream" if "file_stream/" in url else "api_v2"
        if status in (401, 403):
            log.append({"route": safe_route, "http_status": status, "outcome": "ACCESS_DENIED_STOP"})
            # A denial is authoritative; do not switch route as an auth workaround.
            break
        if status != 200:
            log.append({"route": safe_route, "http_status": status, "outcome": "HTTP_NOT_200"})
            continue
        gate = classify_bytes(raw, expected_size, digest, mime)
        log.append({"route": safe_route, "http_status": 200, "outcome": gate})
        if gate == "ORIGINAL_BYTES_SHA256_VERIFIED":
            return {"name": file["name"], "file_id": fid, "byte_verified": True, "attempts": log}
        # Public HTML challenges may not be bypassed using tricks.
        if gate == "CHALLENGE_OR_HTML_NOT_SOURCE":
            break
    return {"name": file["name"], "file_id": fid, "byte_verified": False, "attempts": log}


def pure_get(url: str, max_bytes: int) -> tuple[int, str, bytes]:
    # Request no cookies, auth headers, or privileged endpoints.
    req = Request(url, headers={"User-Agent": "EOG-public-source-byte-audit/1.0"})
    with urlopen(req, timeout=22) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read(max_bytes)


def run(inventory: dict, get=pure_get) -> dict:
    dryad = inventory["official_dryad"]
    if (
        inventory.get("schema") != "eog.helgeland.saatoglu2021_genetic_cmr_provenance_preflight.v1"
        or dryad.get("doi") != "10.5061/dryad.xgxd254h1"
        or dryad.get("dataset_id") != 72603
        or dryad.get("version_id") != EXPECTED_VERSION_ID
    ):
        raise ValueError("Unexpected original Dryad scientific source contract")
    files = dryad["files"]
    if len(files) != 5 or len(set(f["id"] for f in files)) != 5:
        raise ValueError("Source file manifest must pin five unique source IDs")
    # Old source digests are now the source integrity condition, no new guesses.
    expected = {f["name"]: f for f in files}
    if set(expected) != {
        "Geneticassignment_README.txt", "Dispersaldata.txt", "Misassignments_givenaway.txt",
        "Misassignments_received.txt", "Pairwise_Fst.txt"
    }:
        raise ValueError("Source file manifest mismatch")
    readme = inspect_http_file(expected[README], get)
    result = [readme]
    if readme["byte_verified"]:
        for name in ("Dispersaldata.txt", "Misassignments_givenaway.txt",
                     "Misassignments_received.txt", "Pairwise_Fst.txt"):
            result.append(inspect_http_file(expected[name], get))
    any_verified = sum(x["byte_verified"] for x in result)
    complete = any_verified == 5
    return {
        "schema": SCHEMA,
        "status": "ALL_FIVE_ORIGINAL_BYTES_SHA256_VERIFIED__NO_DATA_ROWS_READ" if complete else
                  "PUBLIC_ACCESS_DIAGNOSTIC_ONLY__SOME_OR_ALL_ORIGINAL_BYTES_NOT_VERIFIED",
        "dryad_version_id": EXPECTED_VERSION_ID,
        "files_checked": result,
        "verified_file_count": any_verified,
        "five_files_verified": complete,
        "original_2021_record_headers_or_bird_values_read": False,
        "individual_ID_join_or_genetic_assignments_scored": False,
        "source_available_at_2014_forecast_cutoff": False,
        "new_EOG_WF_endpoint_scored": False,
        "raw_source_file_bytes_persisted_or_exported": False,
        "access_denial_bypassed": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    receipt = run(json.loads(INVENTORY.read_text(encoding="utf-8")))
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refuse to overwrite existing source-access receipt")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(receipt, out, ensure_ascii=False, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({
        "status": receipt["status"], "verified_file_count": receipt["verified_file_count"],
        "source_2021_biological_rows_read": False, "EOG_WF_modified": False,
    }))


if __name__ == "__main__":
    main()
