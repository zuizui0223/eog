import hashlib
import json
import runpy

import pytest


def _module():
    return runpy.run_path("scripts/glanville_zenodo_software_schema_v4.py")


def _proto():
    return json.load(open("validation/glanville_zenodo_software_schema_v4/protocol_v4.json"))


def _fixture():
    p=_proto()
    source=b'''
library(dplyr)
sourcePatch <- "A"
destinationPatch <- "B"
year <- 2021
geneticAssignment <- "GENECLASS2"
dat <- read.csv("/private/hypothesis/dispersal_events.csv")
'''
    p["source_file_bytes"]=len(source)
    p["source_md5"]=hashlib.md5(source).hexdigest()
    record={
        "metadata":{"title":"Source code"},
        "files":[{
            "key":"mainAnalysis.R",
            "size":len(source),
            "checksum":"md5:"+p["source_md5"],
            "links":{"self":"https://zenodo.org/api/files/pinned/mainAnalysis.R"}
        }]
    }
    return p,record,source


def test_source_freeze_and_software_only_limit():
    p=_proto()
    assert p["status"]=="pre_fetch_single_publisher_software_frozen"
    assert p["source_md5"]=="f75ce54da557c221ee0a09f9fb1aaee2"
    assert p["source_file_bytes"]==26693
    assert p["source_filename"]=="mainAnalysis.R"
    assert p["dryad_source_stop"]=="STOP_HTTP_SOURCE_401"
    assert p["network"]["max_downloads"]==1


def test_verified_script_symbols_are_static_not_data_rows(monkeypatch):
    m=_module()
    p,record,source=_fixture()
    calls=[]
    def fake_get(url,*,limit):
        calls.append(url)
        return json.dumps(record).encode() if url==p["zenodo_api"] else source
    monkeypatch.setitem(m["run"].__globals__,"_get",fake_get)
    result=m["run"](p)
    assert result["status"]=="SOFTWARE_STATIC_IDENTIFIERS_QUALIFIED_EVENT_DATA_UNVERIFIED"
    assert len(calls)==2
    assert result["script_executed"] is False
    assert result["source_destination_year_events_verified"] is False
    assert result["genetic_event_data_rows_read"]==0
    assert "dispersal_events.csv" in result["static_token_metadata"]["distinct_input_filename_like_literals"]
    assert "sourcePatch" in result["static_token_metadata"]["distinct_identifier_hints"]
    assert result["static_token_metadata"]["source_destination_year_symbol_cues"]["source_or_origin"]
    assert result["static_token_metadata"]["source_destination_year_symbol_cues"]["destination_or_sample"]
    assert "/private/" not in json.dumps(result)


def test_bad_checksum_refuses_inference(monkeypatch):
    m=_module()
    p,record,source=_fixture()
    record["files"][0]["checksum"]="md5:"+"0"*32
    called=[]
    def fake(url,*,limit):
        called.append(url)
        return json.dumps(record).encode()
    monkeypatch.setitem(m["run"].__globals__,"_get",fake)
    result=m["run"](p)
    assert result["status"]=="STOP_ZENODO_FILE_METADATA_CHANGED"
    assert len(called)==1
    assert result["genetic_event_data_rows_read"]==0


def test_missing_script_returns_explicit_stop(monkeypatch):
    m=_module()
    p,record,source=_fixture()
    record["files"]=[]
    monkeypatch.setitem(m["run"].__globals__,"_get",lambda u,*,limit:json.dumps(record).encode())
    result=m["run"](p)
    assert result["status"]=="STOP_ZENODO_FILE_MISSING_OR_AMBIGUOUS"


def test_external_source_hosts_are_not_followed():
    m=_module()
    with pytest.raises(m["SourceStop"],match="STOP_UNAPPROVED_ZENODO_FILE_LINK"):
        m["_safe_source"]("https://example.org/api/files/abc/mainAnalysis.R")
