import json
from pathlib import Path


def test_contraction_conditioned_contract_is_response_free_and_post_portal():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "validation/layer_b_mechanism_v2/contraction_conditioned_known_truth_contract_v1.json").read_text()
    )
    assert contract["frozen_before_runner"] is True
    assert contract["uses_biological_response"] is False
    assert contract["counts_as_fresh_predictive_endpoint"] is False
    assert contract["changes_closed_eog_wf_synthesis"] is False
    assert contract["post_portal_hypothesis"] is True
    assert contract["design"]["replicates"] == 64
    assert contract["design"]["true_world_threshold"] == 0.22
    assert contract["decision"]["production_gate_authorized_by_this_test_alone"] is False


def test_cross_endpoint_audit_keeps_azores_unidentified():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads(
        (root / "validation/layer_b_mechanism_v2/cross_endpoint_contraction_audit_v1.json").read_text()
    )
    assert audit["cross_endpoint_hypothesis_status"] == "not_identified"
    rows = {row["system"]: row for row in audit["endpoints"]}
    azores = rows["Azores yellow eel telemetry"]
    assert azores["layer_a_contraction_status"] == "not_recoverable_from_frozen_terminal_evidence"
    assert azores["raw_response_reopen_allowed"] is False
    assert rows["Southwest Louisiana King Rail passive acoustics"]["layer_a_contraction_status"] == "contracted"
    assert rows["Tampa Bay seagrass monitoring"]["layer_a_contraction_status"] == "fully_saturated"
    assert rows["Portal Dipodomys merriami contextual-representation validation"]["layer_a_contraction_status"] == "fully_saturated"
