import json
from pathlib import Path


def test_selective_promotion_contract_is_outer_response_safe():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "validation/layer_b_mechanism_v2/selective_promotion_known_truth_contract_v1.json").read_text()
    )
    assert contract["frozen_before_runner"] is True
    assert contract["uses_biological_response"] is False
    assert contract["counts_as_fresh_predictive_endpoint"] is False
    assert contract["changes_closed_eog_wf_synthesis"] is False
    assert contract["depends_on_contraction_gate"] is False
    assert contract["design"]["no_outer_feedback"] is True
    assert contract["decision"]["production_use_authorized_by_this_test_alone"] is False


def test_selective_promotion_has_three_predeclared_regimes():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "validation/layer_b_mechanism_v2/selective_promotion_known_truth_contract_v1.json").read_text()
    )
    assert set(contract["regimes"]) == {
        "helpful_stable",
        "neutral",
        "harmful_shift_visible_in_calibration",
    }
    assert sum(spec["replicates"] for spec in contract["regimes"].values()) == 96
