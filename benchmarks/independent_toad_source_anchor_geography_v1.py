#!/usr/bin/env python3
"""Externally published toad source-anchor geography, frozen before outcomes.

This is a geographically measured individual release-vs-historical-capture
anchor stress test, not natural founder inference, colonization or the
three-axis EOG-MRR. Never archive original individual IDs, coordinates, dates,
source rows or any individual derived scores. Output aggregates only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
from statistics import mean, median
from typing import Any
import zipfile

from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/independent_toad_source_anchor_geography_v1/protocol_v1.json")
PUBLISHER_TRANSFER = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
PUBLISHER_GATE = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
COORD_COLUMNS = (
    "Initial Easting", "Initial Northing",
    "Released Easting", "Released Northing",
    "Final Easting", "Final Northing",
)
DIST_COLUMNS = ("Distance release-final (m)", "Distance capture-final (m)")


class ScientificStop(ValueError):
    """Do not convert a scientific source/quality STOP to an ecological effect."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_hash(obj: dict[str, Any]) -> str:
    return _digest(
        (json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False)+"\n").encode("utf-8")
    )


def _number(value: object, tokens: set[str]) -> float | None:
    if value is None:
        return None
    literal = str(value).strip()
    if literal.lower() in tokens:
        return None
    try:
        n = float(literal)
    except (ValueError, OverflowError) as exc:
        raise ScientificStop("STOP_UNDECLARED_NUMERIC_FORMAT") from exc
    if not math.isfinite(n):
        raise ScientificStop("STOP_NONFINITE_NUMERIC_VALUE")
    return n


def _distance(x: tuple[float, float], y: tuple[float, float]) -> float:
    return math.hypot(x[0]-y[0],x[1]-y[1])


def _as_rows(csv_bytes: bytes, protocol: dict[str, Any]) -> tuple[list[dict[str,str]],dict[str,int]]:
    source = protocol["source"]
    if len(csv_bytes) != source["csv_size_bytes"] or _digest(csv_bytes) != source["csv_sha256"]:
        raise ScientificStop("STOP_ORIGINAL_PUBLISHER_CSV_SHA256_OR_SIZE_MISMATCH")
    if b"\x00" in csv_bytes:
        raise ScientificStop("STOP_SOURCE_CSV_NUL_BYTES")
    text = csv_bytes.decode("utf-8-sig")
    # Byte-identical duplicate rows are the ONLY permitted duplicate deletion.
    # Refuse multiline CSV rather than misrepresenting one logical row as raw lines.
    lines = csv_bytes.splitlines()
    parsed = list(csv.reader(io.StringIO(text,newline="")))
    if len(parsed)!=len(lines) or not parsed or len(lines)-1!=source["entire_csv_source_only_rows"]:
        raise ScientificStop("STOP_ORIGINAL_CSV_ROW_GRAIN_OR_ROWCOUNT")
    header=parsed[0]
    if len(set(header))!=len(header) or not set(source["required_columns"]).issubset(header):
        raise ScientificStop("STOP_ORIGINAL_SOURCE_HEADER_DRIFT")
    if any(len(row)!=len(header) for row in parsed[1:]):
        raise ScientificStop("STOP_CSV_ROW_WIDTH")
    unique=[]
    seen:set[bytes]=set()
    duplicates=0
    for raw, fields in zip(lines[1:],parsed[1:],strict=True):
        if raw in seen:
            duplicates+=1
            continue
        seen.add(raw)
        unique.append(dict(zip(header,fields,strict=True)))
    return unique,{"published_rows":len(lines)-1,"exact_duplicate_rows_removed":duplicates,
                   "unique_raw_rows_after_byte_exact_dedup":len(unique)}


