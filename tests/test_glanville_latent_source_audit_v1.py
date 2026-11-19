import json
import runpy

import pytest


def _m():
    return runpy.run_path("benchmarks/glanville_latent_source_audit_v1.py")


def _proto():
    return json.load(open("validation/glanville_latent_source_audit_v1/protocol_v1.json"))


def _toy():
    # One source A; B,C,D are t-1 reported zeros and t positives.
    network={"A":(0.,0.),"B":(1000.,0.),"C":(3000.,0.),"D":(5000.,0.)}
    survey={(2006,"A"):(1.,0.,0.)}
    for patch in ("B","C","D"):
        survey[(2006,patch)]=(0.,0.,0.)
        survey[(2007,patch)]=(1.,0.,0.)
    return network,survey


def test_protocol_frozen_history_is_observational_not_detection_posterior():
    p=_proto()
    assert p["parent_main_sha"]=="afbffecf44c1d5fd6e55a1d48cc5dd5a1b7d9d7f"
    assert p["status"]=="frozen_before_latent_source_sensitivity_scoring"
    assert p["fixed_radius_km"]==[2,5]
    assert p["fixed_host_tolerances"]==[1,3]
    assert p["latent_source_addition_budgets"]==[0,1,5,10]
    assert "not patch-level false-negative probability" in p["external_observation_process_evidence"]["separation"].lower()


def test_zero_sources_not_confused_with_missing_or_recorded_positive():
    m=_m()
    network,survey=_toy()
    zeros=m["_candidate_roster"](2007,network,survey,m["_source_modules"]()[0])
    assert {patch for patch,_,_ in zeros["all_recorded_zero"]}=={"B","C","D"}
    assert zeros["supported_tminus2"]==[]
    del survey[(2006,"D")]
    zeros=m["_candidate_roster"](2007,network,survey,m["_source_modules"]()[0])
    assert {patch for patch,_,_ in zeros["all_recorded_zero"]}=={"B","C"}


def test_retrospective_exact_one_source_and_greedy_not_global_claim():
    m=_m()
    network,survey=_toy()
    legacy,tail=m["_source_modules"]()
    targets,sources=tail["_target_and_source_rosters"](2007,"previous_year_recorded_positive",network,survey,legacy)
    zeros=m["_candidate_roster"](2007,network,survey,legacy)["all_recorded_zero"]
    p=m["panel"](2007,3,2,"all_recorded_zero","allow_same_patch",
                 targets,sources,zeros,(0,1,5,10))
    assert p["total_positive_targets"]==3
    assert p["baseline_covered_by_observed_positive_sources"]==1
    assert p["optimistic_coverage_if_all_zero_candidates_are_occupied"]==3
    assert p["max_additional_targets_explained_by_one_source_exact"]==2
    by={row["hypothetical_hidden_source_budget"]:row for row in p["hypothetical_source_budget_results"]}
    assert by[0]["explained_target_count"]==1
    assert by[1]["explained_target_count"]==3
    assert by[5]["explained_target_count"]==3
    assert by[10]["additional_sources_selected"]==1
    assert p["greedy_feasible_not_global_minimum"]


def test_same_patch_exclusion_preserves_arrival_vs_local_persistence_distinction():
    m=_m()
    network,survey=_toy()
    legacy,tail=m["_source_modules"]()
    targets,sources=tail["_target_and_source_rosters"](2007,"previous_year_recorded_positive",network,survey,legacy)
    zeros=m["_candidate_roster"](2007,network,survey,legacy)["all_recorded_zero"]
    without=m["panel"](2007,3,2,"all_recorded_zero","exclude_same_patch",
                      targets,sources,zeros,(0,1,5,10))
    with_self=m["panel"](2007,3,2,"all_recorded_zero","allow_same_patch",
                      targets,sources,zeros,(0,1,5,10))
    assert with_self["max_additional_targets_explained_by_one_source_exact"]==2
    assert without["max_additional_targets_explained_by_one_source_exact"]==1
    assert with_self["baseline_covered_by_observed_positive_sources"]==without["baseline_covered_by_observed_positive_sources"]
    assert with_self["optimistic_coverage_if_all_zero_candidates_are_occupied"]>=without["optimistic_coverage_if_all_zero_candidates_are_occupied"]


def test_history_supported_sources_are_subset_of_any_reported_zero():
    m=_m()
    network,survey=_toy()
    survey[(2005,"C")]=(1.,0.,0.)
    zeros=m["_candidate_roster"](2007,network,survey,m["_source_modules"]()[0])
    assert {x[0] for x in zeros["supported_tminus2"]}=={"C"}
    assert {x[0] for x in zeros["supported_tminus2"]}.issubset(
        {x[0] for x in zeros["all_recorded_zero"]}
    )


def test_distance_relaxation_and_latent_undetected_source_are_not_identifiable_from_same_observation():
    m=_m();net,survey=_toy()
    legacy,tail=m["_source_modules"]()
    targets,sources=tail["_target_and_source_rosters"](2007,"previous_year_recorded_positive",net,survey,legacy)
    zeros=m["_candidate_roster"](2007,net,survey,legacy)["all_recorded_zero"]
    # A 5 km radius explains all; at only 2 km, one hypothetical missed
    # positive C source can explain both remaining targets. Neither proves mechanism.
    assert m["_base_mask"](targets,sources,3,5).bit_count()==3
    result=m["panel"](2007,3,2,"all_recorded_zero","allow_same_patch",
                      targets,sources,zeros,(0,1,5,10))
    assert next(x for x in result["hypothetical_source_budget_results"]
                if x["hypothetical_hidden_source_budget"]==1)["explained_target_count"]==3


def test_bounded_cover_and_no_posterior_probability_in_new_measures():
    m=_m()
    net,survey=_toy()
    legacy,tail=m["_source_modules"]()
    targets,sources=tail["_target_and_source_rosters"](2007,"previous_year_recorded_positive",net,survey,legacy)
    zeros=m["_candidate_roster"](2007,net,survey,legacy)["all_recorded_zero"]
    out=m["panel"](2007,1,2,"all_recorded_zero","exclude_same_patch",
                  targets,sources,zeros,(0,1,5,10))
    assert not any("probability" in k for k in out)
    assert out["optimistic_coverage_if_all_zero_candidates_are_occupied"]<=len(targets)
    assert all(row["still_unexplained_target_count"]>=0 for row in out["hypothetical_source_budget_results"])


def test_post_stop_erratum_is_explicit_and_repairs_only_matrix_cardinality():
    m=_m()
    proto=_proto()
    erratum=json.load(open("validation/glanville_latent_source_audit_v1/protocol_erratum_v1_1.json"))
    assert proto["computational_maxima"]["max_matrix_rows"]==48
    assert erratum["failed_run_id"]==44513808990
    amended=m["apply_arithmetic_erratum"](proto,erratum)
    assert amended["computational_maxima"]["max_matrix_rows"]==96
    assert proto["computational_maxima"]["max_matrix_rows"]==48
    assert amended["fixed_radius_km"]==proto["fixed_radius_km"]
    assert amended["fixed_host_tolerances"]==proto["fixed_host_tolerances"]
    assert amended["target_years"]==proto["target_years"]
    assert amended["latent_source_addition_budgets"]==proto["latent_source_addition_budgets"]
    assert amended["_validated_arithmetic_erratum"]["biological_contract_unchanged"]
    bad=dict(erratum,corrected_max_matrix_rows=48)
    with pytest.raises(m["GateStop"],match="STOP_INVALID_OR_OUT_OF_SCOPE_ERRATUM"):
        m["apply_arithmetic_erratum"](proto,bad)
