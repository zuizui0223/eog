"""Permutation-invariant predictive summaries over exact EOG world-set forecast state.

Independent Glanville validation showed that exposing exact world identity directly as
supervised predictive covariates was adverse relative to a symmetric compression of
the same frozen world information.  Exact world/rule identity nevertheless remains
necessary for sequential compatibility filtering, contraction and falsification.

This module therefore defines a deliberately two-layer boundary:

1. the upstream forecast/reconstruction object remains the exact latent epistemic state;
2. the predictive representation is a world-label-invariant numerical summary of the
   surviving support set at a declared horizon.

The summary is not new general set-function mathematics.  It is a stable EOG product
interface motivated by the adverse independent result.  No claim of predictive
superiority follows from implementing it; that requires a fresh independent test.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

import numpy as np


PREDICTIVE_FEATURE_NAMES: tuple[str, ...] = (
    "surviving_world_fraction",
    "support_mean",
    "support_std",
    "support_min",
    "support_max",
    "support_q25",
    "support_q50",
    "support_q75",
    "positive_support_fraction",
    "support_range",
)


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _declared_world_count(forecast: Any) -> int:
    if hasattr(forecast, "world_fingerprints"):
        count = len(tuple(forecast.world_fingerprints))
    elif hasattr(forecast, "rule_fingerprints"):
        count = len(tuple(forecast.rule_fingerprints))
    else:
        raise TypeError(
            "forecast must expose world_fingerprints or rule_fingerprints so the "
            "declared world universe size is auditable"
        )
    if count <= 0:
        raise ValueError("declared world universe must not be empty")
    return count


def _source_forecast_fingerprint(forecast: Any) -> str:
    value = str(getattr(forecast, "fingerprint", "")).strip()
    if not value:
        raise TypeError("forecast must expose a non-empty fingerprint")
    return value


def _gate_fingerprint(forecast: Any) -> str:
    declaration = getattr(forecast, "gate_declaration", None)
    value = str(getattr(declaration, "fingerprint", "")).strip()
    if not value:
        raise TypeError("forecast must expose gate_declaration.fingerprint")
    return value


@dataclass(frozen=True)
class PredictiveNodeSummary:
    """One node's world-label-invariant predictive feature vector."""

    node_id: str
    step: int
    feature_values: tuple[float, ...]
    status: str
    fingerprint: str

    @property
    def feature_mapping(self) -> dict[str, float]:
        return dict(zip(PREDICTIVE_FEATURE_NAMES, self.feature_values, strict=True))


@dataclass(frozen=True)
class WorldSetPredictiveSummary:
    """Symmetric predictive projection of an exact EOG world-set forecast."""

    node_ids: tuple[str, ...]
    step: int
    feature_names: tuple[str, ...]
    rows: tuple[PredictiveNodeSummary, ...]
    declared_world_count: int
    surviving_world_count: int
    representation_name: str
    gate_fingerprint: str
    source_forecast_fingerprint: str
    feature_fingerprint: str
    fingerprint: str

    @property
    def feature_matrix(self) -> np.ndarray:
        return np.asarray([row.feature_values for row in self.rows], dtype=float)


