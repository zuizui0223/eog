from __future__ import annotations

import csv
from pathlib import Path

import pytest

from benchmarks.finland_csv_format_adapter import detect_csv_format, fixed_dict_reader_delimiter


FIELDS = [
    "outcome",
    "spp.name",
    "holmkod",
    "Historical_total_log",
    "Dist_to_historical_log",
    "Limestone",
    "x",
]


def _write(path: Path, delimiter: str, *, limestone="Yes", historical=2.3) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(FIELDS)
        writer.writerow([1, "Species alpha", "I1", historical, 4.5, limestone, "a,b;c"])


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_detect_csv_format_from_header_only(tmp_path: Path, delimiter: str) -> None:
    path = tmp_path / "colonization_select.csv"
    _write(path, delimiter)
    result = detect_csv_format(path)
    assert result["delimiter"] == delimiter
    assert result["field_names"] == FIELDS
    assert result["binary_recoding"] == {"Limestone": {"yes": "1", "no": "0"}}
    assert result["outcome_column_exists"] is True
    assert result["outcome_values_accessed"] is False
    assert len(result["fingerprint"]) == 64


@pytest.mark.parametrize(("token", "expected"), [("Yes", "1"), ("yes", "1"), ("No", "0"), ("no", "0"), ("1", "1"), ("0", "0")])
def test_fixed_reader_normalizes_only_documented_limestone_binary(tmp_path: Path, token: str, expected: str) -> None:
    path = tmp_path / "colonization_select.csv"
    _write(path, ";", limestone=token)
    original = csv.DictReader
    with fixed_dict_reader_delimiter(";"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["Limestone"] == expected
        assert rows[0]["Historical_total_log"] == "2.3"
        assert rows[0]["outcome"] == "1"
    assert csv.DictReader is original


def test_nonbinary_field_is_not_coerced(tmp_path: Path) -> None:
    path = tmp_path / "colonization_select.csv"
    _write(path, ";", historical="Yes")
    with fixed_dict_reader_delimiter(";"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            row = next(csv.DictReader(handle))
    assert row["Historical_total_log"] == "Yes"


def test_missing_required_header_is_rejected_without_reading_rows(tmp_path: Path) -> None:
    path = tmp_path / "broken.csv"
    path.write_text("outcome;spp.name;holmkod\nTHIS;ROW;MUST_NOT_MATTER\n", encoding="utf-8")
    with pytest.raises(ValueError, match="lacks required fields"):
        detect_csv_format(path)
