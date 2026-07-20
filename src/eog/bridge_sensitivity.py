"""Sensitivity of population-pair bridge diagnostics to declared graph scenarios.

Frequencies produced here describe robustness across a predeclared scenario ensemble.
They are not posterior, occupancy, suitability, dispersal or colonisation probabilities.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .bridge import BridgeInference, BridgeWeights, infer_bridge
from .bridge_builder import (
    BridgeGraphDeclaration,
    BridgeNode,
    build_bridge_graph,
)
from .comparative import RobustReference


@dataclass(frozen=True)
class BridgeSensitivityScenario:
    """One predeclared graph and weighting assumption."""

    scenario_id: str
    declaration: BridgeGraphDeclaration
    weights: BridgeWeights = BridgeWeights()
    barriers: tuple[tuple[str, str, float], ...] = ()
    redundancy_threshold: float | None = None

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be non-empty")
        seen: set[tuple[str, str]] = set()
        for source, target, value in self.barriers:
            if not source.strip() or not target.strip() or source == target:
                raise ValueError("barrier endpoints must be distinct non-empty node IDs")
            if not np.isfinite(value) or value < 0:
                raise ValueError("barrier costs must be finite and non-negative")
            key = tuple(sorted((source, target)))
            if key in seen:
                raise ValueError("barrier pairs must be unique within a scenario")
            seen.add(key)
        if self.redundancy_threshold is not None and (
            not np.isfinite(self.redundancy_threshold) or self.redundancy_threshold < 0
        ):
            raise ValueError("redundancy_threshold must be finite and non-negative")

    def barrier_mapping(self) -> dict[tuple[str, str], float]:
        return {(source, target): float(value) for source, target, value in self.barriers}


@dataclass(frozen=True)
class BridgeScenarioResult:
    scenario_id: str
    scenario_fingerprint: str
    graph_fingerprint: str | None
    connected: bool
    failure_reason: str
    minimum_cost_nodes: tuple[str, ...]
    minimum_bottleneck_nodes: tuple[str, ...]
    cumulative_cost: float | None
    bottleneck_cost: float | None
    geographic_cost: float | None
    environmental_cost: float | None
    barrier_cost: float | None
    bridge_gain: float | None
    edge_disjoint_path_count: int | None


@dataclass(frozen=True)
class BridgeMetricSummary:
    p10: float
    median: float
    p90: float


@dataclass(frozen=True)
class BridgeSensitivityResult:
    source_id: str
    target_id: str
    scenario_count: int
    connected_count: int
    connected_frequency: float
    direct_edge_scenario_count: int
    positive_bridge_gain_count: int
    positive_bridge_gain_frequency: float | None
    minimum_cost_node_support: Mapping[str, float]
    minimum_bottleneck_node_support: Mapping[str, float]
    minimum_cost_edge_support: Mapping[str, float]
    metric_summaries: Mapping[str, BridgeMetricSummary]
    scenarios: tuple[BridgeScenarioResult, ...]
    fingerprint: str


def _scenario_payload(scenario: BridgeSensitivityScenario) -> dict[str, object]:
    return {
        "scenario_id": scenario.scenario_id,
        "declaration": scenario.declaration.__dict__,
        "weights": scenario.weights.__dict__,
        "barriers": sorted(
            (min(a, b), max(a, b), float(value)) for a, b, value in scenario.barriers
        ),
        "redundancy_threshold": scenario.redundancy_threshold,
    }


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _path_ids(inference: BridgeInference, graph_nodes: Sequence[BridgeNode], *, bottleneck: bool) -> tuple[str, ...]:
    path = inference.minimum_bottleneck_path if bottleneck else inference.minimum_cost_path
    return tuple(graph_nodes[index].node_id for index in path.nodes)


def _edge_keys(nodes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple("::".join(sorted((a, b))) for a, b in zip(nodes, nodes[1:]))


def _metric_summary(values: list[float]) -> BridgeMetricSummary:
    array = np.asarray(values, dtype=float)
    return BridgeMetricSummary(
        p10=float(np.quantile(array, 0.10)),
        median=float(np.quantile(array, 0.50)),
        p90=float(np.quantile(array, 0.90)),
    )


def evaluate_bridge_sensitivity(
    nodes: Sequence[BridgeNode],
    reference: RobustReference,
    scenarios: Sequence[BridgeSensitivityScenario],
    source_id: str,
    target_id: str,
) -> BridgeSensitivityResult:
    """Evaluate one source-target pair across a frozen scenario ensemble."""
    if source_id == target_id or not source_id.strip() or not target_id.strip():
        raise ValueError("source_id and target_id must be distinct non-empty IDs")
    ordered_scenarios = tuple(sorted(scenarios, key=lambda item: item.scenario_id))
    if not ordered_scenarios:
        raise ValueError("at least one sensitivity scenario is required")
    if len({scenario.scenario_id for scenario in ordered_scenarios}) != len(ordered_scenarios):
        raise ValueError("scenario IDs must be unique")

    results: list[BridgeScenarioResult] = []
    for scenario in ordered_scenarios:
        scenario_fp = _fingerprint(_scenario_payload(scenario))
        try:
            graph = build_bridge_graph(
                nodes,
                reference,
                scenario.declaration,
                barriers=scenario.barrier_mapping(),
            )
            if source_id not in graph.node_index or target_id not in graph.node_index:
                raise ValueError("source or target node ID is absent from the graph")
            inference = infer_bridge(
                len(graph.nodes),
                graph.edges,
                graph.node_index[source_id],
                graph.node_index[target_id],
                weights=scenario.weights,
                redundancy_threshold=scenario.redundancy_threshold,
            )
            shortest_ids = _path_ids(inference, graph.nodes, bottleneck=False)
            bottleneck_ids = _path_ids(inference, graph.nodes, bottleneck=True)
            path = inference.minimum_cost_path
            results.append(
                BridgeScenarioResult(
                    scenario_id=scenario.scenario_id,
                    scenario_fingerprint=scenario_fp,
                    graph_fingerprint=graph.fingerprint,
                    connected=True,
                    failure_reason="",
                    minimum_cost_nodes=shortest_ids,
                    minimum_bottleneck_nodes=bottleneck_ids,
                    cumulative_cost=path.cumulative_cost,
                    bottleneck_cost=inference.minimum_bottleneck_path.bottleneck_cost,
                    geographic_cost=path.geographic_cost,
                    environmental_cost=path.environmental_cost,
                    barrier_cost=path.barrier_cost,
                    bridge_gain=inference.bridge_gain,
                    edge_disjoint_path_count=inference.edge_disjoint_path_count,
                )
            )
        except ValueError as exc:
            results.append(
                BridgeScenarioResult(
                    scenario_id=scenario.scenario_id,
                    scenario_fingerprint=scenario_fp,
                    graph_fingerprint=None,
                    connected=False,
                    failure_reason=str(exc),
                    minimum_cost_nodes=(),
                    minimum_bottleneck_nodes=(),
                    cumulative_cost=None,
                    bottleneck_cost=None,
                    geographic_cost=None,
                    environmental_cost=None,
                    barrier_cost=None,
                    bridge_gain=None,
                    edge_disjoint_path_count=None,
                )
            )

    connected = [result for result in results if result.connected]
    denominator = len(results)
    connected_denominator = len(connected)

    def node_support(attribute: str) -> dict[str, float]:
        counts: dict[str, int] = {}
        for result in connected:
            path = getattr(result, attribute)
            for node_id in set(path[1:-1]):
                counts[node_id] = counts.get(node_id, 0) + 1
        return {
            node_id: count / connected_denominator
            for node_id, count in sorted(counts.items())
        } if connected_denominator else {}

    edge_counts: dict[str, int] = {}
    for result in connected:
        for edge in set(_edge_keys(result.minimum_cost_nodes)):
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    edge_support = {
        edge: count / connected_denominator for edge, count in sorted(edge_counts.items())
    } if connected_denominator else {}

    metric_names = (
        "cumulative_cost",
        "bottleneck_cost",
        "geographic_cost",
        "environmental_cost",
        "barrier_cost",
        "edge_disjoint_path_count",
    )
    summaries: dict[str, BridgeMetricSummary] = {}
    for name in metric_names:
        values = [float(getattr(result, name)) for result in connected if getattr(result, name) is not None]
        if values:
            summaries[name] = _metric_summary(values)

    direct_results = [result for result in connected if result.bridge_gain is not None]
    positive_count = sum(float(result.bridge_gain) > 0 for result in direct_results)
    positive_frequency = positive_count / len(direct_results) if direct_results else None

    payload = {
        "source_id": source_id,
        "target_id": target_id,
        "reference": reference.to_dict(),
        "scenarios": [result.__dict__ for result in results],
        "minimum_cost_node_support": node_support("minimum_cost_nodes"),
        "minimum_bottleneck_node_support": node_support("minimum_bottleneck_nodes"),
        "minimum_cost_edge_support": edge_support,
    }
    return BridgeSensitivityResult(
        source_id=source_id,
        target_id=target_id,
        scenario_count=denominator,
        connected_count=connected_denominator,
        connected_frequency=connected_denominator / denominator,
        direct_edge_scenario_count=len(direct_results),
        positive_bridge_gain_count=positive_count,
        positive_bridge_gain_frequency=positive_frequency,
        minimum_cost_node_support=node_support("minimum_cost_nodes"),
        minimum_bottleneck_node_support=node_support("minimum_bottleneck_nodes"),
        minimum_cost_edge_support=edge_support,
        metric_summaries=summaries,
        scenarios=tuple(results),
        fingerprint=_fingerprint(payload),
    )
