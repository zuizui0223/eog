from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


BENCHMARK_PATH = Path(__file__).resolve().parents[1] / "benchmarks" / "support_topology_stress.py"
SPEC = spec_from_file_location("support_topology_stress", BENCHMARK_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
run_benchmark = MODULE.run_benchmark


def test_support_topology_stress_benchmark_is_deterministic():
    first = run_benchmark(seed=1234, noise_replicates=12)
    second = run_benchmark(seed=1234, noise_replicates=12)
    assert first == second


def test_headline_components_survive_predeclared_stress_scenarios():
    result = run_benchmark(seed=20260722, noise_replicates=30)
    summary = result["summary"]
    assert summary["threshold_retention"] == 1.0
    assert summary["neighbourhood_retention"] == 1.0
    assert summary["resolution_retention"] == 1.0
    assert summary["anchor_retention"] == 1.0
    assert summary["noise_retention"] >= 0.90


def test_anchor_perturbation_records_all_locations_as_anchored():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    assert all(row["headline_retained"] for row in result["anchor_scenarios"])


def test_resolution_changes_preserve_equal_area_component_area():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    areas = [row["detached_area"] for row in result["resolution_scenarios"]]
    assert all(area is not None for area in areas)
    assert max(areas) - min(areas) < 1e-12


def test_benchmark_keeps_claim_limit_explicit():
    result = run_benchmark(seed=20260722, noise_replicates=5)
    assert "does not establish occupancy prediction" in result["claim_limit"]
    assert "superiority" in result["claim_limit"]
