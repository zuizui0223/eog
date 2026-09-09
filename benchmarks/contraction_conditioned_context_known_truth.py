"""Frozen known-truth test for contraction-conditioned contextual EOG.

The contract was committed before this runner. No biological response is used. Within
replicate, baseline, outcomes, learner, split, source refresh, and declared worlds are
identical; only the prediction-facing choice to respect Layer-A elimination or retain
all declared worlds differs.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation/layer_b_mechanism_v2/contraction_conditioned_known_truth_contract_v1.json"
DEFAULT_OUTPUT = ROOT / "build/contraction_conditioned_context_known_truth_result.json"
EPS = 1e-6


def _sigmoid(value: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(value, -30.0, 30.0)))


def _rf(contract: dict[str, object]) -> RandomForestClassifier:
    hp = contract["design"]["learner_hyperparameters"]
    return RandomForestClassifier(
        n_estimators=int(hp["n_estimators"]),
        max_features=str(hp["max_features"]),
        min_samples_leaf=int(hp["min_samples_leaf"]),
        class_weight=None,
        random_state=int(hp["random_state"]),
        n_jobs=int(hp["n_jobs"]),
    )


def _distance_matrix(coords: np.ndarray) -> np.ndarray:
    diff = coords[:, None, :] - coords[None, :, :]
    return np.sqrt(np.sum(diff * diff, axis=2))


def _source_tensor(
    distances: np.ndarray,
    sources: tuple[int, ...],
    thresholds: tuple[float, ...],
    world_indices: tuple[int, ...],
) -> np.ndarray:
    tensor = np.zeros((len(sources), len(world_indices), distances.shape[0]), dtype=float)
    for s_idx, source in enumerate(sources):
        for w_idx, world_index in enumerate(world_indices):
            tensor[s_idx, w_idx] = (distances[source] <= thresholds[world_index] + 1e-12).astype(float)
    return tensor


def _union_support(
    distances: np.ndarray,
    sources: tuple[int, ...],
    threshold: float,
) -> np.ndarray:
    if not sources:
        raise RuntimeError("source set must not be empty")
    support = np.zeros(distances.shape[0], dtype=bool)
    for source in sources:
        support |= distances[source] <= threshold + 1e-12
    return support


def _contextual_features(
    distances: np.ndarray,
    sources: tuple[int, ...],
    thresholds: tuple[float, ...],
    world_indices: tuple[int, ...],
) -> np.ndarray:
    source_ids = tuple(f"n{source}" for source in sources)
    world_ids = tuple(f"w{index}" for index in world_indices)
    tensor = _source_tensor(distances, sources, thresholds, world_indices)
    summary = summarize_source_symmetric_support(
        tensor,
        source_ids=source_ids,
        world_ids=world_ids,
        node_ids=tuple(f"n{i}" for i in range(distances.shape[0])),
        declared_world_count=len(thresholds),
    )
    return np.asarray(summary.feature_matrix, dtype=float)


def _macro_metric(
    y: np.ndarray,
    p: np.ndarray,
    context_index: np.ndarray,
    heldout_contexts: tuple[int, ...],
    *,
    brier: bool,
) -> float:
    values: list[float] = []
    for context in heldout_contexts:
        mask = context_index == context
        if brier:
            values.append(float(np.mean((p[mask] - y[mask]) ** 2)))
        else:
            values.append(float(log_loss(y[mask], p[mask], labels=[0, 1])))
    return float(np.mean(values))


def _one_replicate(seed: int, contract: dict[str, object]) -> dict[str, object]:
    d = contract["design"]
    rng = np.random.default_rng(seed)
    n_nodes = int(d["node_count"])
    n_contexts = int(d["context_count"])
    n_calibration = int(d["calibration_context_count"])
    thresholds = tuple(float(v) for v in d["world_thresholds"])
    true_threshold = float(d["true_world_threshold"])
    true_world_index = thresholds.index(true_threshold)

    coords = rng.uniform(0.0, 1.0, size=(n_nodes, 2))
    node_covariate = rng.normal(0.0, 1.0, size=n_nodes)
    distances = _distance_matrix(coords)
    anchor_min = int(np.argmin(coords[:, 0]))
    anchor_max = int(np.argmax(coords[:, 0]))
    anchors = {anchor_min, anchor_max}

    all_worlds = tuple(range(len(thresholds)))
    surviving = all_worlds
    previous_positive: set[int] = set()
    cumulative_positive = np.zeros(n_nodes, dtype=int)

    baseline_rows: list[np.ndarray] = []
    conditioned_rows: list[np.ndarray] = []
    uncontracted_rows: list[np.ndarray] = []
    responses: list[np.ndarray] = []
    context_rows: list[np.ndarray] = []
    trajectory: list[int] = []
    contraction_events: list[dict[str, object]] = []
    true_world_survived_calibration = True

    for context in range(n_contexts):
        phase = 2.0 * math.pi * context / n_contexts
        sources = tuple(sorted(anchors | previous_positive))
        conditioned = _contextual_features(distances, sources, thresholds, tuple(surviving))
        uncontracted = _contextual_features(distances, sources, thresholds, all_worlds)

        previous_vector = np.asarray([1.0 if i in previous_positive else 0.0 for i in range(n_nodes)])
        cumulative_fraction = cumulative_positive / max(1, context)
        global_previous_fraction = len(previous_positive) / n_nodes
        baseline = np.column_stack(
            [
                coords[:, 0],
                coords[:, 1],
                node_covariate,
                np.full(n_nodes, math.sin(phase)),
                np.full(n_nodes, math.cos(phase)),
                previous_vector,
                cumulative_fraction,
                np.full(n_nodes, global_previous_fraction),
            ]
        )

        true_support = _union_support(distances, sources, true_threshold)
        inside_lp = -0.35 + 0.45 * node_covariate + 0.30 * math.sin(phase) - 0.15 * math.cos(phase)
        probability = np.where(true_support, _sigmoid(inside_lp), 0.0)
        y = rng.binomial(1, probability).astype(int)
        positive = set(np.flatnonzero(y == 1).tolist())

        baseline_rows.append(baseline)
        conditioned_rows.append(conditioned)
        uncontracted_rows.append(uncontracted)
        responses.append(y)
        context_rows.append(np.full(n_nodes, context, dtype=int))
        trajectory.append(len(surviving))

        before = tuple(surviving)
        kept: list[int] = []
        for world_index in surviving:
            union = _union_support(distances, sources, thresholds[world_index])
            if all(bool(union[node]) for node in positive):
                kept.append(world_index)
        surviving = tuple(kept)
        if true_world_index not in surviving and context < n_calibration:
            true_world_survived_calibration = False
        if len(surviving) < len(before):
            contraction_events.append(
                {
                    "context": context,
                    "before": list(before),
                    "after": list(surviving),
                }
            )
        if not surviving:
            raise RuntimeError("known-truth world universe was fully falsified")

        cumulative_positive += y
        previous_positive = positive

    x_base = np.vstack(baseline_rows)
    x_conditioned = np.hstack([x_base, np.vstack(conditioned_rows)])
    x_uncontracted = np.hstack([x_base, np.vstack(uncontracted_rows)])
    y_all = np.concatenate(responses)
    context_index = np.concatenate(context_rows)
    train = context_index < n_calibration
    test = ~train
    if len(np.unique(y_all[train])) != 2 or len(np.unique(y_all[test])) != 2:
        raise RuntimeError("response realization lost a class in calibration or heldout")

    predictions: dict[str, np.ndarray] = {}
    losses: dict[str, float] = {}
    briers: dict[str, float] = {}
    for name, matrix in (
        ("baseline", x_base),
        ("conditioned", x_conditioned),
        ("uncontracted", x_uncontracted),
    ):
        model = _rf(contract)
        model.fit(matrix[train], y_all[train])
        probability = np.clip(model.predict_proba(matrix[test])[:, 1], EPS, 1.0 - EPS)
        full_probability = np.full(y_all.shape[0], np.nan)
        full_probability[test] = probability
        predictions[name] = full_probability
        heldout_contexts = tuple(range(n_calibration, n_contexts))
        losses[name] = _macro_metric(
            y_all,
            full_probability,
            context_index,
            heldout_contexts,
            brier=False,
        )
        briers[name] = _macro_metric(
            y_all,
            full_probability,
            context_index,
            heldout_contexts,
            brier=True,
        )

    calibration_contracted = any(event["context"] < n_calibration for event in contraction_events)
    return {
        "seed": seed,
        "macro_log_loss": losses,
        "macro_brier": briers,
        "conditioned_minus_uncontracted": losses["conditioned"] - losses["uncontracted"],
        "conditioned_minus_baseline": losses["conditioned"] - losses["baseline"],
        "uncontracted_minus_baseline": losses["uncontracted"] - losses["baseline"],
        "calibration_contracted": calibration_contracted,
        "calibration_contraction_event_count": sum(
            int(event["context"] < n_calibration) for event in contraction_events
        ),
        "true_world_survived_calibration": true_world_survived_calibration,
        "surviving_world_count_before_context": trajectory,
        "contraction_events": contraction_events,
    }


def run_benchmark() -> dict[str, object]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    reps = [_one_replicate(int(seed), contract) for seed in contract["design"]["replicate_seeds"]]
    primary = np.asarray([float(rep["conditioned_minus_uncontracted"]) for rep in reps])
    conditioned_vs_baseline = np.asarray([float(rep["conditioned_minus_baseline"]) for rep in reps])
    uncontracted_vs_baseline = np.asarray([float(rep["uncontracted_minus_baseline"]) for rep in reps])
    contraction_fraction = float(np.mean([bool(rep["calibration_contracted"]) for rep in reps]))
    true_survival_fraction = float(np.mean([bool(rep["true_world_survived_calibration"]) for rep in reps]))

    checks = {
        "median_primary_delta_strictly_negative": bool(np.median(primary) < 0.0),
        "conditioned_beats_uncontracted_in_at_least_0_75_of_replicates": bool(np.mean(primary < 0.0) >= 0.75),
        "at_least_one_calibration_contraction_event_in_at_least_0_90_of_replicates": bool(contraction_fraction >= 0.90),
        "true_world_survives_through_calibration_in_all_replicates": bool(true_survival_fraction == 1.0),
    }
    all_pass = all(checks.values())
    scientific_status = (
        "known_truth_support_for_contraction_conditioning"
        if all_pass
        else "known_truth_refutation_or_non_support_for_contraction_conditioning"
    )
    result = {
        "schema": "eog.layer_b_mechanism_v2.contraction_conditioned_known_truth_result.v1",
        "uses_biological_response": False,
        "counts_as_fresh_predictive_endpoint": False,
        "changes_closed_eog_wf_synthesis": False,
        "replicate_count": len(reps),
        "scientific_status": scientific_status,
        "predeclared_checks_all_passed": all_pass,
        "checks": checks,
        "primary_conditioned_minus_uncontracted": {
            "mean": float(np.mean(primary)),
            "median": float(np.median(primary)),
            "q025": float(np.quantile(primary, 0.025)),
            "q975": float(np.quantile(primary, 0.975)),
            "conditioned_win_fraction": float(np.mean(primary < 0.0)),
        },
        "secondary_conditioned_minus_baseline": {
            "mean": float(np.mean(conditioned_vs_baseline)),
            "median": float(np.median(conditioned_vs_baseline)),
            "favorable_fraction": float(np.mean(conditioned_vs_baseline < 0.0)),
        },
        "secondary_uncontracted_minus_baseline": {
            "mean": float(np.mean(uncontracted_vs_baseline)),
            "median": float(np.median(uncontracted_vs_baseline)),
            "favorable_fraction": float(np.mean(uncontracted_vs_baseline < 0.0)),
        },
        "calibration_contraction_fraction": contraction_fraction,
        "true_world_calibration_survival_fraction": true_survival_fraction,
        "median_calibration_contraction_event_count": float(
            np.median([int(rep["calibration_contraction_event_count"]) for rep in reps])
        ),
        "interpretation": (
            "This paired known-truth test isolates the representation effect of respecting past-evidence Layer-A elimination versus retaining all declared worlds. It cannot establish a real-system necessity or sufficiency claim."
        ),
        "forbidden_interpretations": contract["forbidden_interpretations"],
    }
    return result


def main(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    result = run_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
