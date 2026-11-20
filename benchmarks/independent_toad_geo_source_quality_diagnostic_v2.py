#!/usr/bin/env python3
"""Post-exposure toad-coordinate SOURCE QUALITY diagnostic, NEVER outcome scoring.

The earlier independently frozen toad source-anchor experiment ended in
STOP_GEO_UNIT_CONCORDANCE. This separate, protocol-first diagnostic tests
all 18 *predeclared* reported-distance / geometric-pair / scale combinations
and preserves the original STOP regardless of apparent alternative matches.

All original 165 published rows are source-locked; only aggregate QC exits.
No individual identifiers, original coordinates, dates or animal movements
are stored or printed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median
import hashlib
import math
import urllib.error
import zipfile
from typing import Any

from benchmarks import independent_toad_source_anchor_geography_v1 as old
from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/independent_toad_geocoordinate_diagnostic_v2/protocol_v2.json")
SOURCE_GATE = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
SOURCE_GATE_V1 = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
PARENT = Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json")


def _finite_ratio(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lo = math.floor(position)
    hi = math.ceil(position)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi-position) + ordered[hi] * (position-lo)


def diagnose_clean_rows(
    rows: list[dict[str, str]], protocol: dict[str, Any],
    parent: dict[str, Any],
) -> dict[str, Any]:
    """Compute just predeclared aggregate consistency; never a movement outcome."""
    wanted = protocol["comparison_grid"]
    pairs = wanted["candidate_geometric_pairs"]
    multipliers = wanted["coordinate_multipliers"]
    cols = wanted["two_published_columns"]
    if pairs != ["RF", "IF", "IR"] or cols != list(old.DIST_COLUMNS):
        raise ValueError("STOP_FROZEN_QC_PAIR_OR_CHANNEL_DRIFT")
    if multipliers != [0.001, 1, 1000]:
        raise ValueError("STOP_FROZEN_QC_UNIT_SCALE_DRIFT")
    missing = {x.lower() for x in parent["data_contract"]["missing_values"]}
    total = 0
    with_identity = 0
    dated = 0
    coord_complete = 0
    both_distance_missing = 0
    per_column_present = {col:0 for col in cols}
    IDs = set()
    compared: dict[tuple[str,str,float], dict[str, Any]] = {
        (c,p,float(k)):{"absolute_errors":[],"match_count":0,"total":0}
        for c in cols for p in pairs for k in multipliers
    }
    for item in rows:
        total += 1
        ident = str(item["Toad ID"]).strip()
        if ident.lower() in missing:
            continue
        with_identity += 1
        IDs.add(ident)
        timestamp = str(item["Date of re-encounter"]).strip()
        if timestamp.lower() in missing:
            continue
        dated += 1
        co = [old._number(item[x],missing) for x in old.COORD_COLUMNS]
        if any(x is None for x in co):
            continue
        coord_complete += 1
        I,R,F=((co[0],co[1]),(co[2],co[3]),(co[4],co[5]))
        reference={k:old._number(item[k],missing) for k in cols}
        if all(v is None for v in reference.values()):
            both_distance_missing += 1
            continue
        geo={
            "RF":old._distance(R,F),
            "IF":old._distance(I,F),
            "IR":old._distance(I,R),
        }
        for col in cols:
            reported=reference[col]
            if reported is None:
                continue
            per_column_present[col]+=1
            for pair in pairs:
                for scale in multipliers:
                    calc=geo[pair]*scale
                    err=abs(reported-calc)
                    stat=compared[col,pair,float(scale)]
                    stat["total"]+=1
                    stat["absolute_errors"].append(err)
                    if err<=max(2.,0.05*calc):
                        stat["match_count"]+=1
    output_grid=[]
    for col in cols:
        for p in pairs:
            for scale in multipliers:
                v=compared[col,p,float(scale)]
                n=v["total"]
                output_grid.append({
                    "reported_column":col,
                    "geometric_pair":p,
                    "coordinate_multiplier":scale,
                    "numeric_compared_rows":n,
                    "matched_rows":v["match_count"],
                    "match_fraction":(v["match_count"]/n if n else None),
                    "median_absolute_residual_m":(
                        median(v["absolute_errors"]) if n else None
                    ),
                    "q90_absolute_residual_m":_finite_ratio(v["absolute_errors"],0.9),
                    "comparison_type":"DIAGNOSTIC_ONLY_NOT_AN_AUTHORIZED_REMAP",
                })
    channel_rules={
        "Distance release-final (m)":"RF",
        "Distance capture-final (m)":"IF",
    }
    original={}
    for col,pair in channel_rules.items():
        match=next(x for x in output_grid if x["reported_column"]==col
            and x["geometric_pair"]==pair and x["coordinate_multiplier"]==1)
        original[col]={
            "numeric_compared_rows":match["numeric_compared_rows"],
            "geometric_match_fraction_under_original_tolerance":match["match_fraction"],
            "below_original_95pct_quality_gate":(
                match["match_fraction"] is None or match["match_fraction"]<0.95
            )
        }
    return {
      "status":"POST_EXPOSURE_SOURCE_QC_ONLY_RETAINS_ORIGINAL_SCIENTIFIC_STOP",
      "denominator":{
        "source_unique_rows":total,
        "with_nonmissing_identity":with_identity,
        "distinct_identity_count":len(IDs),
        "nonmissing_reencounter_date":dated,
        "date_and_six_coordinate_values_present":coord_complete,
        "both_published_distance_columns_missing_on_complete_geometry":both_distance_missing,
        "present_numeric_distance_by_column":per_column_present
      },
      "original_gate_reconstruction":original,
      "original_STOP_GEO_UNIT_CONCORDANCE_reproduced":any(
          v["below_original_95pct_quality_gate"] for v in original.values()
      ),
      "predeclared_18_comparisons":output_grid,
      "n_diagnostic_comparisons":len(output_grid),
      "source_analyzed_for_movement_outcomes":False,
      "biological_direction_or_homing_estimated":False,
      "source_reassignment_or_original_STOP_override":False,
      "claim_boundary":"Outcome-free post-exposure aggregate coordinate-QC only. Does not override original scored STOP, independently confirm origin, or validate EOG minrelax."
    }


def run(protocol: dict[str, Any]) -> dict[str, Any]:
    if protocol.get("status")!="PRE_DIAGNOSTIC_FROZEN_AFTER_ORIGINAL_SCIENTIFIC_STOP":
        raise ValueError("STOP_DIAGNOSTIC_NOT_PREDECLARED")
    parent=json.loads(PARENT.read_text(encoding="utf-8"))
    if parent["status"]!="FROZEN_BEFORE_TOAD_EVENT_VALUES_READ":
        raise ValueError("STOP_PARENT_PROTOCOL_CHANGED")
    source=protocol["source"]
    psource=parent["source"]
    if any([
        source["expected_sha256"]!=psource["csv_sha256"],
        source["expected_bytes"]!=psource["csv_size_bytes"],
        source["version_id"]!=psource["version_id"],
        source["expected_data_rows"]!=psource["entire_csv_source_only_rows"],
    ]):
        raise ValueError("STOP_ORIGINAL_SOURCE_IDENTITY_CHANGED")
    v2=json.loads(SOURCE_GATE.read_text(encoding="utf-8"))
    limits=json.loads(SOURCE_GATE_V1.read_text(encoding="utf-8"))["resource_limits"]
    official=f"https://datadryad.org/api/v2/versions/{source['version_id']}/download"
    archive,_=_version_zip(official,limits,v2["exact_trusted_redirect_contract"])
    file=old._verified_member(archive,parent)
    del archive
    parsed,original_grain=old._as_rows(file,parent)
    result=diagnose_clean_rows(parsed,protocol,parent)
    if result["denominator"]["source_unique_rows"]!=original_grain["unique_raw_rows_after_byte_exact_dedup"]:
        raise ValueError("STOP_QC_ROW_COUNT_INCONSISTENT")
    result["original_row_grain"]=original_grain
    result["source_publication_doi"]=source["doi"]
    result["source_publisher_sha256_verified"]=True
    result["parent_original_science_status"]=protocol["parent_result"]["outcome"]
    result["parent_original_science_verdict"]=protocol["parent_result"]["primary_verdict"]
    result["parent_status_may_be_promoted"]=False
    result["source_status"]="PINNED_PUBLISHER_ARCHIVE_VERIFIED"
    if not result["original_STOP_GEO_UNIT_CONCORDANCE_reproduced"]:
        result["status"]="STOP_DIAGNOSTIC_CANNOT_REPRODUCE_ORIGINAL_SCIENTIFIC_STOP"
    result["new_eog_wf_endpoints"]=0
    result["raw_source_records_exported"]=0
    result["raw_coordinates_or_ids_exported"]=0
    result["model_fits"]=0
    return result


def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    opts=p.parse_args()
    protocol=json.loads(opts.protocol.read_text(encoding="utf-8"))
    try:
        res=run(protocol)
    except (ValueError,RuntimeError,urllib.error.URLError,OSError,zipfile.BadZipFile) as exc:
        res={
          "status":str(exc) if str(exc).startswith("STOP_") else "STOP_SOURCE_TRANSFER_OR_SCHEMA",
          "error_type":type(exc).__name__,
          "parent_original_science_status":protocol["parent_result"]["outcome"],
          "parent_status_may_be_promoted":False,
          "source_analyzed_for_movement_outcomes":False,
          "new_eog_wf_endpoints":0,
          "raw_source_records_exported":0,
          "model_fits":0
        }
    canonical=json.dumps(res,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+"\n"
    res["sha256_without_self"]=hashlib.sha256(canonical.encode()).hexdigest()
    opts.output.parent.mkdir(parents=True,exist_ok=True)
    opts.output.write_text(json.dumps(res,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+"\n")
    print(json.dumps({
      "status":res["status"],
      "parent_stop_preserved":res["parent_original_science_status"],
      "qc_reproduced":res.get("original_STOP_GEO_UNIT_CONCORDANCE_reproduced"),
      "original_concordance":res.get("original_gate_reconstruction"),
      "source_rows":res.get("original_row_grain",{}).get("published_rows"),
      "diagnostic_cell_count":res.get("n_diagnostic_comparisons"),
      "new_EOG_WF_endpoints":0,
      "aggregate_sha256":res["sha256_without_self"]
    },sort_keys=True))
if __name__=="__main__":
    main()
