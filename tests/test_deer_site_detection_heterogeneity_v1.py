"""Beta-mixture site detection likelihood checks."""
import numpy as np
from scipy.special import expit
from benchmarks import deer_site_detection_heterogeneity_v1 as m
from benchmarks import emammal_deer_detection_v1 as base

def test_beta_mixture_converges_to_constant_as_concentration_increases():
    n=np.array([3,5,7]);k=np.array([0,2,6])
    psi=.7;p=.4;concentration=100000.
    theta=np.array([np.log(psi/(1-psi)),np.log(p*concentration),np.log((1-p)*concentration)])
    assert np.isclose(m.mixture_loglike(theta,n,k),base.log_likelihood((psi,p),n,k),atol=1e-4)

def test_zero_history_is_mixture_of_absence_and_nondetection():
    n=np.array([4]);k=np.array([0])
    psi=.6;alpha=2.;beta=3.
    from scipy.special import betaln
    theta=np.array([np.log(psi/(1-psi)),np.log(alpha),np.log(beta)])
    expected=(1-psi)+psi*np.exp(betaln(alpha,beta+4)-betaln(alpha,beta))
    assert np.isclose(np.exp(m.mixture_loglike(theta,n,k)),expected)

def test_positive_history_cannot_be_unoccupied():
    n=np.array([4]);k=np.array([2])
    psi=.6;alpha=2.;beta=3.
    from scipy.special import betaln
    theta=np.array([np.log(psi/(1-psi)),np.log(alpha),np.log(beta)])
    expected=psi*np.exp(betaln(alpha+2,beta+2)-betaln(alpha,beta))
    assert np.isclose(np.exp(m.mixture_loglike(theta,n,k)),expected)
