from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from eog.v2.http_range_transport import HttpTransportLedgerRow
from validation.inbo_camtrap_prelock_transport_screen.screen import (
    run,
    screen_source,
)


def _zip_payload():
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "deployments.csv",
            (
                "deploymentID,locationID,latitude,longitude,deploymentStart,deploymentEnd\n"
                "D1,L1,50.0,4.0,2024-01-01T00:00:00Z,2024-01-10T00:00:00Z\n"
                "D2,L1,50.0,4.0,2024-02-01T00:00:00Z,2024-02-10T00:00:00Z\n"
                "D3,L2,50.1,4.1,2024-01-01T00:00:00Z,2024-01-10T00:00:00Z\n"
            ),
        )
        archive.writestr(
            "observations.csv",
            (
                "deploymentID,scientificName\n"
                "D1,SECRET_RESPONSE_SPECIES\n"
            ),
        )
        archive.writestr("datapackage.json", '{"name":"test"}')
    return buffer.getvalue()


class FakeTransport:
    payload = b""

    def __init__(self, url, allowed_hosts, maximum_archive_size):
        self.url = url
        self.allowed_hosts = allowed_hosts
        self.maximum_archive_size = maximum_archive_size
        self.archive_size = None
        self.ledger = []

    def discover_size_by_head(self):
        self.archive_size = len(self.payload)
        return self.archive_size

    def discover_size_by_range_probe(self):
        raise AssertionError("HEAD should qualify size in this fixture")

    def read_range(self, start, end, role):
        self.ledger.append(
            HttpTransportLedgerRow(
                role=role,
                method="GET",
                start=start,
                end=end,
                status=206,
                final_host="example.org",
                content_range=f"bytes {start}-{end}/{len(self.payload)}",
                content_length=str(end - start + 1),
                bytes_opened=end - start + 1,
            )
        )
        return self.payload[start : end + 1]


def _contract():
    return {
        "archive_bounds": {
            "maximum_archive_size_bytes": 10_000_000,
            "maximum_central_directory_bytes": 100_000,
        },
        "safe_member": {
            "basename": "deployments.csv",
            "maximum_compressed_bytes": 1_000_000,
            "maximum_uncompressed_bytes": 1_000_000,
        },
        "response_member": {
            "basename": "observations.csv",
            "payload_access_allowed": False,
        },
    }


def _source():
    return {
        "source_id": "fixture",
        "gbif_dataset_key": "fixture-key",
        "doi": "10.0000/fixture",
        "title": "Fixture",
        "archive_url": "https://example.org/archive.zip",
        "allowed_hosts": ["example.org"],
    }


def test_screen_extracts_only_safe_deployments_and_audits_repetition():
    FakeTransport.payload = _zip_payload()
    result = screen_source(
        _source(),
        _contract(),
        transport_factory=FakeTransport,
    )
    assert result["status"] == "transport_qualified_prelock"
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["response_member_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert result["response_member"]["payload_bytes_opened"] == 0

    audit = result["deployment_audit"]
    assert audit["deployment_count"] == 3
    assert audit["unique_exact_coordinate_count"] == 2
    assert audit["exact_coordinates_repeated_across_deployments"] == 1
    assert audit["unique_nonempty_location_id_count"] == 2
    assert audit["location_ids_repeated_across_deployments"] == 1


def test_screen_never_reads_response_member_payload_range():
    FakeTransport.payload = _zip_payload()
    result = screen_source(
        _source(),
        _contract(),
        transport_factory=FakeTransport,
    )
    response = result["response_member"]
    assert response["payload_bytes_opened"] == 0
    assert result["transport_qualification"]["ready"] is True


def test_run_can_screen_multiple_sources_before_candidate_lock(tmp_path):
    FakeTransport.payload = _zip_payload()
    contract = {
        "schema": "fixture",
        "archive_bounds": _contract()["archive_bounds"],
        "safe_member": _contract()["safe_member"],
        "response_member": _contract()["response_member"],
        "sources": [
            _source(),
            {**_source(), "source_id": "fixture2"},
        ],
    }
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    result = run(
        contract_path,
        output_path,
        transport_factory=FakeTransport,
    )
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["qualified_source_ids"] == ["fixture", "fixture2"]
    assert result["biological_response_values_opened"] is False
    assert output_path.exists()
