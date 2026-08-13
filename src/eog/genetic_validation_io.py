"""Auditable CSV intake for prospective EOG v2 genetic validation.

The predictor bundle and the independent genetic response are loaded and fingerprinted
separately. This makes it possible to freeze the EOG/IBD/IBE predictor state before
attaching FST or another symmetric genetic-distance response.

Only Python's standard-library CSV parser and NumPy are used so the intake layer remains
available in the core package.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .genetic_validation import (
    GeneticValidationConfig,
    GeneticValidationResult,
    evaluate_genetic_validation_ladder,
)


@dataclass(frozen=True)
class GeneticPopulationRecord:
    population_id: str
    latitude: float | None = None
    longitude: float | None = None
    island_id: str | None = None


@dataclass(frozen=True)
class GeneticPredictorBundle:
    node_ids: tuple[str, ...]
    geographic_distance: np.ndarray
    environmental_distance: np.ndarray
    eog_continuous_distance: np.ndarray
    eog_disconnected: np.ndarray
    strong_reference_distance: np.ndarray | None
    fingerprint: str


@dataclass(frozen=True)
class GeneticResponseBundle:
    node_ids: tuple[str, ...]
    genetic_distance: np.ndarray
    n_observed_pairs: int
    fingerprint: str


@dataclass(frozen=True)
class GeneticValidationCsvBundle:
    populations: tuple[GeneticPopulationRecord, ...]
    predictors: GeneticPredictorBundle
    response: GeneticResponseBundle
    validation: GeneticValidationResult
    fingerprint: str


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clean_id(value: object, label: str) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _parse_optional_float(value: str | None, label: str) -> float | None:
    if value is None or not str(value).strip():
        return None
    parsed = float(value)
    if not np.isfinite(parsed):
        raise ValueError(f"{label} must be finite when supplied")
    return parsed


def _read_csv(path: str | Path) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    source = Path(path)
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {source}")
        fieldnames = tuple(str(name).strip() for name in reader.fieldnames)
        rows = [
            {str(key).strip(): "" if value is None else str(value).strip() for key, value in row.items()}
            for row in reader
        ]
    return fieldnames, rows


def load_population_csv(path: str | Path) -> tuple[GeneticPopulationRecord, ...]:
    """Load ordered population metadata.

    Required column: ``population_id``. Optional columns: ``latitude``, ``longitude``,
    ``island_id``. Coordinates must be supplied together when present.
    """

    fields, rows = _read_csv(path)
    if "population_id" not in fields:
        raise ValueError("population CSV must contain population_id")
    if len(rows) < 5:
        raise ValueError("at least five population rows are required")
    result: list[GeneticPopulationRecord] = []
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        population_id = _clean_id(row.get("population_id"), f"population_id row {row_number}")
        if population_id in seen:
            raise ValueError(f"duplicate population_id: {population_id}")
        seen.add(population_id)
        latitude = _parse_optional_float(row.get("latitude"), f"latitude row {row_number}")
        longitude = _parse_optional_float(row.get("longitude"), f"longitude row {row_number}")
        if (latitude is None) != (longitude is None):
            raise ValueError("latitude and longitude must be supplied together")
        if latitude is not None and not (-90.0 <= latitude <= 90.0):
            raise ValueError(f"latitude outside [-90, 90] for {population_id}")
        if longitude is not None and not (-180.0 <= longitude <= 180.0):
            raise ValueError(f"longitude outside [-180, 180] for {population_id}")
        island_id = row.get("island_id", "").strip() or None
        result.append(
            GeneticPopulationRecord(
                population_id=population_id,
                latitude=latitude,
                longitude=longitude,
                island_id=island_id,
            )
        )
    return tuple(result)


def _pair_key(a: str, b: str, lookup: dict[str, int]) -> tuple[int, int]:
    if a not in lookup or b not in lookup:
        unknown = a if a not in lookup else b
        raise ValueError(f"pair table contains unknown population_id: {unknown}")
    i, j = lookup[a], lookup[b]
    if i == j:
        raise ValueError(f"self pair is not allowed: {a}")
    return (i, j) if i < j else (j, i)


def _require_pair_columns(fields: Sequence[str], required: Iterable[str], label: str) -> None:
    missing = [name for name in required if name not in fields]
    if missing:
        raise ValueError(f"{label} missing required columns: {', '.join(missing)}")


def _parse_nonnegative(value: str, label: str) -> float:
    parsed = float(value)
    if not np.isfinite(parsed) or parsed < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return parsed


def _matrix_from_complete_pairs(
    node_ids: tuple[str, ...],
    values: dict[tuple[int, int], float],
    label: str,
) -> np.ndarray:
    n = len(node_ids)
    expected = n * (n - 1) // 2
    if len(values) != expected:
        missing = expected - len(values)
        raise ValueError(f"{label} must contain every unordered population pair; missing {missing}")
    matrix = np.zeros((n, n), dtype=float)
    for (i, j), value in values.items():
        matrix[i, j] = matrix[j, i] = float(value)
    return matrix


def load_predictor_pair_csv(
    path: str | Path,
    populations: Sequence[GeneticPopulationRecord],
) -> GeneticPredictorBundle:
    """Load a complete predictor pair table independent of genetic outcomes.

    Required columns:

    - ``population_a``
    - ``population_b``
    - ``geographic_distance``
    - ``environmental_distance``
    - ``eog_continuous_distance``
    - ``eog_disconnected`` (0/1, false/true, no/yes)

    Optional ``strong_reference_distance`` must be present for every row or none.
    """

    node_ids = tuple(record.population_id for record in populations)
    lookup = {population_id: index for index, population_id in enumerate(node_ids)}
    fields, rows = _read_csv(path)
    required = (
        "population_a",
        "population_b",
        "geographic_distance",
        "environmental_distance",
        "eog_continuous_distance",
        "eog_disconnected",
    )
    _require_pair_columns(fields, required, "predictor pair CSV")
    has_strong = "strong_reference_distance" in fields
    geo: dict[tuple[int, int], float] = {}
    env: dict[tuple[int, int], float] = {}
    eog: dict[tuple[int, int], float] = {}
    disconnected_values: dict[tuple[int, int], bool] = {}
    strong: dict[tuple[int, int], float] = {}
    true_values = {"1", "true", "t", "yes", "y"}
    false_values = {"0", "false", "f", "no", "n"}

    for row_number, row in enumerate(rows, start=2):
        a = _clean_id(row.get("population_a"), f"population_a row {row_number}")
        b = _clean_id(row.get("population_b"), f"population_b row {row_number}")
        key = _pair_key(a, b, lookup)
        if key in geo:
            raise ValueError(f"duplicate unordered predictor pair: {a}, {b}")
        geo[key] = _parse_nonnegative(row["geographic_distance"], f"geographic_distance row {row_number}")
        env[key] = _parse_nonnegative(row["environmental_distance"], f"environmental_distance row {row_number}")
        eog[key] = _parse_nonnegative(row["eog_continuous_distance"], f"eog_continuous_distance row {row_number}")
        token = row["eog_disconnected"].strip().lower()
        if token in true_values:
            disconnected_values[key] = True
        elif token in false_values:
            disconnected_values[key] = False
        else:
            raise ValueError(f"eog_disconnected row {row_number} must be boolean/0/1")
        if has_strong:
            if not row["strong_reference_distance"].strip():
                raise ValueError("strong_reference_distance must be complete when column is present")
            strong[key] = _parse_nonnegative(
                row["strong_reference_distance"],
                f"strong_reference_distance row {row_number}",
            )

    d_geo = _matrix_from_complete_pairs(node_ids, geo, "geographic_distance")
    d_env = _matrix_from_complete_pairs(node_ids, env, "environmental_distance")
    d_eog = _matrix_from_complete_pairs(node_ids, eog, "eog_continuous_distance")
    n = len(node_ids)
    expected = n * (n - 1) // 2
    if len(disconnected_values) != expected:
        raise ValueError("eog_disconnected must contain every unordered population pair")
    disconnected = np.zeros((n, n), dtype=bool)
    for (i, j), value in disconnected_values.items():
        disconnected[i, j] = disconnected[j, i] = bool(value)
    d_strong = None
    if has_strong:
        d_strong = _matrix_from_complete_pairs(node_ids, strong, "strong_reference_distance")

    payload = {
        "node_ids": list(node_ids),
        "geographic_distance": d_geo.tolist(),
        "environmental_distance": d_env.tolist(),
        "eog_continuous_distance": d_eog.tolist(),
        "eog_disconnected": disconnected.astype(int).tolist(),
        "strong_reference_distance": None if d_strong is None else d_strong.tolist(),
    }
    return GeneticPredictorBundle(
        node_ids=node_ids,
        geographic_distance=d_geo,
        environmental_distance=d_env,
        eog_continuous_distance=d_eog,
        eog_disconnected=disconnected,
        strong_reference_distance=d_strong,
        fingerprint=_canonical_sha256(payload),
    )


def load_genetic_response_pair_csv(
    path: str | Path,
    populations: Sequence[GeneticPopulationRecord],
) -> GeneticResponseBundle:
    """Load an independent long-form symmetric genetic response.

    Required columns: ``population_a``, ``population_b``, ``genetic_distance``.
    The response may omit population pairs; omitted pairs remain missing and are never
    imputed. Duplicate unordered pairs and self pairs are rejected.
    """

    node_ids = tuple(record.population_id for record in populations)
    lookup = {population_id: index for index, population_id in enumerate(node_ids)}
    fields, rows = _read_csv(path)
    _require_pair_columns(
        fields,
        ("population_a", "population_b", "genetic_distance"),
        "genetic response CSV",
    )
    n = len(node_ids)
    matrix = np.full((n, n), np.nan, dtype=float)
    np.fill_diagonal(matrix, 0.0)
    seen: set[tuple[int, int]] = set()
    canonical_rows: list[dict[str, object]] = []
    for row_number, row in enumerate(rows, start=2):
        a = _clean_id(row.get("population_a"), f"population_a row {row_number}")
        b = _clean_id(row.get("population_b"), f"population_b row {row_number}")
        key = _pair_key(a, b, lookup)
        if key in seen:
            raise ValueError(f"duplicate unordered genetic pair: {a}, {b}")
        seen.add(key)
        value = _parse_nonnegative(row["genetic_distance"], f"genetic_distance row {row_number}")
        i, j = key
        matrix[i, j] = matrix[j, i] = value
        canonical_rows.append(
            {
                "population_a": node_ids[i],
                "population_b": node_ids[j],
                "genetic_distance": value,
            }
        )
    if len(seen) < n:
        raise ValueError("too few observed genetic pairs for population-wise validation")
    canonical_rows.sort(key=lambda row: (row["population_a"], row["population_b"]))
    return GeneticResponseBundle(
        node_ids=node_ids,
        genetic_distance=matrix,
        n_observed_pairs=len(seen),
        fingerprint=_canonical_sha256(
            {"node_ids": list(node_ids), "observed_pairs": canonical_rows}
        ),
    )


def run_genetic_validation_from_csv(
    population_csv: str | Path,
    predictor_pair_csv: str | Path,
    genetic_response_csv: str | Path,
    *,
    config: GeneticValidationConfig = GeneticValidationConfig(),
) -> GeneticValidationCsvBundle:
    """Load separately fingerprinted inputs and run the LOPO validation ladder."""

    populations = load_population_csv(population_csv)
    predictors = load_predictor_pair_csv(predictor_pair_csv, populations)
    response = load_genetic_response_pair_csv(genetic_response_csv, populations)
    if predictors.node_ids != response.node_ids:
        raise RuntimeError("predictor and response node orders do not match")
    validation = evaluate_genetic_validation_ladder(
        predictors.node_ids,
        response.genetic_distance,
        predictors.geographic_distance,
        predictors.environmental_distance,
        predictors.eog_continuous_distance,
        predictors.eog_disconnected,
        strong_reference_distance=predictors.strong_reference_distance,
        config=config,
    )
    payload = {
        "population_ids": list(predictors.node_ids),
        "predictor_fingerprint": predictors.fingerprint,
        "response_fingerprint": response.fingerprint,
        "validation_fingerprint": validation.fingerprint,
    }
    return GeneticValidationCsvBundle(
        populations=populations,
        predictors=predictors,
        response=response,
        validation=validation,
        fingerprint=_canonical_sha256(payload),
    )
