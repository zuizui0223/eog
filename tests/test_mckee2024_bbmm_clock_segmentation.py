"""Exact source-boundary and synthetic minimal-cut checks for BBMM time splits.

No GPS ZIP is part of the repository and these tests do not read raw
animal records. Synthetic integer clock assignments provide an independent
small-graph oracle for greedy minimal segmentation.
"""
from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import random
import runpy
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
RECEIPT = ROOT / "post_stop_bbmm_clock_segmentation_receipt_v1.json"
PROTOCOL = ROOT / "post_stop_bbmm_clock_segmentation_protocol_v1.json"
SCRIPT = ROOT / "replay_post_stop_bbmm_clock_segmentation.py"
sys.path.insert(0, str(ROOT))
try:
    ns = runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(ROOT))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_before_source_freeze_and_exact_12hour_gap():
    p = _load(PROTOCOL)
    r = _load(RECEIPT)
    assert p["schema"] == "eog.mckee2024.source_only_clock_bridge_segmentation.v1"
    assert p["status"] == "FROZEN_BEFORE_NEW_SEGMENTATION_COMPUTATION"
    assert r["protocol_committed_before_new_source_computation"] == (
        "d1e28d23f6faf63ddc51729dd6671a9a05c7ccf7"
    )
    assert p["source"]["sha256"] == ns["SHA256"] == r["source_sha256"]
    assert p["source"]["size_bytes"] == r["source_file_bytes"] == 1539661
    assert p["source"]["record_count"] == r["source_records"] == 28953
    assert p["published_gap_rule"]["max_seconds"] == r["max_gap_seconds"] == 45000
    assert ns["_validate"]()["status"] == p["status"]
    assert p["data_access"]["dense_2hour_holdout"] is False
    assert p["data_access"]["shapefile_geometry"] is False


def test_source_counts_reconcile_for_all_three_segment_policies():
    r = _load(RECEIPT)
    assert r["source_groups"] == 421
    for scenario in r["scenario_results"].values():
        a = scenario["arm_stats"]
        bins = scenario["segment_length_bins"]
        for arm in ns["ARMS"]:
            cuts = a[f"{arm}_cuts"]
            segments = a[f"{arm}_segments"]
            assert a[f"{arm}_retained_edges"] + cuts == 28532
            assert segments == 421 + cuts
            assert sum(v for key, v in bins.items() if key.startswith(arm + "::")) == segments
            assert a[f"{arm}_segments_ge2"] <= segments
            assert a[f"{arm}_records_in_segments_ge2"] <= 28953
            assert (
                a[f"{arm}_records_in_segments_ge2"]
                + bins.get(f"{arm}::1", 0)
            ) == 28953
        assert a["optimistic_cuts"] <= a["coherent_cuts"] <= a["conservative_cuts"]
        assert (
            a["coherent_cuts"] - a["optimistic_cuts"]
            == a["additional_coherent_cuts_beyond_pairwise"]
        )


def test_original_source_clock_ambiguity_is_not_silently_resolved():
    r = _load(RECEIPT)
    t0 = r["scenario_results"]["T0_FULL_DAY_UNCERTAINTY"]
    t1 = r["scenario_results"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    a, b = t0["arm_stats"], t1["arm_stats"]
    assert (a["optimistic_cuts"], a["coherent_cuts"], a["conservative_cuts"]) == (
        793, 857, 22205
    )
    assert (b["optimistic_cuts"], b["coherent_cuts"], b["conservative_cuts"]) == (
        858, 858, 11498
    )
    assert a["additional_coherent_cuts_beyond_pairwise"] == 64
    assert t0["group_stats"]["groups_with_extra_coherent_cut"] == 41
    assert t0["group_stats"]["groups_all_pairs_possible_but_need_extra_cut"] == 14
    assert b["additional_coherent_cuts_beyond_pairwise"] == 0
    assert sum(
        int(k) * v for k, v in t0["extra_cut_count_frequency_across_groups"].items()
    ) == 64
    assert sum(t0["extra_cut_count_frequency_across_groups"].values()) == 41
    assert a["conservative_retained_edges"] == 6327
    assert b["conservative_retained_edges"] == 17034


def test_gap_definition_split_and_singleton_behaviour():
    split = ns["split_sequence"]
    w = [(0, 0), (1, 20), (25, 25)]
    assert split(w, "optimistic", 10) == ((3,), ())
    assert split(w, "coherent", 10) == ((2, 1), (2,))
    assert split([(0, 0)], "coherent", 10) == ((1,), ())
    assert split([(0, 0), (0, 0)], "optimistic", 10) == ((1, 1), (1,))
    assert split([(0, 0), (1, 1)], "conservative", 10) == ((2,), ())


def _brute_chain_possible(windows, gap):
    return any(
        all(1 <= times[i+1] - times[i] <= gap for i in range(len(times)-1))
        for times in product(*(range(lo, hi+1) for lo, hi in windows))
    )


def _independent_minimum_cuts(windows, gap):
    n = len(windows)
    optimal = n - 1
    for boundaries in product((0, 1), repeat=n-1):
        parts = []
        start = 0
        for idx, cut in enumerate(boundaries, start=1):
            if cut:
                parts.append(windows[start:idx])
                start = idx
        parts.append(windows[start:])
        if all(_brute_chain_possible(part, gap) for part in parts):
            optimal = min(optimal, sum(boundaries))
    return optimal


def test_greedy_coherent_cuts_match_exhaustive_optimal_partition_oracle():
    rng = random.Random(20261124)
    split = ns["split_sequence"]
    for _ in range(350):
        n = rng.randint(2, 5)
        gap = rng.randint(2, 5)
        windows = []
        for _ in range(n):
            lower = rng.randint(-2, 12)
            windows.append((lower, lower + rng.randint(0, 3)))
        _, coherent_cuts = split(windows, "coherent", gap)
        assert len(coherent_cuts) == _independent_minimum_cuts(windows, gap)
        _, possible_cuts = split(windows, "optimistic", gap)
        _, robust_cuts = split(windows, "conservative", gap)
        assert set(possible_cuts).issubset(coherent_cuts)
        assert set(coherent_cuts).issubset(robust_cuts)


def test_wrong_archive_never_opens_animal_records(tmp_path):
    source = tmp_path / "GPS12hrs_Locs.zip"
    source.write_bytes(b"incorrect original source")
    from replay_post_stop_time_interval_qc import _source_rows
    with pytest.raises(ValueError, match="filename or byte size"):
        _source_rows(source)
    r = _load(RECEIPT)
    assert r["actual_BBMM_fitted"] is False
    assert r["2h_dense_holdout_opened"] is False
    assert r["raw_GPS_coordinates_individual_IDs_or_timestamps_exported"] is False
    assert r["EOG_prediction_scored"] is False
    assert r["EOG_WF_frozen_scored"] == 3


def test_invalid_segmentation_input_fails_closed():
    split = ns["split_sequence"]
    with pytest.raises(ValueError, match="Nonempty"):
        split([], "coherent")
    with pytest.raises(ValueError, match="known arm"):
        split([(0, 0)], "not-an-arm")
    with pytest.raises(ValueError, match="empty time interval"):
        split([(2, 1)], "coherent")
    for bad in (0, -2, True):
        with pytest.raises(ValueError, match="Positive integer"):
            split([(0, 0)], "coherent", bad)
