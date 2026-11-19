import json
import runpy

import pytest


def _m():
    return runpy.run_path("scripts/glanville_genetic_origin_dryad_manifest_v2.py")


def _protocol():
    return json.load(open("validation/glanville_genetic_origin_dryad_manifest_v2/protocol_v2.json"))


def _versions():
    return {"_embedded":{"stash:versions":[
        {"versionNumber":1,"publicationDate":"2022-05-01",
         "_links":{"self":{"href":"/api/v2/versions/100"},
                   "stash:files":{"href":"/api/v2/versions/100/files"}}},
        {"versionNumber":2,"publicationDate":"2022-07-04",
         "_links":{"self":{"href":"/api/v2/versions/222"},
                   "stash:files":{"href":"/api/v2/versions/222/files"}}}
    ]}}


def _files():
    return {"_embedded":{"stash:files":[
        {"path":"Assignment_results.csv","size":1000,"mimeType":"text/csv",
         "digest":"a"*64,"digestType":"sha-256",
         "_links":{"stash:version":{"href":"/api/v2/versions/222"}}},
        {"path":"readme.txt","size":220,"digest":"b"*64,
         "digestType":"sha-256",
         "_links":{"stash:version":{"href":"/api/v2/versions/222"}}}
    ]}}


def test_protocol_and_stage_one_fingerprint_are_frozen():
    p=_protocol()
    assert p["status"]=="frozen_before_dryad_version_file_listing"
    assert p["parent_source_result_sha256_without_self_hash"]=="8a32b9efeed085af7bb108f6cd655af5c0e84d16efa818f3a69a515001c9c931"
    assert p["max_file_entries"]==250
    assert p["file_manifest_selection"].startswith("Use _links")


def test_version_selection_pins_public_last_published_and_reads_no_file_bytes(monkeypatch):
    m=_m()
    p=_protocol()
    calls=[]
    def fake_get(url,cap):
        calls.append(url)
        if url==p["version_list_url"]:
            return _versions(),"1"*64
        if url=="https://datadryad.org/api/v2/versions/222/files":
            return _files(),"2"*64
        raise AssertionError("unknown GET "+url)
    monkeypatch.setitem(m["run"].__globals__,"_get_json",fake_get)
    r=m["run"](p)
    assert r["status"]=="DRYAD_VERSION_PINNED_FILE_METADATA_ONLY_EVENT_JOIN_NOT_VERIFIED"
    assert r["version_id"]==222
    assert r["file_count"]==2
    assert r["file_bytes_opened"]==0
    assert r["biological_event_rows_read"]==0
    assert r["genetically_inferred_source_direction_verified"] is False
    assert len(calls)==2
    assert r["filename_only_possible_event_table_names"]==["Assignment_results.csv"]


def test_bad_version_link_fails_closed(monkeypatch):
    m=_m()
    versions=_versions()
    versions["_embedded"]["stash:versions"][-1]["_links"]["stash:files"]["href"]="/api/v2/versions/100/files"
    monkeypatch.setitem(m["run"].__globals__,"_get_json",lambda u,cap:(versions,"1"*64))
    r=m["run"](_protocol())
    assert r["status"]=="STOP_VERSION_FILES_LINK_NOT_PINNABLE"
    assert r["file_count"] if "file_count" in r else r["files"]==[]


def test_mismatched_file_version_is_a_stop_not_a_heuristic_mapping(monkeypatch):
    m=_m()
    files=_files()
    files["_embedded"]["stash:files"][0]["_links"]["stash:version"]["href"]="/api/v2/versions/999"
    def fake(u,cap):
        return (_versions() if "datasets/" in u else files),"1"*64
    monkeypatch.setitem(m["run"].__globals__,"_get_json",fake)
    r=m["run"](_protocol())
    assert r["status"]=="STOP_VERSION_MISMATCH_IN_FILE_LINK"
    assert r["genetically_inferred_source_direction_verified"] is False


def test_empty_file_list_cannot_be_promoted_to_source_data(monkeypatch):
    m=_m()
    def fake(u,cap):
        return (_versions() if "datasets/" in u else {"_embedded":{"stash:files":[]}}),"0"*64
    monkeypatch.setitem(m["run"].__globals__,"_get_json",fake)
    r=m["run"](_protocol())
    assert r["status"]=="STOP_NO_FILES"
    assert r["file_bytes_opened"]==0


def test_unapproved_host_and_unsafe_filename_rejected():
    m=_m()
    with pytest.raises(m["SourceStop"],match="STOP_UNAPPROVED_API_LINK"):
        m["_api_url"]("https://example.org/api/v2/versions/2/files")
    with pytest.raises(m["SourceStop"],match="STOP_FILE_MANIFEST_SCHEMA_BAD_PATH"):
        m["_manifest_page"]({"_embedded":{"stash:files":[
            {"path":"../private.tsv","size":12}
        ]}},123)
