from benchmarks.distribution_gate_shrinkage import run_gate_shrinkage_benchmark


def test_distribution_gate_shrinks_to_environmental_model():
    result = run_gate_shrinkage_benchmark()
    assert result["all_checks_pass"] is True
    assert result["structural_gate_cross_fitted"] is True
    assert result["structural_gate_weight"] == 0.0
    assert result["auc"]["environmental_support"] == 1.0
    assert result["auc"]["eog_distribution_support"] == 1.0
