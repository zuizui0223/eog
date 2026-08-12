from benchmarks.distribution_structural_discrimination import run_synthetic_contract


def test_distribution_model_structural_discrimination_contract():
    result = run_synthetic_contract()
    assert result["all_checks_pass"] is True
    assert all(result["checks"].values())
