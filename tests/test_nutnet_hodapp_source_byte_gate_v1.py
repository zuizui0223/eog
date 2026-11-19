"""Pure offline source-byte integrity tests using invented CSV snippets."""
from __future__ import annotations
import hashlib
import importlib.util
from pathlib import Path

MODULE=Path(__file__).resolve().parents[1]/"benchmarks"/"nutnet_hodapp_source_byte_gate_v1.py"
spec=importlib.util.spec_from_file_location("hodapp_byte_gate",MODULE)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def fake_source(monkeypatch, corrupt=False):
    files={
        "composition-data.csv":b"site_code,block,plot,year,cover\ns1,b1,p1,0,1\n",
        "env-param-Y0.csv":b"site_code,block,plot,pH,Ambient_PAR\ns1,b1,p1,6,500\n"
    }
    for k,v in files.items():
        monkeypatch.setitem(mod.EXPECTED,k,(hashlib.md5(v,usedforsecurity=False).hexdigest(),len(v)))
    def call(url):
        if url==mod.DATASET_API:
            return b'{"_links":{"stash:version":{"href":"/api/v2/versions/19"}}}',"HTTP_200"
        if url=="https://datadryad.org/api/v2/versions/19/files":
            return b'{"_embedded":{"stash:files":[{"filename":"composition-data.csv","id":41},{"filename":"env-param-Y0.csv","id":42}]}}',"HTTP_200"
        if url==mod.ZENODO_API:
            return b'{"files":[]}',"HTTP_200"
        if url=="https://datadryad.org/api/v2/files/41/download":
            return (b"tampered" if corrupt else files["composition-data.csv"]),"HTTP_200"
        if url=="https://datadryad.org/api/v2/files/42/download":
            return files["env-param-Y0.csv"],"HTTP_200"
        raise AssertionError(url)
    return call

def test_dryad_bytes_match_and_only_headers_reported(tmp_path,monkeypatch):
    result=mod.run(tmp_path,fake_source(monkeypatch))
    assert result["status"]=="BYTES_VERIFIED_SCHEMA_NOT_SCORED"
    assert result["number_post_treatment_responses_scored"]==0
    assert list(result["source_files"]["composition-data.csv"]["accepted"]["header"])==["site_code","block","plot","year","cover"]
    assert (tmp_path/"composition-data.csv").is_file()
    assert "s1,b1" not in (tmp_path/"source_gate_result.json").read_text()

def test_md5_mismatch_fail_closed(tmp_path,monkeypatch):
    result=mod.run(tmp_path,fake_source(monkeypatch,corrupt=True))
    assert result["status"]=="SOURCE_BYTE_STOP"
    assert result["source_files"]["composition-data.csv"]["accepted"] is None
    assert not (tmp_path/"composition-data.csv").exists()

def test_missing_provider_metadata_stops(tmp_path):
    result=mod.run(tmp_path,lambda url:(None,"HTTP_403"))
    assert result["status"]=="SOURCE_BYTE_STOP"
    assert all(e["accepted"] is None for e in result["source_files"].values())

def test_header_injection_disallowed():
    assert mod.safe_header(b"site,block,plot,year,cover\nx,b,p,0,1\n")==["site","block","plot","year","cover"]
    assert mod.safe_header(b"one,two\nx,y\n") is None
