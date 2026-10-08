"""Source-only contract assertions: synthetic mutations; NEVER load bird records."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
SCRIPT = ROOT / "scripts/audit_helgeland_2025_parent_recruit_contract_v1.py"


def engine():
    spec = importlib.util.spec_from_file_location("parent_recruit_sourceonly", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixtures():
    return (
        json.loads((BASE / "helgeland_parent_recruit_2025_sourceonly_v1.json").read_text()),
        json.loads((BASE / "helgeland_source_metadata_frozen_v1.json").read_text()),
    )


def test_within_archive_path_exists_but_is_not_observed_provenance():
    contract, inventory = fixtures()
    receipt = engine().qualify(contract, inventory)
    assert receipt["status"] == "HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED"
    assert receipt["expected_files"] == [
        "ARS_Survival.txt", "LRS.txt", "Rectype_ARS_Survival.txt", "Rectype_LRS.txt"
    ]
    assert receipt["candidate_join_links"] == 6
    for field in ("physical_headers_read", "parent_recruit_id_values_joined",
                  "parent_breeding_island_at_offspring_birth_verified",
                  "offspring_first_settlement_island_verified",
                  "prospective_predictors_verified",
                  "first_island_colonization_or_source_loss_identified",
                  "ecological_endpoint_authorized"):
        assert receipt[field] is False


@pytest.mark.parametrize("mutation", [
    "wrong_version", "wrong_file_id", "unregistered_source_file",
    "invented_readme_header", "duplicate_candidate_edge",
    "invented_column", "synthetically_qualified_join", "changed_gates",
    "authorizes_endpoint", "turns_on_temporal_claim", "changes_original_hold",
])
def test_any_invalid_promotion_fails_closed(mutation):
    contract, inventory = fixtures()
    contract = copy.deepcopy(contract)
    inventory = copy.deepcopy(inventory)
    if mutation == "wrong_version":
        contract["source"]["dryad_version_id"] = 0
    elif mutation == "wrong_file_id":
        contract["expected_headers"]["Rectype_LRS.txt"]["dryad_file_id"] = -5
    elif mutation == "unregistered_source_file":
        contract["expected_headers"]["new_unverified_file.txt"] = {
            "dryad_file_id": 0, "required_exact": ["guess"]
        }
    elif mutation == "invented_readme_header":
        contract["expected_headers"]["LRS.txt"]["required_exact"].append("parent.breeding.island")
    elif mutation == "duplicate_candidate_edge":
        contract["candidate_links"][1] = copy.deepcopy(contract["candidate_links"][0])
    elif mutation == "invented_column":
        contract["candidate_links"][0]["left"] = "Rectype_LRS.txt:parent_birth_island"
    elif mutation == "synthetically_qualified_join":
        contract["candidate_links"][0]["qualified"] = True
    elif mutation == "changed_gates":
        contract["gates"][3]["status"] = "PASS"
    elif mutation == "authorizes_endpoint":
        contract["ecological_endpoint_authorized"] = True
    elif mutation == "turns_on_temporal_claim":
        contract["prohibitions"]["infer_parent_breeding_island_from_retrospective_adult_island"] = True
    elif mutation == "changes_original_hold":
        contract["original_helgeland_hold"] = "UNFROZEN"
    with pytest.raises(ValueError):
        engine().qualify(contract, inventory)


def test_no_biological_source_reader_or_http_endpoint_in_contract_auditor():
    code = SCRIPT.read_text(encoding="utf-8")
    for banned in ("urlopen(", "import requests", "import urllib", "read_csv(",
                   "import pandas", "import numpy", "/download", "socket.",
                   "subprocess", "import sqlite3"):
        assert banned not in code
    assert "HOLD_PARENT_RECRUIT_TIME_ORIENTATION_UNVERIFIED" in code


def test_readme_roles_do_not_infer_time_resolved_parent_location():
    contract, _ = fixtures()
    heads = contract["expected_headers"]
    assert {"dam", "sire", "recruit", "lastobs.island"}.issubset(
        heads["Rectype_LRS.txt"]["required_exact"])
    assert {"dam", "sire", "recruit", "obs.year", "lastobs.island"}.issubset(
        heads["Rectype_ARS_Survival.txt"]["required_exact"])
    assert "adult.island" in heads["LRS.txt"]["required_exact"]
    assert "fiflok" in heads["ARS_Survival.txt"]["required_exact"]
    assert "laflok" in heads["ARS_Survival.txt"]["required_exact"]
    assert all(not edge["qualified"] for edge in contract["candidate_links"])
    assert contract["prohibitions"]["infer_year_specific_island_from_first_or_last_observed_island"] is False
