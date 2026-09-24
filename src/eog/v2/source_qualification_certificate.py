"""Joined pre-lock source qualification certificate for EOG-WF v2.

The certificate composes the already-separated discovery, raw-identity, transport and
candidate-preflight layers. It does not fetch content or infer missing evidence.

Its purpose is operational: a future real-system workflow should need one machine-readable
decision before candidate lock rather than manually checking several independent gates.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from eog.v2.candidate_preflight import CandidatePreflightResult
from eog.v2.source_discovery_gate import DiscoveryGateResult
from eog.v2.source_transport_preflight import SourceTransportQualification


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
class SourceQualificationCertificate:
    status: str
    candidate_lock_allowed: bool
    discovery_fingerprint: str
    source_identity_fingerprints: tuple[tuple[str, str], ...]
    transport_fingerprint: str
    candidate_preflight_fingerprint: str
    blocking_layer: str | None
    reason: str
    fingerprint: str


def freeze_source_qualification_certificate(
    *,
    discovery: DiscoveryGateResult,
    source_identity_fingerprints: Mapping[str, str],
    transport: SourceTransportQualification,
    candidate_preflight: CandidatePreflightResult,
) -> SourceQualificationCertificate:
    """Join pre-lock evidence without weakening any upstream gate."""

    if not isinstance(discovery, DiscoveryGateResult):
        raise TypeError("discovery must be DiscoveryGateResult")
    if not isinstance(transport, SourceTransportQualification):
        raise TypeError("transport must be SourceTransportQualification")
    if not isinstance(candidate_preflight, CandidatePreflightResult):
        raise TypeError("candidate_preflight must be CandidatePreflightResult")

    identities = tuple(
        sorted(
            (
                str(source_id).strip(),
                str(fingerprint).strip().lower(),
            )
            for source_id, fingerprint in source_identity_fingerprints.items()
        )
    )
    if discovery.ready_for_safe_content_open and not identities:
        raise ValueError("at least one source identity fingerprint is required")
    if any(not source_id for source_id, _ in identities):
        raise ValueError("source identity IDs must be non-empty")
    if len({source_id for source_id, _ in identities}) != len(identities):
        raise ValueError("source identity IDs must be unique")
    for _, fingerprint in identities:
        if len(fingerprint) != 64 or any(
            char not in "0123456789abcdef" for char in fingerprint
        ):
            raise ValueError(
                "source identity fingerprints must be 64 lowercase hex characters"
            )

    safe_source_ids = set(discovery.safe_source_ids)
    identity_ids = {source_id for source_id, _ in identities}
    extra_identity = identity_ids - safe_source_ids
    if extra_identity:
        raise ValueError(
            "raw identity fingerprints were supplied for sources not authorized as safe "
            f"by discovery: {sorted(extra_identity)!r}"
        )
    missing_identity = safe_source_ids - identity_ids
    if missing_identity:
        raise ValueError(
            "safe discovery sources are missing raw identity fingerprints: "
            f"{sorted(missing_identity)!r}"
        )

    if not discovery.ready_for_safe_content_open:
        status = "stop_discovery"
        allowed = False
        blocking = "discovery"
        reason = discovery.status
    elif not transport.ready:
        status = "stop_transport"
        allowed = False
        blocking = "transport"
        reason = transport.status
    elif not candidate_preflight.ready:
        status = "stop_candidate_preflight"
        allowed = False
        blocking = "candidate_preflight"
        reason = candidate_preflight.status
    else:
        status = "ready_for_candidate_lock"
        allowed = True
        blocking = None
        reason = (
            "required safe sources are resolved, raw identities are bound, "
            "response-blind transport is qualified, and candidate preflight is ready"
        )

    payload = {
        "status": status,
        "candidate_lock_allowed": allowed,
        "discovery_fingerprint": discovery.fingerprint,
        "source_identity_fingerprints": [list(value) for value in identities],
        "transport_fingerprint": transport.fingerprint,
        "candidate_preflight_fingerprint": candidate_preflight.fingerprint,
        "blocking_layer": blocking,
        "reason": reason,
    }
    return SourceQualificationCertificate(
        status=status,
        candidate_lock_allowed=allowed,
        discovery_fingerprint=discovery.fingerprint,
        source_identity_fingerprints=identities,
        transport_fingerprint=transport.fingerprint,
        candidate_preflight_fingerprint=candidate_preflight.fingerprint,
        blocking_layer=blocking,
        reason=reason,
        fingerprint=_sha256(payload),
    )
