"""Held-out site scoring is an exact binary-sequence probability."""
import numpy as np
from scipy.special import betaln
from benchmarks import deer_site_heldout_prediction_v1 as m

def test_beta_converges_to_constant():
    n=np.array([3,5,7]);k=np.array([0,2,6])
    psi=.7;p=.4;concentration=100000.
    a=m.site_log_score_constant(psi,p,n,k)
    b=m.site_log_score_beta(psi,p*concentration,(1-p)*concentration,n,k)
    assert np.allclose(a,b,atol=3e-4)

def test_zero_detection_uses_absent_mixture():
    n=np.array([3]);k=np.array([0]);psi=.5
    assert np.isclose(np.exp(m.site_log_score_constant(psi,.5,n,k))[0],.5+.5*.5**3)

def test_positive_detection_has_no_absence_component():
    n=np.array([3]);k=np.array([1]);psi=.5;p=.2
    assert np.isclose(np.exp(m.site_log_score_constant(psi,p,n,k))[0],psi*p*(1-p)**2)
