"""Deterministic leave-one-native-site-out sign robustness, no field SE."""
import pytest
from benchmarks import wetland_method_site_jackknife_v1 as m


def source_fixture():
    sites={
        "I1":"intervention","I2":"intervention",
        "C1":"control","C2":"control",
        "A1":"artificial","A2":"artificial"
    }
    witnesses={
        ("I1","frog"):{"dipnet"},
        ("I2","frog"):{"bottletrap"},
        ("C1","frog"):{"visual"},
        ("A1","frog"):{"acoustic"}
    }
    return sites,witnesses


def test_matched_26_site_mathematical_contrast_is_not_naive_fixed_denominator():
    sites,witnesses=source_fixture()
    source=set(witnesses)
    x=m.calc_contrast(source,sites,"frog","intervention","control")
    assert (x["category_a_n"],x["category_b_n"])==(2,2)
    assert x["numerator"]==2
    assert x["signed_direction"]==1
    reduced={s:c for s,c in sites.items() if s!="C1"}
    sub={k for k in source if k[0]!="C1"}
    y=m.calc_contrast(sub,reduced,"frog","intervention","control")
    assert (y["category_a_n"],y["category_b_n"])==(2,1)
    assert y["numerator"]==2
    assert y["signed_direction"]==1


def test_synthetic_source_reversal_persistence_vs_ties():
    sites,witnesses=source_fixture()
    out=m.pure_jackknife(sites,witnesses,["frog"])
    assert out["source_site_count"]==6
    assert out["method_panel_count"]==15
    assert out["site_deletion_cases"]==6
    assert out["contrast_count_per_panel_site_drop"]==3
    assert out["full_27_baseline_strict_reversals_by_panel"]["acoustic+visual"]==1
    av=out["panel_summary"]["acoustic+visual"]
    assert av["leave_one_site_out_cases"]==6
    assert av["max"]>=1
    assert out["panel_summary"]["acoustic+visual+dipnet+bottletrap"]["max"]==0
    rows=out["outputs"]["method_panel_site_drop_contrasts"]
    assert len(rows)==15*6*3
    matching=[
        x for x in rows
        if x["panel"]=="acoustic+visual" and
           x["category_a"]=="intervention" and x["category_b"]=="control"
    ]
    by_site={x["excluded_site"]:x for x in matching}
    assert by_site["A1"]["method_subset_strict_reversal_after_site_drop"]==1
    assert by_site["A2"]["method_subset_strict_reversal_after_site_drop"]==1
    assert by_site["C1"]["method_subset_strict_reversal_after_site_drop"]==0
    assert by_site["C1"]["method_subset_tie_transition_after_site_drop"]==1


def test_invalid_method_source_and_missing_category_fail_closed():
    sites,witnesses=source_fixture()
    with pytest.raises(ValueError,match="native positive"):
        m.pure_jackknife(sites,{("I1","frog"):{"not_method"}},["frog"])
    with pytest.raises(ValueError,match="native positive"):
        m.pure_jackknife(sites,{("unknown_site","frog"):{"visual"}},["frog"])
    with pytest.raises(ValueError,match="category"):
        m.pure_jackknife({"I":"intervention","C":"control"},witnesses,["frog"])
    with pytest.raises(ValueError,match="site"):
        m.calc_contrast(set(witnesses),sites,"frog","control","control")


def test_original_paper_Q1_five_are_explicit_predeclared_not_posthoc_search():
    assert len(m.EXPECTED_AV_FIVE)==5
    assert (
        "artificial","control","Lissotriton vulgaris"
    ) in m.EXPECTED_AV_FIVE
    assert m.EXPECTED_TOTALS=={"intervention":13,"control":6,"artificial":8}
