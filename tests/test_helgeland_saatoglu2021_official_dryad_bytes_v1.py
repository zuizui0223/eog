"""Synthetic and source-metadata-only checks, never fetch real bird records."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from probe_helgeland_saatoglu2021_official_dryad_bytes_v1 import (
    SCHEMA, classify_bytes, inspect_http_file, run, INVENTORY,
)


def fixture():
    return json.loads(INVENTORY.read_text(encoding="utf-8"))


def test_fabricated_exact_sha256_receipt_has_no_raw_source_data():
    raw = b"fictional-not-biological-rows"
    f = {"id": 99, "name": "fictional.txt", "size_bytes": len(raw),
         "declared_sha256": hashlib.sha256(raw).hexdigest()}
    calls = []
    def provider(url, limit):
        calls.append(url)
        assert limit == len(raw) + 1
        return 200, "text/plain", raw
    result = inspect_http_file(f, provider)
    assert result["byte_verified"] is True
    assert len(calls) == 1
    assert len(result["attempts"]) == 1
    assert "fictional-not-biological" not in json.dumps(result)


def test_exact_size_wrong_digest_does_not_pass():
    raw = b"fictional-not-biological-rows"
    assert classify_bytes(raw, len(raw), "0" * 64, "text/plain") == (
        "ORIGINAL_BYTES_SHA256_MISMATCH"
    )
    assert classify_bytes(raw, len(raw) + 1, hashlib.sha256(raw).hexdigest()) == (
        "ORIGINAL_BYTES_SIZE_MISMATCH"
    )
    assert classify_bytes(raw, len(raw), hashlib.sha256(raw).hexdigest(), "text/html") == (
        "CHALLENGE_OR_HTML_NOT_SOURCE"
    )


def test_unauthorized_401_stops_no_credential_fallback():
    f = {"name":"notreal.txt","id":99,"size_bytes":3,"declared_sha256":"0"*64}
    calls = []
    def provider(url, limit):
        calls.append(url)
        raise HTTPError(url, 401, "unauthorized", {}, None)
    x = inspect_http_file(f, provider)
    assert x["byte_verified"] is False
    assert x["attempts"][0]["http_status"] == 401
    assert x["attempts"][0]["outcome"] == "ACCESS_DENIED_STOP"
    assert len(calls) == 1
    assert "download" not in calls[0]


def test_public_404_may_consult_only_second_fixed_official_route():
    f = {"name":"notreal.txt","id":99,"size_bytes":3,"declared_sha256":"0"*64}
    calls = []
    def provider(url, limit):
        calls.append(url)
        raise HTTPError(url, 404, "not found", {}, None)
    z = inspect_http_file(f, provider)
    assert z["byte_verified"] is False
    assert len(calls) == 2
    assert all("datadryad.org/" in url for url in calls)


def test_html_challenge_200_does_not_try_to_bypass():
    f = {"name":"notreal.txt","id":99,"size_bytes":3,"declared_sha256":"0"*64}
    calls=[]
    def fake(url, limit):
        calls.append(url)
        return 200,"text/html",b"<h1>Validating</h1>"
    z=inspect_http_file(f,fake)
    assert not z["byte_verified"]
    assert len(calls)==1
    assert z["attempts"][0]["outcome"]=="CHALLENGE_OR_HTML_NOT_SOURCE"


def test_original_manifest_and_denied_readme_blocks_2021_other_file_access():
    meta=fixture()
    calls=[]
    def denied(url, limit):
        calls.append(url)
        return 403,"text/plain",b""
    result=run(meta,denied)
    assert result["schema"]==SCHEMA
    assert result["status"]=="PUBLIC_ACCESS_DIAGNOSTIC_ONLY__SOME_OR_ALL_ORIGINAL_BYTES_NOT_VERIFIED"
    assert result["verified_file_count"]==0
    assert result["five_files_verified"] is False
    assert len(calls)==1
    assert len(result["files_checked"])==1
    assert result["files_checked"][0]["name"]=="Geneticassignment_README.txt"
    for required in (
        "original_2021_record_headers_or_bird_values_read",
        "individual_ID_join_or_genetic_assignments_scored",
        "source_available_at_2014_forecast_cutoff",
        "new_EOG_WF_endpoint_scored",
        "raw_source_file_bytes_persisted_or_exported",
        "access_denial_bypassed",
    ):
        assert result[required] is False


def test_source_metadata_identity_changes_fail_closed():
    p=fixture()
    p["official_dryad"]["version_id"]=133
    with pytest.raises(ValueError,match="original Dryad"):
        run(p,lambda a,b: (401,"",b""))
    p=fixture()
    p["official_dryad"]["files"].pop()
    with pytest.raises(ValueError,match="five unique"):
        run(p,lambda a,b: (401,"",b""))


def test_script_source_never_uses_credentials_or_bird_value_parsers():
    s=(ROOT/"scripts/probe_helgeland_saatoglu2021_official_dryad_bytes_v1.py").read_text()
    for forbidden in ("Authorization:", "Bearer ", "cookiejar", "browser_profile",
                      "read_csv(", "csv.DictReader", "eval(", "BeautifulSoup"):
        assert forbidden not in s
