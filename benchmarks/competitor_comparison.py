"""Frozen comparison of EOG with established multivariate comparators."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from eog.comparative import fit_robust_reference, infer_comparative_geometry, transform_with_reference
from eog.comparators import (
    convex_hull_area_2d,
    energy_distance,
    gaussian_linear_extent,
    mean_centroid_distance,
    median_centroid_distance,
)

METRICS = ("eog_span", "mean_centroid", "median_centroid", "gaussian_linear", "hull_linear")
SCENARIOS = ("dilation", "unequal_null", "outlier", "irrelevant", "curved", "multimodal", "equal_null")


def _log_ratio(value_b: float, value_a: float) -> float:
    if value_a <= 0.0 or value_b <= 0.0:
        return float("nan")
    return float(np.log(value_b / value_a))


def _calculate(group_a: np.ndarray, group_b: np.ndarray, reference) -> dict[str, float]:
    a = transform_with_reference(group_a, reference)
    b = transform_with_reference(group_b, reference)
    span_a = infer_comparative_geometry(group_a, reference).span
    span_b = infer_comparative_geometry(group_b, reference).span
    result = {
        "eog_span": _log_ratio(span_b, span_a),
        "mean_centroid": _log_ratio(mean_centroid_distance(b), mean_centroid_distance(a)),
        "median_centroid": _log_ratio(median_centroid_distance(b), median_centroid_distance(a)),
        "gaussian_linear": _log_ratio(gaussian_linear_extent(b), gaussian_linear_extent(a)),
        "energy_distance": energy_distance(a, b),
        "hull_linear": float("nan"),
    }
    if a.shape[1] == 2:
        area_a = convex_hull_area_2d(a)
        area_b = convex_hull_area_2d(b)
        result["hull_linear"] = 0.5 * _log_ratio(area_b, area_a)
    return result


def _generate(name: str, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    if name == "dilation":
        return rng.normal(size=(80, 2)), 2.0 * rng.normal(size=(80, 2))
    if name == "unequal_null":
        return rng.normal(size=(40, 2)), rng.normal(size=(160, 2))
    if name == "outlier":
        a = rng.normal(size=(80, 2))
        b = rng.normal(size=(80, 2))
        b[rng.choice(80, 4, replace=False)] *= 8.0
        return a, b
    if name == "irrelevant":
        a = np.c_[rng.normal(size=(80, 2)), rng.normal(size=(80, 6))]
        b = np.c_[2.0 * rng.normal(size=(80, 2)), rng.normal(size=(80, 6))]
        return a, b
    if name == "curved":
        t = np.linspace(-2.0, 2.0, 80)
        a = np.c_[t, rng.normal(0.0, 0.08, 80)]
        theta = np.linspace(-np.pi / 2.0, np.pi / 2.0, 80)
        b = np.c_[2.0 * np.sin(theta), 2.0 * np.cos(theta) - 1.0]
        b += rng.normal(0.0, 0.05, b.shape)
        return a, b
    if name == "multimodal":
        a = np.c_[rng.normal(0.0, np.sqrt(4.16), 80), rng.normal(0.0, 0.4, 80)]
        modes = rng.choice([-2.0, 2.0], 80)
        b = np.c_[modes + rng.normal(0.0, 0.4, 80), rng.normal(0.0, 0.4, 80)]
        return a, b
    return rng.normal(size=(80, 2)), rng.normal(size=(80, 2))


def run_benchmark(*, seed: int = 20260719, replicates: int = 20, resamples: int = 20, fraction: float = 0.8) -> dict:
    rng = np.random.default_rng(seed)
    raw: dict[str, list[dict[str, float | bool]]] = {}
    for scenario in SCENARIOS:
        scenario_records = []
        for _ in range(replicates):
            a, b = _generate(scenario, rng)
            reference = fit_robust_reference(
                rng.normal(size=(500, a.shape[1])), provenance="frozen external standard-normal reference"
            )
            draw_size = max(4, int(min(len(a), len(b)) * fraction))
            draws = {key: [] for key in (*METRICS, "energy_distance")}
            for _ in range(resamples):
                sampled_a = a[rng.choice(len(a), draw_size, replace=False)]
                sampled_b = b[rng.choice(len(b), draw_size, replace=False)]
                values = _calculate(sampled_a, sampled_b, reference)
                for key, value in values.items():
                    draws[key].append(value)
            record: dict[str, float | bool] = {}
            for key, values in draws.items():
                array = np.asarray(values, dtype=float)
                finite = np.isfinite(array)
                record[key] = float(np.nanmedian(array)) if finite.any() else float("nan")
                if key != "energy_distance":
                    record[f"{key}_supported"] = bool(
                        finite.any()
                        and max(np.mean(array[finite] > 0.0), np.mean(array[finite] < 0.0)) >= 0.90
                    )
            scenario_records.append(record)
        raw[scenario] = scenario_records

    summary: dict[str, dict] = {}
    for scenario, records in raw.items():
        summary[scenario] = {}
        for key in (*METRICS, "energy_distance"):
            values = np.asarray([record[key] for record in records], dtype=float)
            finite = np.isfinite(values)
            entry = {"median": None, "q10": None, "q90": None}
            if finite.any():
                entry = {
                    "median": float(np.nanmedian(values)),
                    "q10": float(np.nanquantile(values, 0.10)),
                    "q90": float(np.nanquantile(values, 0.90)),
                }
            if key != "energy_distance":
                entry["directional_support_rate"] = float(
                    np.mean([record[f"{key}_supported"] for record in records])
                )
                if scenario == "dilation" and finite.any():
                    entry["median_abs_error_log2"] = float(
                        np.nanmedian(np.abs(values - np.log(2.0)))
                    )
            summary[scenario][key] = entry
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(run_benchmark(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
