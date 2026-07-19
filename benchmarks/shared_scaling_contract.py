#!/usr/bin/env python3
"""Frozen benchmark for comparative EOG scaling and support matching."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import RobustReference, infer_comparative_geometry, infer_occupancy_geometry


def auc(positive: np.ndarray, negative: np.ndarray) -> float:
    return float(np.mean(positive[:, None] > negative[None, :]) + 0.5 * np.mean(positive[:, None] == negative[None, :]))


def compact_cloud(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.normal(0.0, 0.65, size=(n, 2))


def broad_cloud(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.normal(0.0, 1.65, size=(n, 2))


def straight_path(rng: np.random.Generator, n: int) -> np.ndarray:
    t = np.linspace(-2.0, 2.0, n)
    return np.column_stack([t, rng.normal(0.0, 0.025, n)])


def curved_path(rng: np.random.Generator, n: int) -> np.ndarray:
    theta = np.linspace(0.0, np.pi, n)
    return np.column_stack([2.0 * np.cos(theta), 2.0 * np.sin(theta) - 1.0]) + rng.normal(0.0, 0.025, size=(n, 2))


def run(args: argparse.Namespace) -> dict[str, object]:
    rng = np.random.default_rng(args.seed)
    reference = RobustReference(
        median=np.array([0.0, 0.0]),
        scale=np.array([1.0, 1.0]),
        constant=np.array([False, False]),
        provenance="predeclared external coordinate units",
    )
    rows: list[dict[str, object]] = []
    auc_rows: list[dict[str, object]] = []
    for n in args.sample_sizes:
        independent_compact: list[float] = []
        independent_broad: list[float] = []
        shared_compact: list[float] = []
        shared_broad: list[float] = []
        straight_inefficiency: list[float] = []
        curved_inefficiency: list[float] = []
        for repeat in range(1, args.repeats + 1):
            compact = compact_cloud(rng, n)
            broad = broad_cloud(rng, n)
            straight = straight_path(rng, n)
            curved = curved_path(rng, n)

            ci = infer_occupancy_geometry(compact).span
            bi = infer_occupancy_geometry(broad).span
            cs = infer_comparative_geometry(compact, reference).span
            bs = infer_comparative_geometry(broad, reference).span
            si = 1.0 / infer_comparative_geometry(straight, reference).continuity
            ui = 1.0 / infer_comparative_geometry(curved, reference).continuity

            independent_compact.append(ci); independent_broad.append(bi)
            shared_compact.append(cs); shared_broad.append(bs)
            straight_inefficiency.append(si); curved_inefficiency.append(ui)
            rows.extend([
                {"n": n, "repeat": repeat, "family": "compact", "scaling": "independent", "span": ci, "tree_inefficiency": ""},
                {"n": n, "repeat": repeat, "family": "broad", "scaling": "independent", "span": bi, "tree_inefficiency": ""},
                {"n": n, "repeat": repeat, "family": "compact", "scaling": "shared", "span": cs, "tree_inefficiency": ""},
                {"n": n, "repeat": repeat, "family": "broad", "scaling": "shared", "span": bs, "tree_inefficiency": ""},
                {"n": n, "repeat": repeat, "family": "straight_path", "scaling": "shared", "span": "", "tree_inefficiency": si},
                {"n": n, "repeat": repeat, "family": "curved_path", "scaling": "shared", "span": "", "tree_inefficiency": ui},
            ])
        values = {
            "independent_span_broad_vs_compact": auc(np.asarray(independent_broad), np.asarray(independent_compact)),
            "shared_span_broad_vs_compact": auc(np.asarray(shared_broad), np.asarray(shared_compact)),
            "matched_path_curved_vs_straight": auc(np.asarray(curved_inefficiency), np.asarray(straight_inefficiency)),
        }
        for contrast, value in values.items():
            auc_rows.append({"n": n, "contrast": contrast, "auc": value})

    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "shared_scaling_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    with (args.output / "shared_scaling_auc.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(auc_rows[0]))
        writer.writeheader(); writer.writerows(auc_rows)

    independent = [r["auc"] for r in auc_rows if r["contrast"] == "independent_span_broad_vs_compact"]
    shared = [r["auc"] for r in auc_rows if r["contrast"] == "shared_span_broad_vs_compact"]
    path = [r["auc"] for r in auc_rows if r["contrast"] == "matched_path_curved_vs_straight"]
    decision = {
        "maximum_independent_span_auc_deviation_from_chance": max(abs(float(v) - 0.5) for v in independent),
        "minimum_shared_span_auc": min(float(v) for v in shared),
        "minimum_matched_path_auc": min(float(v) for v in path),
        "across_support_path_comparison_performed": False,
        "passes_contract": bool(
            max(abs(float(v) - 0.5) for v in independent) <= 0.20
            and min(float(v) for v in shared) >= 0.90
            and min(float(v) for v in path) >= 0.90
        ),
    }
    (args.output / "shared_scaling_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/shared_scaling"))
    parser.add_argument("--seed", type=int, default=20260719)
    parser.add_argument("--sample-sizes", type=int, nargs="+", default=[60, 120, 240])
    parser.add_argument("--repeats", type=int, default=40)
    args = parser.parse_args()
    decision = run(args)
    print(json.dumps(decision, indent=2))
    if not decision["passes_contract"]:
        raise SystemExit("shared scaling contract gate failed")


if __name__ == "__main__":
    main()
