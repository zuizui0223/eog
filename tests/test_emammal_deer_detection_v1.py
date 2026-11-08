"""Real repeated detection likelihood tests (source fetched separately)."""
import numpy as np
from benchmarks import emammal_deer_detection_v1 as m

def test_all_zero_likelihood_is_occupancy_mixture():
    n=np.array([4]);k=np.array([0])
    psi,p=.6,.4
    assert np.isclose(np.exp(m.log_likelihood((psi,p),n,k)),(1-psi)+psi*(1-p)**4)

def test_positive_history_cannot_be_unoccupied():
    n=np.array([4]);k=np.array([2])
    psi,p=.6,.4
    assert np.isclose(np.exp(m.log_likelihood((psi,p),n,k)),psi*p**2*(1-p)**2)

def test_NA_does_not_become_zero():
    x=np.array([[1,0,np.nan,1],[0,0,np.nan,0],[0,1,0,0],[0,0,0,0],[1,1,1,1]],float)
    r=m.fit(x,4)
    assert r["n_valid_site_days"]==18
    assert r["n_detected_site_days"]==7
    assert r["n_sites_at_least_2_visits"]==5
    assert 0<r["p_MLE"]<1 and 0<r["psi_MLE"]<1

def test_invalid_probability_fails_closed():
    assert m.log_likelihood((0,.5),np.array([3]),np.array([1]))==-np.inf
