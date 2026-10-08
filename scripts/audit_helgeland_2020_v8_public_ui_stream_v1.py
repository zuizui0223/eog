#!/usr/bin/env python3
"""Public dataset *web UI* file-stream route; exact Dryad 2020 v8 IDs only.

This route is distinct from the REST API /api/v2/files/:id/download, whose
anonymous invocation returned 401. No credentials are used. Only public v8
file IDs are requested; the complete bytes are checked against frozen SHA256,
kept in an ephemeral private directory and never emitted as an artifact.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from audit_helgeland_2020_v8_local_bytes_v1 import (
    FROZEN, PINS, audit as offline_audit,
)

WEB_UI_BASE = "https://datadryad.org/downloads/file_stream/"
MAX_SINGLE_FILE_SIZE = 100_000


def public_stream(file_id: int, expected_size: int, destination: Path) -> None:
    if (file_id not in {v[0] for v in PINS.values()} or
        expected_size != next((v[1] for v in PINS.values() if v[0] == file_id), None)):
        raise ValueError("Not one of the precisely pinned 2020 v8 public files")
    if expected_size <= 0 or expected_size > MAX_SINGLE_FILE_SIZE:
        raise ValueError("Unexpected download byte boundary")
    if destination.exists() or destination.is_symlink():
        raise ValueError("Refusing existing source-file target")
    request = urllib.request.Request(
        WEB_UI_BASE + str(file_id),
        headers={"User-Agent": "EOG-source-vintage-public-UI/1.0",
                 "Accept": "application/octet-stream,*/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as stream:
            resolved = urllib.parse.urlparse(stream.geturl())
            if resolved.scheme != "https" or not resolved.hostname or resolved.port not in (None,443):
                raise ValueError("Refusing non-HTTPS or nonstandard-port redirect")
            # Do not log redirected signed object-storage URLs or downloaded values.
            count = 0
            with destination.open("xb") as output:
                for chunk in iter(lambda: stream.read(65536), b""):
                    count += len(chunk)
                    if count > expected_size:
                        raise ValueError("Downloaded bytes exceed original Dryad v8 pin")
                    output.write(chunk)
            if count != expected_size:
                raise ValueError("Downloaded bytes differ from registered v8 size")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        # Preserve only response status/class, no URL or credentials in evidence.
        status = exc.code if isinstance(exc, urllib.error.HTTPError) else None
        raise RuntimeError(f"PUBLIC_WEB_UI_SOURCE_UNAVAILABLE_HTTP_{status or 'NETWORK'}") from None


def check(registered: dict, fetch=public_stream) -> tuple[dict, dict]:
    # The offline attestation verifies DOI, v8 version, all three source hashes
    # and bounded first-line shape AFTER web retrieval, before any PASS.
    with tempfile.TemporaryDirectory(prefix="eog-helgeland-2020-v8-") as folder:
        root = Path(folder)
        for name, (file_id, size, _source_sha) in PINS.items():
            fetch(file_id, size, root / name)
        attestation, receipt = offline_audit(root, registered)
    attestation["acquisition"] = {
        "route": "PUBLIC_DATASET_WEB_UI_FILE_STREAM__NOT_REST_API",
        "original_published_version_id": 78498,
        "number_of_original_files_verified": 3,
        "source_bytes_retained_after_job": False,
        "authentication_token_used": False,
        "date_cutoff_and_site_codes_scored": False,
        "ecological_forecast_authorized": False,
    }
    receipt["actual_public_web_ui_source_bytes_independently_verified"] = True
    receipt["ecological_forecast_authorized"] = False
    return attestation, receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("Refusing to overwrite existing output")
    registered = json.loads(FROZEN.read_text(encoding="utf-8"))
    attestation, receipt = check(registered)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"schema": "eog.helgeland.2020_v8.public_web_ui.attestation.v1",
                   "status": receipt["status"], "source": attestation,
                   "receipt": receipt}, stream,
                  indent=2, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"status": receipt["status"], "files": 3,
                      "ecological_forecast_authorized": False}))


if __name__ == "__main__":
    main()
