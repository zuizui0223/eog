import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/conditional_structural_value/known_truth_2x2_contract_v1.json"
RUNNER = ROOT / "benchmarks/conditional_structural_value_2x2.py"


def test_contract_is_response_free_and_frozen():
    p = json.loads(CONTRACT.read_text())
    assert p["frozen_before_runner"] is True
    assert p["uses_biological_response"] is False
    assert p["counts_as_fresh_predictive_endpoint"] is False
    assert p["historical_systems_not_reanalyzed"] is True


def test_contract_has_only_two_declared_moderators():
    p = json.loads(CONTRACT.read_text())
    assert set(p["factors"]) == {"reference_saturation", "response_alignment"}
    assert p["design"]["factorial"] == "2 x 2 full factorial"
    assert p["design"]["replicates"] == 64


def test_success_rules_are_frozen_before_result():
    p = json.loads(CONTRACT.read_text())
    expected = {
        "weak_refreshed_median_added_value_strictly_negative",
        "weak_refreshed_favorable_fraction_at_least_0_90",
        "saturation_moderation_median_strictly_positive",
        "saturation_moderation_positive_fraction_at_least_0_80",
        "alignment_moderation_median_strictly_positive",
        "alignment_moderation_positive_fraction_at_least_0_80",
        "weak_refreshed_is_best_median_cell",
    }
    assert set(p["predeclared_checks"]) == expected


def test_runner_does_not_read_empirical_validation_tree():
    text = RUNNER.read_text()
    assert "validation/azores" not in text
    assert "validation/louisiana" not in text
    assert "validation/tampa" not in text
    assert "A-Islands" not in text
    assert "Tanzania" not in text
