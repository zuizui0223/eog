import numpy as np

from benchmarks.run_eog_alternaria_genotype_generality_v37 import (
    _binary_history,
    _designs,
    _model_stats,
)


def test_binary_history():
    x = np.asarray(["Alternaria", "Fusarium", "Dioszegia"], dtype=object)
    assert _binary_history(x).tolist() == ["Alternaria", "Other", "Other"]


def test_nested_design_ranks_in_balanced_example():
    genotype = np.asarray(["g1"] * 4 + ["g2"] * 4, dtype=object)
    binary = np.asarray(
        ["Alternaria", "Alternaria", "Other", "Other"] * 2,
        dtype=object,
    )
    m0, m1, m2 = _designs(genotype, binary)
    assert np.linalg.matrix_rank(m0) < np.linalg.matrix_rank(m1)
    assert np.linalg.matrix_rank(m1) < np.linalg.matrix_rank(m2)


def test_history_ss_decomposition_adds():
    genotype = np.asarray(["g1"] * 4 + ["g2"] * 4, dtype=object)
    binary = np.asarray(
        ["Alternaria", "Alternaria", "Other", "Other"] * 2,
        dtype=object,
    )
    y = np.asarray([0.8, 0.75, 0.4, 0.45, 0.7, 0.72, 0.5, 0.48])
    stats = _model_stats(y, binary, genotype)
    assert np.isclose(
        stats["SS_common"] + stats["SS_context"],
        stats["SS_total"],
    )
