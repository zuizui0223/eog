"""Fabricated cohort only: code-33 farm island retained, code-0 excluded."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0, str(ROOT / "scripts"))

from audit_helgeland_11island_habitat_paired_v1 import (
    _validate_protocol, inspect, matrix_zero, resolve_site_habitats,
)


def fabricated_row(ident, date, site, stage="capt"):
    return {
        "date": date, "ID": ident, "Island": site, "stage": stage,
        "Location": "UNRELIABLE_FUTURE_LABEL",
        "Year": "2099", "Least_age": "FUTURE", "scriptsex": "RETROSPECTIVE",
    }


def fabricated_events():
    r = fabricated_row
    return [
        r("a", "2000-06-01", "20", "nest"),
        r("a", "2000-07-01", "20"),
        r("a", "2001-06-01", "23", "obs"),  # farm -> nonfarm, first same
        r("b", "2000-06-01", "22", "nest"),
        r("b", "2000-07-01", "22"),
        r("b", "2001-06-01", "23"),  # nonfarm -> nonfarm, first same
        r("c", "2000-06-01", "33", "nest"),
        r("c", "2000-07-01", "33"),
        r("c", "2001-06-01", "33", "obs"),  # Lurøy-Onøy retained
        r("d", "2000-06-01", "33", "nest"),
        r("d", "2000-07-01", "33"),
        r("d", "2001-06-01", "22"),  # Lurøy-Onøy -> nonfarm
        r("e", "2000-06-01", "20", "nest"),
        r("e", "2000-07-01", "0"),   # other Helgeland before target
        r("e", "2001-06-01", "20"),
        r("f", "2000-06-01", "23", "nest"),
        r("f", "2000-07-01", "23"),
        r("f", "2001-06-01", "23"),
        r("f", "2002-07-01", "0"),  # only after endpoint
        r("g", "2000-06-01", "34", "nest"),
        r("g", "2000-07-01", "20"),
        r("g", "2001-06-01", "34"),  # first changed, next same
        r("h", "2000-06-01", "20", "nest"),
        r("h", "2000-07-01", "20"),
        r("h", "2001-06-01", "0"),  # target outside 11 named
        r("i", "2000-06-01", "0", "nest"),
        r("i", "2000-07-01", "0"),
        r("i", "2001-06-01", "20"),  # origin outside 11 named
        r("j", "2014-06-01", "28", "nest"),  # cannot see 2015 at cutoff
        r("k", "2000-06-01", "38", "nest"),  # no second-year positive
        r("l", "2000-06-01", "27", "nest"),
        r("l", "2000-06-02", "22", "nest"),  # ambiguous source
        r("m", "2000-06-01", "35", "nest"),
        r("m", "2000-07-01", "35"),
        r("m", "2001-06-01", "35"),
        r("n", "2000-06-01", "20", "nest"),
        r("n", "2000-07-01", "20"),
        r("n", "2001-04-01", "33"),  # 33 before endpoint; keep named 11
        r("n", "2001-06-01", "35"),
        r("o", "2000-06-01", "24", "nest"),
        r("o", "2000-07-01", "24"),
        r("o", "2001-06-01", "34"),
        r("o", "2002-07-01", "33"),  # no effect on pretarget 0+33 screen
        r("p", "2000-06-01", "20", "nest"),
        r("p", "2000-07-01", "20"),
        r("p", "2001-06-01", "24"),
        r("p", "2002-07-01", "0"),  # retain pretarget, not all-history
    ]


def protocol():
    return json.loads((BASE / "helgeland_11island_habitat_paired_protocol_v1.json").read_text())


def baseline(rows):
    values = {
        "whole_source_rows_date_checked": len(rows),
        "pre1994_rows_masked": 0,
        "post2014_rows_masked": 0,
        "eligible_pre2015_rows": len(rows),
        "unique_nest_source_ids": 15,
        "ambiguous_nest_source_ids": 1,
        "eligible_birth_cohort_ids": 14,
        "next_season_direct_positive": 13,
    }
    values.update(matrix_zero())
    values["first_raw_same__next_same"] = 3
    values["first_raw_same__next_different"] = 8
    values["first_raw_different__next_same"] = 2
    return values


def evaluate(rows=None, values=None):
    rows = fabricated_events() if rows is None else rows
    values = baseline(rows) if values is None else values
    return inspect(rows, protocol(), values, resolve_site_habitats(protocol()), actual_source=False)


def test_source_internal_11_names_and_habitat_list_match_published_roster():
    sites = resolve_site_habitats(protocol())
    assert len(sites) == 11
    assert sites["33"] == {"name": "Lurøy-Onøy", "habitat": "farm"}
    assert "0" not in sites
    assert sum(x["habitat"] == "farm" for x in sites.values()) == 6
    assert sum(x["habitat"] == "nonfarm" for x in sites.values()) == 5


def test_pretarget_11_island_restores_33_and_preserves_0_33_nested_control():
    result = evaluate()
    c = result["counts"]
    m = result["paired_matrices"]
    assert c["unique_nest_source_ids"] == 15
    assert c["ambiguous_nest_source_ids"] == 1
    assert c["paired_next_year_positive"] == 13
    assert c["code_0_direct_rows"] == 6
    assert c["code_33_direct_rows"] == 7
    assert c["paired_0_before_or_at_target"] == 3
    assert c["paired_33_before_or_at_target"] == 3
    assert c["paired_0_and_33_before_or_at_target"] == 0
    assert c["paired_0_anytime"] == 5
    assert c["paired_0_later_only"] == 2
    assert c["named_11_primary_positive"] == 10
    assert c["named_11_full_history_positive"] == 8
    assert c["model_0_33_primary_positive"] == 7
    assert c["named_11_primary_discordant"] == 7
    assert c["named_11_full_history_discordant"] == 6
    assert c["model_0_33_primary_discordant"] == 5
    assert m["original_all"]["first_raw_same__next_different"] == 8
    assert m["named_11_0_only_pretarget"]["first_raw_same__next_different"] == 6
    assert m["named_11_0_only_pretarget"]["first_raw_different__next_same"] == 1
    assert m["model_0_and_33_pretarget"]["first_raw_same__next_different"] == 4
    assert m["model_0_and_33_pretarget"]["first_raw_different__next_same"] == 1
    assert c["named_11_primary_33_origin"] == 2
    assert c["named_11_primary_33_next"] == 1
    assert c["named_11_primary_33_in_origin_or_target"] == 2
    assert result["original_source_SHA256_and_header_verified"] is False
    assert result["breeding_recruitment_dispersal_or_colonization_inferred"] is False
    assert "UNRELIABLE_FUTURE_LABEL" not in json.dumps(result)
    assert '"a"' not in json.dumps(result)


def test_habitat_cross_type_is_positive_record_only_and_reconciles():
    r = evaluate()
    assert r["habitat_next_positive"] == {
        "farm_to_farm": 1,
        "farm_to_nonfarm": 4,
        "nonfarm_to_farm": 0,
        "nonfarm_to_nonfarm": 5,
    }
    assert r["habitat_different_code_positive"] == {
        "farm_to_farm": 0,
        "farm_to_nonfarm": 4,
        "nonfarm_to_farm": 0,
        "nonfarm_to_nonfarm": 2,
    }
    assert r["first_same_next_different_by_origin_habitat"] == {
        "farm": 4, "nonfarm": 2,
    }
    assert r["counts"]["named_11_primary_next_same_codes"] == 4
    assert r["counts"]["named_11_primary_next_different_codes"] == 6
    assert len(r["per_origin_named_island_positive_counts"]) == 11
    assert sum(row["paired_positive"] for row in r["per_origin_named_island_positive_counts"]) == 10


def test_future_poison_outcome_identity_and_full_source_leakage():
    class Poison(dict):
        def __getitem__(self, k):
            if k != "date":
                raise AssertionError("Future field accessed " + str(k))
            return super().__getitem__(k)
    rows = fabricated_events() + [
        Poison(fabricated_row("sensitive", "2015-06-01", "0")),
        Poison(fabricated_row("older", "1993-12-31", "33")),
    ]
    values = baseline(rows)
    values["eligible_pre2015_rows"] = len(rows) - 2
    values["pre1994_rows_masked"] = 1
    values["post2014_rows_masked"] = 1
    result = evaluate(rows, values)
    assert result["counts"]["post2014_rows_masked"] == 1
    assert result["counts"]["pre1994_rows_masked"] == 1
    assert result["counts"]["paired_next_year_positive"] == 13
    assert result["post2014_bird_identity_or_destination_inspected"] is False


def test_hindsight_derived_fields_never_affect_any_public_result():
    rows = fabricated_events()
    changed = copy.deepcopy(rows)
    for row in changed:
        for col in ("Location", "Year", "Least_age", "scriptsex"):
            row[col] = "UNAUTHORIZED_HINDSIGHT"
    assert evaluate(rows) == evaluate(changed)


def test_modified_prior_paired_matrix_fails_closed():
    rows = fabricated_events()
    b = baseline(rows)
    b["first_raw_same__next_different"] += 1
    with pytest.raises(ValueError, match="original matrix drifted"):
        evaluate(rows, b)


def test_literal_code_33_cannot_be_removed_from_study_roster():
    p = protocol()
    p["study_roster"]["allowed_codes"].remove("33")
    with pytest.raises(ValueError, match="roster changed"):
        inspect(fabricated_events(), p, baseline(fabricated_events()), resolve_site_habitats(protocol()), actual_source=False)


def test_broadening_to_hindsight_or_true_biological_claims_fails():
    p = protocol()
    p["scientific_boundaries"]["no_dispersal_rate_or_true_recruitment"] = False
    with pytest.raises(ValueError, match="scientific claim"):
        inspect(fabricated_events(), p, baseline(fabricated_events()), resolve_site_habitats(protocol()), actual_source=False)
    p = protocol()
    p["fixed_paired_endpoint"]["primary_11_island"] = "drop both code 0 and 33"
    with pytest.raises(ValueError, match="paired-classification rules"):
        inspect(fabricated_events(), p, baseline(fabricated_events()), resolve_site_habitats(protocol()), actual_source=False)


def test_same_day_multiple_target_code_cannot_be_forced_into_named_habitat():
    rows = fabricated_events()
    rows.append(fabricated_row("a", "2001-06-01", "24"))
    counts = baseline(rows)
    counts["first_raw_same__next_different"] -= 1
    counts["first_raw_same__next_ambiguous"] += 1
    with pytest.raises(ValueError, match="multiply observed"):
        evaluate(rows, counts)


def test_real_frozen_prior_1313_125_and_code_33_remains_named_population():
    p = protocol()
    _validate_protocol(p)
    c = p["previous_exposed_counts"]
    assert c["paired_IDs"] == 1313
    assert c["paired_original_same_different"] == 124
    assert c["model_0_33_pretarget_clean_n"] == 1260
    assert p["source"]["source_public_since_2026_not_2014"] is True
    assert p["study_roster"]["retained_code"] == "33"
    source = (ROOT / "scripts/audit_helgeland_11island_habitat_paired_v1.py").read_text()
    assert source.index('stamp = strict_observed_date(row["date"])') < source.index(
        'ident = (row["ID"] or "").strip()'
    )
    for banned in ('row["Year"]', 'row["Location"]', 'row["Least_age"]',
                   'row["scriptsex"]', 'read_csv(', "urllib"):
        assert banned not in source


def test_actual_source_independently_reviewed_full_receipt_guard():
    frozen = json.loads((
        BASE / "helgeland_11island_habitat_paired_observed_frozen_v1.json"
    ).read_text(encoding="utf-8"))
    assert frozen["schema"] == (
        "eog.helgeland.11island_positive_habitat_paired.frozen_source_receipt.v1"
    )
    assert frozen["protocol_freeze_commit"] == (
        "fd18c40e521e14c982164e3b132ff81320c4b8be"
    )
    a = frozen["authority"]
    assert a["github_actions_run_id"] == 39208937959
    assert a["github_actions_artifact_id"] == 12166747729
    assert a["artifact_zip_sha256"] == (
        "c9c6c9fcf4d11d4f007227fd9c265c7d15f06cfc1c197d30a0763302f03744f8"
    )
    r = frozen["receipt"]
    c = r["counts"]
    assert c["paired_next_year_positive"] == 1313
    assert c["paired_0_before_or_at_target"] == 41
    assert c["paired_33_before_or_at_target"] == 14
    assert c["paired_0_and_33_before_or_at_target"] == 2
    assert c["named_11_primary_positive"] == 1272
    assert c["named_11_primary_discordant"] == 118
    assert c["named_11_full_history_positive"] == 1268
    assert c["named_11_full_history_discordant"] == 118
    assert c["model_0_33_primary_positive"] == 1260
    assert c["model_0_33_primary_discordant"] == 112
    assert c["named_11_primary_33_in_origin_or_target"] == 12
    assert c["named_11_primary_next_different_codes"] == 219
    assert r["paired_matrices"]["named_11_0_only_pretarget"][
        "first_raw_same__next_different"
    ] == 117
    assert r["paired_matrices"]["named_11_0_only_pretarget"][
        "first_raw_different__next_same"
    ] == 1
    assert r["habitat_different_code_positive"] == {
        "farm_to_farm": 62,
        "farm_to_nonfarm": 7,
        "nonfarm_to_farm": 21,
        "nonfarm_to_nonfarm": 129,
    }
    assert r["habitat_next_positive"] == {
        "farm_to_farm": 806,
        "farm_to_nonfarm": 7,
        "nonfarm_to_farm": 21,
        "nonfarm_to_nonfarm": 438,
    }
    assert r["first_same_next_different_by_origin_habitat"] == {
        "farm": 39, "nonfarm": 78
    }
    assert r["original_PR646_and_PR647_receipts_exactly_reconciled"] is True
    assert r["original_source_SHA256_and_header_verified"] is True
    assert r["independent_EOG_forecast_scored"] is False
    assert r["breeding_recruitment_dispersal_or_colonization_inferred"] is False
