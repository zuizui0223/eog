"""Experimental odds-scale accessibility fusion for EOG distribution modelling.

This development module compares a second fusion operator against the original
probability-scale gate without changing the frozen structural manuscript or its
empirical results.

The operator treats environmental support as an upper-envelope baseline and applies
source-conditioned accessibility to the *odds* of that baseline:

    odds(D_EOG) = odds(H) * M_EOG ** kappa

where ``kappa >= 0`` is learned only from inner-cross-fitted training predictions.
``kappa = 0`` reduces exactly to the environmental model and ``M_EOG = 1`` leaves the
environmental support unchanged. Lower accessibility can only reduce, never inflate,
the environmental baseline.
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


@dataclass(frozen=True)
class EOGOddsGateConfig:
    """Development contract for odds-scale accessibility gating."""

    base_config: EOGDistributionConfig
    structural_gate_strength: float | None = None
    maximum_strength: float = 4.0
    strength_grid_size: int = 401
    structural_gate_penalty: float = 0.02

    def __post_init__(self) -> None:
        if not np.isfinite(self.maximum_strength) or self.maximum_strength <= 0.0:
            raise ValueError("maximum_strength must be finite and positive")
        if self.strength_grid_size < 2:
            raise ValueError("strength_grid_size must be at least two")
        if (
            not np.isfinite(self.structural_gate_penalty)
            or self.structural_gate_penalty < 0.0
        ):
            raise ValueError("structural_gate_penalty must be finite and non-negative")
        if self.structural_gate_strength is not None and (
            not np.isfinite(self.structural_gate_strength)
            or not 0.0 <= self.structural_gate_strength <= self.maximum_strength
        ):
            raise ValueError(
                "structural_gate_strength must lie in [0, maximum_strength] when supplied"
            )


@dataclass(frozen=True)
class EOGOddsDistributionModel:
    """Fitted environmental baseline plus odds-scale accessibility gate."""

    config: EOGOddsGateConfig
    base_model: EOGDistributionModel
    structural_gate_strength: float
    structural_gate_fitted: bool
    structural_gate_cross_fitted: bool
    gate_fold_ids: tuple[str, ...] | None
    training_gate_log_loss: float
    prediction: EOGDistributionPrediction
    fingerprint: str

    def predict(self, node_ids: Sequence[str] | None = None) -> EOGDistributionPrediction:
        if node_ids is None:
            return self.prediction
        return self.prediction.subset(node_ids)


def _binary_log_loss(response: np.ndarray, prediction: np.ndarray) -> float:
    probability = np.clip(np.asarray(prediction, dtype=float), 1e-12, 1.0 - 1e-12)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(probability) + (1.0 - y) * np.log1p(-probability))))


def odds_accessibility_fusion(
    environmental_support: np.ndarray,
    structural_accessibility: np.ndarray,
    strength: float,
) -> np.ndarray:
    """Apply ``odds(D) = odds(H) * M**strength`` deterministically."""
    if not np.isfinite(strength) or strength < 0.0:
        raise ValueError("strength must be finite and non-negative")
    environmental = np.asarray(environmental_support, dtype=float)
    accessibility = np.asarray(structural_accessibility, dtype=float)
    if environmental.shape != accessibility.shape:
        raise ValueError("environmental_support and structural_accessibility must align")
    if not np.isfinite(environmental).all() or not np.isfinite(accessibility).all():
        raise ValueError("fusion inputs must be finite")
    if np.any((environmental < 0.0) | (environmental > 1.0)):
        raise ValueError("environmental_support must lie in [0, 1]")
    if np.any((accessibility < 0.0) | (accessibility > 1.0)):
        raise ValueError("structural_accessibility must lie in [0, 1]")
    if strength == 0.0:
        return environmental.copy()

    h = np.clip(environmental, 1e-12, 1.0 - 1e-12)
    m = np.clip(accessibility, 1e-12, 1.0)
    log_odds = np.log(h) - np.log1p(-h) + float(strength) * np.log(m)
    log_odds = np.clip(log_odds, -40.0, 40.0)
    result = 1.0 / (1.0 + np.exp(-log_odds))
    return np.clip(result, 0.0, 1.0)


def _normalize_gate_folds(
    gate_fold_ids: Sequence[object] | None,
    n_observations: int,
) -> tuple[str, ...] | None:
    if gate_fold_ids is None:
        return None
    folds = tuple(str(value) for value in gate_fold_ids)
    if len(folds) != n_observations:
        raise ValueError("gate_fold_ids must align with observed_node_ids")
    if any(not value.strip() for value in folds):
        raise ValueError("gate_fold_ids must be non-empty")
    if len(set(folds)) < 2:
        raise ValueError("gate_fold_ids must contain at least two folds")
    return folds


def _fit_strength(
    response: np.ndarray,
    environmental: np.ndarray,
    accessibility: np.ndarray,
    config: EOGOddsGateConfig,
) -> tuple[float, bool, float]:
    if config.structural_gate_strength is not None:
        strength = float(config.structural_gate_strength)
        loss = _binary_log_loss(
            response,
            odds_accessibility_fusion(environmental, accessibility, strength),
        )
        return strength, False, loss

    best_strength = 0.0
    best_loss = float("inf")
    best_objective = float("inf")
    for strength in np.linspace(
        0.0, config.maximum_strength, config.strength_grid_size
    ):
        strength = float(strength)
        prediction = odds_accessibility_fusion(
            environmental, accessibility, strength
        )
        loss = _binary_log_loss(response, prediction)
        normalized = strength / config.maximum_strength
        objective = loss + 0.5 * config.structural_gate_penalty * normalized * normalized
        if objective < best_objective - 1e-15:
            best_objective = objective
            best_loss = loss
            best_strength = strength
    return best_strength, True, best_loss


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


def fit_eog_odds_distribution(
    landscape_nodes: Sequence[BridgeNode],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
    config: EOGOddsGateConfig,
    *,
    support_predictors: np.ndarray | None = None,
    barriers: Mapping[tuple[str, str], float] | None = None,
    gate_fold_ids: Sequence[object] | None = None,
    reference_provenance: str = "EOG odds-gate distribution environmental reference",
) -> EOGOddsDistributionModel:
    """Fit an odds-scale EOG accessibility gate with optional inner cross-fitting."""
    observed_ids = tuple(str(value) for value in observed_node_ids)
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or y.size != len(observed_ids):
        raise ValueError("response must align with observed_node_ids")
    folds = _normalize_gate_folds(gate_fold_ids, len(observed_ids))
    if config.structural_gate_strength is None and folds is None:
        raise ValueError(
            "gate_fold_ids are required when odds structural strength is estimated"
        )

    fixed_base = replace(
        config.base_config,
        structural_gate_weight=1.0,
    )

    gate_cross_fitted = False
    if config.structural_gate_strength is None:
        fold_array = np.asarray(folds, dtype=object)
        gate_environmental = np.full(len(observed_ids), np.nan, dtype=float)
        gate_accessibility = np.full(len(observed_ids), np.nan, dtype=float)
        for fold in sorted(set(folds or ())):
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
            gate_environmental[test_mask] = heldout_prediction.environmental_support
            gate_accessibility[test_mask] = heldout_prediction.structural_accessibility
        if not np.isfinite(gate_environmental).all() or not np.isfinite(
            gate_accessibility
        ).all():
            raise ValueError("inner-cross-fitted odds-gate inputs are non-finite")
        gate_cross_fitted = True
    else:
        exploratory_base = fit_eog_distribution(
            landscape_nodes,
            observed_ids,
            y,
            fixed_base,
            support_predictors=support_predictors,
            barriers=barriers,
            reference_provenance=reference_provenance,
        )
        observed_prediction = exploratory_base.predict(observed_ids)
        gate_environmental = observed_prediction.environmental_support
        gate_accessibility = observed_prediction.structural_accessibility

    strength, fitted, gate_loss = _fit_strength(
        y,
        gate_environmental,
        gate_accessibility,
        config,
    )

    base_model = fit_eog_distribution(
        landscape_nodes,
        observed_ids,
        y,
        fixed_base,
        support_predictors=support_predictors,
        barriers=barriers,
        reference_provenance=reference_provenance,
    )
    final_support = odds_accessibility_fusion(
        base_model.prediction.environmental_support,
        base_model.prediction.structural_accessibility,
        strength,
    )
    prediction = _replace_distribution_support(base_model.prediction, final_support)

    payload = {
        "schema": "eog_odds_distribution_model_v0_1",
        "config": asdict(config),
        "base_model_fingerprint": base_model.fingerprint,
        "structural_gate_strength": strength,
        "structural_gate_fitted": fitted,
        "structural_gate_cross_fitted": gate_cross_fitted,
        "gate_fold_ids": None if folds is None else list(folds),
        "training_gate_log_loss": gate_loss,
        "prediction": prediction.to_dict(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return EOGOddsDistributionModel(
        config=config,
        base_model=base_model,
        structural_gate_strength=float(strength),
        structural_gate_fitted=bool(fitted),
        structural_gate_cross_fitted=bool(gate_cross_fitted),
        gate_fold_ids=folds,
        training_gate_log_loss=float(gate_loss),
        prediction=prediction,
        fingerprint=fingerprint,
    )
