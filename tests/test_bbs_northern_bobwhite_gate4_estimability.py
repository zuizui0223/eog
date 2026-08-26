import json

import pytest

from validation.bbs_northern_bobwhite_replication_2.gate4_prospective_estimability import (
    COUNT_KEYS,
    DEFAULT_CONTRACT,
    run,
)


def test_gate4_preserves_uncertainty_and_requires_the_exact_count_gate(tmp_path):
    result = run(output_path=tmp_path / "result.json")

    assert result["status"] == "uncertain_pre_response"
    assert result["disposition"] == "continue_response_blind_exact_gate_required"
    assert result["exact_count_gate_required"] is True
    assert result["outcome_access_authorized"] is False
    assert result["estimability"]["failing_keys"] == ()
    assert result["estimability"]["unresolved_keys"] == COUNT_KEYS


def test_external_route_total_is_not_relabelled_as_endpoint_matched_evidence():
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))

    assert contract["evidence"]["endpoint_definition_matches"] is False
    assert (
        contract["evidence"]["context_only_not_endpoint_evidence"][
            "reported_detected_route_count"
        ]
        == 1956
    )
    assert all(
        interval == {"lower": None, "upper": None}
        for interval in contract["evidence"]["intervals"].values()
    )


def test_gate4_opens_no_avian_bytes_and_fits_no_models(tmp_path):
    result = run(output_path=tmp_path / "result.json")
    firewall = result["response_firewall"]

    assert firewall == {
        "avian_payload_requests": 0,
        "avian_payload_bytes_opened": 0,
        "avian_header_bytes_opened": 0,
        "avian_rows_opened": False,
        "avian_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }


def test_gate4_rejects_post_response_estimability_evidence(tmp_path):
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    contract["evidence"]["response_rows_opened"] = True
    path = tmp_path / "post_response_contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="before row-level response access"):
        run(contract_path=path, output_path=tmp_path / "result.json")
