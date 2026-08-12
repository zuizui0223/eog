"""Source-conditioned EOG distribution modelling.

This experimental v0.2 layer turns EOG from a structural diagnostic into a
location-indexed distribution model.  It combines three explicitly separate
objects:

1. pointwise environmental support fitted from training predictors;
2. source-conditioned structural accessibility through a declared graph;
3. a final held-out-trainable distribution-support model using both quantities.

The structural field is not a dispersal, colonisation, or occupancy probability.
Its graph assumptions and cost scales must be declared explicitly.  Positive
training rows are evaluated with self-source exclusion so a known occurrence
cannot obtain maximal accessibility merely by acting as its own source.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Iterable, Sequence

import numpy as np

from .bridge import BridgeEdge, BridgeWeights
from .support_model import (
    PenalizedLogisticSupportModel,
    SupportModelError,
    fit_penalized_logistic_support,
)


@dataclass(frozen=True)
class AccessibilityConfig:
    """Explicit transformation from graph path costs to structural accessibility."""

    bridge_weights: BridgeWeights = BridgeWeights()
    cumulative_scale: float = 1.0
    bottleneck_scale: float = 1.0
    cumulative_weight: float = 1.0
    bottleneck_weight: float = 1.0

    def __post_init__(self) -> None:
        scales = (self.cumulative_scale, self.bottleneck_scale)
        weights = (self.cumulative_weight, self.bottleneck_weight)
        if not all(np.isfinite(scales)) or any(value <= 0 for value in scales):
            raise ValueError("accessibility cost scales must be finite and positive")
        if not all(np.isfinite(weights)) or any(value < 0 for value in weights):
            raise ValueError("accessibility weights must be finite and non-negative")
        if not any(value > 0 for value in weights):
            raise ValueError("at least one accessibility weight must be positive")


@dataclass(frozen=True)
class StructuralAccessibility:
    """Source-conditioned path summaries for every graph node."""

    source_nodes: tuple[int, ...]
    cumulative_cost: np.ndarray
    bottleneck_cost: np.ndarray
    accessibility: np.ndarray


@dataclass(frozen=True)
class EOGDistributionPrediction:
    """Decomposed EOG prediction at requested graph nodes."""

    node_indices: np.ndarray
    environmental_support: np.ndarray
    structural_accessibility: np.ndarray
    cumulative_cost: np.ndarray
    bottleneck_cost: np.ndarray
    distribution_support: np.ndarray


@dataclass(frozen=True)
class EOGDistributionModel:
    """Fitted static EOG distribution model on a declared graph."""

    n_nodes: int
    edges: tuple[BridgeEdge, ...]
    accessibility_config: AccessibilityConfig
    environmental_model: PenalizedLogisticSupportModel
    distribution_model: PenalizedLogisticSupportModel
    distribution_feature_indices: tuple[int, ...]
    source_nodes: tuple[int, ...]
    predictor_count: int

    def predict(
        self,
        predictors: np.ndarray,
        *,
        node_indices: Sequence[int] | None = None,
    ) -> EOGDistributionPrediction:
        """Predict decomposed distribution support for nodes in the fitted graph."""
        x = _validate_predictors(predictors, self.predictor_count)
        indices = _validate_node_indices(
            np.arange(self.n_nodes) if node_indices is None else node_indices,
            self.n_nodes,
        )
        if x.shape[0] != indices.size:
            raise ValueError("predictor rows must align with node_indices")
        environment = self.environmental_model.predict_support(x)
        accessibility = infer_structural_accessibility(
            self.n_nodes,
            self.edges,
            self.source_nodes,
            self.accessibility_config,
        )
        structural = accessibility.accessibility[indices]
        raw_features = _distribution_features(environment, structural)
        fitted_features = raw_features[:, self.distribution_feature_indices]
        final = self.distribution_model.predict_support(fitted_features)
        return EOGDistributionPrediction(
            node_indices=indices.copy(),
            environmental_support=environment,
            structural_accessibility=structural,
            cumulative_cost=accessibility.cumulative_cost[indices].copy(),
            bottleneck_cost=accessibility.bottleneck_cost[indices].copy(),
            distribution_support=final,
        )


def _validate_predictors(values: np.ndarray, expected_columns: int | None = None) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if x.ndim != 2 or x.shape[0] < 1 or x.shape[1] < 1:
        raise ValueError("predictors must be a non-empty two-dimensional array")
    if not np.all(np.isfinite(x)):
        raise ValueError("predictors contain non-finite values")
    if expected_columns is not None and x.shape[1] != expected_columns:
        raise ValueError(
            f"predictor count {x.shape[1]} != fitted count {expected_columns}"
        )
    return x


def _validate_node_indices(values: Sequence[int], n_nodes: int) -> np.ndarray:
    indices = np.asarray(values, dtype=int)
    if indices.ndim != 1 or indices.size < 1:
        raise ValueError("node_indices must be a non-empty one-dimensional sequence")
    if len(set(indices.tolist())) != indices.size:
        raise ValueError("node_indices must be unique")
    if np.any(indices < 0) or np.any(indices >= n_nodes):
        raise ValueError("node_indices contain a node outside the graph")
    return indices


def _adjacency(
    n_nodes: int,
    edges: Iterable[BridgeEdge],
    weights: BridgeWeights,
) -> list[list[tuple[int, float]]]:
    graph: list[list[tuple[int, float]]] = [[] for _ in range(n_nodes)]
    seen: set[tuple[int, int]] = set()
    for edge in edges:
        if edge.source >= n_nodes or edge.target >= n_nodes:
            raise ValueError("edge endpoint exceeds n_nodes")
        key = (min(edge.source, edge.target), max(edge.source, edge.target))
        if key in seen:
            raise ValueError("duplicate undirected graph edge")
        seen.add(key)
        cost = edge.total(weights)
        graph[edge.source].append((edge.target, cost))
        graph[edge.target].append((edge.source, cost))
    return graph


def _multi_source_cumulative(
    graph: list[list[tuple[int, float]]],
    sources: tuple[int, ...],
) -> np.ndarray:
    distance = np.full(len(graph), np.inf, dtype=float)
    queue: list[tuple[float, int]] = []
    for source in sources:
        distance[source] = 0.0
        heapq.heappush(queue, (0.0, source))
    while queue:
        current, node = heapq.heappop(queue)
        if current != distance[node]:
            continue
        for neighbour, edge_cost in graph[node]:
            candidate = current + edge_cost
            if candidate < distance[neighbour]:
                distance[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    return distance


def _multi_source_bottleneck(
    graph: list[list[tuple[int, float]]],
    sources: tuple[int, ...],
) -> np.ndarray:
    bottleneck = np.full(len(graph), np.inf, dtype=float)
    queue: list[tuple[float, int]] = []
    for source in sources:
        bottleneck[source] = 0.0
        heapq.heappush(queue, (0.0, source))
    while queue:
        current, node = heapq.heappop(queue)
        if current != bottleneck[node]:
            continue
        for neighbour, edge_cost in graph[node]:
            candidate = max(current, edge_cost)
            if candidate < bottleneck[neighbour]:
                bottleneck[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    return bottleneck


def infer_structural_accessibility(
    n_nodes: int,
    edges: Iterable[BridgeEdge],
    source_nodes: Sequence[int],
    config: AccessibilityConfig = AccessibilityConfig(),
) -> StructuralAccessibility:
    """Infer a continuous source-conditioned accessibility field.

    Accessibility is ``exp(-z)`` where ``z`` is an explicitly scaled weighted sum
    of the minimum cumulative path cost and minimum bottleneck path cost.  Nodes
    disconnected from every source receive accessibility zero.
    """
    if n_nodes < 2:
        raise ValueError("n_nodes must be at least two")
    sources = tuple(sorted(set(int(value) for value in source_nodes)))
    if not sources:
        raise ValueError("at least one source node is required")
    if any(value < 0 or value >= n_nodes for value in sources):
        raise ValueError("source node outside the graph")
    edge_list = tuple(edges)
    graph = _adjacency(n_nodes, edge_list, config.bridge_weights)
    cumulative = _multi_source_cumulative(graph, sources)
    bottleneck = _multi_source_bottleneck(graph, sources)
    exponent = (
        config.cumulative_weight * cumulative / config.cumulative_scale
        + config.bottleneck_weight * bottleneck / config.bottleneck_scale
    )
    accessibility = np.zeros(n_nodes, dtype=float)
    finite = np.isfinite(exponent)
    accessibility[finite] = np.exp(-np.clip(exponent[finite], 0.0, 700.0))
    return StructuralAccessibility(
        source_nodes=sources,
        cumulative_cost=cumulative,
        bottleneck_cost=bottleneck,
        accessibility=accessibility,
    )


def _distribution_features(environmental: np.ndarray, accessibility: np.ndarray) -> np.ndarray:
    environmental = np.asarray(environmental, dtype=float)
    accessibility = np.asarray(accessibility, dtype=float)
    if environmental.shape != accessibility.shape:
        raise ValueError("environmental and accessibility vectors must align")
    return np.column_stack(
        [environmental, accessibility, environmental * accessibility]
    )


def _nonconstant_columns(values: np.ndarray, tolerance: float = 1e-12) -> tuple[int, ...]:
    scales = np.std(values, axis=0, ddof=0)
    return tuple(int(index) for index in np.flatnonzero(scales > tolerance))


def _training_accessibility_with_self_exclusion(
    n_nodes: int,
    edges: tuple[BridgeEdge, ...],
    training_nodes: np.ndarray,
    response: np.ndarray,
    config: AccessibilityConfig,
) -> np.ndarray:
    sources = tuple(int(node) for node, value in zip(training_nodes, response) if value == 1.0)
    if len(sources) < 2:
        raise SupportModelError(
            "EOG distribution fitting requires at least two positive source nodes for self exclusion"
        )
    full = infer_structural_accessibility(n_nodes, edges, sources, config).accessibility
    result = full[training_nodes].copy()
    for row_index, (node, value) in enumerate(zip(training_nodes, response)):
        if value != 1.0:
            continue
        reduced_sources = tuple(source for source in sources if source != int(node))
        result[row_index] = infer_structural_accessibility(
            n_nodes, edges, reduced_sources, config
        ).accessibility[int(node)]
    return result


def fit_eog_distribution(
    predictors: np.ndarray,
    response: np.ndarray,
    *,
    n_nodes: int,
    edges: Iterable[BridgeEdge],
    training_node_indices: Sequence[int] | None = None,
    accessibility_config: AccessibilityConfig = AccessibilityConfig(),
    environmental_l2_penalty: float = 1.0,
    distribution_l2_penalty: float = 1.0,
    min_class_count: int = 5,
) -> EOGDistributionModel:
    """Fit the first static source-conditioned EOG distribution model.

    The environmental model is trained on the supplied environmental predictors.
    The final model then learns from environmental support, self-excluded structural
    accessibility, and their interaction.  Prediction uses all positive training
    nodes as structural sources.
    """
    x = _validate_predictors(predictors)
    y = np.asarray(response, dtype=float)
    if y.ndim != 1 or y.shape[0] != x.shape[0]:
        raise ValueError("response must be one-dimensional and align with predictors")
    if not np.all(np.isin(y, (0.0, 1.0))):
        raise ValueError("response must be binary 0/1")
    if n_nodes < x.shape[0]:
        raise ValueError("n_nodes cannot be smaller than the number of training rows")
    training_nodes = _validate_node_indices(
        np.arange(x.shape[0]) if training_node_indices is None else training_node_indices,
        n_nodes,
    )
    if training_nodes.size != x.shape[0]:
        raise ValueError("training_node_indices must align with predictor rows")
    edge_list = tuple(edges)

    environmental_model = fit_penalized_logistic_support(
        x,
        y,
        l2_penalty=environmental_l2_penalty,
        min_class_count=min_class_count,
    )
    environmental = environmental_model.predict_support(x)
    structural = _training_accessibility_with_self_exclusion(
        n_nodes,
        edge_list,
        training_nodes,
        y,
        accessibility_config,
    )
    raw_features = _distribution_features(environmental, structural)
    selected = _nonconstant_columns(raw_features)
    if not selected:
        raise SupportModelError("all EOG distribution features are constant in training")
    distribution_model = fit_penalized_logistic_support(
        raw_features[:, selected],
        y,
        l2_penalty=distribution_l2_penalty,
        min_class_count=min_class_count,
    )
    source_nodes = tuple(
        sorted(int(node) for node, value in zip(training_nodes, y) if value == 1.0)
    )
    return EOGDistributionModel(
        n_nodes=int(n_nodes),
        edges=edge_list,
        accessibility_config=accessibility_config,
        environmental_model=environmental_model,
        distribution_model=distribution_model,
        distribution_feature_indices=selected,
        source_nodes=source_nodes,
        predictor_count=x.shape[1],
    )
