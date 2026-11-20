#!/usr/bin/env python3
"""Source-only post-STOP toad release-final distance signed encoding check.

Retains 165 original source rows, exact SHA/dedup and 163-row QA denominator.
Candidate signed geographic metrics are PREDECLARED in v4 protocol. This
does not alter original biological H1 or infer natural dispersal.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import urllib.error
import zipfile
from typing import Any

from benchmarks import independent_toad_source_anchor_geography_v1 as old
from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/independent_toad_geocoordinate_diagnostic_v4/protocol_v4.json")
PARENT = Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json")
V2_GATE = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
V1_GATE = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
FORMULAS = (
    "unsigned_euclidean_reference",
    "signed_easting_east_positive",
    "signed_easting_west_positive",
    "signed_easting_component",
    "reverse_signed_easting_component",
    "signed_by_direction_moved_E_positive",
    "signed_by_direction_moved_W_positive",
)
CLASSES = ("-500","-250","-100","0","100","250","500","other_or_missing")
SIGN_CLASSES = ("negative","zero","positive")


def _report_sha(obj: dict[str, Any]) -> str:
    txt=json.dumps(obj,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n"
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def _number(raw: object, missing: set[str]) -> float | None:
    try:
        return old._number(raw,missing)
    except old.ScientificStop as e:
        raise ValueError("STOP_UNDECLARED_NUMBER_IN_SIGN_AUDIT") from e


def _direction(raw: object) -> str:
    label=str(raw if raw is not None else "").strip().upper()
    return label if label in ("E","W") else "missing_or_other"


def _signed_class(x: float | None) -> str:
    if x is None:
        return "other_or_missing"
    for v in CLASSES[:-1]:
        if x==int(v):
            return v
    return "other_or_missing"


def _signed_value(reference_id:str, dx:float, dy:float, rad:float, moving_dir:str) -> float | None:
    sign=1 if dx>0 else (-1 if dx<0 else 0)
    if reference_id=="unsigned_euclidean_reference":
        return rad
    if reference_id=="signed_easting_east_positive":
        return sign*rad
    if reference_id=="signed_easting_west_positive":
        return -sign*rad
    if reference_id=="signed_easting_component":
        return dx
    if reference_id=="reverse_signed_easting_component":
        return -dx
    if reference_id=="signed_by_direction_moved_E_positive":
        return rad if moving_dir=="E" else (-rad if moving_dir=="W" else None)
    if reference_id=="signed_by_direction_moved_W_positive":
        return -rad if moving_dir=="E" else (rad if moving_dir=="W" else None)
    raise ValueError("STOP_UNREGISTERED_SIGNED_FORMULA")


def _sign_class(x:float) -> str:
    return "positive" if x>0 else ("negative" if x<0 else "zero")


def analyze_source_rows(rows:list[dict[str,str]], spec:dict[str,Any],parent:dict[str,Any]) -> dict[str,Any]:
    frozen=[v["id"] for v in spec["signed_formulas"]["candidates"]]
    if tuple(frozen)!=FORMULAS:
        raise ValueError("STOP_SIGNED_FORMULA_ROSTER_CHANGED")
    missing={v.lower() for v in parent["data_contract"]["missing_values"]}
    candidate_stats={formula:{"eligible_formula_rows":0,"matched":0} for formula in FORMULAS}
    by_nominal={c:{
        "source_rows":0,"original_unsigned_RF_matches":0,
        "original_capture_IF_matches":0,"release_reported_signs":Counter(),
        "move_directions":Counter(),"translocated_directions":Counter(),
        "formula_counts":{f:{"eligible":0,"matched":0} for f in FORMULAS},
        "nominal_sign_direction_pairs":Counter(),
    } for c in CLASSES}
    full_rf=0
    full_cf=0
    eligible=0
    sign_metadata=Counter()
    for row in rows:
        n=_number(row.get("Translocated distance"),missing)
        cat=_signed_class(n)
        group=by_nominal[cat]
        group["source_rows"]+=1
        dir_move=_direction(row.get("Direction moved"))
        dir_trans=_direction(row.get("Translocated direction"))
        group["move_directions"][dir_move]+=1
        group["translocated_directions"][dir_trans]+=1
        group["nominal_sign_direction_pairs"][f"{_sign_class(n) if n is not None else 'missing'}|{dir_trans}"]+=1
        ident=str(row.get("Toad ID","")).strip()
        timestamp=str(row.get("Date of re-encounter","")).strip()
        if ident.lower() in missing or timestamp.lower() in missing:
            continue
        coords=[_number(row.get(col),missing) for col in old.COORD_COLUMNS]
        if any(v is None for v in coords):
            continue
        measured_rf=_number(row.get("Distance release-final (m)"),missing)
        measured_cf=_number(row.get("Distance capture-final (m)"),missing)
        if measured_rf is None or measured_cf is None:
            continue
        eligible+=1
        I,R,F=((coords[0],coords[1]),(coords[2],coords[3]),(coords[4],coords[5]))
        dx=F[0]-R[0]
        dy=F[1]-R[1]
        rad=math.hypot(dx,dy)
        measured_if=old._distance(I,F)
        match_if=abs(measured_cf-measured_if)<=max(2.,0.05*measured_if)
        if match_if:
            group["original_capture_IF_matches"]+=1
            full_cf+=1
        match_rf=abs(measured_rf-rad)<=max(2.,0.05*rad)
        if match_rf:
            group["original_unsigned_RF_matches"]+=1
            full_rf+=1
        group["release_reported_signs"][_sign_class(measured_rf)]+=1
        sign_metadata[f"{dir_move}|{_sign_class(dx)}"]+=1
        for formula in FORMULAS:
            val=_signed_value(formula,dx,dy,rad,dir_move)
            if val is None:
                continue
            candidate_stats[formula]["eligible_formula_rows"]+=1
            group["formula_counts"][formula]["eligible"]+=1
            # The ORIGINAL 2m/5% tolerance was scale of |post-release displacement|.
            if abs(measured_rf-val)<=max(2.,0.05*rad):
                candidate_stats[formula]["matched"]+=1
                group["formula_counts"][formula]["matched"]+=1
    grouped=[]
    for cat,g in by_nominal.items():
        grouped.append({
            "nominal_translocation_signed_class":cat,
            "source_rows":g["source_rows"],
            "original_unsigned_release_final_matches":g["original_unsigned_RF_matches"],
            "original_capture_final_matches":g["original_capture_IF_matches"],
            "release_reported_sign_counts":dict(g["release_reported_signs"]),
            "recorded_movement_direction_counts":dict(g["move_directions"]),
            "recorded_translocation_direction_counts":dict(g["translocated_directions"]),
            "nominal_sign_and_recorded_translocation_direction_counts":dict(g["nominal_sign_direction_pairs"]),
            "signed_formula_matches":{
                f:{**v,"match_fraction":(v["matched"]/v["eligible"] if v["eligible"] else None)}
                for f,v in g["formula_counts"].items()
            }
        })
    return {
        "status":"POST_EXPOSURE_SIGNED_SOURCE_COLUMN_QC_ONLY",
        "source_unique_rows":len(rows),
        "qualified_for_both_published_distance_comparisons":eligible,
        "original_unsigned_release_final_matches":full_rf,
        "original_capture_final_matches":full_cf,
        "signed_metric_comparison":{
            f:{**v,"match_fraction":(v["matched"]/v["eligible_formula_rows"] if v["eligible_formula_rows"] else None)}
            for f,v in candidate_stats.items()
        },
        "direction_moved_vs_coordinate_delta_east_sign_counts":dict(sign_metadata),
        "signed_nominal_class_details":grouped,
        "source_record_scope":"same full original deduplicated publisher toad CSV; no row-level values saved",
        "original_scientific_stop":"STOP_GEO_UNIT_CONCORDANCE",
        "original_homing_result_scored":False,
        "original_stop_overridden":False,
        "source_diagnostic_is_post_exposure":True,
        "natural_founder_or_movement_inferred":False,
        "new_EOG_WF_endpoints":0
    }


def run(spec:dict[str,Any])->dict[str,Any]:
    if spec.get("status")!="PRE_SIGNED_FORMULA_TEST_FROZEN_POST_QC_EXPOSURE":
        raise ValueError("STOP_SOURCE_SIGN_PROTOCOL_NOT_FROZEN")
    parent=json.loads(PARENT.read_text(encoding="utf-8"))
    source=spec["parent_source"]
    if (source["csv_sha256"]!=parent["source"]["csv_sha256"] or
        source["bytes"]!=parent["source"]["csv_size_bytes"] or
        source["version_id"]!=parent["source"]["version_id"]):
        raise ValueError("STOP_ORIGINAL_CSV_IDENTITY_CHANGED")
    v2=json.loads(V2_GATE.read_text(encoding="utf-8"))
    limits=json.loads(V1_GATE.read_text(encoding="utf-8"))["resource_limits"]
    uri=f"https://datadryad.org/api/v2/versions/{source['version_id']}/download"
    data_zip,_=_version_zip(uri,limits,v2["exact_trusted_redirect_contract"])
    data=old._verified_member(data_zip,parent)
    del data_zip
    rows,grain=old._as_rows(data,parent)
    output=analyze_source_rows(rows,spec,parent)
    output["published_rows"]=grain["published_rows"]
    output["byte_identical_duplicates_removed"]=grain["exact_duplicate_rows_removed"]
    output["source_pub_doi"]=source["doi"]
    output["source_csv_sha256_pinned"]=source["csv_sha256"]
    output["original_publisher_checksum_verified"]=True
    if (grain["published_rows"]!=165 or len(rows)!=163 or
        output["qualified_for_both_published_distance_comparisons"]!=163 or
        output["original_unsigned_release_final_matches"]!=77 or
        output["original_capture_final_matches"]!=163):
        output["status"]="STOP_PARENT_QC_INVARIANT"
    return output


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    proto=json.loads(a.protocol.read_text(encoding="utf-8"))
    try:
        result=run(proto)
    except (ValueError,old.ScientificStop,OSError,urllib.error.URLError,zipfile.BadZipFile) as e:
        result={
            "status":str(e) if str(e).startswith("STOP_") else "STOP_SOURCE_TRANSPORT_OR_SCHEMA",
            "error_type":type(e).__name__,
            "original_scientific_stop":"STOP_GEO_UNIT_CONCORDANCE",
            "original_homing_result_scored":False,
            "original_stop_overridden":False,
            "new_EOG_WF_endpoints":0
        }
    result["sha256_without_self"]=_report_sha(result)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_scientific_stop":result["original_scientific_stop"],
        "source_unique_rows":result.get("source_unique_rows"),
        "original_release_matches":result.get("original_unsigned_release_final_matches"),
        "original_capture_matches":result.get("original_capture_final_matches"),
        "signed_comparison":result.get("signed_metric_comparison"),
        "nominal_groups":result.get("signed_nominal_class_details"),
        "direction_metadata":result.get("direction_moved_vs_coordinate_delta_east_sign_counts"),
        "receipt":result["sha256_without_self"],
        "new_EOG_WF_endpoints":0
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
