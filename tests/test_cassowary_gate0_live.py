import json
from pathlib import Path

import pytest

from validation.cassowary_endpoint3.gate0_live_metadata import (
    LiveMetadataStop,
    _read_article_metadata,
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
        return "https://api.figshare.com/v2/articles/28050704"

    def read(self, _n=-1):
        self.read_called = True
        return self._body


def _auth():
    return {
        "authorized_url": "https://api.figshare.com/v2/articles/28050704",
        "allowed_final_host": "api.figshare.com",
        "maximum_metadata_bytes": 2_000_000,
    }


def _metadata():
    return {
        "id": 28050704,
        "title": "Range-wide camera trapping to reveal cassowary habitat associations",
        "files": [
            {
                "id": 51265058,
                "name": "primary.zip",
                "download_url": "https://figshare.com/ndownloader/files/51265058",
                "size": 12345,
                "supplied_md5": "0123456789abcdef0123456789abcdef",
            },
            {
                "id": 999,
                "name": "unrelated.txt",
                "download_url": "https://figshare.com/ndownloader/files/999",
                "size": 100,
            },
        ],
    }


def test_metadata_get_reads_json_only():
    response = FakeResponse(json.dumps(_metadata()).encode())

    def opener(_request, timeout):
        assert timeout == 60
        return response

    metadata, ledger = _read_article_metadata(_auth(), opener=opener)
    assert metadata["id"] == 28050704
    assert response.read_called is True
    assert ledger["request_count"] == 1
    assert ledger["metadata_bytes_opened"] > 0


def test_non_200_stops_before_body_read():
    response = FakeResponse(b"forbidden body", status=503)

    def opener(_request, timeout):
        return response

    with pytest.raises(LiveMetadataStop, match="body was not opened"):
        _read_article_metadata(_auth(), opener=opener)
    assert response.read_called is False


def test_wrong_content_type_stops_before_body_read():
    response = FakeResponse(b"<html></html>", content_type="text/html")

    def opener(_request, timeout):
        return response

    with pytest.raises(LiveMetadataStop, match="body was not opened"):
        _read_article_metadata(_auth(), opener=opener)
    assert response.read_called is False


def test_run_never_opens_file_payload(tmp_path: Path):
    response = FakeResponse(json.dumps(_metadata()).encode())

    def opener(_request, timeout):
        return response

    out = tmp_path / "certificate.json"
    result = run(output_path=out, opener=opener)
    assert result["status"] == "gate0_metadata_ready"
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert out.exists()
