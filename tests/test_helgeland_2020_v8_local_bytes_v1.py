"""Synthetic-only tests for the offline 2020 v8 file gate; no original bird data."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/audit_helgeland_2020_v8_local_bytes_v1.py"


def mod():
    spec = importlib.util.spec_from_file_location("eog_helgeland_2020_offline", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sources(tmp_path, monkeypatch):
    m = mod()
    frozen = copy.deepcopy(json.loads(
        (BASE / "helgeland_historical_public_vintages_frozen_v1.json").read_text()))
    raw_dir = tmp_path / "external-raw"
    raw_dir.mkdir()
    pins = {}
    for i, (name, prior) in enumerate(m.PINS.items()):
        first = (b"Year,Island,N\n" if name.endswith(".csv")
                 else b"Public synthetic README content\n")
        raw = first + f"synthetic never export record {i}\n".encode()
        p = raw_dir / name
        p.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        pins[name] = (prior[0], len(raw), digest)
        matching = next(x for x in frozen["archives"]["niskanen_2020"]["critical_files"]
                        if x["name"] == name)
        matching["size_bytes"] = len(raw)
        matching["source_digest"] = digest
    monkeypatch.setattr(m, "PINS", pins)
    return m, frozen, raw_dir


def test_exact_three_synthetic_byte_matches_only_shape(tmp_path, monkeypatch):
    m, frozen, root = sources(tmp_path, monkeypatch)
    evidence, receipt = m.audit(root, frozen)
    assert receipt["status"] == "THREE_LOCALLY_PROVIDED_V8_FILES_HASH_MATCH__ECOLOGY_HOLD"
    assert len(evidence["records"]) == 3
    assert {r["file_name"] for r in evidence["records"]} == set(m.PINS)
    assert all(r["independent_sha256_matches_2020_v8"] for r in evidence["records"])
    assert all(r["biological_rows_parsed"] is False for r in evidence["records"])
    assert all(r["firstline_values_emitted"] is False for r in evidence["records"])
    assert all(r["semantic_header_confirmed"] is False for r in evidence["records"])
    assert all(r["other_lines_decoded"] is False for r in evidence["records"])
    assert receipt["ecological_forecast_authorized"] is False
    assert "synthetic never export" not in json.dumps([evidence, receipt])


def test_same_size_byte_tampering_refused(tmp_path, monkeypatch):
    m, frozen, root = sources(tmp_path, monkeypatch)
    path = root / "Pop_size_1997_2012.csv"
    old = path.read_bytes()
    path.write_bytes(old.replace(b"synthetic", b"SYNTHETIC"))
    assert path.stat().st_size == len(old)
    with pytest.raises(ValueError, match="SHA256"):
        m.audit(root, frozen)


def test_metadata_version_and_digest_tamper_refused(tmp_path, monkeypatch):
    m, frozen, root = sources(tmp_path, monkeypatch)
    frozen["archives"]["niskanen_2020"]["version_id"] = 208617
    with pytest.raises(ValueError, match="historic"):
        m.audit(root, frozen)
    frozen["archives"]["niskanen_2020"]["version_id"] = 78498
    frozen["archives"]["niskanen_2020"]["critical_files"][0]["source_digest"] = "0" * 64
    with pytest.raises(ValueError, match="metadata"):
        m.audit(root, frozen)


def test_missing_and_symlinked_file_refused(tmp_path, monkeypatch):
    m, frozen, root = sources(tmp_path, monkeypatch)
    path = root / "Pop_size_1998_2013.csv"
    path.unlink()
    with pytest.raises(ValueError, match="not a regular file"):
        m.audit(root, frozen)
    target = tmp_path / "outside"
    target.write_bytes(b"Year,Island,N\n")
    path.symlink_to(target)
    with pytest.raises(ValueError, match="Symlinked"):
        m.audit(root, frozen)


@pytest.mark.parametrize("first", [
    b"Year,Island,N", b"Year,Island,N\x00\n",
    b"Year,Island,N\xff\n", b"Year,Island,N\n" + b"Q"*4096,
])
def test_untrusted_header_fails_closed(tmp_path, first):
    m = mod()
    path = tmp_path / "source.csv"
    # The long-row fixture must put its oversized data on physical line 1.
    if first.startswith(b"Year,Island,N\n"):
        first = b"Year," + b"X" * 4096 + b"\n"
    path.write_bytes(first)
    with pytest.raises((ValueError, UnicodeDecodeError)):
        m.firstline_shape(path, "source.csv")


def test_bounded_firstline_delimiter_and_nonheader_readme(tmp_path):
    m = mod()
    a = tmp_path / "source.csv"
    a.write_bytes(b'"Year";"Island";"N"\nPRIVATE ROW MUST NEVER APPEAR\n')
    shape = m.firstline_shape(a, "source.csv")
    assert shape["delimiter"] == "SEMICOLON"
    assert shape["firstline_field_count"] == 3
    assert shape["semantic_header_confirmed"] is False
    assert "PRIVATE" not in json.dumps(shape)
    b = tmp_path / "Dryad_readme.txt"
    b.write_bytes(b"Some note\nPRIVATE\n")
    shape = m.firstline_shape(b, "Dryad_readme.txt")
    assert shape["delimiter"] == "UNCLASSIFIED_TEXT"
    assert shape["firstline_values_emitted"] is False


def test_no_network_and_no_bird_row_analysis():
    script = SCRIPT.read_text(encoding="utf-8")
    for banned in ("urllib", "requests", "urlopen(", "read_csv(", "import pandas",
                   "import numpy", "import sklearn", "socket.", "readlines("):
        assert banned not in script
    assert "prepare_write_paths(" in script
    assert "source_file(root, name)" in script
    assert "ecological_forecast_authorized" in script
