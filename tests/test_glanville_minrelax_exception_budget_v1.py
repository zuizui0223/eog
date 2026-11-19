import json
import runpy

import pytest


def _m():
    return runpy.run_path("benchmarks/glanville_minrelax_exception_budget_v1.py")


def _legacy():
    return runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")


def _protocol():
    return json.load(open("validation/glanville_minrelax_exception_budget_v1/protocol_v1.json"))


def _toy():
    # A is previous-year observed source; all other patches had observed zeros
    # and are recorded positive in 2007. No inferred colonization is assumed.
    network={"A":(0.,0.),"B":(1000.,0.),"C":(3000.,0.),
             "D":(15000.,0.),"E":(20000.,0.)}
    survey={(2006,"A"):(1.,0.,0.)}
    for k in ("B","C","D","E"):
        survey[(2006,k)]=(0.,0.,0.)
        survey[(2007,k)]=(1.,0.,0.)
    return network,survey


def _parent(year,policy,net,survey):
    old=_legacy()["_radius_for_year"](year,policy,net,survey,(0,1,2,3))
    return {
        "n_targets":old["eligible_newly_recorded_positive_targets"],
        "n_sources":old["eligible_candidate_source_patches"],
        "r_km_by_host_gap":[r["max_of_nearest_compatible_source_km"] for r in old["conditional_radius_by_host_tolerance"]],
        "n_no_source_by_host_gap":[r["targets_without_allowed_source"] for r in old["conditional_radius_by_host_tolerance"]],
    }


def test_protocol_fixed_before_scoring_and_old_endpoint_untouched():
    p=_protocol()
    assert p["status"]=="pre-score_frozen_post_exposure_sensitivity"
    assert p["parent_main_sha"]=="a2658ebba8ce385e46ff98909a7a94794342f20e"
    assert p["new_primary_estimand"]["primary_environment_panels"]==[1,3]
    assert [x["id"] for x in p["new_primary_estimand"]["exception_budgets"]]==[
        "strict","one","one_percent","five_percent"
    ]
    assert p["new_primary_estimand"]["never_drop_positives_from_underlying_evidence"]


def test_budget_order_statistics_and_full_strict_reconstruction():
    module=_m();net,survey=_toy();proto=_protocol()
    r=module["analyze_panel"](
        2007,"previous_year_recorded_positive",net,survey,_legacy(),
        (0,1,2,3),proto["new_primary_estimand"]["exception_budgets"],
        _parent(2007,"previous_year_recorded_positive",net,survey)
    )
    assert r["targets"]==4 and r["sources"]==1
    d0=r["host_gap_rows"][0]
    by={x["budget_id"]:x for x in d0["exception_budgets"]}
    assert d0["original_strict_radius_km"]==20.
    assert by["strict"]["minimum_required_radius_km"]==20.
    assert by["one"]["minimum_required_radius_km"]==15.
    assert by["one"]["relative_radius_reduction_vs_strict"]==pytest.approx(.25)
    assert by["one_percent"]["allowed_unexplained_targets"]==0
    assert by["five_percent"]["allowed_unexplained_targets"]==0
    assert d0["distribution_of_nearest_source_distances"]["q50_finite_km"]==pytest.approx(9.)
    assert d0["distribution_of_nearest_source_distances"]["q95_finite_km"]==pytest.approx(19.25)


def test_unreachable_positive_stays_unsupported_without_enough_exception_budget():
    module=_m();net,survey=_toy()
    survey[(2006,"E")]=(0.,3.,3.)
    legacy=_legacy();p=_parent(2007,"previous_year_recorded_positive",net,survey)
    r=module["analyze_panel"](
        2007,"previous_year_recorded_positive",net,survey,legacy,(0,1,2,3),
        _protocol()["new_primary_estimand"]["exception_budgets"],p
    )
    delta0=r["host_gap_rows"][0]
    assert delta0["original_strict_radius_km"] is None
    assert delta0["distribution_of_nearest_source_distances"]["missing_compatible_source_count"]==1
    by={x["budget_id"]:x for x in delta0["exception_budgets"]}
    assert by["strict"]["minimum_required_radius_km"] is None
    assert by["one"]["minimum_required_radius_km"]==pytest.approx(15.)
    assert by["one"]["not_claiming_excluded_positives_false"]


def test_parent_source_fingerprint_and_aggregates_are_fixed():
    module=_m();net,survey=_toy();legacy=_legacy()
    p=_parent(2007,"previous_year_recorded_positive",net,survey)
    p["r_km_by_host_gap"]=[21.,21.,21.,21.]
    with pytest.raises(module["AuditStop"],match="STOP_FROZEN_PARENT_RADIUS_MISMATCH"):
        module["analyze_panel"](
            2007,"previous_year_recorded_positive",net,survey,legacy,(0,1,2,3),
            _protocol()["new_primary_estimand"]["exception_budgets"],p
        )


def test_absence_of_eligible_source_not_converted_to_zero_or_biological_impossibility():
    module=_m();net,survey=_toy();survey[(2006,"A")]=(0.,0.,0.)
    legacy=_legacy();p=_parent(2007,"previous_year_recorded_positive",net,survey)
    r=module["analyze_panel"](
        2007,"previous_year_recorded_positive",net,survey,legacy,(0,1,2,3),
        _protocol()["new_primary_estimand"]["exception_budgets"],p
    )
    for row in r["host_gap_rows"]:
        assert row["original_strict_radius_km"] is None
        assert row["exception_budgets"][0]["minimum_required_radius_km"] is None
        assert row["distribution_of_nearest_source_distances"]["missing_compatible_source_count"]==4


def test_tightening_host_gap_never_lowers_needed_radius_with_fixed_targets_and_sources():
    module=_m();net,survey=_toy()
    survey[(2006,"B")]=(0.,1.,1.)
    r=module["analyze_panel"](
        2007,"previous_year_recorded_positive",net,survey,_legacy(),(0,1,2,3),
        _protocol()["new_primary_estimand"]["exception_budgets"],
        _parent(2007,"previous_year_recorded_positive",net,survey)
    )
    values=[row["exception_budgets"][0]["minimum_required_radius_km"] for row in r["host_gap_rows"]]
    assert all(x is None or (y is not None and y<=x) for x,y in zip(values,values[1:]))
