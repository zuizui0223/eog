#!/usr/bin/env python3
"""Filter Glanville survey rows to the already-frozen patch-network universe.

This is a schema/eligibility adapter, not an outcome transformation.  It reads the
patch ID field only to decide whether a row belongs to the frozen node universe and
copies all retained fields verbatim.  It never parses or branches on population,
previous_population, or any other biological response value.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EXPECTED_SURVEY_HEADER = (
    "year",
    "patch",
    "population",
    "plantago",
    "veronica",
    "plantago_low",
    "veronica_low",
    "plantago_dry",
    "veronica_dry",
    "grazing_presence",
    "grazing_intensity",
    "previous_population",
)


def read_network_ids(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != ("patch", "x", "y", "area"):
            raise ValueError(f"unexpected patch_network schema: {reader.fieldnames!r}")
        ids = {str(row["patch"]).strip() for row in reader}
    if not ids or "" in ids:
        raise ValueError("patch_network IDs must be non-empty")
    return ids


def filter_survey(
    network_path: Path,
    survey_path: Path,
    output_path: Path,
    audit_path: Path,
) -> dict[str, object]:
    network_ids = read_network_ids(network_path)
    retained = 0
    excluded = 0
    excluded_ids: set[str] = set()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with survey_path.open("r", encoding="utf-8-sig", newline="") as source, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as target:
        reader = csv.DictReader(source, delimiter="\t")
        if tuple(reader.fieldnames or ()) != EXPECTED_SURVEY_HEADER:
            raise ValueError(f"unexpected survey_data schema: {reader.fieldnames!r}")
        writer = csv.DictWriter(
            target,
            fieldnames=list(EXPECTED_SURVEY_HEADER),
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in reader:
            patch = str(row["patch"]).strip()
            if patch in network_ids:
                writer.writerow(row)
                retained += 1
            else:
                excluded += 1
                excluded_ids.add(patch)

    audit = {
        "status": "frozen_node_survey_filter_complete",
        "network_node_count": len(network_ids),
        "retained_survey_rows": retained,
        "excluded_survey_rows": excluded,
        "excluded_unique_patch_ids": len(excluded_ids),
        "population_response_values_parsed_or_used_for_filter": False,
        "filter_key": "patch membership in frozen patch_network only",
        "node_universe_expanded": False,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch-network", type=Path, required=True)
    parser.add_argument("--survey", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    audit = filter_survey(args.patch_network, args.survey, args.output, args.audit)
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
