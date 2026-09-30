import io
import os
import zipfile

import pytest

from validation.bam_greatlakes_barrier_external_bridge_v1.run_external_bridge_once import (
    ExecutionStop,
    configured_dryad_token,
    download_bound_file,
    load_authorized_contract,
    try_anonymous_version_archive,
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


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, n: int = -1) -> bytes:
        return self._body if n < 0 else self._body[:n]


class _FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout=0):
        return self.response


def test_bad_http200_archive_records_payload_bytes_and_forbids_zero_byte_retry(monkeypatch):
    import validation.bam_greatlakes_barrier_external_bridge_v1.run_external_bridge_once as mod

    gate0, _, contract = load_authorized_contract()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("unexpected.txt", b"payload")
    payload = buffer.getvalue()
    monkeypatch.setattr(mod, "_OPENER", _FakeOpener(_FakeResponse(payload)))

    with pytest.raises(ExecutionStop) as caught:
        try_anonymous_version_archive(gate0, contract)
    assert caught.value.payload_requests == 1
    assert caught.value.payload_bytes_opened == len(payload)
    assert caught.value.payload_bytes_opened > 0


def test_checksum_bound_file_size_drift_records_opened_bytes(monkeypatch):
    import validation.bam_greatlakes_barrier_external_bridge_v1.run_external_bridge_once as mod

    monkeypatch.setattr(mod, "_OPENER", _FakeOpener(_FakeResponse(b"x")))
    spec = {
        "path": "fixture.rds",
        "download_api_path": "/api/v2/files/1/download",
        "size_bytes": 2,
        "sha256": "0" * 64,
    }
    with pytest.raises(ExecutionStop) as caught:
        download_bound_file(spec, "fixture-token")
    assert caught.value.payload_requests == 1
    assert caught.value.payload_bytes_opened == 1
