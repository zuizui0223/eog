"""Source qualification only: no ecological outcome data in outputs or tests."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

from scripts import eog_independent_movement_source_gate_v1 as m

PROTOCOL = json.loads(Path(
    "validation/independent_movement_source_gate_v1/protocol_v1.json"
).read_text(encoding="utf-8"))


def synthetic_files():
    return {
        "data_site_fidelity.csv": b"individual_id,source,destination,date\ni001,A,B,2020-01-01\ni002,B,C,2020-01-03\n",
        "turning_data.csv": b"individual_id,angle\ni001,80\n",
        "README.txt": b"Test dataset only, not a biological example\nNo real movement values.\n",
    }


def zip_bytes(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


def metadata_files(files):
    return {"_embedded":{"stash:files":[{
        "path":name,
        "size":len(data),
        "digestType":"md5",
        "digest":hashlib.md5(data).hexdigest(),
    } for name, data in files.items()]}}


def test_synthetic_archive_header_only_and_checksum_gate():
    src = PROTOCOL["source_references"][0]
    files = synthetic_files()
    met = m._metadata_files(metadata_files(files), 25)
    actual = m._read_zip(zip_bytes(files), src, PROTOCOL["resource_limits"], met)
    assert {x["name"] for x in actual} == set(files)
    assert [x["data_row_count"] for x in actual if x["name"] == "data_site_fidelity.csv"] == [2]
    assert [x["csv_header"] for x in actual if x["name"] == "data_site_fidelity.csv"] == [
        ["individual_id","source","destination","date"]
    ]
    assert all(x["publisher_digest_verified"] for x in actual)
    assert "i001" not in json.dumps(actual)
    assert "2020-01-01" not in json.dumps(actual)


def test_bad_publisher_digest_fails_without_scoring():
    src = PROTOCOL["source_references"][0]
    files = synthetic_files()
    met = m._metadata_files(metadata_files(files),25)
    met[0]["publisher_digest"] = "0"*32
    with pytest.raises(ValueError, match="STOP_MEMBER_PUBLISHER_CHECKSUM_MISMATCH"):
        m._read_zip(zip_bytes(files),src,PROTOCOL["resource_limits"],met)


def test_wrong_filelist_and_unsafe_zip_fail_closed():
    src = PROTOCOL["source_references"][0]
    files = synthetic_files()
    met = m._metadata_files(metadata_files(files),25)
    with pytest.raises(ValueError, match="STOP_VERSION_ZIP_FILES_MISMATCH"):
        m._read_zip(zip_bytes({**files,"not_expected.csv":b"a\n1\n"}),src,PROTOCOL["resource_limits"],met)
    with pytest.raises(ValueError,match="STOP_ZIP_UNSAFE_PATH"):
        m._read_zip(zip_bytes({**files,"../unsafe.txt":b"a"}),src,PROTOCOL["resource_limits"],met)


def test_schema_without_version_is_stop_not_guess():
    with pytest.raises(ValueError, match="STOP_VERSION_ID_NOT_IN_OFFICIAL_METADATA"):
        m._version_id({"identifier":"doi:10.5061/dryad.test"})
    assert m._version_id({"_links":{"stash:version":{"href":"/api/v2/versions/1111"}}}) == "1111"


def test_fake_official_dryad_metadata_qualification_without_event_values(monkeypatch):
    p = deepcopy(PROTOCOL)
    p["source_references"] = p["source_references"][:1]
    s = p["source_references"][0]
    files = synthetic_files()
    packed = zip_bytes(files)
    def faux_json(url, limits):
        if url.endswith("/files?per_page=100"):
            return metadata_files(files),"file-metadata-sha"
        if url.endswith("/versions/167"):
            return {"versionNumber":1,"publicationDate":"2021-11-14"},"version-sha"
        if "datasets/" in url:
            return {
                "identifier":"doi:"+s["doi"],
                "title":s["publication"],
                "_links":{"stash:version":{"href":"/api/v2/versions/167"}},
            },"dataset-sha"
        raise AssertionError("unexpected URL: "+url)
    def faux_download(url, **kwargs):
        assert url.endswith("/versions/167/download")
        return packed,"datadryad.org"
    monkeypatch.setattr(m,"_json_get",faux_json)
    monkeypatch.setattr(m,"_get",faux_download)
    r=m.run(p)
    assert r["status"]=="SOURCE_SCHEMA_GATES_ALL_PASS"
    assert r["source_results"][0]["status"]=="SOURCE_SCHEMA_ONLY_QUALIFIED_BIOLOGICAL_OUTCOME_NOT_SCORED"
    assert r["source_results"][0]["publisher_version_id"]=="167"
    assert r["source_results"][0]["file_checks"][0]["sha256"]
    assert r["biological_outcomes_analyzed"]==0
    assert r["ecological_models_fit"]==0
    assert r["new_eog_wf_endpoints"]==0
    assert "i001" not in json.dumps(r)


def test_fake_http_denial_retains_scientific_stop(monkeypatch):
    def http_block(url,limits):
        raise m.urllib.error.HTTPError(url,403,"AccessDenied",hdrs=None,fp=None)
    monkeypatch.setattr(m,"_json_get",http_block)
    outcome=m.run(PROTOCOL)
    assert outcome["status"]=="SOURCE_SCHEMA_HAS_SCIENTIFIC_STOP"
    assert len(outcome["source_results"])==2
    assert all(x["status"]=="STOP_TRANSPORT_HTTP_403" for x in outcome["source_results"])
    assert outcome["new_eog_wf_endpoints"]==0


def test_transport_host_approval_is_strict():
    assert m._approved("datadryad.org",payload=False)
    assert m._approved("s3.us-east-1.amazonaws.com",payload=True)
    assert not m._approved("s3.us-east-1.amazonaws.com",payload=False)
    assert not m._approved("untrusted.example.com",payload=True)


def test_protocol_two_sources_are_frozen_with_different_research_units():
    s=PROTOCOL["source_references"]
    assert len(s)==2
    assert s[0]["doi"]=="10.5061/dryad.34tmpg4m6"
    assert s[1]["doi"]=="10.5061/dryad.x3ffbg7ms"
    assert "translocation" in s[0]["declared_research_unit"]
    assert s[0]["publisher_landing_file_names"]==[
        "data_site_fidelity.csv","turning_data.csv","README.txt"
    ]
    assert PROTOCOL["output_contract"]["new_EOG_WF_endpoints"]==0
