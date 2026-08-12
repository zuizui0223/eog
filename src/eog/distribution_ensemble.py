"""Fixed convex structural ensemble for experimental EOG distribution modelling.

The ensemble combines two already leakage-safe EOG distribution candidates:

- the conservative probability-scale accessibility gate;
- the cross-fitted stacked ``f(H, M, H*M)`` model.

No response is fitted at the ensemble layer. For a declared ``stack_weight`` alpha,

    D_ensemble = (1 - alpha) * D_probability + alpha * D_stack.

The model preserves the common environmental-support and structural-accessibility
fields from the probability-gate fit and replaces only ``distribution_support`` with
the convex ensemble.  Alpha is an explicit contract value; confirmatory analyses must
freeze it before any held-out outcome is inspected.
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
from .distribution_stack import (
    EOGStackedDistributionModel,
    EOGStackedFusionConfig,
    fit_eog_stacked_distribution,
)


@dataclass(frozen=True)
class EOGStructuralEnsembleConfig:
    """Frozen configuration for a probability/stack structural ensemble."""

    base_config: EOGDistributionConfig
    stack_weight: float
    stacked_fusion_l2_penalty: float = 1.0

    def __post_init__(self) -> None:
        if not np.isfinite(self.stack_weight) or not 0.0 <= self.stack_weight <= 1.0:
            raise ValueError("stack_weight must lie in [0, 1]")
        if (
            not np.isfinite(self.stacked_fusion_l2_penalty)
            or self.stacked_fusion_l2_penalty <= 0.0
        ):
            raise ValueError("stacked_fusion_l2_penalty must be finite and positive")


@dataclass(frozen=True)
class EOGStructuralEnsembleModel:
    """Fitted fixed-weight EOG structural ensemble."""

    config: EOGStructuralEnsembleConfig
    probability_model: EOGDistributionModel
    stacked_model: EOGStackedDistributionModel
    prediction: EOGDistributionPrediction
    fingerprint: str

    def predict(self, node_ids: Sequence[str] | None = None) -> EOGDistributionPrediction:
        if node_ids is None:
            return self.prediction
        return self.prediction.subset(node_ids)


def _replace_distribution_support(
    prediction: EOGDistributionPrediction,
    support: np.ndarray,
) -> EOGDistributionPrediction:
    values = np.asarray(support, dtype=float).copy()
    if values.shape != prediction.distribution_support.shape or not np.isfinite(values).all():
        raise ValueError("ensemble distribution support must align and be finite")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("ensemble distribution support must lie in [0, 1]")
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


def fit_eog_structural_ensemble(
    landscape_nodes: Sequence[BridgeNode],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
    config: EOGStructuralEnsembleConfig,
    *,
    support_predictors: np.ndarray | None = None,
    barriers: Mapping[tuple[str, str], float] | None = None,
    gate_fold_ids: Sequence[object] | None = None,
    reference_provenance: str = "EOG structural ensemble environmental reference",
) -> EOGStructuralEnsembleModel:
    """Fit the two nested EOG candidates and combine them with fixed ``stack_weight``."""
    probability_config = replace(config.base_config, structural_gate_weight=None)
    probability = fit_eog_distribution(
        landscape_nodes,
        observed_node_ids,
        response,
        probability_config,
        support_predictors=support_predictors,
        barriers=barriers,
        gate_fold_ids=gate_fold_ids,
        reference_provenance=f"{reference_provenance}; probability component",
    )
    stacked = fit_eog_stacked_distribution(
        landscape_nodes,
        observed_node_ids,
        response,
        EOGStackedFusionConfig(
            base_config=probability_config,
            fusion_l2_penalty=config.stacked_fusion_l2_penalty,
        ),
        support_predictors=support_predictors,
        barriers=barriers,
        gate_fold_ids=gate_fold_ids,
        reference_provenance=f"{reference_provenance}; stacked component",
    )

    alpha = float(config.stack_weight)
    ensemble_support = (
        (1.0 - alpha) * probability.prediction.distribution_support
        + alpha * stacked.prediction.distribution_support
    )
    prediction = _replace_distribution_support(probability.prediction, ensemble_support)
    payload = {
        "schema": "eog_structural_ensemble_model_v0_1",
        "config": asdict(config),
        "probability_model_fingerprint": probability.fingerprint,
        "stacked_model_fingerprint": stacked.fingerprint,
        "prediction": prediction.to_dict(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return EOGStructuralEnsembleModel(
        config=config,
        probability_model=probability,
        stacked_model=stacked,
        prediction=prediction,
        fingerprint=fingerprint,
    )