def summarize_worldset_for_prediction(
    forecast: Any,
    *,
    step: int | None = None,
) -> WorldSetPredictiveSummary:
    """Project exact forecast state to a symmetric 10-feature predictive representation.

    The operation is invariant to world ID spelling and member order.  Exact identities
    are intentionally *not* returned in the feature rows; they remain available on the
    upstream forecast object for scientific update/falsification.

    Supported inputs are EOG forecast objects exposing ``node_ids``, ``members``,
    ``max_steps``, ``gate_declaration`` and either ``world_fingerprints`` or
    ``rule_fingerprints``.  This covers both static ``WorldSetForecast`` and sequential
    ``SequentialWorldSetForecast`` without coupling the representation to either class.
    """

    node_ids = tuple(str(value) for value in getattr(forecast, "node_ids", ()))
    if not node_ids or len(set(node_ids)) != len(node_ids):
        raise ValueError("forecast node_ids must contain unique non-empty values")
    max_steps = int(getattr(forecast, "max_steps"))
    resolved_step = max_steps if step is None else int(step)
    if resolved_step < 0 or resolved_step > max_steps:
        raise ValueError("step must lie within the forecast horizon")

    members = tuple(getattr(forecast, "members", ()))
    if not members:
        raise ValueError("forecast must contain at least one surviving world member")
    declared_count = _declared_world_count(forecast)
    surviving_count = len(members)
    if surviving_count > declared_count:
        raise ValueError("surviving world count exceeds declared world universe")

    cumulative = np.stack(
        [np.asarray(member.cumulative_reachability, dtype=float) for member in members],
        axis=0,
    )
    supported = np.stack(
        [np.asarray(member.supported_state, dtype=bool) for member in members],
        axis=0,
    )
    expected_shape = (surviving_count, max_steps + 1, len(node_ids))
    if cumulative.shape != expected_shape or supported.shape != expected_shape:
        raise ValueError(
            f"forecast member matrices must stack to {expected_shape}, got "
            f"{cumulative.shape} and {supported.shape}"
        )
    if not np.isfinite(cumulative).all():
        raise ValueError("forecast cumulative support must be finite")

    step_support = cumulative[:, resolved_step, :]
    step_supported = supported[:, resolved_step, :]
    surviving_fraction = surviving_count / declared_count

    rows: list[PredictiveNodeSummary] = []
    numeric_payload_rows: list[list[object]] = []
    for node_index, node_id in enumerate(node_ids):
        values = step_support[:, node_index]
        flags = step_supported[:, node_index]
        minimum = float(np.min(values))
        maximum = float(np.max(values))
        feature_values = (
            float(surviving_fraction),
            float(np.mean(values)),
            float(np.std(values, ddof=0)),
            minimum,
            maximum,
            float(np.quantile(values, 0.25, method="linear")),
            float(np.quantile(values, 0.50, method="linear")),
            float(np.quantile(values, 0.75, method="linear")),
            float(np.mean(flags)),
            float(maximum - minimum),
        )
        count = int(np.sum(flags))
        if count == 0:
            status = "excluded_in_all_worlds"
        elif count == surviving_count:
            status = "robustly_supported"
        else:
            status = "contingent"
        row_payload = {
            "node_id": node_id,
            "step": resolved_step,
            "feature_names": list(PREDICTIVE_FEATURE_NAMES),
            "feature_values": list(feature_values),
            "status": status,
        }
        row = PredictiveNodeSummary(
            node_id=node_id,
            step=resolved_step,
            feature_values=feature_values,
            status=status,
            fingerprint=_canonical_sha256(row_payload),
        )
        rows.append(row)
        numeric_payload_rows.append([node_id, *feature_values, status])

    gate_fingerprint = _gate_fingerprint(forecast)
    representation_name = "symmetric_world_support_summary_v1"
    feature_payload = {
        "node_ids": list(node_ids),
        "step": resolved_step,
        "feature_names": list(PREDICTIVE_FEATURE_NAMES),
        "rows": numeric_payload_rows,
        "declared_world_count": declared_count,
        "surviving_world_count": surviving_count,
        "representation_name": representation_name,
        "gate_fingerprint": gate_fingerprint,
    }
    feature_fingerprint = _canonical_sha256(feature_payload)
    source_fingerprint = _source_forecast_fingerprint(forecast)
    object_payload = {
        **feature_payload,
        "source_forecast_fingerprint": source_fingerprint,
        "feature_fingerprint": feature_fingerprint,
    }
    return WorldSetPredictiveSummary(
        node_ids=node_ids,
        step=resolved_step,
        feature_names=PREDICTIVE_FEATURE_NAMES,
        rows=tuple(rows),
        declared_world_count=declared_count,
        surviving_world_count=surviving_count,
        representation_name=representation_name,
        gate_fingerprint=gate_fingerprint,
        source_forecast_fingerprint=source_fingerprint,
        feature_fingerprint=feature_fingerprint,
        fingerprint=_canonical_sha256(object_payload),
    )
