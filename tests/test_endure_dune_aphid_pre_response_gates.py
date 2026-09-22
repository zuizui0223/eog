import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from validation.endure_dune_aphid_selective_promotion import gate0_metadata
from validation.endure_dune_aphid_selective_promotion import gate1_zip_inventory


def _contract():
    path = (
        Path("validation")
        / "endure_dune_aphid_selective_promotion"
        / "source_selection_contract.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def _metadata_bytes():
    contract = _contract()
    source = contract["source_identity"]
    return json.dumps(
        {
            "key": source["gbif_dataset_key"],
            "title": source["title"],
            "type": "SAMPLING_EVENT",
            "doi": source["doi"],
            "modified": "2026-08-10T00:00:00.000+00:00",
            "pubDate": "2026-08-10T00:00:00.000+00:00",
            "license": "CC_BY_4_0",
            "endpoints": [
                {"type": "DWC_ARCHIVE", "url": source["archive_url"]},
                {
                    "type": "EML",
                    "url": (
                        "https://ipt.biodiversity.be/eml.do?"
                        "r=endure-invertebrate-sampling-occurrences"
                    ),
                },
            ],
        }
    ).encode("utf-8")


def test_focal_selection_is_frozen_before_archive_access():
    contract = _contract()
    focal = contract["focal_endpoint_selection"]
    assert focal["scientific_name"] == "Metopolophium sabihae"
    assert focal["target_selected_before_archive_payload_access"] is True
    assert focal["endures_species_counts_used_for_selection"] is False
    assert focal["endures_occurrence_rows_used_for_selection"] is False
    assert focal["endures_prevalence_used_for_selection"] is False
    assert contract["gate0_metadata_only"]["archive_bytes_allowed"] == 0
    assert contract["gate1_archive_inventory"]["member_payload_bytes_allowed"] == 0


def test_gate0_accepts_exact_semantic_metadata_identity(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "gate0.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    calls = []

    def fetcher(url, maximum_bytes):
        calls.append((url, maximum_bytes))
        return _metadata_bytes()

    result = gate0_metadata.run(
        contract_path,
        output_path,
        fetcher=fetcher,
    )
    assert result["status"] == "gate0_metadata_ready_for_zip_inventory"
    assert result["metadata_request_count"] == 1
    assert result["archive_requests"] == 0
    assert result["archive_bytes_opened"] == 0
    assert result["occurrence_member_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert calls == [
        (
            contract["gate0_metadata_only"]["authorized_url"],
            contract["gate0_metadata_only"]["maximum_metadata_bytes"],
        )
    ]


def test_gate0_stops_on_dataset_identity_drift(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "gate0.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    metadata = json.loads(_metadata_bytes())
    metadata["key"] = "wrong-key"

    result = gate0_metadata.run(
        contract_path,
        output_path,
        fetcher=lambda *_: json.dumps(metadata).encode("utf-8"),
    )
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert "dataset key drift" in result["reason"]
    assert result["archive_requests"] == 0
    assert result["occurrence_member_bytes_opened"] == 0


def _zip_payload():
    path = Path("/tmp/endure-gate1-test.zip")
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("meta.xml", "<archive/>")
        archive.writestr("eml.xml", "<eml/>")
        archive.writestr("event.txt", "eventID\nE1\n")
        archive.writestr(
            "occurrence.txt",
            "eventID\tscientificName\toccurenceStatus\n"
            "E1\tSECRET_RESPONSE\tpresent\n",
        )
    payload = path.read_bytes()
    path.unlink()
    return payload


class _FakeRangeTransport:
    payload = b""

    def __init__(self, url, allowed_hosts, maximum_archive_size):
        self.url = url
        self.allowed_hosts = allowed_hosts
        self.maximum_archive_size = maximum_archive_size
        self.range_ledger = []
        self.archive_size = None

    def probe_size(self):
        self.archive_size = len(self.payload)
        self.range_ledger.append(
            {
                "role": "archive_size_probe",
                "start": 0,
                "end": 0,
                "status": 206,
                "bytes_opened": 1,
            }
        )
        return self.archive_size

    def read_range(self, start, end, role):
        body = self.payload[start : end + 1]
        self.range_ledger.append(
            {
                "role": role,
                "start": start,
                "end": end,
                "status": 206,
                "bytes_opened": len(body),
            }
        )
        return body


def test_gate1_reads_inventory_only_and_never_occurrence_payload(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    gate0_path = tmp_path / "gate0.json"
    output_path = tmp_path / "gate1.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    gate0_path.write_text(
        json.dumps(
            {
                "status": "gate0_metadata_ready_for_zip_inventory",
                "fingerprint": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    _FakeRangeTransport.payload = _zip_payload()

    result = gate1_zip_inventory.run(
        contract_path,
        gate0_path,
        output_path,
        transport_factory=_FakeRangeTransport,
    )
    assert result["status"] == "gate1_zip_inventory_ready_for_meta_schema_freeze"
    names = {row["basename"] for row in result["members"]}
    assert {"meta.xml", "eml.xml", "event.txt", "occurrence.txt"} <= names
    assert result["local_header_bytes_opened"] == 0
    assert result["member_payload_bytes_opened"] == 0
    assert result["event_member_bytes_opened"] == 0
    assert result["occurrence_member_bytes_opened"] == 0
    assert result["occurrence_rows_opened"] == 0
    assert result["biological_response_values_opened"] is False


def test_gate1_does_not_run_after_gate0_stop(tmp_path):
    contract = _contract()
    contract_path = tmp_path / "contract.json"
    gate0_path = tmp_path / "gate0.json"
    output_path = tmp_path / "gate1.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    gate0_path.write_text(
        json.dumps(
            {
                "status": "stop_pre_response_metadata_identity_or_transport",
                "fingerprint": "b" * 64,
            }
        ),
        encoding="utf-8",
    )

    result = gate1_zip_inventory.run(
        contract_path,
        gate0_path,
        output_path,
        transport_factory=_FakeRangeTransport,
    )
    assert result["status"] == "not_run_gate0_not_ready"
    assert result["range_requests"] == 0
    assert result["occurrence_member_bytes_opened"] == 0
