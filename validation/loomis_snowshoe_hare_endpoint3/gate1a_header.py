from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from typing import Callable


class HeaderGateStop(RuntimeError):
    pass


ByteReader = Callable[[int, str], bytes]


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


@dataclass(frozen=True)
class HeaderEvidence:
    key: str
    raw_header_text: str
    terminator: str
    bytes_consumed: int
    columns: tuple[str, ...]
    fingerprint: str


def read_first_physical_record(
    key: str,
    read_byte: ByteReader,
    *,
    maximum_header_bytes: int = 4096,
    encoding: str = "utf-8-sig",
) -> HeaderEvidence:
    if not isinstance(key, str) or not key.strip():
        raise ValueError("key must be a non-empty string")
    if isinstance(maximum_header_bytes, bool) or not isinstance(maximum_header_bytes, int):
        raise TypeError("maximum_header_bytes must be int")
    if maximum_header_bytes <= 0:
        raise ValueError("maximum_header_bytes must be positive")

    raw = bytearray()
    terminator: str | None = None
    for offset in range(maximum_header_bytes):
        chunk = read_byte(offset, f"header_byte:{key}:{offset}")
        if not isinstance(chunk, (bytes, bytearray)):
            raise TypeError("read_byte must return bytes")
        if len(chunk) != 1:
            raise HeaderGateStop(f"bounded byte read for {key} returned {len(chunk)} bytes")
        value = int(chunk[0])
        if value == 13:
            terminator = "CR"
            break
        if value == 10:
            terminator = "LF"
            break
        raw.append(value)
    else:
        raise HeaderGateStop(
            f"first physical record for {key} exceeded {maximum_header_bytes} bytes or lacked CR/LF"
        )

    if not raw:
        raise HeaderGateStop(f"empty first physical record for {key}")
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError as exc:
        raise HeaderGateStop(f"header for {key} is not valid {encoding}: {exc}") from exc

    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise HeaderGateStop(f"CSV header parse failed for {key}: {exc}") from exc
    if len(rows) != 1 or not rows[0]:
        raise HeaderGateStop(f"header for {key} did not parse as one non-empty CSV record")
    columns = tuple(rows[0])
    if any(not isinstance(col, str) or not col.strip() for col in columns):
        raise HeaderGateStop(f"header for {key} contains an empty column name")
    if len(set(columns)) != len(columns):
        raise HeaderGateStop(f"header for {key} contains duplicate column names")

    payload = {
        "key": key,
        "raw_header_text": text,
        "terminator": terminator,
        "bytes_consumed": len(raw) + 1,
        "columns": list(columns),
    }
    return HeaderEvidence(
        key=key,
        raw_header_text=text,
        terminator=terminator,
        bytes_consumed=len(raw) + 1,
        columns=columns,
        fingerprint=canonical_sha256(payload),
    )


def summarize_stage1a(headers: list[HeaderEvidence]) -> dict[str, object]:
    if not headers:
        raise ValueError("headers must not be empty")
    keys = [item.key for item in headers]
    if len(set(keys)) != len(keys):
        raise ValueError("header keys must be unique")
    ordered = sorted(headers, key=lambda item: item.key)
    result: dict[str, object] = {
        "schema": "eog.loomis_snowshoe_hare_endpoint3.stage1a_header_evidence.v1",
        "status": "stage1a_headers_ready",
        "counts_as_predictive_evidence": False,
        "files": [
            {
                "key": item.key,
                "raw_header_text": item.raw_header_text,
                "terminator": item.terminator,
                "bytes_consumed": item.bytes_consumed,
                "columns": list(item.columns),
                "fingerprint": item.fingerprint,
            }
            for item in ordered
        ],
        "deployment_rows_opened": 0,
        "detection_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "next_stage": "freeze exact physical field mapping from these headers only before deployment rows",
    }
    result["fingerprint"] = canonical_sha256(result)
    return result
