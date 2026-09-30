import os

import pytest

from validation.bam_greatlakes_barrier_external_bridge_v1.run_external_bridge_once import (
    ExecutionStop,
    load_authorized_contract,
    verify_dryad_token,
)


def test_gate2_contract_is_authorized_and_bound_to_gate1():
    gate1, contract = load_authorized_contract()
    assert gate1["status"] == "readme_schema_ready"
    assert contract["status"] == "authorized_for_once_only_rds_execution"
    assert contract["gate1_prerequisite"]["fingerprint"] == gate1["fingerprint"]
    assert contract["engine_binding"]["world_count"] == 35


def test_missing_dryad_token_stops_before_payload(monkeypatch):
    monkeypatch.delenv("DRYAD_TOKEN", raising=False)
    with pytest.raises(ExecutionStop, match="absent"):
        verify_dryad_token()
