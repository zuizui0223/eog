"""Response-blind source transport qualification for prospective EOG-WF candidates.

This module separates transport capability from scientific source identity.

A candidate should not become the active fresh real-system attempt merely because a
public landing page or archive URL exists. Before candidate lock, the validation
programme should establish at least one prospectively declared route that can reach the
response-independent registry/effort inputs while keeping focal biological response
payload bytes at zero.

The route can be HTTP Range inventory, physically separate safe assets, a published
member inventory, or another predeclared response-blind mechanism. The specific HTTP
status code is not itself a scientific requirement here. What matters is whether the
declared route actually provides the safe inputs without opening response payload bytes.

This is qualification infrastructure, not a downloader and not an ecological operator.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Sequence


TransportRouteType = Literal[
    "separate_safe_assets",
    "mixed_archive_bounded_inventory",
    "published_member_inventory",
    "other_response_blind_route",
]

TransportQualificationStatus = Literal[
    "ready_for_candidate_lock",
    "incomplete_transport_evidence",
    "stop_response_opened_during_transport_qualification",
    "stop_no_response_blind_transport_route",
]


_ALLOWED_ROUTE_TYPES = {
    "separate_safe_assets",
    "mixed_archive_bounded_inventory",
    "published_member_inventory",
    "other_response_blind_route",
}


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    result = value.strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be int")
    if value < 0:
        raise ValueError(f"{label} must be >= 0")
    return value


@dataclass(frozen=True)
class TransportRouteEvidence:
    """One prospectively declared response-blind acquisition route.

    qualified means the route has actually been exercised far enough to prove that
    the required safe registry/effort material is reachable under the declared firewall.
    It does not mean that focal response is reachable or that any predictive model is
    estimable.

    A route that merely has a URL but has not been exercised is qualified=False and
    should carry a reason such as not_yet_exercised.
    """

    route_id: str
    route_type: TransportRouteType
    qualified: bool
    safe_payload_bytes_opened: int
    response_payload_bytes_opened: int
    reason: str
    transport_detail: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "route_id",
            _required_text(self.route_id, "route_id"),
        )
        if self.route_type not in _ALLOWED_ROUTE_TYPES:
            raise ValueError(f"unsupported route_type: {self.route_type!r}")
        _require_bool(self.qualified, "qualified")
        object.__setattr__(
            self,
            "safe_payload_bytes_opened",
            _require_nonnegative_int(
                self.safe_payload_bytes_opened,
                "safe_payload_bytes_opened",
            ),
        )
        object.__setattr__(
            self,
            "response_payload_bytes_opened",
            _require_nonnegative_int(
                self.response_payload_bytes_opened,
                "response_payload_bytes_opened",
            ),
        )
        object.__setattr__(
            self,
            "reason",
            _required_text(self.reason, "reason"),
        )
        if not isinstance(self.transport_detail, str):
            raise TypeError("transport_detail must be str")

        if self.qualified and self.response_payload_bytes_opened != 0:
            raise ValueError(
                "a qualified response-blind route cannot have opened response payload bytes"
            )

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "route_id": self.route_id,
                "route_type": self.route_type,
                "qualified": self.qualified,
                "safe_payload_bytes_opened": self.safe_payload_bytes_opened,
                "response_payload_bytes_opened": self.response_payload_bytes_opened,
                "reason": self.reason,
                "transport_detail": self.transport_detail,
            }
        )


@dataclass(frozen=True)
class SourceTransportQualification:
    status: TransportQualificationStatus
    ready: bool
    qualified_route_ids: tuple[str, ...]
    attempted_route_ids: tuple[str, ...]
    response_payload_bytes_opened: int
    reason: str
    route_fingerprints: tuple[tuple[str, str], ...]
    fingerprint: str


def evaluate_source_transport_qualification(
    routes: Sequence[TransportRouteEvidence],
) -> SourceTransportQualification:
    """Evaluate pre-candidate-lock transport readiness.

    This function deliberately does not rank routes or infer fallback order. If a future
    protocol wants to exercise multiple routes, that set and order must be declared
    upstream before the candidate is locked. Here we only evaluate the resulting
    response-blind evidence.

    A route failure such as HTTP 200 instead of 206 is not automatically a scientific
    STOP. It simply means that particular route is unqualified. The candidate is
    transport-ready if another prospectively declared response-blind route is already
    qualified.
    """

    values = tuple(routes)
    if not values:
        status: TransportQualificationStatus = "incomplete_transport_evidence"
        ready = False
        qualified_ids: tuple[str, ...] = ()
        attempted_ids: tuple[str, ...] = ()
        response_bytes = 0
        reason = (
            "no response-blind transport route has been declared and exercised; "
            "do not lock the fresh candidate"
        )
        route_fingerprints: tuple[tuple[str, str], ...] = ()
    else:
        if any(not isinstance(route, TransportRouteEvidence) for route in values):
            raise TypeError("routes must contain TransportRouteEvidence values")

        ids = [route.route_id for route in values]
        if len(ids) != len(set(ids)):
            raise ValueError("transport route IDs must be unique")

        ordered = tuple(sorted(values, key=lambda route: route.route_id))
        route_fingerprints = tuple(
            (route.route_id, route.fingerprint) for route in ordered
        )
        response_bytes = sum(route.response_payload_bytes_opened for route in ordered)
        attempted_ids = tuple(route.route_id for route in ordered)
        qualified_ids = tuple(
            route.route_id for route in ordered if route.qualified
        )

        if response_bytes > 0:
            status = "stop_response_opened_during_transport_qualification"
            ready = False
            reason = (
                "transport qualification opened biological response payload bytes; "
                "the candidate is no longer response-blind"
            )
        elif qualified_ids:
            status = "ready_for_candidate_lock"
            ready = True
            reason = (
                "at least one prospectively declared route reached the required "
                "response-independent inputs while response payload bytes remained zero"
            )
        else:
            status = "stop_no_response_blind_transport_route"
            ready = False
            reason = (
                "all declared transport routes failed before the required safe inputs "
                "were qualified; reject the candidate before scientific attempt lock"
            )

    payload = {
        "status": status,
        "ready": ready,
        "qualified_route_ids": list(qualified_ids),
        "attempted_route_ids": list(attempted_ids),
        "response_payload_bytes_opened": response_bytes,
        "reason": reason,
        "route_fingerprints": [list(value) for value in route_fingerprints],
    }
    return SourceTransportQualification(
        status=status,
        ready=ready,
        qualified_route_ids=qualified_ids,
        attempted_route_ids=attempted_ids,
        response_payload_bytes_opened=response_bytes,
        reason=reason,
        route_fingerprints=route_fingerprints,
        fingerprint=_canonical_sha256(payload),
    )
