"""Synthetic-only Zenodo preservation search / fixed-2020-file-byte parity tests."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import audit_helgeland_2020_v8_zenodo_preservation_v1 as audit


def fixture():
    source=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    original=copy.deepcopy(source)
    items=original["archives"]["niskanen_2020"]["critical_files"]
    fake_data={}
    meta_files=[]
    for n,item in enumerate(items):
        name=item["name"]
        raw=(("Year;Island;N" if name.endswith(".csv") else "README SYNTHETIC")
             +f"\nprivate invented source row {n}\n").encode()
        item["size_bytes"]=len(raw)
        item["source_digest"]=hashlib.sha256(raw).hexdigest()
        link=f"https://zenodo.org/api/records/123456/files/example{n}/content"
        fake_data[link]=raw
        meta_files.append({"key":name,"size":len(raw),"links":{"content":link}})
    meta_files.append({"key":"ADDED_ONLY_IN_2023.csv","size":123,
                       "links":{"content":"https://zenodo.org/api/records/123456/files/new/content"}})
    rec={"id":123456,"metadata":{
        "title":audit.EXPECTED_TITLE,
        "creators":[{"name":"Niskanen, Alina K."}],
        "description":"Preservation copy of Dryad doi:10.5061/dryad.m0cfxpp10"},
        "files":meta_files}
    return original,rec,fake_data


def test_exactly_three_2020_bytes_can_pass_from_zenodo_preservation():
    frozen,record,raw=fixture()
    actual=audit.pinned_files(frozen)
    def get(uri,maximum):
        body=raw[uri]
        assert len(body)<=maximum
        return hashlib.sha256(body).hexdigest(),len(body)
    result=audit.compare(record,actual,get)
    assert result["status"]=="THREE_ZENODO_PRESERVATION_FILES_FULL_HASH_MATCH_ORIGINAL_2020_V8"
    assert result["preservation_zenodo_record_id"]==123456
    assert len(result["files"])==3
    assert result["zenodo_only_newer_files_authorized_for_2020"] is False
    assert result["ecological_forecast_authorized"] is False
    assert "private invented" not in json.dumps(result)


@pytest.mark.parametrize("mutation",["digest","size","missing","title","creator","url"])
def test_wrong_mirror_or_modified_bytes_do_not_pass(mutation):
    frozen,record,raw=fixture()
    if mutation=="digest":
        target=next(iter(raw))
        raw[target]=raw[target].replace(b"private",b"PRIVATE")
    elif mutation=="size":
        record["files"][0]["size"]+=1
    elif mutation=="missing":
        record["files"].pop(0)
    elif mutation=="title":
        record["metadata"]["title"]="A different study"
    elif mutation=="creator":
        record["metadata"]["creators"]=[{"name":"Other author"}]
    elif mutation=="url":
        record["files"][0]["links"]["content"]="https://evil.test/download"
    def get(uri,maximum):
        body=raw[uri]
        return hashlib.sha256(body).hexdigest(),len(body)
    with pytest.raises((ValueError,KeyError)):
        audit.compare(record,audit.pinned_files(frozen),get)


def test_api_search_and_source_identifier_require_authentic_evidence():
    frozen,record,raw=fixture()
    def finder():
        return [record]
    def get(uri,maxsize):
        body=raw[uri]
        return hashlib.sha256(body).hexdigest(),len(body)
    result=audit.audit(frozen,finder,get)
    assert result["status"]=="THREE_ZENODO_PRESERVATION_FILES_FULL_HASH_MATCH_ORIGINAL_2020_V8"
    assert audit.matching_record(record)
    assert not audit.matching_record({**record,"metadata":{**record["metadata"],"title":"Different data"}})


def test_empty_search_and_network_error_stay_hold():
    frozen,_,_=fixture()
    assert audit.audit(frozen,lambda:[])["status"]=="HOLD_NO_MATCHING_ZENODO_SOURCE_RECORD"
    def failure():
        raise TimeoutError("synthetic server unavailable")
    assert audit.audit(frozen,failure)["status"]=="HOLD_ZENODO_SOURCE_SEARCH_UNAVAILABLE"


def test_original_v8_is_immutable_and_2023_only_data_never_eligible():
    x=json.loads(audit.SOURCE.read_text(encoding="utf-8"))
    originals=audit.pinned_files(x)
    assert set(originals)=={
        "Dryad_readme.txt","Pop_size_1997_2012.csv","Pop_size_1998_2013.csv"}
    assert x["archives"]["niskanen_2020"]["version_id"]==78498
    assert x["archives"]["niskanen_2020"]["published_date"]=="2020-08-19"


def test_restricted_link_and_maximum_byte_size_no_credential_or_row_parsing():
    for bad in ("https://other.site/api/records/123/files/a/content",
                "http://zenodo.org/api/records/123/files/a/content",
                "https://zenodo.org.evil.net/api/records/123/files/a/content"):
        with pytest.raises(ValueError,match="unexpected Zenodo"):
            audit._file_link({"links":{"content":bad}})
    script=(ROOT/"scripts/audit_helgeland_2020_v8_zenodo_preservation_v1.py").read_text()
    for forbidden in ("read_csv(", "import pandas", "import numpy", "requests.get(",
                      "api_token", "client_secret", "credential", "eval("):
        assert forbidden not in script
    assert "ecological_forecast_authorized" in script
