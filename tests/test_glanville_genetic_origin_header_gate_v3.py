import copy
import hashlib
import json
import runpy

import pytest


def _m():
    return runpy.run_path("scripts/glanville_genetic_origin_header_gate_v3.py")


def _p():
    return json.load(open("validation/glanville_genetic_origin_header_gate_v3/protocol_v3.json"))


def _fake_data():
    return {
        "README":b"source patch, destination patch, year, assignment quality labels\n",
        "fullsibfamLevelData.csv":b"family_id,source_patch,destination_patch,year,assignment_score\nsecret1,7,8,2010,100\n",
        "nestLevelData.csv":b"nest_id,natal_patch,samplepatch,year\nprivate2,7,8,2011\n",
    }


def _contract_and_manifest():
    p=_p()
    payloads=_fake_data()
    for item in p["files"]:
        item["size_bytes"]=len(payloads[item["name"]])
        item["sha256"]=hashlib.sha256(payloads[item["name"]]).hexdigest()
    entries=[]
    for i,item in enumerate(p["files"],1000):
        entries.append({"path":item["name"],"size":item["size_bytes"],
          "digest":item["sha256"],"digestType":"sha-256",
          "_links":{"stash:version":{"href":"/api/v2/versions/181375"},
                    "stash:download":{"href":f"/api/v2/files/{i}/download"}}})
    return p,{"_embedded":{"stash:files":entries}},payloads


def test_schema_frozen_before_any_get_and_exact_dataset_version():
    p=_p()
    assert p["status"]=="pre_download_exact_header_only_frozen"
    assert p["target_version_id"]==181375
    assert p["lineage"]["manifest_fingerprint"]=="a003bde0841d5647cd628b0a2a4143d9f0fd91c8c064d5dbbac9c6551c175c64"
    assert [x["name"] for x in p["files"]]==["README","fullsibfamLevelData.csv","nestLevelData.csv"]
    assert p["file_downloads_max"]==3


def test_valid_sha_and_header_only_semantics_never_expose_event_rows(monkeypatch):
    m=_m()
    p,manifest,payloads=_contract_and_manifest()
    headers=[]
    def fake_json(url,cap):
        return manifest,"a"*64
    def fake_download(url,cap):
        number=int(url.rsplit("/",2)[1])
        name=p["files"][number-1000]["name"]
        headers.append(name)
        return payloads[name]
    monkeypatch.setitem(m["run"].__globals__,"_get_json",fake_json)
    monkeypatch.setitem(m["run"].__globals__,"_get_bytes",fake_download)
    r=m["run"](p)
    assert r["status"]=="SOURCE_HEADERS_VERIFIED_EVENT_JOIN_NOT_VALIDATED"
    assert len(r["files"])==3
    assert r["biological_event_rows_read"]==0
    assert r["true_movement_direction_identified"] is False
    assert r["source_patch_join_verified"] is False
    assert headers==["README","fullsibfamLevelData.csv","nestLevelData.csv"]
    assert "secret1" not in json.dumps(r)
    assert "private2" not in json.dumps(r)
    assert r["files"][1]["column_name_signals"]["all_three_source_destination_year_column_cues"]


def test_mismatched_sha_never_opens_csv_header_or_looks_at_rows(monkeypatch):
    m=_m()
    p,manifest,data=_contract_and_manifest()
    p["files"][1]["sha256"]="0"*64
    # Metadata checksum is also incorrect: reject without opening file bytes.
    monkeypatch.setitem(m["run"].__globals__,"_get_json",lambda u,cap:(manifest,"a"*64))
    called=[]
    monkeypatch.setitem(m["run"].__globals__,"_get_bytes",
                        lambda u,cap:(called.append(u) or data["README"]))
    r=m["run"](p)
    assert r["status"]=="STOP_FILE_METADATA_MISMATCH_fullsibfamLevelData.csv"
    assert len(called)==1
    assert r["biological_event_rows_read"]==0


def test_unpinned_file_download_url_and_wrong_version_refused(monkeypatch):
    m=_m()
    p,manifest,data=_contract_and_manifest()
    manifest["_embedded"]["stash:files"][1]["_links"]["stash:version"]["href"]="/api/v2/versions/222"
    monkeypatch.setitem(m["run"].__globals__,"_get_json",lambda u,cap:(manifest,"a"*64))
    monkeypatch.setitem(m["run"].__globals__,"_get_bytes",
                        lambda u,cap:data["README"])
    r=m["run"](p)
    assert r["status"]=="STOP_MANIFEST_VERSION_CHANGED"
    with pytest.raises(m["SourceStop"],match="STOP_INVALID_DRYAD_FILE_API_LINK"):
        m["_safe_url"]("https://evil.example/api/v2/files/42/download",download=True)


def test_csv_schema_handles_bom_but_no_data_line():
    m=_m()
    x=m["_csv_header"](b"\xef\xbb\xbfsource_patch,arrival_patch,year\nprivate,private,2000\n")
    assert x==["source_patch","arrival_patch","year"]
    assert "private" not in ",".join(x)
    assert m["_candidate_signals"](x)["all_three_source_destination_year_column_cues"]
