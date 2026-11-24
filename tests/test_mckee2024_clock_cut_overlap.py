"""Offline regressions for exact T0/T1 clock-cut masks, no 2h access."""
from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys

import pytest


HERE = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
PROTOCOL = HERE / "post_stop_clock_cut_overlap_protocol_v1.json"
RECEIPT = HERE / "post_stop_clock_cut_overlap_receipt_v1.json"
SCRIPT = HERE / "replay_post_stop_clock_cut_overlap.py"

sys.path.insert(0, str(HERE))
try:
    code = runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(HERE))


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_frozen_source_mask_alignment_and_precomparison_commit():
    p, r = _json(PROTOCOL), _json(RECEIPT)
    assert p["schema"] == "eog.mckee2024.post_stop_clock_cut_location_overlap.v1"
    assert p["status"] == "FROZEN_BEFORE_CROSS_SCENARIO_CUT_LOCATION_COMPARISON"
    assert r["protocol_commit_before_comparison"] == (
        "d74eb7360a603fae790af5df9b8b95162cc2e7be"
    )
    assert p["source"]["sha256"] == code["SHA256"] == r["source_sha256"]
    assert r["source_sha256_verified"]
    assert r["source_groups"] == 421
    assert r["consecutive_link_count"] == 28532
    assert code["_check_protocol"]()["schema"] == p["schema"]


def test_two_totals_hid_only_one_extra_t1_break():
    r = _json(RECEIPT)
    x = r["link_cut_retention_table"]
    assert x == {
        "cut_both": 857,
        "cut_T0_only": 0,
        "cut_T1_only": 1,
        "retained_both": 27674,
    }
    assert sum(x.values()) == 28532
    assert r["T0_full_day_coherent_cuts"] == x["cut_both"] + x["cut_T0_only"] == 857
    assert r["T1_near_midnight_coherent_and_optimistic_cuts"] == (
        x["cut_both"] + x["cut_T1_only"]
    ) == 858
    assert r["cut_jaccard"] == pytest.approx(857/858)
    assert r["retained_link_jaccard"] == pytest.approx(27674/27675)
    assert r["groups_with_any_cut_disagreement"] == 1
    assert r["groups_with_T0_only_cut"] == 0
    assert r["groups_with_T1_only_cut"] == 1
    assert r["T0_only_cuts_by_T0_pair_status"] == {}
    assert r["T1_only_cuts_by_T0_pair_status"] == {"contingent": 1}


def test_pure_cut_set_table_counts_identical_and_divergent_masks():
    f = code["compare_cut_sets"]
    assert f((1, 2), (1, 2), 4) == {
        "cut_both": 2, "cut_T0_only": 0,
        "cut_T1_only": 0, "retained_both": 2,
    }
    assert f((1, 2), (2, 4), 4) == {
        "cut_both": 1, "cut_T0_only": 1,
        "cut_T1_only": 1, "retained_both": 1,
    }
    assert f((), (), 5) == {
        "cut_both": 0, "cut_T0_only": 0,
        "cut_T1_only": 0, "retained_both": 5,
    }


def test_cut_set_out_of_range_fail_closed():
    f = code["compare_cut_sets"]
    for a, b, length in [
        ((0,), (), 3),
        ((4,), (), 3),
        ((1,), (-1,), 3),
        ((True,), (), 3),
    ]:
        with pytest.raises(ValueError, match="Cut index"):
            f(a, b, length)
    for length in (-1, True, 1.5):
        with pytest.raises(ValueError, match="nonnegative integer"):
            f((), (), length)


def test_input_cut_status_monotonicity_and_scientific_stop():
    r = _json(RECEIPT)
    p = _json(PROTOCOL)
    assert r["dense_2h_GPS_accessed"] is False
    assert r["dense_2h_GPS_accessed"] is False
    assert r["actual_BBMM_or_movement_path_fitted"] is False
    assert r["author_exact_date_only_clock_verified"] is False
    assert r["source_CRS_author_verified"] is False
    assert r["SHP_geometry_or_coordinates_accessed"] is False
    assert r["individual_IDs_exact_times_or_links_exported"] is False
    assert r["EOG_predictive_score_computed"] is False
    assert r["EOG_WF_scored_count_unchanged"] == 3
    assert p["heldout_2h_access"] is False
