"""Exact positive-only partial identification without inventing true absences."""
import pytest
from benchmarks import wetland_positive_only_partial_id_v1 as m


def test_both_strict_signs_remain_possible_with_two_groups_partially_detected():
    r=m.bound_counts(1,3,1,2)
    assert r["conditional_identification_status"]=="two_sided_strict_signs_possible"
    assert r["conditional_negative_possible"] and r["conditional_positive_possible"]
    assert r["conditional_zero_possible"]
    assert not r["conditional_strict_nonzero_sign_identified"]
    assert r["conditional_latent_lower_percentage_points"]==pytest.approx(-200/3)
    assert r["conditional_latent_upper_percentage_points"]==50


def test_one_sided_nonnegative_if_group_A_is_source_confirmed_everywhere():
    r=m.bound_counts(8,8,4,6)
    assert r["observed_recorded_difference_percentage_points"]==pytest.approx(100/3)
    assert r["conditional_latent_lower_percentage_points"]==0
    assert r["conditional_latent_upper_percentage_points"]==pytest.approx(100/3)
    assert r["conditional_identification_status"]=="nonnegative_only"
    assert not r["conditional_negative_possible"]
    assert r["conditional_zero_possible"] and r["conditional_positive_possible"]


def test_one_sided_nonpositive_if_group_B_source_confirmed_everywhere():
    r=m.bound_counts(9,13,8,8)
    assert r["conditional_identification_status"]=="nonpositive_only"
    assert r["conditional_latent_lower_percentage_points"]==pytest.approx(-400/13)
    assert r["conditional_latent_upper_percentage_points"]==0
    assert r["conditional_negative_possible"]
    assert not r["conditional_positive_possible"]
    assert r["conditional_zero_possible"]


def test_all_positive_both_groups_exact_zero_not_nonzero_sign():
    r=m.bound_counts(13,13,8,8)
    assert r["conditional_identification_status"]=="exact_zero"
    assert r["observed_recorded_difference_percentage_points"]==0
    assert r["conditional_latent_lower_percentage_points"]==0
    assert r["conditional_latent_upper_percentage_points"]==0
    assert not r["conditional_negative_possible"] and not r["conditional_positive_possible"]
    assert not r["conditional_strict_nonzero_sign_identified"]


def test_method_only_observed_sign_reversal_does_not_reverse_source_positive_bounds():
    full=m.bound_counts(8,8,4,6)
    av=m.bound_counts(0,8,3,6)
    assert full["observed_recorded_direction"]==1
    assert av["observed_recorded_direction"]==-1
    assert full["identified_lower_numerator"]==0
    assert av["identified_lower_numerator"]<0
    assert full["identified_upper_numerator"]<=av["identified_upper_numerator"]
    assert full["conditional_zero_possible"] and av["conditional_zero_possible"]
    # Native source confirms 8/8 positives in artificial, so a strictly
    # negative latent artificial-control difference is impossible,
    # conditional on positive specificity, regardless of AV zeros.


def test_paired_core_has_40_more_unfixed_binary_cells_not_field_entropy():
    original_cells=27*9
    native_positives=144
    AV_positives=104
    assert original_cells-native_positives==99
    assert original_cells-AV_positives==139
    assert (1<<139)//(1<<99)==(1<<40)


@pytest.mark.parametrize("wrong",[
    (1,0,2,4),(1,4,2,0),(5,4,1,3),(-1,3,1,3),
    (1,3,-1,3),(1,3,4,3),(1.2,3,2,3),(True,3,2,3)
])
def test_bad_counts_denominator_and_uncertainty_are_rejected(wrong):
    with pytest.raises(ValueError):
        m.bound_counts(*wrong)


def test_no_source_recorded_negative_is_upgraded_to_true_absence():
    r=m.bound_counts(0,4,0,6)
    assert r["conditional_identification_status"]=="two_sided_strict_signs_possible"
    assert r["conditional_latent_lower_percentage_points"]==-100
    assert r["conditional_latent_upper_percentage_points"]==100
    assert r["conditional_zero_possible"]


def test_original_five_predeclared_source_recorded_reversal_cases():
    assert len(m.FIXED_REVERSALS)==5
    assert ("artificial","control","Lissotriton vulgaris") in m.FIXED_REVERSALS
    assert ("intervention","artificial","Lissotriton vulgaris") in m.FIXED_REVERSALS
