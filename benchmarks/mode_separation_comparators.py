#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry, minimum_spanning_tree, pairwise_distances, robust_scale

SIZES = (60, 120, 240)
CONNECTED = ("gaussian", "t3", "skewed", "s_curve", "ring", "contam05")
MODES = ("equal_overlap", "equal_medium", "equal_wide", "unequal_20_80", "unequal_35_65")


def cloud(kind: str, n: int, rng: np.random.Generator) -> np.ndarray:
    if kind == "gaussian":
        return rng.multivariate_normal([0, 0], [[1, .55], [.55, .75]], n)
    if kind == "t3":
        z = rng.multivariate_normal([0, 0], [[1, .4], [.4, .7]], n)
        return z / np.sqrt(rng.chisquare(3, n) / 3)[:, None]
    if kind == "skewed":
        z = rng.normal(size=(n, 2)); return np.c_[np.exp(.75 * z[:, 0]), .5 * z[:, 1]]
    if kind == "s_curve":
        t = rng.uniform(-2.5, 2.5, n); return np.c_[t, np.sin(1.4 * t) + rng.normal(0, .14, n)]
    if kind == "ring":
        a = rng.uniform(0, 2 * np.pi, n); rad = 1 + rng.normal(0, .06, n)
        return np.c_[rad * np.cos(a), rad * np.sin(a)]
    if kind == "contam05":
        m = max(1, int(round(.05 * n)))
        core = rng.multivariate_normal([0, 0], [[1, .35], [.35, .65]], n - m)
        ang = rng.uniform(0, 2 * np.pi, m)
        remote = np.c_[5 * np.cos(ang), 5 * np.sin(ang)] + rng.normal(0, .15, (m, 2))
        return np.vstack([core, remote])
    sep = {"equal_overlap": 1.0, "equal_medium": 1.6, "equal_wide": 2.2,
           "unequal_20_80": 1.9, "unequal_35_65": 1.9}[kind]
    p = {"unequal_20_80": .20, "unequal_35_65": .35}.get(kind, .50)
    h = max(2, int(round(n * p)))
    return np.vstack([
        rng.normal((-sep, 0), (.38, .30), (h, 2)),
        rng.normal((sep, 0), (.38, .30), (n - h, 2)),
    ])


def split_balance(n: int, edges: np.ndarray, cut: int) -> float:
    adj = [[] for _ in range(n)]
    for i, (a, b, _) in enumerate(edges):
        if i == cut: continue
        a, b = int(a), int(b); adj[a].append(b); adj[b].append(a)
    lab = np.ones(n, int); stack = [int(edges[cut, 0])]; lab[stack[0]] = 0
    while stack:
        a = stack.pop()
        for b in adj[a]:
            if lab[b]: lab[b] = 0; stack.append(b)
    return float(min((lab == 0).mean(), (lab == 1).mean()))


def core_bridge_score(x: np.ndarray) -> float:
    d = pairwise_distances(x); scales = []
    for i in range(len(x)):
        row = np.delete(d[i], i); k = min(5, len(row))
        scales.append(float(np.median(np.partition(row, k - 1)[:k])))
    keep = np.argsort(scales)[:max(2, int(round(.9 * len(x))))]
    dc = pairwise_distances(x[keep]); edges = minimum_spanning_tree(dc); lengths = edges[:, 2]
    cut = int(np.argmax(lengths)); u, v = int(edges[cut, 0]), int(edges[cut, 1])
    local = []
    for node, other in ((u, v), (v, u)):
        row = np.delete(dc[node], [node, other]); k = min(5, len(row))
        local.append(float(np.median(np.partition(row, k - 1)[:k])))
    return float(lengths[cut]) / max(local) * (split_balance(len(keep), edges, cut) / .5)


