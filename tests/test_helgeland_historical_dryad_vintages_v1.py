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
