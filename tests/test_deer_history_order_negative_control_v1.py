"""Conditional order negative control preserves site sufficiency statistics."""
import numpy as np
from benchmarks import deer_history_order_negative_control_v1 as m
from benchmarks import deer_site_heldout_prediction_v1 as h
from benchmarks import emammal_deer_temporal_dependence_v1 as p

def test_order_does_not_change_predictive_likelihood():
    mat=np.array([[1,0,1,np.nan,0,0],[0,0,0,1,1,np.nan]],float)
    shuffled=p.permute_within_site(mat,np.random.default_rng(20261114))
    n=np.isfinite(mat).sum(axis=1);k=np.nansum(mat,axis=1)
    n2=np.isfinite(shuffled).sum(axis=1);k2=np.nansum(shuffled,axis=1)
    assert np.array_equal(n,n2) and np.array_equal(k,k2)
    assert np.array_equal(np.isnan(mat),np.isnan(shuffled))
    assert np.allclose(h.site_log_score_constant(.72,.37,n,k),h.site_log_score_constant(.72,.37,n2,k2))
    assert np.allclose(h.site_log_score_beta(.84,.79,1.71,n,k),h.site_log_score_beta(.84,.79,1.71,n2,k2))