def kmeans2(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    z = robust_scale(x); best = None; best_loss = np.inf
    for _ in range(10):
        centers = z[rng.choice(len(z), 2, replace=False)].copy()
        for _ in range(30):
            dist = ((z[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            lab = dist.argmin(axis=1)
            if len(np.unique(lab)) < 2: break
            new = np.vstack([z[lab == j].mean(axis=0) for j in range(2)])
            if np.allclose(new, centers): break
            centers = new
        loss = float(((z - centers[lab]) ** 2).sum())
        if loss < best_loss and len(np.unique(lab)) == 2: best_loss, best = loss, lab.copy()
    return best


def clustering_metrics(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    z = robust_scale(x); lab = kmeans2(x, rng)
    d = np.sqrt(((z[:, None, :] - z[None, :, :]) ** 2).sum(axis=2))
    sil = []
    for i in range(len(z)):
        same = lab == lab[i]; other = ~same
        a = float(d[i, same].sum() / max(1, same.sum() - 1))
        b = float(d[i, other].mean())
        sil.append((b - a) / max(a, b, 1e-12))
    centers = np.vstack([z[lab == j].mean(axis=0) for j in range(2)])
    within = np.mean([np.sqrt(((z[lab == j] - centers[j]) ** 2).sum(axis=1)).mean() for j in range(2)])
    separation = float(np.linalg.norm(centers[0] - centers[1]) / max(within, 1e-12))
    return float(np.mean(sil)), separation


def auc(a: list[float], b: list[float]) -> float:
    x, y = np.asarray(a), np.asarray(b)
    return float((y[:, None] > x).mean() + .5 * (y[:, None] == x).mean())


def run(repeats: int, seed: int, out: Path) -> dict[str, object]:
    rng = np.random.default_rng(seed); rows = []
    for n in SIZES:
        for structure in CONNECTED + MODES:
            for rep in range(repeats):
                x = cloud(structure, n, rng); sil, sep = clustering_metrics(x, rng)
                rows.append({"n": n, "structure": structure,
                    "kind": "connected" if structure in CONNECTED else "mode",
                    "repeat": rep + 1,
                    "raw_gap": infer_occupancy_geometry(x).gap_strength,
                    "core_bridge_score": core_bridge_score(x),
                    "kmeans_silhouette": sil,
                    "centroid_separation": sep})
    out.mkdir(parents=True, exist_ok=True)
    with (out / "mode_comparator_results.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    comps = []
    for n in SIZES:
        neg = [r for r in rows if r["n"] == n and r["kind"] == "connected"]
        contam = [r for r in rows if r["n"] == n and r["structure"] == "contam05"]
        for structure in MODES:
            pos = [r for r in rows if r["n"] == n and r["structure"] == structure]
            rec = {"n": n, "structure": structure}
            for metric in ("raw_gap", "core_bridge_score", "kmeans_silhouette", "centroid_separation"):
                rec[metric + "_auc"] = auc([float(r[metric]) for r in neg], [float(r[metric]) for r in pos])
                rec[metric + "_vs_contam_auc"] = auc([float(r[metric]) for r in contam], [float(r[metric]) for r in pos])
            comps.append(rec)
    with (out / "mode_comparator_auc.csv").open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(comps[0])); w.writeheader(); w.writerows(comps)
    min_bridge = min(r["core_bridge_score_auc"] for r in comps)
    min_sil = min(r["kmeans_silhouette_auc"] for r in comps)
    unequal = [r for r in comps if r["structure"] in {"unequal_20_80", "unequal_35_65"}]
    advantage = min(r["core_bridge_score_vs_contam_auc"] - r["kmeans_silhouette_vs_contam_auc"] for r in unequal)
    decision = {"minimum_core_bridge_auc": min_bridge, "minimum_silhouette_auc": min_sil,
                "minimum_unequal_mode_advantage_vs_contamination": advantage}
    decision["passes_publication_gate"] = bool(min_bridge >= min_sil - .05 and advantage >= .05)
    (out / "mode_comparator_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    return decision


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--repeats", type=int, default=20)
    p.add_argument("--seed", type=int, default=20261001)
    p.add_argument("--output", type=Path, default=Path("benchmark_results/mode_comparators"))
    a = p.parse_args(); print(json.dumps(run(a.repeats, a.seed, a.output), indent=2))

if __name__ == "__main__": main()
