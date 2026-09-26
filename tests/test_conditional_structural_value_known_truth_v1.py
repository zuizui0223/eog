from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/conditional_structural_value/known_truth_factorial_contract_v1.json"
RUNNER = ROOT / "benchmarks/conditional_structural_value_known_truth_v1.py"

def test_contract_is_response_free_and_fixed():
    p = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert p["schema"] == "eog.conditional_structural_value.known_truth_factorial_contract.v1"
    assert p["uses_biological_response"] is False
    assert p["counts_as_fresh_predictive_endpoint"] is False
    assert p["changes_closed_eog_wf_synthesis"] is False
    assert p["design"]["factorial"] == "2x2 full factorial"
    assert p["design"]["replicates"] == 64
    assert len(p["design"]["replicate_seeds"]) == 64
    assert p["factors"] == ["reference_saturation", "response_alignment"]

def test_runner_has_no_historical_response_dependency():
    text = RUNNER.read_text(encoding="utf-8")
    for forbidden in ("A-Islands", "Tanzania", "Azores", "Louisiana", "Tampa", "portal_final"):
        assert forbidden not in text
    assert "LogisticRegression" in text
    assert "uses_biological_response" in text
