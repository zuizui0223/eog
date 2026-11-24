"""Audit the source-frozen McKee 12h 2-24-record temporal composition receipts.

No raw GPS archive is checked into GitHub. Synthetic finite-interval
brute-force is an independent oracle for the forward interval algorithm.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path
import random
import runpy
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
SCRIPT = ROOT / "replay_post_stop_global_time_windows.py"
PROTO = ROOT / "post_stop_global_time_window_coherence_protocol_v1.json"
RECEIPT = ROOT / "post_stop_global_time_window_coherence_receipt_v1.json"
prior = str(ROOT)
sys.path.insert(0, prior)
try:
    mod = runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(prior)


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_is_precommitted_to_exact_source_gap_window_lengths_and_no_holdout():
    p = _read(PROTO)
    r = _read(RECEIPT)
    assert p["schema"] == "eog.mckee2024.post_stop_full_segment_time_coherence.v1"
    assert p["status"] == "FROZEN_BEFORE_NEW_WINDOW_LENGTH_OR_GROUP_COHERENCE_COMPUTATION"
    assert r["protocol_committed_before_new_computation"] == "82d3be54e7f4689cbda60a43ab15827532b740b8"
    assert p["source"]["sha256"] == mod["SHA256"] == r["source_sha256"]
    assert mod["_check_protocol"]()["schema"] == p["schema"]
    assert tuple(p["window_lengths"]) == (2, 3, 4, 6, 12, 24)
    assert p["permitted_gap_seconds"] == {"lower": 1, "upper": 45000}
    assert p["historical_claim_boundary"]["dense_2h_holdout_sealed"] is True
    assert r["source_12h_records"] == 28953
    assert r["source_12h_groups"] == 421


def test_all_source_fixed_window_counts_reconcile_and_match_pr748_triples():
    r = _read(RECEIPT)
    totals = [28532, 28111, 27690, 26852, 24421, 20267]
    for scenario in r["clock_scenarios"]:
        rows = r["window_counts_by_scenario"][scenario]
        assert [a["records_per_window"] for a in rows] == [2, 3, 4, 6, 12, 24]
        assert [a["all_windows"] for a in rows] == totals
        for a in rows:
            assert a["coherent_whole_window"] + a["pairwise_only_false_chain"] == a["every_pair_possible"]
            assert 0 <= a["coherent_whole_window"] <= a["every_pair_possible"] <= a["all_windows"]
            assert a["false_fraction_of_pairwise_possible"] == pytest.approx(
                a["pairwise_only_false_chain"] / a["every_pair_possible"]
            )
        assert rows[0]["pairwise_only_false_chain"] == 0
    t0 = r["window_counts_by_scenario"]["T0_FULL_DAY_UNCERTAINTY"]
    t1 = r["window_counts_by_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    assert (t0[1]["every_pair_possible"], t0[1]["coherent_whole_window"], t0[1]["pairwise_only_false_chain"]) == (26764, 26700, 64)
    assert (t1[1]["every_pair_possible"], t1[1]["coherent_whole_window"], t1[1]["pairwise_only_false_chain"]) == (26637, 26637, 0)
    assert [a["pairwise_only_false_chain"] for a in t0] == [0, 64, 123, 217, 390, 590]
    assert [a["pairwise_only_false_chain"] for a in t1] == [0] * 6


def test_entire_group_false_chains_are_not_independent_fix_replicates():
    r = _read(RECEIPT)
    x = r["entire_group_counts_by_scenario"]["T0_FULL_DAY_UNCERTAINTY"]
    y = r["entire_group_counts_by_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    assert x == {
        "total_groups": 421,
        "all_pairwise_possible_groups": 230,
        "globally_coherent_groups": 216,
        "pairwise_only_false_chain_groups": 14,
        "groups_with_any_pair_excluded": 191,
    }
    assert y == {
        "total_groups": 421,
        "all_pairwise_possible_groups": 216,
        "globally_coherent_groups": 216,
        "pairwise_only_false_chain_groups": 0,
        "groups_with_any_pair_excluded": 205,
    }
    assert r["group_record_count_min_median_max"] == [3, 46, 304]
    assert r["claim_boundary"]["EOG_WF_frozen_scored"] == 3


def test_four_record_chain_may_fail_when_both_contiguous_triples_are_feasible():
    f = mod["path_possible"]
    # Independently chosen feasible triplet assignments need not choose
    # consistent clocks at both shared interior records.
    w = [(10, 15), (9, 17), (1, 14), (1, 12)]
    assert f(w[:3], max_gap=10)
    assert f(w[1:], max_gap=10)
    assert all(mod["pair_possible"](w[i], w[i+1], max_gap=10) for i in range(3))
    assert not f(w, max_gap=10)


def test_random_small_integer_chain_exactly_matches_independent_brute_force():
    rng = random.Random(20261124)
    coherent = mod["path_possible"]
    for _ in range(2500):
        n = rng.randint(2, 5)
        windows = []
        for i in range(n):
            lo = rng.randint(-3, 15)
            hi = lo + rng.randint(0, 4)
            windows.append((lo, hi))
        oracle = any(
            all(1 <= times[i+1] - times[i] <= 5 for i in range(n - 1))
            for times in itertools.product(*(range(lo, hi+1) for lo, hi in windows))
        )
        assert coherent(windows, max_gap=5) == oracle


def test_timestamp_window_conversion_does_not_choose_midnight_as_factual():
    fn = mod["_windows"]
    # Historical decoder tuple: T0.lower, T0.upper-exclusive for date,
    # T1.upper-inclusive, precision, DBF ordinal.
    date = (0, 86400, 3600, "date", 0)
    timed = (43200, 43200, 43200, "full", 1)
    assert fn([date, timed], 1) == [(0, 86399), (43200, 43200)]
    assert fn([date, timed], 2) == [(0, 3600), (43200, 43200)]
    with pytest.raises(ValueError, match="Unknown frozen"):
        fn([date], 3)


def test_bad_input_times_and_wrong_source_fails_closed(tmp_path):
    f = mod["path_possible"]
    with pytest.raises(ValueError, match="At least one"):
        f([])
    with pytest.raises(ValueError, match="nonempty"):
        f([(2, 1)])
    for gap in (0, True, -4):
        with pytest.raises(ValueError, match="positive integer"):
            f([(0, 1)], max_gap=gap)
    bogus = tmp_path / "GPS12hrs_Locs.zip"
    bogus.write_bytes(b"wrong original SHA")
    from replay_post_stop_time_interval_qc import _source_rows
    with pytest.raises(ValueError, match="filename or byte size"):
        _source_rows(bogus)


def test_claim_boundaries_remain_explicit_and_frozen():
    r = _read(RECEIPT)
    assert r["source_sha256_verified"] is True
    assert r["ordering_fixed_to_prior_T0_source_blind_rule"] is True
    assert r["UTC_or_DST_clock_alignment_verified"] is False
    assert r["source_author_CRS_verified"] is False
    assert r["ecological_movement_route_inferred"] is False
    assert r["2h_holdout_data_opened"] is False
    assert r["SHP_coordinates_opened"] is False
    assert r["raw_animal_IDs_times_or_locations_exported"] is False
    assert r["EOG_forecast_scored"] is False
