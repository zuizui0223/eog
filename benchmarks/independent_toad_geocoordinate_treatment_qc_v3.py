#!/usr/bin/env python3
"""Post-STOP toad reported-distance QC by NOMINAL translocation class (v3).

Source-publisher-locked exploratory data quality only: categories 0/100/250/500,
same source archive, same SHA, same original tolerance and original denominator.
Never reinterpret, re-score or overturn STOP_GEO_UNIT_CONCORDANCE.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import median
import urllib.error
import zipfile
from typing import Any

from benchmarks import independent_toad_source_anchor_geography_v1 as old
from benchmarks.independent_toad_geo_source_quality_diagnostic_v2 import _finite_ratio
from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/independent_toad_geocoordinate_diagnostic_v3/protocol_v3.json")
V2_GATE = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
V1_GATE = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
PARENT = Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json")
CATEGORIES = ("0", "100", "250", "500", "other_or_missing")


def _hash(x: object) -> str:
    body = json.dumps(x, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _number(value: object, missing: set[str]) -> float | None:
    try:
        return old._number(value, missing)
    except old.ScientificStop as exc:
        raise ValueError("STOP_NOMINAL_TREATMENT_FORMAT_OR_BAD_COORDINATE") from exc


def _category(value: object, missing: set[str]) -> str:
    n = _number(value, missing)
    if n is None:
        return "other_or_missing"
    for cat in ("0", "100", "250", "500"):
        if n == int(cat):
            return cat
    return "other_or_missing"


def _quantiles(values: list[float]) -> dict[str, float | None]:
    if len(values) < 5:
        return {"median_absolute_residual_m": None, "q90_absolute_residual_m": None}
    return {
        "median_absolute_residual_m": median(values),
        "q90_absolute_residual_m": _finite_ratio(values, 0.9),
    }


def stratified_coordinate_quality(
    rows: list[dict[str, str]], spec: dict[str, Any], parent: dict[str, Any]
) -> dict[str, Any]:
    """No per-event output; aggregate each predeclared treatment group."""
    groups: dict[str, dict[str, Any]] = {
        cat:{
            "all_original_deduplicated_rows":0,
            "eligible_reencounters_with_complete_coords":0,
            "distinct_toad_ids_with_complete_coords":0,
            "release_final_comparable":0,
            "release_final_matches":0,
            "capture_final_comparable":0,
            "capture_final_matches":0,
            "release_equals_capture_report_comparable":0,
            "release_equals_capture_report_matches":0,
            "zero_class_initial_to_release_le5m":0,
            "positive_class_initial_to_release_gt5m":0,
            "_ids":set(), "_release_residuals":[], "_capture_residuals":[]
        } for cat in CATEGORIES
    }
    missing = {str(x).strip().lower() for x in parent["data_contract"]["missing_values"]}
    all_count = 0
    eligible = 0
    full_rf = {"n":0,"match":0}
    full_if = {"n":0,"match":0}
    for row in rows:
        all_count += 1
        category = _category(row.get(spec["user_defined_treatment"]["source_field"]), missing)
        group = groups[category]
        group["all_original_deduplicated_rows"] += 1
        ident = str(row.get("Toad ID", "")).strip()
        when = str(row.get("Date of re-encounter", "")).strip()
        if ident.lower() in missing or when.lower() in missing:
            continue
        xyz = [_number(row.get(x), missing) for x in old.COORD_COLUMNS]
        if any(x is None for x in xyz):
            continue
        eligible += 1
        group["eligible_reencounters_with_complete_coords"] += 1
        group["_ids"].add(ident)
        I,R,F = ((xyz[0],xyz[1]),(xyz[2],xyz[3]),(xyz[4],xyz[5]))
        rf=old._distance(R,F)
        cf=old._distance(I,F)
        ir=old._distance(I,R)
        if category == "0" and ir <= 5.0:
            group["zero_class_initial_to_release_le5m"] += 1
        if category in ("100","250","500") and ir > 5.0:
            group["positive_class_initial_to_release_gt5m"] += 1
        observed_rf=_number(row.get("Distance release-final (m)"),missing)
        observed_cf=_number(row.get("Distance capture-final (m)"),missing)
        if observed_rf is not None:
            group["release_final_comparable"] += 1
            full_rf["n"] += 1
            d=abs(observed_rf-rf)
            group["_release_residuals"].append(d)
            if d <= max(2.0, 0.05*rf):
                group["release_final_matches"] += 1
                full_rf["match"] += 1
        if observed_cf is not None:
            group["capture_final_comparable"] += 1
            full_if["n"] += 1
            d=abs(observed_cf-cf)
            group["_capture_residuals"].append(d)
            if d <= max(2.0, 0.05*cf):
                group["capture_final_matches"] += 1
                full_if["match"] += 1
        if observed_rf is not None and observed_cf is not None:
            group["release_equals_capture_report_comparable"] += 1
            if abs(observed_rf-observed_cf) <= max(2.0,0.05*cf):
                group["release_equals_capture_report_matches"] += 1
    results = []
    for key, group in groups.items():
        ids = group.pop("_ids")
        release=group.pop("_release_residuals")
        capture=group.pop("_capture_residuals")
        group["distinct_toad_ids_with_complete_coords"] = len(ids)
        group["release_final_match_fraction"] = (
            group["release_final_matches"]/group["release_final_comparable"]
            if group["release_final_comparable"] else None
        )
        group["capture_final_match_fraction"] = (
            group["capture_final_matches"]/group["capture_final_comparable"]
            if group["capture_final_comparable"] else None
        )
        group["release_final_residuals"]=_quantiles(release)
        group["capture_final_residuals"]=_quantiles(capture)
        results.append({"nominal_translocated_distance_m":key, **group})
    return {
        "schema":"eog.independent_toad_geocoordinate_treatment_QC_v3",
        "status":"POST_EXPOSURE_TREATMENT_STRATIFIED_COORDINATE_QC_ONLY",
        "source_unique_rows":all_count,
        "eligible_complete_coordinate_reencounters":eligible,
        "grand_totals":{
            "release_final_numeric_rows":full_rf["n"],
            "release_final_matches":full_rf["match"],
            "capture_final_numeric_rows":full_if["n"],
            "capture_final_matches":full_if["match"],
        },
        "categories":results,
        "biological_movement_scored":False,
        "original_stop_overridden":False,
        "original_scientific_stop":"STOP_GEO_UNIT_CONCORDANCE",
        "data_values_read_for_source_QC_only":True,
        "no_row_level_data_exported":True,
        "new_eog_wf_endpoints":0,
    }


def run(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("status")!="FROZEN_AFTER_EXTERNAL_QC_STOP_BEFORE_GROUP_SCORING":
        raise ValueError("STOP_PROTOCOL_NOT_FROZEN")
    source = spec["data_source"]
    parent = json.loads(PARENT.read_text(encoding="utf-8"))
    expected = parent["source"]
    if source["csv_sha256"]!=expected["csv_sha256"] or source["csv_size_bytes"]!=expected["csv_size_bytes"]:
        raise ValueError("STOP_SOURCE_IDENTITY")
    v2 = json.loads(V2_GATE.read_text(encoding="utf-8"))
    lim = json.loads(V1_GATE.read_text(encoding="utf-8"))["resource_limits"]
    uri = f"https://datadryad.org/api/v2/versions/{source['version_id']}/download"
    if uri!=source["official_get"] or uri!=expected["official_download_url"]:
        raise ValueError("STOP_SOURCE_ENDPOINT_DRIFT")
    archive, _ = _version_zip(uri,lim,v2["exact_trusted_redirect_contract"])
    csv_bytes=old._verified_member(archive,parent)
    del archive
    rows, grain=old._as_rows(csv_bytes,parent)
    result=stratified_coordinate_quality(rows,spec,parent)
    result["original_165_rows"]=grain["published_rows"]
    result["exact_duplicates_removed"]=grain["exact_duplicate_rows_removed"]
    result["original_csv_sha256"]=source["csv_sha256"]
    result["publisher_version"]=source["version_id"]
    result["source_checksums_verified"]=True
    frozen={"release_final_numeric_rows":163,"release_final_matches":77,
        "capture_final_numeric_rows":163,"capture_final_matches":163}
    if result["grand_totals"]!=frozen or result["source_unique_rows"]!=163 or grain["published_rows"]!=165:
        result["status"]="STOP_PARENT_QC_INVARIANT"
    result["new_eog_wf_endpoints"]=0
    result["original_stop_overridden"]=False
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    spec=json.loads(args.protocol.read_text(encoding="utf-8"))
    try:
        result=run(spec)
    except (ValueError,old.ScientificStop,OSError,urllib.error.URLError,zipfile.BadZipFile) as ex:
        result={
            "status":str(ex) if str(ex).startswith("STOP_") else "STOP_SOURCE_ACCESS",
            "exception_class":type(ex).__name__,
            "original_scientific_stop":"STOP_GEO_UNIT_CONCORDANCE",
            "original_stop_overridden":False,
            "new_eog_wf_endpoints":0,
            "biological_movement_scored":False,
            "no_row_level_data_exported":True
        }
    result["sha256_without_self"]=_hash(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],"source_unique_rows":result.get("source_unique_rows"),
        "original_stop":result["original_scientific_stop"],"grand_totals":result.get("grand_totals"),
        "categories":result.get("categories"),"sha256":result["sha256_without_self"],
        "new_eog_wf_endpoints":0
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
