from __future__ import annotations

from email.message import Message

import pytest

from validation.loomis_snowshoe_hare_endpoint3.gate1a_header import HeaderGateStop
from validation.loomis_snowshoe_hare_endpoint3.run_gate1a_headers import StrictZenodoByteTransport


class FakeResponse:
    def __init__(self, *, status: int, content_range: str | None, body: bytes = b"x", url: str = "https://zenodo.org/f"):
        self.status = status
        self._body = body
        self._url = url
        self.read_called = False
        self.headers = Message()
        if content_range is not None:
            self.headers["Content-Range"] = content_range
        self.headers["Content-Encoding"] = "identity"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, n=-1):
        self.read_called = True
        return self._body[:n]


def test_206_exact_range_reads_one_byte(monkeypatch):
    response = FakeResponse(status=206, content_range="bytes 3-3/10", body=b"z")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: response)
    t = StrictZenodoByteTransport("https://zenodo.org/file.csv", 10)
    assert t.read_byte(3, "r") == b"z"
    assert response.read_called is True
    assert t.ledger[0]["bytes_opened"] == 1


def test_http_200_stops_before_body_read(monkeypatch):
    response = FakeResponse(status=200, content_range=None, body=b"whole-file")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: response)
    t = StrictZenodoByteTransport("https://zenodo.org/file.csv", 10)
    with pytest.raises(HeaderGateStop, match="HTTP 200"):
        t.read_byte(0, "r")
    assert response.read_called is False
    assert t.ledger[0]["bytes_opened"] == 0


def test_wrong_content_range_stops_before_body_read(monkeypatch):
    response = FakeResponse(status=206, content_range="bytes 0-0/11", body=b"a")
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: response)
    t = StrictZenodoByteTransport("https://zenodo.org/file.csv", 10)
    with pytest.raises(HeaderGateStop, match="Content-Range"):
        t.read_byte(0, "r")
    assert response.read_called is False


def test_redirect_host_escape_stops_before_body_read(monkeypatch):
    response = FakeResponse(
        status=206,
        content_range="bytes 0-0/10",
        body=b"a",
        url="https://example.org/file.csv",
    )
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: response)
    t = StrictZenodoByteTransport("https://zenodo.org/file.csv", 10)
    with pytest.raises(HeaderGateStop, match="allowed host"):
        t.read_byte(0, "r")
    assert response.read_called is False


def test_invalid_offset_fails_without_request(monkeypatch):
    called = False

    def bad(*a, **k):
        nonlocal called
        called = True
        raise AssertionError

    monkeypatch.setattr("urllib.request.urlopen", bad)
    t = StrictZenodoByteTransport("https://zenodo.org/file.csv", 10)
    with pytest.raises(HeaderGateStop, match="invalid byte offset"):
        t.read_byte(10, "r")
    assert called is False
