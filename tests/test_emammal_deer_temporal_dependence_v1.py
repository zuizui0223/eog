"""Temporal transition null keeps NA locations and within-site detections."""
import numpy as np
from benchmarks import emammal_deer_temporal_dependence_v1 as m

def test_transition_counts_exclude_missing():
    a=np.array([[1,1,0,np.nan,0],[0,0,1,1,1]],float)
    x=m.transitions(a)
    assert x=={"pairs":6,"same":4,"11":3,"00":1,"switch":2}

def test_permutation_keeps_site_counts_and_missing_positions():
    a=np.array([[1,1,0,np.nan,0],[0,0,1,1,np.nan]],float)
    b=m.permute_within_site(a,np.random.default_rng(42))
    assert np.array_equal(np.isnan(a),np.isnan(b))
    assert np.allclose(np.nansum(a,axis=1),np.nansum(b,axis=1))

def test_no_pairs():
    a=np.array([[np.nan,1,np.nan]],float)
    assert m.transitions(a)["pairs"]==0
