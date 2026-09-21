"""Content-addressed pre-response provenance for generic EOG-WF v2 adapters.

The certificate joins already-existing response-independent contracts without changing
their scientific meanings. It does not authorize a predictive claim. It records whether
the normalized problem is structurally eligible for response access and, separately,
whether a declared prediction-facing state is eligible for default Layer-B use.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from eog.v2.coordinate_registry import CoordinateRegistryAudit
from eog.v2.predictive_state_gate import PredictiveStateEligibility
from eog.v2.problem_contract import NormalizedPreResponseProblem
from eog.v2.schema_adapter import FrozenSchemaResolution
from eog.v2.world_adequacy import (
    WorldUniverseStructuralGate,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
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


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


@dataclass(frozen=True)
class SourceArtifactIdentity:
    """Exact identity for one response-independent source artifact."""

    artifact_id: str
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        artifact_id = _text(self.artifact_id, "artifact_id")
        if (
            isinstance(self.byte_count, bool)
            or not isinstance(self.byte_count, int)
            or self.byte_count < 0
        ):
            raise ValueError("byte_count must be a non-negative integer")
        digest = str(self.sha256).strip().lower()
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("sha256 must be a 64-character hexadecimal digest")
        if artifact_id != self.artifact_id:
            object.__setattr__(self, "artifact_id", artifact_id)
        if digest != self.sha256:
            object.__setattr__(self, "sha256", digest)

    @classmethod
    def from_bytes(cls, artifact_id: str, content: bytes) -> "SourceArtifactIdentity":
        if not isinstance(content, bytes):
            raise TypeError("content must be bytes")
        return cls(
            artifact_id=_text(artifact_id, "artifact_id"),
            byte_count=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "artifact_id": self.artifact_id,
                "byte_count": int(self.byte_count),
                "sha256": self.sha256,
            }
        )


@dataclass(frozen=True)
class AdapterSourceProvenance:
    """Frozen source-side provenance consumed by NormalizedPreResponseProblem."""

    artifacts: tuple[SourceArtifactIdentity, ...]
    schema_resolution_fingerprint: str
    coordinate_registry_fingerprint: str
    fingerprint: str


def freeze_adapter_source_provenance(
    *,
    artifacts: Sequence[SourceArtifactIdentity],
    schema_resolution: FrozenSchemaResolution,
    coordinate_registry: CoordinateRegistryAudit,
) -> AdapterSourceProvenance:
    values = tuple(artifacts)
    if not values:
        raise ValueError("at least one response-independent source artifact is required")
    if any(not isinstance(value, SourceArtifactIdentity) for value in values):
        raise TypeError("artifacts must contain SourceArtifactIdentity values")
    ids = [artifact.artifact_id for artifact in values]
    if len(ids) != len(set(ids)):
        raise ValueError("source artifact IDs must be unique")

    ordered = tuple(sorted(values, key=lambda artifact: artifact.artifact_id))
    payload = {
        "schema": "eog.adapter_source_provenance.v1",
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "byte_count": artifact.byte_count,
                "sha256": artifact.sha256,
                "fingerprint": artifact.fingerprint,
            }
            for artifact in ordered
        ],
        "schema_resolution_fingerprint": schema_resolution.fingerprint,
        "coordinate_registry_fingerprint": coordinate_registry.fingerprint,
    }
    return AdapterSourceProvenance(
        artifacts=ordered,
        schema_resolution_fingerprint=schema_resolution.fingerprint,
        coordinate_registry_fingerprint=coordinate_registry.fingerprint,
        fingerprint=_sha256(payload),
    )


def fingerprint_world_family(
    node_ids: Sequence[str],
    world_adjacencies: Mapping[str, np.ndarray],
) -> str:
    """Fingerprint the exact declared world matrices in one frozen node order."""

    ids = tuple(_text(value, "node_id") for value in node_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("node_ids must be non-empty and unique")
    if not world_adjacencies:
        raise ValueError("world_adjacencies must not be empty")

    worlds: list[dict[str, object]] = []
    for world_id in sorted(world_adjacencies):
        name = _text(world_id, "world_id")
        matrix = np.asarray(world_adjacencies[world_id], dtype=float)
        if matrix.shape != (len(ids), len(ids)):
            raise ValueError(
                f"world {name!r} adjacency must have shape {(len(ids), len(ids))}"
            )
        if not np.isfinite(matrix).all() or np.any(matrix < 0.0):
            raise ValueError(
                f"world {name!r} adjacency must be finite and non-negative"
            )
        worlds.append(
            {
                "world_id": name,
                "adjacency": matrix.tolist(),
            }
        )

    return _sha256(
        {
            "schema": "eog.world_family_identity.v1",
            "node_ids": list(ids),
            "worlds": worlds,
        }
    )


@dataclass(frozen=True)
class PreResponseCertificate:
    """Joined pre-response certificate for one generic EOG problem."""

    node_ids: tuple[str, ...]
    source_provenance_fingerprint: str
    normalized_problem_fingerprint: str
    world_family_fingerprint: str
    structural_gate_fingerprint: str
    predictive_state_fingerprint: str | None
    structural_status: str
    predictive_status: str
    structural_response_access_allowed: bool
    predictive_outcome_access_allowed: bool
    predictive_use_allowed: bool | None
    fingerprint: str


def freeze_pre_response_certificate(
    *,
    source_provenance: AdapterSourceProvenance,
    normalized_problem: NormalizedPreResponseProblem,
    coordinate_registry: CoordinateRegistryAudit,
    structural_gate: WorldUniverseStructuralGate,
    world_adjacencies: Mapping[str, np.ndarray],
    predictive_state: PredictiveStateEligibility | None = None,
) -> PreResponseCertificate:
    """Join source, normalized-problem and gate identities without biological outcomes."""

    if not normalized_problem.response_locked:
        raise ValueError("normalized problem must remain response locked")
    if normalized_problem.source_fingerprint != source_provenance.fingerprint:
        raise ValueError(
            "normalized problem source_fingerprint must equal adapter source provenance"
        )

    if (
        coordinate_registry.fingerprint
        != source_provenance.coordinate_registry_fingerprint
    ):
        raise ValueError(
            "coordinate registry differs from the audit frozen in source provenance"
        )

    coordinate_ids = tuple(node.node_id for node in coordinate_registry.nodes)
    if set(coordinate_ids) != set(normalized_problem.node_ids):
        raise ValueError("coordinate registry node set differs from normalized problem")
    if structural_gate.audit.node_ids != normalized_problem.node_ids:
        raise ValueError(
            "structural gate node order must equal normalized problem node order"
        )

    world_family_fingerprint = fingerprint_world_family(
        normalized_problem.node_ids,
        world_adjacencies,
    )
    if world_family_fingerprint != normalized_problem.world_family_fingerprint:
        raise ValueError(
            "declared world family differs from normalized problem world_family_fingerprint"
        )
    reconstructed_audit = audit_world_universe_structure(
        normalized_problem.node_ids,
        world_adjacencies,
        horizon=structural_gate.audit.horizon,
    )
    if reconstructed_audit.fingerprint != structural_gate.audit.fingerprint:
        raise ValueError(
            "structural gate audit differs from the supplied declared world family"
        )
    reconstructed_gate = apply_structural_adequacy_gate(
        reconstructed_audit,
        structural_gate.declaration,
    )
    if reconstructed_gate != structural_gate:
        raise ValueError(
            "structural gate result differs from reapplication of its frozen declaration"
        )

    structural_status = (
        "structural_ready" if reconstructed_gate.passed else "stop_structural_adequacy"
    )
    if predictive_state is None:
        predictive_status = "not_declared"
        predictive_fingerprint = None
        predictive_allowed = None
    else:
        predictive_status = predictive_state.status
        predictive_fingerprint = predictive_state.fingerprint
        predictive_allowed = predictive_state.predictive_use_allowed

    payload = {
        "schema": "eog.pre_response_certificate.v1",
        "node_ids": list(normalized_problem.node_ids),
        "source_provenance_fingerprint": source_provenance.fingerprint,
        "normalized_problem_fingerprint": normalized_problem.fingerprint,
        "world_family_fingerprint": world_family_fingerprint,
        "coordinate_registry_fingerprint": coordinate_registry.fingerprint,
        "structural_gate_fingerprint": reconstructed_gate.fingerprint,
        "predictive_state_fingerprint": predictive_fingerprint,
        "structural_status": structural_status,
        "predictive_status": predictive_status,
        "structural_response_access_allowed": bool(reconstructed_gate.passed),
        "predictive_outcome_access_allowed": bool(
            reconstructed_gate.passed and predictive_allowed is True
        ),
        "predictive_use_allowed": predictive_allowed,
    }
    return PreResponseCertificate(
        node_ids=normalized_problem.node_ids,
        source_provenance_fingerprint=source_provenance.fingerprint,
        normalized_problem_fingerprint=normalized_problem.fingerprint,
        world_family_fingerprint=world_family_fingerprint,
        structural_gate_fingerprint=reconstructed_gate.fingerprint,
        predictive_state_fingerprint=predictive_fingerprint,
        structural_status=structural_status,
        predictive_status=predictive_status,
        structural_response_access_allowed=bool(reconstructed_gate.passed),
        predictive_outcome_access_allowed=bool(
            reconstructed_gate.passed and predictive_allowed is True
        ),
        predictive_use_allowed=predictive_allowed,
        fingerprint=_sha256(payload),
    )
