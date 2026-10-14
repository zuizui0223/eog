"""Adversarial, fabricated-only tests for original Island code 0/33 robustness."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))

from audit_helgeland_island_0_33_sensitivity_v1 import analyze, validate_contract


def fake(ident: str, stamp: str, island: str, stage: str = "capt") -> dict:
    return {
        "date": stamp, "ID": ident, "Island": island, "stage": stage,
        "Location": "FAKE_SENSITIVE_LOCATION",
        "Year": "FUTURE_YEAR", "Least_age": "FUTURE_AGE",
        "Least_hatchyear": "FUTURE_HATCH", "scriptsex": "RETROSPECTIVE",
    }


def artificial() -> list[dict]:
    return [
        # A: clean and discordant
        fake("alpha", "2000-06-01", "A", "nest"),
        fake("alpha", "2000-07-01", "A"),
        fake("alpha", "2001-06-01", "B", "obs"),
        # B: 0 as nest source; must be excluded before target
        fake("beta", "2000-06-01", "0", "nest"),
        fake("beta", "2000-07-01", "X"),
        fake("beta", "2001-06-01", "X", "obs"),
        # C: 33 in first raw positive, next is source
        fake("charlie", "2000-06-01", "C", "nest"),
        fake("charlie", "2000-07-01", "33"),
        fake("charlie", "2001-06-01", "C", "obs"),
        # D: 33 in next target positive
        fake("delta", "2000-06-01", "D", "nest"),
        fake("delta", "2000-07-01", "D"),
        fake("delta", "2001-06-01", "33", "obs"),
        # E: only after endpoint, primary clear but retrospective strict flags
        fake("echo", "2000-06-01", "E", "nest"),
        fake("echo", "2000-07-01", "E"),
        fake("echo", "2001-06-01", "E", "obs"),
        fake("echo", "2002-07-01", "0"),
        # F: entirely clean
        fake("foxtrot", "2000-06-01", "F", "nest"),
        fake("foxtrot", "2000-07-01", "F"),
        fake("foxtrot", "2001-06-01", "F", "obs"),
        # G: ambiguous first-next same date; clean
        fake("golf", "2001-06-01", "G", "nest"),
        fake("golf", "2002-06-01", "G", "obs"),
        fake("golf", "2002-06-01", "H", "obs"),
        # H: no next target positive
        fake("hotel", "2001-06-01", "H", "nest"),
        # I: 2014 nest excluded from source cohort
        fake("india", "2014-06-01", "I", "nest"),
        # J: January nest excluded from source cohort
        fake("juliet", "2001-01-01", "J", "nest"),
        # K: ambiguous all-time nest codes
        fake("kilo", "2001-06-01", "K", "nest"),
        fake("kilo", "2001-06-02", "Q", "nest"),
        # L: source 33 but no next target observation
        fake("lima", "2001-06-01", "33", "nest"),
        # M: no nest at all, but an excluded code occurs
        fake("mike", "2001-06-01", "0", "capt"),
    ]


def contract() -> dict:
    return json.loads((
        BASE / "helgeland_island_0_33_sensitivity_protocol_v1.json"
    ).read_text(encoding="utf-8"))


def previous(rows: list[dict]) -> dict:
    values = {
        "whole_source_rows_date_checked": len(rows),
        "pre1994_rows_masked": 0,
        "post2014_rows_masked": 0,
        "eligible_pre2015_rows": len(rows),
        "unique_nest_source_ids": 11,
        "ambiguous_nest_source_ids": 1,
        "eligible_birth_cohort_ids": 9,
        "next_season_direct_positive": 7,
    }
    for a in ("same", "different", "ambiguous"):
        for b in ("same", "different", "ambiguous"):
            values[f"first_raw_{a}__next_{b}"] = 0
    values.update({
        "first_raw_same__next_same": 2,
        "first_raw_same__next_different": 2,
        "first_raw_different__next_same": 1,
        "first_raw_different__next_different": 1,
        "first_raw_ambiguous__next_ambiguous": 1,
    })
    return values


def test_complete_paired_matrix_and_two_separate_sensitivity_universes():
    rows = artificial()
    result = analyze(rows, contract(), previous(rows))
    c = result["counts"]
    assert c["raw_code_0_rows_pre2015"] == 3
    assert c["raw_code_33_rows_pre2015"] == 3
    assert c["distinct_ids_with_excluded_codes_pre2015"] == 6
    assert c["eligible_cohort_source_code_excluded"] == 2
    assert c["paired_source_code_excluded"] == 1
    assert c["paired_first_raw_day_contains_excluded"] == 1
    assert c["paired_next_day_contains_excluded"] == 1
    assert c["paired_pre_target_excluded"] == 3
    assert c["paired_ever_excluded"] == 4
    assert c["paired_later_only_excluded"] == 1
    assert c["paired_pre_target_clean"] == 4
    assert c["paired_entire_history_clean"] == 3
    assert c["paired_strict_pre_target_discordant"] == 1
    assert c["paired_strict_entire_history_discordant"] == 1
    assert result["matrices"]["strict_pre_target"] == {
        **{
            f"first_raw_{a}__next_{b}": 0
            for a in ("same", "different", "ambiguous")
            for b in ("same", "different", "ambiguous")
        },
        "first_raw_same__next_same": 2,
        "first_raw_same__next_different": 1,
        "first_raw_ambiguous__next_ambiguous": 1,
    }
    assert result["matrices"]["strict_entire_history"][
        "first_raw_same__next_same"
    ] == 1
    assert result["origin_0_33_rows_not_reclassified_or_removed"] is True
    assert result["raw_individual_or_island_records_exported"] is False
    output = json.dumps(result)
    assert "FAKE_SENSITIVE_LOCATION" not in output
    for forbidden in ('"alpha"', '"beta"', '"charlie"', '"echo"'):
        assert forbidden not in output


def test_out_of_range_individual_fields_cannot_be_read():
    class Poison(dict):
        def __getitem__(self, key):
            if key != "date":
                raise AssertionError("Out-of-range identity/site read: " + key)
            return super().__getitem__(key)

    rows = artificial()
    poisoned = rows + [
        Poison(fake("hidden", "2015-08-01", "0", "obs")),
        Poison(fake("ancient", "1993-06-01", "33", "nest")),
    ]
    ref = previous(poisoned)
    ref["eligible_pre2015_rows"] = len(rows)
    ref["pre1994_rows_masked"] = 1
    ref["post2014_rows_masked"] = 1
    result = analyze(poisoned, contract(), ref)
    assert result["counts"]["raw_code_0_rows_pre2015"] == 3
    assert result["counts"]["raw_code_33_rows_pre2015"] == 3
    assert result["counts"]["paired_pre_target_clean"] == 4
    assert result["post2014_ID_Island_stage_inspected"] is False


def test_after_target_code_is_not_used_to_filter_primary():
    rows = artificial()
    c = analyze(rows, contract(), previous(rows))["counts"]
    assert c["paired_later_only_excluded"] == 1
    assert c["paired_pre_target_clean"] == 4
    assert c["paired_entire_history_clean"] == 3


def test_same_day_invalid_and_valid_codes_triggers_flag_without_reclassifying():
    rows = artificial()
    rows.append(fake("golf", "2002-06-01", "0", "obs"))
    ref = previous(rows)
    result = analyze(rows, contract(), ref)
    assert result["counts"]["paired_next_day_contains_excluded"] == 2
    assert result["counts"]["paired_pre_target_clean"] == 3
    assert result["matrices"]["baseline_exact"]["first_raw_ambiguous__next_ambiguous"] == 1


def test_hindsight_fields_cannot_change_counts():
    rows = artificial()
    changed = copy.deepcopy(rows)
    for row in changed:
        for col in ("Location", "Year", "Least_age", "Least_hatchyear", "scriptsex"):
            row[col] = "AFTER_THE_FACT_UNAUTHORIZED"
    assert analyze(rows, contract(), previous(rows)) == analyze(
        changed, contract(), previous(changed)
    )


def test_original_baseline_matrix_drift_fails_closed():
    rows = artificial()
    earlier = previous(rows)
    earlier["first_raw_same__next_different"] += 1
    with pytest.raises(ValueError, match="matrix drifted"):
        analyze(rows, contract(), earlier)


def test_original_source_baseline_row_count_drift_fails_closed():
    rows = artificial()
    earlier = previous(rows)
    earlier["eligible_pre2015_rows"] -= 1
    with pytest.raises(ValueError, match="baseline count drifted"):
        analyze(rows, contract(), earlier)


def test_contract_and_allowed_claims_are_immutable():
    rows = artificial()
    cfg = contract()
    cfg["author_exclusion"]["excluded_literal_island_codes"] = ["0", "34"]
    with pytest.raises(ValueError, match="literal 0 and 33"):
        analyze(rows, cfg, previous(rows))
    cfg = contract()
    cfg["methods"]["event_exclusion_not_reclassification"] = False
    with pytest.raises(ValueError, match="post-hoc refit"):
        analyze(rows, cfg, previous(rows))
    cfg = contract()
    cfg["scientific_bounds"]["independent_heldout_EOG_forecast_scored"] = True
    with pytest.raises(ValueError, match="ecological claim"):
        analyze(rows, cfg, previous(rows))


def test_no_year_age_or_site_name_access_and_pre_exposure_contract():
    cfg = contract()
    validate_contract(cfg)
    assert cfg["prior"]["paired_direct_positive_ids"] == 1313
    assert cfg["prior"]["paired_discordance"] == 125
    assert cfg["prior"]["main_commit"] == "4aee2041644ad3159ac09c0aabe99e396a642c2f"
    assert cfg["status"] == "FROZEN_POST_PR646_EXPOSURE__BEFORE_0_33_REAL_SOURCE_SENSITIVITY"
    source = (ROOT / "scripts/audit_helgeland_island_0_33_sensitivity_v1.py").read_text()
    assert source.index('stamp = strict_observed_date(row["date"])') < source.index(
        'ident = (row["ID"] or "").strip()'
    )
    for forbidden in (
        'row["Year"]', 'row["Least_age"]', 'row["Location"]',
        "import pandas", "read_csv(", "urllib",
    ):
        assert forbidden not in source
