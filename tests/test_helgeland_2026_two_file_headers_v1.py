"""Synthetic fixtures only: prove bounded first-line attestation and hard biological HOLD."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_helgeland_2026_two_file_headers_v1 import (
    REQUIRED, attest, read_first_physical_header
)
from audit_helgeland_2026_upstream_byte_parity_v1 import FROZEN, TARGETS


def fixture(tmp_path):
    frozen = copy.deepcopy(json.loads(FROZEN.read_text(encoding="utf-8")))
    by_name = {x["name"]: x for x in frozen["files"]}
    root = tmp_path / "upstream"
    for i, (upstream, dryad) in enumerate(TARGETS.items()):
        path = root / upstream
        path.parent.mkdir(parents=True, exist_ok=True)
        fields = sorted(REQUIRED[upstream])
        header = ";".join(f'"{x}"' for x in fields) + "\n"
        data = header.encode("utf-8") + f"private_synthetic_observation_{i}\n".encode()
        path.write_bytes(data)
        by_name[dryad]["size_bytes"] = len(data)
        by_name[dryad]["source_declared_sha256"] = hashlib.sha256(data).hexdigest()
    return root, frozen


def test_two_first_line_headers_only_after_verified_byte_parity(tmp_path):
    root, frozen = fixture(tmp_path)
    result = attest(root, frozen)
    assert result["status"] == "TWO_DRYAD_V6_PHYSICAL_HEADERS_ATTESTED__ECOLOGY_HOLD"
    assert len(result["headers"]) == 2
    assert result["only_first_physical_lines_decoded"] is True
    assert result["biological_data_rows_decoded"] is False
    for header in result["headers"]:
        assert set(REQUIRED[header["github_path"]]).issubset(header["actual_first_line_column_names"])
        assert header["source_whole_byte_sha256_matches_dryad_v6"] is True
        assert header["biological_data_rows_decoded"] is False
    assert "private_synthetic_observation" not in json.dumps(result)
    for flag in ("island_year_surveyed_zero_panel_verified",
                 "same_id_first_recruit_movement_verified",
                 "observation_available_as_of_t_verified",
                 "heldout_benchmark_qualified",
                 "ecological_endpoint_authorized"):
        assert result[flag] is False


def test_tamper_with_equal_size_row_refuses_header_attestation(tmp_path):
    root, frozen = fixture(tmp_path)
    path = root / "Data/presence_data_1994_2022.txt"
    before = path.read_bytes()
    after = before.replace(b"private_synthetic_observation_0",
                           b"PRIVATE_SYNTHETIC_OBSERVATION_0")
    assert len(before) == len(after)
    path.write_bytes(after)
    with pytest.raises(ValueError, match="byte parity"):
        attest(root, frozen)


@pytest.mark.parametrize("firstline", [
    b'ID;Year;ID\n',
    b'ID;Year;bad token\n',
    b'ID;Year;Island',
    b'ID;Year;Island\x00\n',
    b'ID;Year;' + b'x' * 4096 + b'\n',
    b'ID;Year;Island\xff\n',
])
def test_invalid_firstline_fails_closed(tmp_path, firstline):
    p = tmp_path / "sample.txt"
    p.write_bytes(firstline + b"synthetic_second_row\n")
    with pytest.raises((ValueError, UnicodeDecodeError)):
        read_first_physical_header(p)


def test_missing_required_field_does_not_auto_normalize(tmp_path):
    root, frozen = fixture(tmp_path)
    path = root / "Data/presence_data_1994_2022.txt"
    raw = path.read_bytes().replace(b'"Location"', b'"Locality"')
    path.write_bytes(raw)
    meta = next(x for x in frozen["files"] if x["name"] == TARGETS["Data/presence_data_1994_2022.txt"])
    meta["size_bytes"] = len(raw)
    meta["source_declared_sha256"] = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="required predeclared schema"):
        attest(root, frozen)


def test_only_two_git_files_and_no_download_or_outcome_parser():
    text = (ROOT / "scripts/audit_helgeland_2026_two_file_headers_v1.py").read_text()
    assert len(TARGETS) == 2
    for forbidden in ("read_csv(", "import pandas", "import numpy", "urllib", "requests",
                      "socket.", "/download", "readlines(", "read_text()"):
        assert forbidden not in text
    assert "stream.readline(HEADER_BYTES_LIMIT + 1)" in text
    assert "verify_bytes(root, frozen)" in text
