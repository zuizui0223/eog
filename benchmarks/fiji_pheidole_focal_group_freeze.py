"""Freeze the Fiji focal EGPA group using response-free sample metadata only.

The archive must be the Stage-1 verified Zenodo/Dryad byte object. This script opens
only ``sequenceMetaData.csv`` and never opens VCF, SNP, FST/WC, clustering or migration
result members.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import statistics
import zipfile


EXPECTED_ARCHIVE_SHA256 = "9a23543ad59d5f4de7e6f26cc91b75dc60f93c259744e640b8f6576fde89abc7"
EXPECTED_METADATA_SHA256 = "5a41f967d81e005be3b3e91f31bb1a7eae26a9e7fe3f2a495aef7162932cdfbd"
EXPECTED_BASENAME = "sequencemetadata.csv"
MIN_POPULATIONS = 6
MISSING_COORD_TOKENS = {"", "na", "nan", "n/a", "null", "none", "."}


@dataclass(frozen=True)
class MetadataRow:
    species: str
    egpa: str
    population: str
    latitude: float | None
    longitude: float | None

    @property
    def has_finite_coordinate(self) -> bool:
        return self.latitude is not None and self.longitude is not None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _parse_coordinate(value: object, *, row_index: int, field: str) -> float | None:
    text = str(value or "").strip()
    if text.lower() in MISSING_COORD_TOKENS:
        return None
    try:
        parsed = float(text)
    except ValueError as exc:
        raise ValueError(f"unrecognized {field} coordinate token at metadata row {row_index}: {text!r}") from exc
    if not math.isfinite(parsed):
        return None
    bound = 90.0 if field == "latitude" else 180.0
    if not (-bound <= parsed <= bound):
        raise ValueError(f"out-of-range {field} at metadata row {row_index}")
    return parsed


def _load_metadata(archive: Path) -> tuple[list[MetadataRow], str, str]:
    archive_sha = _sha256(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Fiji archive SHA-256 differs from the Stage-1 verified byte object")

    with zipfile.ZipFile(archive, "r") as handle:
        matches = [
            info for info in handle.infolist()
            if not info.is_dir() and PurePosixPath(info.filename).name.lower() == EXPECTED_BASENAME
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one sequenceMetaData.csv member, found {len(matches)}")
        # Hard response firewall: this is the only member content opened by this script.
        data = handle.read(matches[0])

    metadata_sha = hashlib.sha256(data).hexdigest()
    if metadata_sha != EXPECTED_METADATA_SHA256:
        raise ValueError("sequenceMetaData.csv SHA-256 differs from Stage-1 evidence")
    text = data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    expected = {"species", "seq", "egpa", "pop", "casent", "lat", "long"}
    if set(reader.fieldnames or ()) != expected:
        raise ValueError(f"unexpected sequence metadata schema: {reader.fieldnames}")

    rows: list[MetadataRow] = []
    for index, raw in enumerate(reader, start=2):
        species = str(raw.get("species") or "").strip()
        egpa = str(raw.get("egpa") or "").strip()
        population = str(raw.get("pop") or "").strip()
        if not species or not egpa or not population:
            raise ValueError(f"missing species/egpa/pop at metadata row {index}")
        latitude = _parse_coordinate(raw.get("lat"), row_index=index, field="latitude")
        longitude = _parse_coordinate(raw.get("long"), row_index=index, field="longitude")
        if (latitude is None) != (longitude is None):
            raise ValueError(f"only one coordinate is missing at metadata row {index}")
        rows.append(MetadataRow(species, egpa, population, latitude, longitude))
    if not rows:
        raise ValueError("sequence metadata contains no rows")
    return rows, archive_sha, metadata_sha


def freeze_focal_group(archive: Path) -> dict[str, object]:
    rows, archive_sha, metadata_sha = _load_metadata(archive)
    groups: dict[str, list[MetadataRow]] = {}
    for row in rows:
        groups.setdefault(row.egpa, []).append(row)

    candidates: list[dict[str, object]] = []
    centroids_by_group: dict[str, list[dict[str, object]]] = {}
    for egpa in sorted(groups):
        group_rows = groups[egpa]
        species_labels = sorted({row.species for row in group_rows})
        populations: dict[str, list[MetadataRow]] = {}
        for row in group_rows:
            populations.setdefault(row.population, []).append(row)

        population_rows: list[dict[str, object]] = []
        populations_without_coordinates: list[str] = []
        for population in sorted(populations):
            values = populations[population]
            finite = [row for row in values if row.has_finite_coordinate]
            if not finite:
                populations_without_coordinates.append(population)
                continue
            latitudes = [float(row.latitude) for row in finite if row.latitude is not None]
            longitudes = [float(row.longitude) for row in finite if row.longitude is not None]
            population_rows.append(
                {
                    "population_id": population,
                    "n_individuals": len(values),
                    "n_individuals_with_coordinates": len(finite),
                    "n_individuals_missing_coordinates": len(values) - len(finite),
                    "latitude": float(sum(latitudes) / len(latitudes)),
                    "longitude": float(sum(longitudes) / len(longitudes)),
                    "n_unique_sample_coordinates": len({
                        (round(float(row.latitude), 8), round(float(row.longitude), 8))
                        for row in finite
                        if row.latitude is not None and row.longitude is not None
                    }),
                }
            )

        counts_all = [len(values) for values in populations.values()]
        n_rows_with_coordinates = sum(row.has_finite_coordinate for row in group_rows)
        all_populations_have_coordinates = not populations_without_coordinates
        eligible = (
            len(populations) >= MIN_POPULATIONS
            and len(species_labels) == 1
            and all_populations_have_coordinates
        )
        candidates.append(
            {
                "egpa": egpa,
                "species_labels": species_labels,
                "n_individuals": len(group_rows),
                "n_individuals_with_coordinates": int(n_rows_with_coordinates),
                "n_individuals_missing_coordinates": int(len(group_rows) - n_rows_with_coordinates),
                "coordinate_completeness": float(n_rows_with_coordinates / len(group_rows)),
                "n_populations": len(populations),
                "n_populations_with_coordinates": len(population_rows),
                "populations_without_coordinates": populations_without_coordinates,
                "min_individuals_per_population": int(min(counts_all)),
                "median_individuals_per_population": float(statistics.median(counts_all)),
                "max_individuals_per_population": int(max(counts_all)),
                "all_populations_have_finite_centroid": all_populations_have_coordinates,
                "single_species_label": len(species_labels) == 1,
                "eligible": eligible,
            }
        )
        centroids_by_group[egpa] = population_rows

    eligible_candidates = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible_candidates:
        selected = None
        selected_populations: list[dict[str, object]] = []
        status = "no-response-free-group-meets-minimum-population-rule"
    else:
        # Frozen rule: most populations, then most individuals, then lexicographic EGPA.
        selected = sorted(
            eligible_candidates,
            key=lambda value: (
                -int(value["n_populations"]),
                -int(value["n_individuals"]),
                str(value["egpa"]),
            ),
        )[0]
        selected_populations = centroids_by_group[str(selected["egpa"])]
        status = "response-free-focal-group-selected"

    result: dict[str, object] = {
        "status": status,
        "archive_sha256": archive_sha,
        "sequence_metadata_sha256": metadata_sha,
        "n_metadata_rows": len(rows),
        "n_metadata_rows_missing_coordinates": int(sum(not row.has_finite_coordinate for row in rows)),
        "n_egpa_groups": len(candidates),
        "minimum_populations": MIN_POPULATIONS,
        "coordinate_missing_policy": (
            "recognized NA/blank coordinate pairs are retained as missing sample metadata; "
            "an EGPA group is eligible only if every declared population has at least one finite "
            "coordinate pair so a finite population centroid can be frozen"
        ),
        "selection_rule": (
            "eligible iff >=6 distinct population codes, exactly one species label, and every "
            "population has a finite coordinate centroid; select highest n_populations, then "
            "highest n_individuals, then lexicographic EGPA"
        ),
        "candidates": candidates,
        "selected_group": selected,
        "selected_population_centroids": selected_populations,
        "genetic_member_contents_accessed": False,
        "allowed_member_contents_accessed": ["dryad/VCFs/sequenceMetaData.csv"],
        "claim_boundary": (
            "Selection uses only released sample identity and coordinates. No VCF, SNP, FST/WC, "
            "clustering or migration-result member content was opened."
        ),
    }
    result["fingerprint"] = _canonical_sha256(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = freeze_focal_group(args.archive)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
