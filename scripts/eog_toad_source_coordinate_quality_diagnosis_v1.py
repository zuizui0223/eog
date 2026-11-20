#!/usr/bin/env python3
"""One-shot data-quality diagnosis for the already-frozen toad H1 source STOP.

Reopen only the SHA-locked publisher archive. Compare documented published
distance columns to exactly enumerated candidate coordinate-pair formulae and
fixed scale factors. NO toad movement effects, H1 delta, direction, recapture
probabilities or individual records are computed or exported.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from benchmarks.independent_toad_source_anchor_geography_v1 import (
    _verified_member, _as_rows, _number, ScientificStop,
    COORD_COLUMNS, DIST_COLUMNS, _distance
)
from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/independent_toad_coordinate_diagnosis_v1/protocol_v1.json")
PRIMARY = Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json")
PUBLISHER_TRANSFER = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
PUBLISHER_ORIGINAL = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
PAIRS = ("RF","IF","IR")


def _quantile(arr: list[float], p: float) -> float | None:
    if not arr: return None
    v=sorted(arr)
    t=p*(len(v)-1)
    k=int(math.floor(t))
    j=int(math.ceil(t))
    return v[k]+(v[j]-v[k])*(t-k)


def _source_consistent(frozen: dict[str,Any], upstream: dict[str,Any]) -> None:
    original=upstream["source"]
    current=frozen["source"]
    pairs=(("doi","doi"),("version_id","version_id"),
           ("csv_name","csv_name"),("csv_sha256","csv_sha256"),
           ("csv_size_bytes","csv_size_bytes"))
    if any(current[k]!=original[v] for k,v in pairs):
        raise ScientificStop("STOP_REOPENED_QUALITY_SOURCE_IDENTITY_CHANGED")
    if current["expected_raw_rows"]!=original["entire_csv_source_only_rows"]:
        raise ScientificStop("STOP_FROZEN_SOURCE_ROW_ROSTER_CHANGED")
    if frozen["parent_primary_scientific_stop"]!="STOP_GEO_UNIT_CONCORDANCE":
        raise ScientificStop("STOP_ORIGINAL_PRIMARY_STATUS_NOT_FROZEN")


def _parse(value: object, tokens: set[str]) -> tuple[str,float|None]:
    try:
        result=_number(value,tokens)
    except ScientificStop:
        return "invalid",None
    return ("missing",None) if result is None else ("numeric",result)


def _diagnose(data: bytes, parent: dict[str,Any], frozen: dict[str,Any]) -> dict[str,Any]:
    _source_consistent(frozen,parent)
    rows,grain=_as_rows(data,parent)
    tokens={s.lower() for s in parent["data_contract"]["missing_values"]}
    coordinate_summary={key:Counter() for key in COORD_COLUMNS}
    distance_summary={key:Counter() for key in DIST_COLUMNS}
    comparable={
        name:{
            pair:{
                str(scale):{"comparisons":0,"matches":0,"ratio_samples":[]}
                for scale in frozen["audit_scope"]["allowed_scales_for_exploratory_quality"]
            } for pair in PAIRS
        } for name in DIST_COLUMNS
    }
    denominator={
        "published_rows":grain["published_rows"],
        "byte_identical_duplicate_rows":grain["exact_duplicate_rows_removed"],
        "deduplicated_rows":len(rows),
        "missing_T_Identifier":0,
        "missing_reencounter_date":0,
        "coordinate_complete_rows":0,
        "published_h1_coordinate_and_recapture_eligible_rows":0,
        "source_rows_with_missing_some_coordinate":0,
        "source_rows_with_invalid_numeric_coordinate":0,
    }
    strict_checks={
        name:{"nonmissing_numeric_in_original_QC":0,"matches_original_5percent_or_2m":0,"mismatches":0,
              "missing_original_QC":0,"invalid_original_QC":0}
        for name in DIST_COLUMNS
    }
    for row in rows:
        identifier=str(row.get("Toad ID","")).strip()
        recap=str(row.get("Date of re-encounter","")).strip()
        id_ok=bool(identifier and identifier.lower() not in tokens)
        recap_ok=bool(recap and recap.lower() not in tokens)
        if not id_ok:
            denominator["missing_T_Identifier"]+=1
        if not recap_ok:
            denominator["missing_reencounter_date"]+=1
        coords={}
        for key in COORD_COLUMNS:
            category,val=_parse(row.get(key),tokens)
            coordinate_summary[key][category]+=1
            coords[key]=val
        if any(v is None for v in coords.values()):
            denominator["source_rows_with_missing_some_coordinate"]+=1
            if any(_parse(row.get(key),tokens)[0]=="invalid" for key in COORD_COLUMNS):
                denominator["source_rows_with_invalid_numeric_coordinate"]+=1
            continue
        denominator["coordinate_complete_rows"]+=1
        if not id_ok or not recap_ok:
            # Rows without an authenticated post-release outcome remain outside
            # the original v1 coordinate-concordance test (not a negative).
            continue
        denominator["published_h1_coordinate_and_recapture_eligible_rows"]+=1
        I=(coords["Initial Easting"],coords["Initial Northing"])
        R=(coords["Released Easting"],coords["Released Northing"])
        F=(coords["Final Easting"],coords["Final Northing"])
        calc={"RF":_distance(R,F),"IF":_distance(I,F),"IR":_distance(I,R)}
        for name, original_pair in zip(DIST_COLUMNS,("RF","IF"),strict=True):
            category,published=_parse(row.get(name),tokens)
            distance_summary[name][category]+=1
            if category=="missing":
                strict_checks[name]["missing_original_QC"]+=1
            elif category=="invalid":
                strict_checks[name]["invalid_original_QC"]+=1
            else:
                assert published is not None
                strict_checks[name]["nonmissing_numeric_in_original_QC"]+=1
                computed=calc[original_pair]
                if abs(published-computed)<=max(2.0,0.05*computed):
                    strict_checks[name]["matches_original_5percent_or_2m"]+=1
                else:
                    strict_checks[name]["mismatches"]+=1
                for pair,dist in calc.items():
                    for scale in frozen["audit_scope"]["allowed_scales_for_exploratory_quality"]:
                        target=dist*scale
                        cell=comparable[name][pair][str(scale)]
                        cell["comparisons"]+=1
                        if abs(published-target)<=max(2.0,0.05*target):
                            cell["matches"]+=1
                        if target>1e-12:
                            cell["ratio_samples"].append(published/target)
    profile={}
    for name,by_pair in comparable.items():
        profile[name]={}
        for pair,by_scale in by_pair.items():
            profile[name][pair]={}
            for scale,stats in by_scale.items():
                rr=stats["ratio_samples"]
                profile[name][pair][scale]={
                    "comparisons":stats["comparisons"],
                    "matches":stats["matches"],
                    "match_fraction":stats["matches"]/stats["comparisons"] if stats["comparisons"] else None,
                    "ratio_unsigned_q25":_quantile(rr,.25),
                    "ratio_unsigned_median":_quantile(rr,.50),
                    "ratio_unsigned_q75":_quantile(rr,.75),
                    "zero_denominator_not_in_ratio":stats["comparisons"]-len(rr),
                }
    for name in DIST_COLUMNS:
        n=strict_checks[name]["nonmissing_numeric_in_original_QC"]
        strict_checks[name]["fraction_matched"]=(
            strict_checks[name]["matches_original_5percent_or_2m"]/n if n else None
        )
    could_pass=all(
        v["nonmissing_numeric_in_original_QC"]>0
        and v["fraction_matched"]>=.95
        for v in strict_checks.values()
    )
    if could_pass:
        raise ScientificStop("STOP_REPRODUCED_QUALITY_GATE_CONTRADICTS_FROZEN_PRIMARY_STOP")
    return {
        "schema":"eog.toad_source_coordinate_quality_diagnosis_v1",
        "status":"SOURCE_DISTANCE_QC_DIAGNOSIS_COMPLETED_ORIGINAL_GEO_STOP_RETAINED",
        "parent_H1_status":"NOT_SCORED_GEO_UNIT_CONCORDANCE_STOP",
        "original_H1_quality_gate_reproduced_as_failure":True,
        "original_source_sha256":frozen["source"]["csv_sha256"],
        "row_quality_denominators":denominator,
        "coordinate_fields_format_counts":{k:dict(v) for k,v in coordinate_summary.items()},
        "published_distance_format_counts_on_original_QC_grain":{k:dict(v) for k,v in distance_summary.items()},
        "frozen_original_distance_concordance":strict_checks,
        "fixed_alternative_pair_and_scale_diagnostics":profile,
        "diagnostic_alternatives_not_primary_scoring":True,
        "individual_ID_or_coordinates_exported":False,
        "biological_effect_computed":False,
        "new_EOG_WF_endpoints":0,
        "primary_H1_rescored":False,
    }


def run(protocol:dict[str,Any])->dict[str,Any]:
    if protocol.get("status")!="FROZEN_PRE_QUALITY_DIAGNOSIS_POST_PRIMARY_STOP":
        raise ScientificStop("STOP_DIAGNOSTIC_PROTOCOL_NOT_FROZEN")
    parent=json.loads(PRIMARY.read_text(encoding="utf-8"))
    _source_consistent(protocol,parent)
    transfer=json.loads(PUBLISHER_TRANSFER.read_text(encoding="utf-8"))
    limits=json.loads(PUBLISHER_ORIGINAL.read_text(encoding="utf-8"))["resource_limits"]
    source=protocol["source"]
    endpoint=f"https://datadryad.org/api/v2/versions/{source['version_id']}/download"
    zipbytes,_=_version_zip(endpoint,limits,transfer["exact_trusted_redirect_contract"])
    raw=_verified_member(zipbytes,parent)
    del zipbytes
    return _diagnose(raw,parent,protocol)


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    x=p.parse_args()
    spec=json.loads(x.protocol.read_text(encoding="utf-8"))
    try:
        result=run(spec)
    except (ScientificStop,ValueError,OSError) as e:
        result={
            "schema":"eog.toad_source_coordinate_quality_diagnosis_v1",
            "status":str(e) if str(e).startswith("STOP_") else "STOP_QUALITY_DIAGNOSIS_TRANSPORT",
            "diagnostic_exception_type":type(e).__name__,
            "parent_H1_status":"NOT_SCORED_GEO_UNIT_CONCORDANCE_STOP",
            "biological_effect_computed":False,
            "primary_H1_rescored":False,
            "new_EOG_WF_endpoints":0,
        }
    result["sha256_without_self_field"]=_digest(
        (json.dumps(result,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+"\n").encode()
    )
    x.output.parent.mkdir(parents=True,exist_ok=True)
    x.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "geo_qc":result.get("frozen_original_distance_concordance"),
        "row_denominators":result.get("row_quality_denominators"),
        "source_result_sha256":result["sha256_without_self_field"],
        "biological_effect_computed":False,
        "new_EOG_WF_endpoints":0,
    },sort_keys=True))


if __name__=="__main__":
    main()
