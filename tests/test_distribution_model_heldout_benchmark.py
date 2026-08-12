from benchmarks.distribution_model_heldout_benchmark import run_heldout_ranking_benchmark


def test_distribution_model_heldout_ranking_benchmark():
    result = run_heldout_ranking_benchmark()
    assert result["all_checks_pass"] is True
    assert result["auc"]["environmental_support"] == 0.5
    assert result["auc"]["environmental_plus_nearest_source"] == 0.5
    assert result["auc"]["structural_accessibility"] == 1.0
    assert result["auc"]["eog_distribution_support"] == 1.0
