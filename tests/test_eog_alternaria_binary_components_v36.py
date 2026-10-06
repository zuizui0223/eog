import numpy as np

from benchmarks.run_eog_alternaria_binary_components_v36 import _binary_history


def test_binary_history_maps_only_Alternaria_to_focal_level():
    history = np.asarray(
        ["Alternaria", "Aureobasidium", "Cladosporium", "Dioszegia", "Fusarium"],
        dtype=object,
    )
    binary = _binary_history(history)
    assert binary.tolist() == [
        "Alternaria",
        "Other",
        "Other",
        "Other",
        "Other",
    ]
