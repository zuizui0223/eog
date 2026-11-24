"""McKee 12h DST/source-clock sensitivity audit; raw source not in repository.

Independent integer-state oracle verifies disjoint permitted-clock interval
propagation and minimum segmentation for 1000+ small synthetic worlds.
No dense 2h GPS, animal identifiers, coordinates, or dates are scored.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from itertools import product
import json
from pathlib import Path
import random
import runpy
import sys

import pytest


HERE = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
SCRIPT = HERE / "replay_post_stop_dst_union_coherence.py"
PROTOCOL = HERE / "post_stop_dst_fold_coherence_protocol_v1.json"
RECEIPT = HERE / "post_stop_dst_union_coherence_receipt_v1.json"
sys.path.insert(0, str(HERE))
try:
    lib = runpy.run_path(str(SCRIPT))
finally:
    sys.path.remove(str(HERE))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_protocol_precommitted_source_identity_and_no_outcomes():
    p, r = _load(PROTOCOL), _load(RECEIPT)
    assert p["schema"] == "eog.mckee2024.post_stop_local_clock_vs_timezone_gap_audit.v1"
    assert p["status"] == "FROZEN_PRE_SOURCE_TIMESTAMP_TO_UTC_CONVERSION"
    assert r["precommitted_protocol_sha"] == "faac1fad698e88807386819e6c84d9800a87f64f"
    assert p["source"]["sha256"] == lib["SHA256"] == r["source_sha256"]
    assert p["source"]["bytes"] == r["source_file_size_bytes"] == 1539661
    assert p["source"]["records"] == r["records"] == 28953
    assert p["source"]["groups"] == r["groups"] == 421
    assert r["adjacent_links"] == 28532
    assert lib["_check_protocol"]()["schema"] == p["schema"]
    assert p["original_EOG_WF"]["scored"] == 3


def test_fall_back_repeated_hour_is_union_not_convex_hull():
    fold = lib["valid_utc_folds"]
    allowed = lib["allowed_instants"]
    EPOCH = lib["EPOCH"]
    dt = datetime(2018, 11, 4, 1, 30)
    exact = fold(dt)
    assert len(exact) == 2
    assert exact[1] - exact[0] == 3600
    record_full = (int((dt-EPOCH).total_seconds()), 0, 0, "full", 0)
    assert allowed(record_full, lib["SCENARIOS"][1], lib["CLOCKS"][2]) == (
        (exact[0], exact[0]), (exact[1], exact[1])
    )
    day = datetime(2018, 11, 4)
    record_day = (int((day-EPOCH).total_seconds()), 0, 0, "date", 0)
    t1 = allowed(record_day, lib["SCENARIOS"][1], lib["CLOCKS"][2])
    assert len(t1) == 2
    assert t1[1][0] - t1[0][1] == 3600
    assert t1[1][0] == t1[1][1]
    t0 = allowed(record_day, lib["SCENARIOS"][0], lib["CLOCKS"][2])
    assert len(t0) == 1
    assert t0[0][1] - t0[0][0] + 1 == 25 * 3600


def test_spring_forward_day_has_23_real_hours_not_24():
    fold = lib["valid_utc_folds"]
    allowed = lib["allowed_instants"]
    EPOCH = lib["EPOCH"]
    assert not fold(datetime(2018, 3, 11, 2, 30))
    dt = datetime(2018, 3, 11)
    record = (int((dt-EPOCH).total_seconds()), 0, 0, "date", 0)
    day = allowed(record, lib["SCENARIOS"][0], lib["CLOCKS"][2])
    assert len(day) == 1
    assert day[0][1] - day[0][0] + 1 == 23 * 3600
    assert len(allowed(record, lib["SCENARIOS"][1], lib["CLOCKS"][2])) == 1


def test_fixed_mst_is_constant_shift_of_naive_for_each_timestamp_kind():
    allowed = lib["allowed_instants"]
    EPOCH = lib["EPOCH"]
    for dt in (datetime(2018, 11, 4), datetime(2018, 11, 4, 1, 30),
               datetime(2018, 3, 11), datetime(2018, 3, 11, 12, 30)):
        for kind in ("date", "full"):
            record = (int((dt-EPOCH).total_seconds()), 0, 0, kind, 0)
            for scenario in lib["SCENARIOS"]:
                naive = allowed(record, scenario, lib["CLOCKS"][0])
                mst = allowed(record, scenario, lib["CLOCKS"][1])
                assert mst == tuple((lo + 25200, hi + 25200) for lo, hi in naive)


def _enumerate_allowed(interval_union):
    return sorted({t for lo, hi in interval_union for t in range(lo, hi+1)})


def _oracle_path(windows, maximum):
    alternatives = [_enumerate_allowed(w) for w in windows]
    return any(
        all(1 <= values[i+1]-values[i] <= maximum for i in range(len(values)-1))
        for values in product(*alternatives)
    )


def _oracle_min_cuts(windows, maximum):
    count = len(windows)
    optimum = count - 1
    for mask in product((0, 1), repeat=count-1):
        blocks = []
        start = 0
        for i, flag in enumerate(mask, start=1):
            if flag:
                blocks.append(windows[start:i])
                start = i
        blocks.append(windows[start:])
        if all(_oracle_path(block, maximum) for block in blocks):
            optimum = min(optimum, sum(mask))
    return optimum


def test_independent_integer_union_clock_oracle_and_optimal_partitions():
    rng = random.Random(20261124)
    canonical = lib["canonical_union"]
    advance = lib["advance"]
    segment = lib["segmentation"]
    for _ in range(1100):
        n = rng.randint(2, 5)
        maximum = rng.randint(2, 5)
        windows = []
        for _ in range(n):
            intervals = []
            for _ in range(rng.randint(1, 2)):
                start = rng.randint(-2, 9)
                intervals.append((start, start + rng.randint(0, 2)))
            windows.append(canonical(intervals))
        # Independent enumeration of ALL time choices in a small finite world.
        reachable = windows[0]
        for next_window in windows[1:]:
            reachable = advance(reachable, next_window, maximum)
        assert bool(reachable) == _oracle_path(windows, maximum)
        cuts, optimistic = segment(windows) if maximum == lib["H"] else _synthetic_segmentation(lib, windows, maximum)
        assert len(cuts) == _oracle_min_cuts(windows, maximum)
        assert optimistic.issubset(cuts)


def _synthetic_segmentation(module, windows, maximum):
    a, b = set(), set()
    reach = windows[0]
    for i, target in enumerate(windows[1:], start=1):
        if not module["advance"](windows[i-1], target, maximum):
            b.add(i)
        nxt = module["advance"](reach, target, maximum)
        if nxt:
            reach = nxt
        else:
            a.add(i)
            reach = target
    return a, b


def test_disjoint_intervals_prevent_world_spliced_path():
    c = lib["canonical_union"]
    w = (c(((0,0),)), c(((5,5), (15,15))), c(((20,20),)))
    assert lib["advance"](w[0], w[1], 10)
    assert lib["advance"](w[1], w[2], 10)
    assert not lib["advance"](lib["advance"](w[0], w[1], 10), w[2], 10)


def test_frozen_real_source_diagnostics_and_all_three_clock_results():
    r = _load(RECEIPT)
    d = r["fold_and_date_only_transition_counts"]
    assert d == {
        "exact_full_ambiguous_folds": 25,
        "exact_full_nonexistent_times": 0,
        "date_only_fall_transition_records": 74,
        "date_only_spring_transition_records": 36
    }
    assert r["naive_local_vs_fixed_MST_masks_identical"] is True
    for case, naive, denver, first_opt, first_extra in (
        ("T0_FULL_DAY_UNCERTAINTY", 857, 889, 793, 89),
        ("T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW", 858, 890, 858, 25),
    ):
        x = r["clock_gap_arm_counts"][case]
        assert x["NAIVE_MOUNTAIN_LOCAL"] == x["FIXED_MST_UTC_MINUS_07"]
        assert x["NAIVE_MOUNTAIN_LOCAL"]["coherent_cuts"] == naive
        assert x["NAIVE_MOUNTAIN_LOCAL"]["optimistic_cuts"] == first_opt
        assert x["AMERICA_DENVER_IANA"]["coherent_cuts"] == denver
        assert x["AMERICA_DENVER_IANA"]["additional_coherent_cuts"] == first_extra
        table = r["naive_vs_iana_coherent_cut_paired_counts"][case]
        assert table["cut_both"] == naive
        assert table["naive_only"] == 0
        assert table["denver_only"] == 32
        assert table["affected_groups"] == 32
        assert (table["cut_both"]+table["naive_only"]+
                table["denver_only"]+table["retained_both"]) == 28532


def test_claims_never_upgrade_conditional_clock_to_true_migration():
    r = _load(RECEIPT)
    assert r["time_interpretations_author_verified"] is False
    assert r["physical_elapsed_hours_or_DST_source_verified"] is False
    assert r["original_CRS_QC_STOP_retained"] is True
    assert r["original_date_only_clock_QC_STOP_retained"] is True
    assert r["dense_2h_GPS_opened"] is False
    assert r["source_geometry_opened"] is False
    assert r["raw_record_times_animal_IDs_coordinates_exported"] is False
    assert r["ecological_or_EOG_prediction_scored"] is False
    assert r["frozen_EOG_WF_scored_count"] == 3


def test_invalid_source_rejected_prior_to_record_access(tmp_path):
    from replay_post_stop_time_interval_qc import _source_rows
    bad = tmp_path / "GPS12hrs_Locs.zip"
    bad.write_bytes(b"not the original source")
    with pytest.raises(ValueError, match="filename or byte size"):
        _source_rows(bad)
