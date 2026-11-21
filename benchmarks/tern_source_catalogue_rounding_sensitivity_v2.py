#!/usr/bin/env python3
"""Post-exposure, source-SHA-locked Arctic-tern any-source artefact sensitivity v2.

Ten source catalogues are predeclared, including a no-alternatives negative
control. No source row, coordinate, ring event ID, or flight path is emitted.
The parent v1 event-level result is checked exactly before any sensitivity
result is accepted. Published source events are NOT a verified as-of 1975
occupancy or original ringing-database snapshot.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import urllib.error
import zipfile
from typing import Any

from benchmarks import tern_known_origin_geographic_minrelax_v1 as parent

PROTOCOL = Path("validation/tern_source_catalogue_rounding_sensitivity_v2/protocol_v2.json")
PARENT_PROTOCOL = Path("validation/tern_known_origin_geographic_minrelax_v1/protocol_v1.json")
PARENT_SUMMARY = Path("validation/tern_known_origin_geographic_minrelax_v1/frozen_aggregate_summary_v1.json")
V2_TRANSPORT = Path("validation/independent_movement_source_gate_v2/protocol_v2.json")
V1_TRANSPORT = Path("validation/independent_movement_source_gate_v1/protocol_v1.json")
SCENARIOS = (
    "v1_exact_baseline",
    "exclude_exact_destination_coordinate",
    "source_nonlocal_2km",
    "source_nonlocal_5km",
    "source_nonlocal_10km",
    "older_departures_through_1970",
    "older_departures_through_1965",
    "source_site_with_two_earlier_departure_events",
    "same_published_event_table_source_only",
    "no_alternative_source_negative_control",
)


class SourceSensitivityStop(ValueError):
    pass


def _enforce_source_frozen(spec: dict[str, Any], old: dict[str, Any], old_result: dict[str, Any]) -> None:
    frozen = spec["immutable_source"]
    if spec.get("status") != "POST_EXPOSURE_SENSITIVITY_FROZEN_BEFORE_V2_RAW_REOPEN":
        raise SourceSensitivityStop("STOP_V2_PROTOCOL_NOT_FROZEN")
    if frozen["doi"] != old["source_frozen"]["publisher_doi"] or frozen["version"] != old["source_frozen"]["published_version_id"]:
        raise SourceSensitivityStop("STOP_ORIGINAL_SOURCE_OR_VERSION_DRIFT")
    if spec["frozen_original_result_sha256_without_self"] != old_result["execution"]["source_analysis_sha256_without_self"]:
        raise SourceSensitivityStop("STOP_PARENT_RESULT_FINGERPRINT_DRIFT")
    actual = {x["name"]:(x["size_bytes"],x["sha256"]) for x in old["source_frozen"]["exact_files"] if x["name"] in frozen["required_csvs"]}
    expected = {name:(value["bytes"],value["sha256"]) for name,value in frozen["required_csvs"].items()}
    if actual != expected:
        raise SourceSensitivityStop("STOP_ORIGINAL_CSV_SHA_OR_SIZE_DRIFT")
    values = spec["candidate_catalogue_scenarios"]
    if [x["id"] for x in values] != list(SCENARIOS) or len(set(SCENARIOS)) != len(values):
        raise SourceSensitivityStop("STOP_SCENARIO_ROSTER_DRIFT")
    canonical = (
        (1975,"both",1,0,False),
        (1975,"both",1,0,True),
        (1975,"both",1,2,False),
        (1975,"both",1,5,False),
        (1975,"both",1,10,False),
        (1970,"both",1,0,False),
        (1965,"both",1,0,False),
        (1975,"both",2,0,False),
        (1975,"same_group",1,0,False),
        (1975,"none",1,0,False),
    )
    extracted = [
        (s["eligible_source_year_end"],s["source_table_mode"],
         s["minimum_departure_event_count_per_rounded_site"],
         s["per_arrival_minimum_alternative_distance_km"],
         s["exclude_exact_rounded_arrival_coordinate"])
        for s in values
    ]
    if extracted != list(canonical):
        raise SourceSensitivityStop("STOP_SCENARIO_DEFINITION_CHANGED")
    if spec["frozen_metrics"]["R_km"] != old["frozen_estimands"]["prespecified_thresholds_km"]:
        raise SourceSensitivityStop("STOP_RADIUS_LIST_CHANGED")
    if float(old["frozen_estimands"]["earth_radius_km"]) != 6371.0088:
        raise SourceSensitivityStop("STOP_PARENT_EARTH_RADIUS_CHANGED")


def _candidate_sources(
    by_type: dict[str, list[dict[str, Any]]], group: str, scenario: dict[str, Any]
) -> tuple[tuple[float,float], ...]:
    mode = scenario["source_table_mode"]
    if mode == "none":
        return ()
    if mode not in ("both","same_group"):
        raise SourceSensitivityStop("STOP_INVALID_HISTORIC_SOURCE_TYPE")
    counts: Counter[tuple[float,float]] = Counter()
    for record_group, records in by_type.items():
        if mode == "same_group" and group != record_group:
            continue
        for record in records:
            if record["year"] <= scenario["eligible_source_year_end"]:
                counts[record["origin"]] += 1
    floor = scenario["minimum_departure_event_count_per_rounded_site"]
    return tuple(sorted(p for p,n in counts.items() if n >= floor))


def _summary_for_group(
    source: list[dict[str, Any]],
    candidates: tuple[tuple[float,float],...],
    scenario: dict[str, Any],
    prot: dict[str, Any],
    previous: dict[str, Any] | None,
) -> dict[str, Any]:
    H=prot["frozen_metrics"]["geographic_distance"]
    if not H.startswith("same parent"):
        raise SourceSensitivityStop("STOP_DISTANCE_DEFINITION_DRIFT")
    R=6371.0088  # pinned to parent v1; checked by _enforce_source_frozen
    threshold=prot["frozen_metrics"]["R_km"]
    included = [row for row in source if row["year"] >= prot["frozen_sample"]["evaluation_event_year_min"]]
    exact_candidate_with_source_infeasible=Counter()
    original_radii: list[float] = []
    candidate_radii: list[float] = []
    explicit_any_zero=0
    actual_source_infeasible={rad:0 for rad in threshold}
    any_source_false_assurance={rad:0 for rad in threshold}
    conserv={rad:0 for rad in threshold}
    same_rounded_arrival_source_count=0
    for row in included:
        pos=row["arrival"]
        actual=parent._greatcircle_km(row["origin"],pos,R)
        original_radii.append(actual)
        coincident = pos in candidates
        if coincident:
            same_rounded_arrival_source_count+=1
        nonlocal_distances=[]
        for loc in candidates:
            if scenario["exclude_exact_rounded_arrival_coordinate"] and loc == pos:
                continue
            distance=parent._greatcircle_km(loc,pos,R)
            floor=scenario["per_arrival_minimum_alternative_distance_km"]
            if distance < float(floor):
                continue
            nonlocal_distances.append(distance)
        some=min(actual, min(nonlocal_distances)) if nonlocal_distances else actual
        if some > actual+1e-9:
            raise SourceSensitivityStop("STOP_MRR_SOURCE_INCLUSION_ORDER")
        candidate_radii.append(some)
        if some == 0:
            explicit_any_zero+=1
        for rad in threshold:
            if actual > rad:
                actual_source_infeasible[rad]+=1
                if coincident:
                    exact_candidate_with_source_infeasible[rad]+=1
                if some<=rad:
                    any_source_false_assurance[rad]+=1
                if actual>rad+2 and some<rad-2:
                    conserv[rad]+=1
    if not included:
        raise SourceSensitivityStop("STOP_EMPTY_POST_CUTOFF_EVENT_GROUP")
    radii=[]
    for rad in threshold:
        if conserv[rad]>any_source_false_assurance[rad]:
            raise SourceSensitivityStop("STOP_ROUNDING_MARGIN_ORDER")
        radii.append({
            "radius_km":rad,
            "known_source_infeasible_events":actual_source_infeasible[rad],
            "any_alternative_false_assurance_events":any_source_false_assurance[rad],
            "rounding_conservative_false_assurance_events":conserv[rad],
            "known_source_infeasible_with_coincident_historical_candidate":exact_candidate_with_source_infeasible[rad],
            "baseline_false_assurance_removed_events":(
                (next(x["source_agnostic_false_assurance_events"] for x in previous["radii"] if x["radius_km"]==rad)
                -any_source_false_assurance[rad]) if previous is not None else 0
            ),
        })
        if radii[-1]["baseline_false_assurance_removed_events"] < 0:
            raise SourceSensitivityStop("STOP_SUBSET_SOURCE_NESTEDNESS_VIOLATED")
    return {
        "original_event_rows_in_group":len(included),
        "distinct_pre_indexed_candidate_rounded_departure_sites":len(candidates),
        "events_with_exactly_coincident_historical_candidate":same_rounded_arrival_source_count,
        "events_with_any_source_radius_zero":explicit_any_zero,
        "average_known_source_radius_km":sum(original_radii)/len(original_radii),
        "average_optimistic_any_source_radius_km":sum(candidate_radii)/len(candidate_radii),
        "median_optimistic_any_source_radius_km":sorted(candidate_radii)[len(candidate_radii)//2] if len(candidate_radii)%2 else 0.5*(sorted(candidate_radii)[len(candidate_radii)//2-1]+sorted(candidate_radii)[len(candidate_radii)//2]),
        "radius_results":radii,
    }


def analyze_scenarios(by_type: dict[str,list[dict[str,Any]]], spec:dict[str,Any],
                      old:dict[str,Any], parent_summary:dict[str,Any]) -> dict[str,Any]:
    _enforce_source_frozen(spec,old,parent_summary)
    # The original pre-event known-origin analysis is re-run first against the
    # *same* real data. Any mismatch halts the post-hoc sensitivity.
    v1=parent.analyze_events(by_type,old)
    historical_size=parent_summary["original_source_QA"]["source_catalogue_distinct_rounded_departure_coordinates_from_event_year_le1975"]
    if (v1["retrospectively_indexed_distinct_earlier_departure_locations"] != historical_size
        or v1["published_distance_match_within_2km_rows"] != 1090
        or v1["publisher_distance_total_rows"] != 1090
        or v1["publisher_published_rows"] != {"breeding_adult":200,"natal_chick":890}
        or {k:v1["outcomes"][k]["event_rows"] for k in ("breeding_adult","natal_chick")}!={"breeding_adult":87,"natal_chick":491}):
        raise SourceSensitivityStop("STOP_PARENT_SOURCE_EVENT_QUALITY_DRIFT")
    baseline_counts={"breeding_adult":10,"natal_chick":188}
    baseline_conservative={"breeding_adult":9,"natal_chick":171}
    for group in baseline_counts:
        r20=next(row for row in v1["outcomes"][group]["radii"] if row["radius_km"]==20)
        if r20["source_agnostic_false_assurance_events"]!=baseline_counts[group] or r20["conservative_rounding_margin_false_assurance_events"]!=baseline_conservative[group]:
            raise SourceSensitivityStop("STOP_PARENT_20KM_FALSE_ASSURANCE_RESULT_DRIFT")
    results={}
    for scenario in spec["candidate_catalogue_scenarios"]:
        by_group={}
        for group in ("breeding_adult","natal_chick"):
            sites=_candidate_sources(by_type,group,scenario)
            by_group[group]=_summary_for_group(by_type[group],sites,scenario,spec,v1["outcomes"][group])
        summed=[]
        for rad in spec["frozen_metrics"]["R_km"]:
            rows=[next(x for x in by_group[group]["radius_results"] if x["radius_km"]==rad) for group in by_group]
            summed.append({
                "radius_km":rad,
                "known_source_infeasible_events":sum(x["known_source_infeasible_events"] for x in rows),
                "any_alternative_false_assurance_events":sum(x["any_alternative_false_assurance_events"] for x in rows),
                "rounding_conservative_false_assurance_events":sum(x["rounding_conservative_false_assurance_events"] for x in rows),
                "baseline_false_assurance_removed_events":sum(x["baseline_false_assurance_removed_events"] for x in rows),
                "known_source_infeasible_with_coincident_historical_candidate":sum(x["known_source_infeasible_with_coincident_historical_candidate"] for x in rows)
            })
        results[scenario["id"]]={
            "catalogue_rule":scenario,
            "source_group_summaries":by_group,
            "combined": {
                "post_1975_event_rows":sum(g["original_event_rows_in_group"] for g in by_group.values()),
                "events_with_any_source_radius_zero":sum(g["events_with_any_source_radius_zero"] for g in by_group.values()),
                "radii":summed,
            }
        }
    def get(scenario,rad=20):
        return next(x for x in results[scenario]["combined"]["radii"] if x["radius_km"]==rad)
    # Fixed 20km & all other registered thresholds must reproduce parent v1 baseline.
    for rad in spec["frozen_metrics"]["R_km"]:
        baseline=get("v1_exact_baseline",rad)
        for g in baseline_counts:
            expected=next(row for row in v1["outcomes"][g]["radii"] if row["radius_km"]==rad)
            observed=next(row for row in results["v1_exact_baseline"]["source_group_summaries"][g]["radius_results"] if row["radius_km"]==rad)
            if observed["any_alternative_false_assurance_events"]!=expected["source_agnostic_false_assurance_events"] or observed["rounding_conservative_false_assurance_events"]!=expected["conservative_rounding_margin_false_assurance_events"]:
                raise SourceSensitivityStop("STOP_PARENT_BASELINE_NOT_REPLICATED")
        if baseline["any_alternative_false_assurance_events"] != sum(
            next(x["source_agnostic_false_assurance_events"] for x in v1["outcomes"][group]["radii"] if x["radius_km"]==rad) for group in baseline_counts
        ):
            raise SourceSensitivityStop("STOP_PARENT_AGGREGATE_NOT_REPLICATED")
        no=get("no_alternative_source_negative_control",rad)
        if no["any_alternative_false_assurance_events"]!=0 or no["rounding_conservative_false_assurance_events"]!=0:
            raise SourceSensitivityStop("STOP_NO_ALTERNATIVE_SOURCE_NEGATIVE_CONTROL")
        floor_ids=("v1_exact_baseline","exclude_exact_destination_coordinate","source_nonlocal_2km","source_nonlocal_5km","source_nonlocal_10km")
        prev=baseline["any_alternative_false_assurance_events"]
        for scenario in floor_ids[1:]:
            curr=get(scenario,rad)["any_alternative_false_assurance_events"]
            if curr>prev:
                raise SourceSensitivityStop("STOP_SOURCE_CANDIDATE_DISTANCE_MONOTONICITY")
            prev=curr
        last=None
        for scenario in ("older_departures_through_1965","older_departures_through_1970","v1_exact_baseline"):
            current=get(scenario,rad)["any_alternative_false_assurance_events"]
            if last is not None and current<last:
                raise SourceSensitivityStop("STOP_SOURCE_YEAR_ROSTER_MONOTONICITY")
            last=current
        for scenario in ("source_site_with_two_earlier_departure_events","same_published_event_table_source_only"):
            if get(scenario,rad)["any_alternative_false_assurance_events"] > baseline["any_alternative_false_assurance_events"]:
                raise SourceSensitivityStop("STOP_SOURCE_ROSTER_SUBSET_MONOTONICITY")
    primary=[
        {"scenario":name,
         "adult_R20_false_assurance":next(x for x in results[name]["source_group_summaries"]["breeding_adult"]["radius_results"] if x["radius_km"]==20)["any_alternative_false_assurance_events"],
         "natal_R20_false_assurance":next(x for x in results[name]["source_group_summaries"]["natal_chick"]["radius_results"] if x["radius_km"]==20)["any_alternative_false_assurance_events"],
         "combined_R20_false_assurance":get(name)["any_alternative_false_assurance_events"],
         "combined_R20_rounding_conservative":get(name)["rounding_conservative_false_assurance_events"],
         "relative_to_parent_baseline_removed":get(name)["baseline_false_assurance_removed_events"],
         "adult_earlier_source_sites":results[name]["source_group_summaries"]["breeding_adult"]["distinct_pre_indexed_candidate_rounded_departure_sites"],
         "natal_earlier_source_sites":results[name]["source_group_summaries"]["natal_chick"]["distinct_pre_indexed_candidate_rounded_departure_sites"],
         "number_of_possible_zero_radius_events":results[name]["combined"]["events_with_any_source_radius_zero"],
        }
        for name in SCENARIOS
    ]
    if primary[0]["combined_R20_false_assurance"] != 198 or primary[0]["combined_R20_rounding_conservative"]!=180:
        raise SourceSensitivityStop("STOP_ORIGINAL_20KM_NOT_REPRODUCED")
    if results["v1_exact_baseline"]["combined"]["post_1975_event_rows"]!=578:
        raise SourceSensitivityStop("STOP_HOLDOUT_EVENT_DENOMINATOR_CHANGED")
    return {
       "schema":"eog.tern_source_catalogue_and_rounding_sensitivity_v2.aggregate",
       "status":"POST_EXPOSURE_SOURCE_CATALOGUE_SENSITIVITY_COMPLETED_NOT_NEW_ECOLOGY",
       "original_parent_result_fingerprint":spec["frozen_original_result_sha256_without_self"],
       "source_qualified_publisher":{"doi":spec["immutable_source"]["doi"],"version":spec["immutable_source"]["version"],"adult_events":200,"natal_events":890,"published_distance_concordant":1090},
       "frozen_scenario_count":len(SCENARIOS),
       "group_holdout_denominators":{"breeding_adult":87,"natal_chick":491},
       "original_R20_known_source_infeasible_denominator":224,
       "primary_R20_scenario_comparison":primary,
       "all_scenario_groups_and_radii":results,
       "exact_parent_replication_pass":True,
       "no_alt_source_negative_control_pass":True,
       "source_roster_and_floor_monotonicity_pass":True,
       "source_asof_verified":False,
       "coordinate_rounding_causes_zero_minimum":True,
       "source_candidate_site_actually_active_verified":False,
       "individual_disperal_event_independence_verified":False,
       "causal_ecological_mechanism_tested":False,
       "new_EOG_WF_endpoints":0,
       "raw_published_event_rows_exported":0,
       "statistical_inference":"NONE_EVENT_DATA_NOT_INDEPENDENT_INDIVIDUALS",
       "claim_boundary":"Source-specific geographic distance sensitivity to retrospectively assembled candidate catalogues; no as-of source truth, no new actual ecological origin, no full MRR environment/barrier, no new predictive score."
    }


def run(spec: dict[str,Any]) -> dict[str,Any]:
    old=json.loads(PARENT_PROTOCOL.read_text(encoding="utf-8"))
    parent_result=json.loads(PARENT_SUMMARY.read_text(encoding="utf-8"))
    _enforce_source_frozen(spec,old,parent_result)
    frozen=spec["immutable_source"]
    gate=json.loads(V2_TRANSPORT.read_text(encoding="utf-8"))
    limits=json.loads(V1_TRANSPORT.read_text(encoding="utf-8"))["resource_limits"]
    official=old["source_frozen"]["official_version_download_url"]
    if official != "https://datadryad.org/api/v2/versions/466530/download":
        raise SourceSensitivityStop("STOP_PUBLISHER_VERSION_URL_CHANGED")
    original_zip,host=parent._version_zip(official,limits,gate["exact_trusted_redirect_contract"])
    source_tables=parent._read_source_zip(original_zip,old)
    del original_zip
    contracts={x["name"]:x for x in old["source_frozen"]["expected_csvs"]}
    by_type={
        contract["type"]:parent._parse_event_table(source_tables[name],contract)
        for name,contract in contracts.items()
    }
    result=analyze_scenarios(by_type,spec,old,parent_result)
    result["publisher_original_zip_member_SHA_verified"]=True
    result["original_publisher_host_verified"]=True
    return result


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--protocol",type=Path,default=PROTOCOL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    spec=json.loads(args.protocol.read_text(encoding="utf-8"))
    try:
        result=run(spec)
    except (ValueError,SourceSensitivityStop,OSError,urllib.error.URLError,zipfile.BadZipFile) as exc:
        result={
            "schema":"eog.tern_source_catalogue_and_rounding_sensitivity_v2.aggregate",
            "status":str(exc) if str(exc).startswith("STOP_") else "STOP_SOURCE_TRANSPORT_OR_SCHEMA",
            "error_type":type(exc).__name__,
            "new_EOG_WF_endpoints":0,
            "raw_published_event_rows_exported":0,
            "source_asof_verified":False,
            "causal_ecological_mechanism_tested":False,
        }
    result["sha256_without_self"]=parent._fingerprint(result)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "primary_R20_scenario_comparison":result.get("primary_R20_scenario_comparison"),
        "parent_replication":result.get("exact_parent_replication_pass"),
        "source_asof_verified":False,
        "new_EOG_WF_endpoints":0,
        "receipt_SHA256":result["sha256_without_self"],
    },sort_keys=True,ensure_ascii=False))


if __name__=="__main__":
    main()
