"""Offline synthetic controls for post-exposure tern source-catalogue sensitivity.

Original published tern events stay unopened in tests. Full SHA-pinned original
parent result is reproduced in the dedicated one-time Actions run, never
re-purposed as a newly independent ecological validation.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json
import pytest

from benchmarks import tern_source_catalogue_rounding_sensitivity_v2 as m
from benchmarks import tern_known_origin_geographic_minrelax_v1 as parent

SPEC=json.loads(Path("validation/tern_source_catalogue_rounding_sensitivity_v2/protocol_v2.json").read_text(encoding="utf-8"))
OLD=json.loads(Path("validation/tern_known_origin_geographic_minrelax_v1/protocol_v1.json").read_text(encoding="utf-8"))
PREVIOUS=json.loads(Path("validation/tern_known_origin_geographic_minrelax_v1/frozen_aggregate_summary_v1.json").read_text(encoding="utf-8"))


def event(identifier,year,source,destination):
    return {"UID":identifier,"year":year,"origin":source,"arrival":destination,
            "publisher_distance_km":parent._greatcircle_km(source,destination,6371.0088)}


def data():
    # Historical departure A coincides with target; B is ~6.4 km away.
    # Target's actual recorded source is >100 km away. No individual movement
    # is inferred from these synthetic coordinates.
    return {
        "breeding_adult":[
            event("past_a",1967,(55.,10.),(55.,10.2)),
            event("past_b",1971,(55.,10.10),(55.,10.2)),
            event("repeated_b",1975,(55.,10.10),(55.,10.3)),
            event("late_adult",1976,(55.,12.),(55.,10.)),
        ],
        "natal_chick":[
            event("early_natal",1965,(55.,9.),(55.,9.5)),
            event("late_natal",1980,(55.,12.),(55.,10.)),
        ]
    }


def rule(identifier):
    return next(x for x in SPEC["candidate_catalogue_scenarios"] if x["id"]==identifier)


def individual(identifier, group="breeding_adult"):
    scenario=rule(identifier)
    all_data=data()
    sites=m._candidate_sources(all_data,group,scenario)
    result=m._summary_for_group(all_data[group],sites,scenario,SPEC,None)
    r20=next(x for x in result["radius_results"] if x["radius_km"]==20)
    return len(sites), result, r20


def test_protocol_preserves_original_source_and_immutable_parent_result():
    assert SPEC["status"]=="POST_EXPOSURE_SENSITIVITY_FROZEN_BEFORE_V2_RAW_REOPEN"
    assert SPEC["frozen_original_result_sha256_without_self"]=="feaad217d8b105af4fddae81d50055a30a3e259f2716bbdc0100b1a7d878b68f"
    assert len(SPEC["candidate_catalogue_scenarios"])==10
    assert SPEC["frozen_metrics"]["R_km"]==[5,20,50,100]
    assert SPEC["frozen_sample"]["evaluation_event_year_min"]==1976
    assert SPEC["stop_rules"]["new_eog_wf_endpoints"]==0
    m._enforce_source_frozen(SPEC,OLD,PREVIOUS)
    assert len(m.SCENARIOS)==10


def test_candidate_departure_roster_never_uses_arrivals_or_post1975_source():
    datasets=data()
    first=m._candidate_sources(datasets,"breeding_adult",rule("v1_exact_baseline"))
    assert first==((55.,9.),(55.,10.),(55.,10.1))
    assert (55.,10.2) not in first
    assert (55.,12.) not in first  # post-cutoff marked event origin
    early=m._candidate_sources(datasets,"natal_chick",rule("older_departures_through_1965"))
    assert early==((55.,9.),)


def test_exact_destination_coincidence_is_an_important_but_not_only_trivial_source():
    count,original,old_r20=individual("v1_exact_baseline")
    assert count==3
    assert old_r20["any_alternative_false_assurance_events"]==1
    assert old_r20["known_source_infeasible_with_coincident_historical_candidate"]==1
    assert original["events_with_any_source_radius_zero"]==1
    _,alternative,new_r20=individual("exclude_exact_destination_coordinate")
    assert new_r20["any_alternative_false_assurance_events"]==1
    assert alternative["events_with_any_source_radius_zero"]==0
    _,f2,r2=individual("source_nonlocal_2km")
    assert r2["any_alternative_false_assurance_events"]==1
    _,f10,r10=individual("source_nonlocal_10km")
    assert r10["any_alternative_false_assurance_events"]==0
    assert f10["events_with_any_source_radius_zero"]==0


def test_no_alternative_source_negative_control_has_zero_optimism():
    count,x,r20=individual("no_alternative_source_negative_control")
    assert count==0
    assert r20["known_source_infeasible_events"]==1
    assert r20["any_alternative_false_assurance_events"]==0
    assert r20["rounding_conservative_false_assurance_events"]==0
    assert x["events_with_any_source_radius_zero"]==0


def test_same_group_and_repeated_site_are_true_subsets():
    d=data()
    all_catalog=set(m._candidate_sources(d,"breeding_adult",rule("v1_exact_baseline")))
    only_breeding=set(m._candidate_sources(d,"breeding_adult",rule("same_published_event_table_source_only")))
    twice=set(m._candidate_sources(d,"breeding_adult",rule("source_site_with_two_earlier_departure_events")))
    assert all_catalog=={(55.,9.),(55.,10.),(55.,10.10)}
    assert only_breeding=={(55.,10.),(55.,10.10)}
    assert twice=={(55.,10.10)}
    assert only_breeding<=all_catalog and twice<=all_catalog


def test_strict_year_catalogue_nested_without_outcome_index():
    d=data()
    prior65=set(m._candidate_sources(d,"natal_chick",rule("older_departures_through_1965")))
    prior70=set(m._candidate_sources(d,"natal_chick",rule("older_departures_through_1970")))
    prior75=set(m._candidate_sources(d,"natal_chick",rule("v1_exact_baseline")))
    assert prior65 <= prior70 <= prior75
    assert len(prior65)==1 and len(prior70)==2 and len(prior75)==3


def test_source_scenarios_are_invariant_to_record_order_and_future_arrival_changes():
    d=data()
    alt=m._candidate_sources(d,"breeding_adult",rule("v1_exact_baseline"))
    for group in d:
        d[group]=list(reversed(d[group]))
        for row in d[group]:
            row["arrival"]=(60.,-20.)  # should never become candidate origin
    assert m._candidate_sources(d,"breeding_adult",rule("v1_exact_baseline"))==alt


def test_protocol_cannot_be_tuned_after_seeing_exposure():
    for mutate in (
        lambda x:x["candidate_catalogue_scenarios"].pop(),
        lambda x:x["candidate_catalogue_scenarios"][0].update(eligible_source_year_end=1980),
        lambda x:x["candidate_catalogue_scenarios"][3].update(per_arrival_minimum_alternative_distance_km=3),
        lambda x:x["frozen_metrics"].update(R_km=[5,25,50,100]),
        lambda x:x["immutable_source"]["required_csvs"]["U_DaD.csv"].update(bytes=0),
        lambda x:x.update(frozen_original_result_sha256_without_self="0"*64),
    ):
        c=deepcopy(SPEC)
        mutate(c)
        with pytest.raises(m.SourceSensitivityStop,match="STOP_"):
            m._enforce_source_frozen(c,OLD,PREVIOUS)


def test_published_records_never_exported_from_scenario_aggregates():
    _,z,_=individual("v1_exact_baseline")
    content=json.dumps(z)
    assert "past_a" not in content and "late_adult" not in content
    assert '"55.0"' not in content
    assert "0.0" in content or "0" in content
