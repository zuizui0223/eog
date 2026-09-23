"""Metadata-only discovery gate that must pass before prospective source content opens.

This composes the discovery firewall with a frozen declaration of which source roles are
required. It prevents a search workflow from treating a merely safe-looking file as
sufficient when the full response-independent registry/effort set has not yet been
identified.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from eog.v2.source_discovery_firewall import (
    DiscoveryClassification,
    SourceDescriptor,
    classify_discovery_batch,
)


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
class DiscoveryRoleRequirement:
    role: str
    minimum_sources: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("role must be non-empty str")
        if (
            isinstance(self.minimum_sources, bool)
            or not isinstance(self.minimum_sources, int)
            or self.minimum_sources < 1
        ):
            raise ValueError("minimum_sources must be a positive integer")


@dataclass(frozen=True)
class DiscoverySource:
    descriptor: SourceDescriptor
    role: str

    def __post_init__(self) -> None:
        if not isinstance(self.descriptor, SourceDescriptor):
            raise TypeError("descriptor must be SourceDescriptor")
        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("role must be non-empty str")


@dataclass(frozen=True)
class DiscoveryGateResult:
    ready_for_safe_content_open: bool
    status: str
    missing_roles: tuple[str, ...]
    safe_source_ids: tuple[str, ...]
    blocked_source_ids: tuple[str, ...]
    classifications: tuple[DiscoveryClassification, ...]
    fingerprint: str


def evaluate_discovery_gate(
    sources: Sequence[DiscoverySource],
    requirements: Sequence[DiscoveryRoleRequirement],
) -> DiscoveryGateResult:
    values = tuple(sources)
    required = tuple(requirements)
    if not required:
        raise ValueError("at least one discovery role requirement is required")

    source_ids = [item.descriptor.source_id for item in values]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("discovery source IDs must be unique")

    roles = [item.role for item in required]
    if len(roles) != len(set(roles)):
        raise ValueError("discovery role requirements must be unique")

    classifications = classify_discovery_batch(
        tuple(item.descriptor for item in values)
    )
    by_id: Mapping[str, DiscoveryClassification] = {
        item.source_id: item for item in classifications
    }

    safe_by_role: dict[str, list[str]] = {}
    blocked: list[str] = []
    for source in values:
        classification = by_id[source.descriptor.source_id]
        if classification.content_open_allowed:
            safe_by_role.setdefault(source.role, []).append(
                source.descriptor.source_id
            )
        else:
            blocked.append(source.descriptor.source_id)

    missing = []
    for requirement in required:
        observed = len(safe_by_role.get(requirement.role, ()))
        if observed < requirement.minimum_sources:
            missing.append(requirement.role)

    safe_ids = tuple(
        sorted(
            source_id
            for source_ids_for_role in safe_by_role.values()
            for source_id in source_ids_for_role
        )
    )
    blocked_ids = tuple(sorted(blocked))
    missing_roles = tuple(sorted(missing))

    if missing_roles:
        ready = False
        status = "stop_required_safe_source_roles_unresolved"
    else:
        ready = True
        status = "ready_for_declared_safe_content_open"

    payload = {
        "status": status,
        "ready_for_safe_content_open": ready,
        "missing_roles": list(missing_roles),
        "safe_source_ids": list(safe_ids),
        "blocked_source_ids": list(blocked_ids),
        "classifications": [
            {
                "source_id": item.source_id,
                "classification": item.classification,
                "content_open_allowed": item.content_open_allowed,
                "fingerprint": item.fingerprint,
            }
            for item in classifications
        ],
    }
    return DiscoveryGateResult(
        ready_for_safe_content_open=ready,
        status=status,
        missing_roles=missing_roles,
        safe_source_ids=safe_ids,
        blocked_source_ids=blocked_ids,
        classifications=classifications,
        fingerprint=_sha256(payload),
    )
