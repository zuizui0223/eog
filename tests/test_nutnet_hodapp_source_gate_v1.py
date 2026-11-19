"""Offline tests. These fabricated metadata fixtures contain no experiment response."""
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "benchmarks" / "nutnet_hodapp_source_gate_v1.py"
spec = importlib.util.spec_from_file_location("nutnet_source_gate", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def test_manifest_name_and_integrity_controls():
    payload = {"_embedded": {"stash:files": [
        {"filename": "composition-data.csv", "size": 1510000, "checksum": "a" * 64},
        {"filename": "env-param-Y0.csv", "size": 47600, "checksum": "b" * 32},
    ]}}
    files = mod.find_files(payload)
    assert set(files) == set(mod.EXPECTED)
    assert mod.candidate_state(files, True) == "SOURCE_METADATA_COMPLETE_BYTES_NOT_VERIFIED"
    assert mod.candidate_state(files, False) == "MIRROR_PROVENANCE_UNVERIFIED"
    assert mod.candidate_state({"composition-data.csv": files["composition-data.csv"]}, True) == (
        "SOURCE_STOP_EXPECTED_FILES_MISSING"
    )
    no_hash = {k: dict(v) for k, v in files.items()}
    no_hash["composition-data.csv"]["checksum"] = None
    assert mod.candidate_state(no_hash, True) == "SOURCE_STOP_INCOMPLETE_FILE_INTEGRITY_METADATA"

def test_dryad_version_manifest_qualifies_without_response_access():
    def get(url):
        if url == mod.DATASET_API:
            return {"_links": {"stash:version": {"href": "/api/v2/versions/42"}}}, "HTTP_200_JSON"
        if url.endswith("/api/v2/versions/42/files"):
            return {"_embedded": {"stash:files": [
                {"filename": "composition-data.csv", "size": 1510000, "checksum": "a" * 32},
                {"filename": "env-param-Y0.csv", "size": 47600, "checksum": "b" * 32},
            ]}}, "HTTP_200_JSON"
        raise AssertionError("unexpected metadata endpoint " + url)
    r = mod.run(get)
    assert r["status"] == "SOURCE_METADATA_COMPLETE_BYTES_NOT_VERIFIED"
    assert r["actual_intervention_signs_scored"] == 0
    assert r["post_treatment_cover_rows_opened"] == 0
    assert len(r["source_requests"]) == 2

def test_unavailable_dryad_mirror_is_not_authoritative():
    def get(url):
        if url == mod.DATASET_API:
            return None, "HTTP_403"
        if url == mod.MIRROR_API:
            return {"files": [
                {"key": "composition-data.csv", "size": 1510000, "checksum": "a" * 32},
                {"key": "env-param-Y0.csv", "size": 47600, "checksum": "b" * 32},
            ]}, "HTTP_200_JSON"
        raise AssertionError(url)
    r = mod.run(get)
    assert r["status"] == "MIRROR_PROVENANCE_UNVERIFIED"
    assert r["catalogue"].startswith("Zenodo")
    assert r["actual_intervention_signs_scored"] == 0

def test_complete_source_stop_when_no_metadata():
    r = mod.run(lambda url: (None, "HTTP_403"))
    assert r["status"] == "SOURCE_STOP_EXPECTED_FILES_MISSING"
    assert r["identified_file_metadata"] == {}
