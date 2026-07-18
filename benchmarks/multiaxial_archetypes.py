#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry

SIZES = (60, 120, 240)
ARCHETYPES = ("compact", "broad", "curved", "two_mode", "missing_bridge")


def cloud(kind: str, n: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "compact":
        return rng.normal(0, 0.45, (n, 2))
    if kind == "broad":
        return rng.normal(0, 1.35, (n, 2))
    if kind == "curved":
        t = rng.uniform(-2.5, 2.5, n)
        return np.c_[t, np.sin(1.4 * t) + rng.normal(0, 0.12, n)]
    if kind == "two_mode":
        h = n // 2
        return np.vstack([
            rng.normal((-1.8, 0), (0.35, 0.30), (h, 2)),
            rng.normal((1.8, 0), (0.35, 0.30), (n - h, 2)),
        ])
    if kind == "missing_bridge":
        t = np.concatenate([
            rng.uniform(-2.5, -0.45, n // 2),
            rng.uniform(0.45, 2.5, n - n // 2),
        ])
        return np.c_[t, 0.18 * t + rng.normal(0, 0.16, n)]
    raise ValueError(kind)


def auc(negative: list[float], positive: list[float]) -> float:
    x = np.asarray(negative)
    y = np.asarray(positive)
    return float((y[:, None] > x).mean() + 0.5 * (y[:, None] == x).mean())


def run(repeats: int, seed: int, output: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for n in SIZES:
        for archetype in ARCHETYPES:
            for repeat in range(repeats):
                g = infer_occupancy_geometry(cloud(archetype, n, rng))
                rows.append({
                    "n": n,
                    "archetype": archetype,
                    "repeat": repeat + 1,
                    "span": g.span,
                    "continuity": g.continuity,
                    "path_inefficiency": 1.0 / max(g.continuity, 1e-12),
                    "gap_strength": g.gap_strength,
                })

    output.mkdir(parents=True, exist_ok=True)
    with (output / "multiaxial_archetype_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    contrasts = {
        "extent_broad_vs_compact": ("compact", "broad", "span"),
        "path_curved_vs_compact": ("compact", "curved", "path_inefficiency"),
        "separation_two_mode_vs_compact": ("compact", "two_mode", "gap_strength"),
        "support_interruption_missing_bridge_vs_curved": ("curved", "missing_bridge", "gap_strength"),
    }
    summary: list[dict[str, object]] = []
    for n in SIZES:
        cell = [r for r in rows if r["n"] == n]
        for name, (neg_name, pos_name, metric) in contrasts.items():
            neg = [float(r[metric]) for r in cell if r["archetype"] == neg_name]
            pos = [float(r[metric]) for r in cell if r["archetype"] == pos_name]
            summary.append({
                "n": n,
                "contrast": name,
                "metric": metric,
                "auc": auc(neg, pos),
            })

    with (output / "multiaxial_archetype_auc.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    decision = {
        "minimum_extent_auc": min(r["auc"] for r in summary if r["contrast"] == "extent_broad_vs_compact"),
        "minimum_path_auc": min(r["auc"] for r in summary if r["contrast"] == "path_curved_vs_compact"),
        "minimum_two_mode_gap_auc": min(r["auc"] for r in summary if r["contrast"] == "separation_two_mode_vs_compact"),
        "minimum_missing_bridge_gap_auc": min(r["auc"] for r in summary if r["contrast"] == "support_interruption_missing_bridge_vs_curved"),
        "single_composite_score_fitted": False,
    }
    decision["supports_multiaxial_position"] = bool(
        decision["minimum_extent_auc"] >= 0.8
        and decision["minimum_path_auc"] >= 0.8
        and decision["minimum_two_mode_gap_auc"] >= 0.8
    )
    decision["supports_universal_support_interruption_claim"] = bool(
        decision["minimum_missing_bridge_gap_auc"] >= 0.8
    )
    (output / "multiaxial_archetype_decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260718)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/multiaxial_archetypes"))
    args = parser.parse_args()
    print(json.dumps(run(args.repeats, args.seed, args.output), indent=2))


if __name__ == "__main__":
    main()
