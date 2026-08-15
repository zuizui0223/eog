#!/usr/bin/env python3
"""Build an exploratory response-free world-set view of frozen A-Islands scenarios.

This runner reuses the *pre-outcome* A-Islands inputs and the frozen 12 graph scenarios,
but it does not evaluate held-out incidence, fit the frozen pointwise support model, or
compute AUC/concordance.  For each species/fold it uses only outer-training presences as
occurrence anchors and treats every held-out island as an unlabeled candidate state.

The output is exploratory development evidence only.  The A-Islands outcome has already
been viewed in earlier work and cannot become a new confirmatory result for the
integrated EOG world-reconstruction framework.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np

import run_aislands_authoritative_benchmark as authoritative
from aislands_worldset_adapter import summarize_worldset, worldset_from_prepared
from eog.island_reachability import default_aislands_reachability_scenarios
from eog.prepared_island_connectivity import prepare_island_connectivity


PREDICTORS = authoritative.PREDICTORS


def _read_primary_cohort(path: Path) -> list[dict[str, str]]:
    rows = authoritative._read(path)
    if rows and "primary_cohort_included" in rows[0]:
        rows = [row for row in rows if row["primary_cohort_included"].strip() == "1"]
    if len(rows) != 886:
        raise ValueError(f"frozen cohort must resolve to exactly 886 primary rows, got {len(rows)}")
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run(
    island_data: Path,
    species_data: Path,
    cohort: Path,
    folds: Path,
    climate: Path,
    row_output: Path,
    summary_output: Path,
    *,
    min_training_anchors: int = 5,
) -> dict[str, object]:
    if min_training_anchors < 1:
        raise ValueError("min_training_anchors must be positive")

    hashes = {
        "cohort": authoritative._sha256(cohort),
        "folds": authoritative._sha256(folds),
        "climate": authoritative._sha256(climate),
        "island_data": authoritative._sha256(island_data),
        "species_data": authoritative._sha256(species_data),
    }
    if hashes["cohort"] != authoritative.FROZEN_COHORT_SHA256:
        raise ValueError("cohort does not match frozen pre-outcome SHA-256")
    if hashes["folds"] != authoritative.FROZEN_FOLDS_SHA256:
        raise ValueError("spatial folds do not match frozen pre-outcome SHA-256")
    if hashes["climate"] != authoritative.FROZEN_CLIMATE_SHA256:
        raise ValueError("climate table does not match frozen pre-outcome SHA-256")

    islands = authoritative._read(island_data)
    species_rows = authoritative._read(species_data)
    cohort_rows = _read_primary_cohort(cohort)
    fold_rows = authoritative._read(folds)
    climate_rows = authoritative._read(climate)

    island_list = authoritative._col(islands, "List_ID", "list_ID")
    island_id = authoritative._col(islands, "Island_ID", "island_ID")
    species_list = authoritative._col(species_rows, "List_ID", "list_ID")
    species_name = authoritative._col(species_rows, "Species_update", "species_update")
    cohort_name = authoritative._col(cohort_rows, "species")
    fold_id_col = authoritative._col(fold_rows, "island_id")
    fold_col = authoritative._col(fold_rows, "fold")
    x_col = authoritative._col(fold_rows, "x")
    y_col = authoritative._col(fold_rows, "y")
    climate_id = authoritative._col(climate_rows, "island_id")
    climate_cols = [authoritative._col(climate_rows, predictor) for predictor in PREDICTORS]

    list_to_island = {
        authoritative._canonical_id(row[island_list]): authoritative._canonical_id(row[island_id])
        for row in islands
    }
    surveyed = sorted(
        {
            authoritative._canonical_id(
                list_to_island[authoritative._canonical_id(row[species_list])]
            )
            for row in species_rows
        },
        key=int,
    )
    if len(surveyed) != 842:
        raise ValueError(f"expected frozen 842-island universe, got {len(surveyed)}")

    fold_by_island = {
        authoritative._canonical_id(row[fold_id_col]): int(row[fold_col]) for row in fold_rows
    }
    coords = {
        authoritative._canonical_id(row[fold_id_col]): (float(row[y_col]), float(row[x_col]))
        for row in fold_rows
    }
    climate_by_island = {
        authoritative._canonical_id(row[climate_id]): np.asarray(
            [float(row[col]) for col in climate_cols], dtype=float
        )
        for row in climate_rows
    }
    if set(fold_by_island) != set(surveyed) or set(climate_by_island) != set(surveyed):
        raise ValueError("fold/climate island universe differs from frozen 842-island universe")
    if sorted(set(fold_by_island.values())) != [1, 2, 3, 4, 5]:
        raise ValueError("frozen evaluation must contain exactly folds 1..5")

    taxa = sorted({row[cohort_name].strip() for row in cohort_rows if row[cohort_name].strip()})
    if len(taxa) != 886:
        raise ValueError(f"expected 886 frozen taxa, got {len(taxa)}")
    taxon_set = set(taxa)

    # Species rows are used only to identify occurrence anchors that lie in the outer
    # training fold.  Held-out occurrence states are never converted to labels or read
    # into the output/evaluation path below.
    presence_ids: dict[str, set[str]] = {taxon: set() for taxon in taxa}
    for row in species_rows:
        taxon = row[species_name].strip()
        if taxon not in taxon_set:
            continue
        list_id = authoritative._canonical_id(row[species_list])
        if list_id not in list_to_island:
            raise ValueError(f"species List_ID missing from island_data: {list_id}")
        presence_ids[taxon].add(list_to_island[list_id])

    node_ids = tuple(surveyed)
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    x = np.vstack([climate_by_island[node_id] for node_id in node_ids])
    lat = np.asarray([coords[node_id][0] for node_id in node_ids], dtype=float)
    lon = np.asarray([coords[node_id][1] for node_id in node_ids], dtype=float)
    fold_vector = np.asarray([fold_by_island[node_id] for node_id in node_ids], dtype=int)

    scenarios = default_aislands_reachability_scenarios()
    scenario_ids = tuple(scenario.scenario_id for scenario in scenarios)
    if len(scenario_ids) != 12:
        raise RuntimeError(f"frozen A-Islands scenario universe must contain 12 worlds, got {len(scenario_ids)}")

    prepared_by_fold = {}
    for fold in range(1, 6):
        training = fold_vector != fold
        prepared_by_fold[fold] = prepare_island_connectivity(
            node_ids,
            lat,
            lon,
            x,
            training,
            scenarios,
        )

    rows: list[dict[str, object]] = []
    failure_counts: Counter[str] = Counter()
    taxon_fold_evaluable = 0
    for taxon in taxa:
        taxon_presence_ids = presence_ids[taxon]
        for fold in range(1, 6):
            training = fold_vector != fold
            heldout_indices = np.flatnonzero(~training)
            anchor_ids = {
                node_id
                for node_id in taxon_presence_ids
                if fold_by_island[node_id] != fold
            }
            if len(anchor_ids) < min_training_anchors:
                failure_counts["fewer_than_minimum_training_anchors"] += 1
                continue
            anchors = np.zeros(len(node_ids), dtype=bool)
            for anchor_id in anchor_ids:
                anchors[node_index[anchor_id]] = True

            prepared = prepared_by_fold[fold]
            node_rows = worldset_from_prepared(prepared, anchors)
            by_node = {str(row["node_id"]): row for row in node_rows}
            taxon_fold_evaluable += 1

            for heldout_index in heldout_indices:
                island_id_value = node_ids[int(heldout_index)]
                world_row = by_node[island_id_value]
                rows.append(
                    {
                        "species": taxon,
                        "fold": fold,
                        "island_id": island_id_value,
                        "training_presences": len(anchor_ids),
                        "world_count": world_row["world_count"],
                        "support_count": world_row["support_count"],
                        "connected_frequency": world_row["connected_frequency"],
                        "world_class": world_row["world_class"],
                        "geography_support_count": world_row["geography_support_count"],
                        "geography_world_count": world_row["geography_world_count"],
                        "geography_connected_frequency": world_row["geography_connected_frequency"],
                        "geography_world_class": world_row["geography_world_class"],
                        "environment_support_count": world_row["environment_support_count"],
                        "environment_world_count": world_row["environment_world_count"],
                        "environment_connected_frequency": world_row["environment_connected_frequency"],
                        "environment_world_class": world_row["environment_world_class"],
                        "geo_environment_class_disagreement": int(
                            bool(world_row["geo_environment_class_disagreement"])
                        ),
                        "supporting_world_ids": ";".join(world_row["supporting_world_ids"]),
                        "unsupported_world_ids": ";".join(world_row["unsupported_world_ids"]),
                    }
                )

    fields = [
        "species",
        "fold",
        "island_id",
        "training_presences",
        "world_count",
        "support_count",
        "connected_frequency",
        "world_class",
        "geography_support_count",
        "geography_world_count",
        "geography_connected_frequency",
        "geography_world_class",
        "environment_support_count",
        "environment_world_count",
        "environment_connected_frequency",
        "environment_world_class",
        "geo_environment_class_disagreement",
        "supporting_world_ids",
        "unsupported_world_ids",
    ]
    _write_csv(row_output, rows, fields)

    row_summary = summarize_worldset(rows) if rows else None
    class_counts = Counter(str(row["world_class"]) for row in rows)
    support_distribution = Counter(int(row["support_count"]) for row in rows)
    disagreement_count = sum(int(row["geo_environment_class_disagreement"]) for row in rows)
    summary = {
        "status": "exploratory_response_free_aislands_worldset_development",
        "claim_boundary": (
            "Previously viewed A-Islands system; response-free exploratory representation only. "
            "No held-out incidence, AUC, concordance, pointwise support model, or confirmatory "
            "promotion claim is used here."
        ),
        "n_declared_taxa": len(taxa),
        "n_islands": len(node_ids),
        "n_declared_worlds": len(scenario_ids),
        "scenario_ids": list(scenario_ids),
        "n_taxon_folds_evaluable": taxon_fold_evaluable,
        "n_candidate_rows": len(rows),
        "failure_counts": {key: int(value) for key, value in sorted(failure_counts.items())},
        "world_class_counts": {key: int(value) for key, value in sorted(class_counts.items())},
        "support_count_distribution": {
            str(key): int(value) for key, value in sorted(support_distribution.items())
        },
        "geo_environment_class_disagreement_count": int(disagreement_count),
        "adapter_summary": row_summary,
        "input_sha256": hashes,
        "row_output_sha256": authoritative._sha256(row_output),
    }
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    summary_output.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--folds", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--row-output", type=Path, required=True)
    parser.add_argument("--summary-output", type=Path, required=True)
    parser.add_argument("--min-training-anchors", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
