"""Experimental source-conditioned distribution modelling for EOG.

This module is deliberately separate from the frozen structural manuscript. It turns
EOG's graph primitives into a location-indexed distribution-support model rather than
adding one connected-frequency predictor to an external SDM.

The model operates on a *declared landscape node universe*. Observation labels are
available for only a subset of those nodes. Positive training observations define
sources; unlabelled landscape nodes may act as neutral intermediate nodes but never as
sources. The model returns three separate quantities for every landscape node:

1. pointwise environmental support;
2. source-conditioned structural accessibility;
3. a shrinkable structural gate applied to environmental support.

The gate weight lies in [0, 1]. A value of zero reduces EOG exactly to the pointwise
environmental model, while a value of one applies the full accessibility constraint.
Distribution support is a unit-interval support index, not yet a calibrated occupancy,
colonisation, dispersal, or movement probability.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import heapq
import json
from typing import Mapping, Sequence

import numpy as np

from .bridge import BridgeWeights
from .bridge_builder import (
    BridgeGraphDeclaration,
    BridgeNode,
    BuiltBridgeGraph,
    build_bridge_graph,
)
from .comparative import RobustReference, fit_robust_reference
from .support_model import (
    PenalizedLogisticSupportModel,
    SupportModelError,
    fit_penalized_logistic_support,
)


@dataclass(frozen=True)
class EOGDistributionConfig:
    """Frozen modelling choices for the experimental EOG distribution model."""

    graph_declaration: BridgeGraphDeclaration
    bridge_weights: BridgeWeights = field(default_factory=BridgeWeights)
    cumulative_cost_weight: float = 1.0
    bottleneck_cost_weight: float = 1.0
    structural_gate_weight: float | None = None
    structural_gate_penalty: float = 0.0
    gate_grid_size: int = 1001
    l2_penalty: float = 1.0
    min_class_count: int = 2

    def __post_init__(self) -> None:
        cost_weights = (self.cumulative_cost_weight, self.bottleneck_cost_weight)
        if not all(np.isfinite(cost_weights)) or any(value < 0 for value in cost_weights):
            raise ValueError("structural cost weights must be finite and non-negative")
        if not any(value > 0 for value in cost_weights):
            raise ValueError("at least one structural cost weight must be positive")
        if self.structural_gate_weight is not None and (
            not np.isfinite(self.structural_gate_weight)
            or not 0.0 <= self.structural_gate_weight <= 1.0
        ):
            raise ValueError("structural_gate_weight must lie in [0, 1] when supplied")
        if not np.isfinite(self.structural_gate_penalty) or self.structural_gate_penalty < 0:
            raise ValueError("structural_gate_penalty must be finite and non-negative")
        if self.gate_grid_size < 2:
            raise ValueError("gate_grid_size must be at least two")
        if not np.isfinite(self.l2_penalty) or self.l2_penalty <= 0:
            raise ValueError("l2_penalty must be finite and positive")
        if self.min_class_count < 1:
            raise ValueError("min_class_count must be positive")


@dataclass(frozen=True)
class EOGDistributionPrediction:
    """Location-indexed decomposition returned by an EOG distribution model."""

    node_ids: tuple[str, ...]
    environmental_support: np.ndarray
    structural_accessibility: np.ndarray
    minimum_cumulative_cost: np.ndarray
    minimum_bottleneck_cost: np.ndarray
    secondary_source_cost: np.ndarray
    source_redundancy: np.ndarray
    distribution_support: np.ndarray

    def to_dict(self) -> dict[str, object]:
        return {
            "node_ids": list(self.node_ids),
            "environmental_support": self.environmental_support.tolist(),
            "structural_accessibility": self.structural_accessibility.tolist(),
            "minimum_cumulative_cost": self.minimum_cumulative_cost.tolist(),
            "minimum_bottleneck_cost": self.minimum_bottleneck_cost.tolist(),
            "secondary_source_cost": self.secondary_source_cost.tolist(),
            "source_redundancy": self.source_redundancy.tolist(),
            "distribution_support": self.distribution_support.tolist(),
        }

    def subset(self, node_ids: Sequence[str]) -> "EOGDistributionPrediction":
        index = {node_id: i for i, node_id in enumerate(self.node_ids)}
        requested = tuple(str(node_id) for node_id in node_ids)
        if len(set(requested)) != len(requested):
            raise ValueError("requested prediction node IDs must be unique")
        missing = [node_id for node_id in requested if node_id not in index]
        if missing:
            raise ValueError(f"unknown prediction node IDs: {missing}")
        rows = np.asarray([index[node_id] for node_id in requested], dtype=int)
        return _make_prediction(
            requested,
            self.environmental_support[rows],
            self.structural_accessibility[rows],
            self.minimum_cumulative_cost[rows],
            self.minimum_bottleneck_cost[rows],
            self.secondary_source_cost[rows],
            self.source_redundancy[rows],
            self.distribution_support[rows],
        )


@dataclass(frozen=True)
class EOGDistributionModel:
    """Fitted pointwise-support plus source-conditioned accessibility model."""

    config: EOGDistributionConfig
    graph: BuiltBridgeGraph
    environmental_reference: RobustReference
    support_model: PenalizedLogisticSupportModel
    source_node_ids: tuple[str, ...]
    observed_node_ids: tuple[str, ...]
    observed_response: tuple[int, ...]
    cumulative_cost_scale: float
    bottleneck_cost_scale: float
    structural_gate_weight: float
    structural_gate_fitted: bool
    structural_gate_cross_fitted: bool
    gate_fold_ids: tuple[str, ...] | None
    training_gate_log_loss: float
    prediction: EOGDistributionPrediction
    fingerprint: str

    def predict(self, node_ids: Sequence[str] | None = None) -> EOGDistributionPrediction:
        """Return predictions on the declared landscape universe or a requested subset."""
        if node_ids is None:
            return self.prediction
        return self.prediction.subset(node_ids)


@dataclass(frozen=True)
class _SourceCostPair:
    primary: np.ndarray
    secondary: np.ndarray


def _readonly(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float).copy()
    array.setflags(write=False)
    return array


def _make_prediction(
    node_ids: Sequence[str],
    environmental_support: np.ndarray,
    structural_accessibility: np.ndarray,
    minimum_cumulative_cost: np.ndarray,
    minimum_bottleneck_cost: np.ndarray,
    secondary_source_cost: np.ndarray,
    source_redundancy: np.ndarray,
    distribution_support: np.ndarray,
) -> EOGDistributionPrediction:
    return EOGDistributionPrediction(
        node_ids=tuple(node_ids),
        environmental_support=_readonly(environmental_support),
        structural_accessibility=_readonly(structural_accessibility),
        minimum_cumulative_cost=_readonly(minimum_cumulative_cost),
        minimum_bottleneck_cost=_readonly(minimum_bottleneck_cost),
        secondary_source_cost=_readonly(secondary_source_cost),
        source_redundancy=_readonly(source_redundancy),
        distribution_support=_readonly(distribution_support),
    )


def _validate_nodes(nodes: Sequence[BridgeNode]) -> tuple[BridgeNode, ...]:
    ordered = tuple(sorted(nodes, key=lambda item: item.node_id))
    if len(ordered) < 2:
        raise ValueError("landscape_nodes must contain at least two nodes")
    ids = [node.node_id for node in ordered]
    if len(set(ids)) != len(ids):
        raise ValueError("landscape node IDs must be unique")
    dimensions = {len(node.environmental_state) for node in ordered}
    if len(dimensions) != 1:
        raise ValueError("all landscape environmental states must have the same dimension")
    return ordered


def _reorder_support_predictors(
    input_nodes: Sequence[BridgeNode],
    ordered_nodes: Sequence[BridgeNode],
    support_predictors: np.ndarray | None,
) -> np.ndarray:
    if support_predictors is None:
        return np.asarray([node.environmental_state for node in ordered_nodes], dtype=float)
    matrix = np.asarray(support_predictors, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != len(input_nodes) or matrix.shape[1] < 1:
        raise ValueError(
            "support_predictors must be a two-dimensional matrix with one row per input landscape node"
        )
    if not np.isfinite(matrix).all():
        raise ValueError("support_predictors contain non-finite values")
    original_index: dict[str, int] = {}
    for i, node in enumerate(input_nodes):
        if node.node_id in original_index:
            raise ValueError("landscape node IDs must be unique")
        original_index[node.node_id] = i
    return np.asarray([matrix[original_index[node.node_id]] for node in ordered_nodes], dtype=float)


def _normalize_observations(
    node_index: Mapping[str, int],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
) -> tuple[tuple[str, ...], np.ndarray]:
    ids = tuple(str(node_id) for node_id in observed_node_ids)
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("observed_node_ids must contain unique node IDs")
    missing = [node_id for node_id in ids if node_id not in node_index]
    if missing:
        raise ValueError(f"observed node IDs are outside the landscape universe: {missing}")
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or y.size != len(ids):
        raise ValueError("response must be one-dimensional and align with observed_node_ids")
    if not np.isfinite(y).all() or not np.all(np.isin(y, (0.0, 1.0))):
        raise ValueError("response must contain only finite binary 0/1 values")
    return ids, y


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


def _adjacency(graph: BuiltBridgeGraph, weights: BridgeWeights):
    adjacency: list[list[tuple[int, float]]] = [[] for _ in graph.nodes]
    for edge in graph.edges:
        cost = edge.total(weights)
        adjacency[edge.source].append((edge.target, cost))
        adjacency[edge.target].append((edge.source, cost))
    for rows in adjacency:
        rows.sort(key=lambda item: item[0])
    return adjacency


def _two_best_source_costs(
    graph: BuiltBridgeGraph,
    source_indices: Sequence[int],
    weights: BridgeWeights,
    *,
    bottleneck: bool,
) -> _SourceCostPair:
    """Find the two best costs reaching every node from distinct source nodes."""
    sources = tuple(sorted(set(int(index) for index in source_indices)))
    if not sources:
        raise ValueError("at least one source node is required")
    adjacency = _adjacency(graph, weights)
    labels: list[dict[int, float]] = [dict() for _ in graph.nodes]
    queue: list[tuple[float, int, int]] = []
    for source in sources:
        labels[source][source] = 0.0
        heapq.heappush(queue, (0.0, source, source))

    while queue:
        cost, node, source = heapq.heappop(queue)
        current = labels[node].get(source)
        if current is None or cost != current:
            continue
        for neighbour, edge_cost in adjacency[node]:
            candidate = max(cost, edge_cost) if bottleneck else cost + edge_cost
            existing = labels[neighbour].get(source)
            if existing is not None:
                if candidate >= existing:
                    continue
                labels[neighbour][source] = candidate
                heapq.heappush(queue, (candidate, neighbour, source))
                continue
            if len(labels[neighbour]) >= 2:
                worst_source, worst_cost = max(
                    labels[neighbour].items(), key=lambda item: (item[1], item[0])
                )
                if candidate >= worst_cost:
                    continue
                del labels[neighbour][worst_source]
            labels[neighbour][source] = candidate
            heapq.heappush(queue, (candidate, neighbour, source))

    primary = np.full(len(graph.nodes), np.inf, dtype=float)
    secondary = np.full(len(graph.nodes), np.inf, dtype=float)
    for node, values in enumerate(labels):
        ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
        if ordered:
            primary[node] = ordered[0][1]
        if len(ordered) > 1:
            secondary[node] = ordered[1][1]
    return _SourceCostPair(primary=primary, secondary=secondary)


def _positive_scale(values: np.ndarray) -> float:
    finite_positive = np.asarray(values, dtype=float)
    finite_positive = finite_positive[np.isfinite(finite_positive) & (finite_positive > 0.0)]
    if finite_positive.size == 0:
        return 1.0
    scale = float(np.median(finite_positive))
    if not np.isfinite(scale) or scale <= 0:
        return 1.0
    return scale


def _structural_accessibility(
    cumulative: np.ndarray,
    bottleneck: np.ndarray,
    *,
    cumulative_scale: float,
    bottleneck_scale: float,
    cumulative_weight: float,
    bottleneck_weight: float,
) -> np.ndarray:
    result = np.zeros_like(cumulative, dtype=float)
    reachable = np.isfinite(cumulative) & np.isfinite(bottleneck)
    denominator = cumulative_weight + bottleneck_weight
    normalized = np.zeros_like(cumulative, dtype=float)
    if cumulative_weight > 0:
        normalized[reachable] += cumulative_weight * cumulative[reachable] / cumulative_scale
    if bottleneck_weight > 0:
        normalized[reachable] += bottleneck_weight * bottleneck[reachable] / bottleneck_scale
    result[reachable] = np.exp(-normalized[reachable] / denominator)
    return np.clip(result, 0.0, 1.0)


def _source_redundancy(
    primary: np.ndarray,
    secondary: np.ndarray,
    *,
    cumulative_scale: float,
) -> np.ndarray:
    result = np.zeros_like(primary, dtype=float)
    available = np.isfinite(primary) & np.isfinite(secondary)
    gap = np.maximum(0.0, secondary[available] - primary[available])
    result[available] = np.exp(-gap / cumulative_scale)
    return np.clip(result, 0.0, 1.0)


def _gate_fusion(
    environmental: np.ndarray,
    accessibility: np.ndarray,
    gate_weight: float,
) -> np.ndarray:
    result = np.asarray(environmental, dtype=float) * (
        (1.0 - gate_weight) + gate_weight * np.asarray(accessibility, dtype=float)
    )
    return np.clip(result, 0.0, 1.0)


def _binary_log_loss(response: np.ndarray, prediction: np.ndarray) -> float:
    probability = np.clip(np.asarray(prediction, dtype=float), 1e-12, 1.0 - 1e-12)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(probability) + (1.0 - y) * np.log1p(-probability))))


def _fit_structural_gate(
    response: np.ndarray,
    environmental_support: np.ndarray,
    training_accessibility: np.ndarray,
    config: EOGDistributionConfig,
) -> tuple[float, bool, float]:
    if config.structural_gate_weight is not None:
        weight = float(config.structural_gate_weight)
        loss = _binary_log_loss(
            response, _gate_fusion(environmental_support, training_accessibility, weight)
        )
        return weight, False, loss

    best_weight = 0.0
    best_objective = float("inf")
    best_loss = float("inf")
    for weight in np.linspace(0.0, 1.0, config.gate_grid_size):
        prediction = _gate_fusion(environmental_support, training_accessibility, float(weight))
        loss = _binary_log_loss(response, prediction)
        objective = loss + 0.5 * config.structural_gate_penalty * float(weight * weight)
        if objective < best_objective - 1e-15:
            best_objective = objective
            best_loss = loss
            best_weight = float(weight)
    return best_weight, True, best_loss


def _cross_fitted_gate_inputs(
    graph: BuiltBridgeGraph,
    predictors: np.ndarray,
    observed_ids: tuple[str, ...],
    observed_rows: np.ndarray,
    response: np.ndarray,
    folds: tuple[str, ...],
    config: EOGDistributionConfig,
) -> tuple[np.ndarray, np.ndarray]:
    """Build out-of-fold environmental and accessibility inputs for gate fitting."""
    fold_array = np.asarray(folds, dtype=object)
    environmental = np.full(len(observed_ids), np.nan, dtype=float)
    accessibility = np.full(len(observed_ids), np.nan, dtype=float)

    for fold in sorted(set(folds)):
        test_mask = fold_array == fold
        train_mask = ~test_mask
        if not test_mask.any() or not train_mask.any():
            raise ValueError(f"invalid gate fold: {fold}")
        inner_support = fit_penalized_logistic_support(
            predictors[observed_rows[train_mask]],
            response[train_mask],
            l2_penalty=config.l2_penalty,
            min_class_count=config.min_class_count,
        )
        environmental[test_mask] = inner_support.predict_support(
            predictors[observed_rows[test_mask]]
        )

        inner_source_ids = tuple(
            sorted(
                node_id
                for node_id, value, keep in zip(observed_ids, response, train_mask)
                if keep and value == 1.0
            )
        )
        if not inner_source_ids:
            raise SupportModelError(f"gate fold {fold} leaves no positive structural source")
        inner_source_indices = tuple(graph.node_index[node_id] for node_id in inner_source_ids)
        cumulative = _two_best_source_costs(
            graph, inner_source_indices, config.bridge_weights, bottleneck=False
        )
        bottleneck = _two_best_source_costs(
            graph, inner_source_indices, config.bridge_weights, bottleneck=True
        )
        cumulative_scale = _positive_scale(cumulative.primary)
        bottleneck_scale = _positive_scale(bottleneck.primary)
        fold_accessibility = _structural_accessibility(
            cumulative.primary,
            bottleneck.primary,
            cumulative_scale=cumulative_scale,
            bottleneck_scale=bottleneck_scale,
            cumulative_weight=config.cumulative_cost_weight,
            bottleneck_weight=config.bottleneck_cost_weight,
        )
        accessibility[test_mask] = fold_accessibility[observed_rows[test_mask]]

    if not np.isfinite(environmental).all() or not np.isfinite(accessibility).all():
        raise ValueError("cross-fitted gate inputs contain non-finite values")
    return environmental, accessibility


def _canonical_barriers(
    barriers: Mapping[tuple[str, str], float] | None,
) -> list[tuple[str, str, float]]:
    if not barriers:
        return []
    rows: list[tuple[str, str, float]] = []
    for (first, second), value in barriers.items():
        if not np.isfinite(value) or value < 0:
            raise ValueError("barrier costs must be finite and non-negative")
        a, b = sorted((str(first), str(second)))
        rows.append((a, b, float(value)))
    return sorted(rows)


def fit_eog_distribution(
    landscape_nodes: Sequence[BridgeNode],
    observed_node_ids: Sequence[str],
    response: Sequence[int] | np.ndarray,
    config: EOGDistributionConfig,
    *,
    support_predictors: np.ndarray | None = None,
    barriers: Mapping[tuple[str, str], float] | None = None,
    gate_fold_ids: Sequence[object] | None = None,
    reference_provenance: str = "EOG distribution-model landscape environmental reference",
) -> EOGDistributionModel:
    """Fit EOG on one declared landscape universe and return a full distribution map.

    Only response-positive training rows become structural sources. During outer
    validation, held-out labels must not be supplied here.

    When ``gate_fold_ids`` is supplied and the gate is estimated, both environmental
    support and structural accessibility used to select the gate are generated
    out-of-fold. Inner held-out positive rows are completely absent from the source set.
    Without gate folds, a stricter-than-self but non-cross-fitted fallback uses the
    second-best distinct source path for positive rows during gate fitting.
    """
    input_nodes = tuple(landscape_nodes)
    ordered_nodes = _validate_nodes(input_nodes)
    node_index = {node.node_id: i for i, node in enumerate(ordered_nodes)}
    predictors = _reorder_support_predictors(input_nodes, ordered_nodes, support_predictors)
    observed_ids, y = _normalize_observations(node_index, observed_node_ids, response)
    folds = _normalize_gate_folds(gate_fold_ids, len(observed_ids))

    observed_rows = np.asarray([node_index[node_id] for node_id in observed_ids], dtype=int)
    support_model = fit_penalized_logistic_support(
        predictors[observed_rows],
        y,
        l2_penalty=config.l2_penalty,
        min_class_count=config.min_class_count,
    )
    environmental_support = support_model.predict_support(predictors)

    source_ids = tuple(sorted(node_id for node_id, value in zip(observed_ids, y) if value == 1.0))
    if not source_ids:
        raise SupportModelError("EOG distribution modelling requires at least one positive source")

    environmental_states = np.asarray(
        [node.environmental_state for node in ordered_nodes], dtype=float
    )
    reference = fit_robust_reference(environmental_states, provenance=reference_provenance)
    graph = build_bridge_graph(
        ordered_nodes,
        reference,
        config.graph_declaration,
        barriers=barriers,
    )
    source_indices = tuple(graph.node_index[node_id] for node_id in source_ids)
    cumulative = _two_best_source_costs(
        graph, source_indices, config.bridge_weights, bottleneck=False
    )
    bottleneck = _two_best_source_costs(
        graph, source_indices, config.bridge_weights, bottleneck=True
    )

    cumulative_scale = _positive_scale(cumulative.primary)
    bottleneck_scale = _positive_scale(bottleneck.primary)
    accessibility = _structural_accessibility(
        cumulative.primary,
        bottleneck.primary,
        cumulative_scale=cumulative_scale,
        bottleneck_scale=bottleneck_scale,
        cumulative_weight=config.cumulative_cost_weight,
        bottleneck_weight=config.bottleneck_cost_weight,
    )
    redundancy = _source_redundancy(
        cumulative.primary,
        cumulative.secondary,
        cumulative_scale=cumulative_scale,
    )

    gate_cross_fitted = False
    if config.structural_gate_weight is None and folds is not None:
        gate_environmental, gate_accessibility = _cross_fitted_gate_inputs(
            graph,
            predictors,
            observed_ids,
            observed_rows,
            y,
            folds,
            config,
        )
        gate_cross_fitted = True
    else:
        gate_environmental = environmental_support[observed_rows]
        training_cumulative = cumulative.primary[observed_rows].copy()
        training_bottleneck = bottleneck.primary[observed_rows].copy()
        for position, (node_id, value) in enumerate(zip(observed_ids, y)):
            if value == 1.0:
                row = graph.node_index[node_id]
                training_cumulative[position] = cumulative.secondary[row]
                training_bottleneck[position] = bottleneck.secondary[row]
        gate_accessibility = _structural_accessibility(
            training_cumulative,
            training_bottleneck,
            cumulative_scale=cumulative_scale,
            bottleneck_scale=bottleneck_scale,
            cumulative_weight=config.cumulative_cost_weight,
            bottleneck_weight=config.bottleneck_cost_weight,
        )

    gate_weight, gate_fitted, gate_loss = _fit_structural_gate(
        y,
        gate_environmental,
        gate_accessibility,
        config,
    )
    distribution_support = _gate_fusion(
        environmental_support,
        accessibility,
        gate_weight,
    )
    prediction = _make_prediction(
        tuple(node.node_id for node in graph.nodes),
        environmental_support,
        accessibility,
        cumulative.primary,
        bottleneck.primary,
        cumulative.secondary,
        redundancy,
        distribution_support,
    )

    payload = {
        "schema": "eog_distribution_model_v0_2",
        "config": asdict(config),
        "graph_fingerprint": graph.fingerprint,
        "reference": reference.to_dict(),
        "observations": sorted(
            (node_id, int(value)) for node_id, value in zip(observed_ids, y)
        ),
        "sources": list(source_ids),
        "barriers": _canonical_barriers(barriers),
        "gate_fold_ids": None if folds is None else list(folds),
        "support_model": {
            "predictor_mean": support_model.predictor_mean.tolist(),
            "predictor_scale": support_model.predictor_scale.tolist(),
            "coefficients": support_model.coefficients.tolist(),
            "intercept": support_model.intercept,
            "l2_penalty": support_model.l2_penalty,
        },
        "cumulative_cost_scale": cumulative_scale,
        "bottleneck_cost_scale": bottleneck_scale,
        "structural_gate_weight": gate_weight,
        "structural_gate_fitted": gate_fitted,
        "structural_gate_cross_fitted": gate_cross_fitted,
        "training_gate_log_loss": gate_loss,
        "prediction": prediction.to_dict(),
    }
    fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return EOGDistributionModel(
        config=config,
        graph=graph,
        environmental_reference=reference,
        support_model=support_model,
        source_node_ids=source_ids,
        observed_node_ids=observed_ids,
        observed_response=tuple(int(value) for value in y),
        cumulative_cost_scale=float(cumulative_scale),
        bottleneck_cost_scale=float(bottleneck_scale),
        structural_gate_weight=float(gate_weight),
        structural_gate_fitted=bool(gate_fitted),
        structural_gate_cross_fitted=bool(gate_cross_fitted),
        gate_fold_ids=folds,
        training_gate_log_loss=float(gate_loss),
        prediction=prediction,
        fingerprint=fingerprint,
    )
