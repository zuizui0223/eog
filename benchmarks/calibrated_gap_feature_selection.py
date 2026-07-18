#!/usr/bin/env python3
"""Predeclared calibration and feature-selection benchmark for EOG issue #3."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry

SAMPLE_SIZES = (30, 60, 120, 240)
SCENARIOS = ("clean", "correlated", "irrelevant")
STRATEGIES = ("ecological", "correlation_filter", "pca90", "all")


def auc(negative: list[float], positive: list[float]) -> float:
    a = np.asarray(negative, float)
    b = np.asarray(positive, float)
    return float(((b[:, None] > a[None, :]).mean() + 0.5 * (b[:, None] == a[None, :]).mean()))


def make_cloud(kind: str, n: int, scenario: str, rng: np.random.Generator) -> np.ndarray:
    if kind == "connected":
        signal = rng.normal(size=(n, 2))
        signal[:, 1] *= 0.45
    elif kind == "two_modes":
        half = n // 2
        signal = np.vstack([
            rng.normal((-1.8, 0.0), (0.30, 0.28), size=(half, 2)),
            rng.normal((1.8, 0.0), (0.30, 0.28), size=(n - half, 2)),
        ])
    else:
        raise ValueError(kind)

    if scenario == "clean":
        return signal
    if scenario == "correlated":
        correlated = np.column_stack([
            signal[:, 0] + rng.normal(0, 0.08, n),
            -signal[:, 1] + rng.normal(0, 0.08, n),
            0.7 * signal[:, 0] + 0.3 * signal[:, 1] + rng.normal(0, 0.08, n),
            signal[:, 0] - signal[:, 1] + rng.normal(0, 0.08, n),
        ])
        return np.column_stack([signal, correlated])
    if scenario == "irrelevant":
        return np.column_stack([signal, rng.normal(size=(n, 6))])
    raise ValueError(scenario)


def select_features(x: np.ndarray, strategy: str) -> np.ndarray:
    if strategy == "ecological":
        return x[:, :2]
    if strategy == "all":
        return x
    if strategy == "correlation_filter":
        keep: list[int] = []
        corr = np.corrcoef(x, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0)
        for j in range(x.shape[1]):
            if all(abs(corr[j, k]) < 0.80 for k in keep):
                keep.append(j)
        return x[:, keep]
    if strategy == "pca90":
        centered = x - x.mean(axis=0, keepdims=True)
        values, vectors = np.linalg.eigh(np.cov(centered, rowvar=False))
        order = np.argsort(values)[::-1]
        values = np.maximum(values[order], 0.0)
        vectors = vectors[:, order]
        total = values.sum()
        if total <= 0:
            return centered[:, :1]
        count = int(np.searchsorted(np.cumsum(values) / total, 0.90) + 1)
        return centered @ vectors[:, :count]
    raise ValueError(strategy)


def calibrated_gap(x: np.ndarray, raw: float, rng: np.random.Generator, null_draws: int) -> float:
    mean = x.mean(axis=0)
    cov = np.cov(x, rowvar=False)
    cov = np.atleast_2d(cov) + np.eye(x.shape[1]) * 1e-8
    null = []
    for _ in range(null_draws):
        reference = rng.multivariate_normal(mean, cov, size=len(x))
        null.append(infer_occupancy_geometry(reference).gap_strength)
    null_array = np.asarray(null)
    # Mid-rank empirical percentile. Comparable across sample sizes by construction.
    return float(((null_array < raw).sum() + 0.5 * (null_array == raw).sum()) / null_draws)


def run(repeats: int, null_draws: int, seed: int, output: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        for scenario in SCENARIOS:
            for repeat in range(repeats):
                for kind in ("connected", "two_modes"):
                    base = make_cloud(kind, n, scenario, rng)
                    for strategy in STRATEGIES:
                        selected = select_features(base, strategy)
                        raw = infer_occupancy_geometry(selected).gap_strength
                        calibrated = calibrated_gap(selected, raw, rng, null_draws)
                        rows.append({
                            "n": n,
                            "scenario": scenario,
                            "repeat": repeat + 1,
                            "kind": kind,
                            "strategy": strategy,
                            "features_retained": selected.shape[1],
                            "raw_gap": raw,
                            "calibrated_gap_percentile": calibrated,
                        })

    output.mkdir(parents=True, exist_ok=True)
    with (output / "calibration_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = []
    for n in SAMPLE_SIZES:
        for scenario in SCENARIOS:
            for strategy in STRATEGIES:
                cell = [r for r in rows if r["n"] == n and r["scenario"] == scenario and r["strategy"] == strategy]
                neg_raw = [float(r["raw_gap"]) for r in cell if r["kind"] == "connected"]
                pos_raw = [float(r["raw_gap"]) for r in cell if r["kind"] == "two_modes"]
                neg_cal = [float(r["calibrated_gap_percentile"]) for r in cell if r["kind"] == "connected"]
                pos_cal = [float(r["calibrated_gap_percentile"]) for r in cell if r["kind"] == "two_modes"]
                summary_rows.append({
                    "n": n,
                    "scenario": scenario,
                    "strategy": strategy,
                    "raw_auc": auc(neg_raw, pos_raw),
                    "calibrated_auc": auc(neg_cal, pos_cal),
                    "connected_raw_median": float(np.median(neg_raw)),
                    "connected_calibrated_median": float(np.median(neg_cal)),
                    "median_features_retained": float(np.median([r["features_retained"] for r in cell])),
                })

    with (output / "calibration_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    ecological = [r for r in summary_rows if r["strategy"] == "ecological"]
    corr = [r for r in summary_rows if r["strategy"] == "correlation_filter"]
    result = {
        "repeats": repeats,
        "null_draws": null_draws,
        "minimum_ecological_calibrated_auc": min(r["calibrated_auc"] for r in ecological),
        "minimum_correlation_filter_calibrated_auc": min(r["calibrated_auc"] for r in corr),
        "maximum_ecological_connected_calibrated_median_deviation": max(abs(r["connected_calibrated_median"] - 0.5) for r in ecological),
    }
    result["passes_predeclared_gate"] = bool(
        result["minimum_ecological_calibrated_auc"] >= 0.90
        and result["maximum_ecological_connected_calibrated_median_deviation"] <= 0.20
    )
    (output / "calibration_gate.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=30)
    parser.add_argument("--null-draws", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/calibrated_gap_feature_selection"))
    args = parser.parse_args()
    result = run(args.repeats, args.null_draws, args.seed, args.output)
    print(json.dumps(result, indent=2))
    if not result["passes_predeclared_gate"]:
        raise SystemExit("predeclared calibration gate failed")


if __name__ == "__main__":
    main()
