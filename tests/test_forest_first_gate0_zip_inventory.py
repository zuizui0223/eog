from __future__ import annotations

import io
import json
import struct
import zipfile
from pathlib import Path

import pytest

from validation.forest_first_endpoint3.gate0_zip_inventory import (
    Gate0Stop,
    StrictIptRangeTransport,
    inspect_zip_inventory,
    select_required_members,
)


REQUIRED = ["datapackage.json", "deployments.csv", "observations.csv", "media.csv"]


def make_zip(*, names: list[str] | None = None, comment: bytes = b"") -> bytes:
    buffer = io.BytesIO()
    selected = names or REQUIRED
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for index, name in enumerate(selected):
            zf.writestr(name, f"payload-{index}\n")
        zf.comment = comment
    return buffer.getvalue()


def reader_for(data: bytes, calls: list[tuple[int, int, str]]):
    def read_range(start: int, end: int, role: str) -> bytes:
        calls.append((start, end, role))
        return data[start : end + 1]

    return read_range


def mutate_eocd(data: bytes, offset: int, raw: bytes) -> bytes:
    value = bytearray(data)
    start = len(value) - 22 + offset
    value[start : start + len(raw)] = raw
    return bytes(value)


def central_offset(data: bytes) -> int:
    return int(struct.unpack_from("<I", data, len(data) - 22 + 16)[0])


def test_classic_inventory_reads_only_eocd_and_central_directory():
    data = make_zip()
    calls: list[tuple[int, int, str]] = []
    result = inspect_zip_inventory(
        len(data), reader_for(data, calls), maximum_central_directory_bytes=524288
    )
    selected = select_required_members(result, REQUIRED)

    assert result["zip_comment_size"] == 0
    assert result["member_count"] == 4
    assert set(selected) == set(REQUIRED)
    assert result["local_header_bytes_opened"] == 0
    assert result["member_payload_bytes_opened"] == 0
    assert len(calls) == 2
    assert calls[0] == (len(data) - 22, len(data) - 1, "zip_eocd_zero_comment")
    assert calls[1][0] == result["central_directory_offset"]
    assert calls[1][1] == result["eocd_offset"] - 1
    assert all(call[0] >= result["central_directory_offset"] for call in calls)


def test_required_members_are_selected_by_unique_basename_only():
    data = make_zip(names=[f"package/{name}" for name in REQUIRED])
    result = inspect_zip_inventory(
        len(data), reader_for(data, []), maximum_central_directory_bytes=524288
    )
    selected = select_required_members(result, REQUIRED)
    assert selected["observations.csv"]["name"] == "package/observations.csv"
    assert selected["deployments.csv"]["basename"] == "deployments.csv"


def test_missing_required_member_stops():
    data = make_zip(names=["datapackage.json", "deployments.csv", "media.csv"])
    result = inspect_zip_inventory(
        len(data), reader_for(data, []), maximum_central_directory_bytes=524288
    )
    with pytest.raises(Gate0Stop, match="observations.csv"):
        select_required_members(result, REQUIRED)


def test_duplicate_member_names_stop():
    data = make_zip(names=[*REQUIRED, "observations.csv"])
    with pytest.raises(Gate0Stop, match="duplicate member names"):
        inspect_zip_inventory(
            len(data), reader_for(data, []), maximum_central_directory_bytes=524288
        )


def test_zip_comment_stops_without_backwards_scan():
    data = make_zip(comment=b"comment")
    calls: list[tuple[int, int, str]] = []
    with pytest.raises(Gate0Stop, match="zero-comment"):
        inspect_zip_inventory(
            len(data), reader_for(data, calls), maximum_central_directory_bytes=524288
        )
    assert len(calls) == 1
    assert calls[0][2] == "zip_eocd_zero_comment"


def test_zip64_sentinel_stops():
    data = make_zip()
    # EOCD fields entries-on-disk and total-entries are offsets 8 and 10.
    data = mutate_eocd(data, 8, b"\xff\xff\xff\xff")
    with pytest.raises(Gate0Stop, match="ZIP64"):
        inspect_zip_inventory(
            len(data), reader_for(data, []), maximum_central_directory_bytes=524288
        )


