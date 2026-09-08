"""Prospective eligibility diagnostics for prediction-facing EOG state.

This module does not alter Layer A and does not assert predictive superiority.  It
formalizes design properties that must be declared before a Layer-B representation is
fed to a supervised learner, so structural state is not silently treated as a useful
predictive feature block when its training and serving semantics differ.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np


_REFRESH_POLICIES = {"sequential_context", "context_specific", "static_reused"}


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _required_text(value: object, label: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


@dataclass(frozen=True)
class PredictiveStateDesign:
    """Response-independent declaration for Layer-B predictive use.

    ``train_generator_id`` and ``serve_generator_id`` describe the feature-generation
    procedures, not fitted model identities.  They must match when generator parity is
    required.  ``refresh_policy`` records whether repeated observations receive an
    updated state or reuse one static node-level vector.
    """

    repeated_measure_endpoint: bool
    train_generator_id: str
    serve_generator_id: str
    refresh_policy: str
    source_policy: str
    source_label_invariant: bool
    baseline_contains_spatial_coordinates: bool = False
    static_predictive_opt_in: bool = False

    def __post_init__(self) -> None:
        _required_text(self.train_generator_id, "train_generator_id")
        _required_text(self.serve_generator_id, "serve_generator_id")
        _required_text(self.source_policy, "source_policy")
        if self.refresh_policy not in _REFRESH_POLICIES:
            raise ValueError(
                f"refresh_policy must be one of {sorted(_REFRESH_POLICIES)}"
            )

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "repeated_measure_endpoint": self.repeated_measure_endpoint,
                "train_generator_id": self.train_generator_id,
                "serve_generator_id": self.serve_generator_id,
                "refresh_policy": self.refresh_policy,
                "source_policy": self.source_policy,
                "source_label_invariant": self.source_label_invariant,
                "baseline_contains_spatial_coordinates": self.baseline_contains_spatial_coordinates,
                "static_predictive_opt_in": self.static_predictive_opt_in,
            }
        )


@dataclass(frozen=True)
class PredictiveStateEligibility:
    """Decision from response-independent predictive-state design checks."""

    status: str
    predictive_use_allowed: bool
    generator_parity: bool
    repeated_static_reuse: bool
    source_label_invariant: bool
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    design_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class PredictiveStateRefreshAudit:
    """Descriptive audit of realized feature refresh across repeated entities."""

    row_count: int
    feature_count: int
    repeated_entity_count: int
    constant_repeated_entity_count: int
    constant_repeated_entity_fraction: float
    consecutive_transition_count: int
    changed_transition_count: int
    refresh_fraction: float
    exact_unique_state_count: int
    exact_unique_state_fraction: float
    fingerprint: str


def evaluate_predictive_state_design(
    design: PredictiveStateDesign,
) -> PredictiveStateEligibility:
    """Determine whether Layer B is eligible for default supervised augmentation.

    This is deliberately conservative.  A failed gate does *not* invalidate Layer A;
    it only prevents a prediction-facing representation from being treated as a default
    complement without a separately declared and justified design.
    """

    generator_parity = design.train_generator_id == design.serve_generator_id
    repeated_static = design.repeated_measure_endpoint and design.refresh_policy == "static_reused"

    reasons: list[str] = []
    warnings: list[str] = []
    if not generator_parity:
        reasons.append("train_and_serve_feature_generators_differ")
    if not design.source_label_invariant:
        reasons.append("prediction_facing_source_policy_depends_on_arbitrary_source_labels")
    if repeated_static and not design.static_predictive_opt_in:
        reasons.append("repeated_endpoint_reuses_static_state_without_predictive_opt_in")
    if repeated_static and design.baseline_contains_spatial_coordinates:
        warnings.append("static_state_may_duplicate_or_reencode_baseline_spatial_identity")

    if not generator_parity:
        status = "ineligible_generation_shift"
    elif not design.source_label_invariant:
        status = "ineligible_source_label_dependence"
    elif repeated_static and not design.static_predictive_opt_in:
        status = "structural_only_static_reuse"
    else:
        status = "predictive_complement_candidate"

    allowed = not reasons
    payload = {
        "status": status,
        "predictive_use_allowed": allowed,
        "generator_parity": generator_parity,
        "repeated_static_reuse": repeated_static,
        "source_label_invariant": design.source_label_invariant,
        "reasons": reasons,
        "warnings": warnings,
        "design_fingerprint": design.fingerprint,
    }
    return PredictiveStateEligibility(
        status=status,
        predictive_use_allowed=allowed,
        generator_parity=generator_parity,
        repeated_static_reuse=repeated_static,
        source_label_invariant=design.source_label_invariant,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
        design_fingerprint=design.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def audit_predictive_state_refresh(
    feature_matrix: np.ndarray,
    entity_ids: Sequence[str],
    *,
    atol: float = 0.0,
) -> PredictiveStateRefreshAudit:
    """Quantify whether repeated entities receive refreshed Layer-B vectors.

    Rows must already be in the intended context order.  The audit is descriptive and
    response-agnostic: it inspects only the feature matrix and repeated-entity keys.
    ``atol`` controls equality for refresh transitions; exact unique-state counts remain
    byte/numeric exact so the two diagnostics are not conflated.
    """

    matrix = np.asarray(feature_matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] <= 0 or matrix.shape[1] <= 0:
        raise ValueError("feature_matrix must be a non-empty 2D array")
    if not np.isfinite(matrix).all():
        raise ValueError("feature_matrix must be finite")
    ids = tuple(_required_text(value, "entity_id") for value in entity_ids)
    if len(ids) != matrix.shape[0]:
        raise ValueError("entity_ids length must equal feature_matrix row count")
    if atol < 0 or not np.isfinite(atol):
        raise ValueError("atol must be finite and non-negative")

    by_entity: dict[str, list[int]] = {}
    for index, entity_id in enumerate(ids):
        by_entity.setdefault(entity_id, []).append(index)

    repeated = [indices for indices in by_entity.values() if len(indices) >= 2]
    constant_count = 0
    transition_count = 0
    changed_count = 0
    for indices in repeated:
        first = matrix[indices[0]]
        if all(np.allclose(first, matrix[index], rtol=0.0, atol=atol) for index in indices[1:]):
            constant_count += 1
        for left, right in zip(indices, indices[1:]):
            transition_count += 1
            if not np.allclose(matrix[left], matrix[right], rtol=0.0, atol=atol):
                changed_count += 1

    repeated_count = len(repeated)
    constant_fraction = constant_count / repeated_count if repeated_count else 0.0
    refresh_fraction = changed_count / transition_count if transition_count else 0.0
    unique_count = int(np.unique(matrix, axis=0).shape[0])
    unique_fraction = unique_count / matrix.shape[0]
    payload = {
        "row_count": int(matrix.shape[0]),
        "feature_count": int(matrix.shape[1]),
        "repeated_entity_count": repeated_count,
        "constant_repeated_entity_count": constant_count,
        "constant_repeated_entity_fraction": constant_fraction,
        "consecutive_transition_count": transition_count,
        "changed_transition_count": changed_count,
        "refresh_fraction": refresh_fraction,
        "exact_unique_state_count": unique_count,
        "exact_unique_state_fraction": unique_fraction,
        "atol": float(atol),
    }
    return PredictiveStateRefreshAudit(
        row_count=int(matrix.shape[0]),
        feature_count=int(matrix.shape[1]),
        repeated_entity_count=repeated_count,
        constant_repeated_entity_count=constant_count,
        constant_repeated_entity_fraction=float(constant_fraction),
        consecutive_transition_count=transition_count,
        changed_transition_count=changed_count,
        refresh_fraction=float(refresh_fraction),
        exact_unique_state_count=unique_count,
        exact_unique_state_fraction=float(unique_fraction),
        fingerprint=_canonical_sha256(payload),
    )
