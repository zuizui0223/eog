"""Prospective noisy development screen for the experimental EOG distribution model.

This file is intentionally a *development* screen rather than a confirmation test.
The generator families, seeds and comparator definitions are declared in source before
their CI outcome is inspected. Directional performance is reported, but only leakage,
finite-output and bookkeeping invariants are hard-gated here. A later independent-seed
confirmation must freeze any promotion criteria before it runs.

Six regimes are represented:

- habitat_only: occurrence depends on local environment; structure is nuisance;
- dispersal_limited: source distance carries most structural information;
- graded_barrier: total path cost is matched while bottleneck concentration varies;
- stepping_stone: endpoints have matched environment/distance but only some paths exist;
- long_jump: environment dominates and source-distance limitation is deliberately weak;
- mixed: both local environment and bottleneck structure affect occurrence.

The comparator ladder is nested and leakage-safe:

1. environmental support only;
2. environmental support + nearest training-source distance;
3. environmental support + single-path cumulative graph cost;
4. EOG distribution support using cumulative + bottleneck accessibility and a
   training-fitted structural gate.

No frozen A-Islands or Tanzania outcome is read by this benchmark.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
import math

import numpy as np

from eog import (
    BridgeGraphDeclaration,
    BridgeNode,
    BridgeWeights,
    EOGDistributionConfig,
    fit_eog_distribution,
    fit_penalized_logistic_support,
    haversine_km,
)


DEVELOPMENT_SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
REGIMES = (
    "habitat_only",
    "dispersal_limited",
    "graded_barrier",
    "stepping_stone",
    "long_jump",
    "mixed",
)


@dataclass(frozen=True)
class SyntheticBundle:
    nodes: tuple[BridgeNode, ...]
    observed_ids: tuple[str, ...]
    observed_response: tuple[int, ...]
    gate_folds: tuple[str, ...]
    target_ids: tuple[str, ...]
    target_response: tuple[int, ...]
    barriers: dict[tuple[str, str], float]
    config: EOGDistributionConfig


def _sigmoid(value: float) -> float:
    value = float(np.clip(value, -30.0, 30.0))
    return float(1.0 / (1.0 + math.exp(-value)))


def _auc(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = scores[labels == 1]
    negatives = scores[labels == 0]
    if positives.size == 0 or negatives.size == 0:
        raise ValueError("AUC requires both target classes")
    comparison = positives[:, None] - negatives[None, :]
    return float(np.mean((comparison > 0).astype(float) + 0.5 * (comparison == 0)))


def _brier(labels: np.ndarray, scores: np.ndarray) -> float:
    labels = np.asarray(labels, dtype=float)
    scores = np.asarray(scores, dtype=float)
    return float(np.mean((scores - labels) ** 2))


def _clip_environment(value: float) -> float:
    return float(np.clip(value, 0.20, 0.98))


def _probability(regime: str, environment: float, structure: float) -> float:
    if regime == "habitat_only":
        eta = -3.2 + 5.5 * environment
    elif regime == "dispersal_limited":
        eta = -2.0 + 4.0 * structure + 0.5 * (environment - 0.75)
    elif regime == "graded_barrier":
        eta = -2.0 + 4.0 * structure + 0.5 * (environment - 0.75)
    elif regime == "stepping_stone":
        eta = -2.0 + 4.0 * structure + 0.5 * (environment - 0.75)
    elif regime == "long_jump":
        eta = -3.1 + 5.2 * environment + 0.4 * structure
    elif regime == "mixed":
        eta = -3.4 + 3.6 * environment + 2.8 * structure
    else:
        raise ValueError(f"unknown regime: {regime}")
    return _sigmoid(eta)


def _barrier_profile(total_cost: float, concentration: float, rng: np.random.Generator):
    """Return three costs with fixed total and controlled maximum concentration."""
    largest = total_cost * concentration
    remainder = max(0.0, total_cost - largest)
    values = [largest, remainder / 2.0, remainder / 2.0]
    rng.shuffle(values)
    return tuple(float(value) for value in values)


def _structure_draw(regime: str, rng: np.random.Generator):
    if regime in {"habitat_only", "graded_barrier", "mixed"}:
        concentration = float(rng.uniform(0.40, 0.95))
        structure = float(1.0 - (concentration - 0.40) / 0.55)
        return {
            "distance_deg": 0.50,
            "open_path": True,
            "structure": float(np.clip(structure, 0.0, 1.0)),
            "barrier_concentration": concentration,
        }
    if regime == "stepping_stone":
        open_path = bool(rng.integers(0, 2))
        return {
            "distance_deg": 0.50,
            "open_path": open_path,
            "structure": 1.0 if open_path else 0.0,
            "barrier_concentration": None,
        }
    if regime in {"dispersal_limited", "long_jump"}:
        distance_deg = float(rng.choice(np.asarray([0.36, 0.48, 0.60])))
        structure = float(1.0 - (distance_deg - 0.36) / 0.24)
        return {
            "distance_deg": distance_deg,
            "open_path": True,
            "structure": float(np.clip(structure, 0.0, 1.0)),
            "barrier_concentration": None,
        }
    raise ValueError(f"unknown regime: {regime}")


def _append_arm(
    *,
    nodes: list[BridgeNode],
    barriers: dict[tuple[str, str], float],
    prefix: str,
    side: str,
    latitude: float,
    environment_train: float,
    environment_target: float,
    draw: dict[str, object],
    regime: str,
    rng: np.random.Generator,
) -> tuple[str, str]:
    sign = 1.0 if side == "right" else -1.0
    distance_deg = float(draw["distance_deg"])
    train_id = f"{prefix}_{side}_train"
    target_id = f"{prefix}_{side}_target"

    if regime in {"dispersal_limited", "long_jump"}:
        positions = []
        step = 0.12
        position = step
        while position < distance_deg - 0.08:
            positions.append(position)
            position += step
        train_position = distance_deg - 0.02
    else:
        positions = [0.12, 0.24, 0.36]
        train_position = 0.48

    path_ids: list[str] = []
    for index, position in enumerate(positions):
        if regime == "stepping_stone" and not bool(draw["open_path"]) and index == 1:
            continue
        node_id = f"{prefix}_{side}_path_{index + 1}"
        path_ids.append(node_id)
        nodes.append(
            BridgeNode(
                node_id,
                latitude,
                sign * float(position),
                (0.72,),
            )
        )

    nodes.append(
        BridgeNode(
            train_id,
            latitude,
            sign * float(train_position),
            (float(environment_train),),
        )
    )
    nodes.append(
        BridgeNode(
            target_id,
            latitude,
            sign * float(distance_deg),
            (float(environment_target),),
        )
    )

    if regime in {"habitat_only", "graded_barrier", "mixed"}:
        total_cost = 2.4
        concentration = float(draw["barrier_concentration"])
        profile = _barrier_profile(total_cost, concentration, rng)
        expected_path = [
            f"{prefix}_{side}_path_1",
            f"{prefix}_{side}_path_2",
            f"{prefix}_{side}_path_3",
            train_id,
        ]
        for first, second, cost in zip(expected_path, expected_path[1:], profile):
            barriers[(first, second)] = float(cost)

    return train_id, target_id


def build_noisy_landscape(
    regime: str,
    seed: int,
    *,
    n_modules: int = 24,
) -> SyntheticBundle:
    if regime not in REGIMES:
        raise ValueError(f"unknown regime: {regime}")
    if n_modules < 8:
        raise ValueError("n_modules must be at least eight")

    rng = np.random.default_rng(seed)
    nodes: list[BridgeNode] = []
    observed_ids: list[str] = []
    observed_response: list[int] = []
    gate_folds: list[str] = []
    target_ids: list[str] = []
    target_response: list[int] = []
    barriers: dict[tuple[str, str], float] = {}

    for module in range(n_modules):
        latitude = -8.0 + module * 0.25
        prefix = f"m{module:02d}"
        source_a = f"{prefix}_source_a"
        source_b = f"{prefix}_source_b"
        nodes.extend(
            [
                BridgeNode(source_a, latitude + 0.003, 0.0, (0.85,)),
                BridgeNode(source_b, latitude - 0.003, 0.0, (0.85,)),
            ]
        )

        environment_right = float(rng.uniform(0.25, 0.95))
        environment_left = float(rng.uniform(0.25, 0.95))
        target_environment_right = _clip_environment(
            environment_right + float(rng.normal(0.0, 0.04))
        )
        target_environment_left = _clip_environment(
            environment_left + float(rng.normal(0.0, 0.04))
        )
        draw_right = _structure_draw(regime, rng)
        draw_left = _structure_draw(regime, rng)

        right_train, right_target = _append_arm(
            nodes=nodes,
            barriers=barriers,
            prefix=prefix,
            side="right",
            latitude=latitude,
            environment_train=environment_right,
            environment_target=target_environment_right,
            draw=draw_right,
            regime=regime,
            rng=rng,
        )
        left_train, left_target = _append_arm(
            nodes=nodes,
            barriers=barriers,
            prefix=prefix,
            side="left",
            latitude=latitude,
            environment_train=environment_left,
            environment_target=target_environment_left,
            draw=draw_left,
            regime=regime,
            rng=rng,
        )

        right_train_probability = _probability(
            regime, environment_right, float(draw_right["structure"])
        )
        left_train_probability = _probability(
            regime, environment_left, float(draw_left["structure"])
        )
        right_target_probability = _probability(
            regime, target_environment_right, float(draw_right["structure"])
        )
        left_target_probability = _probability(
            regime, target_environment_left, float(draw_left["structure"])
        )

        right_train_label = int(rng.random() < right_train_probability)
        left_train_label = int(rng.random() < left_train_probability)
        right_target_label = int(rng.random() < right_target_probability)
        left_target_label = int(rng.random() < left_target_probability)

        observed_ids.extend([source_a, right_train, source_b, left_train])
        observed_response.extend([1, right_train_label, 1, left_train_label])
        gate_folds.extend(["inner_a", "inner_a", "inner_b", "inner_b"])
        target_ids.extend([right_target, left_target])
        target_response.extend([right_target_label, left_target_label])

    if regime in {"dispersal_limited", "long_jump"}:
        bridge_weights = BridgeWeights(geographic=1.0, environmental=0.0, barrier=0.0)
    else:
        bridge_weights = BridgeWeights(geographic=0.0, environmental=0.0, barrier=1.0)

    return SyntheticBundle(
        nodes=tuple(nodes),
        observed_ids=tuple(observed_ids),
        observed_response=tuple(observed_response),
        gate_folds=tuple(gate_folds),
        target_ids=tuple(target_ids),
        target_response=tuple(target_response),
        barriers=barriers,
        config=EOGDistributionConfig(
            graph_declaration=BridgeGraphDeclaration(max_geographic_km=18.0),
            bridge_weights=bridge_weights,
            structural_gate_penalty=0.02,
            gate_grid_size=201,
            min_class_count=4,
        ),
    )


def _multi_source_cumulative(graph, source_indices, weights) -> np.ndarray:
    adjacency: list[list[tuple[int, float]]] = [[] for _ in graph.nodes]
    for edge in graph.edges:
        cost = edge.total(weights)
        adjacency[edge.source].append((edge.target, cost))
        adjacency[edge.target].append((edge.source, cost))
    distance = np.full(len(graph.nodes), np.inf, dtype=float)
    queue: list[tuple[float, int]] = []
    for source in sorted(set(int(value) for value in source_indices)):
        distance[source] = 0.0
        heapq.heappush(queue, (0.0, source))
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != distance[node]:
            continue
        for neighbour, edge_cost in adjacency[node]:
            candidate = cost + edge_cost
            if candidate < distance[neighbour]:
                distance[neighbour] = candidate
                heapq.heappush(queue, (candidate, neighbour))
    return distance


def _cost_feature(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    result = np.full(values.shape, 6.0, dtype=float)
    finite = np.isfinite(values)
    result[finite] = np.log1p(np.maximum(values[finite], 0.0))
    return result


def _fit_comparator_predictions(
    bundle: SyntheticBundle,
    model,
) -> dict[str, np.ndarray]:
    by_id = {node.node_id: node for node in bundle.nodes}
    ordered_nodes = model.graph.nodes
    node_index = model.graph.node_index
    predictors = np.asarray([node.environmental_state for node in ordered_nodes], dtype=float)
    observed_rows = np.asarray([node_index[node_id] for node_id in bundle.observed_ids], dtype=int)
    target_rows = np.asarray([node_index[node_id] for node_id in bundle.target_ids], dtype=int)
    response = np.asarray(bundle.observed_response, dtype=float)
    folds = np.asarray(bundle.gate_folds, dtype=object)

    oof_environment = np.full(len(bundle.observed_ids), np.nan, dtype=float)
    oof_distance = np.full(len(bundle.observed_ids), np.nan, dtype=float)
    oof_cumulative = np.full(len(bundle.observed_ids), np.nan, dtype=float)

    for fold in sorted(set(bundle.gate_folds)):
        test_mask = folds == fold
        train_mask = ~test_mask
        support = fit_penalized_logistic_support(
            predictors[observed_rows[train_mask]],
            response[train_mask],
            l2_penalty=bundle.config.l2_penalty,
            min_class_count=bundle.config.min_class_count,
        )
        oof_environment[test_mask] = support.predict_support(
            predictors[observed_rows[test_mask]]
        )

        source_ids = [
            node_id
            for node_id, label, keep in zip(
                bundle.observed_ids, response, train_mask
            )
            if keep and label == 1.0
        ]
        source_indices = [node_index[node_id] for node_id in source_ids]
        if not source_indices:
            raise ValueError("inner comparator fold has no positive source")

        for position in np.flatnonzero(test_mask):
            target_node = by_id[bundle.observed_ids[position]]
            oof_distance[position] = min(
                haversine_km(target_node, by_id[source_id]) for source_id in source_ids
            )

        cumulative = _multi_source_cumulative(
            model.graph,
            source_indices,
            bundle.config.bridge_weights,
        )
        oof_cumulative[test_mask] = cumulative[observed_rows[test_mask]]

    if (
        not np.isfinite(oof_environment).all()
        or not np.isfinite(oof_distance).all()
    ):
        raise ValueError("non-finite nested comparator inputs")

    distance_model = fit_penalized_logistic_support(
        np.column_stack([oof_environment, np.log1p(oof_distance)]),
        response,
        l2_penalty=1.0,
        min_class_count=4,
    )
    cumulative_model = fit_penalized_logistic_support(
        np.column_stack([oof_environment, _cost_feature(oof_cumulative)]),
        response,
        l2_penalty=1.0,
        min_class_count=4,
    )

    full_sources = list(model.source_node_ids)
    target_distance = np.asarray(
        [
            min(
                haversine_km(by_id[target_id], by_id[source_id])
                for source_id in full_sources
            )
            for target_id in bundle.target_ids
        ],
        dtype=float,
    )
    target_prediction = model.predict(bundle.target_ids)
    target_cumulative = model.prediction.minimum_cumulative_cost[target_rows]

    return {
        "environmental_support": target_prediction.environmental_support,
        "environmental_plus_nearest_source": distance_model.predict_support(
            np.column_stack(
                [target_prediction.environmental_support, np.log1p(target_distance)]
            )
        ),
        "environmental_plus_single_path": cumulative_model.predict_support(
            np.column_stack(
                [
                    target_prediction.environmental_support,
                    _cost_feature(target_cumulative),
                ]
            )
        ),
        "eog_distribution_support": target_prediction.distribution_support,
    }


def run_noisy_regime_development(
    *,
    seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
    n_modules: int = 24,
) -> dict[str, object]:
    per_regime: dict[str, list[dict[str, object]]] = {regime: [] for regime in REGIMES}
    integrity = {
        "all_target_labels_held_out": True,
        "all_gates_inner_cross_fitted": True,
        "all_scores_finite": True,
        "all_target_seeds_have_both_classes": True,
    }

    for regime in REGIMES:
        for seed in seeds:
            bundle = build_noisy_landscape(regime, seed, n_modules=n_modules)
            model = fit_eog_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                bundle.config,
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"noisy development {regime} seed {seed}",
            )
            scores = _fit_comparator_predictions(bundle, model)
            labels = np.asarray(bundle.target_response, dtype=int)
            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_gates_inner_cross_fitted"] &= bool(
                model.structural_gate_cross_fitted
            )
            integrity["all_scores_finite"] &= all(
                np.isfinite(np.asarray(values, dtype=float)).all()
                for values in scores.values()
            )
            integrity["all_target_seeds_have_both_classes"] &= bool(
                np.any(labels == 1) and np.any(labels == 0)
            )
            per_regime[regime].append(
                {
                    "seed": seed,
                    "structural_gate_weight": model.structural_gate_weight,
                    "training_gate_log_loss": model.training_gate_log_loss,
                    "auc": {name: _auc(labels, values) for name, values in scores.items()},
                    "brier": {
                        name: _brier(labels, values) for name, values in scores.items()
                    },
                    "n_positive_targets": int(np.sum(labels == 1)),
                    "n_negative_targets": int(np.sum(labels == 0)),
                }
            )

    summary: dict[str, object] = {}
    for regime, rows in per_regime.items():
        methods = tuple(rows[0]["auc"])
        summary[regime] = {
            "mean_structural_gate_weight": float(
                np.mean([row["structural_gate_weight"] for row in rows])
            ),
            "sd_structural_gate_weight": float(
                np.std([row["structural_gate_weight"] for row in rows], ddof=0)
            ),
            "mean_auc": {
                method: float(np.mean([row["auc"][method] for row in rows]))
                for method in methods
            },
            "sd_auc": {
                method: float(np.std([row["auc"][method] for row in rows], ddof=0))
                for method in methods
            },
            "mean_brier": {
                method: float(np.mean([row["brier"][method] for row in rows]))
                for method in methods
            },
        }

    return {
        "schema": "eog_distribution_noisy_regime_development_v0_1",
        "status": "development_screen_not_confirmation",
        "seeds": list(seeds),
        "n_modules_per_seed": n_modules,
        "regimes": list(REGIMES),
        "comparator_order": [
            "environmental_support",
            "environmental_plus_nearest_source",
            "environmental_plus_single_path",
            "eog_distribution_support",
        ],
        "integrity_checks": integrity,
        "all_integrity_checks_pass": bool(all(integrity.values())),
        "summary": summary,
        "per_regime": per_regime,
        "claim_boundary": (
            "prospective noisy development screen only; performance may guide a later "
            "algorithm freeze, but no regime-specific superiority claim is confirmatory "
            "until an independent-seed benchmark with predeclared promotion gates passes"
        ),
    }


def main() -> None:
    result = run_noisy_regime_development()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_integrity_checks_pass"]:
        raise SystemExit("noisy EOG distribution development screen failed integrity checks")


if __name__ == "__main__":
    main()
