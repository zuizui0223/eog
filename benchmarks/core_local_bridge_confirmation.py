#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry, minimum_spanning_tree, pairwise_distances

SIZES = (60, 120, 240)
DIMS = (2, 4, 8)
CONNECTED = (
    "gaussian_corr", "t3", "t8", "skew_low", "skew_high",
    "s_curve", "ring", "contam_02", "contam_05", "contam_10",
)
FRAGMENTED = (
    "two_sep_14", "two_sep_18", "two_sep_22", "two_20_80", "two_35_65",
    "bridge_narrow", "bridge_medium", "bridge_wide",
)


def _signal(kind: str, n: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "gaussian_corr":
        return rng.multivariate_normal([0, 0], [[1, .6], [.6, .7]], n)
    if kind in {"t3", "t8"}:
        df = 3 if kind == "t3" else 8
        z = rng.multivariate_normal([0, 0], [[1, .45], [.45, .7]], n)
        return z / np.sqrt(rng.chisquare(df, n) / df)[:, None]
    if kind in {"skew_low", "skew_high"}:
        a = .35 if kind == "skew_low" else .9
        z = rng.normal(size=(n, 2))
        return np.c_[np.exp(a * z[:, 0]), .5 * z[:, 1]]
    if kind == "s_curve":
        t = rng.uniform(-2.5, 2.5, n)
        return np.c_[t, np.sin(1.4 * t) + rng.normal(0, .14, n)]
    if kind == "ring":
        a = rng.uniform(0, 2 * np.pi, n)
        rad = 1 + rng.normal(0, .06, n)
        return np.c_[rad * np.cos(a), rad * np.sin(a)]
    if kind.startswith("contam_"):
        frac = {"contam_02": .02, "contam_05": .05, "contam_10": .10}[kind]
        m = max(1, int(round(n * frac)))
        core = rng.multivariate_normal([0, 0], [[1, .35], [.35, .6]], n - m)
        ang = rng.uniform(0, 2 * np.pi, m)
        remote = np.c_[5 * np.cos(ang), 5 * np.sin(ang)] + rng.normal(0, .15, (m, 2))
        return np.vstack([core, remote])
    if kind.startswith("two_sep_"):
        sep = {"two_sep_14": 1.4, "two_sep_18": 1.8, "two_sep_22": 2.2}[kind]
        h = n // 2
        return np.vstack([
            rng.normal((-sep, 0), (.34, .28), (h, 2)),
            rng.normal((sep, 0), (.34, .28), (n - h, 2)),
        ])
    if kind in {"two_20_80", "two_35_65"}:
        p = .20 if kind == "two_20_80" else .35
        h = max(2, int(round(n * p)))
        return np.vstack([
            rng.normal((-1.9, 0), (.32, .27), (h, 2)),
            rng.normal((1.9, 0), (.32, .27), (n - h, 2)),
        ])
    gap = {"bridge_narrow": .35, "bridge_medium": .7, "bridge_wide": 1.05}[kind]
    h = n // 2
    x = np.r_[rng.uniform(-2.8, -gap, h), rng.uniform(gap, 2.8, n - h)]
    return np.c_[x, rng.normal(0, .20, n)]


def cloud(kind: str, n: int, dim: int, rng: np.random.Generator) -> np.ndarray:
    x = _signal(kind, n, rng)
    if dim > 2:
        x = np.column_stack([x, rng.normal(size=(n, dim - 2))])
    return x


def split_balance(n: int, edges: np.ndarray, cut: int) -> float:
    adjacency = [[] for _ in range(n)]
    for idx, (a, b, _) in enumerate(edges):
        if idx == cut:
            continue
        a, b = int(a), int(b)
        adjacency[a].append(b)
        adjacency[b].append(a)
    labels = np.ones(n, dtype=int)
    stack = [int(edges[cut, 0])]
    labels[stack[0]] = 0
    while stack:
        a = stack.pop()
        for b in adjacency[a]:
            if labels[b]:
                labels[b] = 0
                stack.append(b)
    return float(min((labels == 0).mean(), (labels == 1).mean()))


def local_bridge(x: np.ndarray, *, retain: float) -> float:
    d = pairwise_distances(x)
    scales = []
    for i in range(len(x)):
        row = np.delete(d[i], i)
        k = min(5, len(row))
        scales.append(float(np.median(np.partition(row, k - 1)[:k])))
    keep_n = max(2, int(round(len(x) * retain)))
    keep = np.argsort(scales)[:keep_n]
    dc = pairwise_distances(x[keep])
    edges = minimum_spanning_tree(dc)
    lengths = edges[:, 2]
    cut = int(np.argmax(lengths))
    u, v = int(edges[cut, 0]), int(edges[cut, 1])
    endpoint = []
    for node, other in ((u, v), (v, u)):
        row = np.delete(dc[node], [node, other])
        k = min(5, len(row))
        endpoint.append(float(np.median(np.partition(row, k - 1)[:k])))
    contrast = float(lengths[cut]) / max(endpoint)
    return contrast * (split_balance(len(keep), edges, cut) / .5)


def auc(negative: list[float], positive: list[float]) -> float:
    a, b = np.asarray(negative), np.asarray(positive)
    return float((b[:, None] > a).mean() + .5 * (b[:, None] == a).mean())


def run(repeats: int, seed: int, out: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for dim in DIMS:
        for n in SIZES:
            for structure in CONNECTED + FRAGMENTED:
                for repeat in range(repeats):
                    x = cloud(structure, n, dim, rng)
                    rows.append({
                        "dimension": dim,
                        "n": n,
                        "structure": structure,
                        "kind": "connected" if structure in CONNECTED else "fragmented",
                        "repeat": repeat + 1,
                        "raw_gap": infer_occupancy_geometry(x).gap_strength,
                        "untrimmed_local_bridge_score": local_bridge(x, retain=1.0),
                        "core_local_bridge_score": local_bridge(x, retain=.9),
                    })
    out.mkdir(parents=True, exist_ok=True)
    with (out / "confirmation_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

    comparisons: list[dict[str, object]] = []
    for dim in DIMS:
        for n in SIZES:
            neg = [r for r in rows if r["dimension"] == dim and r["n"] == n and r["kind"] == "connected"]
            for structure in FRAGMENTED:
                pos = [r for r in rows if r["dimension"] == dim and r["n"] == n and r["structure"] == structure]
                record: dict[str, object] = {"dimension": dim, "n": n, "structure": structure}
                for metric in ("raw_gap", "untrimmed_local_bridge_score", "core_local_bridge_score"):
                    record[metric + "_auc"] = auc(
                        [float(r[metric]) for r in neg],
                        [float(r[metric]) for r in pos],
                    )
                comparisons.append(record)
    with (out / "confirmation_auc.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader(); writer.writerows(comparisons)

    primary = [r for r in comparisons if r["dimension"] == 2]
    minimum_raw = min(float(r["raw_gap_auc"]) for r in primary)
    minimum_score = min(float(r["core_local_bridge_score_auc"]) for r in primary)
    unequal_20 = min(float(r["core_local_bridge_score_auc"]) for r in primary if r["structure"] == "two_20_80")
    reversal = False
    for n in SIZES:
        connected_cells = [r for r in rows if r["dimension"] == 2 and r["n"] == n and r["kind"] == "connected"]
        for structure in FRAGMENTED:
            fragmented = [r for r in rows if r["dimension"] == 2 and r["n"] == n and r["structure"] == structure]
            frag_median = float(np.median([r["core_local_bridge_score"] for r in fragmented]))
            for connected in CONNECTED:
                conn = [r for r in connected_cells if r["structure"] == connected]
                if float(np.median([r["core_local_bridge_score"] for r in conn])) > frag_median:
                    reversal = True
    decision = {
        "repeats": repeats,
        "seed": seed,
        "minimum_primary_raw_auc": minimum_raw,
        "minimum_primary_score_auc": minimum_score,
        "minimum_primary_auc_improvement": minimum_score - minimum_raw,
        "minimum_20_80_mode_auc": unequal_20,
        "connected_median_reversal": reversal,
    }
    decision["passes_confirmation_gate"] = bool(
        minimum_score >= .80
        and minimum_score - minimum_raw >= .30
        and unequal_20 >= .75
        and not reversal
    )
    (out / "confirmation_decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20260917)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/core_local_bridge_confirmation"))
    args = parser.parse_args()
    result = run(args.repeats, args.seed, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
