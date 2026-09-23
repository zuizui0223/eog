from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

import pytest

from eog.v2.zip_safe_member import (
    ZipSafeMemberError,
    extract_safe_member,
    inspect_classic_zip,
    require_unique_basenames,
)


def make_zip(*, compression=ZIP_DEFLATED):
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=compression) as archive:
        archive.writestr(
            "data/deployments.csv",
            "deploymentID,latitude,longitude\nD1,50.0,4.0\nD2,50.1,4.1\n",
        )
        archive.writestr(
            "data/observations.csv",
            "deploymentID,scientificName\nD1,SECRET_RESPONSE_SPECIES\n",
        )
        archive.writestr("datapackage.json", '{"name":"test"}')
    return buffer.getvalue()


class RangeAudit:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, start, end, role):
        self.calls.append((start, end, role))
        return self.payload[start : end + 1]


def _payload_range(member, reader):
    before = len(reader.calls)
    result = extract_safe_member(
        inventory=reader.inventory,
        member=member,
        read_range=reader,
        maximum_compressed_bytes=100_000,
        maximum_uncompressed_bytes=100_000,
    )
    calls = reader.calls[before:]
    payload_calls = [call for call in calls if call[2] == "zip_safe_member_compressed_payload"]
    return result, payload_calls


@pytest.mark.parametrize("compression", [ZIP_STORED, ZIP_DEFLATED])
def test_extracts_only_declared_safe_member(compression):
    payload = make_zip(compression=compression)
    reader = RangeAudit(payload)
    inventory = inspect_classic_zip(
        len(payload),
        reader,
        maximum_central_directory_bytes=100_000,
    )
    reader.inventory = inventory

    members = require_unique_basenames(
        inventory,
        ("deployments.csv", "observations.csv"),
    )
    deployments = members["deployments.csv"]
    observations = members["observations.csv"]

    result, safe_payload_calls = _payload_range(deployments, reader)

    assert b"SECRET_RESPONSE_SPECIES" not in result.payload
    assert result.payload.startswith(b"deploymentID,latitude,longitude")
    assert result.member.basename == "deployments.csv"
    assert result.payload_sha256
    assert len(safe_payload_calls) == 1

    response_start = observations.local_header_offset
    response_end = inventory.central_directory_offset - 1
    # No read issued by safe-member extraction may begin inside the response member.
    assert not any(
        response_start <= start <= response_end
        and role.startswith("zip_safe_member")
        for start, _, role in reader.calls
    )


def test_inventory_reads_only_eocd_and_central_directory():
    payload = make_zip()
    reader = RangeAudit(payload)
    inventory = inspect_classic_zip(
        len(payload),
        reader,
        maximum_central_directory_bytes=100_000,
    )
    assert [role for _, _, role in reader.calls] == [
        "zip_eocd",
        "zip_central_directory",
    ]
    assert inventory.metadata_bytes_opened == 22 + inventory.central_directory_size
    assert {member.basename for member in inventory.members} == {
        "deployments.csv",
        "observations.csv",
        "datapackage.json",
    }


def test_duplicate_required_basename_is_rejected():
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("a/deployments.csv", "a")
        archive.writestr("b/deployments.csv", "b")
    payload = buffer.getvalue()
    reader = RangeAudit(payload)
    inventory = inspect_classic_zip(
        len(payload),
        reader,
        maximum_central_directory_bytes=100_000,
    )
    with pytest.raises(ZipSafeMemberError, match="expected exactly once"):
        inventory.by_basename("deployments.csv")


def test_safe_member_size_bounds_fail_before_payload_read():
    payload = make_zip()
    reader = RangeAudit(payload)
    inventory = inspect_classic_zip(
        len(payload),
        reader,
        maximum_central_directory_bytes=100_000,
    )
    member = inventory.by_basename("deployments.csv")
    before = len(reader.calls)
    with pytest.raises(ZipSafeMemberError, match="uncompressed size exceeds"):
        extract_safe_member(
            inventory,
            member,
            reader,
            maximum_compressed_bytes=100_000,
            maximum_uncompressed_bytes=1,
        )
    assert len(reader.calls) == before


def test_unknown_compression_method_fails_closed_before_payload():
    payload = make_zip()
    reader = RangeAudit(payload)
    inventory = inspect_classic_zip(
        len(payload),
        reader,
        maximum_central_directory_bytes=100_000,
    )
    member = inventory.by_basename("deployments.csv")
    fake = type(member)(
        name=member.name,
        basename=member.basename,
        flags=member.flags,
        compression_method=99,
        crc32=member.crc32,
        compressed_size=member.compressed_size,
        uncompressed_size=member.uncompressed_size,
        local_header_offset=member.local_header_offset,
        fingerprint=member.fingerprint,
    )
    with pytest.raises(ValueError, match="not part of"):
        extract_safe_member(
            inventory,
            fake,
            reader,
            maximum_compressed_bytes=100_000,
            maximum_uncompressed_bytes=100_000,
        )


def test_member_payload_crc_is_verified():
    payload = bytearray(make_zip(compression=ZIP_STORED))
    reader0 = RangeAudit(bytes(payload))
    inventory = inspect_classic_zip(
        len(payload),
        reader0,
        maximum_central_directory_bytes=100_000,
    )
    member = inventory.by_basename("deployments.csv")

    # Derive the payload start from the local header without invoking the extractor.
    fixed = bytes(payload[member.local_header_offset : member.local_header_offset + 30])
    import struct

    values = struct.unpack("<4s5H3I2H", fixed)
    name_size, extra_size = int(values[9]), int(values[10])
    start = member.local_header_offset + 30 + name_size + extra_size
    payload[start] ^= 0x01

    reader = RangeAudit(bytes(payload))
    # Keep the original central-directory inventory so the expected CRC remains frozen.
    with pytest.raises(ZipSafeMemberError, match="CRC mismatch"):
        extract_safe_member(
            inventory,
            member,
            reader,
            maximum_compressed_bytes=100_000,
            maximum_uncompressed_bytes=100_000,
        )
