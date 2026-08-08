"""Freeze primary native island incidence for the A-Islands benchmark.

The declared taxon set is fixed upstream by APC status. This stage defines island-level
presence labels before any support-model or EOG result is inspected. Explicit local
non-native evidence is removed conservatively:

- `Naturalised == 1` => that source row does not support native incidence;
- `Native == 0` => that source row does not support native incidence;
- missing/NA/non-numeric local status does not erase an APC-native record.

An island is present when at least one retained source row for that APC-native species
exists on any flora list for the island. If all rows for a species-island combination
are explicitly non-native, the primary native incidence is zero. No taxon is silently
replaced or removed because its cleaned presence count becomes small.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path


def _read(path: Path) -> tuple[list[dict[str, str]], str]:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        return list(csv.DictReader(io.StringIO(text))), encoding
    raise ValueError(f"unable to decode CSV: {path}")


def _column(rows: list[dict[str, str]], name: str, *, required: bool = True) -> str | None:
    if not rows:
        raise ValueError("source table is empty")
    matches = [key for key in rows[0] if key.casefold() == name.casefold()]
    if len(matches) == 1:
        return matches[0]
    if required:
        raise ValueError(f"missing or ambiguous column: {name}")
    return None


def _numeric_flag(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    if number == 0:
        return 0
    if number == 1:
        return 1
    return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def freeze(
    island_data: Path,
    species_data: Path,
    frozen_cohort: Path,
) -> tuple[list[dict[str, str]], list[dict[str, object]], dict[str, object]]:
    islands, island_encoding = _read(island_data)
    species_rows, species_encoding = _read(species_data)
    cohort_rows, cohort_encoding = _read(frozen_cohort)

    island_list_col = _column(islands, "List_ID")
    island_id_col = _column(islands, "Island_ID")
    species_list_col = _column(species_rows, "List_ID")
    species_name_col = _column(species_rows, "Species_update")
    naturalised_col = _column(species_rows, "Naturalised", required=False)
    native_col = _column(species_rows, "Native", required=False)

    required_cohort = {"species", "primary_cohort_included", "status_apc"}
    if not cohort_rows or not required_cohort.issubset(cohort_rows[0]):
        raise ValueError("frozen cohort is missing required columns")
    declared_species = sorted(
        row["species"].strip()
        for row in cohort_rows
        if int(row["primary_cohort_included"]) == 1
    )
    if len(declared_species) != 886 or len(set(declared_species)) != 886:
        raise ValueError(f"expected 886 unique declared APC-native taxa, found {len(declared_species)}")
    if any(row["status_apc"] != "native" for row in cohort_rows if int(row["primary_cohort_included"]) == 1):
        raise ValueError("declared primary cohort contains a non-native APC status")
    declared_set = set(declared_species)

    list_to_island: dict[str, str] = {}
    for row in islands:
        list_id = row[island_list_col].strip()
        island_id = row[island_id_col].strip()
        if not list_id or not island_id:
            raise ValueError("blank list_ID or island_ID in island_data")
        previous = list_to_island.get(list_id)
        if previous is not None and previous != island_id:
            raise ValueError(f"list_ID maps to multiple islands: {list_id}")
        list_to_island[list_id] = island_id

    species_linked_lists: set[str] = set()
    raw_presence: dict[str, set[str]] = defaultdict(set)
    retained_presence: dict[str, set[str]] = defaultdict(set)
    explicit_non_native_rows = 0
    explicit_naturalised_rows = 0
    explicit_native_zero_rows = 0
    unknown_local_status_rows = 0
    retained_rows = 0

    for row in species_rows:
        list_id = row[species_list_col].strip()
        if not list_id:
            raise ValueError("blank List_ID in species_data")
        if list_id not in list_to_island:
            raise ValueError(f"species_data List_ID missing from island_data: {list_id}")
        species_linked_lists.add(list_id)
        taxon = row[species_name_col].strip()
        if taxon not in declared_set:
            continue
        island_id = list_to_island[list_id]
        raw_presence[taxon].add(island_id)

        naturalised = _numeric_flag(row[naturalised_col]) if naturalised_col else None
        native = _numeric_flag(row[native_col]) if native_col else None
        explicitly_non_native = naturalised == 1 or native == 0
        if explicitly_non_native:
            explicit_non_native_rows += 1
            explicit_naturalised_rows += int(naturalised == 1)
            explicit_native_zero_rows += int(native == 0)
            continue
        if naturalised is None and native is None:
            unknown_local_status_rows += 1
        retained_rows += 1
        retained_presence[taxon].add(island_id)

    surveyed_islands = sorted({list_to_island[list_id] for list_id in species_linked_lists}, key=int)
    if len(surveyed_islands) != 842:
        raise ValueError(f"expected 842 species-linked surveyed islands, found {len(surveyed_islands)}")

    edge_rows: list[dict[str, str]] = []
    species_audit: list[dict[str, object]] = []
    for taxon in declared_species:
        raw = raw_presence.get(taxon, set())
        retained = retained_presence.get(taxon, set())
        explicitly_removed_islands = raw - retained
        for island_id in sorted(retained, key=int):
            edge_rows.append({"species": taxon, "island_id": island_id})
        species_audit.append({
            "species": taxon,
            "declared_taxon": 1,
            "surveyed_islands": len(surveyed_islands),
            "raw_present_islands": len(raw),
            "primary_native_present_islands": len(retained),
            "primary_native_absent_islands": len(surveyed_islands) - len(retained),
            "explicit_non_native_only_islands_removed": len(explicitly_removed_islands),
            "below_original_10_presence_screen_after_local_cleaning": int(len(retained) < 10),
            "below_support_model_absolute_minimum_5_presences": int(len(retained) < 5),
        })

    summary = {
        "status": "preoutcome_native_incidence_freeze",
        "declared_taxa": len(declared_species),
        "surveyed_islands": len(surveyed_islands),
        "possible_taxon_island_cells": len(declared_species) * len(surveyed_islands),
        "primary_native_presence_edges": len(edge_rows),
        "primary_native_absence_cells": len(declared_species) * len(surveyed_islands) - len(edge_rows),
        "explicit_non_native_source_rows_excluded": explicit_non_native_rows,
        "explicit_naturalised_source_rows": explicit_naturalised_rows,
        "explicit_native_zero_source_rows": explicit_native_zero_rows,
        "retained_apc_native_source_rows": retained_rows,
        "retained_rows_with_unknown_local_status": unknown_local_status_rows,
        "taxa_below_10_native_presence_islands_after_cleaning": sum(
            int(row["below_original_10_presence_screen_after_local_cleaning"]) for row in species_audit
        ),
        "taxa_below_5_native_presence_islands_after_cleaning": sum(
            int(row["below_support_model_absolute_minimum_5_presences"]) for row in species_audit
        ),
        "incidence_rule": (
            "For APC-native declared taxa, a source row supports primary native incidence unless Naturalised==1 or Native==0. Missing/NA/non-numeric local status does not erase an APC-native record. Island presence is 1 when at least one retained row exists across that island's flora lists."
        ),
        "taxon_replacement_after_cleaning": false,
        "model_or_eog_outcomes_used": false,
        "encodings": {
            "island_data": island_encoding,
            "species_data": species_encoding,
            "frozen_cohort": cohort_encoding,
        },
    }
    return edge_rows, species_audit, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--frozen-cohort", type=Path, required=True)
    parser.add_argument("--output-edges", type=Path, required=True)
    parser.add_argument("--output-species-audit", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    edge_rows, species_audit, summary = freeze(args.island_data, args.species_data, args.frozen_cohort)
    args.output_edges.parent.mkdir(parents=True, exist_ok=True)
    with args.output_edges.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["species", "island_id"])
        writer.writeheader()
        writer.writerows(edge_rows)
    with args.output_species_audit.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(species_audit[0]))
        writer.writeheader()
        writer.writerows(species_audit)
    summary["native_presence_edges_sha256"] = _sha256(args.output_edges)
    summary["species_incidence_audit_sha256"] = _sha256(args.output_species_audit)
    args.output_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
