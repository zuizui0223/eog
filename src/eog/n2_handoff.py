"""Fail-closed intake for versioned ODSP N2 -> N3 payloads.

EOG does not depend on the ODSP Python package. Instead it validates the portable
payload envelope, re-checks the scientific handoff category from serialized
fields, verifies the payload fingerprint, and only then decides whether an
axis-resolved state may enter empirical N3 realization/reachability analysis.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import re
from typing import Mapping

SCHEMA_ID = "n2-to-n3-payload-v1"
PROGRAM_ID = "niche-to-survey-four-chapter-v1"
PRODUCER_REPOSITORY = "zuizui0223/odsp"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_TRANSFERABILITY = {
    "generalizing",
    "mixed",
    "non_generalizing",
    "unavailable",
    "not_tested",
}


@dataclass(frozen=True)
class N2PayloadIntake:
    """EOG-side decision about one serialized N2 handoff payload."""

    evidence_id: str
    handoff_category: str
    fingerprint_verified: bool
    projection_summary_available: bool
    accepted_for_empirical_n3: bool
    accepted_for_method_testing: bool
    state_artifact_uri: str | None
    state_artifact_sha256: str | None
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _list(value: object, *, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _text(value: object, *, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _fingerprint_core(payload: Mapping[str, object]) -> str:
    core = {key: value for key, value in payload.items() if key != "fingerprint"}
    data = json.dumps(
        core,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_axes(payload: Mapping[str, object]) -> tuple[str, ...]:
    axes = _mapping(payload.get("axes"), name="axes")
    base = _list(axes.get("base"), name="axes.base")
    added = _list(axes.get("added"), name="axes.added")
    if not base or not added:
        raise ValueError("axes.base and axes.added must each be non-empty")

    names: list[str] = []
    for collection_name, collection in (("base", base), ("added", added)):
        for item in collection:
            axis = _mapping(item, name=f"axes.{collection_name} item")
            names.append(_text(axis.get("name"), name="axis name"))
            _text(axis.get("semantic"), name="axis semantic")
    if len(names) != len(set(names)):
        raise ValueError("axis names must be unique")
    return tuple(names)


def _validate_artifact(
    artifact: Mapping[str, object],
    *,
    expected_semantics: str,
    axis_names: tuple[str, ...],
) -> tuple[str, str]:
    semantics = _text(artifact.get("artifact_semantics"), name="artifact_semantics")
    if semantics != expected_semantics:
        raise ValueError(
            f"state_artifact semantics {semantics!r} do not match {expected_semantics!r}"
        )
    uri = _text(artifact.get("uri"), name="state_artifact uri")
    sha256 = _text(artifact.get("sha256"), name="state_artifact sha256")
    if not _SHA256_RE.fullmatch(sha256):
        raise ValueError("state_artifact sha256 must be 64 lowercase hexadecimal characters")
    _text(artifact.get("media_type"), name="state_artifact media_type")
    shape = _list(artifact.get("shape"), name="state_artifact shape")
    axis_order = _list(artifact.get("axis_order"), name="state_artifact axis_order")
    if len(shape) != len(axis_names):
        raise ValueError("state_artifact shape rank must match declared axes")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in shape
    ):
        raise ValueError("state_artifact shape must contain positive integers")
    if tuple(str(value) for value in axis_order) != axis_names:
        raise ValueError("state_artifact axis_order must match declared base+added axes")
    return uri, sha256


def _validated_transferability_gains(
    transferability: Mapping[str, object],
    category: str,
) -> tuple[float, ...]:
    if category not in _ALLOWED_TRANSFERABILITY:
        raise ValueError(f"unsupported transferability category: {category!r}")
    raw = _list(transferability.get("independent_gains"), name="independent_gains")
    gains: list[float] = []
    for value in raw:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("independent_gains must contain numeric values")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("independent_gains must be finite")
        gains.append(number)

    if category == "generalizing" and gains and not all(value > 0.0 for value in gains):
        raise ValueError("generalizing transferability requires all supplied gains > 0")
    if category == "non_generalizing" and gains and not all(value <= 0.0 for value in gains):
        raise ValueError("non_generalizing transferability requires all supplied gains <= 0")
    if category == "mixed":
        if not gains or not (any(value > 0.0 for value in gains) and any(value <= 0.0 for value in gains)):
            raise ValueError("mixed transferability requires both positive and non-positive gains")
    return tuple(gains)


def inspect_n2_handoff_payload(payload: Mapping[str, object]) -> N2PayloadIntake:
    """Validate an ODSP handoff payload and classify EOG intake eligibility.

    The empirical N3 gate is intentionally redundant with ODSP: EOG re-checks
    evidence scope, support semantics, prospective freezing, estimability,
    transferability, artifact semantics and integrity rather than trusting a
    serialized boolean alone.
    """

    if payload.get("schema_id") != SCHEMA_ID:
        raise ValueError("unsupported N2 handoff schema_id")
    if payload.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected N1-N4 program_id")
    producer = _mapping(payload.get("producer"), name="producer")
    if producer.get("chapter") != "N2" or producer.get("repository") != PRODUCER_REPOSITORY:
        raise ValueError("unexpected N2 payload producer")

    evidence_id = _text(payload.get("evidence_id"), name="evidence_id")
    fingerprint = _text(payload.get("fingerprint"), name="fingerprint")
    if not _SHA256_RE.fullmatch(fingerprint):
        raise ValueError("payload fingerprint must be 64 lowercase hexadecimal characters")
    if _fingerprint_core(payload) != fingerprint:
        raise ValueError("payload fingerprint mismatch")

    axis_names = _validate_axes(payload)
    handoff = _mapping(payload.get("handoff"), name="handoff")
    transferability = _mapping(payload.get("transferability"), name="transferability")

    evidence_scope = _text(handoff.get("evidence_scope"), name="handoff evidence_scope")
    support_semantics = _text(
        handoff.get("support_semantics"), name="handoff support_semantics"
    )
    transferability_category = _text(
        handoff.get("transferability_category"),
        name="handoff transferability_category",
    )
    handoff_category = _text(handoff.get("handoff_category"), name="handoff_category")
    if transferability.get("category") != transferability_category:
        raise ValueError("transferability category disagrees with handoff")
    gains = _validated_transferability_gains(transferability, transferability_category)

    axis_semantics_declared = handoff.get("axis_semantics_declared") is True
    source_frozen = handoff.get("prospective_source_boundary_frozen") is True
    thickness_estimable = handoff.get("thickness_estimable") is True
    projection_allowed = handoff.get("projection_summary_allowed") is True
    serialized_empirical_permission = (
        handoff.get("axis_resolved_species_state_allowed_for_empirical_n3") is True
    )
    serialized_method_permission = (
        handoff.get("axis_resolved_state_allowed_for_method_testing") is True
    )

    projection_summary = payload.get("projection_summary")
    if projection_allowed:
        summary = _mapping(projection_summary, name="projection_summary")
        if not summary:
            raise ValueError("projection_summary must be non-empty when allowed")
    elif projection_summary is not None:
        raise ValueError("projection_summary must be null when unavailable")

    artifact_raw = payload.get("state_artifact")
    artifact_uri: str | None = None
    artifact_sha256: str | None = None
    accepted_empirical = False
    accepted_method = False
    reasons: list[str] = []

    if handoff_category == "empirical_axis_resolved_supported":
        expected = (
            evidence_scope == "empirical"
            and support_semantics == "species_support"
            and axis_semantics_declared
            and source_frozen
            and thickness_estimable
            and transferability_category == "generalizing"
            and serialized_empirical_permission
            and not serialized_method_permission
        )
        if not expected:
            raise ValueError("empirical_axis_resolved_supported payload is internally inconsistent")
        artifact = _mapping(artifact_raw, name="state_artifact")
        artifact_uri, artifact_sha256 = _validate_artifact(
            artifact,
            expected_semantics="empirical_species_support",
            axis_names=axis_names,
        )
        if not gains:
            raise ValueError("empirical generalizing payload requires independent gains")
        accepted_empirical = True

    elif handoff_category == "known_truth_method_state_only":
        if not (
            evidence_scope == "known_truth"
            and support_semantics == "species_support"
            and axis_semantics_declared
            and thickness_estimable
            and serialized_method_permission
            and not serialized_empirical_permission
        ):
            raise ValueError("known_truth_method_state_only payload is internally inconsistent")
        artifact = _mapping(artifact_raw, name="state_artifact")
        artifact_uri, artifact_sha256 = _validate_artifact(
            artifact,
            expected_semantics="known_truth_method_state",
            axis_names=axis_names,
        )
        accepted_method = True
        reasons.append("known_truth_not_empirical_species_evidence")

    elif handoff_category == "structural_capacity_only":
        if support_semantics != "structural_capacity" or serialized_empirical_permission:
            raise ValueError("structural_capacity_only payload is internally inconsistent")
        artifact = _mapping(artifact_raw, name="state_artifact")
        artifact_uri, artifact_sha256 = _validate_artifact(
            artifact,
            expected_semantics="structural_capacity",
            axis_names=axis_names,
        )
        reasons.append("structural_capacity_not_species_support")

    elif handoff_category == "descriptive_projection_only":
        if artifact_raw is not None:
            raise ValueError("descriptive_projection_only payload must not contain state_artifact")
        if not projection_allowed:
            raise ValueError("descriptive_projection_only requires a projection summary")
        if serialized_empirical_permission or serialized_method_permission:
            raise ValueError("descriptive_projection_only cannot carry axis-resolved permission")
        reasons.append("axis_resolved_state_not_admitted")

    elif handoff_category == "unavailable":
        if artifact_raw is not None or projection_allowed or projection_summary is not None:
            raise ValueError("unavailable payload cannot carry state or projection output")
        if serialized_empirical_permission or serialized_method_permission:
            raise ValueError("unavailable payload cannot carry axis-resolved permission")
        reasons.append("n2_handoff_unavailable")

    else:
        raise ValueError(f"unsupported handoff_category: {handoff_category!r}")

    return N2PayloadIntake(
        evidence_id=evidence_id,
        handoff_category=handoff_category,
        fingerprint_verified=True,
        projection_summary_available=projection_allowed,
        accepted_for_empirical_n3=accepted_empirical,
        accepted_for_method_testing=accepted_method,
        state_artifact_uri=artifact_uri,
        state_artifact_sha256=artifact_sha256,
        reason_codes=tuple(reasons),
    )


def verify_n2_state_artifact_bytes(
    payload: Mapping[str, object],
    data: bytes,
) -> N2PayloadIntake:
    """Verify serialized artifact bytes against the integrity-pinned N2 payload."""

    intake = inspect_n2_handoff_payload(payload)
    if intake.state_artifact_sha256 is None:
        raise ValueError("payload does not admit an axis-resolved state artifact")
    observed = hashlib.sha256(bytes(data)).hexdigest()
    if observed != intake.state_artifact_sha256:
        raise ValueError("state artifact sha256 mismatch")
    return intake
