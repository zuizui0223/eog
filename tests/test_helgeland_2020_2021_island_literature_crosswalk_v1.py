"""Evidence-only schema tests: no unpublished bird or island-year data loaded."""
from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1/helgeland_2020_2021_island_literature_crosswalk_v1.json"

EIGHT={
 "Aldra","Gjerøy","Hestmannøy","Indre Kvarøy","Nesøy",
 "Myken","Selvær","Træna",
}
ELEVEN_ONLY={"Lovund","Lurøy-Onøy","Sleneset"}
FARM_EIGHT={"Aldra","Gjerøy","Hestmannøy","Indre Kvarøy","Nesøy"}
NONFARM_EIGHT={"Myken","Selvær","Træna"}


def read():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_exact_named_scope_no_unearned_numerical_join():
    x=read()
    assert x["status"]=="LITERATURE_NAME_CROSSWALK_ONLY__NUMERIC_CODES_AND_EFFORT_HOLD"
    assert x["sources"]["eight"]["source_data_published_v8_id"]==78498
    records=x["islands"]
    assert len(records)==len({p["name"] for p in records})==11
    shared={p["name"] for p in records if p["niskanen_2020_included"]}
    excluded={p["name"] for p in records if not p["niskanen_2020_included"]}
    assert shared==EIGHT
    assert excluded==ELEVEN_ONLY
    assert EIGHT.isdisjoint({"Ytre Kvarøy","Sundøy"})
    assert x["counts"]=={
        "niskanen_2020_named":8,"ranke_2021_named":11,
        "names_shared":8,"eleven_only":3,
    }


def test_paper_specific_genotyped_adult_year_windows_are_not_effort():
    x=read()
    subjects={p["name"]:p for p in x["islands"]}
    assert {name for name in EIGHT if subjects[name]["habitat"]=="farm"}==FARM_EIGHT
    assert {name for name in EIGHT if subjects[name]["habitat"]=="nonfarm"}==NONFARM_EIGHT
    for name in FARM_EIGHT:
        assert subjects[name]["niskanen_2020_genotyped_adult_years"]==[1998,2013]
    for name in {"Selvær","Træna"}:
        assert subjects[name]["niskanen_2020_genotyped_adult_years"]==[2003,2013]
    assert subjects["Myken"]["niskanen_2020_genotyped_adult_years"]==[2004,2013]
    for name in ELEVEN_ONLY:
        assert subjects[name]["niskanen_2020_genotyped_adult_years"] is None
    assert x["qualifiers"]["niskanen_year_ranges_are_genotyped_adult_sample_windows_not_survey_effort"] is True


def test_no_false_zero_or_hindsight_endpoint_claims():
    x=read()
    q=x["qualifiers"]
    assert q["published_names_directly_confirmed"] is True
    for key in (
        "source_file_2020_v8_physical_header_or_rows_verified",
        "source_file_2026_v6_numeric_site_code_crosswalk_verified",
        "source_file_2020_v8_island_code_crosswalk_verified",
        "absence_of_rows_licensed_as_sampled_zero",
        "eleven_islands_all_consistently_sampled_across_1993_2014",
        "historical_ecological_input_model_fitted",
        "independent_heldout_predictions_authorized",
        "new_ecological_effect_claim",
    ):
        assert q[key] is False, key


def test_2021_dispersal_precedent_not_misrepresented_as_new_eog_result():
    x=read()
    precedent=x["existing_published_movement_precedent"]
    assert precedent["ranked_natal_recruits_total"]==2192
    assert precedent["recorded_dispersed_natal_recruits"]==376
    assert precedent["recording_period"]==[1993,2014]
    assert "NOT new EOG" in precedent["scientific_note"]
    assert x["sources"]["eleven"]["doi"]=="10.1111/1365-2656.13580"
    assert x["sources"]["eight"]["doi"]=="10.1073/pnas.1909599117"
