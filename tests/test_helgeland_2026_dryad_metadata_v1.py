"""Synthetic JSON fixtures only: no source files, bird observations or HTTP requests."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_helgeland_2026_dryad_metadata_v1.py"
sys.path.insert(0, str(ROOT / "scripts"))


def module():
    spec = importlib.util.spec_from_file_location("helgeland_dryad_2026_public_only", SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mock_json():
    m = module()
    version = 654321
    dataset = {
        "id": 987654,
        "identifier": "doi:" + m.DOI,
        "versionNumber": 1,
        "_links": {"stash:version": {"href": f"/api/v2/versions/{version}"}},
    }
    entries = [
        {
            "path": name, "size": 100 + i,
            "digest": "a" * 64, "digestType": "sha-256",
            "_links": {"self": {"href": f"/api/v2/files/{700000 + i}"}},
        }
        for i, name in enumerate(sorted(m.EXPECTED))
    ]
    files = {
        "_links": {"self": {"href": f"/api/v2/versions/{version}/files"}},
        "count": len(entries), "total": len(entries),
        "_embedded": {"stash:files": entries},
    }
    return dataset, files


def test_18_files_only_metadata_no_bird_rows_and_no_unearned_endpoint():
    m = module()
    dataset, files = mock_json()
    result = m.qualify(dataset, files)
    assert len(m.EXPECTED) == 18
    assert result["status"] == "PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED"
    assert result["file_count"] == 18
    assert result["dryad_version_id"] == 654321
    assert result["dryad_dataset_id"] == 987654
    assert result["source_reported_digest_is_independent_byte_verification"] is False
    for name in ("raw_bird_data_downloaded", "individual_or_population_observations_read",
                 "surveyed_zero_panel_verified", "as_of_t_processing_verified",
                 "ecological_endpoint_authorized"):
        assert result[name] is False
    for entry in result["files"]:
        assert entry["file_bytes_downloaded"] is False
        assert entry["physical_header_read"] is False
        assert entry["biological_rows_read"] is False
        assert entry["digest_verified_against_file_bytes"] is False


@pytest.mark.parametrize("mutation", [
    "doi", "version", "pagination", "missing", "extra", "duplicate_name",
    "file_meta_id", "duplicate_file_meta_id", "empty_file_size",
])
def test_identity_conflicts_fail_closed(mutation):
    m = module()
    dataset, files = mock_json()
    if mutation == "doi":
        dataset["identifier"] = "doi:10.5061/dryad.unrelated"
    elif mutation == "version":
        files["_links"]["self"]["href"] = "/api/v2/versions/999/files"
    elif mutation == "pagination":
        files["total"] += 1
    elif mutation == "missing":
        files["_embedded"]["stash:files"].pop()
        files["count"] -= 1
        files["total"] -= 1
    elif mutation == "extra":
        files["_embedded"]["stash:files"][0]["path"] = "unexpected_bird_data.txt"
    elif mutation == "duplicate_name":
        rows = files["_embedded"]["stash:files"]
        rows[1]["path"] = rows[0]["path"]
    elif mutation == "file_meta_id":
        files["_embedded"]["stash:files"][0]["_links"]["self"]["href"] = "/download/1"
    elif mutation == "duplicate_file_meta_id":
        rows = files["_embedded"]["stash:files"]
        rows[1]["_links"]["self"]["href"] = rows[0]["_links"]["self"]["href"]
    elif mutation == "empty_file_size":
        files["_embedded"]["stash:files"][0]["size"] = 0
    with pytest.raises(ValueError):
        m.qualify(dataset, files)


def test_no_digest_is_never_misrepresented_as_verified_bytes():
    m = module()
    dataset, files = mock_json()
    files["_embedded"]["stash:files"][0]["digestType"] = "md5"
    files["_embedded"]["stash:files"][0]["digest"] = "b" * 32
    result = m.qualify(dataset, files)
    assert result["status"] == "HOLD_SOURCE_DIGEST_INCOMPLETE"
    assert result["source_reported_digest_is_independent_byte_verification"] is False
    assert not result["files"][0]["source_declared_sha256_well_formed"]


def test_audit_uses_only_two_metadata_endpoints():
    m = module()
    dataset, files = mock_json()
    called = []

    def metadata_only_fetch(url):
        called.append(url)
        if url == "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.rr4xgxdnq":
            return dataset
        if url == "https://datadryad.org/api/v2/versions/654321/files":
            return files
        raise AssertionError("Undeclared URL: " + url)

    result = m.audit(metadata_only_fetch)
    assert result["status"] == "PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED"
    assert len(called) == 2
    assert all("/download" not in url for url in called)


def test_api_failure_stays_hold_and_never_unlocks_ecology():
    m = module()

    def offline(_url):
        raise TimeoutError("synthetic network unavailable")

    result = m.audit(offline)
    assert result["status"] == "HOLD_SOURCE_METADATA_UNVERIFIED"
    assert result["raw_bird_data_downloaded"] is False
    assert result["ecological_endpoint_authorized"] is False


def test_existing_endpoint_allowlist_refuses_file_downloads():
    m = module()
    for url in (
        "https://datadryad.org/api/v2/files/123/download",
        "https://datadryad.org/api/v2/versions/123/download",
        "http://datadryad.org/api/v2/versions/123/files",
        "https://other.example/api/v2/versions/123/files",
    ):
        with pytest.raises(ValueError, match="Refusing non-metadata endpoint"):
            m.api_json(url)


def test_no_observation_parsing_or_download_implementation_in_auditor():
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("read_csv(", "import pandas", "import numpy",
                      "import sklearn", "socket.socket(", "/download",
                      "subprocess", "import requests"):
        assert forbidden not in source
    assert "raw_bird_data_downloaded" in source
    assert "ecological_endpoint_authorized" in source


def test_frozen_2026_v6_identities_can_be_verified_without_file_bytes():
    import json
    m = module()
    frozen_path = (ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
                   / "helgeland_2026_source_metadata_frozen_v1.json")
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    assert frozen["dryad_dataset_id"] == 177360
    assert frozen["dryad_version_id"] == 421942
    assert frozen["dryad_version_number"] == 6
    assert len(frozen["files"]) == 18
    assert frozen["authority"]["github_actions_artifact_id"] == 11556844942
    assert frozen["authority"]["artifact_zip_sha256"] == (
        "aa0a7f0ff034ac8d254f3633d5e7b2e2a8a32e5285520e4906d3071ca33d76d4"
    )

    observed = {
        "schema": m.SCHEMA,
        "status": "PUBLIC_METADATA_IDENTITY_RETRIEVED_SHA256_DECLARED",
        "source_doi": frozen["source_doi"],
        "dryad_dataset_id": frozen["dryad_dataset_id"],
        "dryad_version_id": frozen["dryad_version_id"],
        "dryad_version_number": frozen["dryad_version_number"],
        "files": [{
            "name": x["name"],
            "file_metadata_id": x["file_metadata_id"],
            "size_bytes": x["size_bytes"],
            "source_declared_digest_type": x["source_declared_digest_type"],
            "source_declared_digest": x["source_declared_sha256"],
            "source_declared_sha256_well_formed": True,
        } for x in frozen["files"]],
        "raw_bird_data_downloaded": False,
        "individual_or_population_observations_read": False,
        "surveyed_zero_panel_verified": False,
        "as_of_t_processing_verified": False,
        "ecological_endpoint_authorized": False,
    }
    verdict = m.verify_against_frozen(observed, frozen)
    assert verdict["status"] == "MATCHES_FROZEN_DRYAD_2026_V6_PUBLIC_JSON"
    assert verdict["ecological_endpoint_authorized"] is False
    assert verdict["source_reported_digests_are_not_independent_byte_verification"] is True

    for kind in ("version", "dataset", "file_digest", "file_id", "wrong_size",
                 "missing", "wrong_digest_type", "biological_claim"):
        changed = copy.deepcopy(observed)
        if kind == "version":
            changed["dryad_version_id"] = 0
        elif kind == "dataset":
            changed["dryad_dataset_id"] = 0
        elif kind == "file_digest":
            changed["files"][0]["source_declared_digest"] = "f" * 64
        elif kind == "file_id":
            changed["files"][0]["file_metadata_id"] = 0
        elif kind == "wrong_size":
            changed["files"][0]["size_bytes"] += 1
        elif kind == "missing":
            changed["files"].pop()
        elif kind == "wrong_digest_type":
            changed["files"][0]["source_declared_digest_type"] = "md5"
        elif kind == "biological_claim":
            changed["ecological_endpoint_authorized"] = True
        with pytest.raises(ValueError):
            m.verify_against_frozen(changed, frozen)
