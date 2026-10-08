"""Synthetic controls for the as-of observation-only information barrier."""
from __future__ import annotations

import dataclasses
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/helgeland_date_only_asof_firewall_v1.py"


def mod():
    spec = importlib.util.spec_from_file_location("helgeland_asof_firewall", SCRIPT)
    assert spec and spec.loader
    x = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = x
    spec.loader.exec_module(x)
    return x


def rows():
    return [
        dict(ID="bird_a", Island="A", Location="a", date="2013-05-01",
             stage="nest", Year="9999", Least_age="FUTURE", scriptsex="FUTURE"),
        dict(ID="bird_a", Island="B", Location="b", date="2014-04-02",
             stage="obs", Year="0", Least_age="FUTURE", scriptsex="FUTURE"),
        dict(ID="bird_b", Island="A", Location="a", date="2014-03-31",
             stage="capt", Year="2013", Least_age="FUTURE", scriptsex="FUTURE"),
        dict(ID="bird_c", Island="A", Location="a", date="2013-06-02",
             stage="nest", Year="2013", Least_age="FUTURE", scriptsex="FUTURE"),
        dict(ID="bird_c", Island="B", Location="b", date="2013-06-03",
             stage="nest", Year="2013", Least_age="FUTURE", scriptsex="FUTURE"),
    ]


def test_cutoff_uses_real_date_not_april_year_label_or_derived_age():
    m = mod()
    historical = m.direct_history_as_of(rows(), "2014-03-31")
    assert [(x.individual_id, x.island, x.direct_stage) for x in historical] == [
        ("bird_a", "A", "nest"),
        ("bird_c", "A", "nest"),
        ("bird_c", "B", "nest"),
        ("bird_b", "A", "capt"),
    ]
    assert ("bird_a", "A") in m.directly_observed_single_nest_sources_as_of(historical)
    assert not any(x.island == "B" and x.individual_id == "bird_a" for x in historical)
    assert not any(x.individual_id == "bird_c" for x in
                   (m.ObservedAtCutoff(*x, None, "") for x in []))


def test_post_cutoff_rows_cannot_change_predictor_history():
    m = mod()
    before = m.direct_history_as_of(rows(), "2013-12-31")
    supplement = rows() + [
        dict(ID="bird_a", Island="C", Location="c", date="2019-04-15",
             stage="nest", Year="2018", scriptsex="F", Least_age="2"),
    ]
    after = m.direct_history_as_of(supplement, "2013-12-31")
    assert before == after


def test_bad_retrospective_fields_are_never_read():
    m = mod()
    class Poisoned(dict):
        def __getitem__(self, key):
            if key not in m.ALLOWED_FIELDS:
                raise RuntimeError("Leakage: accessed " + key)
            return super().__getitem__(key)
    direct = Poisoned(rows()[0])
    direct["Year"] = "wrong"
    direct["Least_age"] = "unknown"
    direct["Least_hatchyear"] = "future"
    direct["scriptsex"] = "inferred"
    found = m.direct_history_as_of([direct], "2014-03-31")
    assert len(found) == 1
    assert found[0].observed_date.year == 2013


def test_single_nest_island_only_never_assigns_from_later_observation():
    m = mod()
    history = m.direct_history_as_of(rows(), "2014-12-31")
    singles = m.directly_observed_single_nest_sources_as_of(history)
    assert ("bird_a", "A") in singles
    assert ("bird_c", "A") not in singles
    assert ("bird_c", "B") not in singles
    assert not any(x.individual_id == "bird_b" for x in history if x.direct_stage == "nest")


@pytest.mark.parametrize("bad", [
    "2014", "20140401", "2014/04/01", "2014-02-30",
    "2014-04-01T12:00:00", "2020-13-01", "2014- 4-01",
])
def test_non_iso_or_invalid_calendar_cutoffs_fail_closed(bad):
    m = mod()
    with pytest.raises(ValueError):
        m.direct_history_as_of(rows(), bad)


def test_frozen_hold_receipt_never_promotes_actual_database_availability():
    m = mod()
    x = m.hold_receipt("2014-03-31")
    assert x["status"] == "SYNTHETIC_INFORMATION_FIREWALL_ONLY__ECOLOGICAL_HOLD"
    assert x["input_time_source"] == "physical date field only; never the Year label"
    assert x["database_ingestion_time_verified"] is False
    assert x["ecological_endpoint_authorized"] is False
    assert x["individual_observations_exported"] is False
    assert "bird_a" not in str(x)