def _verified_member(archive: bytes, protocol: dict[str, Any]) -> bytes:
    source = protocol["source"]
    published = json.loads(PUBLISHER_TRANSFER.read_text(encoding="utf-8"))
    toad = next(x for x in published["sources"] if x["id"]=="toad_jreidini_green_2022")
    if toad["doi"] != source["doi"] or toad["version_id"] != source["version_id"]:
        raise ScientificStop("STOP_FROZEN_SOURCE_IDENTITY_DRIFT")
    expected={x["name"]:x for x in toad["expected"]}
    if not zipfile.is_zipfile(io.BytesIO(archive)):
        raise ScientificStop("STOP_OFFICIAL_VERSION_NOT_ZIP")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        members=[x for x in z.infolist() if not x.is_dir()]
        names=[]
        for x in members:
            p=x.filename.replace("\\","/")
            if p.startswith("/") or ".." in p.split("/"):
                raise ScientificStop("STOP_UNSAFE_ZIP_PATH")
            names.append(PurePosixPath(p).name)
        if len(set(names)) != len(names) or set(names)!=set(expected):
            raise ScientificStop("STOP_ORIGINAL_PUBLISHER_ZIP_MEMBERS_CHANGED")
        for item, name in zip(members,names,strict=True):
            original=z.read(item)
            if len(original)!=expected[name]["size"] or _digest(original)!=expected[name]["sha256"]:
                raise ScientificStop("STOP_ORIGINAL_PUBLISHER_MEMBER_SHA256_OR_SIZE")
            if name==source["csv_name"]:
                selected=original
    return selected


