"""Counterfactual certified-negative witness design; never promote zeros to absences."""
import pytest

from benchmarks import wetland_negative_witness_plan_v1 as m


def test_one_independently_certified_control_absence_makes_saturated_artificial_positive():
    original=m.bounds_with_certified_negatives(8,8,4,6)
    assert original["lower_percentage_points"]==0
    assert original["strict_sign_status"]=="strict_direction_not_identified"
    hypothetical=m.bounds_with_certified_negatives(8,8,4,6,negative_b=1)
    assert hypothetical["strict_sign_status"]=="strict_positive"
    assert hypothetical["lower_percentage_points"]==pytest.approx(100/6)
    assert hypothetical["upper_percentage_points"]==pytest.approx(100/3)
    assert not hypothetical["zero_still_feasible"]


def test_one_independently_certified_intervention_absence_makes_negative_vs_full_artificial():
    original=m.bounds_with_certified_negatives(9,13,8,8)
    assert original["upper_percentage_points"]==0
    hypothetical=m.bounds_with_certified_negatives(9,13,8,8,negative_a=1)
    assert hypothetical["strict_sign_status"]=="strict_negative"
    assert hypothetical["lower_percentage_points"]==pytest.approx(-400/13)
    assert hypothetical["upper_percentage_points"]==pytest.approx(-100/13)
    assert not hypothetical["zero_still_feasible"]


def test_true_negative_occupied_source_site_is_rejected():
    for args in [
        (8,8,4,6,1,0),
        (8,8,4,6,0,3),
        (9,13,8,8,0,1),
        (8,8,4,6,-1,0),
        (8,8,4,6,0,1.0),
    ]:
        with pytest.raises(ValueError):
            m.bounds_with_certified_negatives(*args[:4],negative_a=args[4],
                                              negative_b=args[5])


def test_source_positive_only_weak_sign_needs_valid_negative_not_more_nondetections():
    original=m.bounds_with_certified_negatives(12,13,8,8)
    assert original["strict_sign_status"]=="strict_direction_not_identified"
    assert original["upper_percentage_points"]==0
    # More simple unvalidated nondetections contribute no valid constraint.
    assert m.bounds_with_certified_negatives(12,13,8,8)==original
    assert m.bounds_with_certified_negatives(12,13,8,8,negative_a=1)["strict_sign_status"]=="strict_negative"


def test_joint_site_cover_shares_site_visits_across_taxa_but_not_certificates():
    targets={
      "L_int":{("r","L"),("x","L")},
      "H_int":{("r","H")},
      "L_ctrl":{("n","L"),("q","L")},
      "H_ctrl":{("n","H"),("p","H")}
    }
    out=m.minimum_cover(targets)
    assert out["target_count"]==4
    assert out["distinct_candidate_sites"]==5
    assert out["candidate_site_species_records"]==7
    assert out["minimum_distinct_site_visit_count_in_counterfactual_ideal"]==2
    assert out["all_minimum_site_visit_sets"]==[["n","r"]]
    assert out["minimum_independent_true_negative_site_species_certificates"]==4
    # Four independent species×site certificates can be distributed
    # over more than two sites; only the *minimum-site* visit set is unique.
    assert len(out["all_minimum_certificate_sets"])==8
    assert any({(r["site"],r["species"]) for r in records}=={
        ("r","L"),("r","H"),("n","L"),("n","H")
    }for records in out["all_minimum_certificate_sets"])


def test_empty_or_unreachable_targets_fail_closed():
    for d in ({},{"a":set()}):
        with pytest.raises(ValueError):
            m.minimum_cover(d)


def test_strict_biological_direction_not_inferred_from_new_positive_alone():
    # Even after every unknown control site is re-observed positive,
    # the true artificial-control difference becomes 0, not strictly >0.
    all_positive=m.bounds_with_certified_negatives(8,8,6,6)
    assert all_positive["strict_sign_status"]=="strict_direction_not_identified"
    assert all_positive["lower_percentage_points"]==0
    assert all_positive["upper_percentage_points"]==0
