"""Audit v23 standalone readout rescue versus exact two-family synergy."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "validation" / "eog_virtual_world_ecology_synthesis_v1"
RECEIPT = DIR / "v23_readout_synergy_decomposition_v1.json"
PARENT = DIR / "matched_readout_crossover_v1.json"
SCRIPT = ROOT / "scripts" / "audit_eog_v23_readout_synergy_v1.py"


def module():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        spec = importlib.util.spec_from_file_location("v23_synergy_audit", SCRIPT)
        assert spec and spec.loader
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
        return a
    finally:
        sys.path.pop(0)


def test_frozen_standalone_and_joint_rescue_reconcile_with_prior_v23_crossover():
    original = json.loads(PARENT.read_text(encoding="utf-8"))
    report = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert report["status"] == "POST_RESULT_DESCRIPTIVE_NOT_PREREGISTERED"
    assert report["original_v23_sha256"] == original["original_artifact_zip_sha256"]["v23"]
    assert report["original_v23_fingerprint"] == original["original_result_fingerprints"]["v23"]
    assert report["panel_count"] == 384
    assert report["design_count"] == 768
    assert report["true_mixed_library_synergy_designs"] == 18

    total_mixed = 0
    for layout, expected in (("clustered", (46,17,90,93,138)),
                             ("dispersed", (35,1,0,304,44))):
        v = report["layouts"][layout]
        frequencies = v["truth_table"]
        assert tuple(frequencies[k] for k in ("000","001","011","101","111")) == expected
        assert sum(frequencies.values()) == 384
        assert v["occupancy_unresolved"] == frequencies["000"] + frequencies["001"] + frequencies["011"]
        assert v["provenance_unresolved"] == frequencies["000"] + frequencies["001"] + frequencies["101"]
        assert v["provenance_alone_rescues_occupancy_unresolved"] == frequencies["011"]
        assert v["mixed_only_rescues_occupancy_unresolved"] == frequencies["001"]
        assert v["total_rescued_after_adding_provenance"] == frequencies["001"] + frequencies["011"]
        assert v["newly_identified_by_occupancy_alone_after_provenance"] == frequencies["101"]
        assert v["newly_identified_by_mixed_information_after_provenance"] == frequencies["001"]
        occ_identified = frequencies["101"] + frequencies["111"]
        prov_identified = frequencies["011"] + frequencies["111"]
        combined_identified = 384-frequencies["000"]
        for target, value in [
            ("occupancy_only", occ_identified),
            ("provenance_only", prov_identified),
            ("combined", combined_identified),
        ]:
            assert original["identification_by_readout"][target][layout] == value
        assert math.isclose(
            v["fraction_unresolved_rescued_by_both_only"],
            frequencies["001"] / v["occupancy_unresolved"]
        )
        assert math.isclose(
            v["fraction_unresolved_rescued_by_provenance_alone"],
            frequencies["011"] / v["occupancy_unresolved"]
        )
        assert math.isclose(
            v["fraction_unresolved_rescued_in_total"],
            (frequencies["011"] + frequencies["001"]) / v["occupancy_unresolved"]
        )
        total_mixed += frequencies["001"]
    assert total_mixed == 18
    assert original["identification_by_readout"]["combined"]["clustered"] == 338
    assert original["identification_by_readout"]["combined"]["dispersed"] == 349


def record(occ, prov, combined, combined_actions):
    def full(value, actions):
        return {
            "identified": value,
            "minimum_action_ids": actions if value else None,
            "minimum_size": len(actions) if value else None,
        }
    return {
        "plans": {
            "occupancy_only": {"full_history": full(occ, ["O_t4"])},
            "provenance_only": {"full_history": full(prov, ["P_r2c1"])},
            "combined": {"full_history": full(combined, combined_actions)},
        }
    }


def test_mixed_only_requires_both_readout_families_not_just_two_actions():
    audit = module()
    assert audit.classify_record(record(False,False,True,["O_t4","P_r2c1"])) == ("001",True)
    assert audit.classify_record(record(False,True,True,["P_r2c1"])) == ("011",False)
    assert audit.classify_record(record(True,False,True,["O_t4"])) == ("101",False)
    assert audit.classify_record(record(False,False,False,[])) == ("000",False)

    with pytest.raises(ValueError,match="two-family witness"):
        audit.classify_record(record(False,False,True,["P_r2c1","P_r2c2"]))
    with pytest.raises(ValueError,match="two-family witness"):
        audit.classify_record(record(False,False,True,["O_t4"]))
    with pytest.raises(ValueError,match="Combining libraries"):
        audit.classify_record(record(True,False,False,[]))


def test_claim_scope_does_not_substitute_same_layout_for_independent_ecological_data():
    report = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert "not 768 independent biological samples" in " ".join(report["boundaries"])
    assert any("different information payload" in s for s in report["boundaries"])
    assert any("not a prospective ecological mechanism test" in s for s in report["boundaries"])
