"""Response-blind preflight for fresh empirical EOG validation candidates.

This module is validation infrastructure, not an ecological operator. It consolidates
metadata-level checks that should happen before candidate-specific geometry workflows or
row-level outcome access. Candidate-specific sample-size minima remain explicit inputs;
EOG does not embed universal ecological cutoffs here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal


CandidatePreflightStatus = Literal[
    "ready_for_geometry_gate",
    "incomplete_response_blind_metadata",
    "stop_response_already_opened",
    "stop_inseparable_geometry_response",
    "stop_no_response_independent_coordinate_geometry",
    "stop_analysis_registry_not_closed",
    "stop_insufficient_nodes",
    "stop_insufficient_outer_units",
    "stop_insufficient_repeated_nodes",
]

LayoutDesign = Literal[
    "unknown",
    "natural_irregular",
    "regular_grid",
    "linear_transect",
    "other",
]

_ALLOWED_LAYOUTS = {
    "unknown",
    "natural_irregular",
    "regular_grid",
    "linear_transect",
    "other",
}


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _clean_required(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be str")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{label} must be non-empty")
    return cleaned


def _clean_optional(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _clean_required(value, label)


def _require_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} must be bool")
    return value


def _optional_bool(value: object, label: str) -> bool | None:
    if value is None:
        return None
    return _require_bool(value, label)


def _require_nonnegative_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be int")
    if value < 0:
        raise ValueError(f"{label} must be >= 0")
    return value


def _optional_nonnegative_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _require_nonnegative_int(value, label)


@dataclass(frozen=True)
class CandidatePreflightDeclaration:
    """Prospectively declared metadata-level eligibility minima for one attempt."""

    attempt_id: str
    minimum_nodes: int
    minimum_outer_units: int
    minimum_repeated_nodes: int
    require_separate_geometry_and_response: bool = True
    require_coordinate_geometry: bool = True
    require_closed_analysis_registry: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "attempt_id", _clean_required(self.attempt_id, "attempt_id"))
        object.__setattr__(
            self,
            "minimum_nodes",
            _require_nonnegative_int(self.minimum_nodes, "minimum_nodes"),
        )
        object.__setattr__(
            self,
            "minimum_outer_units",
            _require_nonnegative_int(self.minimum_outer_units, "minimum_outer_units"),
        )
        object.__setattr__(
            self,
            "minimum_repeated_nodes",
            _require_nonnegative_int(self.minimum_repeated_nodes, "minimum_repeated_nodes"),
        )
        _require_bool(
            self.require_separate_geometry_and_response,
            "require_separate_geometry_and_response",
        )
        _require_bool(self.require_coordinate_geometry, "require_coordinate_geometry")
        _require_bool(
            self.require_closed_analysis_registry,
            "require_closed_analysis_registry",
        )

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "attempt_id": self.attempt_id,
                "minimum_nodes": self.minimum_nodes,
                "minimum_outer_units": self.minimum_outer_units,
                "minimum_repeated_nodes": self.minimum_repeated_nodes,
                "require_separate_geometry_and_response": self.require_separate_geometry_and_response,
                "require_coordinate_geometry": self.require_coordinate_geometry,
                "require_closed_analysis_registry": self.require_closed_analysis_registry,
            }
        )


@dataclass(frozen=True)
class CandidatePreflightEvidence:
    """Response-blind metadata evidence available before the geometry gate.

    ``None`` means genuinely unresolved from metadata and produces an incomplete result,
    not an inferred pass. File/member identities should be precise enough to audit later.

    ``analysis_registry_closed`` means response-blind metadata already establishes a
    one-to-one registry for the intended analysis nodes, either directly or through a
    deterministic filtering/centroid rule declared from external metadata before the
    candidate geometry is opened. A generic source-wide location catalogue is not a
    closed analysis registry merely because it is physically separate from response.
    """

    source_identity: str
    geometry_source_identity: str | None
    response_source_identity: str | None
    geometry_response_separable: bool | None
    coordinate_geometry_present: bool | None
    node_count: int | None
    outer_unit_count: int | None
    repeated_node_count: int | None
    layout_design: LayoutDesign = "unknown"
    analysis_registry_closed: bool | None = None
    response_rows_opened: bool = False
    response_bytes_opened: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_identity", _clean_required(self.source_identity, "source_identity")
        )
        object.__setattr__(
            self,
            "geometry_source_identity",
            _clean_optional(self.geometry_source_identity, "geometry_source_identity"),
        )
        object.__setattr__(
            self,
            "response_source_identity",
            _clean_optional(self.response_source_identity, "response_source_identity"),
        )
        object.__setattr__(
            self,
            "geometry_response_separable",
            _optional_bool(self.geometry_response_separable, "geometry_response_separable"),
        )
        object.__setattr__(
            self,
            "coordinate_geometry_present",
            _optional_bool(self.coordinate_geometry_present, "coordinate_geometry_present"),
        )
        object.__setattr__(
            self, "node_count", _optional_nonnegative_int(self.node_count, "node_count")
        )
        object.__setattr__(
            self,
            "outer_unit_count",
            _optional_nonnegative_int(self.outer_unit_count, "outer_unit_count"),
        )
        object.__setattr__(
            self,
            "repeated_node_count",
            _optional_nonnegative_int(self.repeated_node_count, "repeated_node_count"),
        )
        if not isinstance(self.layout_design, str) or self.layout_design not in _ALLOWED_LAYOUTS:
            raise ValueError(f"unsupported layout_design: {self.layout_design!r}")
        object.__setattr__(
            self,
            "analysis_registry_closed",
            _optional_bool(self.analysis_registry_closed, "analysis_registry_closed"),
        )
        _require_bool(self.response_rows_opened, "response_rows_opened")
        _require_bool(self.response_bytes_opened, "response_bytes_opened")
        if not isinstance(self.note, str):
            raise TypeError("note must be str")

        if (
            self.geometry_response_separable is True
            and self.geometry_source_identity is not None
            and self.response_source_identity is not None
            and self.geometry_source_identity == self.response_source_identity
        ):
            raise ValueError(
                "geometry_response_separable=True contradicts identical geometry/response identities"
            )
        if (
            self.node_count is not None
            and self.repeated_node_count is not None
            and self.repeated_node_count > self.node_count
        ):
            raise ValueError("repeated_node_count must not exceed node_count")

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "source_identity": self.source_identity,
                "geometry_source_identity": self.geometry_source_identity,
                "response_source_identity": self.response_source_identity,
                "geometry_response_separable": self.geometry_response_separable,
                "coordinate_geometry_present": self.coordinate_geometry_present,
                "node_count": self.node_count,
                "outer_unit_count": self.outer_unit_count,
                "repeated_node_count": self.repeated_node_count,
                "layout_design": self.layout_design,
                "analysis_registry_closed": self.analysis_registry_closed,
                "response_rows_opened": self.response_rows_opened,
                "response_bytes_opened": self.response_bytes_opened,
                "note": self.note,
            }
        )


@dataclass(frozen=True)
class CandidatePreflightResult:
    status: CandidatePreflightStatus
    ready: bool
    missing_metadata: tuple[str, ...]
    warnings: tuple[str, ...]
    declaration_fingerprint: str
    evidence_fingerprint: str
    reason: str
    fingerprint: str


def evaluate_candidate_preflight(
    declaration: CandidatePreflightDeclaration,
    evidence: CandidatePreflightEvidence,
) -> CandidatePreflightResult:
    """Evaluate metadata-level candidate eligibility without inspecting outcome rows."""

    if not isinstance(declaration, CandidatePreflightDeclaration):
        raise TypeError("declaration must be CandidatePreflightDeclaration")
    if not isinstance(evidence, CandidatePreflightEvidence):
        raise TypeError("evidence must be CandidatePreflightEvidence")

    missing: list[str] = []
    if evidence.geometry_source_identity is None:
        missing.append("geometry_source_identity")
    if evidence.response_source_identity is None:
        missing.append("response_source_identity")
    if (
        declaration.require_separate_geometry_and_response
        and evidence.geometry_response_separable is None
    ):
        missing.append("geometry_response_separable")
    if declaration.require_coordinate_geometry and evidence.coordinate_geometry_present is None:
        missing.append("coordinate_geometry_present")
    if declaration.require_closed_analysis_registry and evidence.analysis_registry_closed is None:
        missing.append("analysis_registry_closed")
    if evidence.node_count is None:
        missing.append("node_count")
    if evidence.outer_unit_count is None:
        missing.append("outer_unit_count")
    if evidence.repeated_node_count is None:
        missing.append("repeated_node_count")

    warnings: list[str] = []
    if evidence.layout_design == "regular_grid":
        warnings.append("regular_grid_structural_scale_collapse_risk")
    elif evidence.layout_design == "linear_transect":
        warnings.append("linear_layout_requires_geometry_gate_for_scale_diversity")

    if evidence.response_rows_opened or evidence.response_bytes_opened:
        status: CandidatePreflightStatus = "stop_response_already_opened"
        reason = "candidate preflight must be completed before row-level or byte-level response access"
    elif (
        declaration.require_separate_geometry_and_response
        and evidence.geometry_response_separable is False
    ):
        status = "stop_inseparable_geometry_response"
        reason = "response-independent geometry cannot be physically separated from response content"
    elif declaration.require_coordinate_geometry and evidence.coordinate_geometry_present is False:
        status = "stop_no_response_independent_coordinate_geometry"
        reason = "metadata shows no response-independent coordinate geometry for the declared node universe"
    elif declaration.require_closed_analysis_registry and evidence.analysis_registry_closed is False:
        status = "stop_analysis_registry_not_closed"
        reason = (
            "response-blind metadata shows that the available geometry registry is not already "
            "closed one-to-one on the intended analysis nodes under a prospectively declared rule"
        )
    elif evidence.node_count is not None and evidence.node_count < declaration.minimum_nodes:
        status = "stop_insufficient_nodes"
        reason = "known response-blind node count is below the prospectively declared minimum"
    elif (
        evidence.outer_unit_count is not None
        and evidence.outer_unit_count < declaration.minimum_outer_units
    ):
        status = "stop_insufficient_outer_units"
        reason = "known response-blind outer-unit count is below the prospectively declared minimum"
    elif (
        evidence.repeated_node_count is not None
        and evidence.repeated_node_count < declaration.minimum_repeated_nodes
    ):
        status = "stop_insufficient_repeated_nodes"
        reason = "known response-blind repeated-node count is below the prospectively declared minimum"
    elif missing:
        status = "incomplete_response_blind_metadata"
        reason = (
            "metadata is insufficient for a fail-closed candidate decision; "
            "do not open response to fill the gaps"
        )
    else:
        status = "ready_for_geometry_gate"
        reason = (
            "response-blind metadata passes the declared preflight; "
            "structural geometry still requires its own frozen gate"
        )

    ready = status == "ready_for_geometry_gate"
    payload = {
        "status": status,
        "ready": ready,
        "missing_metadata": missing,
        "warnings": warnings,
        "declaration_fingerprint": declaration.fingerprint,
        "evidence_fingerprint": evidence.fingerprint,
        "reason": reason,
    }
    return CandidatePreflightResult(
        status=status,
        ready=ready,
        missing_metadata=tuple(missing),
        warnings=tuple(warnings),
        declaration_fingerprint=declaration.fingerprint,
        evidence_fingerprint=evidence.fingerprint,
        reason=reason,
        fingerprint=_canonical_sha256(payload),
    )
