from __future__ import annotations

import hashlib
import json
import re
import struct
import urllib.error
import urllib.request
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "gate5_archive_metadata_contract.json"
DEFAULT_OUTPUT = (
    ROOT
    / "build"
    / "bbs_northern_bobwhite_replication_2"
    / "gate5_archive_metadata.json"
)
USER_AGENT = "EOG-BBS-Northern-Bobwhite-Gate5/1.0"
RangeReader = Callable[[int, int, str], bytes]


class ArchiveGateStop(RuntimeError):
    """A terminal response-blind source/transport/metadata STOP."""


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
        raise ArchiveGateStop("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ":" in path.parts[0]:
        raise ArchiveGateStop(f"unsafe ZIP member name: {value!r}")
    return value


def _overlaps(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def inspect_zip_metadata(
    archive_size: int,
    read_range: RangeReader,
) -> dict[str, object]:
    """Read classic ZIP container metadata without reading any member payload."""

    if isinstance(archive_size, bool) or not isinstance(archive_size, int):
        raise TypeError("archive_size must be int")
    if archive_size < 22:
        raise ArchiveGateStop("archive is too small to contain a ZIP EOCD")

    eocd_offset = archive_size - 22
    eocd = read_range(eocd_offset, archive_size - 1, "zip_eocd_zero_comment")
    if len(eocd) != 22 or eocd[:4] != b"PK\x05\x06":
        raise ArchiveGateStop(
            "final 22 bytes are not a zero-comment ZIP EOCD; backwards scanning is forbidden"
        )
    fields = struct.unpack("<4s4H2IH", eocd)
    disk_number, central_disk, disk_records, total_records = fields[1:5]
    central_size, central_offset, comment_size = fields[5:8]
    if comment_size != 0:
        raise ArchiveGateStop("ZIP comments are outside this bounded metadata gate")
    if disk_number != 0 or central_disk != 0 or disk_records != total_records:
        raise ArchiveGateStop("multi-disk ZIP archives are outside this gate")
    if total_records <= 0:
        raise ArchiveGateStop("ZIP central directory contains no members")
    if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (
        central_size,
        central_offset,
    ):
        raise ArchiveGateStop("ZIP64 discovery is outside this bounded gate")
    if central_size <= 0 or central_offset + central_size != eocd_offset:
        raise ArchiveGateStop("central directory is not exactly adjacent to the EOCD")

    central = read_range(
        central_offset,
        central_offset + central_size - 1,
        "zip_central_directory",
    )
    if len(central) != central_size:
        raise ArchiveGateStop("central-directory range length differs from the EOCD")

    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise ArchiveGateStop("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise ArchiveGateStop(
                f"invalid central-directory signature at byte {cursor}"
            )
        flags = values[3]
        method = values[4]
        crc32 = values[7]
        compressed_size = values[8]
        uncompressed_size = values[9]
        name_size, extra_size, member_comment_size = values[10:13]
        disk_start = values[13]
        local_offset = values[16]
        if flags & 0x1:
            raise ArchiveGateStop("encrypted ZIP members are outside this gate")
        if disk_start != 0:
            raise ArchiveGateStop("member starts on a nonzero ZIP disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise ArchiveGateStop("ZIP64 member metadata are outside this gate")
        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise ArchiveGateStop("central-directory variable fields are invalid")
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
        raise ArchiveGateStop(
            f"central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [str(member["name"]) for member in members]
    if len(set(names)) != len(names):
        raise ArchiveGateStop("ZIP central directory contains duplicate member names")

    for member in members:
        offset = int(member["local_header_offset"])
        if offset < 0 or offset + 30 > central_offset:
            raise ArchiveGateStop(
                f"local header offset is outside member area: {member['name']}"
            )
        fixed = read_range(offset, offset + 29, f"local_header:{member['name']}")
        if len(fixed) != 30:
            raise ArchiveGateStop(f"truncated local header: {member['name']}")
        local = struct.unpack("<4s5H3I2H", fixed)
        if local[0] != b"PK\x03\x04":
            raise ArchiveGateStop(f"invalid local header signature: {member['name']}")
        local_flags, local_method = local[2], local[3]
        name_size, extra_size = local[9], local[10]
        if name_size <= 0:
            raise ArchiveGateStop(f"empty local member name: {member['name']}")
        variable = read_range(
            offset + 30,
            offset + 30 + name_size + extra_size - 1,
            f"local_name_extra:{member['name']}",
        )
        encoding = "utf-8" if int(member["flags"]) & 0x800 else "cp437"
        local_name = variable[:name_size].decode(encoding)
        if local_name != member["name"]:
            raise ArchiveGateStop(
                f"local/central member name mismatch: {member['name']}"
            )
        if (
            local_flags != member["flags"]
            or local_method != member["compression_method"]
        ):
            raise ArchiveGateStop(
                f"local/central ZIP flags or method mismatch: {member['name']}"
            )
        payload_start = offset + 30 + name_size + extra_size
        compressed_size = int(member["compressed_size"])
        payload_end = payload_start + compressed_size - 1
        if compressed_size and payload_end >= central_offset:
            raise ArchiveGateStop(
                f"member payload overlaps central directory: {member['name']}"
            )
        member["local_metadata_start"] = offset
        member["local_metadata_end"] = payload_start - 1
        member["payload_start"] = payload_start
        member["payload_end"] = payload_end if compressed_size else None

    payload_intervals = sorted(
        (int(member["payload_start"]), int(member["payload_end"]))
        for member in members
        if member["payload_end"] is not None
    )
    for left, right in pairwise(payload_intervals):
        if _overlaps(left, right):
            raise ArchiveGateStop("ZIP member payload intervals overlap")

    result: dict[str, object] = {
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
    """Strict byte-range reader for the frozen ScienceBase response archive."""

    def __init__(
        self,
        url: str,
        expected_size: int,
        allowed_final_hosts: tuple[str, ...],
    ) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != "www.sciencebase.gov":
            raise ValueError("archive URL must use HTTPS on www.sciencebase.gov")
        if not allowed_final_hosts:
            raise ValueError("allowed_final_hosts must not be empty")
        self.url = url
        self.expected_size = expected_size
        self.allowed_final_hosts = allowed_final_hosts
        self.ledger: list[dict[str, object]] = []

    def read(self, start: int, end: int, role: str) -> bytes:
        if start < 0 or end < start or end >= self.expected_size:
            raise ArchiveGateStop(f"invalid bounded range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        try:
            response_context = urllib.request.urlopen(request, timeout=90)
        except (OSError, urllib.error.URLError) as exc:
            raise ArchiveGateStop(
                f"bounded range transport unavailable: {exc}"
            ) from exc

        with response_context as response:
            status = getattr(response, "status", None) or response.getcode()
            headers = {key.lower(): value for key, value in response.headers.items()}
            final = urlparse(response.geturl())
            ledger_row: dict[str, object] = {
                "role": role,
                "start": start,
                "end": end,
                "bytes": 0,
                "status": status,
                "content_range": headers.get("content-range"),
                "final_host": final.hostname,
            }
            self.ledger.append(ledger_row)
            if status != 206:
                raise ArchiveGateStop(
                    f"range request returned HTTP {status}; response body was not opened"
                )
            match = re.fullmatch(
                rf"bytes {start}-{end}/(\d+)",
                headers.get("content-range", ""),
            )
            if match is None or int(match.group(1)) != self.expected_size:
                raise ArchiveGateStop(
                    "Content-Range does not preserve the frozen archive size"
                )
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise ArchiveGateStop(
                    "range response unexpectedly applied content encoding"
                )
            if (
                final.scheme != "https"
                or final.hostname not in self.allowed_final_hosts
            ):
                raise ArchiveGateStop(
                    f"range request left the frozen ScienceBase host set: {final.hostname!r}"
                )
            body = response.read(end - start + 2)
            ledger_row["bytes"] = len(body)
        expected = end - start + 1
        if len(body) != expected:
            raise ArchiveGateStop(f"range response length {len(body)} != {expected}")
        return body


def _verify_prerequisites(contract: dict[str, object]) -> None:
    expected = contract["prerequisite_sha256"]
    for name, digest in expected.items():
        actual = hashlib.sha256(
            (HERE / name).read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        if actual != digest:
            raise RuntimeError(f"prerequisite SHA-256 drift for {name}: {actual}")


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    archive = contract["archive"]
    expected_size = int(archive["size_bytes"])
    transport = FrozenRangeTransport(
        str(archive["download_url"]),
        expected_size,
        tuple(archive["allowed_final_hosts"]),
    )
    base: dict[str, object] = {
        "schema": "eog.bbs_northern_bobwhite_replication_2.gate5_archive_metadata.v1",
        "attempt_id": contract["attempt_id"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "archive_name": archive["name"],
        "archive_expected_size": expected_size,
        "archive_expected_md5": archive["md5"],
        "gate4_required": contract["gate4_required"],
        "response_firewall": contract["response_firewall"],
    }
    try:
        _verify_prerequisites(contract)
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
                raise ArchiveGateStop(
                    "archive metadata request overlapped a ZIP member payload"
                )
        result = {
            **base,
            "status": "gate5_pass_archive_container_metadata",
            "archive_metadata_requests": len(transport.ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes"]) for row in transport.ledger
            ),
            "request_ledger": transport.ledger,
            "inventory": inventory,
            "decision": (
                "PASS: exact ZIP container/member metadata are available without member "
                "payload access; freeze the focal physical response-member identity before "
                "any bounded header attempt"
            ),
        }
    except ArchiveGateStop as exc:
        result = {
            **base,
            "status": "stop_pre_response_archive_metadata_unavailable",
            "archive_metadata_requests": len(transport.ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes"]) for row in transport.ledger
            ),
            "request_ledger": transport.ledger,
            "reason": str(exc),
            "decision": (
                "STOP: do not download, scan, decompress or repair the response archive; "
                "this attempt supplies no predictive evidence"
            ),
        }
    except Exception as exc:  # noqa: BLE001 - preserve an artifact for engineering failures
        result = {
            **base,
            "status": "engineering_failure_pre_response",
            "archive_metadata_requests": len(transport.ledger),
            "archive_metadata_bytes_opened": sum(
                int(row["bytes"]) for row in transport.ledger
            ),
            "request_ledger": transport.ledger,
            "reason": f"{type(exc).__name__}: {exc}",
        }

    result["fingerprint"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] == "engineering_failure_pre_response":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
