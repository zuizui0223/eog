"""Dynamic-occupancy reference boundary for prospective EOG v2.

This development benchmark creates repeated island incidence from a correctly specified
first-order colonisation/persistence process. It asks whether a process reference that
uses the observed previous state and current neighbour pressure should retain primacy
over static source-conditioned EOG-R support when that process generated the truth.

This is a negative-control/reference-depth benchmark, not evidence that dynamic
occupancy is universally superior or that EOG-R is unnecessary when repeated incidence
is unavailable.
"""
from __future__ import annotations

import json

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
    propagate_dynamic_reachability,
)

SEEDS = (101, 211, 307, 401, 503, 601, 701, 809)
N_MOTIFS = 48
N_FOLDS = 6
N_TIME_STEPS = 10
LOSS_SUPPORT = 0.55
STATIC_MAX_STEPS = 5
L2_PENALTY = 1.0

MIN_PROCESS_GAIN_OVER_STATE_ENV = 0.03
MIN_PROCESS_GAIN_OVER_STATIC_EOG = 0.02
MAX_ALLOWED_EOG_GAIN_OVER_PROCESS = 0.005
MIN_PROCESS_FAVOURABLE_SEEDS = 6

MODELS = (
    "state_environment",
    "state_environment_eog",
    "dynamic_occupancy",
    "dynamic_occupancy_eog",
)


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-values))


