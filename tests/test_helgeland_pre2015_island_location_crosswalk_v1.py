"""Invented aggregate labels only; never read original bird/individual data."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_helgeland_pre2015_island_location_crosswalk_v1 import (
    audit, normalize_label, verify_protocol,
)


def rec(when, code, label, stage="capt"):
    return {
        "date": when, "Island": code, "Location": label, "stage": stage,
        "ID": "UNSAFE_INDIVIDUAL_ID", "Year": "NONCONTEMPORANEOUS",
        "Least_age": "RETROSPECTIVE", "scriptsex": "FUTURE",
    }


def policy():
    return json.loads((
        BASE / "helgeland_pre2015_island_location_crosswalk_protocol_v1.json"
    ).read_text(encoding="utf-8"))


def invented():
    return [
        rec("1999-06-01", "1", "Aldra", "nest"),
        rec("2007-06-01", "1", " alDra ", "capt"),
        rec("2000-05-01", "2", "Gjerøy"),
        rec("2000-05-01", "0", "other helgeland", "nest"),
        rec("2010-05-01", "0", "Other  Helgeland", "obs"),
        rec("2001-07-01", "33", "lurøy-onøy"),
        rec("2011-07-01", "33", "LURØY-ONØY", "obs"),
        rec("2005-05-01", "11", "Træna"),
        rec("2005-05-01", "22", "Lovund"),
        rec("2009-05-01", "23", "lovund"),
        rec("2009-05-01", "99", "Ytre Kvarøy"),
        rec("1998-05-01", "21", "Aldra"),
        rec("2008-05-01", "21", "Nesøy"),
    ]


def test_literal_code_to_label_mapping_flags_non_bijection_and_both_periods():
    result = audit(invented(), policy(), check_real_preexposed=False)
    c = result["counts"]
    assert c["total_file_rows"] == 13
    assert c["eligible_rows_pre2015"] == 13
    assert c["rows_before_1994"] == 0
    assert c["rows_after_2014"] == 0
    assert c["raw_island_code_0_eligible_rows"] == 2
    assert c["raw_island_code_33_eligible_rows"] == 2
    assert c["nest_rows"] == 2
    assert c["capt_rows"] == 9
    assert c["obs_rows"] == 2
    assert c["codes_with_multiple_normalized_labels"] == 1
    assert c["normalized_labels_with_multiple_codes"] == 2
    assert c["distinct_code_location_pairs"] == 10
    assert result["individual_IDs_or_trajectories_exported"] is False
    assert result["source_code_to_physical_coordinates_verified"] is False

    codes = {r["island_code_raw"]: r for r in result["per_code"]}
    assert codes["1"]["single_location_label_internal"] is True
    assert codes["1"]["same_label_in_both_bins"] is True
    assert codes["21"]["single_location_label_internal"] is False
    assert codes["21"]["same_label_in_both_bins"] is False
    assert codes["2"]["same_label_in_both_bins"] is None
    assert codes["0"]["normalized_location_labels"] == ["other helgeland"]
    assert codes["33"]["normalized_location_labels"] == ["lurøy-onøy"]

    names = {r["location_normalized"]: r for r in result["per_location"]}
    assert names["lovund"]["raw_island_codes"] == ["22", "23"]
    assert names["aldra"]["raw_island_codes"] == ["1", "21"]
    assert names["other helgeland"]["published_2021_name_exact_text"] is None
    assert names["lurøy-onøy"]["published_2021_name_exact_text"] == "Lurøy-Onøy"
    assert names["ytre kvarøy"]["explicit_non_synonym"] is True
    assert names["ytre kvarøy"]["published_2021_name_exact_text"] is None
    assert result["literal_0_33_rows"]["0"]["row_count"] == 2
    assert result["literal_0_33_rows"]["33"]["row_count"] == 2
    assert "UNSAFE_INDIVIDUAL_ID" not in json.dumps(result)


def test_2015_future_poison_never_reads_identity_or_site_or_stage():
    class Poison(dict):
        def __getitem__(self, key):
            if key != "date":
                raise RuntimeError("Out of window accessed: " + key)
            return super().__getitem__(key)

    rows = invented() + [
        Poison(rec("2015-01-01", "0", "FUTURE SECRET")),
        Poison(rec("1993-12-31", "33", "PAST SECRET")),
    ]
    x = audit(rows, policy(), check_real_preexposed=False)
    assert x["counts"]["total_file_rows"] == 15
    assert x["counts"]["rows_before_1994"] == 1
    assert x["counts"]["rows_after_2014"] == 1
    assert x["counts"]["raw_island_code_0_eligible_rows"] == 2
    assert x["counts"]["raw_island_code_33_eligible_rows"] == 2
    assert "FUTURE SECRET" not in json.dumps(x)
    assert "PAST SECRET" not in json.dumps(x)


def test_no_individual_id_read_even_within_allowed_period():
    class IDPoison(dict):
        def __getitem__(self, key):
            if key in ("ID", "Year", "Least_age", "Least_hatchyear", "scriptsex"):
                raise RuntimeError("Forbidden person/hindsight column: " + key)
            return super().__getitem__(key)

    rows = [IDPoison(r) for r in invented()]
    assert audit(rows, policy(), check_real_preexposed=False) == audit(
        invented(), policy(), check_real_preexposed=False
    )


def test_raw_variants_are_preserved_but_case_only_spelling_is_normalized():
    x = audit(invented(), policy(), check_real_preexposed=False)
    loc = {r["location_normalized"]: r for r in x["per_location"]}
    assert loc["aldra"]["raw_location_variants"] == ["Aldra", "alDra"]
    assert loc["other helgeland"]["raw_location_variants"] == [
        "Other  Helgeland", "other helgeland"
    ]
    assert normalize_label("  LURØY-ONØY  ") == "lurøy-onøy"
    assert normalize_label("Ytre Kvarøy") != normalize_label("Indre Kvarøy")
    assert normalize_label("Træna") != normalize_label("Traena")


def test_real_data_total_contract_is_not_relaxed_during_actual_run():
    rows = invented()
    with pytest.raises(ValueError, match="Actual data differ"):
        audit(rows, policy(), check_real_preexposed=True)


def test_strong_scientific_claims_are_never_promoted():
    p = policy()
    p["claim_bounds"]["no_external_geographic_coordinate_verification"] = False
    with pytest.raises(ValueError, match="scientific claims"):
        audit(invented(), p, check_real_preexposed=False)
    p = policy()
    p["strict_evidence_rules"]["2020_Niskanen_numeric_cross_archive_equivalence_never_inferred"] = False
    with pytest.raises(ValueError, match="scientific claims"):
        audit(invented(), p, check_real_preexposed=False)
    p = policy()
    p["published_2021_names"].append("Ytre Kvarøy")
    with pytest.raises(ValueError, match="scientific claims"):
        audit(invented(), p, check_real_preexposed=False)


def test_category_bound_is_enforced():
    p = policy()
    many = [
        rec("2005-05-01", str(i), "Fake island " + str(i))
        for i in range(81)
    ]
    with pytest.raises(ValueError, match="Excess category cardinality"):
        audit(many, p, check_real_preexposed=False)


def test_source_script_forbids_ID_lookups_and_historical_leakage():
    p = policy()
    verify_protocol(p)
    assert p["source"]["version_id"] == 421942
    assert p["frozen_preexposed_checks"]["eligible_rows_pre2015"] == 51162
    assert p["frozen_preexposed_checks"]["raw_island_code_0_eligible_rows"] == 2613
    assert p["frozen_preexposed_checks"]["raw_island_code_33_eligible_rows"] == 1738
    assert p["claim_bounds"]["no_2020_v8_code_crosswalk_certification"] is True
    script = (
        ROOT / "scripts/audit_helgeland_pre2015_island_location_crosswalk_v1.py"
    ).read_text(encoding="utf-8")
    assert script.index('stamp = strict_observed_date(row["date"])') < (
        script.index('code = row["Island"]')
    )
    for banned in (
        'row["ID"]', 'row["Year"]', 'row["Least_age"]',
        'row["Least_hatchyear"]', 'row["scriptsex"]',
        "import pandas", "read_csv(", "urllib",
    ):
        assert banned not in script


def test_original_source_audited_mapping_receipt_and_scientific_boundary():
    frozen = json.loads((
        BASE / "helgeland_pre2015_island_location_crosswalk_observed_frozen_v1.json"
    ).read_text(encoding="utf-8"))
    assert frozen["schema"] == (
        "eog.helgeland.pre2015.island_location_crosswalk.frozen_source_receipt.v1"
    )
    assert frozen["protocol_freeze_commit"] == (
        "db66fb583db890ea8c7bed251ae37e235ba8ceee"
    )
    assert frozen["authority"]["github_actions_run_id"] == 39202831125
    assert frozen["authority"]["github_actions_artifact_id"] == 12165010358
    assert frozen["authority"]["artifact_zip_sha256"] == (
        "34e54b9781b8afadc823ccf3f27e6c825c1a12afc3a1bb3de9b2834ffe9fcade"
    )
    result = frozen["receipt"]
    assert result["frozen_original_sha256_header_first_events_rechecked"] is True
    assert result["frozen_0_33_row_counts_reconciled"] is True
    c = result["counts"]
    assert c["total_file_rows"] == 73593
    assert c["eligible_rows_pre2015"] == 51162
    assert c["distinct_raw_island_codes"] == 12
    assert c["distinct_normalized_location_labels"] == 12
    assert c["distinct_code_location_pairs"] == 12
    assert c["codes_with_multiple_normalized_labels"] == 0
    assert c["normalized_labels_with_multiple_codes"] == 0
    assert c["published_2021_named_labels_observed"] == 11
    assert c["published_2021_named_labels_not_observed"] == 0
    assert result["unobserved_2021_named_labels"] == []
    assert result["literal_0_33_rows"]["0"] == {
        "row_count": 2613, "normalized_location_labels": ["other helgeland"]
    }
    assert result["literal_0_33_rows"]["33"] == {
        "row_count": 1738, "normalized_location_labels": ["lurøy-onøy"]
    }
    assert all(x["same_label_in_both_bins"] is True for x in result["per_code"])
    assert all(x["single_location_label_internal"] is True for x in result["per_code"])
    assert all(x["single_code_internal"] is True for x in result["per_location"])
    assert all(x["explicit_non_synonym"] is False for x in result["per_location"])
    assert all(x["location_normalized"] not in ("ytre kvarøy", "sundøy")
               for x in result["per_location"])
    assert sum(x["pair_direct_row_count"] for x in result["code_location_pairs"]) == 51162
    assert result["strict_scope"] == policy()["claim_bounds"]
    assert result["external_2020_code_equivalence_verified"] is False
    assert result["source_code_to_physical_coordinates_verified"] is False
    assert result["surveyed_zero_or_recruitment_verified"] is False
    assert result["independent_EOG_forecast_scored"] is False
