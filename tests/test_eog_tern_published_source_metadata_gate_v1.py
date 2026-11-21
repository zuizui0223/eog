"""Offline source metadata-only Arctic tern admission; biological rows never loaded."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts import eog_tern_published_source_metadata_gate_v1 as m

SPEC=json.loads(Path("validation/tern_published_departure_source_gate_v1/protocol_v1.json").read_text(encoding="utf-8"))
DOI="10.5061/dryad.x69p8czxh"
ROSTER=sorted(["Ad_DaD.csv","U_DaD.csv","BasicInfoplot.Rmd","README.md","revision.R"])


def fake_get(url, limits):
    if url.endswith("datasets/doi%3A10.5061%2Fdryad.x69p8czxh"):
        return {
            "identifier":"doi:"+DOI,
            "title":"Natal versus breeding dispersal in Arctic terns",
            "_links":{"stash:version":{"href":"/api/v2/versions/123456"}},
        },"sha_dataset"
    if url.endswith("versions/123456"):
        return {"publicationDate":"2026-09-30T00:00:00Z", "versionNumber":1},"sha_version"
    if url.endswith("/versions/123456/files?per_page=100"):
        return {"_embedded":{"stash:files":[
            {"path":name,"size":123+idx, "digestType":"sha256", "digest":"0123"}
            for idx,name in enumerate(ROSTER)
        ]}},"sha_files"
    raise AssertionError("unexpected metadata endpoint "+url)


def test_frozen_source_id_and_no_event_read():
    assert SPEC["status"]=="PRE_METADATA_SOURCE_ONLY_FROZEN"
    assert SPEC["declared_source"]["dataset_doi"]==DOI
    assert SPEC["stage0_transport"]["metadata_only"]
    assert SPEC["declared_source"]["declared_official_data_grain"]["Ad_DaD.csv"].startswith("200")
    assert SPEC["original_eog_wf_closed_denominator"]=={
        "scored":3,"scientific_STOP":31,"administrative_exclusions":3}


def test_exact_official_version_and_file_manifest_no_movement_scoring():
    out=m.qualify_metadata(SPEC,fetch_json=fake_get)
    assert out["status"]=="SOURCE_METADATA_AND_FILE_MANIFEST_QUALIFIED_NO_EVENTS"
    assert out["publisher_version_id"]==123456
    assert out["published_date"]=="2026-09-30"
    assert sorted(x["name"] for x in out["file_manifest"])==ROSTER
    assert out["data_files_downloaded"]==0
    assert out["event_rows_read"]==0
    assert out["predictions_scored"]==0
    assert out["source_holdout_authorized"] is False


def test_wrong_doi_fails_closed():
    def broken(url, limits):
        data, sha=fake_get(url,limits)
        if "datasets/" in url:
            data["identifier"]="doi:10.5061/dryad.bad"
        return data,sha
    result=m.qualify_metadata(SPEC,fetch_json=broken)
    assert result["status"]=="STOP_DATASET_DOI_IDENTITY"
    assert result["event_rows_read"]==0


def test_publisher_roster_drift_cannot_change_selected_files():
    def changed(url, limits):
        data,sha=fake_get(url,limits)
        if url.endswith("/files?per_page=100"):
            data["_embedded"]["stash:files"].pop()
        return data,sha
    result=m.qualify_metadata(SPEC,fetch_json=changed)
    assert result["status"]=="STOP_PUBLISHED_FILE_ROSTER_MISMATCH"
    assert "file_manifest" not in result


def test_date_scope_is_locked_without_outcome_search():
    def changed(url,limits):
        data,sha=fake_get(url,limits)
        if url.endswith("versions/123456"):
            data["publicationDate"]="2025-09-30T00:00:00Z"
        return data,sha
    result=m.qualify_metadata(SPEC,fetch_json=changed)
    assert result["status"]=="STOP_VERSION_PUBLICATION_DATE_MISMATCH"


def test_title_does_not_allow_another_taxon():
    def changed(url,limits):
        data,sha=fake_get(url,limits)
        if "datasets/" in url:
            data["title"]="Movements of unidentified mammals"
        return data,sha
    result=m.qualify_metadata(SPEC,fetch_json=changed)
    assert result["status"]=="STOP_TITLE_SCOPE_MISMATCH"


def test_bad_source_protocol_fails_without_network():
    p=deepcopy(SPEC)
    p["status"]="POST_SCORE_UNKNOWN"
    result=m.qualify_metadata(p,fetch_json=lambda *_: (_ for _ in ()).throw(AssertionError("network called")))
    assert result["status"]=="STOP_PROTOCOL_NOT_FROZEN"
    assert result["new_eog_wf_endpoints"]==0


def test_resource_protection_negative_file_sizes():
    def changed(url,limits):
        data,sha=fake_get(url,limits)
        if url.endswith("/files?per_page=100"):
            data["_embedded"]["stash:files"][0]["size"]=0
        return data,sha
    result=m.qualify_metadata(SPEC,fetch_json=changed)
    assert result["status"]=="STOP_MISSING_PUBLISHER_FILE_SIZE"
