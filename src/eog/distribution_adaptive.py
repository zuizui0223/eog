"""Adaptive source-conditioned EOG distribution modelling.

EOG v0.2 treats ordinary environmental support as the simplest member of a nested
model family rather than forcing every species or landscape to use structural terms.
The training-only candidate family is ordered by complexity:

1. ``environmental``: pointwise environmental support only;
2. ``probability_gate``: conservative EOG accessibility gate;
3. ``stacked``: cross-fitted ``f(H, M, H*M)`` meta-model.

Family selection is performed inside the outer-training data. Declared positive
``selection_fixed_source_ids`` remain available as known source anchors in every
selection fit and are not scored as selection targets. Non-anchor training rows are
held out in selection folds, while each structural candidate performs its own inner
cross-fitting with ``gate_fold_ids``. The untouched outer test is therefore absent from
source construction, fusion fitting, and family selection.

Two explicit complexity margins prevent weak development-set gains from promoting a
more flexible family. A structural family must improve held-out selection log loss over
the environmental model by at least ``minimum_structural_log_loss_gain``. The stacked
family must additionally improve over the probability gate by at least
``minimum_stack_log_loss_gain``. Ties remain biased toward the simpler family.

Nested structural candidates that cannot satisfy the predeclared class-count gate in a
small selection fold fall back to the environmental prediction for that fold; the
fallback count remains visible in the candidate audit rather than weakening the gate.
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
from .support_model import SupportModelError, fit_penalized_logistic_support


ADAPTIVE_FAMILIES = ("environmental", "probability_gate", "stacked")


@dataclass(frozen=True)
class AdaptiveEOGDistributionConfig:
    """Frozen choices for training-only EOG family selection."""

    base_config: EOGDistributionConfig
    stacked_fusion_l2_penalty: float = 1.0
    selection_tolerance: float = 1e-12
    minimum_structural_log_loss_gain: float = 0.0
    minimum_stack_log_loss_gain: float = 0.0

    def __post_init__(self) -> None:
        if (
            not np.isfinite(self.stacked_fusion_l2_penalty)
            or self.stacked_fusion_l2_penalty <= 0.0
        ):
            raise ValueError("stacked_fusion_l2_penalty must be finite and positive")
        for value, name in (
            (self.selection_tolerance, "selection_tolerance"),
            (self.minimum_structural_log_loss_gain, "minimum_structural_log_loss_gain"),
            (self.minimum_stack_log_loss_gain, "minimum_stack_log_loss_gain"),
        ):
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")


@dataclass(frozen=True)
class AdaptiveCandidateScore:
    family: str
    log_loss: float
    n_predictions: int
    fallback_folds: int


@dataclass(frozen=True)
class AdaptiveEOGDistributionModel:
    """EOG model with family choice learned entirely inside outer training."""

    config: AdaptiveEOGDistributionConfig
    selected_family: str
    candidate_scores: tuple[AdaptiveCandidateScore, ...]
    selection_fold_ids: tuple[str, ...]
    gate_fold_ids: tuple[str, ...]
    selection_fixed_source_ids: tuple[str, ...]
    structural_log_loss_gain: float
    stack_log_loss_gain: float
    final_model_fingerprint: str
    prediction: EOGDistributionPrediction
    fingerprint: str

    @property
    def candidate_log_loss(self) -> dict[str, float]:
        return {item.family: item.log_loss for item in self.candidate_scores}

    @property
    def candidate_fallback_folds(self) -> dict[str, int]:
        return {item.family: item.fallback_folds for item in self.candidate_scores}

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


def _normalize_fixed_sources(
    observed_ids: tuple[str, ...],
    response: np.ndarray,
    selection_fixed_source_ids: Sequence[str] | None,
) -> tuple[tuple[str, ...], np.ndarray]:
    fixed = tuple(sorted(str(value) for value in (selection_fixed_source_ids or ())))
    if len(set(fixed)) != len(fixed):
        raise ValueError("selection_fixed_source_ids must be unique")
    observed_index = {node_id: index for index, node_id in enumerate(observed_ids)}
    missing = [node_id for node_id in fixed if node_id not in observed_index]
    if missing:
        raise ValueError(
            f"selection_fixed_source_ids are outside observed training rows: {missing}"
        )
    nonpositive = [
        node_id for node_id in fixed if response[observed_index[node_id]] != 1.0
    ]
    if nonpositive:
        raise ValueError(
            "selection_fixed_source_ids must be positive outer-training observations: "
            f"{nonpositive}"
        )
    fixed_set = set(fixed)
    mask = np.asarray([node_id in fixed_set for node_id in observed_ids], dtype=bool)
    return fixed, mask


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
    fixed_mask: np.ndarray,
    config: AdaptiveEOGDistributionConfig,
    *,
    support_predictors: np.ndarray | None,
    barriers: Mapping[tuple[str, str], float] | None,
    reference_provenance: str,
) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, int]]:
    selection_array = np.asarray(selection_folds, dtype=object)
    gate_array = np.asarray(gate_folds, dtype=object)
    eligible = ~np.asarray(fixed_mask, dtype=bool)
    eligible_folds = tuple(sorted(set(selection_array[eligible].tolist())))
    if len(eligible_folds) < 3:
        raise ValueError(
            "non-fixed adaptive selection rows must contain at least three selection folds"
        )
    predictions = {
        family: np.full(len(observed_ids), np.nan, dtype=float)
        for family in ADAPTIVE_FAMILIES
    }
    fallback_folds = {family: 0 for family in ADAPTIVE_FAMILIES}
    probability_config = replace(config.base_config, structural_gate_weight=None)

    for selection_fold in eligible_folds:
        test_mask = eligible & (selection_array == selection_fold)
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

        environmental_prediction = _environmental_selection_prediction(
            predictors,
            observed_rows,
            response,
            train_mask,
            test_mask,
            probability_config,
        )
        predictions["environmental"][test_mask] = environmental_prediction

        try:
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
        except SupportModelError:
            predictions["probability_gate"][test_mask] = environmental_prediction
            fallback_folds["probability_gate"] += 1
        else:
            predictions["probability_gate"][test_mask] = probability_model.predict(
                test_ids
            ).distribution_support

        try:
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
        except SupportModelError:
            predictions["stacked"][test_mask] = environmental_prediction
            fallback_folds["stacked"] += 1
        else:
            stacked_prediction = stacked_model.predict(test_ids).distribution_support
            if not stacked_model.structural_fusion_present:
                stacked_prediction = environmental_prediction.copy()
                fallback_folds["stacked"] += 1
            predictions["stacked"][test_mask] = stacked_prediction

    for family, values in predictions.items():
        if not np.isfinite(values[eligible]).all():
            raise ValueError(f"adaptive selection produced non-finite {family} predictions")
    return predictions, eligible, fallback_folds


def _select_family(
    response: np.ndarray,
    predictions: Mapping[str, np.ndarray],
    selection_mask: np.ndarray,
    config: AdaptiveEOGDistributionConfig,
    fallback_folds: Mapping[str, int],
) -> tuple[str, tuple[AdaptiveCandidateScore, ...], float, float]:
    mask = np.asarray(selection_mask, dtype=bool)
    if not mask.any():
        raise ValueError("adaptive family selection has no scored candidate rows")
    scores = tuple(
        AdaptiveCandidateScore(
            family=family,
            log_loss=_binary_log_loss(response[mask], predictions[family][mask]),
            n_predictions=int(np.sum(mask)),
            fallback_folds=int(fallback_folds.get(family, 0)),
        )
        for family in ADAPTIVE_FAMILIES
    )
    loss = {item.family: item.log_loss for item in scores}
    environmental_loss = loss["environmental"]
    probability_gain = environmental_loss - loss["probability_gate"]
    stack_gain_vs_environment = environmental_loss - loss["stacked"]
    stack_gain_vs_probability = loss["probability_gate"] - loss["stacked"]
    best_structural_gain = max(probability_gain, stack_gain_vs_environment)

    probability_eligible = (
        probability_gain + config.selection_tolerance
        >= config.minimum_structural_log_loss_gain
    )
    stack_eligible = (
        stack_gain_vs_environment + config.selection_tolerance
        >= config.minimum_structural_log_loss_gain
        and stack_gain_vs_probability + config.selection_tolerance
        >= config.minimum_stack_log_loss_gain
    )

    if stack_eligible:
        selected = "stacked"
    elif probability_eligible:
        selected = "probability_gate"
    else:
        selected = "environmental"
    return selected, scores, float(best_structural_gain), float(stack_gain_vs_probability)


def _replace_support(
    prediction: EOGDistributionPrediction,
    values: np.ndarray,
) -> EOGDistributionPrediction:
    support = np.asarray(values, dtype=float).copy()
    support.setflags(write=False)
    return EOGDistributionPrediction(
        node_ids=prediction.node_ids,
        environmental_support=prediction.environmental_support,
        structural_accessibility=prediction.structural_accessibility,
        minimum_cumulative_cost=prediction.minimum_cumulative_cost,
        minimum_bottleneck_cost=prediction.minimum_bottleneck_cost,
        secondary_source_cost=prediction.secondary_source_cost,
        source_redundancy=prediction.source_redundancy,
        distribution_support=support,
    )


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
    selection_fixed_source_ids: Sequence[str] | None = None,
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
    fixed_sources, fixed_mask = _normalize_fixed_sources(
        observed_ids,
        y,
        selection_fixed_source_ids,
    )
    predictors = _reorder_support_predictors(
        landscape_nodes,
        ordered_nodes,
        support_predictors,
    )
    observed_rows = np.asarray([node_index[node_id] for node_id in observed_ids], dtype=int)

    selection_predictions, selection_mask, fallback_folds = _candidate_selection_predictions(
        landscape_nodes,
        observed_ids,
        y,
        predictors,
        observed_rows,
        selection_folds,
        gate_folds,
        fixed_mask,
        config,
        support_predictors=support_predictors,
        barriers=barriers,
        reference_provenance=reference_provenance,
    )
    selected_family, candidate_scores, structural_gain, stack_gain = _select_family(
        y,
        selection_predictions,
        selection_mask,
        config,
        fallback_folds,
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
        "schema": "adaptive_eog_distribution_v0_4",
        "config": asdict(config),
        "selected_family": selected_family,
        "candidate_scores": [asdict(item) for item in candidate_scores],
        "selection_fold_ids": list(selection_folds),
        "gate_fold_ids": list(gate_folds),
        "selection_fixed_source_ids": list(fixed_sources),
        "structural_log_loss_gain": structural_gain,
        "stack_log_loss_gain": stack_gain,
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
        selection_fixed_source_ids=fixed_sources,
        structural_log_loss_gain=structural_gain,
        stack_log_loss_gain=stack_gain,
        final_model_fingerprint=final_model_fingerprint,
        prediction=prediction,
        fingerprint=fingerprint,
    )
