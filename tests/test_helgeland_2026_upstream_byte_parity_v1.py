"""Synthetic-only byte parity tests; no original bird or abundance rows."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_helgeland_2026_upstream_byte_parity_v1.py"


def mod():
    spec=importlib.util.spec_from_file_location("helgeland_upstream_bytes", SCRIPT)
    assert spec and spec.loader
    result=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def fixtures(tmp_path):
    m=mod()
    frozen=json.loads(m.FROZEN.read_text(encoding="utf-8"))
    data=copy.deepcopy(frozen)
    upstream=tmp_path/"checkout"
    catalog={x["name"]:x for x in data["files"]}
    for i,(rel,dryad) in enumerate(m.TARGETS.items()):
        path=upstream/rel
        path.parent.mkdir(parents=True,exist_ok=True)
        body=("ID;Year;Location\n"+"synthetic_record_"+str(i)+"\n").encode("utf-8")
        path.write_bytes(body)
        catalog[dryad]["size_bytes"]=len(body)
        catalog[dryad]["source_declared_sha256"]=hashlib.sha256(body).hexdigest()
    return upstream,data


def test_two_opaque_byte_matches_do_not_certify_biological_interpretation(tmp_path):
    root,frozen=fixtures(tmp_path)
    x=mod().audit(root,frozen)
    assert x["status"]=="MATCHES_TWO_FROZEN_DRYAD_V6_FILES"
    assert len(x["files"])==2
    assert x["upstream_commit"]=="a4e1c9ebc1148d7c7aca2bb5730b9d7104094fe5"
    for f in x["files"]:
        assert f["whole_upstream_file_bytes_read_opaquely_for_hash"] is True
        assert f["physical_headers_decoded"] is False
        assert f["biological_rows_decoded_or_scored"] is False
    assert x["ecological_endpoint_authorized"] is False
    assert x["surveyed_zero_panel_verified"] is False
    assert x["as_of_t_processing_verified"] is False
    assert "synthetic_record" not in json.dumps(x)


def test_same_size_response_byte_change_fails_hash_gate(tmp_path):
    root,frozen=fixtures(tmp_path)
    f=root/"Data/presence_data_1994_2022.txt"
    raw=f.read_bytes()
    f.write_bytes(raw.replace(b"synthetic_record_0",b"SYNTHETIC_RECORD_0"))
    assert len(raw)==f.stat().st_size
    out=mod().audit(root,frozen)
    assert out["status"]=="HOLD_UPSTREAM_DRYAD_BYTE_MISMATCH"
    assert out["files"][0]["biological_rows_decoded_or_scored"] is False


def test_source_file_size_mismatch_is_hold(tmp_path):
    root,frozen=fixtures(tmp_path)
    f=root/"Data/presence_data_1994_2022.txt"
    with f.open("ab") as stream: stream.write(b"extra")
    assert mod().audit(root,frozen)["status"]=="HOLD_UPSTREAM_DRYAD_BYTE_MISMATCH"


def test_reject_symlinked_upstream_source(tmp_path):
    root,frozen=fixtures(tmp_path)
    path=root/"Data/presence_data_1994_2022.txt"
    target=tmp_path/"outside.txt"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(ValueError,match="symlink"):
        mod().audit(root,frozen)


def test_dryad_version_change_refused(tmp_path):
    root,frozen=fixtures(tmp_path)
    frozen["dryad_version_id"]=0
    with pytest.raises(ValueError,match="Unfrozen Dryad"):
        mod().audit(root,frozen)


def test_script_does_not_open_biological_table_for_analysis():
    source=SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("read_csv(", "import pandas", "import numpy", "import requests",
                      "urlopen(", "from Bio", "socket."):
        assert forbidden not in source
    assert "sha256_opaque_bytes(source)" in source
    assert "ecological_endpoint_authorized" in source
