"""Prior-family and likelihood misspecification contracts."""
import numpy as np
import pytest
from benchmarks import bam_detection_prior_calibration_v1 as m

STATES=[{"G":1,"sign":-1},{"G":1,"sign":-1},{"G":2,"sign":1},{"G":3,"sign":0}]

def test_all_priors_are_strict_and_normalized():
    for family in m.PRIOR_FAMILIES:
        w=m.weights(STATES,family)
        assert np.all(w>0)
        assert np.isclose(w.sum(),1)

def test_uniform_G_is_not_uniform_mask():
    w=m.weights(STATES,"uniform_G")
    assert np.isclose(w[0]+w[1],w[2])
    assert np.isclose(w[2],w[3])

def test_uniform_sign_equalizes_sign_mass():
    w=m.weights(STATES,"uniform_sign")
    assert np.isclose(w[:2].sum(),w[2])
    assert np.isclose(w[2],w[3])

def test_unknown_prior_rejected():
    with pytest.raises(ValueError):
        m.weights(STATES,"data_driven")

def test_scenarios_fixed():
    assert m.TRUE_PS==(0.5,0.8)
    assert m.ASSUMED_PS==(0.5,0.8)
    assert m.VISITS==3
