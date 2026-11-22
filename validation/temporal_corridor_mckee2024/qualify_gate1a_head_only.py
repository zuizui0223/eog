#!/usr/bin/env python3
"""HEAD-only official Dryad first-hop transport audit for McKee 2024.

Never GETs, downloads, reads response bodies, follows redirects, or logs
publisher-issued signed URLs/query strings. No GPS or README source bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "gate1a_redirect_head_protocol_v1.json"
FROZEN = ROOT / "gate0_publisher_metadata_frozen_v1.json"
SCHEMA = "eog.temporal_corridor_mckee2024.gate1a_first_redirect_receipt.v1"
REDIRECTS = frozenset((301, 302, 303, 307, 308))


def _digest(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _validate_protocol(contract: dict, frozen: dict) -> tuple[dict, ...]:
    if contract.get("schema") != "eog.temporal_corridor_mckee2024.gate1_redirect_head_protocol.v1":
        raise ValueError("Unknown frozen head-only source contract")
    if contract.get("status") != "FROZEN_BEFORE_HEAD_REQUEST__NO_FILE_PAYLOAD":
        raise ValueError("Head-only protocol is not frozen before transport")
    if contract.get("parent_gate0_version_id") != frozen.get("publisher_version_id"):
        raise ValueError("Gate0 publisher version identity mismatch")
    if frozen.get("status") != "SOURCE_DECLARED_METADATA_FROZEN__NO_GPS_FILE_BYTES":
        raise ValueError("Gate0 publisher identity was not safely frozen")
    files = contract["fixed_eligible_files"]
    if not isinstance(files, list) or len(files) != 2:
        raise ValueError("Exactly two allowed HEAD targets required")
    names = {row["name"] for row in files}
    if names != {"GPS12hrs_Locs.zip", "README.md"}:
        raise ValueError("Unexpected source file authorization")
    allowed_urls = {
        "https://datadryad.org/downloads/file_stream/3334125",
        "https://datadryad.org/downloads/file_stream/3334129",
    }
    if {row.get("url") for row in files} != allowed_urls:
        raise ValueError("Approved Dryad HEAD-only URLs changed")
    if set(contract["network_contract"]["allowed_request_urls"]) != allowed_urls:
        raise ValueError("Allowed request URL list changed")
    if contract["network_contract"]["method"] != "HEAD":
        raise ValueError("Only HEAD method is allowed")
    if contract["network_contract"]["follow_any_redirect"] is not False:
        raise ValueError("Redirect following is forbidden")
    if contract["network_contract"]["do_not_open_response_body"] is not True:
        raise ValueError("Body access is forbidden")
    frozen_by_id = {row["file_id"]: row for row in frozen["files"]}
    for row in files:
        ref = frozen_by_id.get(row["file_id"])
        if (
            ref is None
            or (row["name"], row["size_bytes"], row["sha256"]) != (
                ref["name"], ref["size_bytes"], ref["publisher_declared_sha256"]
            )
        ):
            raise ValueError("Gate1A pinned file ID/size/hash changed from frozen Gate0")
    if 3334126 not in {item["file_id"] for item in contract["explicitly_forbidden_files"]}:
        raise ValueError("The 2h GPS holdout file must remain explicitly forbidden")
    return tuple(files)


class _NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _head_once(url: str) -> dict:
    allowlist = {
        "https://datadryad.org/downloads/file_stream/3334125",
        "https://datadryad.org/downloads/file_stream/3334129",
    }
    if url not in allowlist:
        raise ValueError("Refusing an unpinned HEAD source URL")
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "EOG-McKee-2024-HEAD-only-source-preflight/1.0"},
    )
    opener = urllib.request.build_opener(_NoFollow)
    try:
        with opener.open(request, timeout=25) as stream:
            status = int(stream.status)
            headers = stream.headers
            # Deliberately do not call stream.read() even for status 200.
    except urllib.error.HTTPError as exc:
        # Redirects are expected to raise without following through _NoFollow.
        status = int(exc.code)
        headers = exc.headers
        # Deliberately do NOT call exc.read().
    if status not in (*REDIRECTS, 200):
        raise ValueError(f"Unexpected publisher HTTP HEAD status: {status}")
    redirect = headers.get("Location")
    host = None
    if status in REDIRECTS:
        if not redirect:
            raise ValueError("Redirect lacks Location header")
        parsed = urllib.parse.urlsplit(redirect)
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.fragment
        ):
            raise ValueError("Unexpected first publisher redirect form")
        host = parsed.hostname.lower()
        if len(host) > 255:
            raise ValueError("First redirect host name unreasonably long")
    elif redirect:
        raise ValueError("Unexpected Location header with direct HEAD 200")

    length = headers.get("Content-Length")
    if length is not None:
        if not str(length).isdigit():
            raise ValueError("Unparseable response header Content-Length")
        length = int(length)
    return {
        "http_status": status,
        "redirect_present": status in REDIRECTS,
        "first_redirect_host": host,
        "publisher_header_content_type": headers.get("Content-Type"),
        "publisher_header_content_length": length,
        "source_body_read": False,
        "redirect_followed": False,
        "signed_redirect_url_logged": False,
    }


def audit(*, head=None, protocol_path: Path = PROTOCOL, frozen_path: Path = FROZEN) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    result = {
        "schema": SCHEMA,
        "status": "HOLD_SOURCE_TRANSPORT_UNVERIFIED",
        "protocol_fingerprint": _digest(protocol),
        "frozen_gate0_fingerprint": _digest(frozen),
        "source_version_id": frozen.get("publisher_version_id"),
        "source_byte_downloads_performed": False,
        "GPS_rows_or_headers_read": False,
        "dense_2h_holdout_opened": False,
        "source_redirect_followed": False,
        "signed_redirect_url_logged": False,
        "next_stage_download_authorized": False,
        "EOG_WF_denominator_unchanged": True,
    }
    try:
        targets = _validate_protocol(protocol, frozen)
        probe = _head_once if head is None else head
        rows = []
        for item in targets:
            response = probe(item["url"])
            if (
                not isinstance(response, dict)
                or response.get("http_status") not in (*REDIRECTS, 200)
                or response.get("source_body_read") is not False
                or response.get("redirect_followed") is not False
                or response.get("signed_redirect_url_logged") is not False
            ):
                raise ValueError("Publisher probe violated the HEAD-only contract")
            rows.append({
                "file_id": item["file_id"],
                "name": item["name"],
                "pinned_size_bytes": item["size_bytes"],
                "pinned_publisher_sha256": item["sha256"],
                **response,
            })
        result["records"] = rows
        result["status"] = "HEAD_FIRST_HOP_METADATA_RETRIEVED__NO_FILE_BYTES"
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        result["status"] = "HOLD_SOURCE_TRANSPORT_UNVERIFIED"
        result["error_type"] = type(exc).__name__
        result["error_summary"] = str(exc)[:160]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "probed_files": [
            {
                "file_id": row["file_id"],
                "http_status": row["http_status"],
                "first_redirect_host": row["first_redirect_host"],
            }
            for row in result.get("records", [])
        ],
        "source_byte_downloads_performed": result["source_byte_downloads_performed"],
        "dense_2h_holdout_opened": result["dense_2h_holdout_opened"],
        "error_type": result.get("error_type"),
        "error_summary": result.get("error_summary"),
    }, sort_keys=True))
    if result["status"] != "HEAD_FIRST_HOP_METADATA_RETRIEVED__NO_FILE_BYTES":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
