from __future__ import annotations

import hashlib
import json
import re
import struct
import urllib.error
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Callable
from urllib.parse import urlparse


HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "source_contract.json"
DEFAULT_OUTPUT = HERE / "gate0_zip_inventory_certificate.json"
USER_AGENT = "EOG-Forest-First-Endpoint3-Gate0/1.0"
RangeReader = Callable[[int, int, str], bytes]


class Gate0Stop(RuntimeError):
    """Terminal response-blind archive transport or ZIP inventory STOP."""


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
        raise Gate0Stop("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or (path.parts and ":" in path.parts[0]):
        raise Gate0Stop(f"unsafe ZIP member name: {value!r}")
    return value


def _parse_central_directory(
    central: bytes,
    total_records: int,
    central_offset: int,
) -> list[dict[str, object]]:
    members: list[dict[str, object]] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise Gate0Stop("truncated ZIP central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise Gate0Stop(f"invalid central-directory signature at byte {cursor}")
        flags = int(values[3])
        method = int(values[4])
        crc32 = int(values[7])
        compressed_size = int(values[8])
        uncompressed_size = int(values[9])
        name_size, extra_size, member_comment_size = map(int, values[10:13])
        disk_start = int(values[13])
        local_offset = int(values[16])
        if flags & 0x1:
            raise Gate0Stop("encrypted ZIP members are outside the frozen Gate0")
        if disk_start != 0:
            raise Gate0Stop("ZIP member starts on a nonzero disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise Gate0Stop("ZIP64 member metadata are outside the frozen Gate0")
        if local_offset < 0 or local_offset >= central_offset:
            raise Gate0Stop("ZIP local-header offset is outside the member area")
        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise Gate0Stop("ZIP central-directory variable fields are invalid")
        name_bytes = central[cursor + 46 : cursor + 46 + name_size]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        try:
            decoded = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            raise Gate0Stop("ZIP member name failed its declared encoding") from exc
        name = _safe_member_name(decoded)
        members.append(
            {
                "name": name,
                "basename": PurePosixPath(name).name,
                "parent": PurePosixPath(name).parent.as_posix(),
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
        raise Gate0Stop(
            f"ZIP central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [str(row["name"]) for row in members]
    if len(names) != len(set(names)):
        raise Gate0Stop("ZIP central directory contains duplicate member names")
    return members


def inspect_zip_inventory(
    archive_size: int,
    read_range: RangeReader,
    *,
    maximum_central_directory_bytes: int,
) -> dict[str, object]:
    """Read only the final classic EOCD and central directory; never a local header/payload."""
    if isinstance(archive_size, bool) or not isinstance(archive_size, int) or archive_size < 22:
        raise Gate0Stop("archive size is invalid for classic ZIP inventory")
    eocd_offset = archive_size - 22
    eocd = read_range(eocd_offset, archive_size - 1, "zip_eocd_zero_comment")
    if len(eocd) != 22 or eocd[:4] != b"PK\x05\x06":
        raise Gate0Stop(
            "final 22 bytes are not a zero-comment classic ZIP EOCD; backwards scanning is forbidden"
        )
    fields = struct.unpack("<4s4H2IH", eocd)
    disk_number, central_disk, disk_records, total_records = map(int, fields[1:5])
    central_size, central_offset, comment_size = map(int, fields[5:8])
    if comment_size != 0:
        raise Gate0Stop("ZIP comments are outside the frozen Gate0")
    if disk_number != 0 or central_disk != 0 or disk_records != total_records:
        raise Gate0Stop("multi-disk ZIP archives are outside the frozen Gate0")
    if total_records <= 0:
        raise Gate0Stop("ZIP central directory contains no members")
    if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (central_size, central_offset):
        raise Gate0Stop("ZIP64 EOCD metadata are outside the frozen Gate0")
    if central_size <= 0 or central_size > maximum_central_directory_bytes:
        raise Gate0Stop("ZIP central directory size is outside the frozen Gate0 bound")
    if central_offset < 0 or central_offset + central_size != eocd_offset:
        raise Gate0Stop("ZIP central directory is not exactly adjacent to the EOCD")
    central = read_range(
        central_offset,
        central_offset + central_size - 1,
        "zip_central_directory",
    )
    if len(central) != central_size:
        raise Gate0Stop("central-directory range length differs from EOCD metadata")
    members = _parse_central_directory(central, total_records, central_offset)
    result: dict[str, object] = {
        "archive_size": archive_size,
        "eocd_offset": eocd_offset,
        "zip_comment_size": comment_size,
        "central_directory_offset": central_offset,
        "central_directory_size": central_size,
        "central_directory_sha256": hashlib.sha256(central).hexdigest(),
        "member_count": len(members),
        "members": members,
        "local_header_bytes_opened": 0,
        "member_payload_bytes_opened": 0,
    }
    result["fingerprint"] = canonical_sha256(result)
    return result


def select_required_members(
    inventory: dict[str, object],
    required_basenames: list[str],
) -> dict[str, dict[str, object]]:
    members = inventory.get("members")
    if not isinstance(members, list):
        raise Gate0Stop("ZIP inventory has no member list")
    selected: dict[str, dict[str, object]] = {}
    for basename in required_basenames:
        matches = [
            row
            for row in members
            if isinstance(row, dict) and row.get("basename") == basename
        ]
        if len(matches) != 1:
            raise Gate0Stop(
                f"required basename {basename!r} expected exactly once, observed {len(matches)}"
            )
        selected[basename] = dict(matches[0])
    if len({str(row["name"]) for row in selected.values()}) != len(selected):
        raise Gate0Stop("two frozen roles resolved to the same ZIP member")
    return selected


class StrictIptRangeTransport:
    def __init__(
        self,
        url: str,
        allowed_hosts: tuple[str, ...],
        maximum_archive_size: int,
        *,
        opener=None,
    ) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
            raise ValueError("archive URL must be HTTPS on a frozen allowed host")
        self.url = url
        self.allowed_hosts = allowed_hosts
        self.maximum_archive_size = int(maximum_archive_size)
        self.archive_size: int | None = None
        self.range_ledger: list[dict[str, object]] = []
        self.opener = opener or urllib.request.build_opener()

    def _validate_final(self, final_url: str) -> str:
        parsed = urlparse(final_url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise Gate0Stop(f"range request left frozen host set: {parsed.hostname!r}")
        return parsed.hostname or ""

    def probe_size(self) -> int:
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": "bytes=0-0",
            },
        )
        ledger: dict[str, object] = {
            "role": "archive_size_probe",
            "start": 0,
            "end": 0,
            "status": None,
            "content_range": None,
            "final_host": None,
            "bytes_opened": 0,
        }
        self.range_ledger.append(ledger)
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            ledger["status"] = int(exc.code)
            raise Gate0Stop(f"archive size probe returned HTTP {exc.code}; body was not opened") from exc
        except (OSError, urllib.error.URLError) as exc:
            raise Gate0Stop(f"archive size probe transport unavailable: {exc}") from exc
        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            ledger["status"] = status
            ledger["content_range"] = headers.get("content-range")
            ledger["final_host"] = self._validate_final(response.geturl())
            if status != 206:
                raise Gate0Stop(f"archive size probe returned HTTP {status}; body was not opened")
            match = re.fullmatch(r"bytes 0-0/([1-9][0-9]*)", headers.get("content-range", ""))
            if match is None:
                raise Gate0Stop("archive size probe lacked exact Content-Range bytes 0-0/<size>")
            archive_size = int(match.group(1))
            if archive_size < 22 or archive_size > self.maximum_archive_size:
                raise Gate0Stop("archive size is outside the prospectively frozen bound")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate0Stop("archive size probe unexpectedly applied content encoding")
            body = response.read(2)
            ledger["bytes_opened"] = len(body)
        if len(body) != 1:
            raise Gate0Stop(f"archive size probe opened {len(body)} bytes instead of exactly one")
        self.archive_size = archive_size
        return archive_size

    def read_range(self, start: int, end: int, role: str) -> bytes:
        if self.archive_size is None:
            raise RuntimeError("probe_size must pass before metadata range reads")
        if start < 0 or end < start or end >= self.archive_size:
            raise Gate0Stop(f"invalid bounded range {start}-{end}")
        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        ledger: dict[str, object] = {
            "role": role,
            "start": start,
            "end": end,
            "status": None,
            "content_range": None,
            "final_host": None,
            "bytes_opened": 0,
        }
        self.range_ledger.append(ledger)
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            ledger["status"] = int(exc.code)
            raise Gate0Stop(f"bounded range returned HTTP {exc.code}; body was not opened") from exc
        except (OSError, urllib.error.URLError) as exc:
            raise Gate0Stop(f"bounded range transport unavailable: {exc}") from exc
        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            ledger["status"] = status
            ledger["content_range"] = headers.get("content-range")
            ledger["final_host"] = self._validate_final(response.geturl())
            if status != 206:
                raise Gate0Stop(f"bounded range returned HTTP {status}; body was not opened")
            expected_content_range = f"bytes {start}-{end}/{self.archive_size}"
            if headers.get("content-range") != expected_content_range:
                raise Gate0Stop("bounded range Content-Range drifted from frozen archive size")
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise Gate0Stop("bounded range unexpectedly applied content encoding")
            expected = end - start + 1
            body = response.read(expected + 1)
            ledger["bytes_opened"] = len(body)
        if len(body) != expected:
            raise Gate0Stop(f"bounded range opened {len(body)} bytes instead of {expected}")
        return body


def run(
    contract_path: Path = DEFAULT_CONTRACT,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    transport_factory=StrictIptRangeTransport,
) -> dict[str, object]:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = contract["source"]
    gate = contract["gate0"]
    base: dict[str, object] = {
        "schema": "eog.forest_first_endpoint3.gate0_zip_inventory.v1",
        "attempt_id": contract["attempt_id"],
        "issue": contract["issue"],
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "archive_url": source["archive_url"],
        "status": None,
        "range_requests": 0,
        "archive_metadata_bytes_opened": 0,
        "local_header_bytes_opened": 0,
        "member_payload_bytes_opened": 0,
        "datapackage_payload_bytes_opened": 0,
        "deployments_payload_bytes_opened": 0,
        "observations_header_bytes_opened": 0,
        "observations_payload_bytes_opened": 0,
        "observations_rows_opened": 0,
        "observations_values_opened": False,
        "media_payload_bytes_opened": 0,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    transport = transport_factory(
        str(source["archive_url"]),
        tuple(source["allowed_final_hosts"]),
        int(gate["maximum_archive_size_bytes"]),
    )
    try:
        archive_size = transport.probe_size()
        inventory = inspect_zip_inventory(
            archive_size,
            transport.read_range,
            maximum_central_directory_bytes=int(gate["maximum_central_directory_bytes"]),
        )
        selected = select_required_members(
            inventory,
            list(gate["required_unique_basenames"]),
        )
        result = {
            **base,
            "status": "gate0_zip_inventory_ready",
            "archive_size": archive_size,
            "inventory": inventory,
            "required_members": selected,
            "next_gate": "open only datapackage.json and deployments.csv under a separately frozen safe-member gate",
        }
    except (Gate0Stop, ValueError) as exc:
        result = {
            **base,
            "status": "stop_pre_response_zip_transport_or_inventory",
            "reason": str(exc),
            "next_gate": "none; do not open archive member payloads and do not repair/rerun this attempt",
        }
    ledger = list(getattr(transport, "range_ledger", []))
    result["range_requests"] = len(ledger)
    result["archive_metadata_bytes_opened"] = sum(int(row.get("bytes_opened", 0)) for row in ledger)
    result["range_ledger"] = ledger
    result["fingerprint"] = canonical_sha256({k: v for k, v in result.items() if k != "fingerprint"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    run()
