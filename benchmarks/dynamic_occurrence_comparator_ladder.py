"""Prospective occurrence-comparator ladder for EOG v2.

This synthetic benchmark isolates the source-conditioned estimand with a frozen set of
known occurrence sources and spatially held-out candidate islands. Development seeds were
used to choose the motifs and gates. Confirmation seeds are separate and must not be
changed after this contract is committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
)

DEVELOPMENT_SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
CONFIRMATION_SEEDS = (907, 1009, 1103, 1201, 1301, 1409, 1511, 1601)
REGIMES = (
    "environment_only",
    "nearest_source",
    "source_pressure",
    "currentflow",
    "static_topology",
    "dynamic_bottleneck",
    "dynamic_directional",
)
MODELS = (
    "environment",
    "env_nearest",
    "env_pressure",
    "env_currentflow",
    "env_static",
    "env_dynamic",
    "env_currentflow_dynamic",
    "env_static_dynamic",
)
N_MOTIFS = 48
N_FOLDS = 6
L2_PENALTY = 1.0
SOURCE_SCALE = 1.6
STATIC_THRESHOLDS = (0.05, 0.10, 0.15, 0.20)
DYNAMIC_MAX_STEPS = 5
DYNAMIC_LOSS_SUPPORT = 0.55
MIN_REQUIRED_SIGNAL = 0.05
MAX_ALLOWED_EXTRA_GAIN = 0.01
MIN_DYNAMIC_FAVOURABLE_SEEDS = 6


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-values))


def _zscore(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    scale = float(np.std(array))
    return np.zeros_like(array) if scale <= 0.0 else (array - np.mean(array)) / scale


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _nearest_distance(coordinates: np.ndarray, sources: Sequence[int]) -> np.ndarray:
    source_coordinates = coordinates[np.asarray(sources, dtype=int)]
    distance = np.linalg.norm(
        coordinates[:, None, :] - source_coordinates[None, :, :], axis=2
    )
    return np.min(distance, axis=1)


def _source_pressure(
    coordinates: np.ndarray, sources: Sequence[int], *, scale: float
) -> np.ndarray:
    source_coordinates = coordinates[np.asarray(sources, dtype=int)]
    distance = np.linalg.norm(
        coordinates[:, None, :] - source_coordinates[None, :, :], axis=2
    )
    return np.sum(np.exp(-distance / scale), axis=1)


def _components(adjacency: np.ndarray) -> list[list[int]]:
    seen = np.zeros(adjacency.shape[0], dtype=bool)
    output: list[list[int]] = []
    for start in range(adjacency.shape[0]):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in np.flatnonzero(adjacency[node]):
                value = int(neighbour)
                if not seen[value]:
                    seen[value] = True
                    stack.append(value)
        output.append(component)
    return output


def _currentflow_support(conductance: np.ndarray, sources: Sequence[int]) -> np.ndarray:
    """Geography-only effective-resistance support to a grounded source set."""
    output = np.zeros(conductance.shape[0], dtype=float)
    source_set = set(int(value) for value in sources)
    symmetric = 0.5 * (conductance + conductance.T)
    for component in _components(symmetric > 0.0):
        grounded = [node for node in component if node in source_set]
        if not grounded:
            continue
        non_sources = [node for node in component if node not in source_set]
        output[grounded] = 1.0
        if not non_sources:
            continue
        sub = symmetric[np.ix_(component, component)]
        laplacian = np.diag(np.sum(sub, axis=1)) - sub
        position = {node: index for index, node in enumerate(component)}
        reduced_indices = [position[node] for node in non_sources]
        reduced = laplacian[np.ix_(reduced_indices, reduced_indices)]
        resistance = np.diag(np.linalg.inv(reduced))
        for node, value in zip(non_sources, resistance):
            output[node] = 1.0 / (1.0 + float(value))
    return output


def _static_connected_frequency(
    raw_support: np.ndarray, sources: Sequence[int], thresholds: Sequence[float]
) -> np.ndarray:
    output = np.zeros(raw_support.shape[0], dtype=float)
    undirected = np.maximum(raw_support, raw_support.T)
    for threshold in thresholds:
        adjacency = undirected >= float(threshold)
        seen = set(int(value) for value in sources)
        stack = list(seen)
        while stack:
            node = stack.pop()
            for neighbour in np.flatnonzero(adjacency[node]):
                value = int(neighbour)
                if value not in seen:
                    seen.add(value)
                    stack.append(value)
        output[list(seen)] += 1.0
    return output / float(len(tuple(thresholds)))


def _dynamic_support(raw_support: np.ndarray, sources: Sequence[int]) -> np.ndarray:
    node_ids = tuple(f"node_{index:04d}" for index in range(raw_support.shape[0]))
    edges = [
        DynamicReachabilityEdge(
            int(source),
            int(target),
            geographic_support=float(raw_support[source, target]),
        )
        for source, target in zip(*np.nonzero(raw_support > 0.0))
    ]
    operator = build_dynamic_transition_operator(
        node_ids, edges, loss_support=DYNAMIC_LOSS_SUPPORT
    )
    result = propagate_dynamic_reachability(
        operator,
        [node_ids[index] for index in sources],
        max_steps=DYNAMIC_MAX_STEPS,
    )
    return result.integrated_node_support


def _ridge_logistic_fit(
    predictors: np.ndarray, response: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(response, dtype=float)
    mean = np.mean(x, axis=0)
    scale = np.where(np.std(x, axis=0) > 1e-12, np.std(x, axis=0), 1.0)
    z = (x - mean) / scale
    design = np.column_stack([np.ones(len(y), dtype=float), z])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.concatenate([[0.0], np.full(x.shape[1], L2_PENALTY)])

    def objective(value: np.ndarray) -> float:
        eta = design @ value
        loss = np.logaddexp(0.0, eta) - y * eta
        return float(
            np.sum(loss) + 0.5 * L2_PENALTY * np.dot(value[1:], value[1:])
        )

    current = objective(beta)
    for _ in range(200):
        probability = _sigmoid(design @ beta)
        weights = probability * (1.0 - probability)
        gradient = design.T @ (probability - y) + penalty * beta
        hessian = design.T @ (design * weights[:, None])
        hessian += np.diag(penalty) + np.eye(hessian.shape[0]) * 1e-12
        step = np.linalg.solve(hessian, gradient)
        step_scale = 1.0
        accepted = False
        while step_scale >= 2.0 ** -20:
            candidate = beta - step_scale * step
            candidate_objective = objective(candidate)
            if candidate_objective <= current + 1e-12:
                improvement = current - candidate_objective
                beta = candidate
                current = candidate_objective
                accepted = True
                break
            step_scale *= 0.5
        if not accepted:
            raise RuntimeError("ridge logistic update failed")
        if np.max(np.abs(step_scale * step)) <= 1e-9 or improvement <= 1e-9:
            break
    return mean, scale, beta


def _ridge_logistic_predict(
    model: tuple[np.ndarray, np.ndarray, np.ndarray], predictors: np.ndarray
) -> np.ndarray:
    mean, scale, beta = model
    z = (np.asarray(predictors, dtype=float) - mean) / scale
    design = np.column_stack([np.ones(len(z), dtype=float), z])
    return _sigmoid(design @ beta)


def _log_loss(response: np.ndarray, probability: np.ndarray) -> float:
    p = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))))


def _brier(response: np.ndarray, probability: np.ndarray) -> float:
    return float(np.mean((np.asarray(response, dtype=float) - probability) ** 2))


def _auc(response: np.ndarray, score: np.ndarray) -> float | None:
    y = np.asarray(response, dtype=int)
    s = np.asarray(score, dtype=float)
    positive = s[y == 1]
    negative = s[y == 0]
    if not len(positive) or not len(negative):
        return None
    greater = np.mean(positive[:, None] > negative[None, :])
    ties = np.mean(positive[:, None] == negative[None, :])
    return float(greater + 0.5 * ties)


def _build_motifs(regime: str) -> dict[str, object]:
    coordinates: list[tuple[float, float]] = []
    viability: list[float] = []
    source_nodes: list[int] = []
    target_nodes: list[int] = []
    motif_ids: list[int] = []
    geographic_edges: list[tuple[int, int, float]] = []
    raw_edges: list[tuple[int, int, float]] = []
    spacing = 12.0

    for motif in range(N_MOTIFS):
        x0 = float(motif % N_FOLDS) * spacing
        y0 = float(motif // N_FOLDS) * spacing
        level = (motif // N_FOLDS) % 4
        target_dx = (2.4, 3.0, 3.6, 4.2)[level] if regime == "nearest_source" else 3.0
        start = len(coordinates)
        coordinates.extend(
            [(x0, y0), (x0 + 1.0, y0), (x0 + 2.0, y0), (x0 + target_dx, y0)]
        )
        target_viability = 0.12 + 0.76 * float(
            _sigmoid(
                np.asarray(
                    [1.2 * np.sin(0.9 * motif) + 0.5 * np.cos(1.7 * motif)]
                )
            )[0]
        )
        viability.extend([0.5, 0.5, 0.5, target_viability])
        source, step1, step2, target = [start + offset for offset in range(4)]
        source_nodes.append(source)
        target_nodes.append(target)
        motif_ids.append(motif)
        for a, b in ((source, step1), (step1, step2), (step2, target)):
            geographic_edges.append((a, b, 0.8))

        raw_local: dict[tuple[int, int], float] = {
            (source, step1): 0.70,
            (step1, source): 0.70,
            (step1, step2): 0.70,
            (step2, step1): 0.70,
            (step2, target): 0.70,
            (target, step2): 0.70,
        }

        if regime == "source_pressure":
            if level in (1, 3):
                second_source = len(coordinates)
                coordinates.append((x0 + target_dx, y0 + 3.0))
                viability.append(0.5)
                source_nodes.append(second_source)
        elif regime == "currentflow":
            for alternative in range(level):
                first = len(coordinates)
                second = first + 1
                offset = 0.35 * float(alternative + 1)
                coordinates.extend(
                    [(x0 + 1.0, y0 + offset), (x0 + 2.0, y0 + offset)]
                )
                viability.extend([0.5, 0.5])
                for a, b in ((source, first), (first, second), (second, target)):
                    geographic_edges.append((a, b, 0.8))
                    raw_local[(a, b)] = 0.70
                    raw_local[(b, a)] = 0.70
        elif regime == "static_topology":
            middle = (0.0, 0.12, 0.32, 0.32)[level]
            raw_local[(step1, step2)] = middle
            raw_local[(step2, step1)] = middle
        elif regime == "dynamic_bottleneck":
            middle = (0.22, 0.30, 0.42, 0.70)[level]
            raw_local[(step1, step2)] = middle
            raw_local[(step2, step1)] = middle
        elif regime == "dynamic_directional":
            forward = (0.05, 0.15, 0.35, 0.70)[level]
            raw_local[(source, step1)] = forward
            raw_local[(step1, step2)] = forward
            raw_local[(step2, target)] = forward
            raw_local[(step1, source)] = 0.70
            raw_local[(step2, step1)] = 0.70
            raw_local[(target, step2)] = 0.70
        elif regime in ("environment_only", "nearest_source"):
            pass
        else:
            raise ValueError(f"unknown comparator regime: {regime}")

        for (a, b), support in raw_local.items():
            raw_edges.append((a, b, float(support)))

    coordinate_array = np.asarray(coordinates, dtype=float)
    viability_array = np.asarray(viability, dtype=float)
    n_nodes = len(coordinate_array)
    geographic = np.zeros((n_nodes, n_nodes), dtype=float)
    raw = np.zeros((n_nodes, n_nodes), dtype=float)
    for a, b, value in geographic_edges:
        geographic[a, b] = value
        geographic[b, a] = value
    for a, b, value in raw_edges:
        raw[a, b] = value

    return {
        "coordinates": coordinate_array,
        "viability": viability_array,
        "geographic": geographic,
        "raw": raw,
        "sources": tuple(sorted(set(source_nodes))),
        "targets": np.asarray(target_nodes, dtype=int),
        "motif_ids": np.asarray(motif_ids, dtype=int),
    }


def _predictor_sets(regime: str) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    design = _build_motifs(regime)
    coordinates = design["coordinates"]
    viability = design["viability"]
    geographic = design["geographic"]
    raw = design["raw"]
    sources = design["sources"]
    targets = design["targets"]

    nearest = np.exp(-_nearest_distance(coordinates, sources) / SOURCE_SCALE)
    pressure = _source_pressure(coordinates, sources, scale=SOURCE_SCALE)
    currentflow = _currentflow_support(geographic, sources)
    static = _static_connected_frequency(raw, sources, STATIC_THRESHOLDS)
    dynamic = _dynamic_support(raw, sources)
    target_viability = viability[targets]

    feature = {
        "environment": target_viability[:, None],
        "env_nearest": np.column_stack([target_viability, nearest[targets]]),
        "env_pressure": np.column_stack([target_viability, pressure[targets]]),
        "env_currentflow": np.column_stack([target_viability, currentflow[targets]]),
        "env_static": np.column_stack([target_viability, static[targets]]),
        "env_dynamic": np.column_stack([target_viability, dynamic[targets]]),
        "env_currentflow_dynamic": np.column_stack(
            [target_viability, currentflow[targets], dynamic[targets]]
        ),
        "env_static_dynamic": np.column_stack(
            [target_viability, static[targets], dynamic[targets]]
        ),
    }
    truth = {
        "viability": target_viability,
        "nearest": nearest[targets],
        "pressure": pressure[targets],
        "currentflow": currentflow[targets],
        "static": static[targets],
        "dynamic": dynamic[targets],
        "motif_ids": design["motif_ids"],
    }
    return feature, truth


def _truth_probability(regime: str, truth: dict[str, np.ndarray]) -> np.ndarray:
    viability = truth["viability"]
    if regime == "environment_only":
        eta = -0.15 + 1.50 * _zscore(viability)
    elif regime == "nearest_source":
        eta = -0.35 + 0.50 * _zscore(viability) + 1.70 * _zscore(truth["nearest"])
    elif regime == "source_pressure":
        eta = -0.35 + 0.50 * _zscore(viability) + 1.70 * _zscore(truth["pressure"])
    elif regime == "currentflow":
        eta = -0.35 + 0.45 * _zscore(viability) + 1.80 * _zscore(truth["currentflow"])
    elif regime == "static_topology":
        eta = -0.35 + 0.45 * _zscore(viability) + 1.90 * _zscore(truth["static"])
    elif regime == "dynamic_bottleneck":
        eta = -0.35 + 0.45 * _zscore(viability) + 2.00 * _zscore(
            np.log(truth["dynamic"] + 1e-6)
        )
    elif regime == "dynamic_directional":
        eta = -0.35 + 0.45 * _zscore(viability) + 2.00 * _zscore(
            np.log(truth["dynamic"] + 1e-8)
        )
    else:
        raise ValueError(regime)
    return _sigmoid(eta)


def _evaluate_seed(regime: str, seed: int) -> dict[str, object]:
    predictors, truth = _predictor_sets(regime)
    probability = _truth_probability(regime, truth)
    rng = np.random.default_rng(seed)
    response = (rng.random(len(probability)) < probability).astype(int)
    folds = truth["motif_ids"] % N_FOLDS
    prediction = {name: np.full(len(response), np.nan, dtype=float) for name in MODELS}

    for fold in range(N_FOLDS):
        test = folds == fold
        train = ~test
        if len(np.unique(response[train])) < 2:
            raise RuntimeError(
                f"one-class training fold for regime={regime} seed={seed} fold={fold}"
            )
        for name in MODELS:
            model = _ridge_logistic_fit(predictors[name][train], response[train])
            prediction[name][test] = _ridge_logistic_predict(
                model, predictors[name][test]
            )

    result: dict[str, object] = {
        "seed": int(seed),
        "prevalence": float(np.mean(response)),
        "n_targets": int(len(response)),
        "models": {},
    }
    for name in MODELS:
        score = prediction[name]
        if not np.isfinite(score).all():
            raise RuntimeError(f"non-estimable prediction for {regime}/{seed}/{name}")
        result["models"][name] = {
            "log_loss": _log_loss(response, score),
            "brier": _brier(response, score),
            "auc": _auc(response, score),
        }
    return result


def _aggregate(regime: str, seeds: Sequence[int]) -> dict[str, object]:
    rows = [_evaluate_seed(regime, int(seed)) for seed in seeds]
    summary: dict[str, object] = {
        "regime": regime,
        "seeds": [int(seed) for seed in seeds],
        "rows": rows,
        "mean_prevalence": float(np.mean([row["prevalence"] for row in rows])),
        "models": {},
    }
    for name in MODELS:
        log_loss = [row["models"][name]["log_loss"] for row in rows]
        brier = [row["models"][name]["brier"] for row in rows]
        auc_values = [row["models"][name]["auc"] for row in rows]
        finite_auc = [value for value in auc_values if value is not None]
        summary["models"][name] = {
            "mean_log_loss": float(np.mean(log_loss)),
            "mean_brier": float(np.mean(brier)),
            "mean_auc": None if not finite_auc else float(np.mean(finite_auc)),
        }
    return summary


def _confirmation_decision(regimes: dict[str, dict[str, object]]) -> dict[str, object]:
    def loss(regime: str, model: str) -> float:
        return float(regimes[regime]["models"][model]["mean_log_loss"])

    checks: dict[str, dict[str, object]] = {}

    def add(name: str, value: float, relation: str, threshold: float, passed: bool) -> None:
        checks[name] = {
            "value": float(value),
            "relation": relation,
            "threshold": float(threshold),
            "passed": bool(passed),
        }

    delta = loss("environment_only", "env_dynamic") - loss(
        "environment_only", "environment"
    )
    add(
        "environment_null_dynamic_increment",
        delta,
        ">=",
        -MAX_ALLOWED_EXTRA_GAIN,
        delta >= -MAX_ALLOWED_EXTRA_GAIN,
    )

    nearest_gain = loss("nearest_source", "environment") - loss(
        "nearest_source", "env_nearest"
    )
    add(
        "nearest_source_signal",
        nearest_gain,
        ">=",
        MIN_REQUIRED_SIGNAL,
        nearest_gain >= MIN_REQUIRED_SIGNAL,
    )
    delta = loss("nearest_source", "env_dynamic") - loss(
        "nearest_source", "env_nearest"
    )
    add(
        "nearest_source_dynamic_increment",
        delta,
        ">=",
        -MAX_ALLOWED_EXTRA_GAIN,
        delta >= -MAX_ALLOWED_EXTRA_GAIN,
    )

    pressure_gain = loss("source_pressure", "environment") - loss(
        "source_pressure", "env_pressure"
    )
    add(
        "source_pressure_signal",
        pressure_gain,
        ">=",
        MIN_REQUIRED_SIGNAL,
        pressure_gain >= MIN_REQUIRED_SIGNAL,
    )
    delta = loss("source_pressure", "env_dynamic") - loss(
        "source_pressure", "env_pressure"
    )
    add(
        "source_pressure_dynamic_increment",
        delta,
        ">=",
        -MAX_ALLOWED_EXTRA_GAIN,
        delta >= -MAX_ALLOWED_EXTRA_GAIN,
    )

    current_gain = loss("currentflow", "environment") - loss(
        "currentflow", "env_currentflow"
    )
    add(
        "currentflow_signal",
        current_gain,
        ">=",
        MIN_REQUIRED_SIGNAL,
        current_gain >= MIN_REQUIRED_SIGNAL,
    )
    delta = loss("currentflow", "env_currentflow_dynamic") - loss(
        "currentflow", "env_currentflow"
    )
    add(
        "currentflow_dynamic_increment",
        delta,
        ">=",
        -MAX_ALLOWED_EXTRA_GAIN,
        delta >= -MAX_ALLOWED_EXTRA_GAIN,
    )

    static_gain = loss("static_topology", "environment") - loss(
        "static_topology", "env_static"
    )
    add(
        "static_topology_signal",
        static_gain,
        ">=",
        MIN_REQUIRED_SIGNAL,
        static_gain >= MIN_REQUIRED_SIGNAL,
    )
    delta = loss("static_topology", "env_static_dynamic") - loss(
        "static_topology", "env_static"
    )
    add(
        "static_topology_dynamic_increment",
        delta,
        ">=",
        -MAX_ALLOWED_EXTRA_GAIN,
        delta >= -MAX_ALLOWED_EXTRA_GAIN,
    )

    simple = (
        "environment",
        "env_nearest",
        "env_pressure",
        "env_currentflow",
        "env_static",
    )
    for regime in ("dynamic_bottleneck", "dynamic_directional"):
        best_simple = min(loss(regime, name) for name in simple)
        gain = best_simple - loss(regime, "env_dynamic")
        add(
            f"{regime}_dynamic_signal",
            gain,
            ">=",
            MIN_REQUIRED_SIGNAL,
            gain >= MIN_REQUIRED_SIGNAL,
        )
        favourable = 0
        for row in regimes[regime]["rows"]:
            row_best = min(
                float(row["models"][name]["log_loss"]) for name in simple
            )
            if float(row["models"]["env_dynamic"]["log_loss"]) < row_best:
                favourable += 1
        checks[f"{regime}_favourable_seed_count"] = {
            "value": int(favourable),
            "relation": ">=",
            "threshold": int(MIN_DYNAMIC_FAVOURABLE_SEEDS),
            "passed": bool(favourable >= MIN_DYNAMIC_FAVOURABLE_SEEDS),
        }

    return {
        "passed": bool(all(check["passed"] for check in checks.values())),
        "checks": checks,
    }


def _contract() -> dict[str, object]:
    return {
        "status": "occurrence_comparator_confirmation_frozen_before_confirmation_outcomes",
        "development_seeds": list(DEVELOPMENT_SEEDS),
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "regimes": list(REGIMES),
        "models": list(MODELS),
        "n_motifs": N_MOTIFS,
        "n_spatial_folds": N_FOLDS,
        "source_scale": SOURCE_SCALE,
        "static_thresholds": list(STATIC_THRESHOLDS),
        "dynamic_max_steps": DYNAMIC_MAX_STEPS,
        "dynamic_loss_support": DYNAMIC_LOSS_SUPPORT,
        "l2_penalty": L2_PENALTY,
        "minimum_required_signal_log_loss": MIN_REQUIRED_SIGNAL,
        "maximum_allowed_extra_gain_log_loss": MAX_ALLOWED_EXTRA_GAIN,
        "minimum_dynamic_favourable_seeds": MIN_DYNAMIC_FAVOURABLE_SEEDS,
        "source_policy": (
            "designated known occurrence source nodes are frozen before target outcomes; "
            "target labels never enter source construction in this benchmark"
        ),
        "scope": (
            "synthetic estimand/reference-depth confirmation only; source-set expansion "
            "from additional training positives is a separate later sensitivity"
        ),
    }


def run(phase: str) -> dict[str, object]:
    if phase not in {"development", "confirmation", "both"}:
        raise ValueError("phase must be development, confirmation, or both")
    contract = _contract()
    output: dict[str, object] = {
        "contract": contract,
        "contract_fingerprint": _canonical_sha256(contract),
    }
    if phase in {"development", "both"}:
        output["development"] = {
            regime: _aggregate(regime, DEVELOPMENT_SEEDS) for regime in REGIMES
        }
    if phase in {"confirmation", "both"}:
        confirmation = {
            regime: _aggregate(regime, CONFIRMATION_SEEDS) for regime in REGIMES
        }
        output["confirmation"] = confirmation
        output["decision"] = _confirmation_decision(confirmation)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("development", "confirmation", "both"),
        default="development",
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run(args.phase)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
