import os

import pytest

from validation.bam_greatlakes_barrier_external_bridge_v1.run_external_bridge_once import (
    ExecutionStop,
    configured_dryad_token,
    load_authorized_contract,
    verify_dryad_token,
)


def test_gate2_contract_is_authorized_and_bound_to_gate1():
    gate0, gate1, contract = load_authorized_contract()
    assert gate0["status"] == "dryad_source_identity_ready"
    assert gate1["status"] == "readme_schema_ready"
    assert gate1["gate0_fingerprint"] == gate0["fingerprint"]
    assert contract["status"] == "authorized_for_once_only_rds_execution"
    assert contract["gate1_prerequisite"]["fingerprint"] == gate1["fingerprint"]
    assert contract["engine_binding"]["world_count"] == 35


def test_missing_all_supported_dryad_credentials_stops_before_payload(monkeypatch):
    for name in (
        "DRYAD_TOKEN",
        "DRYAD_API_TOKEN",
        "DRYAD_ACCESS_TOKEN",
        "DRYAD_CLIENT_ID",
        "DRYAD_CLIENT_SECRET",
        "DRYAD_TOKEN_URL",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(ExecutionStop, match="credentials are absent"):
        configured_dryad_token()


def test_existing_repository_direct_token_alias_is_accepted_without_network(monkeypatch):
    monkeypatch.delenv("DRYAD_TOKEN", raising=False)
    monkeypatch.delenv("DRYAD_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("DRYAD_CLIENT_ID", raising=False)
    monkeypatch.delenv("DRYAD_CLIENT_SECRET", raising=False)
    monkeypatch.setenv("DRYAD_API_TOKEN", "fixture-token")
    token, mode = configured_dryad_token()
    assert token == "fixture-token"
    assert mode == "direct_bearer_token"


def test_legacy_bridge_token_remains_accepted(monkeypatch):
    monkeypatch.setenv("DRYAD_TOKEN", "legacy-fixture-token")
    monkeypatch.setenv("DRYAD_API_TOKEN", "new-fixture-token")
    token, mode = configured_dryad_token()
    assert token == "legacy-fixture-token"
    assert mode == "legacy_dryad_token"
