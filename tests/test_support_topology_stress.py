from benchmarks.support_topology_stress import run_benchmark


def test_support_topology_stress_benchmark_is_deterministic():
    first = run_benchmark(seed=1234, noise_replicates=12)
    second = run_benchmark(seed=1234, noise_replicates=12)
    assert first == second


def test_headline_components_survive_most_predeclared_stress_scenarios():
    result = run_benchmark(seed=20260722, noise_replicates=30)
    summary = result["summary"]
    assert summary["threshold_retention"] == 1.0
    assert summary["neighbourhood_retention"] == 1.0
    assert summary["resolution_retention"] == 1.0
    assert summary["noise_retention"] >= 0.90


def test_anchor_perturbation_exposes_threshold_dependence():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    # Only the anchor already active at the highest threshold preserves the
    # occurrence-anchored headline class under the current birth-state rule.
    assert result["summary"]["anchor_retention"] == 0.2
    retained = [row for row in result["anchor_scenarios"] if row["headline_retained"]]
    assert [row["anchor"] for row in retained] == [[2, 2]]


def test_resolution_changes_preserve_equal_area_component_area():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    areas = [row["detached_area"] for row in result["resolution_scenarios"]]
    assert all(area is not None for area in areas)
    assert max(areas) - min(areas) < 1e-12


def test_benchmark_keeps_claim_limit_explicit():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    assert "does not establish occupancy prediction" in result["claim_limit"]
    assert "superiority" in result["claim_limit"]
