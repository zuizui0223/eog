import copy
import json
from pathlib import Path

import pytest

from validation.leipzig_roedeer_endpoint3.response_header_gate import HeaderStop, evaluate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation" / "leipzig_roedeer_endpoint3" / "response_header_contract.json"


class FakeFetcher:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.requests = 0
        self.bytes_opened = 0
        self.offsets = []

    def read_byte(self, offset: int) -> bytes:
        self.requests += 1
        self.offsets.append(offset)
        if offset >= len(self.payload):
            raise HeaderStop("synthetic payload exhausted")
        self.bytes_opened += 1
        return self.payload[offset : offset + 1]


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def expected_header(c):
    return c["reference_header"]["expected_header_ascii"].encode("ascii")


def test_contract_is_bound_to_gate0_and_forbids_multibyte_or_row_reads():
    c = contract()
    assert c["attempt_id"] == "leipzig_roedeer_endpoint3_v1"
    assert c["issue"] == 384
    assert c["gate0"]["recording_merge"] == "159ba574f2a1ca9742bea913c3861059b72cb2a7"
    assert c["gate0"]["result_fingerprint"] == "cd34456362a1f35742f7158adb7acbbab928bf125ddd121db274b174fd51855d"
    assert c["source"]["git_blob_sha1"] == "b4263a634d4bafdfe77ef4bef1fab24d45034cda"
    assert c["transport"]["range_unit_bytes"] == 1
    assert c["transport"]["maximum_requests"] == 388
    assert c["transport"]["multi_byte_range_allowed"] is False
    assert c["transport"]["request_after_first_LF_allowed"] is False
    assert c["transport"]["full_body_fallback_allowed"] is False
    assert c["transport"]["response_data_row_bytes_allowed"] == 0
    assert c["firewall"]["response_rows_allowed"] == 0
    assert c["firewall"]["response_values_allowed"] is False


def test_exact_lf_header_passes_and_stops_before_first_data_byte():
    c = contract()
    header = expected_header(c)
    payload = header + b"\nFIRST_DATA_ROW_MUST_NOT_OPEN"
    f = FakeFetcher(payload)
    result = evaluate(c, f)
    assert result["status"] == "response_header_ready"
    assert result["header_line_terminator"] == "LF"
    assert result["response_header_range_requests"] == len(header) + 1 == 387
    assert result["response_header_bytes_opened"] == 387
    assert result["response_data_row_bytes_opened"] == 0
    assert f.offsets[-1] == len(header)
    assert max(f.offsets) < payload.index(b"F")


def test_exact_crlf_header_passes_without_opening_data_row():
    c = contract()
    header = expected_header(c)
    payload = header + b"\r\nFIRST_DATA_ROW_MUST_NOT_OPEN"
    f = FakeFetcher(payload)
    result = evaluate(c, f)
    assert result["status"] == "response_header_ready"
    assert result["header_line_terminator"] == "CRLF"
    assert result["response_header_range_requests"] == len(header) + 2 == 388
    assert result["response_header_bytes_opened"] == 388
    assert result["response_data_row_bytes_opened"] == 0
    assert f.offsets[-1] == len(header) + 1


def test_short_mismatched_header_stops_at_its_lf_without_touching_row():
    c = contract()
    payload = b"wrong,header\nSECRET_RESPONSE_ROW"
    f = FakeFetcher(payload)
    with pytest.raises(HeaderStop, match="does not exactly match"):
        evaluate(c, f)
    newline = payload.index(b"\n")
    assert f.requests == newline + 1
    assert f.bytes_opened == newline + 1
    assert f.offsets[-1] == newline
    assert all(offset <= newline for offset in f.offsets)


def test_alias_or_extra_column_is_not_repaired():
    c = contract()
    mutated = copy.deepcopy(c)
    header = expected_header(c).replace(b"scientificName", b"scientific_name")
    f = FakeFetcher(header + b"\n")
    with pytest.raises(HeaderStop, match="does not exactly match"):
        evaluate(mutated, f)


def test_header_longer_than_ceiling_stops_before_any_data_row_exists():
    c = contract()
    payload = b"x" * c["transport"]["maximum_requests"]
    f = FakeFetcher(payload)
    with pytest.raises(HeaderStop, match="no LF terminator"):
        evaluate(c, f)
    assert f.requests == 388
    assert f.bytes_opened == 388
