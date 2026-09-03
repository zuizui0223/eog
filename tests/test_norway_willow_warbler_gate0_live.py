import json
from pathlib import Path

import pytest

from validation.norway_willow_warbler_endpoint3.gate0_live_metadata import (
    LiveMetadataStop,
    _read_record_metadata,
    run,
)


class FakeResponse:
    def __init__(self, body: bytes, *, status=200, content_type="application/json"):
        self._body = body
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "Content-Encoding": "identity",
        }
        self.read_called = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def getcode(self):
        return self.status

    def geturl(self):
        return "https://zenodo.org/api/records/18452203"

    def read(self, _n=-1):
        self.read_called = True
        return self._body


def _auth():
    return {
        "authorized_url": "https://zenodo.org/api/records/18452203",
        "allowed_final_host": "zenodo.org",
        "maximum_metadata_bytes": 2_000_000,
    }


def _metadata():
    return {
        "id": 18452203,
        "doi": "10.5281/zenodo.18452203",
        "metadata": {
            "title": "National-scale acoustic monitoring of avian biodiversity and migration"
        },
        "files": [
            {
                "key": "National_PAM_of_Biodiversity_Bick_et_al_2026.zip",
                "size": 491_572_428,
                "checksum": "md5:47a757dd5aae5974498e3b953d684282",
                "links": {
                    "content": "https://zenodo.org/api/records/18452203/files/archive/content"
                },
            }
        ],
    }


def test_metadata_get_reads_only_record_json():
    response = FakeResponse(json.dumps(_metadata()).encode())

    def opener(_request, timeout):
        assert timeout == 60
        return response

    metadata, ledger = _read_record_metadata(_auth(), opener=opener)
    assert metadata["id"] == 18452203
    assert response.read_called is True
    assert ledger["request_count"] == 1
    assert ledger["metadata_bytes_opened"] > 0


def test_non_200_stops_before_body_read():
    response = FakeResponse(b"forbidden body", status=503)

    def opener(_request, timeout):
        return response

    with pytest.raises(LiveMetadataStop, match="body was not opened"):
        _read_record_metadata(_auth(), opener=opener)
    assert response.read_called is False


def test_wrong_content_type_stops_before_body_read():
    response = FakeResponse(b"<html></html>", content_type="text/html")

    def opener(_request, timeout):
        return response

    with pytest.raises(LiveMetadataStop, match="body was not opened"):
        _read_record_metadata(_auth(), opener=opener)
    assert response.read_called is False


def test_run_keeps_archive_member_and_response_payloads_closed(tmp_path: Path):
    response = FakeResponse(json.dumps(_metadata()).encode())

    def opener(_request, timeout):
        return response

    out = tmp_path / "certificate.json"
    result = run(output_path=out, opener=opener)
    assert result["status"] == "gate0_metadata_ready"
    assert result["archive_payload_requests"] == 0
    assert result["archive_payload_bytes_opened"] == 0
    assert result["member_payload_requests"] == 0
    assert result["member_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert out.exists()
