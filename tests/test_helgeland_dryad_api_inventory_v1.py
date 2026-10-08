"""Offline fail-closed contract tests for PUBLIC Dryad JSON metadata inventories.

No bird-level rows, genotype payload, or physical headers are fetched by tests.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_helgeland_dryad_api_inventory_v1.py"


def module():
    spec=importlib.util.spec_from_file_location("helgeland_metadata_api",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mock_record(name):
    m=module()
    vid=123 if name=="fitness_2025" else 124
    doi=m.SOURCES[name]["doi"]
    dataset={
        "identifier":"doi:"+doi,
        "id":456,
        "versionNumber":1,
        "_links":{"stash:version":{"href":f"/api/v2/versions/{vid}"}},
    }
    rows=[
        {"path":name,"digest":"a"*64,"digestType":"sha-256",
         "size":len(name)*127,
         "_links":{"self":{"href":f"/api/v2/files/{900+i}"}}}
        for i,name in enumerate(sorted(m.SOURCES[name]["expected"]))
    ]
    files={
        "_links":{"self":{"href":f"/api/v2/versions/{vid}/files"}},
        "count":len(rows),"total":len(rows),"_embedded":{"stash:files":rows},
    }
    return dataset,files


@pytest.mark.parametrize("name",["fitness_2025","pedigree_2024"])
def test_inventory_proves_metadata_identity_not_file_byte_identity(name):
    m=module()
    d,f=mock_record(name)
    got=m.inventory_from_metadata(name,d,f)
    assert got["doi"]==m.SOURCES[name]["doi"]
    assert got["status"]=="SOURCE_DECLARED_INVENTORY_WITH_SHA256"
    assert len(got["files"])==5
    assert got["source_archive_downloaded"] is False
    assert got["physical_headers_verified"] is False
    assert got["bird_island_join_verified"] is False
    for entry in got["files"]:
        assert entry["sha256_format_valid"] is True
        assert entry["actual_file_header_read"] is False
        assert entry["actual_file_bytes_downloaded"] is False
        assert entry["actual_digest_verified_against_downloaded_bytes"] is False


def test_unknown_or_extra_file_must_not_be_silently_accepted():
    m=module()
    d,files=mock_record("fitness_2025")
    files["_embedded"]["stash:files"][0]["path"]="extra_result_data.txt"
    with pytest.raises(ValueError,match="unexpected Dryad file inventory"):
        m.inventory_from_metadata("fitness_2025",d,files)
    d,files=mock_record("fitness_2025")
    files["total"]=6
    with pytest.raises(ValueError,match="incomplete/paginated"):
        m.inventory_from_metadata("fitness_2025",d,files)


def test_doi_or_version_mismatch_must_stop():
    m=module()
    d,files=mock_record("pedigree_2024")
    d["identifier"]="doi:10.5061/dryad.fake"
    with pytest.raises(ValueError,match="DOI mismatch"):
        m.inventory_from_metadata("pedigree_2024",d,files)
    d,files=mock_record("pedigree_2024")
    files["_links"]["self"]["href"]="/api/v2/versions/999/files"
    with pytest.raises(ValueError,match="version differs"):
        m.inventory_from_metadata("pedigree_2024",d,files)


def test_non_sha256_digests_do_not_pass_digest_classification():
    m=module()
    d,files=mock_record("fitness_2025")
    files["_embedded"]["stash:files"][0]["digestType"]="md5"
    files["_embedded"]["stash:files"][0]["digest"]="c"*32
    out=m.inventory_from_metadata("fitness_2025",d,files)
    assert out["status"]=="SOURCE_DECLARED_INVENTORY_DIGEST_UNQUALIFIED"
    assert out["files"][0]["actual_digest_verified_against_downloaded_bytes"] is False


def test_network_allowlist_rejects_all_biological_file_download_endpoints():
    m=module()
    forbidden=[
        "https://datadryad.org/api/v2/files/123/download",
        "https://datadryad.org/api/v2/versions/123/download",
        "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.qfttdz0sx/download",
        "https://example.org/api/v2/versions/123/files",
        "http://datadryad.org/api/v2/versions/123/files",
        "https://datadryad.org/api/v2/versions/123/files?page=2",
    ]
    for url in forbidden:
        with pytest.raises(ValueError,match="Refusing non-metadata endpoint"):
            m.api_json(url)


def test_script_does_not_import_response_analysis_or_download_helpers():
    s=SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("import pandas","import numpy","read_csv(","/download",
                      "from Bio","import sklearn"):
        # '/download' occurs inside no call even in the docstring for this tool.
        assert forbidden not in s
    assert "individual_or_fitness_records_opened" in s
    assert "source_declared_digest_is_independent_byte_verification" in s
