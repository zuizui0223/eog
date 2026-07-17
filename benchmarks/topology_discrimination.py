#!/usr/bin/env python3
"""Synthetic discrimination benchmark for environmental occupancy geometry.

The fragmentation scenarios are affine-matched to the same mean and covariance,
so PCA breadth and Gaussian covariance volume are held constant. The benchmark
then checks whether gap strength detects fragmentation and continuity detects
path tortuosity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog import infer_occupancy_geometry


def _match_moments(values: np.ndarray, target: np.ndarray) -> np.ndarray:
    x = values - values.mean(axis=0)
    t = target - target.mean(axis=0)
    cov_x = np.cov(x, rowvar=False)
    cov_t = np.cov(t, rowvar=False)
    ex, vx = np.linalg.eigh(cov_x)
    et, vt = np.linalg.eigh(cov_t)
    wx = vx @ np.diag(1.0 / np.sqrt(np.maximum(ex, 1e-12))) @ vx.T
    ct = vt @ np.diag(np.sqrt(np.maximum(et, 1e-12))) @ vt.T
    return x @ wx @ ct + target.mean(axis=0)


def _fragmentation(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    connected = rng.normal(size=(n, 2))
    connected[:, 1] *= 0.35
    two = np.vstack([
        rng.normal(loc=(-2.0, 0.0), scale=(0.35, 0.25), size=(n // 2, 2)),
        rng.normal(loc=(2.0, 0.0), scale=(0.35, 0.25), size=(n - n // 2, 2)),
    ])
    t = np.linspace(-2.5, 2.5, n)
    bridge = np.column_stack([t, rng.normal(scale=0.20, size=n)])
    bridge = bridge[np.abs(bridge[:, 0]) > 0.65]
    bridge = bridge[rng.choice(len(bridge), size=n, replace=True)]
    return {
        "connected": connected,
        "two_modes": _match_moments(two, connected),
        "missing_bridge": _match_moments(bridge, connected),
    }


def _paths(rng: np.random.Generator, n: int) -> dict[str, np.ndarray]:
    t = np.linspace(-1.0, 1.0, n)
    straight = np.column_stack([t, t]) + rng.normal(scale=0.015, size=(n, 2))
    theta = np.linspace(0.0, np.pi, n)
    curved = np.column_stack([np.cos(theta), np.sin(theta)])
    curved += rng.normal(scale=0.015, size=(n, 2))
    return {"straight": straight, "curved": curved}


def run(repeats: int, points: int, seed: int) -> dict[str, float | bool]:
    rng = np.random.default_rng(seed)
    gap_two, gap_bridge, path_ratio = [], [], []
    for _ in range(repeats):
        f = {k: infer_occupancy_geometry(v) for k, v in _fragmentation(rng, points).items()}
        gap_two.append(f["two_modes"].gap_strength / f["connected"].gap_strength)
        gap_bridge.append(f["missing_bridge"].gap_strength / f["connected"].gap_strength)
        p = {k: infer_occupancy_geometry(v) for k, v in _paths(rng, points).items()}
        path_ratio.append(p["curved"].continuity / p["straight"].continuity)
    result = {
        "two_modes_gap_ratio_median": float(np.median(gap_two)),
        "missing_bridge_gap_ratio_median": float(np.median(gap_bridge)),
        "curved_to_straight_continuity_ratio_median": float(np.median(path_ratio)),
    }
    result["passes"] = bool(
        result["two_modes_gap_ratio_median"] > 1.5
        and result["missing_bridge_gap_ratio_median"] > 1.5
        and result["curved_to_straight_continuity_ratio_median"] < 0.75
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--points", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260731)
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/topology_summary.json"))
    args = parser.parse_args()
    result = run(args.repeats, args.points, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["passes"]:
        raise SystemExit("topology discrimination gate failed")


if __name__ == "__main__":
    main()
