#!/usr/bin/env python3
"""Inspect the frozen Zenodo ZIP structure without opening member payload bytes.

This is a response-blind transport/identity step.  It reads one archive-size byte,
the fixed 22-byte zero-comment EOCD record, the exact central directory, and each
member's local header/name/extra metadata.  It never requests a compressed member
payload interval and therefore cannot inspect geometry or response rows/values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import urllib.request
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "archive_metadata_inventory.json"
USER_AGENT = "EOG-soil-microfauna-archive-metadata/1.0"

RangeReader = Callable[[int, int, str], bytes]


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


def _safe_member_name(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise RuntimeError("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        raise RuntimeError(f"unsafe ZIP member name: {value!r}")
    return value


def _overlaps(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def inspect_zip_metadata(
    archive_size: int, read_range: RangeReader
) -> dict[str, object]:
    """Return exact ZIP metadata using ranges that exclude all member payloads.

    The preflight intentionally supports only a classic, single-disk, zero-comment
    ZIP.  Anything requiring a backwards scan or ZIP64 discovery stops rather than
    risk reading bytes that may belong to a response-bearing member.
    """

    if isinstance(archive_size, bool) or not isinstance(archive_size, int):
        raise TypeError("archive_size must be int")
    if archive_size < 22:
        raise RuntimeError("archive is too small to contain a ZIP EOCD record")

    eocd_offset = archive_size - 22
    eocd = read_range(eocd_offset, archive_size - 1, "zip_eocd_zero_comment")
    if len(eocd) != 22 or eocd[:4] != b"PK\x05\x06":
        raise RuntimeError(
            "final 22 bytes are not a zero-comment ZIP EOCD; no backwards scan is allowed"
        )
    fields = struct.unpack("<4s4H2IH", eocd)
    disk_number, central_disk, disk_records, total_records = fields[1:5]
    central_size, central_offset, comment_size = fields[5:8]
    if comment_size != 0:
        raise RuntimeError(
            "ZIP comments are not permitted by this bounded metadata gate"
        )
    if disk_number != 0 or central_disk != 0 or disk_records != total_records:
        raise RuntimeError("multi-disk ZIP archives are not supported")
    if total_records <= 0:
        raise RuntimeError("ZIP central directory contains no members")
    if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (
        central_size,
        central_offset,
    ):
        raise RuntimeError("ZIP64 discovery is outside this bounded metadata gate")
    if central_size <= 0 or central_offset + central_size != eocd_offset:
        raise RuntimeError("central directory is not exactly adjacent to the EOCD")

    central = read_range(
        central_offset,
        central_offset + central_size - 1,
        "zip_central_directory",
    )
    if len(central) != central_size:
        raise RuntimeError("central-directory range length differs from the EOCD")

    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise RuntimeError("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise RuntimeError(f"invalid central-directory signature at byte {cursor}")
        flags = values[3]
        method = values[4]
        crc32 = values[7]
        compressed_size = values[8]
        uncompressed_size = values[9]
        name_size, extra_size, member_comment_size = values[10:13]
        disk_start = values[13]
        local_offset = values[16]
        if disk_start != 0:
            raise RuntimeError("member starts on a nonzero ZIP disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise RuntimeError("ZIP64 member metadata is outside this bounded gate")
        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise RuntimeError("central-directory variable fields are invalid")
        name_bytes = central[cursor + 46 : cursor + 46 + name_size]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        name = _safe_member_name(name_bytes.decode(encoding))
        members.append(
            {
                "name": name,
                "flags": flags,
                "compression_method": method,
                "crc32": f"{crc32:08x}",
                "compressed_size": compressed_size,
                "uncompressed_size": uncompressed_size,
                "local_header_offset": local_offset,
            }
        )
        cursor = end

    if cursor != len(central) or len(members) != total_records:
        raise RuntimeError(
            f"central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [str(member["name"]) for member in members]
    if len(set(names)) != len(names):
        raise RuntimeError("ZIP central directory contains duplicate member names")

    for member in members:
        offset = int(member["local_header_offset"])
        if offset < 0 or offset + 30 > central_offset:
            raise RuntimeError(
                f"local header offset is outside member area: {member['name']}"
            )
        fixed = read_range(offset, offset + 29, f"local_header:{member['name']}")
        if len(fixed) != 30:
            raise RuntimeError(f"truncated local header: {member['name']}")
        local = struct.unpack("<4s5H3I2H", fixed)
        if local[0] != b"PK\x03\x04":
            raise RuntimeError(f"invalid local header signature: {member['name']}")
        local_flags, local_method = local[2], local[3]
        name_size, extra_size = local[9], local[10]
        if name_size <= 0:
            raise RuntimeError(f"empty local member name: {member['name']}")
        variable = read_range(
            offset + 30,
            offset + 30 + name_size + extra_size - 1,
            f"local_name_extra:{member['name']}",
        )
        encoding = "utf-8" if int(member["flags"]) & 0x800 else "cp437"
        local_name = variable[:name_size].decode(encoding)
        if local_name != member["name"]:
            raise RuntimeError(f"local/central member name mismatch: {member['name']}")
        if (
            local_flags != member["flags"]
            or local_method != member["compression_method"]
        ):
            raise RuntimeError(
                f"local/central ZIP flags or method mismatch: {member['name']}"
            )
        payload_start = offset + 30 + name_size + extra_size
        compressed_size = int(member["compressed_size"])
        payload_end = payload_start + compressed_size - 1
        if compressed_size and payload_end >= central_offset:
            raise RuntimeError(
                f"member payload overlaps central directory: {member['name']}"
            )
        member["local_metadata_start"] = offset
        member["local_metadata_end"] = payload_start - 1
        member["payload_start"] = payload_start
        member["payload_end"] = payload_end if compressed_size else None

    payload_intervals = sorted(
        (
            int(member["payload_start"]),
            int(member["payload_end"]),
        )
        for member in members
        if member["payload_end"] is not None
    )
    for left, right in pairwise(payload_intervals):
        if _overlaps(left, right):
            raise RuntimeError("ZIP member payload intervals overlap")

    result = {
        "archive_size": archive_size,
        "central_directory_offset": central_offset,
        "central_directory_size": central_size,
        "central_directory_sha256": hashlib.sha256(central).hexdigest(),
        "eocd_offset": eocd_offset,
        "eocd_comment_size": comment_size,
        "member_count": len(members),
        "members": members,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


class FrozenRangeTransport:
    """Strict HTTP Range reader bound to one frozen Zenodo archive identity."""

    def __init__(self, url: str, expected_size: int) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "zenodo.org":
            raise ValueError("archive URL must use HTTPS on zenodo.org")
        self.url = url
        self.expected_size = expected_size
        self.ledger: list[dict[str, object]] = []

    def read(self, start: int, end: int, role: str) -> bytes:
        if start < 0 or end < start or end >= self.expected_size:
            raise RuntimeError(f"invalid bounded range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_host = urlparse(response.geturl()).hostname
            ledger_row = {
                "role": role,
                "start": start,
                "end": end,
                "bytes": 0,
                "status": status,
                "content_range": headers.get("content-range"),
                "final_host": final_host,
            }
            self.ledger.append(ledger_row)
            if status != 206:
                raise RuntimeError(
                    f"range request returned HTTP {status}, expected 206"
                )
            match = re.fullmatch(
                rf"bytes {start}-{end}/(\d+)",
                headers.get("content-range", ""),
            )
            if match is None or int(match.group(1)) != self.expected_size:
                raise RuntimeError(
                    "Content-Range does not preserve the frozen archive size"
                )
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise RuntimeError(
                    "range response unexpectedly applied content encoding"
                )
            if final_host != "zenodo.org":
                raise RuntimeError(
                    f"range request left frozen Zenodo host: {final_host!r}"
                )
            body = response.read(end - start + 2)
            ledger_row["bytes"] = len(body)
        expected = end - start + 1
        if len(body) != expected:
            raise RuntimeError(f"range response length {len(body)} != {expected}")
        return body


def run(contract_path: Path, output_path: Path) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    gate = contract["archive_metadata_gate"]
    archive = gate["archive"]
    expected_size = int(archive["size_bytes"])
    transport = FrozenRangeTransport(str(archive["content_url"]), expected_size)
    base = {
        "schema": "eog.soil_microfauna_archive_metadata_preflight.v1",
        "attempt_id": contract["attempt_id"],
        "source_contract_sha256": hashlib.sha256(
            contract_path.read_bytes()
        ).hexdigest(),
        "metadata_evidence_run_id": gate["metadata_evidence"]["github_run_id"],
        "archive_name": archive["name"],
        "archive_expected_size": expected_size,
        "archive_expected_checksum": archive["checksum"],
        "member_payload_requests": 0,
        "member_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    try:
        first = transport.read(0, 0, "archive_size_and_signature_probe")
        if first != b"P":
            raise RuntimeError(
                "archive does not begin with a ZIP local-header signature"
            )
        inventory = inspect_zip_metadata(expected_size, transport.read)
        payload_intervals = [
            (int(member["payload_start"]), int(member["payload_end"]))
            for member in inventory["members"]
            if member["payload_end"] is not None
        ]
        for request in transport.ledger:
            request_interval = (int(request["start"]), int(request["end"]))
            if any(
                _overlaps(request_interval, payload) for payload in payload_intervals
            ):
                raise RuntimeError("metadata request overlapped a ZIP member payload")
        result = {
            **base,
            "status": "zip_metadata_inventory_pass",
            "archive_metadata_requests": len(transport.ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes"]) for row in transport.ledger
            ),
            "request_ledger": transport.ledger,
            "inventory": inventory,
        }
    except Exception as exc:  # noqa: BLE001 - every gate failure must leave a STOP artifact
        result = {
            **base,
            "status": "stop_pre_response_archive_metadata_unavailable",
            "archive_metadata_requests": len(transport.ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes"]) for row in transport.ledger
            ),
            "request_ledger": transport.ledger,
            "reason": repr(exc),
        }
    result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(args.contract, args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "zip_metadata_inventory_pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
