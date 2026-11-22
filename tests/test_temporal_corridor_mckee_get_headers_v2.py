"""Offline controls: a GET may inspect only the first publisher headers."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import runpy

import pytest


HERE = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
ns = runpy.run_path(str(HERE / "qualify_gate1a_get_headers_v2.py"))
validate = ns["validate_protocol"]
audit = ns["audit"]
probe_once = ns["get_only_first_response"]


def fixture():
    return (
        json.loads((HERE / "gate1a_get_headers_v2_protocol.json").read_text()),
        json.loads((HERE / "gate0_publisher_metadata_frozen_v1.json").read_text()),
    )


def test_v2_contract_fixed_after_head_v1_stop_and_before_get():
    protocol, gate0 = fixture()
    rows = validate(protocol, gate0)
    assert protocol["previous_attempt"]["pr"] == 741
    assert protocol["previous_attempt"]["run_id"] == 45029791588
    assert protocol["network_contract"]["method"] == "GET"
    assert protocol["network_contract"]["no_redirect_following"] is True
    assert protocol["network_contract"]["no_response_body_read"] is True
    assert protocol["network_contract"]["no_retry"] is True
    assert protocol["forbidden_file_id"] == 3334126
    assert {r["file_id"] for r in rows} == {3334125, 3334129}


def test_first_redirect_host_only_and_no_source_body():
    urls = []
    def fake(url):
        urls.append(url)
        return {
            "http_status": 302,
            "first_redirect_host": "pinned.example.net",
            "redirect_followed": False,
            "response_body_consumed": False,
            "signed_url_logged": False,
            "signed_download_URL_UNTRUSTED_EXCESS_KEY": "do-not-echo",
        }
    result = audit(probe=fake)
    assert result["status"] == "FIRST_GET_REDIRECT_METADATA_OBSERVED__NO_SOURCE_ROWS"
    assert urls == [
        "https://datadryad.org/downloads/file_stream/3334125",
        "https://datadryad.org/downloads/file_stream/3334129",
    ]
    assert result["results"][0]["first_redirect_host"] == "pinned.example.net"
    assert not any("UNTRUSTED_EXCESS_KEY" in item for item in result["results"])
    assert result["dense_2h_holdout_opened"] is False
    assert result["sparse_12h_GPS_records_opened"] is False
    assert result["gate1b_download_authorized"] is False


def test_direct_200_stops_instead_of_reading_body():
    def direct(url):
        return {
            "http_status": 200,
            "first_redirect_host": "",
            "redirect_followed": False,
            "response_body_consumed": False,
            "signed_url_logged": False,
        }
    result = audit(probe=direct)
    assert result["status"] == "HOLD_TRANSPORT_UNVERIFIED"
    assert result["no_response_body_intentionally_consumed"] is True


def test_broken_transport_contract_stops_without_get():
    calls = []
    def violating(url):
        calls.append(url)
        return {
            "http_status": 302,
            "first_redirect_host": "x.example.org",
            "redirect_followed": True,
            "response_body_consumed": False,
            "signed_url_logged": False,
        }
    result = audit(probe=violating)
    assert result["status"] == "HOLD_TRANSPORT_UNVERIFIED"
    assert len(calls) == 1
    assert result["dense_2h_holdout_opened"] is False


@pytest.mark.parametrize("mutation, phrase", [
    ("version", "Version"),
    ("sha", "file ID/size/hash"),
    ("two_hour", "two pinned"),
    ("follow", "restrictions"),
    ("read", "restrictions"),
    ("retry", "restrictions"),
    ("not_frozen", "pre-access frozen"),
])
def test_frozen_source_mutations_fail_closed(mutation, phrase):
    protocol, gate0 = fixture()
    if mutation == "version":
        protocol["version_id"] = 1
    elif mutation == "sha":
        protocol["requests"][0]["publisher_sha256"] = "0" * 64
    elif mutation == "two_hour":
        protocol["requests"].append({
            "url": "https://datadryad.org/downloads/file_stream/3334126"
        })
    elif mutation == "follow":
        protocol["network_contract"]["no_redirect_following"] = False
    elif mutation == "read":
        protocol["network_contract"]["no_response_body_read"] = False
    elif mutation == "retry":
        protocol["network_contract"]["no_retry"] = False
    elif mutation == "not_frozen":
        protocol["status"] = "MUTABLE"
    with pytest.raises(ValueError, match=phrase):
        validate(protocol, gate0)


def test_unknown_url_is_denied_without_network():
    with pytest.raises(ValueError, match="unpinned source"):
        probe_once("https://datadryad.org/downloads/file_stream/3334126")
