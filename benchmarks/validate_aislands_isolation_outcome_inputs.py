"""Validate every real input needed by the frozen island-isolation runner without scoring species outcomes.

This script may read the frozen occurrence table only to verify taxon/island identity and
construct the presence mapping expected by the already-declared runner. It does not fit
models, calculate EOG outcome contrasts, inspect C-R3, or produce species performance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_aislands_isolation_adequacy import (
    EXPECTED,
    find_unique_sha,
    load_climate,
    load_cohort,
    load_folds,
    load_model_audit,
    load_presence_sets,
    load_scalar_table,
    sha256_file,
)


def validate(args: argparse.Namespace) -> dict[str, object]:
    root = args.repo_root.resolve()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if contract["schema_version"] != "eog_aislands_isolation_adequacy_v1_3":
        raise RuntimeError("wrong frozen island-isolation contract")
    if contract["reference_design_status"] != "final_before_extension_species_outcomes":
        raise RuntimeError("reference hierarchy is not closed")
    if contract["outcomes_inspected_for_this_extension"] is not False:
        raise RuntimeError("contract no longer records an uninspected extension")

    fold_path = find_unique_sha(root, EXPECTED["folds"])
    climate_path = find_unique_sha(root, EXPECTED["climate"])
    cohort_path = find_unique_sha(root, EXPECTED["cohort"])

    for path, expected in (
        (args.island_data, EXPECTED["island_data"]),
        (args.species_data, EXPECTED["species_data"]),
        (args.area_csv, EXPECTED["area"]),
        (args.mainland_csv, EXPECTED["mainland"]),
    ):
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"input SHA mismatch for {path}: {actual} != {expected}")

    cohort = load_cohort(cohort_path)
    folds = load_folds(fold_path)
    climate = load_climate(climate_path)
    island_ids, coords = load_model_audit(args.island_audit_csv)
    areas = load_scalar_table(args.area_csv, "area_km2")
    mainland = load_scalar_table(args.mainland_csv, "distance_to_australia_mainland_km")

    island_set = set(island_ids)
    if len(island_set) != 842:
        raise RuntimeError("model audit does not resolve exactly 842 unique islands")
    for label, mapping in (("folds", folds), ("climate", climate), ("areas", areas), ("mainland", mainland)):
        if set(mapping) != island_set:
            raise RuntimeError(f"{label} island identities differ from the frozen model audit")

    presence_sets = load_presence_sets(args.species_data, island_set, cohort)
    presence_counts = [len(presence_sets[taxon]) for taxon in cohort]
    if len(presence_sets) != 886 or min(presence_counts) < 1:
        raise RuntimeError("frozen cohort/presence mapping is incomplete")

    fold_levels = sorted(set(folds.values()), key=lambda value: (len(str(value)), str(value)))
    if len(fold_levels) != 5:
        raise RuntimeError(f"expected five frozen fold levels, got {fold_levels}")

    summary = {
        "schema_version": "eog_aislands_isolation_input_validation_v1",
        "status": "real_inputs_validated_without_extension_outcome_scoring",
        "contract_schema": contract["schema_version"],
        "islands": len(island_ids),
        "taxa": len(cohort),
        "folds": len(fold_levels),
        "presence_count_min": min(presence_counts),
        "presence_count_median": sorted(presence_counts)[len(presence_counts) // 2],
        "presence_count_max": max(presence_counts),
        "coordinate_shape": list(coords.shape),
        "input_sha256": {
            "folds": EXPECTED["folds"],
            "climate": EXPECTED["climate"],
            "cohort": EXPECTED["cohort"],
            "island_data": EXPECTED["island_data"],
            "species_data": EXPECTED["species_data"],
            "area": EXPECTED["area"],
            "mainland": EXPECTED["mainland"],
            "contract": sha256_file(args.contract),
        },
        "models_fitted": 0,
        "heldout_predictions_scored": 0,
        "c_minus_r3_inspected": False,
        "scientific_boundary": "schema/identity validation only; no extension model fit or outcome contrast",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--contract", type=Path, default=Path("validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json"))
    parser.add_argument("--island-data", type=Path, required=True)
    parser.add_argument("--species-data", type=Path, required=True)
    parser.add_argument("--island-audit-csv", type=Path, required=True)
    parser.add_argument("--area-csv", type=Path, required=True)
    parser.add_argument("--mainland-csv", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    validate(parse_args())
