"""Fabricated bytes only; no real source file or unauthorized REST use."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/audit_helgeland_2020_v8_public_ui_stream_v1.py"


def load():
    spec=importlib.util.spec_from_file_location("eog_2020_v8_public_ui", SCRIPT)
    m=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=m
    spec.loader.exec_module(m)
    return m


def synthetic(tmp_path, monkeypatch):
    import audit_helgeland_2020_v8_local_bytes_v1 as offline
    m=load()
    inventory=json.loads(m.FROZEN.read_text(encoding="utf-8"))
    entries={x["name"]:x for x in inventory["archives"]["niskanen_2020"]["critical_files"]}
    rows={}
    pins={}
    for name,(identifier,_size,_digest) in m.PINS.items():
        fake=(b"Island,Year,Abundance\n" if name.endswith(".csv")
              else b"README for a fictional dataset\n") + b"ARTIFICIAL_DATA_NOT_FOR_ANALYSIS\n"
        sha=hashlib.sha256(fake).hexdigest()
        pins[name]=(identifier,len(fake),sha)
        entries[name]["size_bytes"]=len(fake)
        entries[name]["source_digest"]=sha
        rows[identifier]=fake
    monkeypatch.setattr(m,"PINS",pins)
    monkeypatch.setattr(offline,"PINS",pins)
    return m,inventory,rows


def test_public_browser_route_exact_three_files_and_no_bird_row_output(tmp_path,monkeypatch):
    m,frozen,rows=synthetic(tmp_path,monkeypatch)
    seen=[]
    def fetch(file_id,size,path):
        seen.append((file_id,size))
        assert len(rows[file_id])==size
        path.write_bytes(rows[file_id])
    result,receipt=m.check(frozen,fetch)
    assert len(seen)==3
    assert result["acquisition"]["route"]=="PUBLIC_DATASET_WEB_UI_FILE_STREAM__NOT_REST_API"
    assert result["acquisition"]["source_bytes_retained_after_job"] is False
    assert len(result["records"])==3
    assert all(x["independent_sha256_matches_2020_v8"] is True for x in result["records"])
    assert receipt["actual_public_web_ui_source_bytes_independently_verified"] is True
    assert receipt["ecological_forecast_authorized"] is False
    assert "ARTIFICIAL_DATA" not in json.dumps([result,receipt])


def test_bytes_changed_while_same_size_must_stop(tmp_path,monkeypatch):
    m,frozen,rows=synthetic(tmp_path,monkeypatch)
    first=next(iter(rows))
    original=rows[first]
    rows[first]=original.replace(b"ARTIFICIAL",b"artificial")
    assert len(rows[first])==len(original)
    def fetch(file_id,size,path):
        path.write_bytes(rows[file_id])
    with pytest.raises(ValueError,match="SHA256"):
        m.check(frozen,fetch)


def test_wrong_file_id_and_mismatch_rejected_before_http(tmp_path,monkeypatch):
    m,frozen,rows=synthetic(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match="precisely pinned"):
        m.public_stream(999999,10,tmp_path/"bad.csv")
    ident=next(iter(rows))
    with pytest.raises(ValueError,match="precisely pinned"):
        m.public_stream(ident,999999,tmp_path/"bad.csv")


def test_public_url_route_cannot_fall_back_to_current_v10():
    script=SCRIPT.read_text(encoding="utf-8")
    assert 'WEB_UI_BASE = "https://datadryad.org/downloads/file_stream/"' in script
    assert "/api/v2/files/" not in script.split('"""', 2)[-1]
    assert "v10" not in script.replace('"""', '')
    assert "urllib.request.urlopen" in script
    assert 'tempfile.TemporaryDirectory' in script
    assert "ecological_forecast_authorized" in script
    assert "read_csv(" not in script
