"""Offline tests: source only, never GPS/ZIP/README payloads."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = runpy.run_path(
    str(ROOT / "validation/temporal_corridor_mckee2024/qualify_gate0.py")
)
SOURCE = ROOT / "validation/temporal_corridor_mckee2024/source_gate0_protocol_v1.json"
qualify = NAMESPACE["qualify_documents"]
audit = NAMESPACE["audit"]
fetch_json = NAMESPACE["_fetch_official_json"]


@pytest.fixture
def fixture_documents():
    proto = json.loads(SOURCE.read_text(encoding="utf-8"))
    version_id = 12345
    dataset = {
        "identifier": "doi:10.5061/dryad.15dv41p51",
        "id": 44444,
        "versionNumber": 1,
        "_links": {"stash:version": {"href": f"/api/v2/versions/{version_id}"}},
    }
    rows = []
    for i, item in enumerate(proto["fixed_source"]["expected_files"]):
        file_id = item["source_landing_file_id"]
        rows.append({
            "path": item["name"],
            "size": 1000 + i,
            "digestType": "sha-256",
            "digest": ("a" if i == 0 else "b" if i == 1 else "c") * 64,
            "status": "created",
            "_links": {
                "self": {"href": f"/api/v2/files/{file_id}"},
                "stash:version": {"href": f"/api/v2/versions/{version_id}"},
            },
        })
    files = {
        "count": 3,
        "total": 3,
        "_links": {"self": {"href": f"/api/v2/versions/{version_id}/files"}},
        "_embedded": {"stash:files": rows},
    }
    return proto, dataset, files


def test_exact_metadata_identity_qualifies_without_opening_source(fixture_documents):
    proto, dataset, files = fixture_documents
    result = qualify(proto, dataset, files)
    assert result["status"] == "SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS"
    assert [f["name"] for f in result["files"]] == sorted(
        x["name"] for x in proto["fixed_source"]["expected_files"]
    )
    assert all(f["source_declared_hash_verified_against_bytes"] is False for f in result["files"])
    assert result["file_payloads_downloaded"] is False
    assert result["README_payload_opened"] is False
    assert result["sparse_12h_tracks_opened"] is False
    assert result["dense_2h_holdout_opened"] is False
    assert result["GPS_records_read"] is False
    assert result["ecological_score_computed"] is False
    assert result["followup_payload_access_authorized"] is False


def test_network_audit_requests_only_two_exact_public_api_json_endpoints(fixture_documents):
    proto, dataset, files = fixture_documents
    urls = []
    def fake_get(url):
        urls.append(url)
        if url == proto["fixed_source"]["api_dataset_url"]:
            return dataset
        if url == "https://datadryad.org/api/v2/versions/12345/files":
            return files
        raise AssertionError("disallowed API endpoint")
    result = audit(fetch=fake_get, protocol_path=SOURCE)
    assert result["status"] == "SOURCE_METADATA_IDENTITY_QUALIFIED__NO_TRACK_ROWS"
    assert urls == [
        proto["fixed_source"]["api_dataset_url"],
        "https://datadryad.org/api/v2/versions/12345/files",
    ]
    assert not any("/download" in url or "file_stream" in url for url in urls)


@pytest.mark.parametrize("patch, label", [
    ("wrong_doi", "DOI"),
    ("changed_roster", "paths or IDs"),
    ("changed_file_id", "paths or IDs"),
    ("missing_digest", "digestType"),
    ("broken_version", "canonical"),
    ("partial_roster", "incomplete"),
    ("bad_size", "size"),
])
def test_invalid_metadata_fails_closed(fixture_documents, patch, label):
    proto, dataset, files = copy.deepcopy(fixture_documents)
    if patch == "wrong_doi":
        dataset["identifier"] = "doi:10.5061/dryad.WRONG"
    elif patch == "changed_roster":
        files["_embedded"]["stash:files"][0]["path"] = "Unexpected.zip"
    elif patch == "changed_file_id":
        files["_embedded"]["stash:files"][0]["_links"]["self"]["href"] = "/api/v2/files/9988"
    elif patch == "missing_digest":
        files["_embedded"]["stash:files"][0]["digestType"] = ""
    elif patch == "broken_version":
        dataset["_links"]["stash:version"]["href"] = "/api/v2/versions/non-numeric"
    elif patch == "partial_roster":
        files["total"] = 6
    elif patch == "bad_size":
        files["_embedded"]["stash:files"][0]["size"] = -1
    with pytest.raises((ValueError, TypeError), match=label):
        qualify(proto, dataset, files)


def test_failed_source_gate_sets_stop_not_score(fixture_documents):
    proto, dataset, files = fixture_documents
    files["_embedded"]["stash:files"][0]["size"] = -5
    def fake_get(url):
        return dataset if "/datasets/" in url else files
    result = audit(fetch=fake_get, protocol_path=SOURCE)
    assert result["status"] == "HOLD_SOURCE_METADATA_UNVERIFIED"
    assert result["GPS_records_read"] is False
    assert result["ecological_score_computed"] is False
    assert result["followup_payload_access_authorized"] is False
    assert result["EOG_WF_frozen_three_endpoint_denominator_unchanged"] is True


def test_download_endpoints_are_rejected_before_network_io(fixture_documents):
    proto, _, _ = fixture_documents
    for endpoint in (
        "https://datadryad.org/downloads/file_stream/3334126",
        "https://datadryad.org/api/v2/files/3334126/download",
        "https://datadryad.org/api/v2/versions/12345/download",
        "https://example.org/api/v2/versions/12345/files",
    ):
        with pytest.raises(ValueError, match="Refusing non-metadata endpoint"):
            fetch_json(endpoint, pinned_dataset_url=proto["fixed_source"]["api_dataset_url"])


def test_source_contract_declares_no_dense_holdout_authorization(fixture_documents):
    proto, dataset, files = fixture_documents
    assert proto["gate0_authorized_access"]["allowed_only"] == [
        "official publisher DOI metadata JSON",
        "official publisher numeric version's file roster JSON",
    ]
    assert proto["intended_next_stage_NOT_YET_AUTHORIZED"]["dense_2h_holdout_access"] == (
        "PROHIBITED_UNTIL_EXACT_FROZEN_ANALYSIS_AND_MASK_LAYOUT"
    )
    assert proto["claim_boundary"]["new_predictive_endpoint_authorized"] is False
    assert proto["claim_boundary"]["original_EOG_WF_scored"] == 3
    changed = copy.deepcopy(proto)
    changed["status"] = "ALLOW_DATA"
    with pytest.raises(ValueError, match="frozen-before-access"):
        qualify(changed, dataset, files)
