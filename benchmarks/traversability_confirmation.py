"""Frozen known-truth confirmation for EOG v2 ecological traversability.

The benchmark is intentionally synthetic and prospective. It tests whether the new
pathwise features add held-out information only when the generating truth contains
path discontinuity, transit viability, or a declared long-jump mechanism, while
retreating when endpoint information is already sufficient.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.ecological_traversability import (
    EcologicalTransitionEdge,
    summarize_path_traversability,
)
from eog.support_model import fit_penalized_logistic_support


CONFIRMATION_SEEDS = (1709, 1801, 1907, 2003, 2111, 2203, 2309, 2411)
REGIMES = (
    "endpoint_ibe",
    "path_discontinuity",
    "niche_desert",
    "long_jump",
)
N_MOTIFS = 96
N_FOLDS = 6
L2_PENALTY = 1.0
MIN_FAVOURABLE_SEEDS = 6
MIN_PATH_GAIN = 0.035
MIN_NICHE_GAIN = 0.035
MIN_LONG_JUMP_GAIN = 0.025
MAX_ENDPOINT_EXTRA_GAIN = 0.010
CONTRACT_VERSION = "eog_v2_traversability_confirmation_v1"


def _sigmoid(values: np.ndarray) -> np.ndarray:
    values = np.clip(np.asarray(values, dtype=float), -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-values))


def _zscore(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    scale = float(np.std(values))
    if scale <= 0.0:
        raise RuntimeError("truth signal must vary")
    return (values - np.mean(values)) / scale


def _log_loss(response: np.ndarray, probability: np.ndarray) -> float:
    p = np.clip(np.asarray(probability, dtype=float), 1e-9, 1.0 - 1e-9)
    y = np.asarray(response, dtype=float)
    return float(np.mean(-(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))))


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _generate(seed: int, regime: str) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    endpoint_distance = rng.uniform(0.05, 1.60, N_MOTIFS)
    endpoint_viability = rng.uniform(0.15, 1.0, N_MOTIFS)
    geographic_distance = rng.uniform(0.25, 2.0, N_MOTIFS)
    excursion = rng.uniform(0.0, 2.8, N_MOTIFS)
    intermediate_viability = rng.uniform(0.015, 1.0, (N_MOTIFS, 2))
    jump_direction = rng.uniform(0.02, 1.0, N_MOTIFS)

    cumulative = np.zeros(N_MOTIFS, dtype=float)
    bottleneck = np.zeros(N_MOTIFS, dtype=float)
    minimum_viability = np.zeros(N_MOTIFS, dtype=float)
    niche_penalty = np.zeros(N_MOTIFS, dtype=float)
    jump_support = np.zeros(N_MOTIFS, dtype=float)

    for index in range(N_MOTIFS):
        source = 0.0
        target = float(endpoint_distance[index])
        step1 = float(excursion[index])
        step2 = float(-0.55 * excursion[index] + 0.20 * target)
        states = np.asarray([[source], [step1], [step2], [target]], dtype=float)
        viability = np.asarray(
            [
                1.0,
                intermediate_viability[index, 0],
                intermediate_viability[index, 1],
                endpoint_viability[index],
            ],
            dtype=float,
        )
        summary = summarize_path_traversability(states, viability, [0, 1, 2, 3])
        cumulative[index] = summary.cumulative_environmental_crossing
        bottleneck[index] = summary.environmental_bottleneck
        minimum_viability[index] = float(summary.minimum_intermediate_viability)
        niche_penalty[index] = summary.niche_desert_penalty

        direct_jump = EcologicalTransitionEdge(
            0,
            3,
            geographic_support=float(np.exp(-geographic_distance[index])),
            environmental_distance=float(endpoint_distance[index]),
            transit_viability=float(minimum_viability[index]),
            directional_support=float(jump_direction[index]),
            dispersal_mode="long_jump",
        )
        jump_support[index] = direct_jump.geographic_support * direct_jump.effective_environmental_support(
            scale=1.0
        ) * direct_jump.directional_support

    if regime == "endpoint_ibe":
        truth = -endpoint_distance + 0.35 * endpoint_viability - 0.15 * geographic_distance
    elif regime == "path_discontinuity":
        truth = -bottleneck - 0.20 * cumulative
    elif regime == "niche_desert":
        truth = 1.7 * minimum_viability - 0.35 * niche_penalty
    elif regime == "long_jump":
        truth = jump_support
    else:
        raise ValueError(f"unknown regime: {regime}")

    eta = 1.65 * _zscore(truth) + rng.normal(0.0, 0.18, N_MOTIFS)
    probability = _sigmoid(eta)
    response = rng.binomial(1, probability).astype(float)
    folds = np.arange(N_MOTIFS, dtype=int) % N_FOLDS

    predictors = {
        "R0": np.column_stack([endpoint_distance, endpoint_viability, geographic_distance]),
        "R1": np.column_stack(
            [endpoint_distance, endpoint_viability, geographic_distance, cumulative, bottleneck]
        ),
        "R2": np.column_stack(
            [
                endpoint_distance,
                endpoint_viability,
                geographic_distance,
                cumulative,
                bottleneck,
                minimum_viability,
                niche_penalty,
            ]
        ),
        "R3": np.column_stack(
            [
                endpoint_distance,
                endpoint_viability,
                geographic_distance,
                cumulative,
                bottleneck,
                minimum_viability,
                niche_penalty,
                jump_support,
            ]
        ),
    }
    return {"response": response, "folds": folds, **predictors}


def _heldout_losses(data: dict[str, np.ndarray]) -> dict[str, float]:
    response = data["response"]
    folds = data["folds"].astype(int)
    predictions = {name: np.zeros(len(response), dtype=float) for name in ("R0", "R1", "R2", "R3")}

    for fold in range(N_FOLDS):
        train = folds != fold
        test = folds == fold
        for name in predictions:
            model = fit_penalized_logistic_support(
                data[name][train],
                response[train],
                l2_penalty=L2_PENALTY,
                min_class_count=5,
            )
            predictions[name][test] = model.predict_support(data[name][test])

    return {name: _log_loss(response, probability) for name, probability in predictions.items()}


def _evaluate() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for regime in REGIMES:
        for seed in CONFIRMATION_SEEDS:
            losses = _heldout_losses(_generate(seed, regime))
            rows.append(
                {
                    "regime": regime,
                    "seed": seed,
                    **losses,
                    "R3_minus_R0": losses["R3"] - losses["R0"],
                    "R1_minus_R0": losses["R1"] - losses["R0"],
                    "R2_minus_R1": losses["R2"] - losses["R1"],
                    "R3_minus_R2": losses["R3"] - losses["R2"],
                }
            )

    def values(regime: str, field: str) -> np.ndarray:
        return np.asarray(
            [row[field] for row in rows if row["regime"] == regime],
            dtype=float,
        )

    endpoint = values("endpoint_ibe", "R3_minus_R0")
    path = values("path_discontinuity", "R1_minus_R0")
    niche = values("niche_desert", "R2_minus_R1")
    jump = values("long_jump", "R3_minus_R2")

    gates = {
        "endpoint_retreat": {
            "mean_delta": float(np.mean(endpoint)),
            "threshold": -MAX_ENDPOINT_EXTRA_GAIN,
            "passed": bool(float(np.mean(endpoint)) >= -MAX_ENDPOINT_EXTRA_GAIN),
        },
        "path_added_information": {
            "mean_delta": float(np.mean(path)),
            "threshold": -MIN_PATH_GAIN,
            "favourable_seeds": int(np.sum(path < 0.0)),
            "passed": bool(
                float(np.mean(path)) <= -MIN_PATH_GAIN
                and int(np.sum(path < 0.0)) >= MIN_FAVOURABLE_SEEDS
            ),
        },
        "niche_added_information": {
            "mean_delta": float(np.mean(niche)),
            "threshold": -MIN_NICHE_GAIN,
            "favourable_seeds": int(np.sum(niche < 0.0)),
            "passed": bool(
                float(np.mean(niche)) <= -MIN_NICHE_GAIN
                and int(np.sum(niche < 0.0)) >= MIN_FAVOURABLE_SEEDS
            ),
        },
        "long_jump_added_information": {
            "mean_delta": float(np.mean(jump)),
            "threshold": -MIN_LONG_JUMP_GAIN,
            "favourable_seeds": int(np.sum(jump < 0.0)),
            "passed": bool(
                float(np.mean(jump)) <= -MIN_LONG_JUMP_GAIN
                and int(np.sum(jump < 0.0)) >= MIN_FAVOURABLE_SEEDS
            ),
        },
    }
    decision = "pass" if all(gate["passed"] for gate in gates.values()) else "fail"
    result = {
        "schema": CONTRACT_VERSION,
        "confirmation_seeds": list(CONFIRMATION_SEEDS),
        "regimes": list(REGIMES),
        "n_motifs": N_MOTIFS,
        "n_folds": N_FOLDS,
        "l2_penalty": L2_PENALTY,
        "gates": gates,
        "decision": decision,
        "rows": rows,
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = _evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "gates": result["gates"], "fingerprint": result["fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
