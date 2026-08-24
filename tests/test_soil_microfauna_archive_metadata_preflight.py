import io
import json
import zipfile
from pathlib import Path

import pytest

from validation.soil_microfauna_paired_complementarity.run_archive_metadata_preflight import (
    FrozenRangeTransport,
    inspect_zip_metadata,
)


def _archive(*, comment=b""):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("geometry/nodes.csv", "node,x,y\na,0,0\nb,1,1\n")
        archive.writestr("response/soil_fauna.csv", "node,time,response\na,15,1\n")
        archive.comment = comment
    return buffer.getvalue()


def _reader(payload, ledger):
    def read(start, end, role):
        ledger.append((role, start, end))
        return payload[start : end + 1]

    return read


def _overlaps(first, second):
    return first[0] <= second[1] and second[0] <= first[1]


def test_inventory_reads_only_zip_metadata_ranges():
    payload = _archive()
    ledger = []

    result = inspect_zip_metadata(len(payload), _reader(payload, ledger))

    assert result["member_count"] == 2
    assert [member["name"] for member in result["members"]] == [
        "geometry/nodes.csv",
        "response/soil_fauna.csv",
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


def test_zip_comment_stops_without_backwards_scan():
    payload = _archive(comment=b"not permitted")
    ledger = []

    with pytest.raises(RuntimeError, match="zero-comment ZIP EOCD"):
        inspect_zip_metadata(len(payload), _reader(payload, ledger))

    assert ledger == [("zip_eocd_zero_comment", len(payload) - 22, len(payload) - 1)]


def test_local_and_central_member_name_mismatch_stops():
    payload = bytearray(_archive())
    payload[30] = ord("X")

    with pytest.raises(RuntimeError, match="local/central member name mismatch"):
        inspect_zip_metadata(len(payload), _reader(payload, []))


def test_frozen_contract_keeps_all_member_payload_access_forbidden():
    contract = json.loads(
        Path(
            "validation/soil_microfauna_paired_complementarity/source_contract.json"
        ).read_text(encoding="utf-8")
    )

    gate = contract["archive_metadata_gate"]
    boundary = contract["stage_boundary"]
    assert gate["archive"]["size_bytes"] == 17_249_862
    assert gate["metadata_evidence"]["file_payload_bytes_opened"] == 0
    assert boundary["archive_container_metadata_access_allowed"] is True
    assert boundary["archive_member_payload_access_allowed"] is False
    assert boundary["response_header_access_allowed"] is False
    assert boundary["response_payload_access_allowed"] is False


def test_non_range_response_stops_before_reading_any_body(monkeypatch):
    class FakeResponse:
        status = 200

        def __init__(self):
            self.read_calls = 0
            self.headers = {"Content-Length": "17249862"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def geturl(self):
            return "https://zenodo.org/records/7528078/files/archive.zip"

        def read(self, _size):
            self.read_calls += 1
            return b"PK"

    response = FakeResponse()
    monkeypatch.setattr(
        "validation.soil_microfauna_paired_complementarity."
        "run_archive_metadata_preflight.urllib.request.urlopen",
        lambda *_args, **_kwargs: response,
    )
    transport = FrozenRangeTransport(
        "https://zenodo.org/api/records/7528078/files/archive.zip/content",
        17_249_862,
    )

    with pytest.raises(RuntimeError, match="HTTP 200"):
        transport.read(0, 0, "archive_size_and_signature_probe")

    assert response.read_calls == 0
    assert transport.ledger == [
        {
            "role": "archive_size_and_signature_probe",
            "start": 0,
            "end": 0,
            "bytes": 0,
            "status": 200,
            "content_range": None,
            "final_host": "zenodo.org",
        }
    ]
