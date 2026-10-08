"""All fixtures are manufactured public JSON metadata, not bird data."""
from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_helgeland_historical_dryad_vintages_v1.py"


def module():
    spec=importlib.util.spec_from_file_location("eog_dryad_historical_vintages",SCRIPT)
    m=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=m
    spec.loader.exec_module(m)
    return m


def versions():
    return {
        "total":2,
        "_embedded":{"stash:versions":[
            {"publicationDate":"2020-07-15","versionNumber":1,
             "_links":{"self":{"href":"/api/v2/versions/150001"}}},
            {"publicationDate":"2023-01-19","versionNumber":2,
             "_links":{"self":{"href":"/api/v2/versions/250001"}}},
        ]}
    }


def files(names,version=150001):
    entries=[]
    for i,name in enumerate(sorted(names)):
        entries.append({
            "path":name,"size":101+i,
            "digestType":"sha-256","digest":"a"*64,
            "_links":{"self":{"href":f"/api/v2/files/{300+i}"}},
        })
    return {"total":len(entries),"count":len(entries),
            "_links":{"self":{"href":f"/api/v2/versions/{version}/files"}},
            "_embedded":{"stash:files":entries}}


def test_as_of_2020_uses_2020_version_not_2023():
    m=module()
    chosen,all_versions=m.choose_asof_version(m.SOURCES["niskanen_2020"],versions())
    assert chosen["version_id"]==150001
    assert chosen["published_date"]=="2020-07-15"
    assert len(all_versions)==2
    assert chosen["version_id"]!=250001


def test_2014_version_selection_ignores_future_data():
    m=module()
    v=versions()
    v["_embedded"]["stash:versions"].insert(0,{
        "publicationDate":"2014-04-24","versionNumber":1,
        "_links":{"self":{"href":"/api/v2/versions/140001"}},
    })
    v["total"]=3
    chosen,_=m.choose_asof_version(m.SOURCES["baalsrud_2014"],v)
    assert chosen["version_id"]==140001


def test_missing_historically_required_file_stops():
    m=module()
    chosen={"version_id":150001,"published_date":"2020-07-15","version_number":1}
    with pytest.raises(ValueError,match="preregistered baseline filenames"):
        m.qualify_file_inventory(m.SOURCES["niskanen_2020"],chosen,
                                 files(["Pop_size_1997_2012.csv"]))


def test_historical_list_pagination_stops():
    m=module()
    v=versions()
    v["total"]=3
    with pytest.raises(ValueError,match="incomplete"):
        m.choose_asof_version(m.SOURCES["niskanen_2020"],v)


def test_no_pre_cutoff_version_stops():
    m=module()
    with pytest.raises(ValueError,match="No version demonstrably published"):
        m.choose_asof_version(m.SOURCES["baalsrud_2014"],versions())


def test_readonly_audit_never_follows_later_2023_update():
    m=module()
    urls=[]
    def fetch(u):
        urls.append(u)
        if "nb260/versions" in u:
            return {"total":1,"_embedded":{"stash:versions":[{
                "publicationDate":"2014-04-24","versionNumber":1,
                "_links":{"self":{"href":"/api/v2/versions/140001"}},
            }]}}
        if "m0cfxpp10/versions" in u:
            return versions()
        if "/140001/files" in u:
            return files(m.SOURCES["baalsrud_2014"]["expected_files"],140001)
        if "/150001/files" in u:
            return files(m.SOURCES["niskanen_2020"]["expected_files"],150001)
        raise AssertionError("Refuse unexpected URL: "+u)
    result=m.audit(fetch)
    assert result["status"]=="BOTH_HISTORICAL_PUBLIC_METADATA_VINTAGES_IDENTIFIED"
    assert len(urls)==4
    assert "/versions/250001/files" not in "|".join(urls)
    assert all("per_page=100" in url for url in urls if "/files" in url)
    assert result["actual_biological_file_bytes_read"] is False
    assert result["ecological_scoring_authorized"] is False
    assert len(result["datasets"]["niskanen_2020"]["versions_after_cutoff_not_eligible"])==1


def test_unavailable_archive_is_explicit_hold_not_invented_metadata():
    m=module()
    def error(_):
        raise TimeoutError("synthetic metadata source unavailable")
    result=m.audit(error)
    assert result["status"]=="HOLD_INCOMPLETE_HISTORICAL_PUBLIC_VINTAGES"
    assert result["datasets"]["niskanen_2020"]["status"]=="HOLD_HISTORICAL_SOURCE_VERSION_UNVERIFIED"
    assert result["individual_bird_rows_read"] is False


