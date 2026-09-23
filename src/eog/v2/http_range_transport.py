"""Strict HTTPS bounded-range transport for response-blind archive qualification.

HTTP details are transport evidence, not ecological criteria. This class implements one
possible response-blind route. A caller may mark this route unqualified and still use a
different prospectively declared route.

The transport never falls back from a failed Range request to a full-body GET.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import urllib.error
import urllib.request
from urllib.parse import urlparse


class HttpRangeTransportError(RuntimeError):
    """A bounded HTTPS transport route could not satisfy its frozen byte contract."""


@dataclass(frozen=True)
class HttpTransportLedgerRow:
    role: str
    method: str
    start: int | None
    end: int | None
    status: int | None
    final_host: str | None
    content_range: str | None
    content_length: str | None
    bytes_opened: int


class StrictHttpRangeTransport:
    """HTTPS Range reader with explicit host and byte bounds."""

    def __init__(
        self,
        url: str,
        allowed_hosts: tuple[str, ...],
        maximum_archive_size: int,
        *,
        user_agent: str = "EOG-WF-v2-RangeTransport/1.0",
        opener=None,
    ) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError("archive URL must use HTTPS")
        if not allowed_hosts or parsed.hostname not in allowed_hosts:
            raise ValueError("archive URL host must be in allowed_hosts")
        if (
            isinstance(maximum_archive_size, bool)
            or not isinstance(maximum_archive_size, int)
            or maximum_archive_size < 22
        ):
            raise ValueError("maximum_archive_size must be an integer >= 22")
        self.url = url
        self.allowed_hosts = tuple(allowed_hosts)
        self.maximum_archive_size = maximum_archive_size
        self.user_agent = str(user_agent)
        self.opener = opener or urllib.request.build_opener()
        self.archive_size: int | None = None
        self.ledger: list[HttpTransportLedgerRow] = []

    def _validated_final_host(self, final_url: str) -> str:
        parsed = urlparse(final_url)
        if parsed.scheme != "https" or parsed.hostname not in self.allowed_hosts:
            raise HttpRangeTransportError(
                f"request left frozen HTTPS host set: {parsed.hostname!r}"
            )
        return parsed.hostname or ""

    def bind_frozen_size(self, archive_size: int) -> int:
        """Bind a size supplied by prospectively frozen metadata without HTTP body access."""

        if isinstance(archive_size, bool) or not isinstance(archive_size, int):
            raise TypeError("archive_size must be int")
        if archive_size < 22 or archive_size > self.maximum_archive_size:
            raise HttpRangeTransportError("frozen archive size is outside allowed bound")
        self.archive_size = archive_size
        return archive_size

    def discover_size_by_head(self) -> int:
        """Use a body-free HEAD Content-Length when the server provides one."""

        request = urllib.request.Request(
            self.url,
            method="HEAD",
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "identity",
            },
        )
        status: int | None = None
        final_host: str | None = None
        content_length: str | None = None
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            self.ledger.append(
                HttpTransportLedgerRow(
                    role="archive_size_head",
                    method="HEAD",
                    start=None,
                    end=None,
                    status=status,
                    final_host=None,
                    content_range=None,
                    content_length=None,
                    bytes_opened=0,
                )
            )
            raise HttpRangeTransportError(
                f"archive HEAD returned HTTP {status}; body was not opened"
            ) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise HttpRangeTransportError(
                f"archive HEAD transport unavailable: {exc}"
            ) from exc

        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_host = self._validated_final_host(response.geturl())
            content_length = headers.get("content-length")
            self.ledger.append(
                HttpTransportLedgerRow(
                    role="archive_size_head",
                    method="HEAD",
                    start=None,
                    end=None,
                    status=status,
                    final_host=final_host,
                    content_range=headers.get("content-range"),
                    content_length=content_length,
                    bytes_opened=0,
                )
            )
            if status < 200 or status >= 400:
                raise HttpRangeTransportError(
                    f"archive HEAD returned HTTP {status}; body was not opened"
                )
            if headers.get("content-encoding", "identity").casefold() != "identity":
                raise HttpRangeTransportError("archive HEAD declared content encoding")
            if content_length is None or not re.fullmatch(r"[1-9][0-9]*", content_length):
                raise HttpRangeTransportError(
                    "archive HEAD did not provide a positive Content-Length"
                )
            archive_size = int(content_length)

        return self.bind_frozen_size(archive_size)

    def discover_size_by_range_probe(self) -> int:
        """Read exactly byte zero and require exact HTTP partial-content semantics."""

        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "identity",
                "Range": "bytes=0-0",
            },
        )
        status: int | None = None
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            self.ledger.append(
                HttpTransportLedgerRow(
                    role="archive_size_range_probe",
                    method="GET",
                    start=0,
                    end=0,
                    status=status,
                    final_host=None,
                    content_range=None,
                    content_length=None,
                    bytes_opened=0,
                )
            )
            raise HttpRangeTransportError(
                f"archive size Range probe returned HTTP {status}; body was not opened"
            ) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise HttpRangeTransportError(
                f"archive size Range probe transport unavailable: {exc}"
            ) from exc

        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_host = self._validated_final_host(response.geturl())
            content_range = headers.get("content-range")
            row = HttpTransportLedgerRow(
                role="archive_size_range_probe",
                method="GET",
                start=0,
                end=0,
                status=status,
                final_host=final_host,
                content_range=content_range,
                content_length=headers.get("content-length"),
                bytes_opened=0,
            )
            if status != 206:
                self.ledger.append(row)
                raise HttpRangeTransportError(
                    f"archive size Range probe returned HTTP {status}; body was not opened"
                )
            match = re.fullmatch(r"bytes 0-0/([1-9][0-9]*)", content_range or "")
            if match is None:
                self.ledger.append(row)
                raise HttpRangeTransportError(
                    "archive size Range probe lacked exact Content-Range bytes 0-0/<size>"
                )
            if headers.get("content-encoding", "identity").casefold() != "identity":
                self.ledger.append(row)
                raise HttpRangeTransportError(
                    "archive size Range probe unexpectedly applied content encoding"
                )
            body = response.read(2)
            self.ledger.append(
                HttpTransportLedgerRow(
                    role=row.role,
                    method=row.method,
                    start=row.start,
                    end=row.end,
                    status=row.status,
                    final_host=row.final_host,
                    content_range=row.content_range,
                    content_length=row.content_length,
                    bytes_opened=len(body),
                )
            )

        if len(body) != 1:
            raise HttpRangeTransportError(
                f"archive size Range probe opened {len(body)} bytes instead of one"
            )
        return self.bind_frozen_size(int(match.group(1)))

    def read_range(self, start: int, end: int, role: str) -> bytes:
        """Read one exact inclusive range after archive size has been bound."""

        if self.archive_size is None:
            raise RuntimeError("archive size must be bound before range reads")
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end < start
            or end >= self.archive_size
        ):
            raise ValueError(f"invalid bounded range {start}-{end}")

        request = urllib.request.Request(
            self.url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
        )
        try:
            response = self.opener.open(request, timeout=90)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
            self.ledger.append(
                HttpTransportLedgerRow(
                    role=str(role),
                    method="GET",
                    start=start,
                    end=end,
                    status=status,
                    final_host=None,
                    content_range=None,
                    content_length=None,
                    bytes_opened=0,
                )
            )
            raise HttpRangeTransportError(
                f"bounded Range returned HTTP {status}; body was not opened"
            ) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise HttpRangeTransportError(
                f"bounded Range transport unavailable: {exc}"
            ) from exc

        expected = end - start + 1
        with response:
            status = int(getattr(response, "status", response.getcode()))
            headers = {key.lower(): value for key, value in response.headers.items()}
            final_host = self._validated_final_host(response.geturl())
            content_range = headers.get("content-range")
            base = HttpTransportLedgerRow(
                role=str(role),
                method="GET",
                start=start,
                end=end,
                status=status,
                final_host=final_host,
                content_range=content_range,
                content_length=headers.get("content-length"),
                bytes_opened=0,
            )
            if status != 206:
                self.ledger.append(base)
                raise HttpRangeTransportError(
                    f"bounded Range returned HTTP {status}; body was not opened"
                )
            expected_content_range = f"bytes {start}-{end}/{self.archive_size}"
            if content_range != expected_content_range:
                self.ledger.append(base)
                raise HttpRangeTransportError(
                    "bounded Range Content-Range differs from frozen archive size"
                )
            if headers.get("content-encoding", "identity").casefold() != "identity":
                self.ledger.append(base)
                raise HttpRangeTransportError(
                    "bounded Range unexpectedly applied content encoding"
                )
            body = response.read(expected + 1)
            self.ledger.append(
                HttpTransportLedgerRow(
                    role=base.role,
                    method=base.method,
                    start=base.start,
                    end=base.end,
                    status=base.status,
                    final_host=base.final_host,
                    content_range=base.content_range,
                    content_length=base.content_length,
                    bytes_opened=len(body),
                )
            )

        if len(body) != expected:
            raise HttpRangeTransportError(
                f"bounded Range opened {len(body)} bytes instead of {expected}"
            )
        return body
