"""Effort/detection likelihood tests, independent of ecological outcomes."""
import math
import pytest
from benchmarks import bam_detection_effort_v1 as m

def test_nondetection_retains_occupied_candidate_when_p_below_one():
    sites=(0,1,2,3,4,5)
    assert m.likelihood(0,0b111111,sites,0.8,3)>0
    assert m.likelihood(0,0b111111,sites,1.,1)==0

def test_no_false_positives():
    sites=(0,1,2,3,4,5)
    assert m.likelihood(1,0,sites,0.8,3)==0
    assert m.likelihood(1,1,sites,0.8,3)>0

def test_exact_likelihood_normalization():
    sites=tuple(range(6))
    for p,k in m.SCENARIOS:
        for g in (0,1,0b10101,0b111111):
            assert sum(m.likelihood(obs,g,sites,p,k) for obs in range(64))==pytest.approx(1.)

def test_more_visits_reduce_occupied_nondetection_probability():
    sites=tuple(range(6))
    assert m.likelihood(0,1,sites,0.8,6)<m.likelihood(0,1,sites,0.8,3)<m.likelihood(0,1,sites,0.8,1)

def test_target_blind_site_selection():
    rows=[{"A_bits":1,"B_bits":1,"M_bits":1,"G_bits":1},
          {"A_bits":2,"B_bits":2,"M_bits":2,"G_bits":2}]
    assert m.choose_sites(rows,6)==(0,1,2,3,4,5)
    with pytest.raises(ValueError):m.choose_sites(rows,5,6)

def test_invalid_p_rejected():
    with pytest.raises(ValueError):m.likelihood(0,1,tuple(range(6)),0,1)
    with pytest.raises(ValueError):m.likelihood(0,1,tuple(range(6)),0.8,0)
