"""Fabricated encounter streams only; no real sparrow biological rows."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_helgeland_next_breeding_direct_positive_v1 import inspect


def rec(ident, when, island, stage="capt"):
    return {
        "ID": ident, "date": when, "Island": island, "stage": stage,
        "Location": "synthetic SECRET locality",
        "Year": "2099", "Least_age": "888", "Least_hatchyear": "1888",
        "scriptsex": "RETROSPECTIVE",
    }


def invented():
    return [
        rec("a", "2000-06-01", "A", "nest"),
        rec("a", "2000-08-01", "A"),
        rec("a", "2001-06-02", "B", "obs"),  # first-same, next-season different
        rec("b", "2000-07-01", "A", "nest"),
        rec("b", "2000-11-01", "B"),
        rec("b", "2001-06-01", "A", "obs"),  # first-different, next-season same
        rec("c", "2001-05-01", "C", "nest"),
        rec("c", "2002-05-01", "D", "obs"),
        rec("c", "2002-05-01", "E"),  # same-day conflicting code
        rec("d", "2001-05-01", "D", "nest"),
        rec("d", "2002-09-01", "D"),  # autumn not counted as next breeding
        rec("e", "2014-05-01", "E", "nest"),  # next breeding year is 2015: shield
        rec("f", "2000-01-02", "F", "nest"),  # out-of-season birth
        rec("f", "2001-06-01", "G"),
        rec("g", "2001-06-01", "G", "nest"),
        rec("g", "2001-06-02", "H", "nest"),  # conflicting source code
        rec("h", "2002-06-01", "H", "nest"),
        rec("h", "2003-05-01", "H", "capt"),  # first-same, next-season same
    ]


def policy_for(rows):
    p = json.loads(
        (BASE / "helgeland_next_breeding_direct_positive_protocol_v1.json").read_text(
            encoding="utf-8"
        )
    )
    b = p["pre_exposed_expected"]
    b["whole_source_rows"] = len(rows)
    b["eligible_pre2015_rows"] = len(rows)
    b["pre1994_rows"] = 0
    b["post2014_rows"] = 0
    b["unique_nest_ids"] = 7
    b["ambiguous_nest_ids"] = 1
    return p


def test_earliest_raw_vs_next_breeding_season_is_distinct():
    rows = invented()
    result = inspect(rows, policy_for(rows))
    c = result["counts"]
    assert c["whole_source_rows_date_checked"] == 18
    assert c["unique_nest_source_ids"] == 7
    assert c["ambiguous_nest_source_ids"] == 1
    assert c["excluded_birth_year_2014"] == 1
    assert c["excluded_birth_outside_may_aug"] == 1
    assert c["eligible_birth_cohort_ids"] == 5
    assert c["next_season_no_direct_positive"] == 1
    assert c["next_season_direct_positive"] == 4
    assert c["next_season_same"] == 2
    assert c["next_season_different"] == 1
    assert c["next_season_ambiguous"] == 1
    assert c["first_raw_same__next_same"] == 1
    assert c["first_raw_same__next_different"] == 1
    assert c["first_raw_different__next_same"] == 1
    assert c["first_raw_ambiguous__next_ambiguous"] == 1
    assert c["first_raw_before_next_season_detection"] == 2
    assert sum(v for k, v in c.items() if k.startswith("first_raw_")
               and "__next_" in k) == 4
    assert result["next_breeding_positive_proves_recruitment"] is False
    assert result["observed_code_change_proves_dispersal"] is False
    assert result["surveyed_zero_or_detection_effort_verified"] is False
    assert "synthetic SECRET" not in json.dumps(result)
    assert '"a"' not in json.dumps(result)


def test_future_and_pre1994_fields_are_masked_before_identity():
    class Poison(dict):
        def __getitem__(self, key):
            if key != "date":
                raise AssertionError("Unpermitted future source field read: " + key)
            return super().__getitem__(key)

    rows = invented()
    poison = [
        Poison(rec("hidden1", "2015-05-01", "HIDDEN", "obs")),
        Poison(rec("hidden2", "1993-12-30", "HIDDEN", "nest")),
    ]
    p = policy_for(rows + poison)
    p["pre_exposed_expected"]["eligible_pre2015_rows"] = len(rows)
    p["pre_exposed_expected"]["pre1994_rows"] = 1
    p["pre_exposed_expected"]["post2014_rows"] = 1
    result = inspect(rows + poison, p)
    assert result["counts"]["post2014_rows_masked"] == 1
    assert result["counts"]["pre1994_rows_masked"] == 1
    assert result["counts"]["next_season_direct_positive"] == 4
    assert result["no_2015_2022_ID_Island_stage_read"] is True


def test_retrospective_ages_year_sex_and_location_cannot_affect_result():
    rows = invented()
    altered = copy.deepcopy(rows)
    for r in altered:
        for k in ("Year", "Least_age", "Least_hatchyear", "scriptsex", "Location"):
            r[k] = "INVALID_AFTER_THE_FACT"
    assert inspect(rows, policy_for(rows)) == inspect(
        altered, policy_for(altered)
    )


def test_contradictory_next_breeding_day_fails_closed_as_ambiguous():
    rows = invented()
    assert inspect(rows, policy_for(rows))["counts"]["next_season_ambiguous"] == 1


def test_absent_nextyear_detection_is_not_a_zero_or_non_recruit():
    rows = invented()
    outcome = inspect(rows, policy_for(rows))
    assert outcome["counts"]["next_season_no_direct_positive"] == 1
    assert outcome["surveyed_zero_or_detection_effort_verified"] is False


def test_original_denominator_or_semantics_cannot_be_modified():
    rows = invented()
    p = policy_for(rows)
    p["pre_exposed_expected"]["unique_nest_ids"] += 1
    with pytest.raises(ValueError, match="denominator"):
        inspect(rows, p)

    p = policy_for(rows)
    p["scientific_bounds"]["biological_dispersal_rate_estimated"] = True
    with pytest.raises(ValueError, match="Scientific inference"):
        inspect(rows, p)

    p = policy_for(rows)
    p["cohort"]["source_birth_months"] = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    with pytest.raises(ValueError, match="calendar changed"):
        inspect(rows, p)


def test_unphysical_stages_and_invalid_dates_are_rejected():
    rows = invented()
    rows[0]["stage"] = "recruit"
    with pytest.raises(ValueError, match="Invalid direct encounter"):
        inspect(rows, policy_for(rows))
    rows = invented()
    rows[0]["date"] = "bad-date"
    with pytest.raises(ValueError, match="date"):
        inspect(rows, policy_for(rows))


def test_real_protocol_is_post_exposure_without_independent_forecast():
    p = json.loads(
        (BASE / "helgeland_next_breeding_direct_positive_protocol_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert p["pre_exposed_expected"]["first_different"] == 223
    assert p["pre_exposed_expected"]["any_later_different"] == 451
    assert p["pre_exposed_expected"]["first_same_later_different"] == 228
    assert p["source"]["public_at_forecast_cutoff_2014"] is False
    assert p["cohort"]["birth_year_last_included"] == 2013
    assert p["scientific_bounds"]["independent_heldout_ecological_model_scored"] is False
    source = (
        ROOT / "scripts/audit_helgeland_next_breeding_direct_positive_v1.py"
    ).read_text(encoding="utf-8")
    assert source.index('stamp = strict_observed_date(row["date"])') < source.index(
        'ident = (row["ID"] or "").strip()'
    )
    for banned in ('row["Year"]', 'row["Least_age"]', 'row["Location"]',
                   "import pandas", "read_csv(", "urllib"):
        assert banned not in source
