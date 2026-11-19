import json
import runpy

import pytest


def _m():
    return runpy.run_path("benchmarks/glanville_minrelax_empirical_v1.py")


def test_unit_fix_protocol_is_only_documented_conversion():
    p=json.load(open("validation/glanville_minrelax_empirical_unitfix_v2/protocol_v2.json"))
    parent=json.load(open("validation/glanville_minrelax_empirical_v1/protocol_v1.json"))
    assert p["parent_scientific_stop_run"] == 44482618167
    assert p["source_only_diagnostic_run"] == 44483096052
    assert p["only_authorized_change"]["multiply_by"] == 1000.0
    assert p["only_authorized_change"]["no_analytical_threshold_changes"]
    assert parent["years"] == list(range(2007,2013))
    assert parent["environmental_threshold_grid"] == [0,1,2,3]
    assert p["existing_eogwf_denominator"]["unchanged"]


def test_source_km_to_m_is_required_for_matching_identical_projected_patch():
    m=_m()
    original_in_km={"A":(0.12,6.7),"B":(1.12,6.7)}
    genetic_in_m={"A":[(120,6700)],"B":[(1120,6700)]}
    genotype={(2007,"i1"):("A","r1"),(2007,"i2"):("B","r1")}
    family={(2007,"i1"):"F1",(2007,"i2"):"F1"}
    parent={"genetic_coordinate_verification":{
        "minimum_paired_patches":2,"median_max_m":1000,"q95_max_m":5000},
        "family_id_minimum_match_fraction":0.95}
    with pytest.raises(m["SourceStop"],match="STOP_CRS_NUMERICAL_CONCORDANCE_FAILED"):
        m["_check_geographic_contract"](original_in_km,genetic_in_m,genotype,family,parent)
    scaled={p:(x*1000,y*1000) for p,(x,y) in original_in_km.items()}
    r=m["_check_geographic_contract"](scaled,genetic_in_m,genotype,family,parent)
    assert r["matched_patch_coordinate_residual_m_median"] == pytest.approx(0.0)
    assert m["_family_summary"](scaled,genotype,family,(2007,))["distance_km_median"] == pytest.approx(1.0)


def test_real_source_priority_cannot_raise_required_radius_when_lag2_added():
    m=_m()
    network={"A":(0.,0.),"B":(1000.,0.)}
    survey={
      (2005,"B"):(1.,0.,1.),
      (2006,"A"):(1.,0.,0.),
      (2006,"B"):(0.,0.,1.),
      (2007,"B"):(1.,0.,1.)
    }
    one=m["_radius_for_year"](2007,"previous_year_recorded_positive",network,survey,(0,1,2,3))
    two=m["_radius_for_year"](2007,"previous_two_years_recorded_positive",network,survey,(0,1,2,3))
    assert one["conditional_radius_by_host_tolerance"][3]["max_of_nearest_compatible_source_km"]==1.0
    assert two["conditional_radius_by_host_tolerance"][3]["max_of_nearest_compatible_source_km"]==0.0
