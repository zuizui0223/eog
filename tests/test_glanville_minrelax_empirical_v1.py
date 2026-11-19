import json
import runpy

import pytest


def _m():
    return runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")


def test_predeclared_real_protocol_is_exploratory_and_has_both_guards():
    p=json.load(open("validation/glanville_minrelax_empirical_v1/protocol_v1.json"))
    assert p["status"] == "frozen_before_ecological_response_scoring"
    assert p["years"] == list(range(2007,2013))
    assert p["environmental_threshold_grid"] == [0,1,2,3]
    assert p["genetic_coordinate_verification"]["minimum_paired_patches"] == 100
    assert p["family_id_minimum_match_fraction"] == 0.95
    assert "not proven colonization" in " ".join(p["claim_restrictions"]).lower() or any(
        "NOT proven colonization" in x for x in p["claim_restrictions"]
    )


def _data():
    network = {"A": (0.0, 0.0), "B": (1000.0, 0.0), "C": (4000.0, 0.0)}
    survey = {
        (2005, "B"): (1.0, 0.0, 1.0),
        (2006, "A"): (1.0, 0.0, 0.0),
        (2006, "B"): (0.0, 0.0, 1.0),
        (2006, "C"): (0.0, 3.0, 3.0),
        (2007, "B"): (1.0, 0.0, 1.0),
        (2007, "C"): (0.0, 3.0, 3.0),
    }
    return network, survey


def test_target_condition_is_recorded_zero_to_positive_not_true_colonisation():
    m=_m()
    network, survey=_data()
    r=m["_radius_for_year"](2007,"previous_year_recorded_positive",network,survey,(0,1,2,3))
    assert r["eligible_newly_recorded_positive_targets"] == 1
    assert r["eligible_candidate_source_patches"] == 1
    by={x["host_gap_tolerance"]:x for x in r["conditional_radius_by_host_tolerance"]}
    assert by[0]["max_of_nearest_compatible_source_km"] is None
    assert by[0]["targets_without_allowed_source"] == 1
    assert by[1]["max_of_nearest_compatible_source_km"] == pytest.approx(1.0)
    assert r["pareto_minimum_absolute_limits"] == [
        {"minimum_required_step_km": 1.0, "minimum_ordinal_host_tolerance": 1}
    ]


def test_extended_prior_source_policy_reduces_required_radius_without_founder_claim():
    m=_m()
    network,survey=_data()
    a=m["_radius_for_year"](2007,"previous_year_recorded_positive",network,survey,(0,1,2,3))
    b=m["_radius_for_year"](2007,"previous_two_years_recorded_positive",network,survey,(0,1,2,3))
    assert a["conditional_radius_by_host_tolerance"][3]["max_of_nearest_compatible_source_km"] == 1.0
    assert b["conditional_radius_by_host_tolerance"][0]["max_of_nearest_compatible_source_km"] == 0.0
    assert b["conditional_radius_by_host_tolerance"][3]["max_of_nearest_compatible_source_km"] == 0.0
    assert b["eligible_candidate_source_patches"] == 2


def test_undirected_family_distances_are_not_given_a_migration_direction():
    m=_m()
    network,_=_data()
    genotype={(2007,"g1"):("A","r1"),(2007,"g2"):("B","r1")}
    families={(2007,"g1"):"family_a",(2007,"g2"):"family_a"}
    r=m["_family_summary"](network,genotype,families,(2007,))
    assert r["reconstructed_family_groups_spanning_multiple_patches"] == 1
    assert r["undirected_cross_patch_pairs"] == 1
    assert r["distance_km_median"] == pytest.approx(1.0)
    assert "NOT source direction" in r["interpretation"]


def test_coordinate_and_individual_join_gate_can_pass_on_exact_synthetic_keys():
    m=_m()
    network, _ = _data()
    geno={(2007,"g1"):("A","r1"),(2007,"g2"):("B","r1")}
    coords={"A":[(0.0,0.0)],"B":[(1000.0,0.0)]}
    families={(2007,"g1"):"f1",(2007,"g2"):"f1"}
    p={"genetic_coordinate_verification":{
           "minimum_paired_patches":2,"median_max_m":1000,"q95_max_m":5000},
       "family_id_minimum_match_fraction":0.95}
    r=m["_check_geographic_contract"](network,coords,geno,families,p)
    assert r["individual_year_matched"] == 2
    assert r["shared_coordinate_patch_count"] == 2
    assert r["matched_patch_coordinate_residual_m_median"] == 0.0


def test_coordinate_scale_mismatch_is_a_stop_not_reinterpreted_as_km():
    m=_m()
    network,_=_data()
    geno={(2007,"g1"):("A","r1"),(2007,"g2"):("B","r1")}
    coords={"A":[(100000.0,0.0)],"B":[(101000.0,0.0)]}
    families={(2007,"g1"):"f1",(2007,"g2"):"f1"}
    p={"genetic_coordinate_verification":{
           "minimum_paired_patches":2,"median_max_m":1000,"q95_max_m":5000},
       "family_id_minimum_match_fraction":0.95}
    with pytest.raises(m["SourceStop"],match="STOP_CRS_NUMERICAL_CONCORDANCE_FAILED"):
        m["_check_geographic_contract"](network,coords,geno,families,p)
