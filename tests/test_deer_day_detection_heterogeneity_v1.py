"""Day-index detection model likelihood and null regression."""
import numpy as np
from benchmarks import deer_day_detection_heterogeneity_v1 as m

def test_design_predeclared():
    assert m.design("constant").shape==(22,1)
    assert m.design("linear").shape==(22,2)
    assert m.design("early_late")[10,1]==0
    assert m.design("early_late")[11,1]==1

def test_constant_likelihood_equals_parent():
    a=np.array([[1,0,np.nan]+[np.nan]*19,[0,0,0]+[np.nan]*19],float)
    theta=np.array([np.log(.6/.4),np.log(.4/.6)])
    value=m.loglike(theta,a,m.design("constant"))
    n=np.isfinite(a).sum(axis=1);k=np.nansum(a,axis=1)
    from benchmarks import emammal_deer_detection_v1 as parent
    assert np.isclose(value,parent.log_likelihood((.6,.4),n,k))

def test_heterogeneous_likelihood_finite():
    a=np.array([[1,0,np.nan]+[np.nan]*19,[0,0,0]+[np.nan]*19],float)
    for model in ("constant","linear","early_late"):
        assert np.isfinite(m.loglike(np.zeros(1+m.design(model).shape[1]),a,m.design(model)))
