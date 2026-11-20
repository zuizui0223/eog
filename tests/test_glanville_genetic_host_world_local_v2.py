import json
import runpy

import pytest


def _m():
    return runpy.run_path("scripts/glanville_genetic_host_world_local_audit_v2.py")


def test_host_gate_source_and_destination_use_original_two_host_scores():
    m=_m()
    survey={
        (2007,"A"):(1,0,0),(2007,"B"):(1,3,3),
        (2007,"C"):(0,0,0),(2007,"D"):(0,2,2),
        (2008,"C"):(1,0,0),(2008,"D"):(1,2,2),
    }
    sites={"A":(0,0),"B":(5,0),"C":(1,0),"D":(2,0)}
    genetic=[
       (2007,2008,"A","C","family1",1,1.0),
       (2007,2008,"B","C","family2",1,4.0),
       (2007,2008,"B","D","family3",1,3.0),
    ]
    eligible,worlds=m["make_worlds"](genetic,survey,sites,strict=False)
    assert len(eligible)==3
    lookup={(x["host_gap_delta"],x["radius_km"]):x["combined"] for x in worlds}
    d0r2=lookup[(0,2)]
    assert d0r2["EOG_any_source_within_r_distinct_destinations"]==1
    assert d0r2["at_least_one_assigned_source_within_r_distinct_destinations"]==1
    assert d0r2["EOG_any_source_within_r_assignment_rows"]==2
    assert d0r2["genetically_assigned_source_within_r_assignment_rows"]==1
    d1r5=lookup[(1,5)]
    assert d1r5["EOG_any_source_within_r_distinct_destinations"]==2
    assert d1r5["genetically_assigned_source_within_r_assignment_rows"]==2
    d3r5=lookup[(3,5)]
    assert d3r5["genetically_assigned_source_within_r_assignment_rows"]==3


def test_original_2019_source_fingerprint_and_family_grain_guard():
    m=_m()
    assert m["GENETIC_SHA"]=="140e5361f9bced20a434bfee01bae6ce7c925e028718cdb9c6fd8aa635cc912a"
    assert m["PARENT_COUNTS"]=={2008:(157,695),2009:(285,508),2010:(102,587),2011:(521,298),2012:(400,764)}
    assert m["number"]("NULL") is None
    assert m["number"]("NA") is None
    assert m["number"]("1.5")==1.5
    with pytest.raises(m["SourceStop"],match="STOP_SURVEY_YEAR_SCOPE"):
        m["qualified_survey"]({"years":[2011],"survey":[],"network":[]})


def test_narrowing_environment_excludes_actual_assigned_source_but_not_alternative():
    m=_m()
    survey={(2007,"A"):(1,0,0),(2007,"B"):(1,3,3),
            (2007,"C"):(0,0,0),(2008,"C"):(1,0,0)}
    net={"A":(0,0),"B":(5,0),"C":(1,0)}
    genetic=[(2007,2008,"B","C","f2",1,4.0)]
    e,worlds=m["make_worlds"](genetic,survey,net,strict=False)
    d1r2=next(x for x in worlds if x["host_gap_delta"]==1 and x["radius_km"]==2)["combined"]
    assert d1r2["EOG_any_source_within_r_distinct_destinations"]==1
    assert d1r2["at_least_one_assigned_source_within_r_distinct_destinations"]==0
    assert e[0]["host_gap"]==3
    assert e[0]["nearest"][1]==pytest.approx(1.0)


def test_no_raw_assignments_or_ids_in_aggregate_world_rows():
    m=_m()
    survey={(2007,"A"):(1,0,0),(2007,"C"):(0,0,0),(2008,"C"):(1,0,0)}
    net={"A":(0,0),"C":(1,0)}
    genetic=[(2007,2008,"A","C","secret-family-id",1,1.0)]
    eligible,worlds=m["make_worlds"](genetic,survey,net,strict=False)
    serialized=json.dumps(worlds)
    assert "secret-family-id" not in serialized
    assert '"A"' not in serialized and '"C"' not in serialized
    assert len(worlds)==8


def test_full_aggregate_result_invariant_against_frozen_previous_crosswalk():
    r=json.load(open("validation/glanville_genetic_host_world_v2/frozen_aggregate_summary_v2.json"))
    assert r["science_status"]=="POST_EXPOSURE_GENETIC_HOST_WORLD_AUDITED"
    assert r["n_selected_assignment_rows"]==163
    assert r["n_distinct_target_patch_years"]==100
    assert r["n_distinct_families_in_selected_rows"]==157
    worlds={(x["delta"],x["r_km"]):x for x in r["worlds"]}
    assert len(worlds)==8
    assert worlds[(1,2)]["EOG_any_source_target_years"]==91
    assert worlds[(1,2)]["assigned_source_any_target_years"]==50
    assert worlds[(3,2)]["EOG_any_source_target_years"]==97
    assert worlds[(3,2)]["assigned_source_any_target_years"]==72
    assert worlds[(3,5)]["EOG_any_source_target_years"]==100
    assert worlds[(3,5)]["assigned_source_any_target_years"]==93
    assert all(x["assigned_source_any_target_years"]<=x["EOG_any_source_target_years"] for x in worlds.values())
