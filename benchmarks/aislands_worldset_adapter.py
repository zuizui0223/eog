#!/usr/bin/env python3
"""Response-free world-set view of the frozen A-Islands graph scenarios.

This benchmark-layer adapter exposes the 12 predeclared A-Islands reachability scenarios
as explicit analyst-choice worlds instead of immediately averaging them into connected
frequency.  It does not use held-out incidence labels and does not alter the frozen
A-Islands estimand or authoritative benchmark outputs.

The adapter is intentionally not part of the public EOG API.  It is an exploratory
representation used to ask whether preserving scenario/world identity is informative
before any new empirical promotion claim is considered.
"""
from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np

from eog.island_reachability import IslandReachabilityResult
from eog.prepared_island_connectivity import PreparedIslandConnectivity


WORLD_CLASSES = ("robust", "contingent", "excluded_under_declared_scenarios")


def _world_class(support_count: int, total_count: int) -> str:
    if total_count <= 0:
        raise ValueError("world family must contain at least one scenario")
    if support_count < 0 or support_count > total_count:
        raise ValueError("support_count must lie within the declared world family")
    if support_count == total_count:
        return "robust"
    if support_count == 0:
        return "excluded_under_declared_scenarios"
    return "contingent"


def _reach_matrix_from_prepared(
    prepared: PreparedIslandConnectivity,
    anchor_mask: Sequence[bool],
) -> np.ndarray:
    anchors = np.asarray(anchor_mask, dtype=bool)
    n_nodes = len(prepared.node_ids)
    if anchors.shape != (n_nodes,) or not np.any(anchors):
        raise ValueError("anchor_mask must align and contain at least one training anchor")

    reach = np.zeros((len(prepared.scenario_ids), n_nodes), dtype=bool)
    for scenario_index, labels in enumerate(prepared.component_labels):
        anchor_components = np.unique(labels[anchors])
        reach[scenario_index] = np.isin(labels, anchor_components)
    return reach


def _reach_matrix_from_full(result: IslandReachabilityResult) -> tuple[tuple[str, ...], np.ndarray]:
    scenario_ids = tuple(scenario.scenario_id for scenario in result.scenarios)
    if not scenario_ids:
        raise ValueError("full reachability result contains no declared scenarios")
    reach = np.vstack([np.asarray(scenario.reachable, dtype=bool) for scenario in result.scenarios])
    if reach.shape[1] != len(result.node_ids):
        raise ValueError("scenario reachability rows do not align with node IDs")
    return scenario_ids, reach


def _rows_from_matrix(
    node_ids: Sequence[str],
    scenario_ids: Sequence[str],
    reach_matrix: np.ndarray,
) -> list[dict[str, object]]:
    ids = tuple(str(value) for value in node_ids)
    scenarios = tuple(str(value) for value in scenario_ids)
    reach = np.asarray(reach_matrix, dtype=bool)
    if reach.shape != (len(scenarios), len(ids)):
        raise ValueError("reach_matrix must be scenario-by-node")
    if not scenarios or len(set(scenarios)) != len(scenarios):
        raise ValueError("scenario_ids must be non-empty and unique")

    geo_indices = [i for i, scenario_id in enumerate(scenarios) if scenario_id.endswith("env_none")]
    env_indices = [i for i, scenario_id in enumerate(scenarios) if not scenario_id.endswith("env_none")]
    if not geo_indices or not env_indices:
        raise ValueError("declared scenarios must include geography-only and environmental worlds")

    rows: list[dict[str, object]] = []
    for node_index, node_id in enumerate(ids):
        supported = tuple(sorted(scenarios[i] for i in range(len(scenarios)) if reach[i, node_index]))
        unsupported = tuple(sorted(scenarios[i] for i in range(len(scenarios)) if not reach[i, node_index]))
        geo_supported = tuple(sorted(scenarios[i] for i in geo_indices if reach[i, node_index]))
        env_supported = tuple(sorted(scenarios[i] for i in env_indices if reach[i, node_index]))
        total = len(scenarios)
        rows.append(
            {
                "node_id": node_id,
                "supporting_world_ids": supported,
                "unsupported_world_ids": unsupported,
                "support_count": len(supported),
                "world_count": total,
                "connected_frequency": len(supported) / total,
                "world_class": _world_class(len(supported), total),
                "geography_supporting_world_ids": geo_supported,
                "geography_support_count": len(geo_supported),
                "geography_world_count": len(geo_indices),
                "geography_connected_frequency": len(geo_supported) / len(geo_indices),
                "geography_world_class": _world_class(len(geo_supported), len(geo_indices)),
                "environment_supporting_world_ids": env_supported,
                "environment_support_count": len(env_supported),
                "environment_world_count": len(env_indices),
                "environment_connected_frequency": len(env_supported) / len(env_indices),
                "environment_world_class": _world_class(len(env_supported), len(env_indices)),
                "geo_environment_class_disagreement": (
                    _world_class(len(geo_supported), len(geo_indices))
                    != _world_class(len(env_supported), len(env_indices))
                ),
            }
        )
    return rows


def worldset_from_prepared(
    prepared: PreparedIslandConnectivity,
    anchor_mask: Sequence[bool],
) -> list[dict[str, object]]:
    """Recover explicit scenario-world support from prepared fold geometry."""

    reach = _reach_matrix_from_prepared(prepared, anchor_mask)
    return _rows_from_matrix(prepared.node_ids, prepared.scenario_ids, reach)


def worldset_from_full(result: IslandReachabilityResult) -> list[dict[str, object]]:
    """Expose the same scenario-world support from the full frozen evaluator."""

    scenario_ids, reach = _reach_matrix_from_full(result)
    return _rows_from_matrix(result.node_ids, scenario_ids, reach)


def summarize_worldset(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    declared = list(rows)
    if not declared:
        raise ValueError("at least one node row is required")
    class_counts = Counter(str(row["world_class"]) for row in declared)
    support_counts = Counter(int(row["support_count"]) for row in declared)
    disagreement = sum(bool(row["geo_environment_class_disagreement"]) for row in declared)
    return {
        "n_nodes": len(declared),
        "world_count": int(declared[0]["world_count"]),
        "class_counts": {key: int(class_counts.get(key, 0)) for key in WORLD_CLASSES},
        "support_count_distribution": {
            str(key): int(value) for key, value in sorted(support_counts.items())
        },
        "geo_environment_class_disagreement_count": int(disagreement),
    }
