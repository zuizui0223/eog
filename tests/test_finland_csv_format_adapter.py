from __future__ import annotations

import csv
from pathlib import Path

import pytest

from benchmarks.finland_csv_format_adapter import (
    detect_csv_format,
    fixed_dict_reader_delimiter,
)


FIELDS = [
    "outcome",
    "spp.name",
    "holmkod",
    "Historical_total_log",
    "Dist_to_historical_log",
    "x",
]


def _write(path: Path, delimiter: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(FIELDS)
        writer.writerow([1, "Species alpha", "I1", 2.3, 4.5, "a,b;c"])


@pytest.mark.parametrize("delimiter", [",", ";", "\t", "|"])
def test_detect_csv_format_from_header_only(tmp_path: Path, delimiter: str) -> None:
    path = tmp_path / "colonization_select.csv"
    _write(path, delimiter)
    result = detect_csv_format(path)
    assert result["delimiter"] == delimiter
    assert result["field_names"] == FIELDS
    assert result["outcome_column_exists"] is True
    assert result["outcome_values_accessed"] is False
    assert len(result["fingerprint"]) == 64


def test_fixed_dict_reader_uses_detected_delimiter_and_restores_stdlib(tmp_path: Path) -> None:
    path = tmp_path / "colonization_select.csv"
    _write(path, ";")
    original = csv.DictReader
    with fixed_dict_reader_delimiter(";"):
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows[0]["spp.name"] == "Species alpha"
        assert rows[0]["outcome"] == "1"
    assert csv.DictReader is original


def test_missing_required_header_is_rejected_without_reading_rows(tmp_path: Path) -> None:
    path = tmp_path / "broken.csv"
    path.write_text("outcome;spp.name;holmkod\nTHIS;ROW;MUST_NOT_MATTER\n", encoding="utf-8")
    with pytest.raises(ValueError, match="lacks required fields"):
        detect_csv_format(path)
