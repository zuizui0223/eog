"""Produce frozen cross-fitted local environmental support for the A-Islands cohort."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from eog.local_support import LogisticSupportDeclaration, cross_fitted_logistic_support

PREDICTORS = ("bio1", "bio5", "bio6", "bio12", "bio15")
FROZEN_CLIMATE_SHA256 = "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _col(rows: list[dict[str, str]], name: str, label: str) -> str:
    if not rows:
        raise ValueError(f"{label} is empty")
    matches = [key for key in rows[0] if key.casefold() == name.casefold()]
    if len(matches) != 1:
        raise ValueError(f"{label} missing or ambiguous column: {name}")
    return matches[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(
    island_data: Path,
    species_data: Path,
    cohort: Path,
    climate: Path,
    output: Path,
    manifest: Path,
) -> dict[str, object]:
    climate_sha = _sha256(climate)
    if climate_sha != FROZEN_CLIMATE_SHA256:
        raise ValueError(
            "climate artifact does not match the pre-outcome frozen CHELSA CSV: "
            f"expected {FROZEN_CLIMATE_SHA256}, got {climate_sha}"
        )

    island_rows = _read(island_data)
    species_rows = _read(species_data)
    cohort_rows = _read(cohort)
    climate_rows = _read(climate)

    island_list_col = _col(island_rows, "List_ID", "island_data")
    island_id_col = _col(island_rows, "Island_ID", "island_data")
    species_list_col = _col(species_rows, "List_ID", "species_data")
    species_name_col = _col(species_rows, "Species_update", "species_data")
    cohort_species_col = _col(cohort_rows, "species", "cohort")
    climate_island_col = _col(climate_rows, "island_id", "climate")
    climate_predictor_cols = [_col(climate_rows, name, "climate") for name in PREDICTORS]

    list_to_island: dict[str, str] = {}
    for row in island_rows:
        list_id = row[island_list_col].strip()
        island_id = row[island_id_col].strip()
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"List_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id

    species_linked_islands = sorted({
        list_to_island[row[species_list_col].strip()]
        for row in species_rows
        if row[species_list_col].strip() in list_to_island
    }, key=lambda value: int(value))
    if len(species_linked_islands) != 842:
        raise ValueError(f"expected frozen 842-island universe, got {len(species_linked_islands)}")

    climate_by_island: dict[str, np.ndarray] = {}
    for row in climate_rows:
        island_id = row[climate_island_col].strip()
        if island_id in climate_by_island:
            raise ValueError(f"duplicate climate row for Island_ID: {island_id}")
        values = np.asarray([float(row[col]) for col in climate_predictor_cols], dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite climate value for Island_ID: {island_id}")
        climate_by_island[island_id] = values
    missing_climate = sorted(set(species_linked_islands) - set(climate_by_island))
    extra_climate = sorted(set(climate_by_island) - set(species_linked_islands))
    if missing_climate:
        raise ValueError(f"missing climate rows for surveyed islands: {missing_climate[:10]}")
    if extra_climate:
        raise ValueError(f"climate table contains islands outside frozen universe: {extra_climate[:10]}")

    cohort_species = sorted({row[cohort_species_col].strip() for row in cohort_rows if row[cohort_species_col].strip()})
    if len(cohort_species) != 886:
        raise ValueError(f"expected frozen 886-taxon cohort, got {len(cohort_species)}")

    presences: dict[str, set[str]] = {species: set() for species in cohort_species}
    cohort_set = set(cohort_species)
    for row in species_rows:
        species = row[species_name_col].strip()
        if species not in cohort_set:
            continue
        list_id = row[species_list_col].strip()
        if list_id not in list_to_island:
            raise ValueError(f"species List_ID missing from island_data: {list_id}")
        presences[species].add(list_to_island[list_id])

    x = np.vstack([climate_by_island[island_id] for island_id in species_linked_islands])
    declaration = LogisticSupportDeclaration(n_splits=10, l2_penalty=1.0, class_weight="balanced")
    output.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    species_fingerprints: dict[str, str] = {}
    with output.open("w", newline="", encoding="utf-8") as handle:
        fields = ["species", "Island_ID", "observed_presence", "fold_id", "local_support"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for species in cohort_species:
            y = np.asarray([int(island_id in presences[species]) for island_id in species_linked_islands], dtype=int)
            if int(np.sum(y)) < 10 or int(np.sum(1 - y)) < 10:
                raise ValueError(f"frozen cohort violates 10/10 incidence rule: {species}")
            fitted = cross_fitted_logistic_support(x, y, species_linked_islands, declaration)
            species_fingerprints[species] = fitted.fingerprint
            for island_id, observed, fold_id, probability in zip(
                species_linked_islands, y, fitted.fold_ids, fitted.probabilities
            ):
                writer.writerow({
                    "species": species,
                    "Island_ID": island_id,
                    "observed_presence": int(observed),
                    "fold_id": int(fold_id),
                    "local_support": f"{probability:.12g}",
                })
                row_count += 1

    result = {
        "n_species": len(cohort_species),
        "n_islands": len(species_linked_islands),
        "n_rows": row_count,
        "predictors": list(PREDICTORS),
        "support_producer": "training-fold-standardized class-balanced L2 logistic regression",
        "optimizer": "deterministic Newton updates",
        "n_splits": declaration.n_splits,
        "l2_penalty": declaration.l2_penalty,
        "class_weight": declaration.class_weight,
        "input_sha256": {
            "island_data": _sha256(island_data),
            "species_data": _sha256(species_data),
            "cohort": _sha256(cohort),
            "climate": climate_sha,
        },
        "frozen_climate_sha256": FROZEN_CLIMATE_SHA256,
        "output_sha256": _sha256(output),
        "species_support_fingerprints_sha256": hashlib.sha256(
            json.dumps(species_fingerprints, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "scientific_boundary": (
            "cross-fitted pointwise climate support only; no distance, island area, coordinates, "
            "EOG topology, bridge cost, or held-out performance comparison used"
        ),
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--climate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
