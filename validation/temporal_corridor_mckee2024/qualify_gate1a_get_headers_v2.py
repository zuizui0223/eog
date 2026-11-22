#!/usr/bin/env python3
"""One official GET first-response check, no redirects or body consumption.

This is a separately frozen v2 transport check after the v1 HEAD 403 STOP.
Only sparse 12-hour GPS and README file URLs are permitted, never dense 2h.
Even a direct 200 stops without reading a response body.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "gate1a_get_headers_v2_protocol.json"
GATE0 = HERE / "gate0_publisher_metadata_frozen_v1.json"
SCHEMA = "eog.temporal_corridor_mckee2024.get_no_body_preflight.v2"
REDIRECTS = {301, 302, 303, 307, 308}
SINGLE_SOURCE_URLS = {
    "https://datadryad.org/downloads/file_stream/3334125",
    "https://datadryad.org/downloads/file_stream/3334129",
}


def _hash(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def validate_protocol(protocol: dict, gate0: dict) -> tuple[dict, ...]:
    if protocol.get("schema") != "eog.temporal_corridor_mckee2024.gate1a_get_header_protocol.v2":
        raise ValueError("Not the declared GET-no-body source protocol")
    if protocol.get("status") != "FROZEN_BEFORE_FIRST_GET__NO_RESPONSE_BODY_ACCESS":
        raise ValueError("GET-no-body protocol must have pre-access frozen status")
    if protocol.get("doi") != gate0.get("source_doi"):
        raise ValueError("DOI differs from frozen Gate0 source")
    if protocol.get("version_id") != gate0.get("publisher_version_id"):
        raise ValueError("Version differs from frozen Gate0 source")
    if protocol.get("forbidden_file_id") != 3334126:
        raise ValueError("2h holdout ID prohibition was changed")
    nc = protocol["network_contract"]
    if (
        nc.get("method") != "GET"
        or nc.get("no_redirect_following") is not True
        or nc.get("no_response_body_read") is not True
        or nc.get("no_retry") is not True
        or nc.get("no_raw_GPS_data_access") is not True
    ):
        raise ValueError("GET-no-body transport restrictions were changed")
    rows = protocol["requests"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("Exactly two pinned source URLs are required")
    if {x.get("url") for x in rows} != SINGLE_SOURCE_URLS:
        raise ValueError("Pinned publisher source URLs were changed")
    frozen_files = {x["file_id"]: x for x in gate0["files"]}
    for row in rows:
        known = frozen_files.get(row["file_id"])
        if known is None or (
            row["name"], row["size_bytes"], row["publisher_sha256"]
        ) != (
            known["name"], known["size_bytes"], known["publisher_declared_sha256"]
        ):
            raise ValueError("Publisher file ID/size/hash does not match frozen Gate0")
    return tuple(rows)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_only_first_response(url: str) -> dict:
    if url not in SINGLE_SOURCE_URLS:
        raise ValueError("Refusing unpinned source file URL")
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"User-Agent": "EOG-McKee-2024-GET-headers-only/2.0"},
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=25) as stream:
            status = int(stream.status)
            headers = stream.headers
            # DO NOT call stream.read(); close the direct response immediately.
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = exc.headers
        # DO NOT call exc.read().
    if status not in REDIRECTS:
        raise ValueError(
            f"Publisher first-response status {status}; no bytes consumed or redirect followed"
        )
    location = headers.get("Location")
    if not location:
        raise ValueError("Publisher redirect lacks Location header")
    parsed = urllib.parse.urlsplit(location)
    if (
        parsed.scheme != "https" or not parsed.hostname
        or parsed.username or parsed.password or parsed.fragment
    ):
        raise ValueError("Invalid first redirect target; no follow-up request allowed")
    host = parsed.hostname.lower()
    if len(host) > 255:
        raise ValueError("First redirect hostname too long")
    # Deliberately do not log path, query, signature or complete location.
    return {
        "http_status": status,
        "first_redirect_host": host,
        "redirect_followed": False,
        "response_body_consumed": False,
        "signed_url_logged": False,
    }


def audit(*, probe=None, protocol_path: Path = PROTOCOL, gate0_path: Path = GATE0) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    frozen = json.loads(gate0_path.read_text(encoding="utf-8"))
    receipt = {
        "schema": SCHEMA,
        "status": "HOLD_TRANSPORT_UNVERIFIED",
        "protocol_sha256": _hash(protocol),
        "gate0_sha256": _hash(frozen),
        "DOI": frozen.get("source_doi"),
        "source_version_id": frozen.get("publisher_version_id"),
        "no_follow_up_redirect_request": True,
        "no_response_body_intentionally_consumed": True,
        "sparse_12h_GPS_records_opened": False,
        "dense_2h_holdout_opened": False,
        "source_file_sha256_verified_from_bytes": False,
        "no_ecological_score": True,
        "gate1b_download_authorized": False,
        "new_EOG_WF_endpoint": False,
    }
    try:
        rows = validate_protocol(protocol, frozen)
        request_fn = get_only_first_response if probe is None else probe
        result_rows = []
        for row in rows:
            reply = request_fn(row["url"])
            if (
                not isinstance(reply, dict)
                or reply.get("http_status") not in REDIRECTS
                or not isinstance(reply.get("first_redirect_host"), str)
                or reply.get("redirect_followed") is not False
                or reply.get("response_body_consumed") is not False
                or reply.get("signed_url_logged") is not False
            ):
                raise ValueError("First response violated no-body / no-redirect contract")
            # Avoid echoing untrusted extra fields from a caller.
            result_rows.append({
                "source_file_id": row["file_id"],
                "name": row["name"],
                "http_status": reply["http_status"],
                "first_redirect_host": reply["first_redirect_host"],
                "redirect_followed": False,
                "response_body_consumed": False,
                "signed_url_logged": False,
            })
        receipt["results"] = result_rows
        receipt["status"] = "FIRST_GET_REDIRECT_METADATA_OBSERVED__NO_SOURCE_ROWS"
    except (OSError, urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        receipt["status"] = "HOLD_TRANSPORT_UNVERIFIED"
        receipt["error_type"] = type(exc).__name__
        receipt["error_summary"] = str(exc)[:160]
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "results": result.get("results", []),
        "error_type": result.get("error_type"),
        "error_summary": result.get("error_summary"),
        "dense_2h_holdout_opened": result["dense_2h_holdout_opened"],
        "no_response_body_intentionally_consumed": result["no_response_body_intentionally_consumed"],
    }, sort_keys=True))
    if result["status"] != "FIRST_GET_REDIRECT_METADATA_OBSERVED__NO_SOURCE_ROWS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
