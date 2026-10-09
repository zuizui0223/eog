"""Fabricated v10 JSON only: no original biological file bytes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_niskanen_v8_v10_source_digest_equivalence_v1 import (
    FROZEN,V10,compare,
)


def fixture():
    frozen=json.loads(FROZEN.read_text(encoding="utf-8"))
    entries=[]
    for i,x in enumerate(frozen["archives"]["niskanen_2020"]["critical_files"]):
        entries.append({
            "path":x["name"],"size":x["size_bytes"],
            "digestType":"sha-256","digest":x["source_digest"],
            "_links":{"self":{"href":f"/api/v2/files/{500000+i}"}},
        })
    doc={
       "_links":{"self":{"href":f"/api/v2/versions/{V10}/files?per_page=100"}},
       "_embedded":{"stash:files":entries},
       "count":len(entries),"total":len(entries),
    }
    return frozen,doc


def test_exact_original_digest_equivalence_only_source_claims():
    pinned,shown=fixture()
    r=compare(pinned,shown)
    assert r["status"]=="ALL_THREE_2020_FILES_HAVE_IDENTICAL_V10_SOURCE_DECLARATIONS"
    assert all(f["sha256_registered_equal"] for f in r["files"])
    assert r["source_file_bytes_downloaded"] is False
    assert r["independent_sha256_of_actual_bytes_verified"] is False
    assert r["ecological_forecast_authorized"] is False
    assert r["never_authorize_use_of_2023_only_files_as_2020_inputs"] is True


@pytest.mark.parametrize("change",["digest","size","type","missing","duplicate","pagination","wrong_version"])
def test_drift_never_passes(change):
    frozen,doc=fixture()
    items=doc["_embedded"]["stash:files"]
    if change=="digest":
        items[0]["digest"]="0"*64
    elif change=="size":
        items[0]["size"]+=1
    elif change=="type":
        items[0]["digestType"]="md5"
    elif change=="missing":
        items.pop()
        doc["count"]=len(items);doc["total"]=len(items)
    elif change=="duplicate":
        items[1]["path"]=items[0]["path"]
    elif change=="pagination":
        doc["total"]+=1
    elif change=="wrong_version":
        doc["_links"]["self"]["href"]="/api/v2/versions/78498/files"
    if change in ("duplicate","pagination","wrong_version"):
        with pytest.raises(ValueError):
            compare(frozen,doc)
    else:
        r=compare(frozen,doc)
        assert r["status"]=="HOLD_NOT_ALL_HISTORICAL_FILES_SAME_AS_2023"
        assert not all(f["sha256_registered_equal"] for f in r["files"])


def test_only_pinned_v8_files_never_2023_added_features():
    frozen,doc=fixture()
    doc["_embedded"]["stash:files"].append({
       "path":"post_2020_hindsight.csv","size":1,"digestType":"sha-256",
       "digest":"f"*64,"_links":{"self":{"href":"/api/v2/files/800001"}}
    })
    doc["total"]+=1;doc["count"]+=1
    result=compare(frozen,doc)
    assert len(result["files"])==3
    assert "post_2020_hindsight.csv" not in json.dumps(result)


def test_real_metadata_comparison_receipt_frozen_with_all_claim_holds():
    frozen=json.loads((
        ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/"
        "helgeland_niskanen_v8_v10_registered_digest_match_frozen_v1.json"
    ).read_text())
    assert frozen["status"]=="ALL_THREE_REGISTERED_DIGESTS_AND_SIZES_IDENTICAL__NO_FILE_BYTES_ACCESSED"
    assert frozen["authority"]["github_actions_run_id"]==37862858112
    assert frozen["authority"]["artifact_id"]==11587525387
    assert frozen["authority"]["artifact_zip_sha256"]==(
        "3e74a16b2a514824262068ba607cc834b1ccb76b1f1d23e830418f103c3852e2")
    assert frozen["source"]["historical_v8_version_id"]==78498
    assert frozen["source"]["later_v10_version_id"]==208617
    assert [(p["name"],p["v10_file_id"]) for p in frozen["pairs"]]==[
        ("Dryad_readme.txt",1952534),
        ("Pop_size_1997_2012.csv",1952533),
        ("Pop_size_1998_2013.csv",1952529)]
    assert all(x["source_reported_sizes_equal"] and x["source_reported_sha256_equal"]
               for x in frozen["pairs"])
    assert frozen["registered_source_digest_is_independent_byte_hash"] is False
    assert frozen["actual_source_file_bytes_downloaded"] is False
    assert frozen["newly_published_2023_only_file_ever_2020_input"] is False
    assert frozen["ecological_forecast_authorized"] is False
