import json
from pathlib import Path

import pytest

from validation.bam_round_goby_external_bridge_v1.gate1_schema import (
    Gate1Stop,
    parse_header,
    read_header,
)


class FakeByteFetcher:
    def __init__(self, payload: bytes, name: str = "x.csv"):
        self.payload = payload
        self.file_name = name
        self.requests = 0
        self.bytes_opened = 0

    def read_byte(self, offset: int) -> bytes:
        self.requests += 1
        if offset >= len(self.payload):
            raise Gate1Stop("fixture EOF")
        self.bytes_opened += 1
        return self.payload[offset : offset + 1]


def test_header_firewall_stops_at_first_lf_and_opens_zero_data_bytes():
    payload = b"year,site,value\n2019,A,7\n"
    fetcher = FakeByteFetcher(payload)
    text, terminator = read_header(fetcher)
    assert text == "year,site,value"
    assert terminator == "LF"
    assert fetcher.bytes_opened == len(b"year,site,value\n")
    assert fetcher.bytes_opened < len(payload)
    assert parse_header(text, "x.csv") == ["year", "site", "value"]


def test_header_firewall_supports_crlf():
    fetcher = FakeByteFetcher(b"a,b\r\n1,2\r\n")
    text, terminator = read_header(fetcher)
    assert text == "a,b"
    assert terminator == "CRLF"


def test_header_parser_fails_on_duplicate_columns():
    with pytest.raises(Gate1Stop, match="duplicate"):
        parse_header("a,b,a", "x.csv")