def _ridge_logistic_fit(
    predictors: np.ndarray, response: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = np.asarray(predictors, dtype=float)
    y = np.asarray(response, dtype=float)
    mean = np.mean(x, axis=0)
    standard_deviation = np.std(x, axis=0)
    scale = np.where(standard_deviation > 1e-12, standard_deviation, 1.0)
    z = (x - mean) / scale
    design = np.column_stack([np.ones(len(y), dtype=float), z])
    beta = np.zeros(design.shape[1], dtype=float)
    penalty = np.concatenate(
        [[0.0], np.full(x.shape[1], L2_PENALTY, dtype=float)]
    )

    def objective(value: np.ndarray) -> float:
        eta = design @ value
        return float(
            np.sum(np.logaddexp(0.0, eta) - y * eta)
            + 0.5 * L2_PENALTY * np.dot(value[1:], value[1:])
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
        improvement = 0.0
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
        if (
            np.max(np.abs(step_scale * step)) <= 1e-9
            or improvement <= 1e-9
        ):
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
    return float(
        np.mean((np.asarray(response, dtype=float) - probability) ** 2)
    )


def _build_design() -> dict[str, object]:
    node_ids: list[str] = []
    viability: list[float] = []
    motif_ids: list[int] = []
    sources: list[int] = []
    edges: list[DynamicReachabilityEdge] = []
    middle_support = (0.08, 0.20, 0.45, 0.80)

    for motif in range(N_MOTIFS):
        first = len(node_ids)
        level = (motif // N_FOLDS) % len(middle_support)
        for position in range(4):
            node_ids.append(f"m{motif:02d}_n{position}")
            viability.append(
                float(
                    np.clip(
                        0.55
                        + 0.18
                        * np.sin(0.7 * motif + 0.4 * position),
                        0.20,
                        0.90,
                    )
                )
            )
            motif_ids.append(motif)
        sources.append(first)

        transitions = (
            (first, first + 1, 0.75),
            (first + 1, first, 0.75),
            (first + 1, first + 2, middle_support[level]),
            (first + 2, first + 1, middle_support[level]),
            (first + 2, first + 3, 0.75),
            (first + 3, first + 2, 0.75),
        )
        edges.extend(
            DynamicReachabilityEdge(
                source,
                target,
                geographic_support=float(support),
            )
            for source, target, support in transitions
        )

    operator = build_dynamic_transition_operator(
        tuple(node_ids),
        edges,
        loss_support=LOSS_SUPPORT,
    )
    static_result = propagate_dynamic_reachability(
        operator,
        [node_ids[index] for index in sources],
        max_steps=STATIC_MAX_STEPS,
    )
    return {
        "node_ids": tuple(node_ids),
        "viability": np.asarray(viability, dtype=float),
        "motif_ids": np.asarray(motif_ids, dtype=int),
        "source_indices": np.asarray(sources, dtype=int),
        "operator": operator,
        "static_eog": static_result.integrated_node_support,
    }


def _simulate(seed: int, design: dict[str, object]) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(int(seed))
    viability = design["viability"]
    motif_ids = design["motif_ids"]
    sources = design["source_indices"]
    q = design["operator"].transition
    static_eog = design["static_eog"]

    occupied = np.zeros(len(viability), dtype=bool)
    occupied[sources] = True
    source_mask = np.zeros(len(viability), dtype=bool)
    source_mask[sources] = True

    response: list[int] = []
    rows_motif: list[int] = []
    rows_viability: list[float] = []
    rows_previous: list[int] = []
    rows_pressure: list[float] = []
    rows_eog: list[float] = []

    for _ in range(N_TIME_STEPS):
        previous = occupied.copy()
        incoming = 1.0 - np.prod(
            1.0 - previous.astype(float)[:, None] * q,
            axis=0,
        )
        colonisation = _sigmoid(
            -2.2 + 1.1 * (viability - 0.5) + 5.0 * incoming
        )
        persistence = _sigmoid(1.2 + 1.0 * (viability - 0.5))
        probability = np.where(previous, persistence, colonisation)
        probability[sources] = 1.0
        occupied = rng.random(len(viability)) < probability
        occupied[sources] = True

        eligible = ~source_mask
        response.extend(occupied[eligible].astype(int).tolist())
        rows_motif.extend(motif_ids[eligible].tolist())
        rows_viability.extend(viability[eligible].tolist())
        rows_previous.extend(previous[eligible].astype(int).tolist())
        rows_pressure.extend(incoming[eligible].tolist())
        rows_eog.extend(static_eog[eligible].tolist())

    return {
        "response": np.asarray(response, dtype=int),
        "motif_ids": np.asarray(rows_motif, dtype=int),
        "viability": np.asarray(rows_viability, dtype=float),
        "previous_state": np.asarray(rows_previous, dtype=float),
        "incoming_pressure": np.asarray(rows_pressure, dtype=float),
        "static_eog": np.asarray(rows_eog, dtype=float),
    }


def _evaluate_seed(seed: int, design: dict[str, object]) -> dict[str, object]:
    data = _simulate(seed, design)
    y = data["response"]
    folds = data["motif_ids"] % N_FOLDS
    predictors = {
        "state_environment": np.column_stack(
            [data["viability"], data["previous_state"]]
        ),
        "state_environment_eog": np.column_stack(
            [
                data["viability"],
                data["previous_state"],
                data["static_eog"],
            ]
        ),
        "dynamic_occupancy": np.column_stack(
            [
                data["viability"],
                data["previous_state"],
                data["incoming_pressure"],
            ]
        ),
        "dynamic_occupancy_eog": np.column_stack(
            [
                data["viability"],
                data["previous_state"],
                data["incoming_pressure"],
                data["static_eog"],
            ]
        ),
    }
    prediction = {
        name: np.full(len(y), np.nan, dtype=float) for name in MODELS
    }

    for fold in range(N_FOLDS):
        test = folds == fold
        train = ~test
        if len(np.unique(y[train])) < 2:
            raise RuntimeError(
                f"one-class training fold for seed={seed} fold={fold}"
            )
        for name in MODELS:
            model = _ridge_logistic_fit(predictors[name][train], y[train])
            prediction[name][test] = _ridge_logistic_predict(
                model, predictors[name][test]
            )

    models: dict[str, dict[str, float]] = {}
    for name in MODELS:
        score = prediction[name]
        if not np.isfinite(score).all():
            raise RuntimeError(f"non-estimable predictions for {seed}/{name}")
        models[name] = {
            "log_loss": _log_loss(y, score),
            "brier": _brier(y, score),
        }
    return {
        "seed": int(seed),
        "prevalence": float(np.mean(y)),
        "n_observations": int(len(y)),
        "models": models,
    }


def evaluate() -> dict[str, object]:
    design = _build_design()
    rows = [_evaluate_seed(seed, design) for seed in SEEDS]

    mean_models = {
        name: {
            "mean_log_loss": float(
                np.mean([row["models"][name]["log_loss"] for row in rows])
            ),
            "mean_brier": float(
                np.mean([row["models"][name]["brier"] for row in rows])
            ),
        }
        for name in MODELS
    }

    state_environment = mean_models["state_environment"]["mean_log_loss"]
    state_environment_eog = mean_models["state_environment_eog"]["mean_log_loss"]
    process = mean_models["dynamic_occupancy"]["mean_log_loss"]
    process_eog = mean_models["dynamic_occupancy_eog"]["mean_log_loss"]

    gain_over_state_environment = state_environment - process
    gain_over_static_eog = state_environment_eog - process
    eog_increment_over_process = process_eog - process
    favourable = sum(
        int(
            row["models"]["dynamic_occupancy"]["log_loss"]
            < row["models"]["state_environment_eog"]["log_loss"]
        )
        for row in rows
    )

    checks = {
        "process_gain_over_state_environment": {
            "value": gain_over_state_environment,
            "relation": ">=",
            "threshold": MIN_PROCESS_GAIN_OVER_STATE_ENV,
            "passed": bool(
                gain_over_state_environment >= MIN_PROCESS_GAIN_OVER_STATE_ENV
            ),
        },
        "process_gain_over_static_eog": {
            "value": gain_over_static_eog,
            "relation": ">=",
            "threshold": MIN_PROCESS_GAIN_OVER_STATIC_EOG,
            "passed": bool(
                gain_over_static_eog >= MIN_PROCESS_GAIN_OVER_STATIC_EOG
            ),
        },
        "eog_no_material_gain_over_process": {
            "value": eog_increment_over_process,
            "relation": ">=",
            "threshold": -MAX_ALLOWED_EOG_GAIN_OVER_PROCESS,
            "passed": bool(
                eog_increment_over_process >= -MAX_ALLOWED_EOG_GAIN_OVER_PROCESS
            ),
        },
        "process_favourable_seed_count": {
            "value": int(favourable),
            "relation": ">=",
            "threshold": MIN_PROCESS_FAVOURABLE_SEEDS,
            "passed": bool(favourable >= MIN_PROCESS_FAVOURABLE_SEEDS),
        },
    }

    return {
        "status": "development-dynamic-occupancy-reference-boundary",
        "interpretation": (
            "when repeated incidence is generated by a correctly specified first-order "
            "colonisation/persistence process, the process reference should retain "
            "primacy and static EOG-R should not manufacture incremental signal"
        ),
        "seeds": list(SEEDS),
        "design": {
            "n_motifs": N_MOTIFS,
            "n_spatial_folds": N_FOLDS,
            "n_time_steps": N_TIME_STEPS,
            "operator_loss_support": LOSS_SUPPORT,
            "static_eog_max_steps": STATIC_MAX_STEPS,
            "process_predictors": [
                "local viability",
                "previous observed occupancy state",
                "one-step incoming neighbour pressure from previous state",
            ],
            "spatial_cv_policy": (
                "whole motifs held out; repeated time points from held-out motifs "
                "never enter training"
            ),
        },
        "operator_fingerprint": design["operator"].fingerprint,
        "mean_models": mean_models,
        "rows": rows,
        "decision": {
            "passed": bool(all(check["passed"] for check in checks.values())),
            "checks": checks,
        },
        "scientific_boundary": (
            "this benchmark does not estimate detection probability and does not claim "
            "EOG-R replaces a dynamic occupancy/process model when repeated incidence "
            "supports that estimand"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, sort_keys=True, allow_nan=False))
