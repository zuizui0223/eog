#!/usr/bin/env python3
"""Published banding-derived Arctic tern colony source vs existential MRR geometry.

This is a post-publication external ecological EVENT-level descriptive audit,
not true dispersal trajectory, as-of source identification, or EOG-WF prediction.
The source is pinned by Dryad v466530's five original file SHA256 digests.
No individual event rows/positions are emitted or committed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from math import asin, cos, isfinite, radians, sin, sqrt
from pathlib import Path, PurePosixPath
from statistics import mean, median
import urllib.error
import zipfile
from typing import Any

from scripts.eog_independent_movement_source_gate_v2 import _version_zip

PROTOCOL = Path("validation/tern_known_origin_geographic_minrelax_v1/protocol_v1.json")
V2_SOURCE = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
V1_SOURCE = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
META = Path("validation/tern_published_departure_source_gate_v1/frozen_metadata_summary_v1.json")
CORE = ("UID","depart_lat","depart_lon","arrive_lat","arrive_lon","year","distance_km","direction_deg")


class ScientificStop(ValueError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _fingerprint(obj: dict[str, Any]) -> str:
    return _sha((json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+"\n").encode("utf-8"))


def _read_source_zip(archive_bytes: bytes, protocol: dict[str, Any]) -> dict[str, bytes]:
    """Validate complete source ZIP and five SHA bytes BEFORE CSV decode."""
    pinned=protocol["source_frozen"]
    expected={x["name"]:x for x in pinned["exact_files"]}
    if len(archive_bytes)>pinned["archive_max_bytes"] or not zipfile.is_zipfile(io.BytesIO(archive_bytes)):
        raise ScientificStop("STOP_ARCHIVE_SIZE_OR_ZIP")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        entries=[f for f in z.infolist() if not f.is_dir()]
        if len(entries)!=pinned["max_members"] or sum(f.file_size for f in entries)>pinned["max_uncompressed_bytes"]:
            raise ScientificStop("STOP_PUBLISHER_ARCHIVE_MEMBERS_OR_UNCOMPRESSED_BUDGET")
        located:dict[str,zipfile.ZipInfo]={}
        for e in entries:
            path=e.filename.replace("\\","/")
            if path.startswith("/") or ".." in path.split("/"):
                raise ScientificStop("STOP_UNSAFE_PUBLISHER_ZIP_MEMBER")
            name=PurePosixPath(path).name
            if name in located or name not in expected:
                raise ScientificStop("STOP_PUBLISHER_FILE_ROSTER_DRIFT")
            located[name]=e
        if set(located)!=set(expected):
            raise ScientificStop("STOP_PUBLISHER_FILE_ROSTER_DRIFT")
        chosen={}
        for name,entry in located.items():
            raw=z.read(entry)
            target=expected[name]
            if len(raw)!=target["size_bytes"] or _sha(raw)!=target["sha256"]:
                raise ScientificStop("STOP_PUBLISHER_SHA256_OR_BYTE_IDENTITY")
            if name in ("Ad_DaD.csv","U_DaD.csv"):
                chosen[name]=raw
        if len(chosen)!=2:
            raise ScientificStop("STOP_MISSING_EVENT_TABLES")
        return chosen


def _float(raw: object, key: str) -> float:
    if raw is None or str(raw).strip()=="":
        raise ScientificStop("STOP_MISSING_PUBLISHER_EVENT_COLUMN_"+key)
    try:
        value=float(raw)
    except (ValueError,TypeError,OverflowError) as ex:
        raise ScientificStop("STOP_BAD_PUBLISHER_EVENT_NUMERIC_"+key) from ex
    if not isfinite(value):
        raise ScientificStop("STOP_NONFINITE_PUBLISHER_EVENT_VALUE_"+key)
    return value


def _parse_event_table(raw: bytes, target: dict[str, Any]) -> list[dict[str, Any]]:
    if b"\x00" in raw:
        raise ScientificStop("STOP_SOURCE_CSV_NULL_BYTES")
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    if reader.fieldnames != list(CORE):
        raise ScientificStop("STOP_PUBLISHER_EVENT_HEADER_SCHEMA")
    seen=set()
    rows=[]
    for row in reader:
        uid=str(row.get("UID") or "").strip()
        if not uid or uid in seen:
            raise ScientificStop("STOP_DUPLICATE_OR_MISSING_EVENT_UID")
        seen.add(uid)
        year_float=_float(row["year"],"year")
        if int(year_float)!=year_float:
            raise ScientificStop("STOP_EVENT_YEAR_NON_INTEGER")
        year=int(year_float)
        if not target["expected_year_min"]<=year<=target["expected_year_max"]:
            raise ScientificStop("STOP_EVENT_YEAR_OUTSIDE_PUBLISHER_SCOPE")
        coords=tuple(_float(row[k],k) for k in CORE[1:5])
        latd,lond,lata,lona=coords
        if not (-90<=latd<=90 and -90<=lata<=90 and -180<=lond<=180 and -180<=lona<=180):
            raise ScientificStop("STOP_OUT_OF_WGS84_COORDINATE_RANGE")
        if any(abs(v-round(v,2))>1e-8 for v in coords):
            raise ScientificStop("STOP_COORDINATE_PRECISION_NOT_0P01_DEGREE")
        distance=_float(row["distance_km"],"distance_km")
        heading=_float(row["direction_deg"],"direction_deg")
        if distance<0 or not -180<=heading<=180:
            raise ScientificStop("STOP_PUBLISHED_DISTANCE_OR_BEARING_DOMAIN")
        rows.append({
            "UID":uid, "year":year,
            "origin":(latd,lond),
            "arrival":(lata,lona),
            "publisher_distance_km":distance,
        })
        if len(rows)>target["rows"]:
            raise ScientificStop("STOP_EXCESS_PUBLISHER_EVENT_ROWS")
    if len(rows)!=target["rows"]:
        raise ScientificStop("STOP_PUBLISHER_EVENT_COUNT_DRIFT")
    return rows


def _greatcircle_km(p:tuple[float,float],q:tuple[float,float],R:float) -> float:
    # For very short source-anchor contrasts, haversine is numerically stable.
    p1,l1,p2,l2=map(radians,(p[0],p[1],q[0],q[1]))
    h=sin((p2-p1)/2)**2+cos(p1)*cos(p2)*sin((l2-l1)/2)**2
    return R*2*asin(min(1.,sqrt(max(0.,h))))


def _quantiles(numbers: list[float]) -> dict[str, float | None]:
    if not numbers:
        return {"mean":None,"median":None}
    return {"mean":mean(numbers),"median":median(numbers)}


def analyze_events(
    by_type: dict[str, list[dict[str, Any]]],
    protocol:dict[str,Any],
) -> dict[str, Any]:
    """All holdout *event* rows retained; source catalog only <=1975 departures."""
    model=protocol["frozen_estimands"]
    sc=protocol["source_inference"]
    qa=protocol["no_leakage_and_QA"]
    R=float(model["earth_radius_km"])
    early_year=1975  # also locked in the protocol's historical alternative source
    all_rows=[(label,row) for label,rows in by_type.items() for row in rows]
    expected_counts={x["type"]:x["rows"] for x in protocol["source_frozen"]["expected_csvs"]}
    if set(by_type)!=set(expected_counts) or any(len(by_type[x])!=expected_counts[x] for x in by_type):
        raise ScientificStop("STOP_EVENT_TYPE_OR_DENOMINATOR_CHANGED")
    historical=sorted({
        row["origin"] for label,row in all_rows if row["year"]<=early_year
    })
    if len(historical)<qa["min_retrospective_reference_source_sites"]:
        raise ScientificStop("STOP_INSUFFICIENT_HISTORIC_DEPARTURE_SOURCE_CATALOG")
    audit=Counter()
    for label,row in all_rows:
        actual=_greatcircle_km(row["origin"],row["arrival"],R)
        deviation=abs(actual-row["publisher_distance_km"])
        audit[label+"_total"]+=1
        audit[label+"_distance_compared"]+=1
        if deviation<=2.0:
            audit[label+"_distance_match"]+=1
        if row["year"]<=early_year:
            audit[label+"_historical_event_count"]+=1
    total_match=sum(audit[k] for k in audit if k.endswith("_distance_match"))
    if total_match<0.95*sum(expected_counts.values()):
        raise ScientificStop("STOP_PUBLISHED_DISTANCE_GEO_CONCORDANCE")
    groups={}
    for group in sorted(by_type):
        eligible=[x for x in by_type[group] if x["year"]>early_year]
        if len(eligible)<qa["min_holdout_events_per_group"]:
            raise ScientificStop("STOP_INSUFFICIENT_POST_CUTOFF_EVENT_ROWS_"+group)
        comparisons=[]
        for row in eligible:
            actual=_greatcircle_km(row["origin"],row["arrival"],R)
            # Avoid using any post-1975 event's arrival or source to construct
            # the historical index; known actual origin is admitted explicitly.
            catalog_min=min(_greatcircle_km(c,row["arrival"],R) for c in historical)
            possible=min(actual,catalog_min)
            gap=actual-possible
            if gap < -1e-9:
                raise ScientificStop("STOP_MRR_SOURCE_MINIMUM_ORDER_VIOLATION")
            comparisons.append({"actual":actual,"possible":possible,"gap":gap})
        rs=[]
        for radius in model["prespecified_thresholds_km"]:
            actual_valid=sum(x["actual"]<=radius for x in comparisons)
            possible_valid=sum(x["possible"]<=radius for x in comparisons)
            assurance=sum(x["actual"]>radius and x["possible"]<=radius for x in comparisons)
            strong=sum(x["actual"]>radius+2 and x["possible"]<radius-2 for x in comparisons)
            original_infeasible=sum(x["actual"]>radius for x in comparisons)
            if possible_valid<actual_valid or strong>assurance:
                raise ScientificStop("STOP_MRR_RADIUS_LOGIC_VIOLATION")
            rs.append({
                "radius_km":radius,
                "actual_marked_source_feasible":actual_valid,
                "some_retrospective_source_feasible":possible_valid,
                "source_agnostic_false_assurance_events":assurance,
                "conservative_rounding_margin_false_assurance_events":strong,
                "source_specific_original_infeasible_events":original_infeasible,
                "conditional_false_assurance_fraction_among_source_infeasible":(
                    assurance/original_infeasible if original_infeasible else None
                ),
            })
        groups[group]={
            "event_rows":len(eligible),
            "original_event_year_min":min(x["year"] for x in eligible),
            "original_event_year_max":max(x["year"] for x in eligible),
            "actual_source_radius_km":_quantiles([x["actual"] for x in comparisons]),
            "retrospective_any_source_radius_km":_quantiles([x["possible"] for x in comparisons]),
            "source_optimism_gap_km":_quantiles([x["gap"] for x in comparisons]),
            "source_optimism_gap_gt_2km_events":sum(x["gap"]>2 for x in comparisons),
            "radii":rs,
        }
    return {
        "schema":"eog.tern_known_departure_source_geometry_v1",
        "status":"EXTERNAL_POST_PUBLICATION_SOURCE_GEOGRAPHY_DESCRIPTIVE_ONLY",
        "source":"SHA_PINNED_PUBLISHED_RINGING_DERIVED_EVENT_ENDPOINTS",
        "publisher_published_rows":{"breeding_adult":len(by_type["breeding_adult"]),"natal_chick":len(by_type["natal_chick"])},
        "publisher_haversine_concordance":dict(audit),
        "published_distance_match_within_2km_rows":total_match,
        "publisher_distance_total_rows":sum(expected_counts.values()),
        "source_catalogue_cutoff_year":early_year,
        "retrospectively_indexed_distinct_earlier_departure_locations":len(historical),
        "outcomes":groups,
        "is_asof_prospective":False,
        "prior_year_catalogue_is_verified_available_at_time":False,
        "individual_ring_ids_present":False,
        "stationary_stayers_present":False,
        "geographic_source_uncertainty_illustrated":True,
        "environment_or_barrier_MRR_evaluated":False,
        "original_biological_movement_trajectory_inferred":False,
        "event_records_exported":0,
        "new_EOG_WF_endpoints":0,
        "claim_boundary":"Known banding-derived departure and future observed breeding arrival; historical index may be retrospectively built. Event-level source-specific distance vs optimistic any-source lower bound is descriptive, not prospective predictive validation.",
    }


def run(protocol:dict[str, Any]) -> dict[str,Any]:
    if protocol.get("status")!="FROZEN_PRE_RAW_EVENT_OPEN_AFTER_PUBLISHER_SHA_MANIFEST":
        raise ScientificStop("STOP_PRE_EVENT_PROTOCOL_NOT_FROZEN")
    src=protocol["source_frozen"]
    if src["publisher_doi"]!="10.5061/dryad.x69p8czxh" or src["published_version_id"]!=466530:
        raise ScientificStop("STOP_ORIGINAL_PUBLISHER_VERSION_CHANGED")
    manifest=json.loads(META.read_text(encoding="utf-8"))
    if manifest["manifest_sha256"]!=src["source_metadata_manifest_sha256"]:
        raise ScientificStop("STOP_ORIGINAL_SOURCE_MANIFEST_CHANGED")
    actual={x["name"]:(x["size_bytes"],x["publisher_digest"]) for x in manifest["publisher_file_manifest"]}
    expected={x["name"]:(x["size_bytes"],x["sha256"]) for x in src["exact_files"]}
    if actual!=expected:
        raise ScientificStop("STOP_FROZEN_SHA_OR_SIZE_NO_LONGER_MATCHES_PROVIDER")
    v2=json.loads(V2_SOURCE.read_text(encoding="utf-8"))
    lim=json.loads(V1_SOURCE.read_text(encoding="utf-8"))["resource_limits"]
    if src["official_version_download_url"] != "https://datadryad.org/api/v2/versions/466530/download":
        raise ScientificStop("STOP_PUBLISHER_URL_CHANGED")
    # No alternate CDN redirect allowance is introduced in this stage.
    raw_zip, final_host=_version_zip(src["official_version_download_url"],lim,v2["exact_trusted_redirect_contract"])
    bodies=_read_source_zip(raw_zip,protocol)
    del raw_zip
    desc={x["name"]:x for x in src["expected_csvs"]}
    by_type={}
    for name,contract in desc.items():
        by_type[contract["type"]]=_parse_event_table(bodies[name],contract)
    result=analyze_events(by_type,protocol)
    result["source_version_id"]=src["published_version_id"]
    result["original_source_csv_sha256s"]={name:_sha(raw) for name,raw in bodies.items()}
    result["publisher_version_archive_downloaded"]=True
    result["publisher_archive_host_verified"]=True
    result["published_original_member_hashes_verified"]=True
    result["new_EOG_WF_endpoints"]=0
    return result


def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    try:
        result=run(protocol)
    except (ScientificStop,ValueError,RuntimeError,OSError,urllib.error.URLError,zipfile.BadZipFile) as err:
        result={
            "schema":"eog.tern_known_departure_source_geometry_v1",
            "status":str(err) if str(err).startswith("STOP_") else "STOP_SOURCE_TRANSPORT_OR_SCHEMA",
            "error_type":type(err).__name__,
            "movement_events_scored":0,
            "new_EOG_WF_endpoints":0,
            "raw_publisher_event_rows_exported":0,
        }
    result["sha256_without_self"]=_fingerprint(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "source_catalogue_count":result.get("retrospectively_indexed_distinct_earlier_departure_locations"),
        "publisher_geo_concordance":result.get("published_distance_match_within_2km_rows"),
        "table_event_rows":result.get("publisher_published_rows"),
        "event_group_results":result.get("outcomes"),
        "receipt_sha256":result["sha256_without_self"],
        "new_eog_wf_endpoints":0,
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
