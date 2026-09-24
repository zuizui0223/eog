"""Body-free transport qualification for a prospectively frozen response payload.

This gate is intentionally separate from safe-source transport qualification. A fresh
candidate may have already passed registry/effort/source qualification while the future
biological-response payload remains unopened.

Qualification is HEAD-only: no response payload bytes may be consumed. HTTP mechanics
are recorded as route evidence rather than ecological evidence. Multiple routes may be
declared prospectively; at least one route must be reachable before a once-only response
payload authorization can be created.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence
from urllib.parse import urlparse


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ResponseTransportRouteEvidence:
    route_id: str
    url: str
    expected_size: int
    status: int | None
    final_url: str | None
    content_length: int | None
    payload_bytes_opened: int
    error: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.route_id, str) or not self.route_id.strip():
            raise ValueError("route_id must be non-empty str")
        parsed = urlparse(self.url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("response route URL must be HTTPS")
        if (
            isinstance(self.expected_size, bool)
            or not isinstance(self.expected_size, int)
            or self.expected_size <= 0
        ):
            raise ValueError("expected_size must be positive int")
        if self.status is not None and (
            isinstance(self.status, bool) or not isinstance(self.status, int)
        ):
            raise TypeError("status must be int or None")
        if self.content_length is not None and (
            isinstance(self.content_length, bool)
            or not isinstance(self.content_length, int)
            or self.content_length < 0
        ):
            raise ValueError("content_length must be non-negative int or None")
        if (
            isinstance(self.payload_bytes_opened, bool)
            or not isinstance(self.payload_bytes_opened, int)
            or self.payload_bytes_opened < 0
        ):
            raise ValueError("payload_bytes_opened must be non-negative int")
        if self.final_url is not None:
            final = urlparse(self.final_url)
            if final.scheme != "https" or not final.hostname:
                raise ValueError("final_url must remain HTTPS")

    @property
    def qualified(self) -> bool:
        if self.payload_bytes_opened != 0:
            return False
        if self.error is not None:
            return False
        if self.status is None or not (200 <= self.status < 400):
            return False
        if (
            self.content_length is not None
            and self.content_length != self.expected_size
        ):
            return False
        return self.final_url is not None

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "route_id": self.route_id,
                "url": self.url,
                "expected_size": self.expected_size,
                "status": self.status,
                "final_url": self.final_url,
                "content_length": self.content_length,
                "payload_bytes_opened": self.payload_bytes_opened,
                "error": self.error,
                "qualified": self.qualified,
            }
        )


@dataclass(frozen=True)
class ResponseTransportQualification:
    status: str
    ready: bool
    qualified_route_ids: tuple[str, ...]
    attempted_route_ids: tuple[str, ...]
    response_payload_bytes_opened: int
    reason: str
    route_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


def evaluate_response_transport(
    routes: Sequence[ResponseTransportRouteEvidence],
) -> ResponseTransportQualification:
    values = tuple(routes)
    if not values:
        raise ValueError("at least one response transport route is required")
    ids = [route.route_id for route in values]
    if len(ids) != len(set(ids)):
        raise ValueError("response transport route IDs must be unique")

    ordered = tuple(sorted(values, key=lambda route: route.route_id))
    opened = sum(route.payload_bytes_opened for route in ordered)
    qualified = tuple(route.route_id for route in ordered if route.qualified)
    route_fingerprints = tuple(
        (route.route_id, route.fingerprint) for route in ordered
    )

    if opened > 0:
        status = "stop_response_payload_opened_during_transport_preflight"
        ready = False
        reason = (
            "response transport preflight consumed payload bytes; the route is no longer "
            "a body-free qualification"
        )
    elif qualified:
        status = "response_transport_ready"
        ready = True
        reason = (
            "at least one prospectively declared HTTPS response route completed a "
            "body-free HEAD qualification without contradicting the frozen payload size"
        )
    else:
        status = "stop_no_qualified_response_transport"
        ready = False
        reason = (
            "no prospectively declared response route completed body-free transport "
            "qualification; do not authorize response payload access"
        )

    payload = {
        "status": status,
        "ready": ready,
        "qualified_route_ids": list(qualified),
        "attempted_route_ids": [route.route_id for route in ordered],
        "response_payload_bytes_opened": opened,
        "reason": reason,
        "route_fingerprints": [list(value) for value in route_fingerprints],
    }
    return ResponseTransportQualification(
        status=status,
        ready=ready,
        qualified_route_ids=qualified,
        attempted_route_ids=tuple(route.route_id for route in ordered),
        response_payload_bytes_opened=opened,
        reason=reason,
        route_fingerprints=route_fingerprints,
        fingerprint=_sha256(payload),
    )
