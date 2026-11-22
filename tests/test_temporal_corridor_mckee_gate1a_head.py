"""Offline tests for HEAD-only Dryad first-redirect preflight."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "validation/temporal_corridor_mckee2024"
FUNCTIONS = runpy.run_path(str(FOLDER / "qualify_gate1a_head_only.py"))
PROTOCOL = FOLDER / "gate1a_redirect_head_protocol_v1.json"
FROZEN = FOLDER / "gate0_publisher_metadata_frozen_v1.json"
validate = FUNCTIONS["_validate_protocol"]
audit = FUNCTIONS["audit"]
head_once = FUNCTIONS["_head_once"]


def fixture_sources():
    return json.loads(PROTOCOL.read_text()), json.loads(FROZEN.read_text())


def test_protocol_uses_two_pinned_head_targets_and_excludes_dense_holdout():
    protocol, frozen = fixture_sources()
    targets = validate(protocol, frozen)
    assert {x["file_id"] for x in targets} == {3334125, 3334129}
    assert {x["name"] for x in targets} == {"GPS12hrs_Locs.zip", "README.md"}
    assert protocol["network_contract"]["method"] == "HEAD"
    assert protocol["network_contract"]["follow_any_redirect"] is False
    assert 3334126 in {
        x["file_id"] for x in protocol["explicitly_forbidden_files"]
    }


def test_head_metadata_receipt_records_hosts_only_and_no_bytes():
    called = []
    def fake_head(url):
        called.append(url)
        return {
            "http_status": 302,
            "redirect_present": True,
            "first_redirect_host": "example.lambda-url.us-west-2.on.aws",
            "publisher_header_content_type": None,
            "publisher_header_content_length": 123,
            "source_body_read": False,
            "redirect_followed": False,
            "signed_redirect_url_logged": False,
        }
    result = audit(head=fake_head)
    assert result["status"] == "HEAD_FIRST_HOP_METADATA_RETRIEVED__NO_FILE_BYTES"
    assert len(called) == 2
    assert not any("3334126" in url for url in called)
    assert all(row["first_redirect_host"] == "example.lambda-url.us-west-2.on.aws" for row in result["records"])
    assert result["source_byte_downloads_performed"] is False
    assert result["GPS_rows_or_headers_read"] is False
    assert result["dense_2h_holdout_opened"] is False
    assert result["next_stage_download_authorized"] is False


def test_head_200_direct_response_without_redirect_is_a_metadata_only_receipt():
    def fake_head(url):
        return {
            "http_status": 200,
            "redirect_present": False,
            "first_redirect_host": None,
            "publisher_header_content_type": "application/zip",
            "publisher_header_content_length": 1024,
            "source_body_read": False,
            "redirect_followed": False,
            "signed_redirect_url_logged": False,
        }
    result = audit(head=fake_head)
    assert result["status"].startswith("HEAD_FIRST_HOP_METADATA_RETRIEVED")
    assert result["source_byte_downloads_performed"] is False


def test_probe_must_not_follow_redirect_or_read_source_bytes():
    for forbidden_fields in (
        {"redirect_followed": True},
        {"source_body_read": True},
        {"signed_redirect_url_logged": True},
    ):
        def fake_head(url):
            return {
                "http_status": 302,
                "first_redirect_host": "example.net",
                "source_body_read": False,
                "redirect_followed": False,
                "signed_redirect_url_logged": False,
                **forbidden_fields,
            }
        result = audit(head=fake_head)
        assert result["status"] == "HOLD_SOURCE_TRANSPORT_UNVERIFIED"
        assert result["source_byte_downloads_performed"] is False
        assert result["next_stage_download_authorized"] is False


def test_deny_all_non_approved_source_urls_before_http_request():
    for url in (
        "https://datadryad.org/downloads/file_stream/3334126",
        "https://datadryad.org/api/v2/files/3334125/download",
        "https://foo.example/downloads/file_stream/3334125",
    ):
        with pytest.raises(ValueError, match="unpinned HEAD source"):
            head_once(url)


@pytest.mark.parametrize("mutation, match", [
    ("wrong_version", "version"),
    ("wrong_sha", "hash"),
    ("holdout_in_approved", "Exactly two|Unexpected|changed"),
    ("allow_get", "Only HEAD"),
    ("follow_redirects", "Redirect following"),
    ("read_body", "Body access"),
    ("not_frozen", "not frozen"),
])
def test_mutated_protocol_fails_before_network(mutation, match):
    protocol, frozen = fixture_sources()
    if mutation == "wrong_version":
        protocol["parent_gate0_version_id"] = 111
    if mutation == "wrong_sha":
        protocol["fixed_eligible_files"][0]["sha256"] = "0" * 64
    if mutation == "holdout_in_approved":
        protocol["fixed_eligible_files"].append({
            "name": "GPS2hrs_Locs.zip", "file_id": 3334126,
            "url": "https://datadryad.org/downloads/file_stream/3334126",
        })
    if mutation == "allow_get":
        protocol["network_contract"]["method"] = "GET"
    if mutation == "follow_redirects":
        protocol["network_contract"]["follow_any_redirect"] = True
    if mutation == "read_body":
        protocol["network_contract"]["do_not_open_response_body"] = False
    if mutation == "not_frozen":
        protocol["status"] = "OPEN"
    with pytest.raises(ValueError, match=match):
        validate(protocol, frozen)


def test_transport_errors_hold_without_fallback_or_source_reads():
    called = []
    def fake_head(url):
        called.append(url)
        raise OSError("mock network failure")
    result = audit(head=fake_head)
    assert result["status"] == "HOLD_SOURCE_TRANSPORT_UNVERIFIED"
    assert result["error_type"] == "OSError"
    assert called == ["https://datadryad.org/downloads/file_stream/3334125"]
    assert result["source_byte_downloads_performed"] is False
    assert result["dense_2h_holdout_opened"] is False
