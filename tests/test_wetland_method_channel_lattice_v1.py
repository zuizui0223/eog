"""Method-subset Boolean witness lattice, exact contrast signs and safety checks."""
import pytest
from benchmarks import wetland_method_channel_lattice_v1 as m


def test_declared_15_nonempty_method_subsets_are_exhaustive():
    subsets=m.method_panels()
    assert len(subsets)==15
    assert len(set(subsets))==15
    assert [sum(len(p)==k for p in subsets) for k in range(1,5)]==[4,6,4,1]
    assert subsets[-1]==m.METHODS
    assert m.panel_name(("acoustic","visual"))=="acoustic+visual"
    assert m.panel_name(("visual","dipnet","bottletrap"))=="visual+dipnet+bottletrap"


def test_exact_native_method_union_is_monotone_without_ecological_absence():
    detected={
        ("a","frog"):{"acoustic"},
        ("a","newt"):{"bottletrap"},
        ("b","newt"):{"visual","dipnet"},
    }
    panels=m.method_panels()
    for a in panels:
        for b in panels:
            if set(a)<=set(b):
                assert m.positive_witnesses(detected,a)<=m.positive_witnesses(detected,b)
    assert m.positive_witnesses(detected,("acoustic","visual"))=={
        ("a","frog"),("b","newt")
    }
    assert len(m.positive_witnesses(detected,m.METHODS))==3


def test_leave_one_out_exclusive_observation_witnesses_only():
    detected={
        ("A","frog"):{"acoustic"},
        ("B","newt"):{"bottletrap"},
        ("C","frog"):{"visual","dipnet"},
    }
    full=m.positive_witnesses(detected,m.METHODS)
    for method in m.METHODS:
        remainder=tuple(m for m in m.METHODS if m!=method)
        lost=full-m.positive_witnesses(detected,remainder)
        assert lost=={pair for pair,methodset in detected.items()
                      if methodset=={method}}


def test_crossproduct_sign_reversal_but_not_an_estimated_occupancy_effect():
    n,d=m.exact_difference(8,4,8,6)
    k,_=m.exact_difference(0,3,8,6)
    assert (n,d)==(16,48) and k==-24
    assert n*k<0
    assert 100*n/d==pytest.approx(100/3)
    assert 100*k/d==-50
    assert m.sign(n)==1 and m.sign(k)==-1 and m.sign(0)==0


def test_bad_method_subset_or_invalid_group_denominator_fails_closed():
    for methods in ((),("visual","acoustic"),("acoustic","acoustic"),
                    ("unrecorded",),("visual","trawl")):
        with pytest.raises(ValueError):
            m.panel_name(methods)
    for a,b,na,nb in ((-1,1,3,3),(1,5,3,3),(1,1,0,3),
                       (1,1,3,0),(1,1.2,3,3)):
        with pytest.raises(ValueError):
            m.exact_difference(a,b,na,nb)


def test_missing_source_dimensions_or_wrong_method_type_blocked():
    nine=[f"species{i}" for i in range(9)]
    with pytest.raises(ValueError,match="original source dimensions"):
        m.validate_source([],[],nine)
    with pytest.raises(ValueError,match="invalid or empty"):
        m.compute_lattice({f"site{i}":"control" for i in range(27)},
                          {("a","newt"):set()}, {}, ["newt"])
