from __future__ import annotations

import json
from pathlib import Path

import pytest

from validation.sebms_ochlodes_endpoint3.gate0_gbif_registry import (
    RegistryGateStop,
    evaluate_gbif_registry,
    load_contract,
    terminal_stop_result,
)
from validation.sebms_ochlodes_endpoint3.gate0_live_registry import run


CONTRACT = load_contract()


def _metadata() -> dict[str, object]:
    return {
        "key": "be77e203-486c-4651-91b9-8347968b728c",
        "title": "Swedish Butterfly Monitoring Scheme (SeBMS)",
        "type": "SAMPLING_EVENT",
        "doi": "10.15468/othndo",
        "pubDate": "2025-03-24T00:00:00.000+00:00",
        "modified": "2025-03-24T00:00:00.000+00:00",
        "endpoints": [
            {
                "type": "DWC_ARCHIVE",
                "url": "https://www.gbif.se/ipt/archive.do?r=lu_sebms",
            },
            {
                "type": "EML",
                "url": "https://www.gbif.se/ipt/eml.do?r=lu_sebms",
            },
        ],
    }


def test_exact_registry_identity_passes_without_dwca_access():
    result = evaluate_gbif_registry(_metadata(), CONTRACT)
    assert result["status"] == "gate0_metadata_ready"
    assert result["identity"]["dataset_key"] == CONTRACT["source"]["dataset_key"]
    assert result["identity"]["frozen_version_dwca_url"].endswith("&v=1.12")
    assert result["dwca_payload_requests"] == 0
    assert result["occurrence_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("key", "wrong", "dataset key drift"),
        ("title", "Other dataset", "dataset title drift"),
        ("type", "OCCURRENCE", "dataset type drift"),
        ("doi", "10.0000/wrong", "dataset DOI drift"),
    ],
)
def test_primary_identity_drift_fails_closed(key: str, value: str, message: str):
    metadata = _metadata()
    metadata[key] = value
    with pytest.raises(RegistryGateStop, match=message):
        evaluate_gbif_registry(metadata, CONTRACT)


def test_missing_frozen_dwca_endpoint_fails_closed():
    metadata = _metadata()
    metadata["endpoints"] = [{"type": "EML", "url": "https://www.gbif.se/ipt/eml.do?r=lu_sebms"}]
    with pytest.raises(RegistryGateStop, match="occurs 0 times"):
        evaluate_gbif_registry(metadata, CONTRACT)


def test_duplicate_frozen_dwca_endpoint_fails_closed():
    metadata = _metadata()
    metadata["endpoints"] = [metadata["endpoints"][0], dict(metadata["endpoints"][0])]
    with pytest.raises(RegistryGateStop, match="occurs 2 times"):
        evaluate_gbif_registry(metadata, CONTRACT)


def test_terminal_stop_preserves_full_response_firewall():
    result = terminal_stop_result(CONTRACT, "synthetic stop")
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert result["dwca_payload_requests"] == 0
    assert result["dwca_payload_bytes_opened"] == 0
    assert result["event_rows_opened"] == 0
    assert result["emof_rows_opened"] == 0
    assert result["occurrence_header_bytes_opened"] == 0
    assert result["occurrence_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0


class _Headers(dict):
    def items(self):
        return super().items()


class _FakeResponse:
    def __init__(self, body: bytes, *, status: int = 200, allow_read: bool = True):
        self._body = body
        self.status = status
        self.allow_read = allow_read
        self.read_called = False
        self.headers = _Headers(
            {
                "Content-Type": "application/json",
                "Content-Encoding": "identity",
            }
        )

    def getcode(self):
        return self.status

    def geturl(self):
        return "https://api.gbif.org/v1/dataset/be77e203-486c-4651-91b9-8347968b728c"

    def read(self, _n: int):
        self.read_called = True
        if not self.allow_read:
            raise AssertionError("response body must not be opened")
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_live_runner_with_mocked_registry_reads_one_json_only(tmp_path: Path):
    response = _FakeResponse(json.dumps(_metadata()).encode("utf-8"))

    def opener(_request, timeout=60):
        assert timeout == 60
        return response

    output = tmp_path / "gate0.json"
    result = run(output_path=output, opener=opener)
    assert result["status"] == "gate0_metadata_ready"
    assert response.read_called is True
    assert result["live_registry_transport"]["request_count"] == 1
    assert result["dwca_payload_requests"] == 0
    assert result["occurrence_rows_opened"] == 0
    assert output.exists()


def test_non_200_stops_before_body_read(tmp_path: Path):
    response = _FakeResponse(b"forbidden", status=500, allow_read=False)

    def opener(_request, timeout=60):
        return response

    result = run(output_path=tmp_path / "stop.json", opener=opener)
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert response.read_called is False
    assert result["dwca_payload_requests"] == 0
    assert result["response_values_opened"] is False
