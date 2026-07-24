from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


BENCHMARK_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "support_topology_heldout_comparison.py"
)
SPEC = spec_from_file_location("support_topology_heldout_comparison", BENCHMARK_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
run_benchmark = MODULE.run_benchmark


def test_heldout_comparison_is_deterministic():
    assert run_benchmark() == run_benchmark()


def test_multi_threshold_contract_outperforms_frozen_baselines():
    result = run_benchmark()
    metrics = result["metrics"]
    multi = metrics["multi_threshold_persistent"]
    assert multi["roc_auc"] == 1.0
    assert multi["brier_score"] == 0.0
    for method in (
        "support_only",
        "distance_only",
        "support_plus_distance",
        "single_threshold_detached",
    ):
        assert multi["roc_auc"] > metrics[method]["roc_auc"]
        assert multi["brier_score"] < metrics[method]["brier_score"]


def test_single_threshold_confuses_transient_patches():
    result = run_benchmark()
    transient = [
        row for row in result["candidates"] if row["candidate_id"].startswith("transient_")
    ]
    assert len(transient) == 2
    assert all(row["single_threshold_class"] == "persistent_detached_component" for row in transient)
    assert all(row["multi_threshold_class"] == "transient_detached_component" for row in transient)
    assert all(row["scores"]["single_threshold_detached"] == 1.0 for row in transient)
    assert all(row["scores"]["multi_threshold_persistent"] == 0.0 for row in transient)


def test_claim_limit_remains_explicit():
    claim = run_benchmark()["claim_limit"]
    assert "does not establish empirical predictive superiority" in claim
    assert "occupancy probability" in claim
