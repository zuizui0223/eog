"""Only fabricated digests; never load real house sparrow rows in synthetic CI."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_2023_public_copies_against_v8_bytes_v1 import (
    HIST,EQUIV,IDS,verify,hash_official_public_copy,
)


def source():
    h=json.loads(HIST.read_text(encoding="utf-8"))
    e=json.loads(EQUIV.read_text(encoding="utf-8"))
    entries={x["name"]:x for x in h["archives"]["niskanen_2020"]["critical_files"]}
    simulated={}
    for name,v10_id in IDS.items():
        fake=(name+"\nSYNTHETIC private data never serialize\n").encode()
        entries[name]["size_bytes"]=len(fake)
        entries[name]["source_digest"]=hashlib.sha256(fake).hexdigest()
        simulated[v10_id]=fake
    return h,e,simulated


def test_three_actual_copy_hash_gate_with_synthetic_files():
    h,e,data=source()
    def download(identifier,size):
        raw=data[identifier]
        return hashlib.sha256(raw).hexdigest(),len(raw)
    x=verify(h,e,download)
    assert x["status"]=="THREE_PUBLIC_COPIES_INDEPENDENTLY_HASH_MATCH_ORIGINAL_2020_V8"
    assert len(x["files"])==3
    assert all(item["independent_actual_byte_sha256_matches_historical_v8"] for item in x["files"])
    assert x["2023_only_files_authorized_as_2020_inputs"] is False
    assert x["ecological_forecast_authorized"] is False
    assert "SYNTHETIC private" not in json.dumps(x)


def test_same_size_modified_later_copy_is_rejected():
    h,e,data=source()
    name="Pop_size_1997_2012.csv"
    bad_id=IDS[name]
    old=data[bad_id]
    data[bad_id]=old.replace(b"SYNTHETIC",b"synthetic")
    assert len(data[bad_id])==len(old)
    def download(identifier,size):
        raw=data[identifier]
        return hashlib.sha256(raw).hexdigest(),len(raw)
    with pytest.raises(ValueError,match="NOT identical"):
        verify(h,e,download)


def test_source_version_identity_drift_is_rejected():
    h,e,data=source()
    e["source"]["later_v10_version_id"]=123
    with pytest.raises(ValueError,match="source pair"):
        verify(h,e,lambda *_:(None,None))


def test_reported_digest_mismatch_cannot_unlock_later_copy():
    h,e,data=source()
    e["pairs"][0]["source_reported_sha256_equal"]=False
    with pytest.raises(ValueError,match="equivalence unqualified"):
        verify(h,e,lambda *_:(None,None))


def test_no_other_public_file_ids_and_no_new_2023_source_fields():
    with pytest.raises(ValueError,match="unpinned"):
        hash_official_public_copy(999999,100)
    script=(ROOT/"scripts/audit_helgeland_2023_public_copies_against_v8_bytes_v1.py").read_text()
    assert len(IDS)==3
    assert 'ROOT_URL = "https://datadryad.org/downloads/file_stream/"' in script
    assert "read_csv(" not in script
    assert "import pandas" not in script
    assert "actual_bytes_decoded_as_biological_rows" in script
