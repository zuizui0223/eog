"""Cross-fitted stacked fusion for experimental EOG distribution modelling.

This module adapts the useful joint-fusion idea from the parallel v0.2 development
track while preserving the stricter nested information boundary developed in PR #138.
The second-stage model is trained only on inner out-of-fold environmental support and
source-conditioned accessibility, never on in-sample self-supported structural values.

The meta features are ``H``, ``M`` and ``H*M``. They are low-dimensional and fitted
with the repository's deterministic L2 logistic engine. This is a development
candidate, not yet the promoted public EOG fusion.

If cross-fitting shows that the structural columns are constant or exact duplicates of
the environmental column, the stacked candidate is not allowed to win merely by
recalibrating ``H``. In that case its distribution support reduces exactly to the
cross-fitted environmental model, preserving the simpler-family fallback contract.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .bridge_builder import BridgeNode
from .distribution import (
    EOGDistributionConfig,
    EOGDistributionModel,
    EOGDistributionPrediction,
    fit_eog_distribution,
)
from .support_model import PenalizedLogisticSupportModel, fit_penalized_logistic_support


@dataclass(frozen=True)
class EOGStackedFusionConfig:
    """Development contract for a cross-fitted EOG meta-model."""

    base_config: EOGDistributionConfig
    fusion_l2_penalty: float = 1.0
    min_class_count: int | None = None

    def __post_init__(self) -> None:
        if not np.isfinite(self.fusion_l2_penalty) or self.fusion_l2_penalty <= 0.0:
            raise ValueError("fusion_l2_penalty must be finite and positive")
        if self.min_class_count is not None and self.min_class_count < 1:
            raise ValueError("min_class_count must be positive when supplied")


@dataclass(frozen=True)
class EOGStackedDistributionModel:
    """Fitted cross-fitted second-stage EOG distribution model."""

    config: EOGStackedFusionConfig
    base_model: EOGDistributionModel
    fusion_model: PenalizedLogisticSupportModel
    fusion_feature_indices: tuple[int, ...]
    structural_fusion_present: bool
    gate_fold_ids: tuple[str, ...]
    training_fusion_log_loss: float
    prediction: EOGDistributionPrediction
    fingerprint: str

    def predict(self, node_ids: Sequence[str] | None = None) -> EOGDistributionPrediction:
        if node_ids is None:
            return self.prediction
        return self.prediction.subset(node_ids)


def _normalize_gate_folds(
    gate_fold_ids: Sequence[object] | None,
    n_observations: int,
) -> tuple[str, ...]:
    if gate_fold_ids is None:
        raise ValueError("gate_fold_ids are required for cross-fitted stacked fusion")
    folds = tuple(str(value) for value in gate_fold_ids)
    if len(folds) != n_observations:
        raise ValueError("gate_fold_ids must align with observed_node_ids")
    if any(not value.strip() for value in folds):
        raise ValueError("gate_fold_ids must be non-empty")
    if len(set(folds)) < 2:
        raise ValueError("gate_fold_ids must contain at least two folds")
    return folds


def _fusion_features(environmental: np.ndarray, accessibility: np.ndarray) -> np.ndarray:
    environmental = np.asarray(environmental, dtype=float)
    accessibility = np.asarray(accessibility, dtype=float)
    if environmental.shape != accessibility.shape:
        raise ValueError("environmental and accessibility vectors must align")
    if not np.isfinite(environmental).all() or not np.isfinite(accessibility).all():
        raise ValueError("fusion inputs must be finite")
    return np.column_stack(
        [environmental, accessibility, environmental * accessibility]
    )


def _select_features(values: np.ndarray, tolerance: float = 1e-12) -> tuple[int, ...]:
    """Drop constants and exact duplicate columns deterministically."""
    selected: list[int] = []
    for index in range(values.shape[1]):
        column = values[:, index]
        if float(np.std(column, ddof=0)) <= tolerance:
            continue
        duplicate = any(
            np.allclose(column, values[:, prior], rtol=0.0, atol=tolerance)
            for prior in selected
        )
        if not duplicate:
            selected.append(index)
    if not selected:
        raise ValueError("all stacked EOG fusion features are constant")
    return tuple(selected)


def _binary_log_loss(response: np.ndarray, prediction: np.ndarray) -> float:
    probability = np.clip(np.asarray(prediction, dtype=float), 1e-12, 1.0 - 1e-12)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(probability) + (1.0 - y) * np.log1p(-probability))))


def _replace_distribution_support(
    prediction: EOGDistributionPrediction,
    distribution_support: np.ndarray,
) -> EOGDistributionPrediction:
    values = np.asarray(distribution_support, dtype=float).copy()
    values.setflags(write=False)
    return EOGDistributionPrediction(
        node_ids=prediction.node_ids,
        environmental_support=prediction.environmental_support,
        structural_accessibility=prediction.structural_accessibility,
        minimum_cumulative_cost=prediction.minimum_cumulative_cost,
        minimum_bottleneck_cost=prediction.minimum_bottleneck_cost,
        secondary_source_cost=prediction.secondary_source_cost,
        source_redundancy=prediction.source_redundancy,
        distribution_support=values,
    )


def fit_eog_stacked_distribution(
    landscape_nodes: Sequence[BridgeNode],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
    config: EOGStackedFusionConfig,
    *,
    support_predictors: np.ndarray | None = None,
    barriers: Mapping[tuple[str, str], float] | None = None,
    gate_fold_ids: Sequence[object] | None = None,
    reference_provenance: str = "EOG stacked distribution environmental reference",
) -> EOGStackedDistributionModel:
    """Fit ``f(H, M, H*M)`` from inner out-of-fold EOG components."""
    observed_ids = tuple(str(value) for value in observed_node_ids)
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or y.size != len(observed_ids):
        raise ValueError("response must align with observed_node_ids")
    folds = _normalize_gate_folds(gate_fold_ids, len(observed_ids))
    fold_array = np.asarray(folds, dtype=object)

    fixed_base = replace(config.base_config, structural_gate_weight=1.0)
    oof_environmental = np.full(len(observed_ids), np.nan, dtype=float)
    oof_accessibility = np.full(len(observed_ids), np.nan, dtype=float)

    for fold in sorted(set(folds)):
        test_mask = fold_array == fold
        train_mask = ~test_mask
        inner_ids = tuple(
            node_id for node_id, keep in zip(observed_ids, train_mask) if keep
        )
        inner_response = y[train_mask]
        inner_model = fit_eog_distribution(
            landscape_nodes,
            inner_ids,
            inner_response,
            fixed_base,
            support_predictors=support_predictors,
            barriers=barriers,
            reference_provenance=f"{reference_provenance}; inner fold {fold}",
        )
        heldout_ids = tuple(
            node_id for node_id, keep in zip(observed_ids, test_mask) if keep
        )
        heldout_prediction = inner_model.predict(heldout_ids)
        oof_environmental[test_mask] = heldout_prediction.environmental_support
        oof_accessibility[test_mask] = heldout_prediction.structural_accessibility

    if not np.isfinite(oof_environmental).all() or not np.isfinite(
        oof_accessibility
    ).all():
        raise ValueError("cross-fitted stacked fusion inputs are non-finite")

    raw_oof = _fusion_features(oof_environmental, oof_accessibility)
    selected = _select_features(raw_oof)
    structural_present = any(index in {1, 2} for index in selected)
    min_class_count = (
        config.base_config.min_class_count
        if config.min_class_count is None
        else config.min_class_count
    )
    fusion_model = fit_penalized_logistic_support(
        raw_oof[:, selected],
        y,
        l2_penalty=config.fusion_l2_penalty,
        min_class_count=min_class_count,
    )
    if structural_present:
        oof_prediction = fusion_model.predict_support(raw_oof[:, selected])
    else:
        # A stack with only H is not a structural model family. Preserve the exact
        # environmental OOF prediction so it cannot win by response recalibration.
        oof_prediction = oof_environmental.copy()
    training_loss = _binary_log_loss(y, oof_prediction)

    base_model = fit_eog_distribution(
        landscape_nodes,
        observed_ids,
        y,
        fixed_base,
        support_predictors=support_predictors,
        barriers=barriers,
        reference_provenance=reference_provenance,
    )
    raw_full = _fusion_features(
        base_model.prediction.environmental_support,
        base_model.prediction.structural_accessibility,
    )
    if structural_present:
        final_support = fusion_model.predict_support(raw_full[:, selected])
    else:
        final_support = base_model.prediction.environmental_support.copy()
    prediction = _replace_distribution_support(base_model.prediction, final_support)

    payload = {
        "schema": "eog_stacked_distribution_model_v0_2",
        "config": asdict(config),
        "base_model_fingerprint": base_model.fingerprint,
        "fusion_feature_indices": list(selected),
        "fusion_model": {
            "predictor_mean": fusion_model.predictor_mean.tolist(),
            "predictor_scale": fusion_model.predictor_scale.tolist(),
            "coefficients": fusion_model.coefficients.tolist(),
            "intercept": fusion_model.intercept,
            "l2_penalty": fusion_model.l2_penalty,
        },
        "structural_fusion_present": structural_present,
        "gate_fold_ids": list(folds),
        "training_fusion_log_loss": training_loss,
        "prediction": prediction.to_dict(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return EOGStackedDistributionModel(
        config=config,
        base_model=base_model,
        fusion_model=fusion_model,
        fusion_feature_indices=selected,
        structural_fusion_present=bool(structural_present),
        gate_fold_ids=folds,
        training_fusion_log_loss=float(training_loss),
        prediction=prediction,
        fingerprint=fingerprint,
    )
