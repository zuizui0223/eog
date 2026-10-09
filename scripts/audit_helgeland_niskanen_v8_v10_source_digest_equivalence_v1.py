#!/usr/bin/env python3
"""Metadata-only comparison of 2020-v8 and 2023-v10 Dryad *individual file* digests.

The 2023 release may contain the SAME bytes as already published in 2020,
but never treat same filename/size as sufficient. Requires EXACT registered
SHA256 of each specific 2020-v8 file; never downloads bird or abundance rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from audit_helgeland_historical_dryad_vintages_v1 import api_json

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/helgeland_historical_public_vintages_frozen_v1.json"
SOURCE_DOI="10.5061/dryad.m0cfxpp10"
V8=78498
V10=208617


def compare(frozen: dict, v10: dict) -> dict:
    if frozen.get("schema") != "eog.helgeland.historical_public_dryad_versions.frozen_observed_v1":
        raise ValueError("Frozen historical source contract missing")
    pre=frozen["archives"]["niskanen_2020"]
    if pre["doi"]!=SOURCE_DOI or pre["version_id"]!=V8 or pre["version_number"]!=8:
        raise ValueError("2020-source identity mismatch")
    if not any(x["version_id"]==V10 and x["published_date"]=="2023-01-19"
               for x in pre["version_history"]):
        raise ValueError("Later source version not frozen")
    if v10.get("_links",{}).get("self",{}).get("href") not in (
        f"/api/v2/versions/{V10}/files",
        f"/api/v2/versions/{V10}/files?per_page=100",
    ):
        raise ValueError("Wrong or ambiguous later-version file listing")
    records=v10.get("_embedded",{}).get("stash:files")
    if (not isinstance(records,list) or
        v10.get("total")!=len(records) or v10.get("count")!=len(records)):
        raise ValueError("2023 list is incomplete or paginated")
    name_map={}
    for r in records:
        name=r.get("path")
        if not isinstance(name,str) or name in name_map:
            raise ValueError("Missing or duplicate 2023 file name")
        name_map[name]=r
    observed=[]
    for pin in pre["critical_files"]:
        name=pin["name"]
        item=name_map.get(name)
        if not item:
            observed.append({"name":name,"status":"HOLD_NOT_IN_LATER_VERSION",
                             "sha256_registered_equal":False})
            continue
        item_digest=item.get("digest")
        item_type=item.get("digestType")
        source_sha=pin["source_digest"]
        equal=(item_type=="sha-256" and pin["source_digest_type"]=="sha-256"
               and isinstance(item_digest,str) and
               item_digest.lower()==source_sha.lower() and
               item.get("size")==pin["size_bytes"])
        observed.append({
          "name":name,
          "v8_file_metadata_id":pin["file_id"],
          "v8_published_date":"2020-08-19",
          "v8_source_sha256":source_sha,
          "v10_file_metadata_id":int(item.get("_links",{}).get("self",{}).get("href","-1").rsplit("/",1)[-1]),
          "v10_published_date":"2023-01-19",
          "v10_registered_size":item.get("size"),
          "sha256_registered_equal":equal,
          "status":"SOURCE_REGISTERED_SHA256_AND_SIZE_EQUAL__BYTES_NOT_DOWNLOADED" if equal
                    else "HOLD_SOURCE_REGISTERED_DIGEST_DIFFERENT",
        })
    return {
       "schema":"eog.helgeland.v8_v10.published_file_registered_digest_comparison.v1",
       "status":"ALL_THREE_2020_FILES_HAVE_IDENTICAL_V10_SOURCE_DECLARATIONS"
                if all(r["sha256_registered_equal"] for r in observed)
                else "HOLD_NOT_ALL_HISTORICAL_FILES_SAME_AS_2023",
       "2020_original_version_id":V8,
       "2023_later_version_id":V10,
       "files":observed,
       "source_file_bytes_downloaded":False,
       "independent_sha256_of_actual_bytes_verified":False,
       "never_authorize_use_of_2023_only_files_as_2020_inputs":True,
       "historical_model_features_read":False,
       "island_year_sampled_zero_verified":False,
       "ecological_forecast_authorized":False,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    frozen=json.loads(FROZEN.read_text(encoding="utf-8"))
    latest=api_json(f"https://datadryad.org/api/v2/versions/{V10}/files?per_page=100")
    result=compare(frozen,latest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2,sort_keys=True,ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status":result["status"],"files_compared":len(result["files"])}))


if __name__=="__main__":
    main()
