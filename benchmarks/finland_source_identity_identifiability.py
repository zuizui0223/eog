"""Audit whether SW Finland historical source identities are uniquely recoverable.

This is strictly response-free. It never reads ``outcome``. The released
``Historical_total_log`` values are decoded back to their integer historical-island counts
using their exact shared affine ``ln(count+1)`` grid. For species where the raw potential-
target complement contains more islands than the released count, a candidate source is
considered individually removable only if deleting it leaves the nearest-source distance
for every released potential target unchanged.

A species is called uniquely recoverable only under the conservative sufficient rule:

* decoded historical count equals complement count; or
* the number of individually removable complement islands equals exactly the number that
  must be removed to match the decoded count.

If more individually removable islands exist than required, source identity is ambiguous
and the species is not admitted. No colonization outcome is used to break ties.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

if __package__ in {None, ""}:
    root = str(Path(__file__).resolve().parents[1])
    if root not in sys.path:
        sys.path.insert(0, root)

from benchmarks.finland_csv_format_adapter import detect_csv_format, fixed_dict_reader_delimiter
from benchmarks.finland_colonization_preoutcome_admission import _load_response_free_projection


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def _fit_affine_log1p(counts: np.ndarray, released: np.ndarray) -> tuple[float, float]:
    z = np.log1p(np.asarray(counts, dtype=float))
    y = np.asarray(released, dtype=float)
    design = np.column_stack([np.ones(len(z)), z])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    if not np.isfinite(beta).all() or float(beta[1]) <= 0.0:
        raise ValueError("invalid historical-count standardization fit")
    return float(beta[0]), float(beta[1])


def decode_integer_historical_counts(
    candidate_counts: np.ndarray,
    released_scaled: np.ndarray,
    *,
    max_count: int,
    max_iterations: int = 50,
) -> tuple[np.ndarray, dict[str, object]]:
    """Decode the exact integer grid without using any outcome information."""
    x = np.asarray(candidate_counts, dtype=float)
    y = np.asarray(released_scaled, dtype=float)
    if x.shape != y.shape or x.ndim != 1 or len(x) < 3:
        raise ValueError("historical count decoding requires aligned vectors")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("historical count decoding requires finite values")

    intercept, slope = _fit_affine_log1p(x, y)
    previous: np.ndarray | None = None
    for iteration in range(1, max_iterations + 1):
        continuous = np.exp((y - intercept) / slope) - 1.0
        decoded = np.rint(continuous).astype(int)
        if np.any(decoded < 0) or np.any(decoded > max_count):
            raise ValueError("decoded historical count outside island universe")
        intercept, slope = _fit_affine_log1p(decoded.astype(float), y)
        if previous is not None and np.array_equal(decoded, previous):
            break
        previous = decoded.copy()
    else:
        raise RuntimeError("historical integer-grid decoding did not converge")

    continuous = np.exp((y - intercept) / slope) - 1.0
    decoded = np.rint(continuous).astype(int)
    integer_error = np.abs(continuous - decoded)
    fitted = intercept + slope * np.log1p(decoded.astype(float))
    residual = y - fitted
    if float(np.max(integer_error)) > 1e-7 or float(np.max(np.abs(residual))) > 1e-10:
        raise RuntimeError("released Historical_total_log is not an exact affine log1p integer grid")

    return decoded, {
        "transform": "affine_lnp1_integer_grid",
        "intercept": intercept,
        "slope": slope,
        "iterations": iteration,
        "max_integer_decode_error": float(np.max(integer_error)),
        "max_released_residual": float(np.max(np.abs(residual))),
    }


def _individually_removable_sources(
    candidate_indices: np.ndarray,
    target_indices: np.ndarray,
    coordinates: np.ndarray,
) -> tuple[int, ...]:
    if len(candidate_indices) == 0:
        return ()
    if len(target_indices) == 0:
        return tuple(int(value) for value in candidate_indices)
    target_xy = coordinates[target_indices]
    source_xy = coordinates[candidate_indices]
    distance2 = np.sum(np.square(target_xy[:, None, :] - source_xy[None, :, :]), axis=2)
    nearest = np.min(distance2, axis=1)
    # EUREF coordinates are metre-scale. Equality is used only to identify a source whose
    # removal can alter an already-released nearest-distance summary; scale-aware tolerance
    # protects arithmetic identity without merging genuinely different distances.
    tolerance = np.maximum(1e-12, 1e-12 * np.maximum(1.0, nearest))
    nearest_mask = np.abs(distance2 - nearest[:, None]) <= tolerance[:, None]
    nearest_multiplicity = np.sum(nearest_mask, axis=1)
    uniquely_needed = set()
    for target_row in np.where(nearest_multiplicity == 1)[0]:
        source_position = int(np.flatnonzero(nearest_mask[target_row])[0])
        uniquely_needed.add(source_position)
    return tuple(
        int(candidate_indices[position])
        for position in range(len(candidate_indices))
        if position not in uniquely_needed
    )


def audit(path: str | Path) -> dict[str, object]:
    source = Path(path)
    fmt = detect_csv_format(source)
    with fixed_dict_reader_delimiter(str(fmt["delimiter"])):
        projection = _load_response_free_projection(source)

    island_ids: tuple[str, ...] = projection["island_ids"]
    species_ids: tuple[str, ...] = projection["species_ids"]
    coordinates: np.ndarray = projection["coordinates"]
    island_index = {island: index for index, island in enumerate(island_ids)}
    universe = set(island_ids)

    species_for_count = []
    candidate_counts = []
    released_values = []
    for species in species_ids:
        values = projection["species_history_values"].get(species, [])
        if not values:
            continue
        unique = sorted({float(value) for value in values})
        if len(unique) != 1:
            raise ValueError(f"Historical_total_log varies within species {species}")
        candidate = universe - projection["species_targets"][species]
        species_for_count.append(species)
        candidate_counts.append(len(candidate))
        released_values.append(unique[0])

    decoded_counts, grid = decode_integer_historical_counts(
        np.asarray(candidate_counts, dtype=float),
        np.asarray(released_values, dtype=float),
        max_count=len(island_ids),
    )

    species_results = []
    recovered_sets: dict[str, tuple[str, ...]] = {}
    status_counts: dict[str, int] = {}
    for species, candidate_count, true_count in zip(
        species_for_count, candidate_counts, decoded_counts.tolist(), strict=True
    ):
        candidate_ids = tuple(sorted(universe - projection["species_targets"][species]))
        extras = int(candidate_count - true_count)
        if extras < 0:
            status = "inconsistent_true_count_exceeds_complement"
            removable_ids: tuple[str, ...] = ()
            recovered: tuple[str, ...] | None = None
        elif extras == 0:
            status = "exact_complement"
            removable_ids = ()
            recovered = candidate_ids
        elif true_count == 0:
            status = "unique_recovered_zero_source" if extras == len(candidate_ids) else "ambiguous"
            removable_ids = candidate_ids
            recovered = () if status.startswith("unique_recovered") else None
        else:
            candidate_indices = np.asarray([island_index[value] for value in candidate_ids], dtype=int)
            target_ids = tuple(sorted(projection["species_targets"][species]))
            target_indices = np.asarray([island_index[value] for value in target_ids], dtype=int)
            removable_indices = _individually_removable_sources(candidate_indices, target_indices, coordinates)
            removable_ids = tuple(island_ids[index] for index in removable_indices)
            if len(removable_ids) < extras:
                status = "inconsistent_nearest_distance_constraints"
                recovered = None
            elif len(removable_ids) == extras:
                status = "unique_recovered_by_count_and_nearest"
                removal_set = set(removable_ids)
                recovered = tuple(value for value in candidate_ids if value not in removal_set)
            else:
                status = "ambiguous_multiple_removable_sources"
                recovered = None

        if recovered is not None:
            if len(recovered) != true_count:
                raise RuntimeError("recovered historical source count drift")
            recovered_sets[species] = recovered
        status_counts[status] = status_counts.get(status, 0) + 1
        species_results.append(
            {
                "species": species,
                "candidate_complement_count": int(candidate_count),
                "decoded_historical_count": int(true_count),
                "extra_complement_islands": extras,
                "n_individually_removable": len(removable_ids),
                "status": status,
                "removable_island_ids": list(removable_ids) if len(removable_ids) <= 20 else None,
                "recovered_source_ids": list(recovered) if recovered is not None else None,
            }
        )

    uniquely_recoverable = len(recovered_sets)
    payload = {
        "status": "finland-response-free-source-identity-identifiability",
        "outcome_values_accessed": False,
        "raw_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "n_islands": len(island_ids),
        "n_species_total": len(species_ids),
        "n_species_with_released_historical_count": len(species_for_count),
        "historical_count_grid": grid,
        "source_identity_status_counts": dict(sorted(status_counts.items())),
        "n_uniquely_recoverable_species": uniquely_recoverable,
        "minimum_species_gate": 100,
        "minimum_species_gate_passed": uniquely_recoverable >= 100,
        "species_results": species_results,
        "recovered_source_fingerprint": _canonical_sha256(
            {species: list(recovered_sets[species]) for species in sorted(recovered_sets)}
        ),
        "claim_boundary": (
            "Response-free identifiability diagnostic only. Source identities are recovered only when "
            "count plus released nearest-distance constraints give a conservative unique solution; "
            "ambiguous species remain excluded and no outcome value is accessed."
        ),
    }
    payload["fingerprint"] = _canonical_sha256(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "outcome_values_accessed": False,
        "n_uniquely_recoverable_species": result["n_uniquely_recoverable_species"],
        "minimum_species_gate_passed": result["minimum_species_gate_passed"],
        "source_identity_status_counts": result["source_identity_status_counts"],
        "fingerprint": result["fingerprint"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
