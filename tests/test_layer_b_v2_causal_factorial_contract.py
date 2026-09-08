from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/layer_b_mechanism_v2/causal_factorial_contract_v1.json"
RUNNER = ROOT / "benchmarks/layer_b_v2_causal_factorial.py"


def test_causal_factorial_contract_is_closed_and_response_free() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert payload["schema"] == "eog.layer_b_mechanism_v2.causal_factorial_contract.v1"
    assert payload["counts_as_fresh_predictive_endpoint"] is False
    assert payload["uses_biological_response"] is False
    assert payload["changes_closed_eog_wf_synthesis"] is False
    assert payload["layer_a_modified"] is False
    assert payload["design"]["factorial"] == "2^3 full factorial"
    assert payload["design"]["replicates"] == 64
    assert len(payload["design"]["replicate_seeds"]) == 64
    assert payload["factors"] == [
        "training_serving_generator_shift",
        "static_repeated_state_under_dynamic_truth",
        "label_dependent_single_source",
    ]


def test_runner_cannot_be_mistaken_for_empirical_endpoint() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "uses_biological_response" in text
    assert '"counts_as_fresh_predictive_endpoint": False' in text
    assert "EERecords.csv" not in text
    assert "tampa_seagrass" not in text
    assert "RandomForestClassifier" in text
