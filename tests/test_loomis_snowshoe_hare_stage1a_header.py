from __future__ import annotations

import pytest

from validation.loomis_snowshoe_hare_endpoint3.gate1a_header import (
    HeaderGateStop,
    read_first_physical_record,
    summarize_stage1a,
)


def reader_from_bytes(data: bytes):
    calls: list[int] = []

    def read_byte(offset: int, role: str) -> bytes:
        calls.append(offset)
        if offset >= len(data):
            return b""
        return data[offset : offset + 1]

    return read_byte, calls


def test_reads_only_first_lf_record():
    reader, calls = reader_from_bytes(b"a,b,c\n1,2,3\n")
    result = read_first_physical_record("x.csv", reader)
    assert result.raw_header_text == "a,b,c"
    assert result.terminator == "LF"
    assert result.columns == ("a", "b", "c")
    assert result.bytes_consumed == 6
    assert max(calls) == 5


def test_reads_only_first_cr_record():
    reader, calls = reader_from_bytes(b"a,b\r1,2\r")
    result = read_first_physical_record("x.csv", reader)
    assert result.terminator == "CR"
    assert result.columns == ("a", "b")
    assert max(calls) == 3


def test_quoted_header_is_parsed():
    reader, _ = reader_from_bytes(b'"camera,id",lat,lon\n1,2,3\n')
    result = read_first_physical_record("x.csv", reader)
    assert result.columns == ("camera,id", "lat", "lon")


def test_empty_column_stops():
    reader, _ = reader_from_bytes(b"a,,c\n1,2,3\n")
    with pytest.raises(HeaderGateStop, match="empty column"):
        read_first_physical_record("x.csv", reader)


def test_duplicate_column_stops():
    reader, _ = reader_from_bytes(b"a,b,a\n1,2,3\n")
    with pytest.raises(HeaderGateStop, match="duplicate"):
        read_first_physical_record("x.csv", reader)


def test_no_terminator_stops_without_reading_data_semantics():
    reader, _ = reader_from_bytes(b"a,b,c")
    with pytest.raises(HeaderGateStop):
        read_first_physical_record("x.csv", reader, maximum_header_bytes=5)


def test_overlong_header_stops():
    reader, calls = reader_from_bytes(b"abcdef\n1\n")
    with pytest.raises(HeaderGateStop, match="exceeded"):
        read_first_physical_record("x.csv", reader, maximum_header_bytes=4)
    assert calls == [0, 1, 2, 3]


def test_short_read_stops():
    def reader(offset: int, role: str) -> bytes:
        return b"ab"

    with pytest.raises(HeaderGateStop, match="returned 2 bytes"):
        read_first_physical_record("x.csv", reader)


def test_summary_retains_only_header_evidence_and_zero_response_counters():
    a, _ = reader_from_bytes(b"site,camera,lat,lon,start,end\n1,x,0,0,a,b\n")
    b, _ = reader_from_bytes(b"camera,model\rfoo,bar\r")
    headers = [
        read_first_physical_record("deployment_2022.csv", a),
        read_first_physical_record("camera_info_new.csv", b),
    ]
    out = summarize_stage1a(headers)
    assert out["status"] == "stage1a_headers_ready"
    assert out["counts_as_predictive_evidence"] is False
    assert out["deployment_rows_opened"] == 0
    assert out["detection_header_bytes_opened"] == 0
    assert out["response_rows_opened"] == 0
    assert out["response_values_opened"] is False
    assert out["model_fits"] == 0
    assert out["heldout_scores"] == 0
    assert [f["key"] for f in out["files"]] == [
        "camera_info_new.csv",
        "deployment_2022.csv",
    ]
