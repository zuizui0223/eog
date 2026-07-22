import numpy as np

from eog import SupportTopologyConfig, infer_support_topology


def test_masked_cell_values_do_not_change_topology_or_fingerprint():
    mask = np.array([[False, True, False]])
    first = infer_support_topology(
        np.array([[0.9, -999.0, 0.9]]),
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,)),
        missing_mask=mask,
    )
    second = infer_support_topology(
        np.array([[0.9, 999.0, 0.9]]),
        {"known": (0, 0)},
        SupportTopologyConfig((0.8,)),
        missing_mask=mask,
    )
    assert first.fingerprint == second.fingerprint
    assert first.components == second.components