def _analyze_verified_csv(data: bytes, protocol: dict[str, Any]) -> dict[str, Any]:
    clean, grain = _as_rows(data,protocol)
    tokens={x.lower() for x in protocol["data_contract"]["missing_values"]}
    minimum=protocol["data_contract"]["min_eligible_individuals_for_directional_summary"]
    triangle_tol=protocol["data_contract"]["triangle_tolerance_meters"]
    missing_counts={"missing_toad_id":0,"missing_reencounter_date":0,
                    "missing_at_least_one_coordinate":0,"reencounter_and_all_coordinates":0}
    checks={x:{"with_published_distance":0,"geometric_matches":0,"mismatches":0}
            for x in DIST_COLUMNS}
    eligible_events:dict[str,list[dict[str,Any]]]={
        "relocated":[],"sham":[],"intermediate":[]
    }
    unique_ids:set[str]=set()
    for row in clean:
        identity=str(row["Toad ID"]).strip()
        if identity.lower() in tokens:
            missing_counts["missing_toad_id"]+=1
            continue
        unique_ids.add(identity)
        date=str(row["Date of re-encounter"]).strip()
        if date.lower() in tokens:
            missing_counts["missing_reencounter_date"]+=1
            continue
        coords=[_number(row[k],tokens) for k in COORD_COLUMNS]
        if any(v is None for v in coords):
            missing_counts["missing_at_least_one_coordinate"]+=1
            continue
        missing_counts["reencounter_and_all_coordinates"]+=1
        assert all(v is not None for v in coords)
        I=(coords[0],coords[1])
        R=(coords[2],coords[3])
        F=(coords[4],coords[5])
        d_ir=_distance(I,R)
        d_rf=_distance(R,F)
        d_if=_distance(I,F)
        delta=d_rf-d_if
        if abs(delta)>d_ir+triangle_tol:
            raise ScientificStop("STOP_TRIANGLE_INEQUALITY_MISMATCH")
        for col,computed in zip(DIST_COLUMNS,(d_rf,d_if),strict=True):
            val=_number(row[col],tokens)
            if val is None:
                continue
            checks[col]["with_published_distance"]+=1
            tolerance=max(2.0, 0.05*computed)
            if abs(val-computed)<=tolerance:
                checks[col]["geometric_matches"]+=1
            else:
                checks[col]["mismatches"]+=1
        if d_ir>=protocol["data_contract"]["relocated"].startswith("d_IR"): # placeholder guarded below
            pass
        if d_ir>=90.0:
            cat="relocated"
        elif d_ir<=5.0:
            cat="sham"
        else:
            cat="intermediate"
        eligible_events[cat].append({
            "id":identity,"d_ir":d_ir,"d_rf":d_rf,"d_if":d_if,
            "delta":delta, "anchor_width":abs(delta),
        })
    numeric_quality={}
    for col,qty in checks.items():
        n=qty["with_published_distance"]
        frac=qty["geometric_matches"]/n if n else None
        numeric_quality[col]={**qty,"match_fraction":frac}
    # At least 95% of each nonempty published-distance channel must match.
    if any(q["with_published_distance"]==0 or q["match_fraction"]<0.95
           for q in numeric_quality.values()):
        raise ScientificStop("STOP_GEO_UNIT_CONCORDANCE")
    category_summary={}
    group_cache={}
    for cat,rows in eligible_events.items():
        groups:dict[str,list[dict[str,Any]]]=defaultdict(list)
        for event in rows:
            groups[event["id"]].append(event)
        grouped=[]
        for events in groups.values():
            grouped.append({
                key:mean(evt[key] for evt in events)
                for key in ("d_ir","d_rf","d_if","delta","anchor_width")
            })
        group_cache[cat]=grouped
        category_summary[cat]={
            "eligible_event_rows":len(rows),
            "distinct_individuals":len(grouped),
            "individuals_with_multiple_eligible_events":sum(len(v)>1 for v in groups.values()),
            "positive_delta_individuals":sum(v["delta"]>1e-9 for v in grouped),
            "zero_delta_individuals":sum(abs(v["delta"])<=1e-9 for v in grouped),
            "negative_delta_individuals":sum(v["delta"]< -1e-9 for v in grouped),
        }
    summary={
        "schema":"eog.independent_toad_source_anchor_geography.v1.result",
        "status":"STOP_PENDING_QUALITY",
        "input":"SHA256_PINNED_OFFICIAL_TOAD_RECAPTURE_EXPERIMENT",
        "source_doi":protocol["source"]["doi"],
        "source_version_id":protocol["source"]["version_id"],
        "original_row_grain":grain,
        "distinct_ids_in_nonduplicate_rows":len(unique_ids),
        "eligible_and_missing":missing_counts,
        "published_distance_concordance":numeric_quality,
        "category_counts":category_summary,
        "independent_ecological_populations":1,
        "new_EOG_WF_endpoints":0,
        "three_axis_abiotic_biotic_barrier_MRR_tested":False,
        "historical_founder_or_natural_dispersal_inferred":False,
        "claim_boundary":"Experimental individual release/capture anchors; not natural colonization, causal environment or dispersal kernel."
    }
    subjects=group_cache["relocated"]
    if len(subjects)<minimum:
        summary["status"]="STOP_MINIMUM_ELIGIBLE_RELOCATED_INDIVIDUALS"
        summary["primary_verdict"]="NOT_SCORED_SOURCE_QUALITY_STOP"
        return summary
    contrasts=[x["delta"] for x in subjects]
    summary["status"]="EXPLORATORY_EXTERNAL_RECAPTURE_SOURCE_ANCHOR_GEOGRAPHY_SCORED"
    summary["primary_verdict"]=(
        "SUPPORTED_POST_PUBLICATION_CONDITIONAL_GEOGRAPHY"
        if mean(contrasts)>0 else "REFUTED_OR_NOT_SUPPORTED"
    )
    summary["primary"]={
        "name":"Equal-individual-weighted source-anchor contrast: d(release,final)-d(capture,final)",
        "n_individuals":len(subjects),
        "mean_delta_m":mean(contrasts),
        "median_delta_m":median(contrasts),
        "positive_individuals":category_summary["relocated"]["positive_delta_individuals"],
        "zero_individuals":category_summary["relocated"]["zero_delta_individuals"],
        "negative_individuals":category_summary["relocated"]["negative_delta_individuals"],
        "mean_possible_radius_m":mean(min(x["d_rf"],x["d_if"]) for x in subjects),
        "mean_source_robust_radius_m":mean(max(x["d_rf"],x["d_if"]) for x in subjects),
        "mean_ambiguity_width_m":mean(x["anchor_width"] for x in subjects),
        "mean_normalized_delta":mean(x["delta"]/max(x["d_ir"],1) for x in subjects),
    }
    radius_rows=[]
    for rad in protocol["inferential_targets"]["thresholds_meters"]:
        k={"radius_m":rad}
        gate={
            "release_valid":lambda x:x["d_rf"]<=rad,
            "historical_capture_valid":lambda x:x["d_if"]<=rad,
            "possible_source_valid":lambda x:min(x["d_rf"],x["d_if"])<=rad,
            "source_robust_valid":lambda x:max(x["d_rf"],x["d_if"])<=rad,
            "historical_false_assurance":lambda x:x["d_if"]<=rad<x["d_rf"],
            "converse_release_only":lambda x:x["d_rf"]<=rad<x["d_if"],
        }
        for label,criterion in gate.items():
            k[label+"_individuals"]=sum(criterion(x) for x in subjects)
        radius_rows.append(k)
    summary["radius_thresholds_by_individual_mean_event_distance"]=radius_rows
    shams=group_cache["sham"]
    summary["sham_h3_control"]={
        "n_individuals":len(shams),
        "max_mean_anchor_width_m":max((x["anchor_width"] for x in shams),default=None),
        "violations":sum(x["anchor_width"]>5.0+triangle_tol for x in shams),
    }
    if summary["sham_h3_control"]["violations"]:
        raise ScientificStop("STOP_SHAM_TRIANGLE_CONTROL_FAILED")
    return summary


