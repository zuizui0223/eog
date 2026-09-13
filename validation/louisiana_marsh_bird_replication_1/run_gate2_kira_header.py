from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT = Path("build/louisiana_marsh_bird_replication_1/gate2_kira_header.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

AUDIT = {
    "sciencebase_metadata_requests": 0,
    "sciencebase_metadata_bytes_opened": 0,
    "selected_response_header_requests": 0,
    "selected_response_header_bytes_opened": 0,
    "selected_response_payload_requests": 0,
    "selected_response_payload_bytes_opened": 0,
    "selected_response_rows_opened": False,
    "selected_response_values_opened": False,
    "unselected_species_payload_requests": 0,
    "unselected_species_payload_bytes_opened": 0,
    "model_fits": 0,
    "heldout_scores": 0,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def emit(status: str, reason: str, **extra: object) -> dict:
    payload = {
        "schema": "eog.louisiana_marsh_bird_kira_header_gate.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": status,
        "reason": reason,
        "audit": dict(AUDIT),
        **extra,
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return payload


def get_item() -> dict:
    item_id = CONTRACT["official_source"]["sciencebase_item_id"]
    req = urllib.request.Request(
        f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json",
        headers={
            "User-Agent": "EOG-Louisiana-KIRA-Header-Gate/1.0",
            "Accept": "application/json",
        },
    )
    AUDIT["sciencebase_metadata_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(5_000_001)
        status = int(getattr(response, "status", 200))
    AUDIT["sciencebase_metadata_bytes_opened"] += len(body)
    if status != 200 or len(body) > 5_000_000:
        raise RuntimeError(f"ScienceBase metadata failure: status={status}, bytes={len(body)}")
    observed = hashlib.sha256(body).hexdigest()
    expected = CONTRACT["official_source"]["sciencebase_item_metadata_sha256"]
    if observed != expected:
        raise RuntimeError(f"ScienceBase metadata changed: {observed} != {expected}")
    return json.loads(body.decode("utf-8"))


def selected_file(item: dict) -> tuple[dict, dict]:
    selected = CONTRACT["biological_response_assets"]["selected"]["KIRA.csv"]
    rows = [row for row in (item.get("files") or []) if str(row.get("name") or "") == "KIRA.csv"]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one KIRA.csv file object, observed {len(rows)}")
    row = rows[0]
    checksum = row.get("checksum") or {}
    if isinstance(checksum, dict):
        md5 = str(checksum.get("value") or checksum.get("checksum") or "")
    else:
        md5 = str(checksum)
    size = int(row.get("size") or 0)
    if md5 != selected["md5"] or size != int(selected["bytes"]):
        raise RuntimeError(
            f"KIRA.csv metadata identity drift: md5={md5!r}, size={size}"
        )
    return row, selected


def read_bounded_header(row: dict, selected: dict) -> tuple[bytes, str, int, int | None]:
    gate = CONTRACT["selected_response_header_gate_frozen_before_header_access"]
    max_bytes = int(gate["maximum_header_bytes"])
    url = row.get("downloadUri") or row.get("url")
    if not url:
        raise RuntimeError("KIRA.csv has no download URI")
    req = urllib.request.Request(
        str(url),
        headers={
            "User-Agent": "EOG-Louisiana-KIRA-Header-Gate/1.0",
            "Accept-Encoding": "identity",
        },
    )
    AUDIT["selected_response_header_requests"] += 1
    with urllib.request.urlopen(req, timeout=60) as response:
        status = int(getattr(response, "status", 200))
        content_length_raw = response.headers.get("Content-Length")
        content_length = int(content_length_raw) if content_length_raw else None
        if status != 200:
            raise RuntimeError(f"KIRA.csv header transport failed: status={status}")
        if content_length is not None and content_length != int(selected["bytes"]):
            raise RuntimeError(
                f"KIRA.csv Content-Length drift: {content_length} != {selected['bytes']}"
            )
        opened = bytearray()
        header = bytearray()
        terminator: str | None = None
        while len(opened) < max_bytes:
            chunk = response.read(1)
            if not chunk:
                break
            opened.extend(chunk)
            if chunk == b"\r":
                terminator = "CR"
                break
            if chunk == b"\n":
                terminator = "LF"
                break
            header.extend(chunk)
    AUDIT["selected_response_header_bytes_opened"] += len(opened)
    if terminator is None:
        raise RuntimeError(
            f"KIRA.csv first record terminator not found within {max_bytes} bytes"
        )
    return bytes(header), terminator, len(opened), content_length


def parse_and_validate(header_bytes: bytes) -> tuple[list[str], dict[str, int]]:
    gate = CONTRACT["selected_response_header_gate_frozen_before_header_access"]
    try:
        header_text = header_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"KIRA.csv header is not UTF-8: {exc}") from exc
    rows = list(csv.reader(io.StringIO(header_text), strict=True))
    if len(rows) != 1:
        raise RuntimeError("KIRA.csv bounded header did not parse to exactly one CSV record")
    columns = [value.strip() for value in rows[0]]
    if len(columns) != int(gate["expected_column_count"]):
        raise RuntimeError(
            f"KIRA.csv header column count mismatch: {len(columns)} != {gate['expected_column_count']}"
        )
    if columns[0] != gate["expected_first_column_literal"]:
        raise RuntimeError(
            f"KIRA.csv first column mismatch: {columns[0]!r} != {gate['expected_first_column_literal']!r}"
        )

    patterns = [re.compile(pattern) for pattern in gate["predeclared_period_token_grammar"]]
    period_by_column: dict[str, int] = {}
    observed_periods: list[int] = []
    for column in columns[1:]:
        matches: list[int] = []
        for pattern in patterns:
            match = pattern.fullmatch(column)
            if match:
                matches.append(int(match.group(1)))
        if len(matches) != 1:
            raise RuntimeError(
                f"KIRA.csv sampling-period column violates frozen grammar: {column!r}"
            )
        period = matches[0]
        observed_periods.append(period)
        period_by_column[column] = period

    if sorted(observed_periods) != list(range(1, 21)) or len(set(observed_periods)) != 20:
        raise RuntimeError(
            f"KIRA.csv period mapping is not a bijection of 1..20: {observed_periods}"
        )
    return columns, period_by_column


def main() -> None:
    try:
        item = get_item()
        row, selected = selected_file(item)
        header_bytes, terminator, bytes_consumed, content_length = read_bounded_header(row, selected)
        columns, period_by_column = parse_and_validate(header_bytes)
        if AUDIT["selected_response_payload_requests"] != 0:
            raise RuntimeError("selected response payload request audit drift")
        if AUDIT["selected_response_payload_bytes_opened"] != 0:
            raise RuntimeError("selected response payload byte audit drift")
        if AUDIT["selected_response_rows_opened"] or AUDIT["selected_response_values_opened"]:
            raise RuntimeError("selected response row/value firewall violated")
        emit(
            "selected_response_header_schema_pass",
            "bounded KIRA.csv physical header matches the frozen Site + bijective sampling-period 1..20 grammar",
            selected_response={
                "file": "KIRA.csv",
                "metadata_md5": selected["md5"],
                "metadata_size_bytes": int(selected["bytes"]),
                "transport_content_length": content_length,
                "terminator": terminator,
                "bytes_consumed_including_terminator": bytes_consumed,
                "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
                "physical_header": columns,
                "period_by_column": period_by_column,
            },
            row_access_authorized=False,
        )
    except Exception as exc:
        emit(
            "terminal_pre_response_selected_header_failure",
            str(exc),
            row_access_authorized=False,
        )
        raise


if __name__ == "__main__":
    main()
