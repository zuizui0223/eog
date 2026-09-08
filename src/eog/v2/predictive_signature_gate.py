"""Response-independent gate for saturated static entity signatures in Layer B.

This gate is deliberately narrow. It does not decide whether a predictive feature block
is generally redundant or useful. It detects the exact structural failure mode observed
in the Tampa audit: the compatible world set never contracts, repeated observations of
an entity reuse one unchanged Layer-B vector, and those entity-level vectors form an
injective identity-like signature.

Layer A remains valid when this gate withholds Layer B from supervised prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

import numpy as np

from .worldset_contraction_audit import WorldSetContractionAudit


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class PredictiveSignatureGateResult:
    status: str
    predictive_use_allowed: bool
    worldset_fully_saturated: bool
    repeated_entity_count: int
    all_repeated_entities_static: bool
    entity_signature_count: int
    entity_signature_injective: bool
    reasons: tuple[str, ...]
    fingerprint: str


def evaluate_saturated_static_signature(
    feature_matrix: np.ndarray,
    entity_ids: Sequence[str],
    contraction_audit: WorldSetContractionAudit,
    *,
    atol: float = 0.0,
) -> PredictiveSignatureGateResult:
    """Detect a saturated, static, injective entity-level Layer-B signature.

    The blocking condition is exact and conjunctive:

    1. every audited context retains the full declared world universe;
    2. every repeated entity has one unchanged Layer-B vector across its rows;
    3. the resulting entity-level vectors are one-to-one across repeated entities.

    This is a prediction-facing safeguard only. It never invalidates exact Layer-A
    compatibility, contraction, or falsification state.
    """

    matrix = np.asarray(feature_matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("feature_matrix must be a non-empty 2D array")
    if not np.isfinite(matrix).all():
        raise ValueError("feature_matrix must be finite")
    if len(entity_ids) != matrix.shape[0]:
        raise ValueError("entity_ids length must equal feature_matrix rows")
    if not np.isfinite(atol) or atol < 0:
        raise ValueError("atol must be finite and non-negative")

    ids = tuple(str(value).strip() for value in entity_ids)
    if any(not value for value in ids):
        raise ValueError("entity_ids must be non-empty strings")

    by_entity: dict[str, list[int]] = {}
    for row, entity_id in enumerate(ids):
        by_entity.setdefault(entity_id, []).append(row)
    repeated = {key: rows for key, rows in by_entity.items() if len(rows) >= 2}

    representatives: list[np.ndarray] = []
    static_flags: list[bool] = []
    for entity_id in sorted(repeated):
        rows = repeated[entity_id]
        first = matrix[rows[0]]
        is_static = all(
            np.allclose(first, matrix[row], rtol=0.0, atol=atol) for row in rows[1:]
        )
        static_flags.append(is_static)
        if is_static:
            representatives.append(first)

    all_static = bool(repeated) and all(static_flags)
    signature_count = 0
    injective = False
    if all_static:
        rep_matrix = np.asarray(representatives, dtype=float)
        signature_count = int(np.unique(rep_matrix, axis=0).shape[0])
        injective = signature_count == len(repeated)

    fully_saturated = contraction_audit.fully_saturated_context_count == contraction_audit.context_count
    blocked = fully_saturated and all_static and injective
    reasons: list[str] = []
    if blocked:
        reasons.append("full_worldset_saturation_with_static_injective_entity_signature")
        status = "structural_only_spatial_signature"
    else:
        status = "no_exact_saturated_static_signature"

    payload = {
        "status": status,
        "predictive_use_allowed": not blocked,
        "worldset_fully_saturated": fully_saturated,
        "repeated_entity_count": len(repeated),
        "all_repeated_entities_static": all_static,
        "entity_signature_count": signature_count,
        "entity_signature_injective": injective,
        "reasons": reasons,
        "contraction_fingerprint": contraction_audit.fingerprint,
        "atol": float(atol),
    }
    return PredictiveSignatureGateResult(
        status=status,
        predictive_use_allowed=not blocked,
        worldset_fully_saturated=fully_saturated,
        repeated_entity_count=len(repeated),
        all_repeated_entities_static=all_static,
        entity_signature_count=signature_count,
        entity_signature_injective=injective,
        reasons=tuple(reasons),
        fingerprint=_sha256(payload),
    )
