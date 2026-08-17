from pathlib import Path

import pytest

from eog.v2.response_firewall import (
    read_bounded_first_record_bytes,
    read_bounded_first_record_text,
)


def _write(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    return path


def test_lf_only_file_stops_before_second_record(tmp_path):
    path = _write(tmp_path / "lf.csv", b"a,b,c\nSECRET_RESPONSE_ROW\n")

    record = read_bounded_first_record_bytes(path)

    assert record.data == b"a,b,c"
    assert record.terminator == "LF"
    assert record.bytes_consumed == 6
    assert b"SECRET" not in record.data


def test_cr_only_file_stops_before_second_record(tmp_path):
    # Regression for the Peck Ranch Gate 0 contamination: binary readline() would
    # consume this entire file because it has CR separators but no LF bytes.
    path = _write(tmp_path / "cr.txt", b"header1\theader2\rSECRET_RESPONSE_ROW\r")

    text, record = read_bounded_first_record_text(path)

    assert text == "header1\theader2"
    assert record.terminator == "CR"
    assert b"SECRET" not in record.data
    assert record.bytes_consumed == len(b"header1\theader2") + 1


def test_crlf_file_stops_on_cr_without_reading_lf_or_second_record(tmp_path):
    path = _write(tmp_path / "crlf.csv", b"site,year,response\r\nSECRET_RESPONSE_ROW\r\n")

    record = read_bounded_first_record_bytes(path)

    assert record.data == b"site,year,response"
    assert record.terminator == "CR"
    assert record.bytes_consumed == len(b"site,year,response") + 1
    assert b"SECRET" not in record.data


def test_utf8_bom_is_decoded_without_exposing_second_record(tmp_path):
    path = _write(tmp_path / "bom.csv", b"\xef\xbb\xbfsite,year\nSECRET\n")

    text, record = read_bounded_first_record_text(path)

    assert text == "site,year"
    assert record.terminator == "LF"


def test_eof_without_physical_terminator_is_rejected(tmp_path):
    path = _write(tmp_path / "unterminated.txt", b"header_without_terminator")

    with pytest.raises(ValueError, match="terminator not found before EOF"):
        read_bounded_first_record_bytes(path)


def test_record_longer_than_declared_bound_is_rejected_before_reading_farther(tmp_path):
    path = _write(tmp_path / "long.txt", b"1234567890\rSECRET")

    with pytest.raises(ValueError, match="exceeds max_record_bytes=5"):
        read_bounded_first_record_bytes(path, max_record_bytes=5)


def test_invalid_record_bound_is_rejected(tmp_path):
    path = _write(tmp_path / "x.txt", b"x\n")

    for value in (0, -1, True):
        with pytest.raises(ValueError, match="positive integer"):
            read_bounded_first_record_bytes(path, max_record_bytes=value)
