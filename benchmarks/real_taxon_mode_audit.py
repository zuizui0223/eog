#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from eog import infer_occupancy_geometry
from eog.chelsa import DEFAULT_VARIABLES, sample_chelsa_at_coordinates
from mode_separation_comparators import clustering_metrics, core_bridge_score
from real_taxon_pilot import cap_evenly, fetch_occurrences, thin


def q(values: list[float], p: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=float), p))


def run(args: argparse.Namespace) -> dict[str, object]:
    rng = np.random.default_rng(args.seed)
    declarations = list(csv.DictReader(args.manifest.open(encoding="utf-8")))
    rows: list[dict[str, object]] = []
    stability: list[dict[str, object]] = []

    for declaration in declarations:
        base: dict[str, object] = {
            "pair_id": declaration["pair_id"],
            "kingdom": declaration["kingdom"],
            "scientific_name": declaration["scientific_name"],
            "status": "failed",
            "failure_reason": "",
        }
        try:
            taxon_key, records = fetch_occurrences(declaration, args.max_gbif_records)
            thinned = cap_evenly(thin(records, args.thinning_km), args.max_analysis_records)
            sampled = sample_chelsa_at_coordinates(pd.DataFrame(thinned), variables=DEFAULT_VARIABLES)
            complete = sampled.frame.iloc[sampled.complete_indices].reset_index(drop=True)
            base.update({
                "gbif_taxon_key": taxon_key,
                "raw_coordinate_count": len(records),
                "thinned_count": len(thinned),
                "complete_chelsa_count": len(complete),
                "variables": ";".join(DEFAULT_VARIABLES),
            })
            if len(complete) < args.minimum_n:
                base.update(status="ineligible", failure_reason=f"complete_n<{args.minimum_n}")
                rows.append(base)
                continue

            states = complete[list(DEFAULT_VARIABLES)].to_numpy(float)
            silhouette, separation = clustering_metrics(states, rng)
            full = {
                "gap_strength": infer_occupancy_geometry(states).gap_strength,
                "core_bridge_score": core_bridge_score(states),
                "kmeans_silhouette": silhouette,
                "centroid_separation": separation,
            }
            base.update(status="eligible", **full)

            subset_n = max(args.minimum_n, int(math.floor(len(states) * args.subsample_fraction)))
            per_metric = {name: [] for name in full}
            for repeat in range(args.stability_repeats):
                subset = states[rng.choice(len(states), size=subset_n, replace=False)]
                sub_silhouette, sub_separation = clustering_metrics(subset, rng)
                values = {
                    "gap_strength": infer_occupancy_geometry(subset).gap_strength,
                    "core_bridge_score": core_bridge_score(subset),
                    "kmeans_silhouette": sub_silhouette,
                    "centroid_separation": sub_separation,
                }
                for name, value in values.items():
                    per_metric[name].append(float(value))
                stability.append({
                    "pair_id": declaration["pair_id"],
                    "repeat": repeat + 1,
                    "subset_n": subset_n,
                    **values,
                })
            for name, values in per_metric.items():
                base[f"{name}_subsample_p10"] = q(values, .10)
                base[f"{name}_subsample_median"] = q(values, .50)
                base[f"{name}_subsample_p90"] = q(values, .90)
            rows.append(base)
        except Exception as exc:
            base["failure_reason"] = f"{type(exc).__name__}: {exc}"
            rows.append(base)

    eligible = [row for row in rows if row["status"] == "eligible"]
    for metric in ("core_bridge_score", "kmeans_silhouette"):
        ordered = sorted(eligible, key=lambda row: float(row[metric]))
        for rank, row in enumerate(ordered, start=1):
            row[f"{metric}_rank"] = rank
    for row in eligible:
        n = len(eligible)
        bridge_high = int(row["core_bridge_score_rank"]) > 2 * n / 3
        silhouette_high = int(row["kmeans_silhouette_rank"]) > 2 * n / 3
        bridge_low = int(row["core_bridge_score_rank"]) <= n / 3
        silhouette_low = int(row["kmeans_silhouette_rank"]) <= n / 3
        if bridge_high and silhouette_high:
            label = "both_high"
        elif bridge_high and silhouette_low:
            label = "bridge_high_silhouette_low"
        elif silhouette_high and bridge_low:
            label = "silhouette_high_bridge_low"
        else:
            label = "intermediate_or_mixed"
        row["within_cohort_agreement_class"] = label

    args.output.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with (args.output / "real_taxon_mode_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    stability_fields = list(stability[0]) if stability else ["pair_id", "repeat", "subset_n"]
    with (args.output / "real_taxon_mode_stability.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=stability_fields); writer.writeheader(); writer.writerows(stability)

    decision = {
        "declared_pairs": len(declarations),
        "status_rows": len(rows),
        "eligible_pairs": len(eligible),
        "failed_pairs": sum(row["status"] == "failed" for row in rows),
        "ineligible_pairs": sum(row["status"] == "ineligible" for row in rows),
        "eligible_with_stability": len({row["pair_id"] for row in stability}),
    }
    decision["passes_completion_gate"] = bool(
        decision["status_rows"] == decision["declared_pairs"]
        and decision["eligible_with_stability"] == decision["eligible_pairs"]
        and decision["eligible_pairs"] >= args.minimum_eligible
    )
    (args.output / "real_taxon_mode_decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("benchmarks/real_taxon_pilot_manifest.csv"))
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/real_taxon_mode_audit"))
    parser.add_argument("--seed", type=int, default=20261015)
    parser.add_argument("--max-gbif-records", type=int, default=3000)
    parser.add_argument("--max-analysis-records", type=int, default=240)
    parser.add_argument("--thinning-km", type=float, default=10.0)
    parser.add_argument("--minimum-n", type=int, default=60)
    parser.add_argument("--minimum-eligible", type=int, default=4)
    parser.add_argument("--stability-repeats", type=int, default=20)
    parser.add_argument("--subsample-fraction", type=float, default=.8)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, indent=2))
    if not result["passes_completion_gate"]:
        raise SystemExit("real-taxon mode audit completion gate failed")


if __name__ == "__main__":
    main()
