"""Run the predeclared A-Islands reachability-mode secondary analyses.

This script does not alter the frozen primary estimand. It reuses the exact primary
support model, spatial folds, nearest-anchor distance conditioning, 5x5 strata, and
12 frozen reachability scenarios. The two secondary scores were already exposed by
the frozen reachability contract:

- geography-only connected frequency (four geographic-radius scenarios);
- environmentally constrained connected frequency (eight geo+environment scenarios).

As a drift guard, the script also recomputes the combined primary score and requires
its species-level mean to match the first authoritative execution.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import run_aislands_authoritative_benchmark as runner
import run_aislands_authoritative_benchmark_fast as fast
from eog.conditional_reachability import conditional_reachability_concordance
from eog.support_model import SupportModelError, fit_penalized_logistic_support

EXPECTED_PRIMARY_MEAN = 0.6177465917820878
BOOTSTRAP_REPLICATES = 10_000
SIGN_FLIP_REPLICATES = 100_000
RANDOM_SEED = 20260808
MODES = (
    ("combined", "connected_frequency"),
    ("geography_only", "geography_only_connected_frequency"),
    ("environmentally_constrained", "environmentally_constrained_connected_frequency"),
)


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _summarize(values: np.ndarray, *, seed: int) -> dict[str, object]:
    if values.size == 0:
        return {
            "n_species_estimable": 0,
            "mean_conditional_concordance": None,
            "bootstrap_95_ci": None,
            "sign_flip_two_sided_p": None,
        }
    mean = float(np.mean(values))
    rng = np.random.default_rng(seed)
    bootstrap = np.mean(
        rng.choice(values, size=(BOOTSTRAP_REPLICATES, len(values)), replace=True),
        axis=1,
    )
    centered = values - 0.5
    observed_abs = abs(float(np.mean(centered)))
    exceed = 0
    chunk = 1000
    for start in range(0, SIGN_FLIP_REPLICATES, chunk):
        size = min(chunk, SIGN_FLIP_REPLICATES - start)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(size, len(centered)))
        simulated = np.abs(np.mean(signs * centered[None, :], axis=1))
        exceed += int(np.sum(simulated >= observed_abs))
    return {
        "n_species_estimable": int(values.size),
        "mean_conditional_concordance": mean,
        "bootstrap_95_ci": [
            float(np.quantile(bootstrap, 0.025)),
            float(np.quantile(bootstrap, 0.975)),
        ],
        "sign_flip_two_sided_p": float((exceed + 1) / (SIGN_FLIP_REPLICATES + 1)),
    }


def run(
    island_data: Path,
    species_data: Path,
    cohort: Path,
    folds: Path,
    climate: Path,
    fold_output: Path,
    species_output: Path,
    summary_output: Path,
) -> dict[str, object]:
    hashes = {
        "cohort": runner._sha256(cohort),
        "folds": runner._sha256(folds),
        "climate": runner._sha256(climate),
        "island_data": runner._sha256(island_data),
        "species_data": runner._sha256(species_data),
    }
    if hashes["cohort"] != runner.FROZEN_COHORT_SHA256:
        raise ValueError("cohort does not match frozen pre-outcome SHA-256")
    if hashes["folds"] != runner.FROZEN_FOLDS_SHA256:
        raise ValueError("spatial folds do not match frozen pre-outcome SHA-256")
    if hashes["climate"] != runner.FROZEN_CLIMATE_SHA256:
        raise ValueError("climate table does not match frozen pre-outcome SHA-256")

    islands = runner._read(island_data)
    species_rows = runner._read(species_data)
    cohort_rows = runner._read(cohort)
    fold_rows = runner._read(folds)
    climate_rows = runner._read(climate)

    island_list = runner._col(islands, "List_ID", "list_ID")
    island_id = runner._col(islands, "Island_ID", "island_ID")
    species_list = runner._col(species_rows, "List_ID", "list_ID")
    species_name = runner._col(species_rows, "Species_update", "species_update")
    cohort_name = runner._col(cohort_rows, "species")
    fold_id_col = runner._col(fold_rows, "island_id")
    fold_col = runner._col(fold_rows, "fold")
    x_col = runner._col(fold_rows, "x")
    y_col = runner._col(fold_rows, "y")
    climate_id = runner._col(climate_rows, "island_id")
    climate_cols = [runner._col(climate_rows, predictor) for predictor in runner.PREDICTORS]

    list_to_island = {
        runner._canonical_id(row[island_list]): runner._canonical_id(row[island_id])
        for row in islands
    }
    surveyed = sorted(
        {
            runner._canonical_id(list_to_island[runner._canonical_id(row[species_list])])
            for row in species_rows
        },
        key=int,
    )
    if len(surveyed) != 842:
        raise ValueError(f"expected 842 surveyed islands, got {len(surveyed)}")

    fold_by_island = {
        runner._canonical_id(row[fold_id_col]): int(row[fold_col]) for row in fold_rows
    }
    coords = {
        runner._canonical_id(row[fold_id_col]): (float(row[y_col]), float(row[x_col]))
        for row in fold_rows
    }
    climate_by_island = {
        runner._canonical_id(row[climate_id]): np.asarray(
            [float(row[col]) for col in climate_cols], dtype=float
        )
        for row in climate_rows
    }

    taxa = sorted({row[cohort_name].strip() for row in cohort_rows if row[cohort_name].strip()})
    if len(taxa) != 886:
        raise ValueError(f"expected 886 frozen primary taxa, got {len(taxa)}")
    taxon_set = set(taxa)
    presence = {taxon: set() for taxon in taxa}
    for row in species_rows:
        taxon = row[species_name].strip()
        if taxon not in taxon_set:
            continue
        list_id = runner._canonical_id(row[species_list])
        presence[taxon].add(list_to_island[list_id])

    node_ids = tuple(surveyed)
    x = np.vstack([climate_by_island[node] for node in node_ids])
    lat = np.asarray([coords[node][0] for node in node_ids], dtype=float)
    lon = np.asarray([coords[node][1] for node in node_ids], dtype=float)
    fold_vector = np.asarray([fold_by_island[node] for node in node_ids], dtype=int)

    fold_results: list[dict[str, object]] = []
    species_accumulator = {
        taxon: {mode: [] for mode, _ in MODES} for taxon in taxa
    }

    for taxon in taxa:
        labels = np.asarray([int(node in presence[taxon]) for node in node_ids], dtype=int)
        for fold in range(1, 6):
            heldout = fold_vector == fold
            training = ~heldout
            anchors = training & (labels == 1)
            try:
                model = fit_penalized_logistic_support(
                    x[training], labels[training], l2_penalty=1.0, min_class_count=5
                )
                support = model.predict_support(x)
                if np.sum(anchors) < 5:
                    raise ValueError("fewer than five training-presence anchors")
                reach = fast._cached_evaluate(node_ids, lat, lon, x, training, anchors)
                held_labels = labels[heldout]
                held_support = support[heldout]
                held_distance = reach.nearest_anchor_distance_km[heldout]
                for mode, attribute in MODES:
                    score = getattr(reach, attribute)[heldout]
                    result = conditional_reachability_concordance(
                        held_labels,
                        held_support,
                        held_distance,
                        score,
                        support_bins=5,
                        distance_bins=5,
                    )
                    value = result.concordance
                    fold_results.append({
                        "species": taxon,
                        "fold": fold,
                        "mode": mode,
                        "evaluable": int(value is not None),
                        "concordance": "" if value is None else value,
                        "comparable_pairs": result.comparable_pairs,
                        "informative_strata": result.informative_strata,
                        "failure": "" if value is not None else "no comparable presence-absence pairs within frozen 5x5 strata",
                    })
                    if value is not None:
                        species_accumulator[taxon][mode].append(float(value))
            except (SupportModelError, ValueError, np.linalg.LinAlgError) as exc:
                for mode, _ in MODES:
                    fold_results.append({
                        "species": taxon,
                        "fold": fold,
                        "mode": mode,
                        "evaluable": 0,
                        "concordance": "",
                        "comparable_pairs": 0,
                        "informative_strata": 0,
                        "failure": str(exc),
                    })

    species_results: list[dict[str, object]] = []
    mode_values: dict[str, list[float]] = {mode: [] for mode, _ in MODES}
    for taxon in taxa:
        for mode, _ in MODES:
            values = species_accumulator[taxon][mode]
            species_value = None if not values else float(np.mean(values))
            species_results.append({
                "species": taxon,
                "mode": mode,
                "estimable_folds": len(values),
                "conditional_concordance": "" if species_value is None else species_value,
            })
            if species_value is not None:
                mode_values[mode].append(species_value)

    summaries: dict[str, object] = {}
    for index, (mode, _) in enumerate(MODES):
        values = np.asarray(mode_values[mode], dtype=float)
        summaries[mode] = _summarize(values, seed=RANDOM_SEED + index)

    combined_mean = summaries["combined"]["mean_conditional_concordance"]
    if combined_mean is None or not np.isclose(combined_mean, EXPECTED_PRIMARY_MEAN, atol=1e-12, rtol=0):
        raise RuntimeError(
            f"primary drift guard failed: expected {EXPECTED_PRIMARY_MEAN}, got {combined_mean}"
        )

    _write_csv(
        fold_output,
        fold_results,
        ["species", "fold", "mode", "evaluable", "concordance", "comparable_pairs", "informative_strata", "failure"],
    )
    _write_csv(
        species_output,
        species_results,
        ["species", "mode", "estimable_folds", "conditional_concordance"],
    )

    summary = {
        "status": "predeclared_aislands_reachability_mode_secondary",
        "n_declared_taxa": 886,
        "n_islands": 842,
        "null": 0.5,
        "primary_drift_guard_expected": EXPECTED_PRIMARY_MEAN,
        "primary_drift_guard_passed": True,
        "modes": summaries,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "sign_flip_replicates": SIGN_FLIP_REPLICATES,
        "input_sha256": hashes,
        "fold_output_sha256": runner._sha256(fold_output),
        "species_output_sha256": runner._sha256(species_output),
        "interpretation_boundary": (
            "Predeclared secondary decomposition of structural reachability. Geography-only and environmentally constrained connected frequencies remain assumption-dependent graph summaries, not dispersal or colonisation probabilities."
        ),
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--folds", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--fold-output", type=Path, required=True)
    parser.add_argument("--species-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    args = parser.parse_args()
    run(**vars(args))


if __name__ == "__main__":
    main()
