from __future__ import annotations

from email.message import Message

import pytest

from eog.v2.http_range_transport import (
    HttpRangeTransportError,
    StrictHttpRangeTransport,
)


class FakeResponse:
    def __init__(self, *, status, url, headers=None, body=b""):
        self.status = status
        self._url = url
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value
        self.body = body
        self.read_calls = []

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, n=-1):
        self.read_calls.append(n)
        if n < 0:
            return self.body
        return self.body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout=90):
        self.requests.append(request)
        if not self.responses:
            raise AssertionError("unexpected request")
        return self.responses.pop(0)


def transport(opener, maximum=10_000):
    return StrictHttpRangeTransport(
        "https://data.example.org/archive.zip",
        ("data.example.org",),
        maximum,
        opener=opener,
    )


def test_head_discovers_size_without_reading_body():
    response = FakeResponse(
        status=200,
        url="https://data.example.org/archive.zip",
        headers={"Content-Length": "1234"},
        body=b"THIS BODY MUST NOT BE READ",
    )
    item = transport(FakeOpener([response]))
    assert item.discover_size_by_head() == 1234
    assert item.archive_size == 1234
    assert response.read_calls == []
    assert item.ledger[-1].bytes_opened == 0
    assert item.ledger[-1].method == "HEAD"


def test_range_probe_200_stops_without_reading_body():
    response = FakeResponse(
        status=200,
        url="https://data.example.org/archive.zip",
        headers={"Content-Length": "999"},
        body=b"SECRET MIXED ARCHIVE CONTENT",
    )
    item = transport(FakeOpener([response]))
    with pytest.raises(HttpRangeTransportError, match="HTTP 200"):
        item.discover_size_by_range_probe()
    assert response.read_calls == []
    assert item.ledger[-1].bytes_opened == 0
    assert item.archive_size is None


def test_range_probe_206_reads_exactly_one_byte():
    response = FakeResponse(
        status=206,
        url="https://data.example.org/archive.zip",
        headers={
            "Content-Range": "bytes 0-0/1234",
            "Content-Length": "1",
        },
        body=b"P",
    )
    item = transport(FakeOpener([response]))
    assert item.discover_size_by_range_probe() == 1234
    assert response.read_calls == [2]
    assert item.ledger[-1].bytes_opened == 1


def test_bounded_range_200_stops_without_reading_body():
    response = FakeResponse(
        status=200,
        url="https://data.example.org/archive.zip",
        headers={"Content-Length": "1000"},
        body=b"RESPONSE DATA THAT MUST STAY UNREAD",
    )
    item = transport(FakeOpener([response]))
    item.bind_frozen_size(1000)
    with pytest.raises(HttpRangeTransportError, match="HTTP 200"):
        item.read_range(100, 109, "zip_eocd")
    assert response.read_calls == []
    assert item.ledger[-1].bytes_opened == 0


def test_bounded_range_206_reads_only_requested_length():
    response = FakeResponse(
        status=206,
        url="https://data.example.org/archive.zip",
        headers={
            "Content-Range": "bytes 100-109/1000",
            "Content-Length": "10",
        },
        body=b"0123456789",
    )
    item = transport(FakeOpener([response]))
    item.bind_frozen_size(1000)
    assert item.read_range(100, 109, "central") == b"0123456789"
    assert response.read_calls == [11]
    assert item.ledger[-1].bytes_opened == 10


def test_redirect_outside_allowed_host_fails_before_body_read():
    response = FakeResponse(
        status=206,
        url="https://other.example.net/archive.zip",
        headers={"Content-Range": "bytes 0-0/1234"},
        body=b"P",
    )
    item = transport(FakeOpener([response]))
    with pytest.raises(HttpRangeTransportError, match="left frozen HTTPS host set"):
        item.discover_size_by_range_probe()
    assert response.read_calls == []


def test_frozen_size_can_be_bound_without_network_request():
    opener = FakeOpener([])
    item = transport(opener)
    assert item.bind_frozen_size(4321) == 4321
    assert opener.requests == []
    assert item.ledger == []


def test_invalid_or_oversized_frozen_size_fails_closed():
    item = transport(FakeOpener([]), maximum=1000)
    with pytest.raises(HttpRangeTransportError, match="outside allowed bound"):
        item.bind_frozen_size(1001)
    with pytest.raises(TypeError, match="must be int"):
        item.bind_frozen_size(True)  # type: ignore[arg-type]


def test_head_missing_content_length_is_unqualified_without_body_read():
    response = FakeResponse(
        status=200,
        url="https://data.example.org/archive.zip",
        headers={},
        body=b"UNREAD",
    )
    item = transport(FakeOpener([response]))
    with pytest.raises(HttpRangeTransportError, match="Content-Length"):
        item.discover_size_by_head()
    assert response.read_calls == []
    assert item.ledger[-1].bytes_opened == 0
