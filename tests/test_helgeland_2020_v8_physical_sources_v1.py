"""Synthetic public Dryad v8 file-byte/header gate, no original bird values."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"scripts/audit_helgeland_2020_v8_physical_sources_v1.py"
FROZEN=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json"


def module():
    spec=importlib.util.spec_from_file_location("eog_2020_v8_byte_gate",SOURCE)
    m=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=m
    spec.loader.exec_module(m)
    return m


def setup():
    m=module()
    source=copy.deepcopy(json.loads(FROZEN.read_text(encoding="utf-8")))
    fake={}
    for item in source["archives"]["niskanen_2020"]["critical_files"]:
        suffix="\nSYNTHETIC_IGNORED_BIRD_RECORD\n"
        data=(('ID;Year;Island' if item["name"].endswith(".csv")
               else 'Readme for fictional data') + suffix).encode()
        fake[item["file_id"]]=data
        item["size_bytes"]=len(data)
        item["source_digest"]=hashlib.sha256(data).hexdigest()
    return source,fake


def test_exact_three_whole_file_hashes_and_firstline_shape_only():
    m=module()
    frozen,mock=setup()
    def fetch(file_id,max_bytes):
        data=mock[file_id]
        assert len(data)<=max_bytes
        return hashlib.sha256(data).hexdigest(),len(data),data.split(b"\n",1)[0]+b"\n"
    result=m.audit(frozen,fetch)
    assert result["status"]=="THREE_2020_V8_SOURCE_SHA256S_MATCH__FIRSTLINE_SHAPE_ONLY"
    assert len(result["records"])==3
    assert all(x["whole_file_sha256_verified"] for x in result["records"])
    assert all(x["physical_semantic_header_attested"] is False for x in result["records"])
    assert all(x["data_records_parsed"] is False for x in result["records"])
    assert "SYNTHETIC_IGNORED" not in json.dumps(result)
    assert result["ecological_forecast_authorized"] is False


def test_same_length_modified_file_bytes_stop():
    m=module();frozen,mock=setup()
    changed=next(iter(mock))
    original=mock[changed]
    mock[changed]=original.replace(b"SYNTHETIC",b"SYNTHETIc")
    assert len(original)==len(mock[changed])
    def fetch(file_id,max_bytes):
        raw=mock[file_id]
        return hashlib.sha256(raw).hexdigest(),len(raw),raw.split(b"\n",1)[0]+b"\n"
    with pytest.raises(ValueError,match="independent actual source bytes"):
        m.audit(frozen,fetch)


def test_latest_2023_source_revision_rejected():
    m=module();frozen,_=setup()
    frozen["archives"]["niskanen_2020"]["version_id"]=208617
    with pytest.raises(ValueError,match="historically published"):
        m.audit(frozen,lambda *_:None)


def test_delimiter_and_shape_are_only_potential_not_a_claim_of_semantics():
    m=module()
    result=m.firstline_shape(b'Year,Island,N\n')
    assert result["delimiter"]=="COMMA"
    assert result["firstline_field_count"]==3
    assert result["physical_semantic_header_attested"] is False
    result=m.firstline_shape(b'a;b,c\n')
    assert result["delimiter"]=="HOLD_AMBIGUOUS_PHYSICAL_SEPARATOR"
    assert result["firstline_values_emitted"] if "firstline_values_emitted" in result else True


def test_no_actual_bird_output_or_broad_remote_downloads():
    m=module()
    with pytest.raises(ValueError,match="File ID"):
        m.opaque_file_download(999999, 10)
    source=SOURCE.read_text(encoding="utf-8")
    for banned in ("read_csv(", "import pandas", "import numpy", "import sklearn",
                   "from Bio", "biological_outcome", "compute_score("):
        assert banned not in source
    assert "other_physical_lines_decoded" in source
