"""Adaptive-family development screen on the frozen noisy EOG generators.

This screen reuses the already-open development seeds, so it can guide model-family
design but cannot confirm superiority. For every seed/regime, outer target labels are
untouched. The two declared positive source anchors in each synthetic module remain
fixed in every family-selection fit. The additional right/left training candidates are
assigned to three crossed selection folds and choose among environmental-only,
conservative probability-gated EOG, and cross-fitted stacked EOG by held-out Bernoulli
log loss. Two orthogonal gate folds remain inside each selection-training subset for
source/fusion cross-fitting.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
from collections import Counter

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eog.distribution_adaptive import (
    AdaptiveEOGDistributionConfig,
    fit_adaptive_eog_distribution,
)
from benchmarks.distribution_model_noisy_regimes import (
    DEVELOPMENT_SEEDS,
    REGIMES,
    _auc,
    _brier,
    _fit_comparator_predictions,
    build_noisy_landscape,
)
from eog import fit_eog_distribution


def _selection_folds(observed_ids: tuple[str, ...]) -> tuple[str, ...]:
    offsets = {
        "source_a": 0,
        "right_train": 1,
        "source_b": 1,
        "left_train": 2,
    }
    result: list[str] = []
    for node_id in observed_ids:
        module = int(node_id[1:3])
        role = node_id.split("_", 1)[1]
        result.append(f"selection_{(module + offsets[role]) % 3}")
    return tuple(result)


def _fixed_sources(observed_ids: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        node_id
        for node_id in observed_ids
        if node_id.endswith("_source_a") or node_id.endswith("_source_b")
    )


def run_adaptive_development(
    *,
    seeds: tuple[int, ...] = DEVELOPMENT_SEEDS,
    n_modules: int = 24,
) -> dict[str, object]:
    per_regime: dict[str, list[dict[str, object]]] = {regime: [] for regime in REGIMES}
    integrity = {
        "same_declared_development_seeds": seeds == DEVELOPMENT_SEEDS,
        "all_target_labels_held_out": True,
        "all_selection_has_three_folds": True,
        "all_gate_has_two_folds": True,
        "all_fixed_sources_positive": True,
        "all_selection_candidates_have_both_classes": True,
        "all_scores_finite": True,
        "all_candidate_selection_scores_finite": True,
    }

    for regime in REGIMES:
        for seed in seeds:
            bundle = build_noisy_landscape(regime, seed, n_modules=n_modules)
            selection_folds = _selection_folds(bundle.observed_ids)
            fixed_sources = _fixed_sources(bundle.observed_ids)
            observed_label = dict(zip(bundle.observed_ids, bundle.observed_response))
            scored_labels = np.asarray(
                [
                    label
                    for node_id, label in zip(
                        bundle.observed_ids, bundle.observed_response
                    )
                    if node_id not in set(fixed_sources)
                ],
                dtype=int,
            )
            adaptive = fit_adaptive_eog_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                AdaptiveEOGDistributionConfig(
                    base_config=bundle.config,
                    stacked_fusion_l2_penalty=1.0,
                    selection_tolerance=1e-12,
                ),
                selection_fold_ids=selection_folds,
                gate_fold_ids=bundle.gate_folds,
                selection_fixed_source_ids=fixed_sources,
                barriers=bundle.barriers,
                reference_provenance=f"adaptive development {regime} seed {seed}",
            )

            probability_companion = fit_eog_distribution(
                bundle.nodes,
                bundle.observed_ids,
                bundle.observed_response,
                bundle.config,
                barriers=bundle.barriers,
                gate_fold_ids=bundle.gate_folds,
                reference_provenance=f"adaptive comparator {regime} seed {seed}",
            )
            scores = _fit_comparator_predictions(bundle, probability_companion)
            scores["adaptive_eog"] = adaptive.predict(
                bundle.target_ids
            ).distribution_support
            labels = np.asarray(bundle.target_response, dtype=int)

            integrity["all_target_labels_held_out"] &= set(bundle.target_ids).isdisjoint(
                bundle.observed_ids
            )
            integrity["all_selection_has_three_folds"] &= len(
                {
                    fold
                    for node_id, fold in zip(bundle.observed_ids, selection_folds)
                    if node_id not in set(fixed_sources)
                }
            ) == 3
            integrity["all_gate_has_two_folds"] &= len(set(bundle.gate_folds)) == 2
            integrity["all_fixed_sources_positive"] &= all(
                observed_label[node_id] == 1 for node_id in fixed_sources
            )
            integrity["all_selection_candidates_have_both_classes"] &= bool(
                np.any(scored_labels == 1) and np.any(scored_labels == 0)
            )
            integrity["all_scores_finite"] &= all(
                np.isfinite(np.asarray(values, dtype=float)).all()
                for values in scores.values()
            )
            integrity["all_candidate_selection_scores_finite"] &= all(
                np.isfinite(value) for value in adaptive.candidate_log_loss.values()
            )

            per_regime[regime].append(
                {
                    "seed": seed,
                    "selected_family": adaptive.selected_family,
                    "candidate_selection_log_loss": adaptive.candidate_log_loss,
                    "n_fixed_sources": len(fixed_sources),
                    "n_selection_candidates": int(scored_labels.size),
                    "auc": {name: _auc(labels, values) for name, values in scores.items()},
                    "brier": {name: _brier(labels, values) for name, values in scores.items()},
                }
            )

    summary: dict[str, object] = {}
    for regime, rows in per_regime.items():
        methods = tuple(rows[0]["auc"])
        selected = Counter(row["selected_family"] for row in rows)
        summary[regime] = {
            "selected_family_counts": {
                family: int(selected.get(family, 0))
                for family in ("environmental", "probability_gate", "stacked")
            },
            "mean_candidate_selection_log_loss": {
                family: float(
                    np.mean(
                        [row["candidate_selection_log_loss"][family] for row in rows]
                    )
                )
                for family in ("environmental", "probability_gate", "stacked")
            },
            "mean_auc": {
                method: float(np.mean([row["auc"][method] for row in rows]))
                for method in methods
            },
            "mean_brier": {
                method: float(np.mean([row["brier"][method] for row in rows]))
                for method in methods
            },
            "adaptive_minus_environmental_mean_auc": float(
                np.mean(
                    [
                        row["auc"]["adaptive_eog"] - row["auc"]["environmental_support"]
                        for row in rows
                    ]
                )
            ),
            "adaptive_minus_single_path_mean_auc": float(
                np.mean(
                    [
                        row["auc"]["adaptive_eog"]
                        - row["auc"]["environmental_plus_single_path"]
                        for row in rows
                    ]
                )
            ),
            "adaptive_minus_environmental_mean_brier": float(
                np.mean(
                    [
                        row["brier"]["adaptive_eog"]
                        - row["brier"]["environmental_support"]
                        for row in rows
                    ]
                )
            ),
        }

    return {
        "schema": "adaptive_eog_noisy_development_v0_3",
        "status": "development_screen_not_confirmation",
        "seeds": list(seeds),
        "regimes": list(REGIMES),
        "selection_rule": {
            "metric": "Bernoulli log loss on non-anchor selection candidates",
            "fixed_sources": "source_a and source_b within every synthetic module",
            "complexity_tie_break": ["environmental", "probability_gate", "stacked"],
            "selection_folds": 3,
            "gate_folds": 2,
        },
        "integrity_checks": integrity,
        "all_integrity_checks_pass": bool(all(integrity.values())),
        "summary": summary,
        "per_regime": per_regime,
        "claim_boundary": (
            "adaptive-family development on previously opened seeds only; selected family "
            "and numerical promotion criteria must be frozen before independent-seed confirmation"
        ),
    }


def main() -> None:
    result = run_adaptive_development()
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_integrity_checks_pass"]:
        raise SystemExit("adaptive EOG development screen failed integrity checks")


if __name__ == "__main__":
    main()