def test_multidisk_stops():
    data = mutate_eocd(make_zip(), 4, b"\x01\x00")
    with pytest.raises(Gate0Stop, match="multi-disk"):
        inspect_zip_inventory(
            len(data), reader_for(data, []), maximum_central_directory_bytes=524288
        )


def test_encrypted_member_flag_stops():
    data = bytearray(make_zip())
    offset = central_offset(data)
    flags = int(struct.unpack_from("<H", data, offset + 8)[0]) | 0x1
    struct.pack_into("<H", data, offset + 8, flags)
    with pytest.raises(Gate0Stop, match="encrypted"):
        inspect_zip_inventory(
            len(data), reader_for(bytes(data), []), maximum_central_directory_bytes=524288
        )


def test_unsafe_member_path_stops():
    data = make_zip(names=["../datapackage.json", "deployments.csv", "observations.csv", "media.csv"])
    with pytest.raises(Gate0Stop, match="unsafe ZIP member"):
        inspect_zip_inventory(
            len(data), reader_for(data, []), maximum_central_directory_bytes=524288
        )


class FakeResponse:
    def __init__(self, *, status: int, headers: dict[str, str], url: str, body: bytes, forbid_read=False):
        self.status = status
        self.headers = headers
        self._url = url
        self._body = body
        self._forbid_read = forbid_read
        self.read_calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, amount=-1):
        self.read_calls += 1
        if self._forbid_read:
            raise AssertionError("body must not be read")
        return self._body if amount < 0 else self._body[:amount]


class FakeOpener:
    def __init__(self, responses: list[FakeResponse]):
        self.responses = responses
        self.requests = []

    def open(self, request, timeout=90):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def test_http_200_size_probe_fails_closed_without_body_read():
    url = "https://ipt.biodiversidad.co/sib/archive.do?r=x&v=3"
    response = FakeResponse(status=200, headers={}, url=url, body=b"forbidden", forbid_read=True)
    transport = StrictIptRangeTransport(
        url, ("ipt.biodiversidad.co",), 2_000_000, opener=FakeOpener([response])
    )
    with pytest.raises(Gate0Stop, match="HTTP 200; body was not opened"):
        transport.probe_size()
    assert response.read_calls == 0
    assert transport.range_ledger[0]["bytes_opened"] == 0


def test_exact_206_size_probe_opens_one_byte_and_freezes_size():
    url = "https://ipt.biodiversidad.co/sib/archive.do?r=x&v=3"
    response = FakeResponse(
        status=206,
        headers={"Content-Range": "bytes 0-0/513000", "Content-Encoding": "identity"},
        url=url,
        body=b"P",
    )
    opener = FakeOpener([response])
    transport = StrictIptRangeTransport(
        url, ("ipt.biodiversidad.co",), 2_000_000, opener=opener
    )
    assert transport.probe_size() == 513000
    assert response.read_calls == 1
    assert transport.range_ledger[0]["bytes_opened"] == 1
    assert opener.requests[0].get_header("Range") == "bytes=0-0"


def test_source_contract_keeps_response_locked():
    contract = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "validation"
            / "forest_first_endpoint3"
            / "source_contract.json"
        ).read_text(encoding="utf-8")
    )
    assert contract["issue"] == 381
    assert contract["selection_boundary"]["fresh_predictive_endpoints_with_scores"] == 2
    assert contract["selection_boundary"]["selected_after_scientific_stops"] == 29
    assert contract["gate0"]["size_probe_range"] == "bytes=0-0"
    assert contract["gate0"]["local_header_reads_allowed"] is False
    assert contract["gate0"]["member_payload_reads_allowed"] is False
    assert contract["gate0"]["observations_header_bytes_allowed"] == 0
    assert contract["gate0"]["observations_values_allowed"] is False
