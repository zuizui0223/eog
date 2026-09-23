"""Strict classic-ZIP inventory and safe-member extraction for EOG-WF v2.

This module is transport-neutral. Callers provide a bounded read_range function.
It is designed for response-blind qualification of mixed archives: inspect ZIP metadata,
then extract only a prospectively declared safe member such as deployments.csv while
leaving biological-response members unopened.

The implementation supports classic single-disk ZIP archives and compression methods
STORE (0) and DEFLATE (8). ZIP64 and encrypted members fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass
import binascii
import hashlib
import json
from pathlib import PurePosixPath
import struct
from typing import Callable, Sequence
import zlib


RangeReader = Callable[[int, int, str], bytes]


class ZipSafeMemberError(RuntimeError):
    """Fail-closed ZIP metadata or safe-member extraction error."""


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _safe_member_name(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise ZipSafeMemberError("ZIP member name is empty or uses an unsafe separator")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or (path.parts and ":" in path.parts[0]):
        raise ZipSafeMemberError(f"unsafe ZIP member name: {value!r}")
    return value


@dataclass(frozen=True)
class ZipMemberRecord:
    name: str
    basename: str
    flags: int
    compression_method: int
    crc32: str
    compressed_size: int
    uncompressed_size: int
    local_header_offset: int
    fingerprint: str


@dataclass(frozen=True)
class ZipInventory:
    archive_size: int
    eocd_offset: int
    central_directory_offset: int
    central_directory_size: int
    central_directory_sha256: str
    members: tuple[ZipMemberRecord, ...]
    metadata_bytes_opened: int
    fingerprint: str

    def by_basename(self, basename: str) -> ZipMemberRecord:
        matches = [member for member in self.members if member.basename == basename]
        if len(matches) != 1:
            raise ZipSafeMemberError(
                f"required basename {basename!r} expected exactly once, observed {len(matches)}"
            )
        return matches[0]


@dataclass(frozen=True)
class SafeZipMemberPayload:
    member: ZipMemberRecord
    payload: bytes
    payload_sha256: str
    local_header_bytes_opened: int
    compressed_payload_bytes_opened: int
    fingerprint: str


def inspect_classic_zip(
    archive_size: int,
    read_range: RangeReader,
    *,
    maximum_central_directory_bytes: int,
) -> ZipInventory:
    """Inspect only EOCD and central directory of a classic, zero-comment ZIP."""

    if isinstance(archive_size, bool) or not isinstance(archive_size, int):
        raise TypeError("archive_size must be int")
    if archive_size < 22:
        raise ZipSafeMemberError("archive is too small for classic ZIP EOCD")
    if maximum_central_directory_bytes <= 0:
        raise ValueError("maximum_central_directory_bytes must be positive")

    metadata_bytes = 0
    eocd_offset = archive_size - 22
    eocd = read_range(eocd_offset, archive_size - 1, "zip_eocd")
    metadata_bytes += len(eocd)
    if len(eocd) != 22 or eocd[:4] != b"PK\x05\x06":
        raise ZipSafeMemberError(
            "final 22 bytes are not a zero-comment classic ZIP EOCD"
        )

    fields = struct.unpack("<4s4H2IH", eocd)
    disk_number, central_disk, disk_records, total_records = map(int, fields[1:5])
    central_size, central_offset, comment_size = map(int, fields[5:8])
    if comment_size != 0:
        raise ZipSafeMemberError("ZIP comments are outside the strict inventory route")
    if disk_number != 0 or central_disk != 0 or disk_records != total_records:
        raise ZipSafeMemberError("multi-disk ZIP archives are unsupported")
    if total_records <= 0:
        raise ZipSafeMemberError("ZIP central directory contains no members")
    if 0xFFFF in (disk_records, total_records) or 0xFFFFFFFF in (
        central_size,
        central_offset,
    ):
        raise ZipSafeMemberError("ZIP64 EOCD is unsupported")
    if central_size <= 0 or central_size > maximum_central_directory_bytes:
        raise ZipSafeMemberError("central-directory size exceeds frozen bound")
    if central_offset < 0 or central_offset + central_size != eocd_offset:
        raise ZipSafeMemberError("central directory is not adjacent to final EOCD")

    central = read_range(
        central_offset,
        central_offset + central_size - 1,
        "zip_central_directory",
    )
    metadata_bytes += len(central)
    if len(central) != central_size:
        raise ZipSafeMemberError("central-directory range length mismatch")

    members: list[ZipMemberRecord] = []
    cursor = 0
    while cursor < len(central):
        if cursor + 46 > len(central):
            raise ZipSafeMemberError("truncated central-directory member")
        values = struct.unpack_from("<4s6H3I5H2I", central, cursor)
        if values[0] != b"PK\x01\x02":
            raise ZipSafeMemberError(
                f"invalid central-directory signature at offset {cursor}"
            )

        flags = int(values[3])
        method = int(values[4])
        crc32_value = int(values[7])
        compressed_size = int(values[8])
        uncompressed_size = int(values[9])
        name_size, extra_size, member_comment_size = map(int, values[10:13])
        disk_start = int(values[13])
        local_offset = int(values[16])

        if flags & 0x1:
            raise ZipSafeMemberError("encrypted ZIP members are unsupported")
        if disk_start != 0:
            raise ZipSafeMemberError("ZIP member starts on nonzero disk")
        if 0xFFFFFFFF in (compressed_size, uncompressed_size, local_offset):
            raise ZipSafeMemberError("ZIP64 member metadata are unsupported")
        if local_offset < 0 or local_offset >= central_offset:
            raise ZipSafeMemberError("member local-header offset is outside member area")

        end = cursor + 46 + name_size + extra_size + member_comment_size
        if name_size <= 0 or end > len(central):
            raise ZipSafeMemberError("invalid central-directory variable fields")

        name_bytes = central[cursor + 46 : cursor + 46 + name_size]
        encoding = "utf-8" if flags & 0x800 else "cp437"
        try:
            decoded = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            raise ZipSafeMemberError("member name failed declared encoding") from exc
        name = _safe_member_name(decoded)

        member_payload = {
            "name": name,
            "flags": flags,
            "compression_method": method,
            "crc32": f"{crc32_value:08x}",
            "compressed_size": compressed_size,
            "uncompressed_size": uncompressed_size,
            "local_header_offset": local_offset,
        }
        members.append(
            ZipMemberRecord(
                name=name,
                basename=PurePosixPath(name).name,
                flags=flags,
                compression_method=method,
                crc32=f"{crc32_value:08x}",
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
                local_header_offset=local_offset,
                fingerprint=_sha256(member_payload),
            )
        )
        cursor = end

    if cursor != len(central) or len(members) != total_records:
        raise ZipSafeMemberError(
            f"central-directory member count mismatch: {len(members)} != {total_records}"
        )
    names = [member.name for member in members]
    if len(names) != len(set(names)):
        raise ZipSafeMemberError("ZIP contains duplicate member names")

    payload = {
        "schema": "eog.zip_inventory.v1",
        "archive_size": archive_size,
        "eocd_offset": eocd_offset,
        "central_directory_offset": central_offset,
        "central_directory_size": central_size,
        "central_directory_sha256": hashlib.sha256(central).hexdigest(),
        "members": [
            {
                "name": member.name,
                "basename": member.basename,
                "flags": member.flags,
                "compression_method": member.compression_method,
                "crc32": member.crc32,
                "compressed_size": member.compressed_size,
                "uncompressed_size": member.uncompressed_size,
                "local_header_offset": member.local_header_offset,
                "fingerprint": member.fingerprint,
            }
            for member in members
        ],
        "metadata_bytes_opened": metadata_bytes,
    }
    return ZipInventory(
        archive_size=archive_size,
        eocd_offset=eocd_offset,
        central_directory_offset=central_offset,
        central_directory_size=central_size,
        central_directory_sha256=hashlib.sha256(central).hexdigest(),
        members=tuple(members),
        metadata_bytes_opened=metadata_bytes,
        fingerprint=_sha256(payload),
    )


def extract_safe_member(
    inventory: ZipInventory,
    member: ZipMemberRecord,
    read_range: RangeReader,
    *,
    maximum_compressed_bytes: int,
    maximum_uncompressed_bytes: int,
) -> SafeZipMemberPayload:
    """Extract one already-declared safe member without touching any other payload."""

    if member not in inventory.members:
        raise ValueError("member is not part of the supplied inventory")
    if maximum_compressed_bytes <= 0 or maximum_uncompressed_bytes <= 0:
        raise ValueError("safe-member byte bounds must be positive")
    if member.compressed_size > maximum_compressed_bytes:
        raise ZipSafeMemberError("safe member compressed size exceeds frozen bound")
    if member.uncompressed_size > maximum_uncompressed_bytes:
        raise ZipSafeMemberError("safe member uncompressed size exceeds frozen bound")
    if member.compression_method not in {0, 8}:
        raise ZipSafeMemberError(
            f"unsupported safe-member compression method {member.compression_method}"
        )

    offset = member.local_header_offset
    fixed = read_range(offset, offset + 29, "zip_safe_member_local_header")
    if len(fixed) != 30:
        raise ZipSafeMemberError("truncated safe-member local header")
    values = struct.unpack("<4s5H3I2H", fixed)
    if values[0] != b"PK\x03\x04":
        raise ZipSafeMemberError("invalid safe-member local-header signature")

    flags = int(values[2])
    method = int(values[3])
    local_crc = int(values[6])
    local_compressed = int(values[7])
    local_uncompressed = int(values[8])
    name_size = int(values[9])
    extra_size = int(values[10])

    if flags != member.flags:
        raise ZipSafeMemberError("safe-member local-header flags differ from central directory")
    if method != member.compression_method:
        raise ZipSafeMemberError(
            "safe-member local-header compression method differs from central directory"
        )

    variable_size = name_size + extra_size
    variable = (
        b""
        if variable_size == 0
        else read_range(
            offset + 30,
            offset + 30 + variable_size - 1,
            "zip_safe_member_local_name_extra",
        )
    )
    if len(variable) != variable_size:
        raise ZipSafeMemberError("truncated safe-member local name/extra fields")

    name_bytes = variable[:name_size]
    encoding = "utf-8" if flags & 0x800 else "cp437"
    try:
        local_name = name_bytes.decode(encoding)
    except UnicodeDecodeError as exc:
        raise ZipSafeMemberError("safe-member local name failed declared encoding") from exc
    if local_name != member.name:
        raise ZipSafeMemberError("safe-member local name differs from central directory")

    if not (flags & 0x08):
        if local_crc != int(member.crc32, 16):
            raise ZipSafeMemberError("safe-member local CRC differs from central directory")
        if local_compressed != member.compressed_size:
            raise ZipSafeMemberError(
                "safe-member local compressed size differs from central directory"
            )
        if local_uncompressed != member.uncompressed_size:
            raise ZipSafeMemberError(
                "safe-member local uncompressed size differs from central directory"
            )

    payload_start = offset + 30 + variable_size
    if member.compressed_size == 0:
        compressed = b""
    else:
        payload_end = payload_start + member.compressed_size - 1
        if payload_end >= inventory.central_directory_offset:
            raise ZipSafeMemberError("safe-member payload overlaps central directory")
        compressed = read_range(
            payload_start,
            payload_end,
            "zip_safe_member_compressed_payload",
        )
    if len(compressed) != member.compressed_size:
        raise ZipSafeMemberError("safe-member compressed payload length mismatch")

    if member.compression_method == 0:
        payload_bytes = compressed
    else:
        try:
            payload_bytes = zlib.decompress(compressed, -zlib.MAX_WBITS)
        except zlib.error as exc:
            raise ZipSafeMemberError("safe-member DEFLATE payload failed to decompress") from exc

    if len(payload_bytes) != member.uncompressed_size:
        raise ZipSafeMemberError("safe-member uncompressed size mismatch")
    crc = binascii.crc32(payload_bytes) & 0xFFFFFFFF
    if f"{crc:08x}" != member.crc32:
        raise ZipSafeMemberError("safe-member CRC mismatch")

    local_bytes = len(fixed) + len(variable)
    result_payload = {
        "schema": "eog.safe_zip_member_payload.v1",
        "member_fingerprint": member.fingerprint,
        "payload_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "payload_bytes": len(payload_bytes),
        "local_header_bytes_opened": local_bytes,
        "compressed_payload_bytes_opened": len(compressed),
    }
    return SafeZipMemberPayload(
        member=member,
        payload=payload_bytes,
        payload_sha256=hashlib.sha256(payload_bytes).hexdigest(),
        local_header_bytes_opened=local_bytes,
        compressed_payload_bytes_opened=len(compressed),
        fingerprint=_sha256(result_payload),
    )


def require_unique_basenames(
    inventory: ZipInventory,
    basenames: Sequence[str],
) -> dict[str, ZipMemberRecord]:
    """Resolve prospectively declared unique basenames without opening member payloads."""

    values = tuple(str(value).strip() for value in basenames)
    if not values or any(not value for value in values):
        raise ValueError("basenames must be non-empty strings")
    if len(values) != len(set(values)):
        raise ValueError("basenames must be unique")
    return {basename: inventory.by_basename(basename) for basename in values}
