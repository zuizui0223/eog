import copy
import hashlib
import io
import json
import runpy
import urllib.error
import urllib.request
import zipfile

import pytest


def _m():
    return runpy.run_path("scripts/glanville_genetic_origin_source_preflight_v1.py")


def _protocol():
    return json.load(open("validation/glanville_genetic_origin_source_preflight_v1/protocol_v1.json"))


def test_protocol_scope_and_research_provenance():
    p=_protocol()
    assert p["status"]=="pre_transport_metadata_only_frozen"
    assert p["base_main_sha"]=="899dc7be7ea5ffc5a475551316484a12a2d2dd55"
    assert p["source_contract"]["record_id"]==6610910
    assert p["source_contract"]["candidate_downloads_max"]==1
    assert "not a fresh independent" in " ".join(p["scientific_separation"]).lower()


def test_zenodo_api_v3_and_v4_file_normalization():
    m=_m()
    v3={"files":[{"key":"b.csv","size":3,"checksum":"md5:8d777f385d3dfec8815d20f7496026dc",
                  "links":{"self":"https://zenodo.org/api/files/x/b.csv"}}]}
    a=m["_normalize_files"](v3)
    assert len(a)==1 and a[0]["filename"]=="b.csv"
    v4={"files":{"entries":{"a.zip":{"size":50,"checksum":"md5:abc",
                                         "links":{"content":"https://zenodo.org/api/records/6610910/files/a.zip/content"}}}}}
    b=m["_normalize_files"](v4)
    assert b[0]["filename"]=="a.zip" and b[0]["size"]==50


def test_candidate_choosing_is_fixed_without_response_scanning():
    m=_m()
    p=_protocol()["source_contract"]
    x=[{"filename":"z.zip","size":500,"checksum":"md5:x","_url":"https://zenodo.org/a"},
       {"filename":"dispersal_events.csv","size":200,"checksum":"md5:y","_url":"https://zenodo.org/b"},
       {"filename":"README.md","size":100,"checksum":"md5:z","_url":"https://zenodo.org/c"}]
    assert m["_candidate"](x,p)["filename"]=="dispersal_events.csv"
    assert m["_candidate"](x[:1],p)["filename"]=="z.zip"
    assert m["_candidate"](x[2:],p) is None


def test_single_metadata_and_one_file_manifest_does_not_read_event_rows(monkeypatch):
    m=_m()
    p=_protocol()
    data=b"source_patch,destination_patch,year\nA,B,2010\n"
    md5=hashlib.md5(data).hexdigest()
    zenodo={"metadata":{"title":"software test"},
            "files":[{"key":"dispersal_events.csv","size":len(data),"checksum":"md5:"+md5,
                      "links":{"self":"https://zenodo.org/api/files/test/dispersal_events.csv"}}]}
    fake={
        p["source_contract"]["zenodo_api"]:(json.dumps(zenodo).encode(),200),
        p["source_contract"]["dryad_api"]:(b'{"title":"test Dryad"}',200),
        "https://zenodo.org/api/files/test/dispersal_events.csv":(data,200)
    }
    calls=[]
    def request(url,*,byte_cap):
        calls.append(url)
        return fake[url]
    monkeypatch.setitem(m["run"].__globals__,"_request",request)
    result=m["run"](p)
    assert len(calls)==3
    assert result["status"]=="SOURCE_METADATA_PREFLIGHT_COMPLETED_EVENT_JOIN_NOT_VERIFIED"
    assert result["zenodo"]["candidate_checksum_matches_publisher"] is True
    assert result["zenodo"]["candidate_structure"]["first_line_header"]=="source_patch,destination_patch,year"
    assert result["biological_event_rows_read"]==0
    assert result["join_to_Glanville_patch_table_verified"] is False


def test_http_stop_not_replaced_by_ecological_failure(monkeypatch):
    m=_m()
    def fail(url,*,byte_cap):
        raise urllib.error.HTTPError(url,403,"Forbidden",{},None)
    monkeypatch.setitem(m["run"].__globals__,"_request",fail)
    result=m["run"](_protocol())
    assert result["status"]=="STOP_SOURCE_METADATA_UNAVAILABLE"
    assert result["zenodo"]["status"]=="STOP_HTTP_403"
    assert result["dryad"]["status"]=="STOP_HTTP_403"
    assert result["new_EOG_WF_endpoints"]==0


def test_checksum_disagreement_does_not_open_record_rows(monkeypatch):
    m=_m();p=_protocol()
    record={"metadata":{},"files":[{"key":"dispersal_data.csv","size":10,
          "checksum":"md5:"+"0"*32,
          "links":{"content":"https://zenodo.org/api/files/test/dispersal_data.csv"}}]}
    def fake(url,*,byte_cap):
        if url==p["source_contract"]["zenodo_api"]:
            return json.dumps(record).encode(),200
        if url==p["source_contract"]["dryad_api"]:
            return b'{"title":"Dryad"}',200
        return b"row,x\n1,2\n",200
    monkeypatch.setitem(m["run"].__globals__,"_request",fake)
    result=m["run"](p)
    assert result["zenodo"]["file_gate_status"]=="STOP_SOURCE_CHECKSUM_MISMATCH"
    assert "candidate_structure" not in result["zenodo"]
    assert result["biological_event_rows_read"]==0
