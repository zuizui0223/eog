"""Adaptive source-conditioned EOG distribution modelling.

This development model selects the *amount and form* of structural complexity inside
outer training data rather than committing every species or region to one fusion rule.
The candidate family is deliberately small and ordered by complexity:

1. ``environmental``: pointwise environmental support only;
2. ``probability_gate``: conservative EOG accessibility gate;
3. ``stacked``: cross-fitted ``f(H, M, H*M)`` meta-model.

Candidate selection uses an additional set of held-out selection folds inside the
outer-training sample.  Each structural candidate performs its own inner cross-fitting
of environmental support and occurrence-source accessibility using ``gate_fold_ids``.
The untouched outer test therefore participates in neither source construction, fusion
fitting, nor candidate-family selection.

The primary family-selection score is Bernoulli log loss.  If candidates are tied
within ``selection_tolerance``, the simpler family wins in the order above.  This makes
ordinary environmental SDM behavior an explicit member of the EOG model class rather
than something that must be recovered approximately by a structural penalty.
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
    _normalize_observations,
    _reorder_support_predictors,
    _validate_nodes,
    fit_eog_distribution,
)
from .distribution_stack import (
    EOGStackedDistributionModel,
    EOGStackedFusionConfig,
    fit_eog_stacked_distribution,
)
from .support_model import fit_penalized_logistic_support


ADAPTIVE_FAMILIES = ("environmental", "probability_gate", "stacked")


@dataclass(frozen=True)
class AdaptiveEOGDistributionConfig:
    """Frozen choices for training-only EOG family selection."""

    base_config: EOGDistributionConfig
    stacked_fusion_l2_penalty: float = 1.0
    selection_tolerance: float = 1e-12

    def __post_init__(self) -> None:
        if (
            not np.isfinite(self.stacked_fusion_l2_penalty)
            or self.stacked_fusion_l2_penalty <= 0.0
        ):
            raise ValueError("stacked_fusion_l2_penalty must be finite and positive")
        if not np.isfinite(self.selection_tolerance) or self.selection_tolerance < 0.0:
            raise ValueError("selection_tolerance must be finite and non-negative")


@dataclass(frozen=True)
class AdaptiveCandidateScore:
    family: str
    log_loss: float
    n_predictions: int


@dataclass(frozen=True)
class AdaptiveEOGDistributionModel:
    """EOG model with family choice learned entirely inside outer training."""

    config: AdaptiveEOGDistributionConfig
    selected_family: str
    candidate_scores: tuple[AdaptiveCandidateScore, ...]
    selection_fold_ids: tuple[str, ...]
    gate_fold_ids: tuple[str, ...]
    final_model_fingerprint: str
    prediction: EOGDistributionPrediction
    fingerprint: str

    @property
    def candidate_log_loss(self) -> dict[str, float]:
        return {item.family: item.log_loss for item in self.candidate_scores}

    def predict(self, node_ids: Sequence[str] | None = None) -> EOGDistributionPrediction:
        if node_ids is None:
            return self.prediction
        return self.prediction.subset(node_ids)


def _binary_log_loss(response: np.ndarray, prediction: np.ndarray) -> float:
    probability = np.clip(np.asarray(prediction, dtype=float), 1e-12, 1.0 - 1e-12)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(probability) + (1.0 - y) * np.log1p(-probability))))


def _normalize_folds(
    values: Sequence[object] | None,
    n_observations: int,
    *,
    name: str,
    minimum_unique: int,
) -> tuple[str, ...]:
    if values is None:
        raise ValueError(f"{name} are required")
    folds = tuple(str(value) for value in values)
    if len(folds) != n_observations:
        raise ValueError(f"{name} must align with observed_node_ids")
    if any(not value.strip() for value in folds):
        raise ValueError(f"{name} must be non-empty")
    if len(set(folds)) < minimum_unique:
        raise ValueError(f"{name} must contain at least {minimum_unique} folds")
    return folds


def _environmental_selection_prediction(
    predictors: np.ndarray,
    observed_rows: np.ndarray,
    response: np.ndarray,
    train_mask: np.ndarray,
    test_mask: np.ndarray,
    config: EOGDistributionConfig,
) -> np.ndarray:
    support = fit_penalized_logistic_support(
        predictors[observed_rows[train_mask]],
        response[train_mask],
        l2_penalty=config.l2_penalty,
        min_class_count=config.min_class_count,
    )
    return support.predict_support(predictors[observed_rows[test_mask]])


def _candidate_selection_predictions(
    landscape_nodes: Sequence[BridgeNode],
    observed_ids: tuple[str, ...],
    response: np.ndarray,
    predictors: np.ndarray,
    observed_rows: np.ndarray,
    selection_folds: tuple[str, ...],
    gate_folds: tuple[str, ...],
    config: AdaptiveEOGDistributionConfig,
    *,
    support_predictors: np.ndarray | None,
    barriers: Mapping[tuple[str, str], float] | None,
    reference_provenance: str,
) -> dict[str, np.ndarray]:
    selection_array = np.asarray(selection_folds, dtype=object)
    gate_array = np.asarray(gate_folds, dtype=object)
    predictions = {
        family: np.full(len(observed_ids), np.nan, dtype=float)
        for family in ADAPTIVE_FAMILIES
    }
    probability_config = replace(config.base_config, structural_gate_weight=None)

    for selection_fold in sorted(set(selection_folds)):
        test_mask = selection_array == selection_fold
        train_mask = ~test_mask
        train_gate_folds = tuple(str(value) for value in gate_array[train_mask])
        if len(set(train_gate_folds)) < 2:
            raise ValueError(
                "every adaptive selection-training subset must retain at least two gate folds"
            )
        train_ids = tuple(
            node_id for node_id, keep in zip(observed_ids, train_mask) if keep
        )
        train_response = response[train_mask]
        test_ids = tuple(
            node_id for node_id, keep in zip(observed_ids, test_mask) if keep
        )

        predictions["environmental"][test_mask] = _environmental_selection_prediction(
            predictors,
            observed_rows,
            response,
            train_mask,
            test_mask,
            probability_config,
        )

        probability_model = fit_eog_distribution(
            landscape_nodes,
            train_ids,
            train_response,
            probability_config,
            support_predictors=support_predictors,
            barriers=barriers,
            gate_fold_ids=train_gate_folds,
            reference_provenance=(
                f"{reference_provenance}; adaptive selection {selection_fold}; probability"
            ),
        )
        predictions["probability_gate"][test_mask] = probability_model.predict(
            test_ids
        ).distribution_support

        stacked_model = fit_eog_stacked_distribution(
            landscape_nodes,
            train_ids,
            train_response,
            EOGStackedFusionConfig(
                base_config=probability_config,
                fusion_l2_penalty=config.stacked_fusion_l2_penalty,
            ),
            support_predictors=support_predictors,
            barriers=barriers,
            gate_fold_ids=train_gate_folds,
            reference_provenance=(
                f"{reference_provenance}; adaptive selection {selection_fold}; stacked"
            ),
        )
        predictions["stacked"][test_mask] = stacked_model.predict(
            test_ids
        ).distribution_support

    for family, values in predictions.items():
        if not np.isfinite(values).all():
            raise ValueError(f"adaptive selection produced non-finite {family} predictions")
    return predictions


def _select_family(
    response: np.ndarray,
    predictions: Mapping[str, np.ndarray],
    tolerance: float,
) -> tuple[str, tuple[AdaptiveCandidateScore, ...]]:
    scores = tuple(
        AdaptiveCandidateScore(
            family=family,
            log_loss=_binary_log_loss(response, predictions[family]),
            n_predictions=int(response.size),
        )
        for family in ADAPTIVE_FAMILIES
    )
    best_loss = min(item.log_loss for item in scores)
    eligible = {
        item.family
        for item in scores
        if item.log_loss <= best_loss + tolerance
    }
    selected = next(family for family in ADAPTIVE_FAMILIES if family in eligible)
    return selected, scores


def _fit_final_family(
    family: str,
    landscape_nodes: Sequence[BridgeNode],
    observed_ids: tuple[str, ...],
    response: np.ndarray,
    gate_folds: tuple[str, ...],
    config: AdaptiveEOGDistributionConfig,
    *,
    support_predictors: np.ndarray | None,
    barriers: Mapping[tuple[str, str], float] | None,
    reference_provenance: str,
) -> tuple[EOGDistributionPrediction, str]:
    if family == "environmental":
        model: EOGDistributionModel = fit_eog_distribution(
            landscape_nodes,
            observed_ids,
            response,
            replace(config.base_config, structural_gate_weight=0.0),
            support_predictors=support_predictors,
            barriers=barriers,
            reference_provenance=f"{reference_provenance}; adaptive final environmental",
        )
        return model.prediction, model.fingerprint

    if family == "probability_gate":
        model = fit_eog_distribution(
            landscape_nodes,
            observed_ids,
            response,
            replace(config.base_config, structural_gate_weight=None),
            support_predictors=support_predictors,
            barriers=barriers,
            gate_fold_ids=gate_folds,
            reference_provenance=f"{reference_provenance}; adaptive final probability",
        )
        return model.prediction, model.fingerprint

    if family == "stacked":
        stacked: EOGStackedDistributionModel = fit_eog_stacked_distribution(
            landscape_nodes,
            observed_ids,
            response,
            EOGStackedFusionConfig(
                base_config=replace(config.base_config, structural_gate_weight=None),
                fusion_l2_penalty=config.stacked_fusion_l2_penalty,
            ),
            support_predictors=support_predictors,
            barriers=barriers,
            gate_fold_ids=gate_folds,
            reference_provenance=f"{reference_provenance}; adaptive final stacked",
        )
        return stacked.prediction, stacked.fingerprint

    raise ValueError(f"unknown adaptive EOG family: {family}")


def fit_adaptive_eog_distribution(
    landscape_nodes: Sequence[BridgeNode],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
    config: AdaptiveEOGDistributionConfig,
    *,
    selection_fold_ids: Sequence[object] | None,
    gate_fold_ids: Sequence[object] | None,
    support_predictors: np.ndarray | None = None,
    barriers: Mapping[tuple[str, str], float] | None = None,
    reference_provenance: str = "adaptive EOG environmental reference",
) -> AdaptiveEOGDistributionModel:
    """Select and refit an EOG distribution family without using outer-test labels."""
    ordered_nodes = _validate_nodes(landscape_nodes)
    node_index = {node.node_id: index for index, node in enumerate(ordered_nodes)}
    observed_ids, y = _normalize_observations(node_index, observed_node_ids, response)
    selection_folds = _normalize_folds(
        selection_fold_ids,
        len(observed_ids),
        name="selection_fold_ids",
        minimum_unique=3,
    )
    gate_folds = _normalize_folds(
        gate_fold_ids,
        len(observed_ids),
        name="gate_fold_ids",
        minimum_unique=2,
    )
    predictors = _reorder_support_predictors(
        landscape_nodes,
        ordered_nodes,
        support_predictors,
    )
    observed_rows = np.asarray([node_index[node_id] for node_id in observed_ids], dtype=int)

    selection_predictions = _candidate_selection_predictions(
        landscape_nodes,
        observed_ids,
        y,
        predictors,
        observed_rows,
        selection_folds,
        gate_folds,
        config,
        support_predictors=support_predictors,
        barriers=barriers,
        reference_provenance=reference_provenance,
    )
    selected_family, candidate_scores = _select_family(
        y,
        selection_predictions,
        config.selection_tolerance,
    )
    prediction, final_model_fingerprint = _fit_final_family(
        selected_family,
        landscape_nodes,
        observed_ids,
        y,
        gate_folds,
        config,
        support_predictors=support_predictors,
        barriers=barriers,
        reference_provenance=reference_provenance,
    )

    payload = {
        "schema": "adaptive_eog_distribution_v0_1",
        "config": asdict(config),
        "selected_family": selected_family,
        "candidate_scores": [asdict(item) for item in candidate_scores],
        "selection_fold_ids": list(selection_folds),
        "gate_fold_ids": list(gate_folds),
        "final_model_fingerprint": final_model_fingerprint,
        "prediction": prediction.to_dict(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return AdaptiveEOGDistributionModel(
        config=config,
        selected_family=selected_family,
        candidate_scores=candidate_scores,
        selection_fold_ids=selection_folds,
        gate_fold_ids=gate_folds,
        final_model_fingerprint=final_model_fingerprint,
        prediction=prediction,
        fingerprint=fingerprint,
    )
