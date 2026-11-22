"""Source-group contrast control tests: integer denominator signs, no causal status."""
import pytest
from benchmarks import wetland_method_group_contrast_v1 as m


def test_strict_sign_reversal_from_identical_sites_different_method_recordings():
    # Same site cohorts; only which recorded method family is retained changes.
    r=m.compare_category_positive_counts(
        a_full=8,b_full=4,a_core=0,b_core=3,na=8,nb=6)
    assert r["strict_direction_reversal"]
    assert r["native_full_direction"]==1
    assert r["paired_core_direction"]==-1
    assert r["native_full_difference_percentage_points"]==pytest.approx(100/3)
    assert r["paired_core_difference_percentage_points"]==-50
    assert r["difference_shift_core_minus_native_percentage_points"]==pytest.approx(-250/3)
    assert not r["ties_in_either_source_representation"]


def test_small_positive_shift_is_not_an_inference_of_causal_effect():
    r=m.compare_category_positive_counts(
        a_full=9,b_full=4,a_core=3,b_core=3,na=13,nb=6)
    assert r["native_full_difference_percentage_points"]==pytest.approx(100/39)
    assert r["paired_core_difference_percentage_points"]==pytest.approx(-350/13)
    # Signs are exact integer comparisons, not rounded percentage comparisons.
    assert r["strict_direction_reversal"]
    assert r["native_full_direction"]==1 and r["paired_core_direction"]==-1


def test_tie_is_not_strict_direction_reversal():
    r=m.compare_category_positive_counts(
        a_full=2,b_full=1,a_core=0,b_core=0,na=8,nb=6)
    assert not r["strict_direction_reversal"]
    assert r["ties_in_either_source_representation"]
    assert r["paired_core_direction"]==0


def test_core_cannot_invent_source_positive_or_invalid_denominator():
    for values in [
        (1,1,2,0,5,5), (3,1,2,2,5,5),
        (1,1,0,0,0,5), (1,1,0,0,5,0),
        (-1,1,0,0,5,5), (1,1,0,0,5.5,5),
    ]:
        with pytest.raises(ValueError):
            m.compare_category_positive_counts(*values)


def test_hard_source_constraints_reject_non_original_q1_site_set():
    nine=[f"taxon{i}" for i in range(9)]
    with pytest.raises(ValueError,match="roster"):
        m.describe([],[{"site":"only","ci":"control"}],nine)


def test_method_and_class_roster_fixed():
    assert m.CATS == ("intervention","control","artificial")
    assert m.CORE == ("acoustic","visual")
    assert len(m.CONTRASTS)==3
