"""Response-free admission audit for the SW Finland colonization benchmark.

The program deliberately never accesses the released ``outcome`` field. It reconstructs
historical source identities from the complement of potential-target islands and tests
that reconstruction against the released historical-count and nearest-history predictors
before any EOG v2 colonization score may be computed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from eog.dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)

EXPECTED_ISLANDS = 471
MIN_SOURCEFUL_SPECIES = 100
CONSISTENCY_R2 = 0.999999
LOSS_SUPPORT = 0.55
N_SPATIAL_FOLDS = 5

HABITAT_COLUMNS = (
    "Buildings",
    "Meadow_or_pasture",
    "Deciduous_forest",
    "Coniferous_forest",
    "Mixed_forest",
    "Sand",
    "Open_rock_or_bare_ground",
    "Marsh",
    "Shore_meadow",
    "Limestone",
)

REQUIRED_COLUMNS = {
    "outcome",  # existence is checked, values are never read
    "spp.name",
    "holmkod",
    "Euref_X_original",
    "Euref_Y_original",
    "Historical_total_log",
    "Dist_to_historical_log",
    *HABITAT_COLUMNS,
}

MISSING = {"", "na", "nan", "null", "."}


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _finite_or_none(value: str) -> float | None:
    normalized = value.strip().lower()
    if normalized in MISSING:
        return None
    result = float(value)
    if not np.isfinite(result):
        return None
    return result


def _transform_values(values: np.ndarray, transform: str) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    if transform == "raw":
        return x
    if transform == "log10":
        if np.any(x <= 0.0):
            raise ValueError("log10 transform requires positive values")
        return np.log10(x)
    if transform == "log10p1":
        if np.any(x < 0.0):
            raise ValueError("log10p1 transform requires non-negative values")
        return np.log10(x + 1.0)
    if transform == "ln":
        if np.any(x <= 0.0):
            raise ValueError("ln transform requires positive values")
        return np.log(x)
    if transform == "lnp1":
        if np.any(x < 0.0):
            raise ValueError("lnp1 transform requires non-negative values")
        return np.log1p(x)
    raise ValueError(transform)


def _best_affine_transform_r2(
    reconstructed: np.ndarray,
    released: np.ndarray,
) -> dict[str, float | str]:
    x = np.asarray(reconstructed, dtype=float)
    y = np.asarray(released, dtype=float)
    if x.shape != y.shape or x.ndim != 1 or x.size < 3:
        raise ValueError("transform comparison requires aligned one-dimensional samples")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("transform comparison requires finite values")
    candidates = []
    for transform in ("raw", "log10", "log10p1", "ln", "lnp1"):
        try:
            z = _transform_values(x, transform)
        except ValueError:
            continue
        design = np.column_stack([np.ones(len(z)), z])
        beta = np.linalg.lstsq(design, y, rcond=None)[0]
        fitted = design @ beta
        residual = float(np.sum(np.square(y - fitted)))
        total = float(np.sum(np.square(y - np.mean(y))))
        r2 = 1.0 if total <= 1e-30 and residual <= 1e-30 else 1.0 - residual / max(total, 1e-30)
        candidates.append(
            {
                "transform": transform,
                "intercept": float(beta[0]),
                "slope": float(beta[1]),
                "r2": float(r2),
            }
        )
    if not candidates:
        raise RuntimeError("no release transform was estimable")
    return max(candidates, key=lambda row: (row["r2"], -len(str(row["transform"]))))


def _gabriel_edges(coordinates: np.ndarray, *, tolerance: float = 1e-10) -> list[tuple[int, int]]:
    xy = np.asarray(coordinates, dtype=float)
    n = len(xy)
    if xy.shape != (n, 2) or n < 2 or not np.isfinite(xy).all():
        raise ValueError("coordinates must be a finite n-by-2 matrix")
    if len(np.unique(xy, axis=0)) != n:
        raise ValueError("Gabriel graph requires unique island coordinates")
    edges: list[tuple[int, int]] = []
    for i in range(n):
        for j in range(i + 1, n):
            delta = xy[i] - xy[j]
            diameter2 = float(np.dot(delta, delta))
            midpoint = 0.5 * (xy[i] + xy[j])
            radius2 = 0.25 * diameter2
            distance2 = np.sum(np.square(xy - midpoint), axis=1)
            distance2[i] = np.inf
            distance2[j] = np.inf
            scale = max(1.0, radius2)
            if float(np.min(distance2)) >= radius2 - tolerance * scale:
                edges.append((i, j))
    if not edges:
        raise RuntimeError("Gabriel graph has no edges")
    return edges


def _deterministic_spatial_folds(
    island_ids: tuple[str, ...],
    coordinates: np.ndarray,
    *,
    n_folds: int = N_SPATIAL_FOLDS,
) -> np.ndarray:
    xy = np.asarray(coordinates, dtype=float)
    n = len(xy)
    if n < n_folds:
        raise ValueError("fewer islands than spatial folds")
    ordering = sorted(range(n), key=lambda index: (xy[index, 0], xy[index, 1], island_ids[index]))
    selected = [ordering[0]]
    while len(selected) < n_folds:
        distances = np.min(
            np.sum(np.square(xy[:, None, :] - xy[np.asarray(selected)][None, :, :]), axis=2),
            axis=1,
        )
        distances[np.asarray(selected)] = -1.0
        maximum = float(np.max(distances))
        candidates = [index for index in range(n) if abs(float(distances[index]) - maximum) <= 1e-12]
        selected.append(min(candidates, key=lambda index: island_ids[index]))
    centers = xy[np.asarray(selected)].copy()
    labels = np.zeros(n, dtype=int)
    for _ in range(100):
        distance2 = np.sum(np.square(xy[:, None, :] - centers[None, :, :]), axis=2)
        new_labels = np.argmin(distance2, axis=1)
        if np.array_equal(new_labels, labels) and _ > 0:
            break
        labels = new_labels
        for fold in range(n_folds):
            members = xy[labels == fold]
            if len(members):
                centers[fold] = np.mean(members, axis=0)
    if set(labels.tolist()) != set(range(n_folds)):
        raise RuntimeError("deterministic spatial clustering produced an empty fold")
    return labels


def _load_response_free_projection(path: Path) -> dict[str, object]:
    island_coordinates: dict[str, tuple[float, float]] = {}
    island_habitat: dict[str, tuple[float, ...]] = {}
    species_targets: dict[str, set[str]] = defaultdict(set)
    species_history_values: dict[str, list[float]] = defaultdict(list)
    nearest_records: list[tuple[str, str, float | None]] = []
    row_count = 0

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("colonization CSV has no header")
        columns = set(reader.fieldnames)
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"colonization CSV missing required columns: {sorted(missing)}")
        for row in reader:
            row_count += 1
            # Deliberate outcome firewall: row['outcome'] is never accessed here.
            species = row["spp.name"].strip()
            island = row["holmkod"].strip()
            if not species or not island:
                raise ValueError("species and island IDs must be non-empty")
            x = _finite_or_none(row["Euref_X_original"])
            y = _finite_or_none(row["Euref_Y_original"])
            if x is None or y is None:
                raise ValueError("original island coordinates must be finite")
            coordinate = (x, y)
            previous_coordinate = island_coordinates.setdefault(island, coordinate)
            if not np.allclose(previous_coordinate, coordinate, rtol=0.0, atol=1e-9):
                raise ValueError(f"island coordinate is not invariant for {island}")

            habitat_values = []
            for column in HABITAT_COLUMNS:
                value = _finite_or_none(row[column])
                if value is None:
                    raise ValueError(f"graph habitat value {column} is missing for island {island}")
                habitat_values.append(value)
            habitat = tuple(habitat_values)
            previous_habitat = island_habitat.setdefault(island, habitat)
            if not np.allclose(previous_habitat, habitat, rtol=0.0, atol=1e-9):
                raise ValueError(f"island habitat state is not invariant for {island}")

            species_targets[species].add(island)
            historical = _finite_or_none(row["Historical_total_log"])
            if historical is not None:
                species_history_values[species].append(historical)
            nearest_records.append((species, island, _finite_or_none(row["Dist_to_historical_log"])))

    if row_count < 1:
        raise ValueError("colonization CSV has no rows")
    island_ids = tuple(sorted(island_coordinates))
    species_ids = tuple(sorted(species_targets))
    return {
        "row_count": row_count,
        "island_ids": island_ids,
        "coordinates": np.asarray([island_coordinates[value] for value in island_ids], dtype=float),
        "habitat": np.asarray([island_habitat[value] for value in island_ids], dtype=float),
        "species_ids": species_ids,
        "species_targets": species_targets,
        "species_history_values": species_history_values,
        "nearest_records": nearest_records,
    }


def evaluate_admission(path: str | Path) -> dict[str, object]:
    source_path = Path(path)
    raw_sha256 = _file_sha256(source_path)
    projection = _load_response_free_projection(source_path)
    island_ids: tuple[str, ...] = projection["island_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    habitat: np.ndarray = projection["habitat"]
    species_ids: tuple[str, ...] = projection["species_ids"]
    universe = set(island_ids)

    source_sets = {
        species: tuple(sorted(universe - projection["species_targets"][species]))
        for species in species_ids
    }
    sourceful = tuple(species for species in species_ids if source_sets[species])
    zero_source = tuple(species for species in species_ids if not source_sets[species])

    count_x = []
    count_y = []
    for species in sourceful:
        values = projection["species_history_values"].get(species, [])
        if not values:
            continue
        if not np.allclose(values, values[0], rtol=0.0, atol=1e-12):
            raise ValueError(f"Historical_total_log varies within species {species}")
        count_x.append(float(len(source_sets[species])))
        count_y.append(float(values[0]))
    count_fit = _best_affine_transform_r2(np.asarray(count_x), np.asarray(count_y))

    island_index = {island: index for index, island in enumerate(island_ids)}
    distance_x = []
    distance_y = []
    zero_source_nearest_nonmissing = 0
    source_coordinate_cache = {
        species: coordinates[np.asarray([island_index[value] for value in source_sets[species]], dtype=int)]
        for species in sourceful
    }
    for species, island, released in projection["nearest_records"]:
        if species in zero_source:
            if released is not None:
                zero_source_nearest_nonmissing += 1
            continue
        source_coordinates = source_coordinate_cache[species]
        target_coordinate = coordinates[island_index[island]]
        reconstructed = float(np.min(np.linalg.norm(source_coordinates - target_coordinate, axis=1)))
        if released is None:
            continue
        distance_x.append(reconstructed)
        distance_y.append(released)
    distance_fit = _best_affine_transform_r2(np.asarray(distance_x), np.asarray(distance_y))

    gabriel = _gabriel_edges(coordinates)
    geo_lengths = np.asarray(
        [np.linalg.norm(coordinates[i] - coordinates[j]) for i, j in gabriel], dtype=float
    )
    geographic_scale = float(np.median(geo_lengths))
    if not np.isfinite(geographic_scale) or geographic_scale <= 0.0:
        raise RuntimeError("invalid geometry-derived geographic scale")

    mean = np.mean(habitat, axis=0)
    standard_deviation = np.std(habitat, axis=0)
    scale = np.where(standard_deviation > 1e-12, standard_deviation, 1.0)
    standardized_habitat = (habitat - mean) / scale
    env_lengths = np.asarray(
        [np.linalg.norm(standardized_habitat[i] - standardized_habitat[j]) for i, j in gabriel],
        dtype=float,
    )
    positive_env = env_lengths[env_lengths > 1e-12]
    if not len(positive_env):
        raise RuntimeError("no non-zero environmental transition distances")
    environmental_scale = float(np.median(positive_env))

    edges = []
    for (i, j), geo_distance, env_distance in zip(gabriel, geo_lengths, env_lengths):
        geo_support = float(np.exp(-geo_distance / geographic_scale))
        env_support = float(np.exp(-env_distance / environmental_scale))
        edges.append(
            DynamicReachabilityEdge(i, j, geographic_support=geo_support, environmental_support=env_support)
        )
        edges.append(
            DynamicReachabilityEdge(j, i, geographic_support=geo_support, environmental_support=env_support)
        )
    operator = build_dynamic_transition_operator(island_ids, edges, loss_support=LOSS_SUPPORT)

    folds = _deterministic_spatial_folds(island_ids, coordinates)
    fold_payload = {island: int(folds[index]) for index, island in enumerate(island_ids)}
    fold_fingerprint = _canonical_sha256(fold_payload)
    source_payload = {species: list(source_sets[species]) for species in species_ids}
    source_fingerprint = _canonical_sha256(source_payload)
    projection_fingerprint = _canonical_sha256(
        {
            "raw_sha256": raw_sha256,
            "islands": [
                {
                    "id": island,
                    "coordinate": coordinates[index].tolist(),
                    "habitat": habitat[index].tolist(),
                    "fold": int(folds[index]),
                }
                for index, island in enumerate(island_ids)
            ],
            "source_sets": source_payload,
            "gabriel_edges": [[island_ids[i], island_ids[j]] for i, j in gabriel],
            "operator_fingerprint": operator.fingerprint,
        }
    )

    checks = {
        "island_universe": {
            "value": len(island_ids),
            "required": EXPECTED_ISLANDS,
            "passed": len(island_ids) == EXPECTED_ISLANDS,
        },
        "sourceful_species": {
            "value": len(sourceful),
            "required_minimum": MIN_SOURCEFUL_SPECIES,
            "passed": len(sourceful) >= MIN_SOURCEFUL_SPECIES,
        },
        "historical_count_consistency": {
            "value": float(count_fit["r2"]),
            "required_minimum": CONSISTENCY_R2,
            "passed": float(count_fit["r2"]) >= CONSISTENCY_R2,
        },
        "nearest_history_consistency": {
            "value": float(distance_fit["r2"]),
            "required_minimum": CONSISTENCY_R2,
            "passed": float(distance_fit["r2"]) >= CONSISTENCY_R2,
        },
        "zero_source_nearest_missing": {
            "value_nonmissing": int(zero_source_nearest_nonmissing),
            "required": 0,
            "passed": zero_source_nearest_nonmissing == 0,
        },
    }
    admitted = bool(all(check["passed"] for check in checks.values()))
    return {
        "status": "finland-colonization-response-free-admission",
        "outcome_values_accessed": False,
        "raw_file": source_path.name,
        "raw_sha256": raw_sha256,
        "row_count_response_blind": int(projection["row_count"]),
        "n_islands": len(island_ids),
        "n_species": len(species_ids),
        "n_sourceful_species": len(sourceful),
        "n_zero_source_species": len(zero_source),
        "historical_count_release_fit": count_fit,
        "nearest_history_release_fit": distance_fit,
        "gabriel_edge_count": len(gabriel),
        "geographic_scale": geographic_scale,
        "environmental_scale": environmental_scale,
        "operator_fingerprint": operator.fingerprint,
        "source_fingerprint": source_fingerprint,
        "fold_fingerprint": fold_fingerprint,
        "fold_counts": {
            str(fold): int(np.sum(folds == fold)) for fold in range(N_SPATIAL_FOLDS)
        },
        "response_free_projection_fingerprint": projection_fingerprint,
        "checks": checks,
        "admitted": admitted,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = evaluate_admission(args.input)
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    if not result["admitted"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
