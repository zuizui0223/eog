#!/usr/bin/env python3
"""Audit EOG sensitivity to sample size and irrelevant feature dimensions.

This benchmark is deliberately diagnostic. It measures metric drift under a connected
null and discrimination of fragmented/curved alternatives across sample sizes and
added independent noise features. It does not tune thresholds on the results.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from eog import infer_occupancy_geometry


def _connected(rng: np.random.Generator, n: int) -> np.ndarray:
    t = rng.uniform(-1.5, 1.5, n)
    x = np.column_stack([t, 0.35 * np.sin(2.0 * t)])
    return x + rng.normal(0.0, 0.12, size=x.shape)


def _two_modes(rng: np.random.Generator, n: int) -> np.ndarray:
    half = n // 2
    return np.vstack([
        rng.normal((-1.5, 0.0), (0.18, 0.18), size=(half, 2)),
        rng.normal((1.5, 0.0), (0.18, 0.18), size=(n - half, 2)),
    ])


def _straight(rng: np.random.Generator, n: int) -> np.ndarray:
    t = np.linspace(-1.0, 1.0, n)
    return np.column_stack([t, t]) / np.sqrt(2.0) + rng.normal(0.0, 0.004, (n, 2))


def _curved(rng: np.random.Generator, n: int) -> np.ndarray:
    angle = np.linspace(0.0, np.pi, n)
    x = np.column_stack([np.cos(angle), np.sin(angle)])
    return x + rng.normal(0.0, 0.004, (n, 2))


def _add_noise(x: np.ndarray, rng: np.random.Generator, noise_features: int) -> np.ndarray:
    if noise_features == 0:
        return x
    return np.column_stack([x, rng.normal(size=(len(x), noise_features))])


def _auc(negative: np.ndarray, positive: np.ndarray) -> float:
    """Probability that a random positive score exceeds a random negative score."""
    comparisons = positive[:, None] - negative[None, :]
    return float((np.sum(comparisons > 0) + 0.5 * np.sum(comparisons == 0)) / comparisons.size)


def run(repeats: int, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    rng = np.random.default_rng(seed)
    sample_sizes = (30, 60, 120, 240)
    noise_dimensions = (0, 2, 6)
    rows: list[dict[str, object]] = []

    for n in sample_sizes:
        for noise in noise_dimensions:
            for repeat in range(1, repeats + 1):
                for scenario, generator in (
                    ("connected", _connected),
                    ("two_modes", _two_modes),
                    ("straight", _straight),
                    ("curved", _curved),
                ):
                    values = _add_noise(generator(rng, n), rng, noise)
                    geometry = infer_occupancy_geometry(values)
                    rows.append({
                        "sample_size": n,
                        "noise_features": noise,
                        "total_features": values.shape[1],
                        "repeat": repeat,
                        "scenario": scenario,
                        "span": geometry.span,
                        "continuity": geometry.continuity,
                        "gap_strength": geometry.gap_strength,
                        "component_count": geometry.component_count,
                    })

    frame = pd.DataFrame(rows)
    summaries: list[dict[str, object]] = []
    for (n, noise), group in frame.groupby(["sample_size", "noise_features"]):
        connected = group[group.scenario.eq("connected")]
        modes = group[group.scenario.eq("two_modes")]
        straight = group[group.scenario.eq("straight")]
        curved = group[group.scenario.eq("curved")]
        summaries.append({
            "sample_size": int(n),
            "noise_features": int(noise),
            "connected_gap_median": float(connected.gap_strength.median()),
            "connected_gap_q95": float(connected.gap_strength.quantile(0.95)),
            "two_modes_gap_median": float(modes.gap_strength.median()),
            "gap_auc": _auc(connected.gap_strength.to_numpy(), modes.gap_strength.to_numpy()),
            "straight_continuity_median": float(straight.continuity.median()),
            "curved_continuity_median": float(curved.continuity.median()),
            "continuity_auc": _auc((-straight.continuity).to_numpy(), (-curved.continuity).to_numpy()),
        })
    summary = pd.DataFrame(summaries)

    clean = summary[summary.noise_features.eq(0)]
    noisy = summary[summary.noise_features.eq(6)]
    result = {
        "repeats": repeats,
        "seed": seed,
        "sample_sizes": list(sample_sizes),
        "noise_dimensions": list(noise_dimensions),
        "clean_gap_auc_min": float(clean.gap_auc.min()),
        "clean_continuity_auc_min": float(clean.continuity_auc.min()),
        "six_noise_gap_auc_min": float(noisy.gap_auc.min()),
        "six_noise_continuity_auc_min": float(noisy.continuity_auc.min()),
        "connected_gap_null_median_range_clean": float(
            clean.connected_gap_median.max() - clean.connected_gap_median.min()
        ),
    }
    # CI checks reproducibility and the already-supported two-dimensional signal.
    # Noise-feature performance is reported, not gated, because this is the audit target.
    result["passes_core_audit"] = bool(
        result["clean_gap_auc_min"] >= 0.80
        and result["clean_continuity_auc_min"] >= 0.80
        and np.isfinite(summary.select_dtypes(include=[float, int]).to_numpy()).all()
    )
    return frame, summary, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/robustness_audit"))
    args = parser.parse_args()

    frame, summary, result = run(args.repeats, args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output / "robustness_repeat_results.csv", index=False)
    summary.to_csv(args.output / "robustness_cell_summary.csv", index=False)
    (args.output / "robustness_summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if not result["passes_core_audit"]:
        raise SystemExit("core robustness audit failed")


if __name__ == "__main__":
    main()
