from __future__ import annotations

import csv
import hashlib
import io
import json
import urllib.request
from pathlib import Path

CONTRACT_PATH = Path(__file__).with_name("source_contract.json")
RESULT_PATH = Path(__file__).with_name("header_preflight_result.json")


def write_result(payload: dict[str, object], *, exit_code: int = 0) -> None:
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if exit_code:
        raise SystemExit(exit_code)


def fail(status: str, reason: str, **extra: object) -> None:
    write_result(
        {
            "schema": "eog.peneda_roedeer_response_header_preflight.v1",
            "status": status,
            "reason": reason,
            "response_header_requests": 1,
            "response_payload_bytes_opened": 0,
            "response_rows_opened": False,
            "response_values_opened": False,
            "model_fits": 0,
            "heldout_scores": 0,
            **extra,
        },
        exit_code=1,
    )


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    firewall = contract["response_firewall"]
    maximum = int(firewall["bounded_header_maximum_bytes"])
    range_value = str(firewall["bounded_header_range"])

    request = urllib.request.Request(
        firewall["response_url"],
        headers={
            "User-Agent": "EOG-prospective-validation/1.0 (physical-header-only preflight)",
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
            "Range": range_value,
        },
    )
    opened = bytearray()
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            http_status = int(getattr(response, "status", 200))
            content_type = response.headers.get("Content-Type", "")
            content_range = response.headers.get("Content-Range", "")
            while len(opened) < maximum:
                value = response.read(1)
                if not value:
                    break
                if value in {b"\r", b"\n"}:
                    terminator = "CR" if value == b"\r" else "LF"
                    break
                opened.extend(value)
            else:
                fail(
                    "stop_response_header_too_long",
                    f"no physical record terminator within frozen {maximum}-byte header budget",
                    response_header_bytes_opened=len(opened),
                    response_header_sha256=hashlib.sha256(opened).hexdigest(),
                    http_status=http_status,
                    content_type=content_type,
                    content_range=content_range,
                )
    except SystemExit:
        raise
    except Exception as exc:
        fail(
            "stop_response_header_transport_unavailable",
            repr(exc),
            response_header_bytes_opened=len(opened),
        )

    if not opened:
        fail("stop_response_header_empty", "physical response header is empty")
    if "terminator" not in locals():
        fail(
            "stop_response_header_no_terminator",
            "response stream ended before a physical CSV record terminator",
            response_header_bytes_opened=len(opened),
        )

    try:
        header_text = bytes(opened).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        fail(
            "stop_response_header_encoding",
            f"physical header is not UTF-8/UTF-8-SIG: {exc}",
            response_header_bytes_opened=len(opened),
            response_header_sha256=hashlib.sha256(opened).hexdigest(),
        )

    try:
        rows = list(csv.reader(io.StringIO(header_text)))
    except csv.Error as exc:
        fail(
            "stop_response_header_csv_schema",
            f"CSV header parse failed: {exc}",
            response_header_bytes_opened=len(opened),
            response_header_sha256=hashlib.sha256(opened).hexdigest(),
        )
    if len(rows) != 1:
        fail("stop_response_header_csv_schema", "header-only parser did not produce exactly one record")
    fields = tuple(value.strip() for value in rows[0])
    if not fields or any(not value for value in fields) or len(set(fields)) != len(fields):
        fail(
            "stop_response_header_csv_schema",
            "physical header contains blank or duplicate field names",
            response_header_bytes_opened=len(opened),
            observed_fields=list(fields),
        )

    required = {
        "observationID",
        "deploymentID",
        "timestamp",
        "observationType",
        "scientificName",
    }
    missing = sorted(required.difference(fields))
    if missing:
        fail(
            "stop_response_header_required_fields_missing",
            f"missing prospectively required Camtrap DP observation fields: {missing}",
            response_header_bytes_opened=len(opened),
            response_header_sha256=hashlib.sha256(opened).hexdigest(),
            observed_fields=list(fields),
        )

    result = {
        "schema": "eog.peneda_roedeer_response_header_preflight.v1",
        "status": "response_header_schema_ready_for_final_freeze",
        "response_header_requests": 1,
        "response_header_bytes_opened": len(opened),
        "response_header_sha256": hashlib.sha256(opened).hexdigest(),
        "physical_header_text": header_text,
        "physical_header_fields": list(fields),
        "physical_terminator_prefix": terminator,
        "http_status": http_status,
        "content_type": content_type,
        "content_range": content_range,
        "response_payload_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    write_result(result)


if __name__ == "__main__":
    main()
