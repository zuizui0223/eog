import csv
import hashlib
import io
import json
import runpy
import zipfile
from pathlib import Path

import pytest


_NS = runpy.run_path("benchmarks/run_azores_confirmation_estimability_gate.py")
normalize = _NS["normalize"]
_resolve_canonical_rows = _NS["_resolve_canonical_rows"]


def test_normalize_matches_frozen_ascii_case_punctuation_policy():
    assert normalize(" São-Jorge ") == "sao jorge"
    assert normalize("TRACHEOPHYTA") == "tracheophyta"


def test_accepted_name_resolution_collapses_synonym_to_canonical_row():
    header = [
        "id", "taxonID", "acceptedNameUsageID", "taxonRank", "kingdom", "phylum",
        "higherClassification",
    ]
    accepted = ["core-a", "tax-a", "", "species", "Plantae", "Magnoliophyta", "Plantae; Magnoliophyta"]
    synonym = ["core-s", "tax-s", "tax-a", "species", "Plantae", "Magnoliophyta", "Plantae; Magnoliophyta"]
    canonical, diagnostics = _resolve_canonical_rows(header, [accepted, synonym])
    assert len(canonical) == 1
    assert canonical[0][1] == "tax-a"
    assert diagnostics == {
        "unresolved_accepted_references": 0,
        "accepted_reference_cycles": 0,
    }


def test_frozen_contract_still_requires_literal_tracheophyta_scope():
    contract = json.loads(Path("benchmarks/azores_confirmation_outcome_contract.json").read_text(encoding="utf-8"))
    assert "Tracheophyta" in contract["taxon_scope"]["vascular_rule"]
    assert contract["taxon_scope"]["post_outcome_scope_change_forbidden"] is True
    assert "Do not retune" in contract["no_added_value_rule"]
