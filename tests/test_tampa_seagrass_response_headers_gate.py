from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from validation.tampa_seagrass_endpoint3.response_headers_gate import HeaderStop, evaluate, read_physical_header


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/tampa_seagrass_endpoint3/response_headers_contract.json"


def load_contract():
    return json.loads(CONTRACT_PATH.read_text())


class FakeFetcher:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.requests = 0
        self.bytes_opened = 0
        self.offsets = []
        self.closed = False

    def read_byte(self, offset: int) -> bytes:
        self.requests += 1
        self.offsets.append(offset)
        if offset >= len(self.payload):
            raise HeaderStop("synthetic source exhausted before LF")
        self.bytes_opened += 1
        return self.payload[offset : offset + 1]

    def close(self):
        self.closed = True


class Factory:
    def __init__(self, payloads):
        self.payloads = payloads
        self.created = []

    def __call__(self, source, transport):
        name = "occurrence" if source["path"].endswith("occurrence.csv") else "emof"
        fetcher = FakeFetcher(self.payloads[name])
        self.created.append((name, fetcher))
        return fetcher


def physical(source, terminator=b"\n"):
    return source["expected_header_ascii"].encode("ascii") + terminator


def test_contract_header_lengths_are_exact():
    c = load_contract()
    assert len(c["sources"]["occurrence"]["expected_header_ascii"].encode("ascii")) == 181
    assert len(c["sources"]["emof"]["expected_header_ascii"].encode("ascii")) == 124
    assert c["transport"]["range_unit_bytes"] == 1
    assert c["transport"]["response_data_row_bytes_allowed"] == 0


def test_both_headers_lf_success_and_stop_exactly_at_lf():
    c = load_contract()
    factory = Factory({
        "occurrence": physical(c["sources"]["occurrence"]) + b"SHOULD_NOT_OPEN",
        "emof": physical(c["sources"]["emof"]) + b"SHOULD_NOT_OPEN",
    })
    result = evaluate(c, fetcher_factory=factory)
    assert result["status"] == "response_headers_ready"
    assert result["headers"]["occurrence"]["header_bytes_opened"] == 182
    assert result["headers"]["emof"]["header_bytes_opened"] == 125
    assert result["total_header_range_requests"] == 307
    assert result["response_data_row_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    for _, fetcher in factory.created:
        assert fetcher.offsets == list(range(fetcher.bytes_opened))
        assert fetcher.payload[fetcher.bytes_opened - 1 : fetcher.bytes_opened] == b"\n"
        assert fetcher.closed is True


def test_both_headers_crlf_success_at_exact_ceiling():
    c = load_contract()
    factory = Factory({
        "occurrence": physical(c["sources"]["occurrence"], b"\r\n") + b"ROW",
        "emof": physical(c["sources"]["emof"], b"\r\n") + b"ROW",
    })
    result = evaluate(c, fetcher_factory=factory)
    assert result["status"] == "response_headers_ready"
    assert result["headers"]["occurrence"]["header_line_terminator"] == "CRLF"
    assert result["headers"]["emof"]["header_line_terminator"] == "CRLF"
    assert result["total_header_range_requests"] == 309
    assert result["total_header_bytes_opened"] == 309


def test_short_occurrence_mismatch_stops_at_lf_and_never_opens_emof():
    c = load_contract()
    factory = Factory({
        "occurrence": b"occurrenceID,eventID\nPRIVATE_ROW",
        "emof": physical(c["sources"]["emof"]) + b"PRIVATE_ROW",
    })
    result = evaluate(c, fetcher_factory=factory)
    assert result["status"] == "stop_pre_row_response_header_transport_or_schema"
    assert "occurrence header does not exactly match" in result["reason"]
    assert result["headers"]["occurrence"]["header_bytes_opened"] == len(b"occurrenceID,eventID\n")
    assert result["headers"]["emof"]["header_bytes_opened"] == 0
    assert [name for name, _ in factory.created] == ["occurrence"]
    assert result["response_data_row_bytes_opened"] == 0


def test_emof_mismatch_after_occurrence_pass_never_opens_data_row():
    c = load_contract()
    factory = Factory({
        "occurrence": physical(c["sources"]["occurrence"]) + b"OCC_ROW",
        "emof": b"eventID,occurrenceID,measurementType,EXTRA\nEMOF_ROW",
    })
    result = evaluate(c, fetcher_factory=factory)
    assert result["status"] == "stop_pre_row_response_header_transport_or_schema"
    assert "emof header does not exactly match" in result["reason"]
    assert result["headers"]["occurrence"]["header_bytes_opened"] == 182
    assert result["headers"]["emof"]["header_bytes_opened"] == len(b"eventID,occurrenceID,measurementType,EXTRA\n")
    assert result["headers"]["occurrence"]["data_row_bytes_opened"] == 0
    assert result["headers"]["emof"]["data_row_bytes_opened"] == 0


def test_extra_occurrence_column_is_not_accepted():
    c = load_contract()
    bad = copy.deepcopy(c)
    # Keep the prospectively frozen expected contract unchanged; only the synthetic target changes.
    factory = Factory({
        "occurrence": c["sources"]["occurrence"]["expected_header_ascii"].encode() + b",extra\nROW",
        "emof": physical(c["sources"]["emof"]),
    })
    result = evaluate(bad, fetcher_factory=factory)
    assert result["status"] == "stop_pre_row_response_header_transport_or_schema"
    assert result["response_rows_opened"] == 0


def test_no_lf_within_source_ceiling_fails_closed():
    c = load_contract()
    source = c["sources"]["occurrence"]
    fetcher = FakeFetcher(b"x" * source["maximum_requests"])
    with pytest.raises(HeaderStop, match="no LF terminator"):
        read_physical_header(source, c["transport"], fetcher)
    assert fetcher.requests == 183
    assert fetcher.bytes_opened == 183
