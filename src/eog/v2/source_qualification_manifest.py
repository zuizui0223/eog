"""Declarative compiler for the EOG-WF v2 pre-lock source qualification certificate.

This surface intentionally consumes *already frozen evidence*. It does not discover
files, fetch URLs, inspect response content, or infer missing policies.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Mapping

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.source_discovery_firewall import SourceDescriptor
from eog.v2.source_discovery_gate import (
    DiscoveryRoleRequirement,
    DiscoverySource,
    evaluate_discovery_gate,
)
from eog.v2.source_qualification_certificate import (
    freeze_source_qualification_certificate,
)
from eog.v2.source_transport_preflight import (
    TransportRouteEvidence,
    evaluate_source_transport_qualification,
)


SCHEMA = "eog.source_qualification_manifest.v1"


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    return value


def _sequence(value: object, label: str):
    if isinstance(value, (str, bytes)) or not isinstance(value, list):
        raise TypeError(f"{label} must be a JSON array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty str")
    return value.strip()


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be JSON boolean")
    return value


def compile_source_qualification_manifest(
    manifest: Mapping[str, object],
) -> dict[str, object]:
    if manifest.get("schema") != SCHEMA:
        raise ValueError(f"manifest schema must be {SCHEMA!r}")

    discovery_raw = _mapping(manifest.get("discovery"), "discovery")
    sources = []
    for index, raw in enumerate(
        _sequence(discovery_raw.get("sources"), "discovery.sources")
    ):
        row = _mapping(raw, f"discovery source {index}")
        sources.append(
            DiscoverySource(
                SourceDescriptor(
                    source_id=_text(row.get("source_id"), "source_id"),
                    path_or_name=_text(row.get("path_or_name"), "path_or_name"),
                    declared_schema_fields=tuple(
                        _text(value, "declared schema field")
                        for value in _sequence(
                            row.get("declared_schema_fields", []),
                            "declared_schema_fields",
                        )
                    ),
                    metadata_note=str(row.get("metadata_note", "")),
                ),
                role=_text(row.get("role"), "source role"),
            )
        )
    requirements = tuple(
        DiscoveryRoleRequirement(
            role=_text(row.get("role"), "requirement role"),
            minimum_sources=int(row.get("minimum_sources", 1)),
        )
        for row in (
            _mapping(raw, "discovery requirement")
            for raw in _sequence(
                discovery_raw.get("requirements"),
                "discovery.requirements",
            )
        )
    )
    discovery = evaluate_discovery_gate(tuple(sources), requirements)

    identity_raw = _mapping(
        manifest.get("source_identity_fingerprints", {}),
        "source_identity_fingerprints",
    )
    identities = {
        _text(source_id, "identity source_id"): _text(
            fingerprint, "identity fingerprint"
        )
        for source_id, fingerprint in identity_raw.items()
    }

    transport_raw = _mapping(manifest.get("transport"), "transport")
    routes = []
    for index, raw in enumerate(
        _sequence(transport_raw.get("routes"), "transport.routes")
    ):
        row = _mapping(raw, f"transport route {index}")
        routes.append(
            TransportRouteEvidence(
                route_id=_text(row.get("route_id"), "route_id"),
                route_type=str(row.get("route_type")),
                qualified=_boolean(row.get("qualified"), "qualified"),
                safe_payload_bytes_opened=int(
                    row.get("safe_payload_bytes_opened", 0)
                ),
                response_payload_bytes_opened=int(
                    row.get("response_payload_bytes_opened", 0)
                ),
                reason=_text(row.get("reason"), "transport reason"),
                transport_detail=str(row.get("transport_detail", "")),
            )
        )
    transport = evaluate_source_transport_qualification(tuple(routes))

    preflight_raw = _mapping(
        manifest.get("candidate_preflight"),
        "candidate_preflight",
    )
    declaration_raw = _mapping(
        preflight_raw.get("declaration"),
        "candidate_preflight.declaration",
    )
    evidence_raw = _mapping(
        preflight_raw.get("evidence"),
        "candidate_preflight.evidence",
    )
    declaration = CandidatePreflightDeclaration(
        attempt_id=_text(declaration_raw.get("attempt_id"), "attempt_id"),
        minimum_nodes=int(declaration_raw.get("minimum_nodes")),
        minimum_outer_units=int(declaration_raw.get("minimum_outer_units")),
        minimum_repeated_nodes=int(declaration_raw.get("minimum_repeated_nodes")),
        require_separate_geometry_and_response=_boolean(
            declaration_raw.get("require_separate_geometry_and_response", True),
            "require_separate_geometry_and_response",
        ),
        require_coordinate_geometry=_boolean(
            declaration_raw.get("require_coordinate_geometry", True),
            "require_coordinate_geometry",
        ),
        require_closed_analysis_registry=_boolean(
            declaration_raw.get("require_closed_analysis_registry", False),
            "require_closed_analysis_registry",
        ),
        require_response_blind_transport_qualification=_boolean(
            declaration_raw.get(
                "require_response_blind_transport_qualification",
                True,
            ),
            "require_response_blind_transport_qualification",
        ),
    )
    evidence = CandidatePreflightEvidence(
        source_identity=_text(evidence_raw.get("source_identity"), "source_identity"),
        geometry_source_identity=evidence_raw.get("geometry_source_identity"),
        response_source_identity=evidence_raw.get("response_source_identity"),
        geometry_response_separable=evidence_raw.get("geometry_response_separable"),
        coordinate_geometry_present=evidence_raw.get("coordinate_geometry_present"),
        node_count=evidence_raw.get("node_count"),
        outer_unit_count=evidence_raw.get("outer_unit_count"),
        repeated_node_count=evidence_raw.get("repeated_node_count"),
        layout_design=str(evidence_raw.get("layout_design", "unknown")),
        analysis_registry_closed=evidence_raw.get("analysis_registry_closed"),
        response_blind_transport_qualified=evidence_raw.get(
            "response_blind_transport_qualified"
        ),
        transport_qualification_fingerprint=evidence_raw.get(
            "transport_qualification_fingerprint"
        ),
        response_rows_opened=_boolean(
            evidence_raw.get("response_rows_opened", False),
            "response_rows_opened",
        ),
        response_bytes_opened=_boolean(
            evidence_raw.get("response_bytes_opened", False),
            "response_bytes_opened",
        ),
        note=str(evidence_raw.get("note", "")),
    )
    candidate = evaluate_candidate_preflight(declaration, evidence)

    certificate = freeze_source_qualification_certificate(
        discovery=discovery,
        source_identity_fingerprints=identities,
        transport=transport,
        candidate_preflight=candidate,
    )
    return {
        "schema": "eog.source_qualification_manifest_result.v1",
        "status": certificate.status,
        "candidate_lock_allowed": certificate.candidate_lock_allowed,
        "blocking_layer": certificate.blocking_layer,
        "reason": certificate.reason,
        "certificate": asdict(certificate),
        "layers": {
            "discovery": {
                "status": discovery.status,
                "fingerprint": discovery.fingerprint,
            },
            "transport": {
                "status": transport.status,
                "fingerprint": transport.fingerprint,
            },
            "candidate_preflight": {
                "status": candidate.status,
                "fingerprint": candidate.fingerprint,
            },
        },
    }


def compile_source_qualification_manifest_file(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return compile_source_qualification_manifest(_mapping(payload, "manifest"))
