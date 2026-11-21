#!/usr/bin/env python3
"""Publisher-locked Danish Arctic Tern breeding-schema inspection (v2).

15 frozen GBIF occurrence/search pages x100 records, at fixed first/middle/
last offsets of five historical year windows. Raw observed records are handled
in process only. No IDs, coordinates, names, remarks, field text, or site-years
are uploaded/logged. Nonempty breeding fields are NOT evidence of breeding
until a separate public code/dictionary and site-level verification gate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import urllib.parse
from typing import Any,Callable

from scripts import eog_tern_independent_dofbasen_source_count_gate_v1 as first

PROTOCOL=Path("validation/tern_independent_dofbasen_breeding_field_gate_v2/protocol_v2.json")
PREVIOUS=Path("validation/tern_independent_dofbasen_breeding_gate_v1/frozen_count_receipt_v1.json")
SOURCE="95db4db8-f762-11e1-a439-00145eb45e9a"
SPECIES=5229230

REQUIRED_FIELDS=(
    "gbifID","datasetKey","speciesKey","taxonKey","scientificName","eventDate",
    "year","decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters",
    "coordinatePrecision","hasGeospatialIssues","behavior","reproductiveCondition",
    "occurrenceRemarks","lifeStage","basisOfRecord","occurrenceStatus",
)
UNCERTAINTY_BINS=(
    "MISSING","LE_1000","GT_1000_LE_2000","GT_2000_LE_5000",
    "GT_5000_LE_20000","GT_20000","NONFINITE_OR_INVALID",
)


def _present(value:object)->bool:
    if value is None:
        return False
    if isinstance(value,str):
        return bool(value.strip())
    return True


def _uncertainty_bin(value:object)->str:
    if not _present(value):
        return "MISSING"
    try:
        x=float(value)
    except (ValueError,OverflowError,TypeError):
        return "NONFINITE_OR_INVALID"
    if not math.isfinite(x) or x<0:
        return "NONFINITE_OR_INVALID"
    if x<=1000:
        return "LE_1000"
    if x<=2000:
        return "GT_1000_LE_2000"
    if x<=5000:
        return "GT_2000_LE_5000"
    if x<=20000:
        return "GT_5000_LE_20000"
    return "GT_20000"


def _page_uri(window:dict[str,Any],offset:int) -> str:
    parameters={
        "datasetKey":SOURCE,
        "taxonKey":str(SPECIES),
        "country":"DK",
        "hasCoordinate":"true",
        "year":f'{window["from"]},{window["to"]}',
        "limit":str(window["limit"]),
        "offset":str(offset),
    }
    return "https://api.gbif.org/v1/occurrence/search?"+urllib.parse.urlencode(parameters)


def _validate_protocol(spec:dict[str,Any],source:dict[str,Any])->None:
    if spec.get("status")!="FROZEN_BEFORE_ANY_GBIF_OCCURRENCE_RECORD_READ":
        raise ValueError("STOP_GBIF_FIELD_PROTOCOL_NOT_FROZEN")
    parent=spec["parent_source_gate"]
    if parent["gbif_dataset_uuid"]!=SOURCE or parent["species_key"]!=SPECIES or parent["dataset_doi"]!="10.15468/tww7cj":
        raise ValueError("STOP_ORIGINAL_GBIF_SOURCE_OR_TAXON_DRIFT")
    if parent["source_receipt_sha256"]!=source["source_ci"]["canonical_result_sha256_without_self"]:
        raise ValueError("STOP_PARENT_SOURCE_RECEIPT_FINGERPRINT_CHANGED")
    actual=spec["source_sample_design"]["windows"]
    previous=source["source_count_windows"]
    if len(actual)!=5 or len(previous)!=5:
        raise ValueError("STOP_GBIF_SOURCE_WINDOW_ROSTER")
    for frozen,base in zip(actual,previous,strict=True):
        if (frozen["id"],frozen["from"],frozen["to"],frozen["count"])!=(
           base["id"],base["from"],base["to"],base["n"]):
            raise ValueError("STOP_GBIF_YEAR_OR_COUNT_DRIFT")
        n=frozen["count"]
        if frozen["limit"]!=100 or frozen["offsets"]!=[0,n//2,n-100]:
            raise ValueError("STOP_GBIF_SAMPLE_PAGES_CHANGED")
    if spec["source_sample_design"]["expected_requests"]!=15 or spec["source_sample_design"]["expected_sample_records"]!=1500:
        raise ValueError("STOP_GBIF_SOURCE_RECORD_BUDGET_CHANGED")
    if spec["field_presence_counts"]!=list(REQUIRED_FIELDS):
        raise ValueError("STOP_GBIF_FIELD_ROSTER_CHANGED")
    if spec["field_quality_bins"]["coordinate_uncertainty_meters"]!=list(UNCERTAINTY_BINS):
        raise ValueError("STOP_GBIF_UNCERTAINTY_BINS_CHANGED")


def inspect_frozen_record_pages(
    spec:dict[str,Any],source:dict[str,Any],
    *,fetch:Callable[...,tuple[dict[str,Any],str]]=first._get_official_json,
)->dict[str,Any]:
    result={
        "schema":"eog.tern_independent_dofbasen_breeding_field_gate_v2.result",
        "status":"STOP_UNSTARTED",
        "source_site_years_verified":0,
        "independent_breeding_colonies_matched_to_original_tern":0,
        "individual_occurrence_records_exported":0,
        "original_tern_dispersal_event_rows_reopened":0,
        "historical_asof_source_data_verified":False,
        "new_EOG_WF_scored_endpoints":0,
        "source_claim":"No record's mere presence or nonempty behavior code is a verified breeding or colony export event."
    }
    try:
        _validate_protocol(spec,source)
        cap=spec["source_sample_design"]["max_response_bytes_per_request"]
        timeout=spec["source_sample_design"]["request_timeout_sec"]
        page_results=[]
        all_fields=Counter()
        all_uncertainty=Counter()
        original_id_hashes=set()
        repeated_ids=0
        qa_bad_dataset=0
        qa_bad_species=0
        sample_total=0
        for window in spec["source_sample_design"]["windows"]:
            field_totals=Counter()
            uncertainty=Counter()
            n=0
            for offset in window["offsets"]:
                url=_page_uri(window,offset)
                response,source_hash=fetch(url,byte_cap=cap,timeout=timeout)
                if response.get("count")!=window["count"]:
                    raise ValueError("STOP_GBIF_DATASET_UPDATED_SINCE_COUNT_FREEZE")
                arr=response.get("results")
                if not isinstance(arr,list) or len(arr)!=window["limit"]:
                    raise ValueError("STOP_GBIF_PAGE_SCHEMA_OR_ROW_COUNT")
                for row in arr:
                    if not isinstance(row,dict):
                        raise ValueError("STOP_GBIF_OCCURRENCE_OBJECT_SCHEMA")
                    sample_total+=1
                    n+=1
                    for key in REQUIRED_FIELDS:
                        if _present(row.get(key)):
                            field_totals[key]+=1
                            all_fields[key]+=1
                    bin_name=_uncertainty_bin(row.get("coordinateUncertaintyInMeters"))
                    uncertainty[bin_name]+=1
                    all_uncertainty[bin_name]+=1
                    if row.get("datasetKey")!=SOURCE:
                        qa_bad_dataset+=1
                    # GBIF speciesKey may be omitted/unstable for some records,
                    # so record quality violations WITHOUT substituting a
                    # species inferred from vernacular names.
                    if row.get("speciesKey")!=SPECIES:
                        qa_bad_species+=1
                    record_id=str(row.get("gbifID") or "")
                    if record_id:
                        # Fingerprint inside runner only, never output record ID/hash.
                        fingerprint=first._sha(record_id.encode("utf-8"))
                        if fingerprint in original_id_hashes:
                            repeated_ids+=1
                        else:
                            original_id_hashes.add(fingerprint)
                page_results.append({
                    "window_id":window["id"],
                    "offset":offset,
                    "record_count":len(arr),
                    "response_sha256":source_hash,
                    "source_query_url":url,
                })
            result.setdefault("window_field_summaries",[]).append({
                "window_id":window["id"],
                "sample_records":n,
                "nonempty_original_fields":dict(sorted(field_totals.items())),
                "coordinate_uncertainty_bins":{key:uncertainty.get(key,0) for key in UNCERTAINTY_BINS},
                "none_of_these_fields_proves_a_breeding_colony":True,
            })
        if sample_total!=1500 or len(page_results)!=15:
            raise ValueError("STOP_GBIF_SOURCE_SAMPLE_BUDGET_MISMATCH")
        result.update({
            "status":"GBIF_DOF_BREEDING_FIELD_SCHEMA_INSPECTED_NOT_SITE_YEAR_VALIDATED",
            "actual_observed_records_read_ephemerally":sample_total,
            "page_count":len(page_results),
            "observed_page_fingerprints":page_results,
            "total_nonempty_field_counts":dict(sorted(all_fields.items())),
            "total_uncertainty_bins":{key:all_uncertainty.get(key,0) for key in UNCERTAINTY_BINS},
            "duplicate_record_IDs_across_fixed_pages_not_exported":repeated_ids,
            "datasetKey_mismatches_in_sample":qa_bad_dataset,
            "speciesKey_mismatches_in_sample":qa_bad_species,
            "schema_supports_record_level_breeding_text_inspection":(
                sum(all_fields.get(k,0) for k in ("reproductiveCondition","behavior","occurrenceRemarks"))>0
            ),
            "sample_is_representative":False,
            "can_prove_source_colony_breeding_in_original_year":False,
            "can_directly_crosswalk_115_sites":False,
            "GBIF_source_is_not_historic_AsOf":True,
        })
        if qa_bad_dataset or qa_bad_species:
            result["status"]="STOP_GBIF_ORIGINAL_DATASET_OR_TAXON_CROSS_CONTAMINATION"
        elif not result["schema_supports_record_level_breeding_text_inspection"]:
            result["status"]="STOP_GBIF_SAMPLED_BREEDING_FIELDS_NOT_PRESENT"
    except (ValueError,TypeError,KeyError,OverflowError) as err:
        result["status"]=str(err) if str(err).startswith("STOP_") else "STOP_GBIF_STAGE2_SCHEMA"
        result["error_type"]=type(err).__name__
    except (OSError,ConnectionError,TimeoutError) as err:
        result["status"]="STOP_GBIF_SOURCE_TRANSPORT"
        result["error_type"]=type(err).__name__
    return result


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    parent=json.loads(PREVIOUS.read_text(encoding="utf-8"))
    result=inspect_frozen_record_pages(protocol,parent)
    result["sha256_without_self"]=first._digest_document(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "sample_count":result.get("actual_observed_records_read_ephemerally"),
        "breeding_fields_present":result.get("schema_supports_record_level_breeding_text_inspection"),
        "total_nonempty_fields":result.get("total_nonempty_field_counts"),
        "uncertainty_bins":result.get("total_uncertainty_bins"),
        "wrong_dataset":result.get("datasetKey_mismatches_in_sample"),
        "wrong_species":result.get("speciesKey_mismatches_in_sample"),
        "source_site_years_verified":0,
        "original_tern_rows_reopened":0,
        "new_EOG_WF_endpoints":0,
        "receipt_sha256":result["sha256_without_self"],
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
