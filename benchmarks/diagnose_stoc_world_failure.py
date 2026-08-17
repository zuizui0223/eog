#!/usr/bin/env python3
"""Post-outcome structural diagnostic for the frozen STOC EOG-WF failure.

This script does NOT modify or rescue the confirmatory design. It reuses the exact
frozen source, period-1 transformations, thresholds, anchor IDs, 20 world definitions,
and max_steps=8 to explain why every species was calibration-falsified.

Outputs are explicitly post-hoc/non-confirmatory.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
RUNNER_PATH = HERE / "run_stoc_eogwf_validation.py"
RESULT_PATH = Path("validation/stoc_eogwf/stoc_eogwf_result.json")


def _load_runner():
    spec = importlib.util.spec_from_file_location("_stoc_runner_diag", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load frozen STOC runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def component_labels(adjacency: np.ndarray) -> tuple[np.ndarray, list[int]]:
    n = adjacency.shape[0]
    labels = np.full(n, -1, dtype=int)
    sizes: list[int] = []
    component = 0
    for start in range(n):
        if labels[start] >= 0:
            continue
        queue = deque([start])
        labels[start] = component
        size = 0
        while queue:
            node = queue.popleft()
            size += 1
            for nxt in np.flatnonzero(adjacency[node]):
                nxt = int(nxt)
                if labels[nxt] < 0:
                    labels[nxt] = component
                    queue.append(nxt)
        sizes.append(size)
        component += 1
    return labels, sizes


def shortest_hops_from_sources(adjacency: np.ndarray, sources: np.ndarray) -> np.ndarray:
    n = adjacency.shape[0]
    dist = np.full(n, -1, dtype=int)
    queue = deque()
    for source in sorted(set(int(v) for v in sources)):
        dist[source] = 0
        queue.append(source)
    while queue:
        node = queue.popleft()
        for nxt in np.flatnonzero(adjacency[node]):
            nxt = int(nxt)
            if dist[nxt] < 0:
                dist[nxt] = dist[node] + 1
                queue.append(nxt)
    return dist


def run(source: Path) -> dict[str, object]:
    runner = _load_runner()
    raw = source.read_bytes()
    if len(raw) != runner.EXPECTED_SIZE or runner.git_blob_sha1(raw) != runner.EXPECTED_BLOB_SHA:
        raise ValueError("frozen source identity mismatch")

    df = pd.read_csv(source).rename(columns={"x_wgs84": "X_WGS84", "y_wgs84": "Y_WGS84"})
    calib = df[df["period"].astype(str) == runner.CALIBRATION_PERIOD].copy()
    calib["_site_key"] = calib["site"].astype(str)
    calib = calib.sort_values("_site_key").reset_index(drop=True)
    site_ids = calib["_site_key"].to_numpy(str)
    site_index = {site_id: i for i, site_id in enumerate(site_ids)}

    lon = pd.to_numeric(calib["X_WGS84"], errors="raise").to_numpy(float)
    lat = pd.to_numeric(calib["Y_WGS84"], errors="raise").to_numpy(float)
    geo_dist = runner.haversine_matrix(lon, lat)

    frozen = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
    geo_thresholds = {k: float(v) for k, v in frozen["world_universe"]["geographic_thresholds_km"].items()}
    env_thresholds = {k: float(v) for k, v in frozen["world_universe"]["environment_thresholds"].items()}
    mean = np.asarray(frozen["world_universe"]["environment_mean"], dtype=float)
    sd = np.asarray(frozen["world_universe"]["environment_population_sd"], dtype=float)
    calib_env = calib.loc[:, runner.ENV_COLUMNS].to_numpy(float)
    calib_z = (calib_env - mean) / sd
    env_dist = runner.euclidean_matrix(calib_z)
    worlds = runner.build_world_adjacencies(geo_dist, env_dist, geo_thresholds, env_thresholds)

    world_structure: dict[str, object] = {}
    world_labels: dict[str, np.ndarray] = {}
    for world_id, adjacency in worlds.items():
        labels, sizes = component_labels(adjacency)
        world_labels[world_id] = labels
        degrees = np.sum(adjacency, axis=1)
        world_structure[world_id] = {
            "component_count": len(sizes),
            "largest_component_sites": int(max(sizes)),
            "largest_component_fraction": float(max(sizes) / len(site_ids)),
            "isolated_sites": int(sum(size == 1 for size in sizes)),
            "mean_degree": float(np.mean(degrees)),
            "median_degree": float(np.median(degrees)),
            "max_degree": int(np.max(degrees)),
        }

    frozen_species = {row["species"]: row for row in frozen["species_results"]}
    species_diagnostics: list[dict[str, object]] = []
    for species, frozen_row in frozen_species.items():
        y = pd.to_numeric(calib[species], errors="coerce").to_numpy(float)
        positives = np.flatnonzero(np.isfinite(y) & (y > 0.0))
        anchors = np.asarray([site_index[str(v)] for v in frozen_row["anchor_site_ids"]], dtype=int)
        anchor_set = set(anchors.tolist())
        targets = np.asarray([i for i in positives if int(i) not in anchor_set], dtype=int)

        by_world: list[dict[str, object]] = []
        for world_id, adjacency in worlds.items():
            reachable8 = runner.reachable_within(adjacency, anchors, runner.MAX_STEPS)
            target_reached = int(np.sum(reachable8[targets])) if targets.size else 0
            target_total = int(targets.size)
            coverage = 1.0 if target_total == 0 else float(target_reached / target_total)
            hops = shortest_hops_from_sources(adjacency, anchors)
            target_hops = hops[targets] if targets.size else np.asarray([], dtype=int)
            graph_reachable = target_hops >= 0
            connected_coverage = 1.0 if target_total == 0 else float(np.mean(graph_reachable))
            over8 = int(np.sum(target_hops > runner.MAX_STEPS))
            disconnected = int(np.sum(target_hops < 0))
            finite_hops = target_hops[target_hops >= 0]
            labels = world_labels[world_id]
            positive_components = len(set(int(labels[i]) for i in positives))
            anchor_components = len(set(int(labels[i]) for i in anchors))
            by_world.append({
                "world_id": world_id,
                "target_coverage_within_8": coverage,
                "target_reached_within_8": target_reached,
                "target_total": target_total,
                "target_connected_to_any_anchor_fraction": connected_coverage,
                "target_disconnected_from_all_anchors": disconnected,
                "target_connected_but_over_8_hops": over8,
                "max_finite_target_hops": None if finite_hops.size == 0 else int(np.max(finite_hops)),
                "positive_component_count": positive_components,
                "anchor_component_count": anchor_components,
                "positive_components_without_anchor": int(max(0, positive_components - anchor_components)),
            })

        best = max(by_world, key=lambda row: (row["target_coverage_within_8"], row["target_connected_to_any_anchor_fraction"]))
        species_diagnostics.append({
            "species": species,
            "calibration_positive_sites": int(len(positives)),
            "anchor_sites": int(len(anchors)),
            "target_sites": int(len(targets)),
            "best_world_id": best["world_id"],
            "best_target_coverage_within_8": best["target_coverage_within_8"],
            "best_target_connected_to_any_anchor_fraction": best["target_connected_to_any_anchor_fraction"],
            "best_target_disconnected_from_all_anchors": best["target_disconnected_from_all_anchors"],
            "best_target_connected_but_over_8_hops": best["target_connected_but_over_8_hops"],
            "best_positive_component_count": best["positive_component_count"],
            "best_anchor_component_count": best["anchor_component_count"],
            "worlds": by_world,
        })

    best_coverages = np.asarray([row["best_target_coverage_within_8"] for row in species_diagnostics], dtype=float)
    q90_geo = world_structure["geo_q90"]
    payload: dict[str, object] = {
        "schema_version": "eog_stoc_world_failure_posthoc_v1",
        "status": "posthoc_nonconfirmatory_diagnostic",
        "confirmatory_result_fingerprint": frozen["result_fingerprint"],
        "source_git_blob_sha": runner.EXPECTED_BLOB_SHA,
        "frozen_max_steps": runner.MAX_STEPS,
        "frozen_world_count": len(worlds),
        "world_structure": world_structure,
        "species_diagnostics": species_diagnostics,
        "summary": {
            "species_count": len(species_diagnostics),
            "species_with_full_coverage_in_any_frozen_world": int(np.sum(best_coverages >= 1.0 - 1e-15)),
            "median_best_target_coverage_within_8": float(np.median(best_coverages)),
            "min_best_target_coverage_within_8": float(np.min(best_coverages)),
            "max_best_target_coverage_within_8": float(np.max(best_coverages)),
            "geo_q90_component_count": q90_geo["component_count"],
            "geo_q90_largest_component_fraction": q90_geo["largest_component_fraction"],
            "geo_q90_isolated_sites": q90_geo["isolated_sites"],
            "interpretation_rule": "diagnose frozen world inadequacy only; do not use these values to retune STOC worlds, anchors, or horizon",
        },
    }
    payload["diagnostic_fingerprint"] = runner.canonical_sha256(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = run(args.source)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summary": payload["summary"], "diagnostic_fingerprint": payload["diagnostic_fingerprint"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
