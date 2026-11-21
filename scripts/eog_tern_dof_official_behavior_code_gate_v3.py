#!/usr/bin/env python3
"""Official DOF code vocabulary vs 15 frozen GBIF historical Arctic Tern pages.

Scientific scope: inspect *categorical primary/secondary behavior code labels*
and their positional precision. NEVER emit raw behavior outside approved
publisher whitelist; NEVER emit original GBIF IDs, coordinates, dates, remarks,
or bird movement observations. No breeding source/year is certified here.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Callable

from scripts import eog_tern_independent_dofbasen_breeding_field_gate_v2 as previous
from scripts import eog_tern_independent_dofbasen_source_count_gate_v1 as first

PROTOCOL = Path("validation/tern_independent_dofbasen_behavior_semantics_v3/protocol_v3.json")
PARENT_PROTOCOL = Path("validation/tern_independent_dofbasen_breeding_field_gate_v2/protocol_v2.json")
PARENT_RECEIPT = Path("validation/tern_independent_dofbasen_breeding_field_gate_v2/frozen_field_receipt_v2.json")
COUNT_RECEIPT = Path("validation/tern_independent_dofbasen_breeding_gate_v1/frozen_count_receipt_v1.json")

PRESENCE_FIELDS=("behavior","reproductiveCondition","occurrenceRemarks","lifeStage")
UNKNOWN="UNRECOGNIZED_DO_NOT_CLASSIFY"
MISSING="MISSING"
TIERS=("NONBREEDING_BEHAVIOR","NOT_DIRECT_BREEDING","BREEDING_LABELED_NOT_CERTIFIED_SITE",
       "BREEDING_SUGGESTIVE","NEST_EVIDENCE_POTENTIAL")
ORIGINAL_UNCERTAINTY={
 "MISSING":0,"LE_1000":304,"GT_1000_LE_2000":697,
 "GT_2000_LE_5000":487,"GT_5000_LE_20000":12,
 "GT_20000":0,"NONFINITE_OR_INVALID":0
}


def _normalize_code(raw:object)->str|None:
    if not isinstance(raw,str) or not raw.strip():
        return None
    if len(raw)>100:
        return UNKNOWN
    # Permit only exact publisher-defined categories, no substring guesses.
    s=unicodedata.normalize("NFC",raw).replace("\u00a0"," ")
    return re.sub(r"\s+"," ",s.strip()).upper()


def _validate_vocabulary(v3:dict[str,Any],p2:dict[str,Any],count:dict[str,Any],p2_summary:dict[str,Any])->dict[str,str]:
    if v3.get("status")!="FROZEN_BEFORE_V3_BEHAVIOR_VALUE_READ":
        raise ValueError("STOP_BEHAVIOR_V3_PROTOCOL_NOT_FROZEN")
    x=v3["sources"]
    if (x["gbif_dataset_uuid"]!=previous.SOURCE or x["accepted_species_key"]!=previous.SPECIES
        or x["dataset_doi"]!="10.15468/tww7cj"):
        raise ValueError("STOP_ORIGINAL_DOFBASEN_SOURCE_CHANGED")
    if x["parent_stage1_count_sha"]!=count["source_ci"]["canonical_result_sha256_without_self"]:
        raise ValueError("STOP_PARENT_COUNT_RECEIPT_DRIFT")
    if x["parent_stage2_schema_sha"]!=p2_summary["execution"]["original_result_receipt_sha256_without_self"]:
        raise ValueError("STOP_PARENT_FIELD_RECEIPT_DRIFT")
    if (p2_summary["frozen_sample"]["original_records_ephemerally_read"]!=1500
        or p2_summary["field_presence"]["behavior"]!=1500
        or p2_summary["coordinateUncertaintyInMeters_bins"]!=ORIGINAL_UNCERTAINTY):
        raise ValueError("STOP_FROZEN_STAGE2_FIELD_RESULT_CHANGED")
    previous._validate_protocol(p2,count)
    if (v3["sample"]["windows_count"]!=5
        or v3["sample"]["max_rows"]!=1500
        or not v3["sample"]["same_15_frozen_URLS_as_stage2"]):
        raise ValueError("STOP_SAMPLE_CONTRACT_CHANGED")
    rows=v3["codebook"]["official_codes_to_report"]
    if len(rows)!=31:
        raise ValueError("STOP_CODEBOOK_NUMBER_CHANGED")
    vocab={}
    for row in rows:
        k=row["code"]
        if k in vocab or row["tier"] not in TIERS or _normalize_code(k)!=k:
            raise ValueError("STOP_CODEBOOK_UNKNOWN_OR_DUPLICATE")
        vocab[k]=row["tier"]
    if v3["codebook"]["nest_evidence_codes"]!=["YF B","YF BR","YF UR"]:
        raise ValueError("STOP_NEST_CODE_TIER_DRIFT")
    if any(vocab.get(c)!="NEST_EVIDENCE_POTENTIAL" for c in v3["codebook"]["nest_evidence_codes"]):
        raise ValueError("STOP_NEST_CODEBOOK_MISCLASSIFICATION")
    if sorted(PRESENCE_FIELDS)!=sorted(["behavior","reproductiveCondition","occurrenceRemarks","lifeStage"]):
        raise ValueError("STOP_FIELD_ROSTER")
    return vocab


def inspect_behavior_codebook(v3:dict[str,Any],p2:dict[str,Any],count:dict[str,Any],
                              parent_receipt:dict[str,Any], *,
                              fetch:Callable[...,tuple[dict[str,Any],str]]=first._get_official_json)->dict[str,Any]:
    result={
        "schema":"eog.dof_tern_behavior_code_semantic_gate_v3.aggregate",
        "status":"STOP_UNSTARTED",
        "source_site_years_verified":0,
        "source_breeding_colonies_verified":0,
        "historical_asof_availability_verified":False,
        "original_tern_movement_rows_reopened":0,
        "raw_DOF_observation_rows_exported":0,
        "raw_unrecognized_behavior_values_exported":0,
        "new_EOG_WF_endpoints":0,
    }
    try:
        vocab=_validate_vocabulary(v3,p2,count,parent_receipt)
        source_pages=p2["source_sample_design"]["windows"]
        field_total=Counter()
        uncertainty_total=Counter()
        code_total=Counter()
        tier_total=Counter()
        tier_2km=Counter()
        pages=[]
        sampled=0
        issue_source=0
        issue_species=0
        for window in source_pages:
            bywindow_code=Counter()
            bywindow_tier=Counter()
            for offset in window["offsets"]:
                url=previous._page_uri(window,offset)
                payload,digest=fetch(url,
                    byte_cap=p2["source_sample_design"]["max_response_bytes_per_request"],
                    timeout=p2["source_sample_design"]["request_timeout_sec"])
                if payload.get("count")!=window["count"]:
                    raise ValueError("STOP_GBIF_COUNT_DRIFT_AFTER_PREVIOUS_FIELD_GATE")
                records=payload.get("results")
                if not isinstance(records,list) or len(records)!=100:
                    raise ValueError("STOP_GBIF_RECORD_PAGE_CHANGED")
                pages.append({"window":window["id"],"offset":offset,"source_json_sha256":digest})
                for row in records:
                    if not isinstance(row,dict):
                        raise ValueError("STOP_GBIF_SOURCE_RECORD_SCHEMA")
                    sampled+=1
                    if row.get("datasetKey")!=previous.SOURCE:
                        issue_source+=1
                    if row.get("speciesKey")!=previous.SPECIES:
                        issue_species+=1
                    for k in PRESENCE_FIELDS:
                        if previous._present(row.get(k)):
                            field_total[k]+=1
                    u=previous._uncertainty_bin(row.get("coordinateUncertaintyInMeters"))
                    uncertainty_total[u]+=1
                    original= _normalize_code(row.get("behavior"))
                    code=original if original in vocab else (MISSING if original is None else UNKNOWN)
                    code_total[code]+=1
                    bywindow_code[code]+=1
                    tier=vocab[code] if code in vocab else code
                    tier_total[tier]+=1
                    bywindow_tier[tier]+=1
                    if u in ("LE_1000","GT_1000_LE_2000"):
                        tier_2km[tier]+=1
            result.setdefault("window_behavior_codes",[]).append({
                "window_id":window["id"],
                "source_records_sampled":300,
                "known_publisher_code_counts":{k:bywindow_code[k] for k in vocab if bywindow_code[k]},
                "unknown_or_missing_code_counts":{key:bywindow_code[key] for key in (UNKNOWN,MISSING)},
                "code_tier_counts":{k:bywindow_tier[k] for k in (*TIERS,UNKNOWN,MISSING) if bywindow_tier[k]},
                "meaning_is_not_verified_breeding_site":True
            })
        if sampled!=1500 or len(pages)!=15:
            raise ValueError("STOP_SOURCE_SAMPLE_SIZE_CHANGED")
        if issue_source or issue_species:
            raise ValueError("STOP_DOFBASEN_RECORD_IDENTITY_CROSS_CONTAMINATION")
        if (field_total["behavior"]!=parent_receipt["field_presence"]["behavior"]
            or field_total["reproductiveCondition"]!=parent_receipt["field_presence"]["reproductiveCondition"]
            or field_total["occurrenceRemarks"]!=parent_receipt["field_presence"]["occurrenceRemarks"]
            or field_total["lifeStage"]!=parent_receipt["field_presence"]["lifeStage"]
            or dict(uncertainty_total)!= {k:v for k,v in ORIGINAL_UNCERTAINTY.items() if v}):
            raise ValueError("STOP_GBIF_SAMPLE_CHANGED_AFTER_PARENT_FIELD_RECEIPT")
        classified=sum(code_total[k] for k in vocab)
        result.update({
            "status":"DOF_OFFICIAL_BEHAVIOR_CODE_MATCHES_NOT_YET_SITE_YEAR_VALIDATION"
                     if classified else "STOP_GBIF_ALL_BEHAVIOR_VALUES_OUTSIDE_FROZEN_CODEBOOK",
            "fixed_pages_rechecked":15,
            "original_records_read_ephemerally":sampled,
            "unrecognized_behavior_count":code_total[UNKNOWN],
            "missing_behavior_count":code_total[MISSING],
            "original_allowed_behavior_code_matches":classified,
            "known_public_DOFBasen_code_histogram":{k:code_total[k] for k in vocab if code_total[k]},
            "tier_count_all_fixed_pages":{k:tier_total[k] for k in (*TIERS,UNKNOWN,MISSING) if tier_total[k]},
            "tier_with_coordinate_uncertainty_LE_2km":{k:tier_2km[k] for k in (*TIERS,UNKNOWN,MISSING) if tier_2km[k]},
            "reproduced_parent_field_presence_counts":dict(field_total),
            "reproduced_parent_coordinate_uncertainty_bins":{k:uncertainty_total.get(k,0) for k in previous.UNCERTAINTY_BINS},
            "fixed_page_source_SHA256s":pages,
            "gbif_snapshot_is_not_representative":True,
            "code_semantics_supported_by_original_DOFBasen_public_codebook":True,
            "nonempty_YF_or_nesting_code_does_not_certify_source_site_year":True,
            "individual_observation_raw_behavior_text_or_ids_exported":False,
            "original_source_or_target_site_coordinates_exported":False,
        })
    except (ValueError,TypeError,KeyError,OverflowError) as err:
        result["status"]=str(err) if str(err).startswith("STOP_") else "STOP_BEHAVIOR_CODE_INSPECTION_SCHEMA"
        result["error_type"]=type(err).__name__
    except (OSError,TimeoutError,ConnectionError) as err:
        result["status"]="STOP_BEHAVIOR_GBIF_NETWORK"
        result["error_type"]=type(err).__name__
    return result


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    data=json.loads(a.protocol.read_text(encoding="utf-8"))
    parent=json.loads(PARENT_PROTOCOL.read_text(encoding="utf-8"))
    count=json.loads(COUNT_RECEIPT.read_text(encoding="utf-8"))
    receipt=json.loads(PARENT_RECEIPT.read_text(encoding="utf-8"))
    result=inspect_behavior_codebook(data,parent,count,receipt)
    result["sha256_without_self"]=first._digest_document(result)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_records_read_ephemerally":result.get("original_records_read_ephemerally"),
        "known_code_histogram":result.get("known_public_DOFBasen_code_histogram"),
        "unrecognized":result.get("unrecognized_behavior_count"),
        "nest_code_precision_by_tier":result.get("tier_with_coordinate_uncertainty_LE_2km"),
        "all_tiers":result.get("tier_count_all_fixed_pages"),
        "known_breeding_source_sites_confirmed":0,
        "new_EOG_WF_endpoints":0,
        "receipt_sha256":result["sha256_without_self"],
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