def test_network_allowlist_never_loads_biological_file_urls():
    m=module()
    for url in (
      "https://datadryad.org/api/v2/files/123/download",
      "https://datadryad.org/api/v2/versions/150001/download",
      "https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.nb260/download",
      "https://other.example/api/v2/versions/150001/files",
      "http://datadryad.org/api/v2/versions/150001/files",
      "https://datadryad.org/api/v2/versions/150001/files?page=2",
      "https://datadryad.org/api/v2/versions/150001/files?per_page=500",
      "https://datadryad.org/api/v2/versions/150001/files?per_page=100&page=2",
    ):
        with pytest.raises(ValueError,match="Refusing endpoint"):
            m.api_json(url)


def test_no_2020_readers_or_biological_scores():
    source=SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("read_csv(", "import pandas", "import numpy",
                      "from Bio", "import sklearn", "socket.socket("):
        assert forbidden not in source
    assert "ecological_scoring_authorized" in source
    assert "versions_after_cutoff_not_eligible" in source


def test_full_catalog_fingerprint_rejects_historical_source_mutation():
    m=module()
    from json import loads
    frozen=loads((
        ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/"
        "helgeland_historical_public_vintages_frozen_v1.json"
    ).read_text(encoding="utf-8"))
    assert frozen["archives"]["baalsrud_2014"]["version_id"]==5191
    assert frozen["archives"]["niskanen_2020"]["version_id"]==78498
    assert frozen["archives"]["niskanen_2020"]["file_count"]==22
    assert frozen["archives"]["niskanen_2020"]["version_history"][-1]=={
        "published_date":"2023-01-19","version_id":208617,"version_number":10
    }
    assert frozen["authority"]["github_actions_run_id"]==37856758562
    assert frozen["authority"]["artifact_id"]==11584312291
    assert frozen["authority"]["artifact_zip_sha256"]==(
        "fbe9e500a023e7b45b2da2d91b8a35ac39a7488a2873b651ee62527d2b1b46b1"
    )
    assert all(v["critical_files"] for v in frozen["archives"].values())
    assert frozen["source_reported_digest_independently_verified"] is False
    assert frozen["prospective_EOG_model_or_heldout_score_authorized"] is False

    observed={"status":"BOTH_HISTORICAL_PUBLIC_METADATA_VINTAGES_IDENTIFIED",
              "datasets":{}}
    for key,base in frozen["archives"].items():
        records=[{
            "name":c["name"],"file_id":c["file_id"],
            "source_reported_bytes":c["size_bytes"],
            "source_reported_digest_type":c["source_digest_type"],
            "source_reported_digest":c["source_digest"],
        } for c in base["critical_files"]]
        # This synthetic mock has only the declared key records and needs a
        # corresponding synthetic fingerprint; it is not the actual full catalog.
        mock_baseline=copy.deepcopy(base)
        mock_baseline["file_count"]=len(records)
        mock_baseline["canonical_full_file_metadata_sha256"]=m.canonical_files_sha256(records)
        observed["datasets"][key]={
            "doi":base["doi"],"historical_cutoff":base["cutoff"],
            "selected":{"version_id":base["version_id"],
                        "version_number":base["version_number"],
                        "published_date":base["published_date"]},
            "file_count":len(records),"files":records,
            "published_version_history":base["version_history"],
            "actual_source_file_bytes_read":False,
            "ecological_endpoint_authorized":False,
            "source_files_at_cutoff_qualified_as_model_features":False,
        }
        frozen["archives"][key]=mock_baseline
    assert m.verify_against_frozen(observed,frozen)["status"]==(
        "MATCHES_FROZEN_2014_V1_AND_2020_V8_PUBLIC_VERSION_METADATA"
    )
    mutated=copy.deepcopy(observed)
    mutated["datasets"]["niskanen_2020"]["files"][1]["source_reported_bytes"]+=1
    with pytest.raises(ValueError,match="catalog changed"):
        m.verify_against_frozen(mutated,frozen)
    mutated=copy.deepcopy(observed)
    mutated["datasets"]["niskanen_2020"]["selected"]["version_id"]=208617
    with pytest.raises(ValueError,match="historical version changed"):
        m.verify_against_frozen(mutated,frozen)
