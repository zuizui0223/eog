"""No biological outcomes: pure offline tests of Dryad source-gate contracts."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH=Path(__file__).resolve().parents[1]/"benchmarks"/"mediterranean_sowing_source_gate_v1.py"
spec=importlib.util.spec_from_file_location("med_sowing_gate",PATH)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FILES={name:("site,species,treatment,year,germ\ns1,sp1,protected,2023,1\n".encode()
             if name.endswith(".csv") else b"README example, fictional data\n")
       for name in mod.REQUIRED}

def mock_get(url,limit):
    if url==mod.API:
        return json.dumps({"_links":{"stash:version":{"href":"/api/v2/versions/341"}}}).encode(),"HTTP_200"
    if url=="https://datadryad.org/api/v2/versions/341/files":
        rows=[{"path":k,"id":100+i,"size":len(v),"digest":hashlib.sha256(v).hexdigest(),
               "digestType":"sha-256"} for i,(k,v) in enumerate(FILES.items())]
        return json.dumps({"_embedded":{"stash:files":rows}}).encode(),"HTTP_200"
    for i,(k,v) in enumerate(FILES.items()):
        if url=="https://datadryad.org/api/v2/files/"+str(100+i)+"/download":
            return v,"HTTP_200"
    raise AssertionError("unexpected endpoint "+url)

def test_offline_exact_source_header_gate(tmp_path):
    receipt=mod.run(tmp_path,mock_get)
    assert receipt["status"]=="SOURCE_BYTES_VERIFIED_NOT_SCORED"
    assert receipt["number_response_effects_scored"]==0
    assert receipt["biological_outcome_values_read"] is False
    assert (tmp_path/"sowing_experiment.csv").read_bytes()==FILES["sowing_experiment.csv"]
    assert "s1,sp1" not in (tmp_path/"source_gate.json").read_text()

def test_missing_file_is_stop(tmp_path):
    def no_source(url,limit):
        if url==mod.API:return None,"HTTP_403"
        raise AssertionError(url)
    r=mod.run(tmp_path,no_source)
    assert r["status"]=="SOURCE_STOP"
    assert all(row["status"]=="STOP_MISSING_MANIFEST" for row in r["source_files"].values())
    assert not (tmp_path/"sowing_experiment.csv").exists()

def test_modified_byte_rejected(tmp_path):
    def corrupt(url,limit):
        data,status=mock_get(url,limit)
        if url=="https://datadryad.org/api/v2/files/100/download":
            return data.replace(b"protected",b"exposed!!"),status
        return data,status
    r=mod.run(tmp_path,corrupt)
    assert r["status"]=="SOURCE_STOP"
    assert r["source_files"]["sowing_experiment.csv"]["status"] in ("STOP_SIZE_MISMATCH","STOP_DIGEST_MISMATCH")
    assert not (tmp_path/"sowing_experiment.csv").exists()

def test_reject_unverified_digest_and_external_file_link():
    assert mod.allowed_meta_url("https://example.net/api/v2/versions/1") is None
    assert mod.allowed_meta_url("/api/v2/versions/1")=="https://datadryad.org/api/v2/versions/1"
    fake={"_links":{"stash:version":{"href":"/api/v2/versions/9"}}}
    def manifest_fetch(url,limit):
        payload={"_embedded":{"stash:files":[
          {"path":"sowing_experiment.csv","id":33,"size":14,"digest":"bad","digestType":"md5"}
        ]}}
        return json.dumps(payload).encode(),"HTTP_200"
    files,_=mod.file_manifest(fake,manifest_fetch)
    assert files["sowing_experiment.csv"]["status"]=="STOP_INVALID_DIGEST_OR_SIZE"
