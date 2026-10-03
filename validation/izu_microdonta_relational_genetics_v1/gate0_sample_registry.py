"""Response-free Gate0 validator for the 2026 Izu Campanula registry.

This module must run before any MIG-seq2/SNP/genetic-response processing.
It validates only field/sample identity, island/site structure, coordinates and
leaf-sample availability, then freezes the five-island primary pair universe.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable


REQUIRED_COLUMNS = (
    "sample_id",
    "island",
    "site_id",
    "latitude",
    "longitude",
    "leaf_available",
)
OPTIONAL_COLUMNS = (
    "collection_date",
    "field_individual_id",
    "flower_measurement_id",
)
FORBIDDEN_TOKENS = (
    "genotype",
    "allele",
    "snp",
    "fst",
    "heterozygosity",
    "structure",
    "admixture",
    "migration",
)
PRIMARY_ISLANDS = (
    "Izu_Oshima",
    "Toshima",
    "Niijima",
    "Shikinejima",
    "Kozushima",
)
ISLAND_ALIASES = {
    "Izu_Oshima": {
        "izu_oshima",
        "izu oshima",
        "伊豆大島",
        "大島",
        "oshima",
    },
    "Toshima": {"toshima", "利島"},
    "Niijima": {"niijima", "新島"},
    "Shikinejima": {"shikinejima", "式根島"},
    "Kozushima": {"kozushima", "kozu", "神津島"},
}
TRUE_TOKENS = {"1", "true", "yes", "y"}


class IzuRegistryStop(RuntimeError):
    pass


@dataclass(frozen=True)
class CanonicalSample:
    sample_id: str
    island: str
    site_id: str
    latitude: float
    longitude: float
    leaf_available: bool


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _canonical_island(value: object) -> str:
    raw = str(value).strip()
    key = raw.lower()
    for canonical, aliases in ISLAND_ALIASES.items():
        if key in {alias.lower() for alias in aliases}:
            return canonical
    raise IzuRegistryStop(f"unknown island label: {raw!r}")


def _nonempty(value: object, field: str) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        raise IzuRegistryStop(f"{field} is empty")
    return text


def _coordinate(value: object, field: str, minimum: float, maximum: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise IzuRegistryStop(f"{field} is not numeric: {value!r}") from exc
    if not math.isfinite(result) or result < minimum or result > maximum:
        raise IzuRegistryStop(f"{field} outside [{minimum}, {maximum}]")
    return result


def _leaf_true(value: object) -> bool:
    token = str(value).strip().lower()
    if token not in TRUE_TOKENS:
        raise IzuRegistryStop(
            f"leaf_available must be one of {sorted(TRUE_TOKENS)}, got {value!r}"
        )
    return True


def _schema_check(fieldnames: Iterable[str] | None) -> tuple[str, ...]:
    if fieldnames is None:
        raise IzuRegistryStop("registry has no header")
    columns = tuple(str(value).strip() for value in fieldnames)
    if len(set(columns)) != len(columns):
        raise IzuRegistryStop("registry contains duplicate column names")

    missing = set(REQUIRED_COLUMNS).difference(columns)
    if missing:
        raise IzuRegistryStop(f"registry missing required columns: {sorted(missing)}")

    allowed = set(REQUIRED_COLUMNS) | set(OPTIONAL_COLUMNS)
    unexpected = set(columns).difference(allowed)
    if unexpected:
        lowered = {value.lower() for value in unexpected}
        forbidden = sorted(
            value
            for value in unexpected
            if any(token in value.lower() for token in FORBIDDEN_TOKENS)
        )
        if forbidden:
            raise IzuRegistryStop(
                f"genetic-response-derived columns are forbidden: {forbidden}"
            )
        raise IzuRegistryStop(f"registry contains undeclared columns: {sorted(unexpected)}")
    return columns


def validate_registry_rows(
    fieldnames: Iterable[str] | None,
    raw_rows: Iterable[dict[str, object]],
) -> dict[str, object]:
    columns = _schema_check(fieldnames)
    rows = tuple(raw_rows)
    if len(rows) != 125:
        raise IzuRegistryStop(f"registry row count must be 125, got {len(rows)}")

    canonical: list[CanonicalSample] = []
    seen_ids: set[str] = set()
    for raw in rows:
        sample_id = _nonempty(raw.get("sample_id"), "sample_id")
        if sample_id in seen_ids:
            raise IzuRegistryStop(f"duplicate sample_id: {sample_id}")
        seen_ids.add(sample_id)
        canonical.append(
            CanonicalSample(
                sample_id=sample_id,
                island=_canonical_island(raw.get("island")),
                site_id=_nonempty(raw.get("site_id"), "site_id"),
                latitude=_coordinate(raw.get("latitude"), "latitude", -90.0, 90.0),
                longitude=_coordinate(raw.get("longitude"), "longitude", -180.0, 180.0),
                leaf_available=_leaf_true(raw.get("leaf_available")),
            )
        )

    island_counts = {
        island: sum(row.island == island for row in canonical)
        for island in PRIMARY_ISLANDS
    }
    if set(row.island for row in canonical) != set(PRIMARY_ISLANDS):
        raise IzuRegistryStop("registry must contain exactly the five frozen primary islands")
    too_small = {island: n for island, n in island_counts.items() if n < 2}
    if too_small:
        raise IzuRegistryStop(
            f"every primary island needs at least two leaf samples: {too_small}"
        )

    site_counts: dict[str, int] = {}
    site_coordinates: dict[str, tuple[float, float, str]] = {}
    for row in canonical:
        key = f"{row.island}|{row.site_id}"
        site_counts[key] = site_counts.get(key, 0) + 1
        coordinate = (row.latitude, row.longitude, row.island)
        incumbent = site_coordinates.get(key)
        if incumbent is not None and incumbent != coordinate:
            raise IzuRegistryStop(
                f"site coordinate drift inside registry: {key}"
            )
        site_coordinates[key] = coordinate

    centroids = {}
    for island in PRIMARY_ISLANDS:
        island_rows = [row for row in canonical if row.island == island]
        centroids[island] = {
            "latitude": sum(row.latitude for row in island_rows) / len(island_rows),
            "longitude": sum(row.longitude for row in island_rows) / len(island_rows),
        }

    pair_ids = []
    for i, left in enumerate(PRIMARY_ISLANDS):
        for right in PRIMARY_ISLANDS[i + 1 :]:
            pair_ids.append(f"{left}__{right}")

    canonical_rows = [
        {
            "sample_id": row.sample_id,
            "island": row.island,
            "site_id": row.site_id,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "leaf_available": row.leaf_available,
        }
        for row in sorted(canonical, key=lambda row: row.sample_id)
    ]
    registry_fingerprint = canonical_sha256(canonical_rows)

    result: dict[str, object] = {
        "schema": "eog.izu_microdonta_relational_genetics.gate0_sample_registry.v1",
        "status": "response_free_registry_ready",
        "row_count": len(canonical_rows),
        "columns": list(columns),
        "primary_population_level": "island",
        "primary_islands": list(PRIMARY_ISLANDS),
        "primary_pair_count": len(pair_ids),
        "primary_pair_ids": pair_ids,
        "island_sample_counts": island_counts,
        "site_sample_counts": dict(sorted(site_counts.items())),
        "island_centroids": centroids,
        "genetic_response_columns_present": False,
        "genetic_response_opened": False,
        "registry_fingerprint": registry_fingerprint,
    }
    result["certificate_fingerprint"] = canonical_sha256(result)
    return result


def validate_registry_csv(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return validate_registry_rows(reader.fieldnames, reader)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = validate_registry_csv(args.registry)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
    if args.output is None:
        print(text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
