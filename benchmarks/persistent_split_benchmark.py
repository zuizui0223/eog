#!/usr/bin/env python3
"""Benchmark persistent largest-edge splits without a fitted generative null."""
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


def largest_edge_split(x: np.ndarray) -> tuple[np.ndarray, float, float, float]:
    geometry = infer_occupancy_geometry(x)
    edges = geometry.mst_edges
    lengths = edges[:, 2]
    order = np.argsort(lengths)
    largest_index = int(order[-1])
    largest = float(lengths[largest_index])
    second = float(lengths[order[-2]]) if len(lengths) > 1 else largest
    contrast = 1.0 if second <= 0 else largest / second

    adjacency: list[list[int]] = [[] for _ in range(len(x))]
    for edge_index, (source, target, _) in enumerate(edges):
        if edge_index == largest_index:
            continue
        i, j = int(source), int(target)
        adjacency[i].append(j)
        adjacency[j].append(i)

    labels = np.full(len(x), -1, dtype=int)
    start = int(edges[largest_index, 0])
    stack = [start]
    labels[start] = 0
    while stack:
        current = stack.pop()
        for neighbour in adjacency[current]:
            if labels[neighbour] < 0:
                labels[neighbour] = 0
                stack.append(neighbour)
    labels[labels < 0] = 1
    balance = float(min(np.mean(labels == 0), np.mean(labels == 1)))
    return labels, contrast, balance, geometry.gap_strength


def balanced_agreement(reference: np.ndarray, candidate: np.ndarray) -> float:
    scores = []
    for flipped in (candidate, 1 - candidate):
        class_scores = []
        for label in (0, 1):
            mask = reference == label
            if np.any(mask):
                class_scores.append(float(np.mean(flipped[mask] == label)))
        scores.append(float(np.mean(class_scores)))
    return max(scores)


def persistent_split_metrics(
    x: np.ndarray,
    rng: np.random.Generator,
    subsamples: int,
    fraction: float = 0.80,
) -> dict[str, float | bool]:
    full_labels, contrast, balance, full_gap = largest_edge_split(x)
    agreements: list[float] = []
    gap_ratios: list[float] = []
    sample_size = max(2, int(round(len(x) * fraction)))
    for _ in range(subsamples):
        indices = np.sort(rng.choice(len(x), size=sample_size, replace=False))
        sub_labels, _, _, sub_gap = largest_edge_split(x[indices])
        agreements.append(balanced_agreement(full_labels[indices], sub_labels))
        if full_gap > 0 and sub_gap > 0:
            gap_ratios.append(sub_gap / full_gap)

    persistence = float(np.median(agreements))
    if gap_ratios:
        log_error = float(np.median(np.abs(np.log(np.asarray(gap_ratios)))))
        gap_stability = float(np.exp(-log_error))
    else:
        gap_stability = 0.0
    score = float(
        np.log(max(contrast, 1.0))
        * (balance / 0.5)
        * max(0.0, 2.0 * persistence - 1.0)
        * gap_stability
    )
    strong = bool(
        contrast >= 1.5
        and balance >= 0.10
        and persistence >= 0.80
        and gap_stability >= 0.75
    )
    return {
        "gap_strength": full_gap,
        "edge_contrast": contrast,
        "split_balance": balance,
        "split_persistence": persistence,
        "gap_stability": gap_stability,
        "persistent_split_score": score,
        "strong_evidence": strong,
    }


def auc(negative: list[float], positive: list[float]) -> float:
    a = np.asarray(negative, float)
    b = np.asarray(positive, float)
    return float(((b[:, None] > a[None, :]).mean() + 0.5 * (b[:, None] == a[None, :]).mean()))


def run(repeats: int, subsamples: int, seed: int, output: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        for structure in CONNECTED + FRAGMENTED:
            for repeat in range(repeats):
                metrics = persistent_split_metrics(make_cloud(structure, n, rng), rng, subsamples)
                rows.append({
                    "n": n,
                    "structure": structure,
                    "class": "connected" if structure in CONNECTED else "fragmented",
                    "repeat": repeat + 1,
                    **metrics,
                })

    output.mkdir(parents=True, exist_ok=True)
    with (output / "persistent_split_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metrics = ("gap_strength", "edge_contrast", "split_persistence", "persistent_split_score")
    comparison_rows: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        negatives = [r for r in rows if r["n"] == n and r["class"] == "connected"]
        for structure in FRAGMENTED:
            positives = [r for r in rows if r["n"] == n and r["structure"] == structure]
            record: dict[str, object] = {"n": n, "structure": structure}
            for metric in metrics:
                record[f"{metric}_auc"] = auc(
                    [float(r[metric]) for r in negatives],
                    [float(r[metric]) for r in positives],
                )
            comparison_rows.append(record)

    with (output / "persistent_split_auc.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparison_rows[0]))
        writer.writeheader()
        writer.writerows(comparison_rows)

    rate_rows: list[dict[str, object]] = []
    for n in SAMPLE_SIZES:
        for structure in CONNECTED + FRAGMENTED:
            cell = [r for r in rows if r["n"] == n and r["structure"] == structure]
            rate_rows.append({
                "n": n,
                "structure": structure,
                "class": "connected" if structure in CONNECTED else "fragmented",
                "strong_evidence_rate": float(np.mean([bool(r["strong_evidence"]) for r in cell])),
                "median_score": float(np.median([float(r["persistent_split_score"]) for r in cell])),
            })

    with (output / "persistent_split_rates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rate_rows[0]))
        writer.writeheader()
        writer.writerows(rate_rows)

    minimum_raw_auc = min(float(r["gap_strength_auc"]) for r in comparison_rows)
    minimum_score_auc = min(float(r["persistent_split_score_auc"]) for r in comparison_rows)
    maximum_connected_rate = max(float(r["strong_evidence_rate"]) for r in rate_rows if r["class"] == "connected")
    minimum_fragmented_rate = min(float(r["strong_evidence_rate"]) for r in rate_rows if r["class"] == "fragmented")
    decision = {
        "repeats": repeats,
        "subsamples": subsamples,
        "minimum_raw_gap_auc": minimum_raw_auc,
        "minimum_persistent_score_auc": minimum_score_auc,
        "auc_improvement": minimum_score_auc - minimum_raw_auc,
        "maximum_connected_strong_rate": maximum_connected_rate,
        "minimum_fragmented_strong_rate": minimum_fragmented_rate,
    }
    decision["passes_frozen_gate"] = bool(
        minimum_score_auc >= 0.80
        and decision["auc_improvement"] >= 0.05
        and maximum_connected_rate <= 0.15
        and minimum_fragmented_rate >= 0.50
    )
    (output / "persistent_split_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--subsamples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/persistent_split"))
    args = parser.parse_args()
    result = run(args.repeats, args.subsamples, args.seed, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
