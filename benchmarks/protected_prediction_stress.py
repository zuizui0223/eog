"""Deterministic prediction-level stress test; not fresh empirical validation."""

import json

import numpy as np

from eog.v2.protected_prediction import protect_binary_probabilities


def run_fitted_benchmark():
    """Fixed design: 4 seeds x 3 regimes, no budget or model search.

    Extra columns are synthetic candidate information, not EOG-computed features.
    Outer responses never enter protection, training, or parameter selection.
    """
    from sklearn.ensemble import RandomForestClassifier

    rows = []
    for seed in (601, 607, 613, 617):
        rng = np.random.default_rng(seed)
        x = rng.normal(size=(1000, 2))
        z = rng.normal(size=(1000, 1))
        noise = rng.normal(size=(1000, 9))
        uniforms = rng.uniform(size=1000)
        for regime in ("helpful", "neutral", "unseen_sign_reversal"):
            coefficient = np.full(1000, 2.0 if regime != "neutral" else 0.0)
            if regime == "unseen_sign_reversal":
                coefficient[500:] = -2.0
            probability = 1 / (1 + np.exp(-(x[:, 0] + coefficient * z[:, 0])))
            y = (uniforms < probability).astype(int)
            predictions = {}
            for name, features in (("baseline", x), ("candidate", np.c_[x, z, noise])):
                model = RandomForestClassifier(
                    n_estimators=64,
                    min_samples_leaf=10,
                    max_features="sqrt",
                    random_state=91,
                    n_jobs=1,
                )
                model.fit(features[:500], y[:500])
                # Declare the same finite-log-loss scoring policy for both fits.
                predictions[name] = np.clip(
                    model.predict_proba(features[500:])[:, 1], 1e-6, 1 - 1e-6
                )
            predictions["protected"] = protect_binary_probabilities(
                predictions["baseline"],
                predictions["candidate"],
                max_excess_log_loss=0.01,
            )
            losses = {
                name: float(np.mean(-np.log(np.where(y[500:] == 1, p, 1 - p))))
                for name, p in predictions.items()
            }
            if losses["protected"] - losses["baseline"] > 0.01 + 1e-12:
                raise AssertionError("fitted benchmark violated protection bound")
            rows.append({"seed": seed, "regime": regime, "log_loss": losses})
    return {
        "budget_nats": 0.01,
        "rows": rows,
        "uses_eog_computed_features": False,
        "uses_biological_response": False,
        "regime_mean_deltas": {
            regime: {
                name: float(
                    np.mean(
                        [
                            row["log_loss"][name] - row["log_loss"]["baseline"]
                            for row in rows
                            if row["regime"] == regime
                        ]
                    )
                )
                for name in ("candidate", "protected")
            }
            for regime in ("helpful", "neutral", "unseen_sign_reversal")
        },
    }


def run_benchmark():
    # Fixed illustrative budget, not fitted to Tampa or searched over results.
    budget = 0.01
    truth = np.tile([0, 1], 100)
    base = np.where(truth == 1, 0.7, 0.3)
    rows = []
    # Hand-constructed forecasts intentionally span perfect ordering and reversal.
    # This tests the output policy, not the ability of a learner to find signal.
    for name, candidate in (
        ("helpful", np.where(truth == 1, 0.9, 0.1)),
        ("unchanged", base.copy()),
        ("confidently_wrong", np.where(truth == 1, 0.001, 0.999)),
        ("exactly_wrong", 1 - truth.astype(float)),
    ):
        protected = protect_binary_probabilities(
            base, candidate, max_excess_log_loss=budget
        )
        losses = {}
        for label, p in (
            ("baseline", base),
            ("candidate", candidate),
            ("protected", protected),
        ):
            probability_of_truth = np.where(truth == 1, p, 1 - p)
            losses[label] = (
                float(np.mean(-np.log(probability_of_truth)))
                if np.all(probability_of_truth > 0)
                else None
            )
        excess = losses["protected"] - losses["baseline"]
        if excess > budget + 1e-12:
            raise AssertionError("protected loss exceeded declared budget")
        rows.append(
            {
                "case": name,
                "macro_log_loss": losses,
                "protected_minus_baseline": excess,
                "candidate_loss_infinite": losses["candidate"] is None,
            }
        )
    return {
        "schema": "eog.protected_prediction_stress.v1",
        "budget_nats": budget,
        "uses_biological_response": False,
        "empirical_improvement_demonstrated": False,
        "results": rows,
    }


if __name__ == "__main__":
    print(
        json.dumps(
            {"stress": run_benchmark(), "fitted": run_fitted_benchmark()},
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
