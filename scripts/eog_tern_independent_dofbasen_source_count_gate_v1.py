#!/usr/bin/env python3
"""Independent DOF/BirdLife GBIF historical Arctic Tern source count gate (stage 0).

Counts coordinate-bearing species occurrences from this *external* volunteer
observation dataset by five fixed time windows, before any records are read.
A nonzero presence count DOES NOT verify breeding or contemporaneous source
availability. No term-level records, site identities or ringed bird events
are accessed. All official request URLs/filters were protocol-frozen first.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

PROTOCOL=Path("validation/tern_independent_dofbasen_breeding_gate_v1/protocol_v1.json")
BASE="https://api.gbif.org/v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest_document(obj: object) -> str:
    return _sha((json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode("utf-8"))


def _get_official_json(url: str, *, byte_cap:int, timeout:int) -> tuple[dict[str,Any],str]:
    parsed=urllib.parse.urlsplit(url)
    if parsed.scheme!="https" or parsed.hostname!="api.gbif.org" or parsed.username or parsed.password:
        raise ValueError("STOP_UNDECLARED_GBIF_HOST")
    request=urllib.request.Request(url,headers={"User-Agent":"EOG-independent-tern-source-only/1.0",
                                                  "Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=timeout) as resp:
        final=urllib.parse.urlsplit(resp.geturl())
        if final.scheme!="https" or final.hostname!="api.gbif.org":
            raise ValueError("STOP_GBIF_UNVERIFIED_REDIRECT")
        content=resp.read(byte_cap+1)
        if len(content)>byte_cap:
            raise ValueError("STOP_GBIF_METADATA_BYTE_CAP")
    value=json.loads(content)
    if not isinstance(value,dict):
        raise ValueError("STOP_GBIF_SCHEMA_NOT_OBJECT")
    return value,_sha(content)


def _publisher_doi_is_present(data: dict[str,Any], doi:str) -> bool:
    candidates=[]
    for key in ("doi","identifier","datasetDOI"):
        if data.get(key):
            candidates.append(str(data[key]))
    for row in data.get("identifiers") or []:
        if isinstance(row,dict):
            candidates.append(str(row.get("identifier") or row.get("doi") or ""))
    for row in data.get("alternativeIdentifiers") or []:
        if isinstance(row,dict):
            candidates.append(str(row.get("identifier") or ""))
    normalized=lambda s:s.lower().removeprefix("https://doi.org/").removeprefix("doi:").strip()
    return any(normalized(s)==doi.lower() for s in candidates)


def _validate_source(spec:dict[str,Any], dataset:dict[str,Any],
                     species:dict[str,Any]) -> tuple[int,dict[str,Any]]:
    expected=spec["external_dataset"]
    if str(dataset.get("key") or "")!=expected["gbif_dataset_uuid"]:
        raise ValueError("STOP_DATASET_UUID_CHANGED")
    title=str(dataset.get("title") or "")
    if "DOF" not in title or "DOFbasen" not in title:
        raise ValueError("STOP_DATASET_PUBLISHER_IDENTITY_CHANGED")
    doi_verifiable=_publisher_doi_is_present(dataset,expected["dataset_doi"])
    # GBIF v1 sometimes does not include the DOI in /dataset/{uuid} and lists
    # it only in the dedicated identifiers endpoint. The known UUID/title
    # are mandatory; absent DOI is a HARD source-provenance STOP, not a license
    # to silently substitute another dataset.
    if not doi_verifiable:
        raise ValueError("STOP_DATASET_DOI_NOT_IN_METADATA")
    if species.get("rank")!="SPECIES":
        raise ValueError("STOP_TAXON_NOT_SPECIES")
    scientific=str(species.get("scientificName") or species.get("canonicalName") or "").lower()
    canonical=str(species.get("canonicalName") or "").lower()
    if not (scientific.startswith("sterna paradisaea") or canonical=="sterna paradisaea"):
        raise ValueError("STOP_TAXON_MATCH_NOT_ARCTIC_TERN")
    if species.get("status") not in ("ACCEPTED","DOUBTFUL"):
        raise ValueError("STOP_TAXON_NOT_ACCEPTED")
    key=species.get("speciesKey") or species.get("usageKey")
    if not isinstance(key,int) or key<1:
        raise ValueError("STOP_TAXON_KEY_ABSENT")
    return key,{
        "dataset_uuid":expected["gbif_dataset_uuid"],"dataset_title":title,
        "dataset_doi_verifiable":doi_verifiable,
        "dataset_license":dataset.get("license"),
        "species_match_usage_key":species.get("usageKey"),
        "species_match_species_key":key,
        "species_match_canonical":species.get("canonicalName") or species.get("scientificName"),
        "species_match_status":species.get("status"),
    }


def _count_query(source:dict[str,Any], window:dict[str,Any], taxon_key:int) -> str:
    fields={
        "datasetKey":source["gbif_dataset_uuid"],
        "taxonKey":str(taxon_key),
        "country":"DK",
        "hasCoordinate":"true",
        "year":str(window["year_min"])+","+str(window["year_max"]),
        "limit":"0",
    }
    return BASE+"/occurrence/search?"+urllib.parse.urlencode(fields)


def run(spec:dict[str,Any], fetch:Callable[...,tuple[dict[str,Any],str]]=_get_official_json) -> dict[str,Any]:
    ans={
        "schema":"eog.independent_dofbasen_tern_historical_source_count_v1.receipt",
        "status":"STOP_UNSTARTED",
        "biological_records_read":0,
        "colonies_with_verified_breeding":0,
        "source_site_years_verified":0,
        "tern_original_event_rows_revisited":0,
        "actual_source_occupancy_crosswalk_completed":False,
        "new_eog_wf_scored_endpoints":0,
        "asof_availability_verified":False,
    }
    if spec.get("status")!="PROTOCOL_FIRST_BEFORE_GBIF_QUERY":
        ans["status"]="STOP_PROTOCOL_NOT_FROZEN"
        return ans
    fixed=spec["stage0_count_only"]
    if len(fixed["windows"])!=5 or fixed["strict_unverified_limits"]["maximum_total_requests"]!=7:
        ans["status"]="STOP_SOURCE_COUNT_PROTOCOL_CHANGED"
        return ans
    if spec["external_dataset"]["gbif_dataset_uuid"]!="95db4db8-f762-11e1-a439-00145eb45e9a":
        ans["status"]="STOP_DOFBASEN_UUID_CHANGED"
        return ans
    limits=fixed["strict_unverified_limits"]
    results=[]
    request_count=0
    def request(url:str):
        nonlocal request_count
        request_count+=1
        if request_count>limits["maximum_total_requests"]:
            raise ValueError("STOP_EXCESS_EXTERNAL_SOURCE_REQUESTS")
        return fetch(url,byte_cap=limits["maximum_http_response_bytes"],
                     timeout=limits["maximum_seconds_each"])
    try:
        dataset_url=fixed["endpoints"]["dataset"]
        taxon_url=fixed["endpoints"]["taxon"]
        dataset,source_sha=request(dataset_url)
        species,taxon_sha=request(taxon_url)
        taxon_key,ident=_validate_source(spec,dataset,species)
        ans["source_metadata_sha256"]=source_sha
        ans["taxon_metadata_sha256"]=taxon_sha
        ans["source_identification"]=ident
        for window in fixed["windows"]:
            url=_count_query(spec["external_dataset"],window,taxon_key)
            response,raw_sha=request(url)
            n=response.get("count")
            if not isinstance(n,int) or n<0:
                raise ValueError("STOP_GBIF_COUNT_SCHEMA")
            results.append({
                "window_id":window["id"],
                "year_min":window["year_min"],
                "year_max":window["year_max"],
                "coordinate_bearing_occurrence_count":n,
                "request_url":url,
                "raw_response_sha256":raw_sha,
                "count_is_not_breeding_evidence":True,
            })
        ans.update({
            "status":"GBIF_DOF_SOURCE_COUNT_VERIFIED_NO_BREEDING_VALIDATION",
            "count_window_results":results,
            "count_requests_completed":request_count,
            "source_provenance":"GBIF DOF/BirdLife DOFbasen independent observational data, not derived Danish Tern Group",
            "source_archival_date_asof_verified":False,
            "source_dataset_is_recent_weekly_snapshot":True,
            "next_gate":"Only if pre-2005 counts >0, freeze a separate capped record-SCHEMA stage for reproductive/breeding and coordinate uncertainty information. No direct site-year crosswalk yet.",
        })
    except urllib.error.HTTPError as e:
        ans["status"]="STOP_GBIF_HTTP_"+str(e.code)
    except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as e:
        ans["status"]="STOP_GBIF_TRANSPORT"
        ans["error_type"]=type(e).__name__
    except (ValueError,TypeError,KeyError,json.JSONDecodeError,OverflowError) as e:
        ans["status"]=str(e) if str(e).startswith("STOP_") else "STOP_GBIF_METADATA_SCHEMA"
        ans["error_type"]=type(e).__name__
    return ans


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    spec=json.loads(args.protocol.read_text(encoding="utf-8"))
    result=run(spec)
    result["sha256_without_self"]=_digest_document(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "counts":result.get("count_window_results"),
        "source_identification":result.get("source_identification"),
        "records_read":result["biological_records_read"],
        "colonies_verified":result["colonies_with_verified_breeding"],
        "new_eogwf":result["new_eog_wf_scored_endpoints"],
        "receipt_sha256":result["sha256_without_self"],
    },ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    main()
