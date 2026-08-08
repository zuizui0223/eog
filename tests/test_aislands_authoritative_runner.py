from pathlib import Path
import importlib.util
import json


def _load_runner():
    path = Path("benchmarks/run_aislands_authoritative_benchmark.py")
    spec = importlib.util.spec_from_file_location("aislands_authoritative_runner", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_runner_matches_frozen_model_and_reachability_contracts():
    runner = _load_runner()
    model = json.loads(
        Path("validation/aislands_model_contract_20260808/support_model_contract.json").read_text()
    )
    reach = json.loads(
        Path("validation/aislands_reachability_contract_20260808/reachability_contract.json").read_text()
    )

    assert tuple(item["id"].replace("bio0", "bio") for item in model["climate_source"]["variables"]) == runner.PREDICTORS
    assert model["pointwise_support_model"]["class_weighting"] == "none"
    assert model["evaluation_partition"]["n_folds"] == 5
    assert reach["scenario_ensemble"]["scenario_count"] == 12
    assert reach["primary_heldout_statistic"]["stratification"] == {
        "support_bins": 5,
        "distance_bins": 5,
        "binning_rule": "deterministic empirical rank bins formed from held-out pointwise support and nearest-anchor distance values without consulting held-out labels; exact ties remain in the same bin",
    }
    assert runner.BOOTSTRAP_REPLICATES == 10_000
    assert runner.RANDOM_SEED == 20260808


def test_runner_pins_preoutcome_artifact_hashes():
    runner = _load_runner()
    assert runner.FROZEN_CLIMATE_SHA256 == "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285"
    assert runner.FROZEN_COHORT_SHA256 == "cf645d55b8bcc46be8a8dc5399db736bbcc20bb7114a72c79a5dee61ec918e12"
    assert runner.FROZEN_FOLDS_SHA256 == "221a925e289347069c89354d26acfab83fa3d4bc130b56f0178b8db30ab427fa"
