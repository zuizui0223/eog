"""No invented biological variance: exact fixed source-processing seed guards."""
import math
import pytest
from benchmarks import wetland_seed_ensemble_v1 as m


def test_exact_with_replacement_loss_probability():
    assert math.isclose(m.prob_all_native_positives_dropped(18,1),(17/18)**20)
    assert m.prob_all_native_positives_dropped(15,15)==0
    assert m.prob_all_native_positives_dropped(2,1)==(1/2)**20


def test_exact_without_replacement_loss_probability():
    assert math.isclose(m.prob_all_native_positives_dropped(21,1),1/21)
    assert m.prob_all_native_positives_dropped(21,2)==0
    assert m.prob_all_native_positives_dropped(22,1)>0


def test_invalid_inputs_fail_closed():
    for args in [(1,0),(3,4),(0,1),(3,1,0),(3,1.5)]:
        with pytest.raises(ValueError):
            m.prob_all_native_positives_dropped(*args)


def test_fixed_roster_and_seed123_included():
    assert len(m.SEEDS)==256 and m.SEEDS[0]==1 and m.SEEDS[-1]==256
    assert 123 in m.SEEDS


def test_quantile_and_processing_dispersion():
    assert m.sorted_quantile([0,10,20],.5)==10
    assert m.sorted_quantile([0,10,20],.25)==5
    assert m.sorted_quantile([0,10,20],.0)==0
    assert m.sorted_quantile([0,10,20],1.0)==20
    out=m.describe_seed_values([0,10,20])
    assert out["mean"]==10
    assert out["median"]==10
    assert out["descriptive_mc_se"]>0
    with pytest.raises(ValueError):
        m.sorted_quantile([],0.5)


def test_extra_seed_fails_closed_before_source_scoring():
    with pytest.raises(ValueError,match="outside fixed"):
        m.validate_and_summarize([{"seed":"999"}],[],[],[],[])


def test_duplicate_seed_fails_closed():
    with pytest.raises(ValueError,match="duplicate"):
        m.validate_and_summarize([{"seed":"1"},{"seed":"1"}],[],[],[],[])
