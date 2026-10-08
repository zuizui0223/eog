"""Locked, response-free external-data prequalification for Lepanthes rupestris."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_lepanthes_pre_response_metadata_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("lepanthes_gate", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def catalog():
    return json.loads(
        (ROOT / "validation" / "eog_virtual_world_ecology_synthesis_v1"
         / "lepanthes_pre_response_catalog_v1.json").read_text(encoding="utf-8")
    )


def write_catalog(tmp_path, d):
    path = tmp_path / "mutated_catalog.json"
    path.write_text(json.dumps(d, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_metadata_only_stop_has_full_provenance_and_no_biological_access():
    x = load_module().audit_metadata_only()
    assert x["status"] == "STOP_WITHIN_DECLARED_PRE_RESPONSE_GATE"
    assert x["terminal_code"] == "STOP_REGISTRY_SCHEMA_AND_DETECTION_UNQUALIFIED"
    assert x["doi"] == "10.5061/dryad.9p8cz8wc6"
    assert x["published_reference"] == "10.1111/1365-2745.13361"
    assert x["published_model_count"] == 290
    assert x["advertised_files"] == 1
    assert x["advertised_patches"] == 975
    assert x["dictionary_columns"] == 23
    assert x["survey_columns"] == 17
    assert x["survey_per_year"] == {
        "1999": 1, "2000": 2, "2001": 2, "2002": 3, "2003": 1,
        "2004": 2, "2005": 2, "2006": 1, "2007": 2, "2008": 1,
    }
    assert x["column_conflict_fields"] == sorted([
        "horizontal_coordinate_x",
        "horizontal_coordinate_y",
        "vertical_coordinate",
        "survey_2004_visit_2",
    ])
    assert len(x["unmet_gate_ids"]) == 7
    assert x["model_fits_performed_by_this_script"] == 0
    assert x["prediction_scores_calculated_by_this_script"] == 0
    assert x["focal_response_rows_opened_by_this_script"] is False
    assert "not a negative ecological result" in x["conclusion"].lower()


def test_all_17_visit_codes_present_in_published_order():
    d = catalog()
    a = d["sources"]["dryad"]["dictionary_column_names"]
    b = d["sources"]["ecodata"]["dictionary_column_names"]
    assert len(a) == len(b) == 23
    assert sum(x != y for x, y in zip(a, b)) == 4
    visits = d["metadata_contract"]["dryad_visit_sequence"]
    assert [v["column"] for v in visits] == a[5:-1]
    assert visits[10] == {"column": "X7104", "year": 2004, "within_year_order": 2}
    assert "X71704" in b
    assert d["metadata_contract"]["one_visit_years"] == [1999, 2003, 2006, 2008]


@pytest.mark.parametrize(
    "mutation",
    [
        ("current_gates", "REAL_RESPONSE_OPENING_AUTHORIZED", True),
        ("current_gates", "PHYSICAL_CSV_HEADER_INDEPENDENTLY_VERIFIED", True),
        ("current_gates", "DISTINCT_RESPONSE_INDEPENDENT_PATCH_REGISTRY_VERIFIED", True),
        ("target_and_comparator", "response_row_scoring_authorized", True),
        ("metadata_contract", "allow_silent_alias_normalization", True),
        ("metadata_contract", "actual_csv_header_authorized_to_be_inferred_from_dictionary", True),
        ("decision_rules", "status", "GO_FOR_BIOLOGICAL_SCORING"),
        ("sources", "dryad", "invalid DOI"),
    ],
)
def test_metadata_gate_fails_closed_on_premature_promotion(tmp_path, mutation):
    a, b, value = mutation
    d = catalog()
    if a == "sources":
        d["sources"][b]["doi"] = value
    else:
        d[a][b] = value
    with pytest.raises(ValueError):
        load_module().audit_metadata_only(write_catalog(tmp_path, d))


def test_cannot_resolve_physical_schema_by_guessing_a_dictionary_alias(tmp_path):
    d = catalog()
    d["sources"]["ecodata"]["dictionary_column_names"][3] = "not_a_physical_header"
    with pytest.raises(ValueError):
        load_module().audit_metadata_only(write_catalog(tmp_path, d))


def test_audit_uses_no_network_or_biological_file_reader():
    text = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "import requests", "import urllib", "import socket", "import pandas",
        "import numpy", "subprocess.", "read_csv(", "open('lepa_all.csv'",
        'open("lepa_all.csv"',
    ):
        assert forbidden not in text
    assert "read_bytes()" in text
    assert "DEFAULT_CATALOG" in text
