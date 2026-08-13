"""Freeze the Fiji focal EGPA group using response-free sample metadata only.

The archive must be the Stage-1 verified Zenodo/Dryad byte object.  This script opens
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


@dataclass(frozen=True)
class MetadataRow:
    species: str
    egpa: str
    population: str
    latitude: float
    longitude: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _load_metadata(archive: Path) -> tuple[list[MetadataRow], str, str]:
    archive_sha = _sha256(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Fiji archive SHA-256 differs from the Stage-1 verified byte object")

    member_info = None
    with zipfile.ZipFile(archive, "r") as handle:
        matches = [
            info for info in handle.infolist()
            if not info.is_dir() and PurePosixPath(info.filename).name.lower() == EXPECTED_BASENAME
        ]
        if len(matches) != 1:
            raise ValueError(f"expected one sequenceMetaData.csv member, found {len(matches)}")
        member_info = matches[0]
        # This is the only member content opened by this script.
        data = handle.read(member_info)

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
        try:
            latitude = float(str(raw.get("lat") or "").strip())
            longitude = float(str(raw.get("long") or "").strip())
        except ValueError as exc:
            raise ValueError(f"non-numeric coordinates at metadata row {index}") from exc
        if not math.isfinite(latitude) or not math.isfinite(longitude):
            raise ValueError(f"non-finite coordinates at metadata row {index}")
        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            raise ValueError(f"out-of-range coordinates at metadata row {index}")
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
        for population in sorted(populations):
            values = populations[population]
            population_rows.append(
                {
                    "population_id": population,
                    "n_individuals": len(values),
                    "latitude": float(sum(row.latitude for row in values) / len(values)),
                    "longitude": float(sum(row.longitude for row in values) / len(values)),
                    "n_unique_sample_coordinates": len({
                        (round(row.latitude, 8), round(row.longitude, 8)) for row in values
                    }),
                }
            )
        counts = [row["n_individuals"] for row in population_rows]
        eligible = len(population_rows) >= MIN_POPULATIONS and len(species_labels) == 1
        candidates.append(
            {
                "egpa": egpa,
                "species_labels": species_labels,
                "n_individuals": len(group_rows),
                "n_populations": len(population_rows),
                "min_individuals_per_population": int(min(counts)),
                "median_individuals_per_population": float(statistics.median(counts)),
                "max_individuals_per_population": int(max(counts)),
                "all_rows_have_finite_coordinates": True,
                "single_species_label": len(species_labels) == 1,
                "eligible": eligible,
            }
        )
        centroids_by_group[egpa] = population_rows

    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    if not eligible:
        selected = None
        selected_populations: list[dict[str, object]] = []
        status = "no-response-free-group-meets-minimum-population-rule"
    else:
        # Frozen rule: most populations, then most individuals, then lexicographic EGPA.
        selected = sorted(
            eligible,
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
        "n_egpa_groups": len(candidates),
        "minimum_populations": MIN_POPULATIONS,
        "selection_rule": (
            "eligible iff >=6 distinct population codes and exactly one species label; "
            "select highest n_populations, then highest n_individuals, then lexicographic EGPA"
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
