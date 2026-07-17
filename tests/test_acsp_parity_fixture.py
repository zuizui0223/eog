import numpy as np
import pytest

from eog import infer_occupancy_geometry


def test_frozen_acsp_reference_fixture():
    """Guard the numerical extraction from ACSP main commit cfa24ba."""
    values = np.array([
        [0.0, 0.0],
        [0.1, -0.1],
        [-0.1, 0.1],
        [8.0, 8.0],
        [8.1, 7.9],
        [7.9, 8.1],
    ])
    geometry = infer_occupancy_geometry(values, gap_multiplier=2.0)

    assert geometry.span == pytest.approx(1.9081652211581932)
    assert geometry.mst_length == pytest.approx(2.003135357468973)
    assert geometry.continuity == pytest.approx(0.9526785249401218)
    assert geometry.gap_strength == pytest.approx(80.00000000000018)
    assert geometry.component_count == 2
    np.testing.assert_allclose(
        geometry.mst_edges,
        np.array([
            [0.0, 1.0, 0.0238468494936782],
            [0.0, 2.0, 0.0238468494936782],
            [0.0, 3.0, 1.9077479594942603],
            [3.0, 4.0, 0.02384684949367812],
            [3.0, 5.0, 0.02384684949367812],
        ]),
    )
