#!/usr/bin/env python3
"""Public README/inventory-only audit; NEVER inspect Helgeland bird records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
CONTRACT = BASE / "helgeland_parent_recruit_2025_sourceonly_v1.json"
FROZEN = BASE / "helgeland_source_metadata_frozen_v1.json"

EXPECTED_FILES = {
    "LRS.txt": 3972793,
    "ARS_Survival.txt": 3972792,
    "Rectype_LRS.txt": 3972795,
    "Rectype_ARS_Survival.txt": 3972794,
}
REQUIRED_GATES = ("SOURCE_PIN", "PHYSICAL_HEADERS", "ID_LINK",
                  "TIME_ORIENTATION", "OBSERVATION_PROCESS", "HELDOUT")


def qualify(contract: dict, inventory: dict) -> dict:
    if contract.get("schema") != "eog.helgeland.same_archive_parent_recruit.source_only_contract.v1":
        raise ValueError("Unrecognized source-only contract")
    if contract.get("status") != "FROZEN_PUBLIC_README_ONLY__NO_PHYSICAL_HEADERS_OR_BIRD_ROWS":
        raise ValueError("Do not silently upgrade this source-only evidence stage")
    if contract.get("frozen_before_data_exposure") is not True:
        raise ValueError("Pre-response freeze claim must remain explicit")
    source = contract["source"]
    source_meta = inventory["inventories"]["fitness_2025"]
    if source["dataset"] != "fitness_2025" or source["doi"] != source_meta["doi"]:
        raise ValueError("Wrong 2025 dataset DOI")
    if source["dryad_version_id"] != source_meta["dryad_version_id"] or source["dryad_version_number"] != 2:
        raise ValueError("Changed source version")
    observed = contract["expected_headers"]
    if set(observed) != set(EXPECTED_FILES):
        raise ValueError("Exactly four 2025 source header contracts required")
    registered = {f["name"]: f for f in source_meta["files"]}
    for name, file_id in EXPECTED_FILES.items():
        if name not in registered or observed[name]["dryad_file_id"] != file_id:
            raise ValueError("Frozen file ID changed")
        if registered[name]["file_metadata_id"] != file_id:
            raise ValueError("File ID differs from pinned public Dryad inventory")
        if registered[name]["size_bytes"] <= 0 or len(registered[name]["source_declared_sha256"]) != 64:
            raise ValueError("Incomplete source metadata")
        tokens = observed[name]["required_exact"]
        if not isinstance(tokens, list) or not tokens or len(tokens) != len(set(tokens)):
            raise ValueError("Invalid frozen README role names")
    candidates = contract["candidate_links"]
    if len(candidates) != 6:
        raise ValueError("Six predeclared within-2025 candidate edges expected")
    for entry in candidates:
        if entry["qualified"] is not False:
            raise ValueError("A join candidate cannot be promoted without bird row evidence")
        for member in ("left", "right"):
            filename, colon, field = entry[member].partition(":")
            if colon != ":" or filename not in observed or field not in observed[filename]["required_exact"]:
                raise ValueError("Candidate join refers to absent published README role")
    gates = {gate["gate"]: gate["status"] for gate in contract["gates"]}
    if set(gates) != set(REQUIRED_GATES) or gates["SOURCE_PIN"] != "METADATA_ONLY_PINNED":
        raise ValueError("Required pre-response gates missing")
    if any(gates[gate] != "HOLD" for gate in REQUIRED_GATES[1:]):
        raise ValueError("Insufficient independent evidence to advance any later gate")
    if any(flag is not False for flag in contract["prohibitions"].values()):
        raise ValueError("A forbidden temporal or biological claim was enabled")
    if contract["source_rows_opened"] is not False or contract["ecological_endpoint_authorized"] is not False:
        raise ValueError("Biological data still unopened; no endpoint authorized")
    if contract["original_cross_archive_2024_2025_contract_unchanged"] is not True:
        raise ValueError("Original frozen cross-archive contract must not change")
    if contract["original_helgeland_hold"] != "HOLD_DIRECTIONAL_INDIVIDUAL_PROXY_ONLY":
        raise ValueError("Original observed-provenance HOLD must not change")
    return {
        "schema": "eog.helgeland.same_archive_parent_recruit_sourceonly_receipt.v1",
        "status": "HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED",
        "doi": source["doi"],
        "frozen_version": source["dryad_version_id"],
        "expected_files": sorted(EXPECTED_FILES),
        "candidate_join_links": len(candidates),
        "public_readme_roles_only": True,
        "source_declared_digests_not_byte_verified": True,
        "physical_headers_read": False,
        "parent_recruit_id_values_joined": False,
        "parent_breeding_island_at_offspring_birth_verified": False,
        "offspring_first_settlement_island_verified": False,
        "prospective_predictors_verified": False,
        "first_island_colonization_or_source_loss_identified": False,
        "ecological_endpoint_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory = json.loads(FROZEN.read_text(encoding="utf-8"))
    receipt = qualify(contract, inventory)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "candidate_join_links": receipt["candidate_join_links"]}))


if __name__ == "__main__":
    main()
