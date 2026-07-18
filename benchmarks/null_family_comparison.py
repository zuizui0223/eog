#!/usr/bin/env python3
"""Compare connected-null families for calibrated EOG gap strength."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry

SAMPLE_SIZES = (60, 120, 240)
CONNECTED = ("gaussian", "heavy_tail", "skewed", "banana")
FRAGMENTED = ("two_modes", "missing_bridge")
NULL_FAMILIES = ("gaussian", "student_t", "gaussian_copula", "radial_bootstrap")


def _covariance(x: np.ndarray) -> np.ndarray:
    cov = np.atleast_2d(np.cov(x, rowvar=False))
    return cov + np.eye(x.shape[1]) * 1e-8


def _sqrt_matrix(cov: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(cov)
    return vectors @ np.diag(np.sqrt(np.maximum(values, 1e-10))) @ vectors.T


def _whitener(cov: np.ndarray) -> np.ndarray:
    values, vectors = np.linalg.eigh(cov)
    return vectors @ np.diag(1.0 / np.sqrt(np.maximum(values, 1e-10))) @ vectors.T


def _match_moments(x: np.ndarray, target: np.ndarray) -> np.ndarray:
    centered = x - x.mean(axis=0)
    transformed = centered @ _whitener(_covariance(x)) @ _sqrt_matrix(_covariance(target))
    return transformed + target.mean(axis=0)


def make_cloud(kind: str, n: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "gaussian":
        x = rng.normal(size=(n, 2))
        x[:, 1] *= 0.45
        return x
    if kind == "heavy_tail":
        z = rng.normal(size=(n, 2))
        scale = np.sqrt(rng.chisquare(4, size=n) / 4)[:, None]
        x = z / scale
        x[:, 1] *= 0.45
        return x
    if kind == "skewed":
        z = rng.normal(size=(n, 2))
        return np.column_stack([np.exp(0.65 * z[:, 0]), 0.45 * z[:, 1]])
    if kind == "banana":
        x = rng.normal(size=n)
        y = 0.30 * rng.normal(size=n) + 0.55 * (x * x - 1.0)
        return np.column_stack([x, y])
    if kind == "two_modes":
        half = n // 2
        return np.vstack([
            rng.normal((-1.8, 0.0), (0.30, 0.25), size=(half, 2)),
            rng.normal((1.8, 0.0), (0.30, 0.25), size=(n - half, 2)),
        ])
    if kind == "missing_bridge":
        left = rng.uniform(-2.5, -0.65, size=n // 2)
        right = rng.uniform(0.65, 2.5, size=n - n // 2)
        axis = np.concatenate([left, right])
        return np.column_stack([axis, rng.normal(0, 0.20, size=n)])
    raise ValueError(kind)


def _normal_scores(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    n, p = x.shape
    base = np.sort(rng.standard_normal(n))
    scores = np.empty_like(x, dtype=float)
    for j in range(p):
        order = np.argsort(x[:, j], kind="mergesort")
        scores[order, j] = base
    return scores


def draw_reference(x: np.ndarray, family: str, rng: np.random.Generator) -> np.ndarray:
    n, p = x.shape
    mean = x.mean(axis=0)
    cov = _covariance(x)
    root = _sqrt_matrix(cov)
    if family == "gaussian":
        return rng.normal(size=(n, p)) @ root + mean
    if family == "student_t":
        df = 5.0
        z = rng.normal(size=(n, p))
        scale = np.sqrt(rng.chisquare(df, size=n) / df)[:, None]
        standardized = (z / scale) * np.sqrt((df - 2.0) / df)
        return standardized @ root + mean
    if family == "gaussian_copula":
        scores = _normal_scores(x, rng)
        corr = np.corrcoef(scores, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0) + np.eye(p) * 1e-8
        latent = rng.multivariate_normal(np.zeros(p), corr, size=n)
        result = np.empty_like(x, dtype=float)
        for j in range(p):
            ranks = np.argsort(np.argsort(latent[:, j], kind="mergesort"), kind="mergesort")
            result[:, j] = np.sort(x[:, j])[ranks]
        return result
    if family == "radial_bootstrap":
        centered = x - mean
        white = centered @ _whitener(cov)
        radii = np.linalg.norm(white, axis=1)
        directions = rng.normal(size=(n, p))
        directions /= np.maximum(np.linalg.norm(directions, axis=1, keepdims=True), 1e-12)
        sampled_radii = rng.choice(radii, size=n, replace=True)
        reference = directions * sampled_radii[:, None]
        return reference @ root + mean
    raise ValueError(family)


def calibrated_percentile(x: np.ndarray, family: str, draws: int, rng: np.random.Generator) -> float:
    raw = infer_occupancy_geometry(x).gap_strength
    null = np.asarray([
        infer_occupancy_geometry(draw_reference(x, family, rng)).gap_strength
        for _ in range(draws)
    ])
    return float(((null < raw).sum() + 0.5 * (null == raw).sum()) / draws)


def auc(negative: list[float], positive: list[float]) -> float:
    a = np.asarray(negative, float)
    b = np.asarray(positive, float)
    return float(((b[:, None] > a[None, :]).mean() + 0.5 * (b[:, None] == a[None, :]).mean()))


def run(repeats: int, null_draws: int, seed: int, output: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        for structure in CONNECTED + FRAGMENTED:
            for repeat in range(repeats):
                cloud = make_cloud(structure, n, rng)
                for family in NULL_FAMILIES:
                    rows.append({
                        "n": n,
                        "structure": structure,
                        "class": "connected" if structure in CONNECTED else "fragmented",
                        "repeat": repeat + 1,
                        "null_family": family,
                        "gap_percentile": calibrated_percentile(cloud, family, null_draws, rng),
                    })

    output.mkdir(parents=True, exist_ok=True)
    with (output / "null_family_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    cell_summary: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        for structure in CONNECTED + FRAGMENTED:
            for family in NULL_FAMILIES:
                values = [float(r["gap_percentile"]) for r in rows if r["n"] == n and r["structure"] == structure and r["null_family"] == family]
                cell_summary.append({
                    "n": n,
                    "structure": structure,
                    "class": "connected" if structure in CONNECTED else "fragmented",
                    "null_family": family,
                    "median_percentile": float(np.median(values)),
                    "upper_tail_rate": float(np.mean(np.asarray(values) >= 0.95)),
                })

    with (output / "null_family_cell_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(cell_summary[0]))
        writer.writeheader()
        writer.writerows(cell_summary)

    family_summary: list[dict[str, object]] = []
    for family in NULL_FAMILIES:
        connected_cells = [r for r in cell_summary if r["null_family"] == family and r["class"] == "connected"]
        calibration_loss = float(np.mean([
            abs(float(r["median_percentile"]) - 0.5) + abs(float(r["upper_tail_rate"]) - 0.05)
            for r in connected_cells
        ]))
        aucs: list[float] = []
        detections: list[float] = []
        for n in SAMPLE_SIZES:
            negatives = [float(r["gap_percentile"]) for r in rows if r["n"] == n and r["class"] == "connected" and r["null_family"] == family]
            for structure in FRAGMENTED:
                positives = [float(r["gap_percentile"]) for r in rows if r["n"] == n and r["structure"] == structure and r["null_family"] == family]
                aucs.append(auc(negatives, positives))
                detections.append(float(np.mean(np.asarray(positives) >= 0.95)))
        eligible = bool(calibration_loss <= 0.25 and min(aucs) >= 0.80 and min(detections) >= 0.50)
        family_summary.append({
            "null_family": family,
            "calibration_loss": calibration_loss,
            "minimum_fragmented_auc": min(aucs),
            "minimum_fragmented_detection": min(detections),
            "eligible_primary": eligible,
        })

    eligible = [r for r in family_summary if r["eligible_primary"]]
    order = {name: i for i, name in enumerate(NULL_FAMILIES)}
    eligible.sort(key=lambda r: (
        float(r["calibration_loss"]),
        -float(r["minimum_fragmented_auc"]),
        -float(r["minimum_fragmented_detection"]),
        order[str(r["null_family"])],
    ))
    primary = str(eligible[0]["null_family"]) if eligible else None
    sensitivity = str(eligible[1]["null_family"]) if len(eligible) > 1 else None

    with (output / "null_family_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(family_summary[0]))
        writer.writeheader()
        writer.writerows(family_summary)

    decision = {
        "repeats": repeats,
        "null_draws": null_draws,
        "primary_null": primary,
        "sensitivity_null": sensitivity,
        "eligible_count": len(eligible),
        "selection_rule_applied": True,
        "ready_for_manuscript_scale": primary is not None,
    }
    (output / "null_family_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--null-draws", type=int, default=24)
    parser.add_argument("--seed", type=int, default=20260820)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/null_family_comparison"))
    args = parser.parse_args()
    result = run(args.repeats, args.null_draws, args.seed, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
