"""Fixed development comparison; see docs/innovation_offset_design.md."""

from __future__ import annotations

import json
import platform

import numpy as np
import scipy
import sklearn
from sklearn.ensemble import RandomForestClassifier

from eog.v2.contextual_innovation_summary import summarize_contextual_innovation
from eog.v2.innovation_offset import fit_innovation_offset
from eog.v2.source_symmetric_predictive_summary import (
    summarize_source_symmetric_support,
)

SEEDS = (701, 709, 719, 727)
REGIMES = ("mean_signal", "spread_signal", "neutral", "unseen_reversal")


def _rf():
    return RandomForestClassifier(
        n_estimators=64,
        min_samples_leaf=10,
        max_features="sqrt",
        random_state=91,
        n_jobs=1,
    )


def _probability(model, x):
    if not np.array_equal(model.classes_, [0, 1]):
        raise ValueError("fit split must contain both classes")
    return np.clip(model.predict_proba(x)[:, 1], 1e-6, 1 - 1e-6)


def _loss(y, p):
    y = np.asarray(y)
    p = np.asarray(p, dtype=float)
    if y.shape != p.shape or y.ndim != 1 or not y.size or not np.isin(y, (0, 1)).all():
        raise ValueError("scoring requires aligned nonempty binary outcomes")
    if not np.isfinite(p).all():
        raise ValueError("scoring probabilities must be finite")
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(np.mean(-np.where(y == 1, np.log(p), np.log1p(-p))))


def choose_on_calibration(y_calibration, baseline, candidate):
    return _loss(y_calibration, candidate) < _loss(y_calibration, baseline)


def _design(seed):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(1500, 2))
    u, v = rng.uniform(-1, 1, size=(2, 1500))
    mean = 0.5 + 0.08 * np.tanh(x[:, 1])
    world_sign = np.array([-1, 1])[None, :, None]
    source_sign = np.array([-1, 1])[:, None, None]
    reference_tensor = mean[None, None, :] + 0.1 * world_sign + 0.015 * source_sign
    current_tensor = (
        (mean + 0.12 * u)[None, None, :]
        + (0.1 + 0.08 * v)[None, None, :] * world_sign
        + 0.015 * source_sign
    )
    ids = {
        "source_ids": ("s0", "s1"),
        "world_ids": ("w0", "w1"),
        "node_ids": tuple(f"node_{i}" for i in range(1500)),
        "declared_world_count": 2,
    }
    reference = summarize_source_symmetric_support(reference_tensor, **ids)
    current = summarize_source_symmetric_support(current_tensor, **ids)
    innovation = summarize_contextual_innovation(reference, current)
    shuffled = innovation.feature_matrix.copy()
    for start, end in ((0, 600), (600, 900), (900, 1500)):
        shuffled[start:end] = shuffled[start:end][rng.permutation(end - start)]
    return x, u, v, rng.uniform(size=1500), current.feature_matrix, innovation, shuffled


def run_comparison():
    rows = []
    for seed in SEEDS:
        x, u, v, uniforms, absolute, innovation, shuffled = _design(seed)
        z = innovation.feature_matrix
        names = innovation.feature_names
        for regime in REGIMES:
            effect = (
                np.zeros(1500)
                if regime == "neutral"
                else 2 * (v if regime == "spread_signal" else u)
            )
            if regime == "unseen_reversal":
                effect[900:] *= -1
            probability = 1 / (1 + np.exp(-(0.8 * x[:, 0] - 0.4 * x[:, 1] + effect)))
            y = (uniforms < probability).astype(int)
            base_model = _rf().fit(x[:600], y[:600])
            base = _probability(base_model, x[600:])
            oof = np.full(600, np.nan)
            fold_ids = np.arange(600) % 3
            for fold in range(3):
                training = np.flatnonzero(fold_ids != fold)
                validation = np.flatnonzero(fold_ids == fold)
                if np.intersect1d(training, validation).size:
                    raise AssertionError("OOF row leaked into its own training set")
                model = _rf().fit(x[training], y[training])
                oof[validation] = _probability(model, x[validation])
            candidates = {}
            for name, features in (
                ("concat_absolute", absolute),
                ("concat_innovation", z),
            ):
                full = np.c_[x, features]
                model = _rf().fit(full[:600], y[:600])
                candidates[name] = _probability(model, full[600:])
            for name, features, feature_names in (
                ("offset_all", z, names),
                ("offset_mean_only", z[:, 1:2], names[1:2]),
                ("offset_permuted", shuffled, names),
            ):
                model = fit_innovation_offset(
                    oof, features[:600], y[:600], feature_names=feature_names, ridge=0.1
                )
                candidates[name] = model.predict(
                    base, features[600:], feature_names=feature_names
                )
            # Freeze every decision before accessing outer labels for scoring.
            choices = {
                name: choose_on_calibration(y[600:900], base[:300], p[:300])
                for name, p in candidates.items()
            }
            baseline_loss = _loss(y[900:], base[300:])
            scores = {name: _loss(y[900:], p[300:]) for name, p in candidates.items()}
            rows.append(
                {
                    "seed": seed,
                    "regime": regime,
                    "baseline_log_loss": baseline_loss,
                    "always_on_log_loss": scores,
                    "promoted": choices,
                    "selected_log_loss": {
                        name: score if choices[name] else baseline_loss
                        for name, score in scores.items()
                    },
                    "innovation_fingerprint": innovation.fingerprint,
                }
            )
    summaries = {}
    for regime in REGIMES:
        subset = [row for row in rows if row["regime"] == regime]
        summaries[regime] = {
            name: {
                "always_on_delta": float(
                    np.mean(
                        [
                            row["always_on_log_loss"][name] - row["baseline_log_loss"]
                            for row in subset
                        ]
                    )
                ),
                "selected_delta": float(
                    np.mean(
                        [
                            row["selected_log_loss"][name] - row["baseline_log_loss"]
                            for row in subset
                        ]
                    )
                ),
                "promotions": sum(row["promoted"][name] for row in subset),
            }
            for name in subset[0]["always_on_log_loss"]
        }
    return {
        "schema": "eog.innovation_offset_comparison.v1",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "scipy": scipy.__version__,
        },
        "rows": rows,
        "summaries": summaries,
        "uses_biological_response": False,
        "support_tensors_are_stipulated_not_geometry_generated": True,
        "status": "development_comparison_not_independent_confirmation",
    }


if __name__ == "__main__":
    print(json.dumps(run_comparison(), indent=2, sort_keys=True, allow_nan=False))