def run(protocol: dict[str, Any]) -> dict[str, Any]:
    if protocol.get("status")!="FROZEN_BEFORE_TOAD_EVENT_VALUES_READ":
        raise ScientificStop("STOP_SOURCE_PROTOCOL_NOT_FROZEN")
    upstream=json.loads(PUBLISHER_TRANSFER.read_text(encoding="utf-8"))
    limits=json.loads(PUBLISHER_GATE.read_text(encoding="utf-8"))["resource_limits"]
    contract=upstream["exact_trusted_redirect_contract"]
    endpoint=protocol["source"]["official_download_url"]
    expected=f"https://datadryad.org/api/v2/versions/{protocol['source']['version_id']}/download"
    if endpoint!=expected:
        raise ScientificStop("STOP_SOURCE_ENDPOINT_CHANGED")
    archive,_=_version_zip(endpoint,limits,contract)
    data=_verified_member(archive,protocol)
    del archive
    return _analyze_verified_csv(data,protocol)


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,default=PROTOCOL)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    try:
        result=run(protocol)
    except ScientificStop as e:
        result={
            "schema":"eog.independent_toad_source_anchor_geography.v1.result",
            "status":str(e), "primary_verdict":"NOT_SCORED_SOURCE_QUALITY_STOP",
            "new_EOG_WF_endpoints":0,
            "original_raw_data_persisted":False,
            "source_doi":protocol["source"]["doi"],
        }
    except Exception as e:
        # Networking/version/SSL exceptions are source access STOPs, not biology.
        if isinstance(e,(OSError,zipfile.BadZipFile,ValueError)):
            result={
                "schema":"eog.independent_toad_source_anchor_geography.v1.result",
                "status":"STOP_PUBLIC_SOURCE_ACCESS_OR_ZIP",
                "diagnostic_exception_type":type(e).__name__,
                "primary_verdict":"NOT_SCORED_SOURCE_QUALITY_STOP",
                "new_EOG_WF_endpoints":0,
                "original_raw_data_persisted":False,
            }
        else:
            raise
    result["original_raw_data_persisted"]=False
    result["sha256_without_self_field"]=_canonical_hash(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n")
    # No row-level values or IDs ever printed.
    print(json.dumps({"status":result["status"],
         "primary_verdict":result.get("primary_verdict"),
         "n_relocated_individuals":result.get("primary",{}).get("n_individuals"),
         "mean_delta_m":result.get("primary",{}).get("mean_delta_m"),
         "new_eog_wf_endpoints":0,
         "fingerprint":result["sha256_without_self_field"]},sort_keys=True))


if __name__=="__main__":
    main()
