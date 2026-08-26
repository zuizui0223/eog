import io
import json
import zipfile

import pytest

from validation.bbs_northern_bobwhite_replication_2.gate5_archive_metadata import (
    DEFAULT_CONTRACT,
    ArchiveGateStop,
    FrozenRangeTransport,
    inspect_zip_metadata,
    run,
)


def _archive(*, comment=b""):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("50-StopData/example.csv", "header\nresponse-row\n")
        archive.writestr("50-StopData/readme.txt", "metadata\n")
        archive.comment = comment
    return buffer.getvalue()


def _reader(payload, ledger):
    def read(start, end, role):
        ledger.append((role, start, end))
        return payload[start : end + 1]

    return read


def _overlaps(first, second):
    return first[0] <= second[1] and second[0] <= first[1]


def test_inventory_reads_only_zip_container_metadata_ranges():
    payload = _archive()
    ledger = []

    result = inspect_zip_metadata(len(payload), _reader(payload, ledger))

    assert result["member_count"] == 2
    assert [member["name"] for member in result["members"]] == [
        "50-StopData/example.csv",
        "50-StopData/readme.txt",
    ]
    payload_intervals = [
        (member["payload_start"], member["payload_end"])
        for member in result["members"]
        if member["payload_end"] is not None
    ]
    assert all(
        not _overlaps((start, end), interval)
        for _, start, end in ledger
        for interval in payload_intervals
    )
    assert {role.split(":", 1)[0] for role, _, _ in ledger} == {
        "zip_eocd_zero_comment",
        "zip_central_directory",
        "local_header",
        "local_name_extra",
    }


def test_zip_comment_stops_without_a_backwards_scan():
    payload = _archive(comment=b"comment not scanned")
    ledger = []

    with pytest.raises(ArchiveGateStop, match="zero-comment ZIP EOCD"):
        inspect_zip_metadata(len(payload), _reader(payload, ledger))

    assert ledger == [("zip_eocd_zero_comment", len(payload) - 22, len(payload) - 1)]


def test_local_and_central_member_name_mismatch_stops():
    payload = bytearray(_archive())
    payload[30] = ord("X")

    with pytest.raises(ArchiveGateStop, match="local/central member name mismatch"):
        inspect_zip_metadata(len(payload), _reader(payload, []))


def test_non_range_response_stops_before_reading_any_body(monkeypatch):
    class FakeResponse:
        status = 200

        def __init__(self):
            self.read_calls = 0
            self.headers = {"Content-Length": "68998320"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return "https://www.sciencebase.gov/catalog/file/get/example"

        def read(self, _size):
            self.read_calls += 1
            return b"PK"

    response = FakeResponse()
    monkeypatch.setattr(
        "validation.bbs_northern_bobwhite_replication_2."
        "gate5_archive_metadata.urllib.request.urlopen",
        lambda *_args, **_kwargs: response,
    )
    transport = FrozenRangeTransport(
        "https://www.sciencebase.gov/catalog/file/get/example",
        68_998_320,
        ("www.sciencebase.gov",),
    )

    with pytest.raises(ArchiveGateStop, match="body was not opened"):
        transport.read(0, 0, "probe")

    assert response.read_calls == 0
    assert transport.ledger[0]["bytes"] == 0
    assert transport.ledger[0]["status"] == 200


def test_contract_keeps_member_payload_header_rows_and_models_closed():
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    gate = contract["metadata_gate"]
    firewall = contract["response_firewall"]

    assert gate["archive_member_payload_access_allowed"] is False
    assert gate["response_header_access_allowed"] is False
    assert gate["response_row_access_allowed"] is False
    assert gate["forbid_backwards_eocd_scan"] is True
    assert firewall["avian_member_payload_requests"] == 0
    assert firewall["avian_member_payload_bytes_opened"] == 0
    assert firewall["avian_rows_opened"] is False
    assert firewall["model_fits"] == 0
    assert firewall["heldout_scores"] == 0


def test_prerequisite_drift_writes_zero_request_engineering_artifact(tmp_path):
    contract = json.loads(DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    contract["prerequisite_sha256"]["source_contract.json"] = "0" * 64
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    result = run(contract_path, output_path)

    assert result["status"] == "engineering_failure_pre_response"
    assert "prerequisite SHA-256 drift" in result["reason"]
    assert result["archive_metadata_requests"] == 0
    assert result["archive_metadata_bytes_opened"] == 0
    assert output_path.exists()
