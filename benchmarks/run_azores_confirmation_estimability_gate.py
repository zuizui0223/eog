#!/usr/bin/env python3
"""Run the frozen Azores confirmation until the first non-estimability gate.

The response/comparison contract was frozen before any Taxon or Distribution data row was
read. This runner verifies the exact source bytes, applies the frozen canonical-species and
vascular-plant scope, and stops before parsing distribution responses or fitting models if
that scope contains no eligible taxa. It must not repair the frozen taxonomic rule from
observed source vocabulary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path


EXPECTED_SOURCE_SHA256 = "4129876585a2168abe68bd048d241dfe080e4135ab2f0a0bf1b184a4f50bb2d5"
CONTRACT = Path("benchmarks/azores_confirmation_outcome_contract.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _read_tsv(bundle: zipfile.ZipFile, name: str) -> tuple[list[str], list[list[str]]]:
    with bundle.open(name) as raw:
        wrapper = io.TextIOWrapper(raw, encoding="utf-8", newline="")
        reader = csv.reader(wrapper, delimiter="\t")
        header = next(reader)
        rows = [row for row in reader]
    return header, rows


def _resolve_canonical_rows(header: list[str], rows: list[list[str]]) -> tuple[list[list[str]], dict[str, int]]:
    index = {name: i for i, name in enumerate(header)}
    required = {
        "id", "taxonID", "acceptedNameUsageID", "taxonRank", "kingdom", "phylum",
        "higherClassification",
    }
    missing = required - set(index)
    if missing:
        raise ValueError(f"Taxon core missing frozen fields: {sorted(missing)}")

    by_taxon_id = {row[index["taxonID"]]: row for row in rows if row[index["taxonID"]]}
    by_core_id = {row[index["id"]]: row for row in rows if row[index["id"]]}
    resolved: dict[str, list[str] | None] = {}
    unresolved = 0
    cycles = 0

    def resolve(row: list[str]) -> list[str] | None:
        nonlocal unresolved, cycles
        start_key = row[index["taxonID"]] or row[index["id"]]
        if start_key in resolved:
            return resolved[start_key]
        current = row
        seen: set[str] = set()
        while True:
            key = current[index["taxonID"]] or current[index["id"]]
            if key in seen:
                cycles += 1
                resolved[start_key] = None
                return None
            seen.add(key)
            accepted = current[index["acceptedNameUsageID"]].strip()
            if not accepted or accepted == current[index["taxonID"]] or accepted == current[index["id"]]:
                resolved[start_key] = current
                return current
            nxt = by_taxon_id.get(accepted) or by_core_id.get(accepted)
            if nxt is None:
                unresolved += 1
                resolved[start_key] = None
                return None
            current = nxt

    canonical_by_key: dict[str, list[str]] = {}
    for row in rows:
        canonical = resolve(row)
        if canonical is None:
            continue
        key = canonical[index["taxonID"]] or canonical[index["id"]]
        canonical_by_key[key] = canonical
    return list(canonical_by_key.values()), {
        "unresolved_accepted_references": unresolved,
        "accepted_reference_cycles": cycles,
    }


def evaluate(source_zip: Path) -> dict[str, object]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract["status"] != "pre_outcome_response_and_comparison_contract_frozen":
        raise ValueError("Azores outcome contract is not in the frozen pre-outcome state")
    actual_sha = sha256(source_zip)
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Azores source SHA changed: {actual_sha}")

    with zipfile.ZipFile(source_zip) as bundle:
        names = set(bundle.namelist())
        if not {"taxon.txt", "distribution.txt", "meta.xml"}.issubset(names):
            raise ValueError("Azores DwC-A source is missing the frozen core/extension files")
        header, rows = _read_tsv(bundle, "taxon.txt")

    index = {name: i for i, name in enumerate(header)}
    canonical_rows, resolution = _resolve_canonical_rows(header, rows)
    species_rows = [row for row in canonical_rows if normalize(row[index["taxonRank"]]) == "species"]
    plant_species = [row for row in species_rows if normalize(row[index["kingdom"]]) == "plantae"]
    eligible = []
    for row in plant_species:
        phylum = normalize(row[index["phylum"]])
        higher_tokens = set(normalize(row[index["higherClassification"]]).split())
        if phylum == "tracheophyta" or "tracheophyta" in higher_tokens:
            eligible.append(row)

    phyla = Counter((row[index["phylum"]] or "").strip() for row in plant_species)
    summary: dict[str, object] = {
        "status": "eligible_taxa_available" if eligible else "non_estimable_pre_model_taxon_scope_zero",
        "source_sha256": actual_sha,
        "taxon_core_rows_read": len(rows),
        "distribution_rows_read": 0,
        "canonical_taxa_after_accepted_name_resolution": len(canonical_rows),
        "canonical_species": len(species_rows),
        "canonical_plantae_species": len(plant_species),
        "eligible_species_under_frozen_tracheophyta_rule": len(eligible),
        "plantae_species_phylum_counts": dict(sorted(phyla.items())),
        **resolution,
        "species_island_response_values_scored": False,
        "predictive_models_fitted": False,
        "confirmation_metric_computed": False,
        "contract_changed_after_source_rows": False,
    }
    if not eligible:
        summary["stop_reason"] = (
            "The frozen vascular rule requires canonical species-level Plantae with phylum "
            "Tracheophyta or a Tracheophyta token in higherClassification. The exact frozen "
            "source contains no canonical taxon satisfying that rule. Per the frozen no-retuning "
            "contract, the rule is not broadened to Magnoliophyta/Pteridophyta/Lycopodiophyta/"
            "Pinophyta after source vocabulary is observed."
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
