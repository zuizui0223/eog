"""Offline regression for frozen McKee sparse-time interval/trajectory coherence.

Does not access raw GPS files. Small integer-window brute-force oracle is
independent from the dynamic programming implementation under test.
"""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import random
import runpy

import pytest


ROOT = Path(__file__).resolve().parents[1] / "validation/temporal_corridor_mckee2024"
MODULE = runpy.run_path(str(ROOT / "replay_post_stop_time_interval_qc.py"))
PAIR = ROOT / "post_stop_time_interval_pair_receipt_v1.json"
TRIPLE = ROOT / "post_stop_triplet_time_coherence_receipt_v1.json"
PP = ROOT / "post_stop_time_interval_identifiability_protocol_v1.json"
TP = ROOT / "post_stop_triplet_time_coherence_protocol_v1.json"
SOURCE_SHA = "556062b7426336a94fe93dd9e6b049dc6c960d3dc8135f7298f465126c6962c4"


def _load(filename: Path):
    return json.loads(filename.read_text(encoding="utf-8"))


def test_protocols_freeze_source_identity_before_pair_and_triple_computations():
    p, t = _load(PP), _load(TP)
    assert p["status"] == "FROZEN_BEFORE_NEW_INTERVAL_GAP_COMPUTATION"
    assert t["status"] == "FROZEN_BEFORE_NEW_3_RECORD_TIME_FEASIBILITY_COMPUTATION"
    assert p["source"]["sha256"] == t["source_sha256"] == MODULE["SHA256"] == SOURCE_SHA
    assert p["max_bridge_gap_hours"] == 12.5
    assert t["maximum_allowed_gap_seconds"] == 45000
    assert t["minimum_allowed_forward_gap_seconds"] == 1
    assert "2h" in str(p["source"]["prohibit"])


def test_all_pairwise_counts_reconcile_and_midnight_is_not_claimed_as_truth():
    a = _load(PAIR)
    assert a["protocol_sha_commit"] == "0db021f77bbcf6bda0f434b01e7cc5f899287620"
    assert a["source_sha256_verified"]
    assert a["source_dbf_records"] == 28953
    assert a["within_group_total"] == 421
    assert a["observed_full_datetime_count"] == 18118
    assert a["observed_date_only_count"] == 10835
    assert sum(a["pair_timestamp_types"].values()) == 28532
    assert a["pair_timestamp_types"] == {
        "date-date": 61, "date-full": 21363, "full-full": 7108
    }
    for row in a["pair_status_by_time_scenario"].values():
        assert sum(row[key] for key in ("robust", "contingent", "excluded")) == 28532
        assert row["total_pairs"] == 28532
    assert a["pair_status_by_time_scenario"]["T0_FULL_DAY_UNCERTAINTY"]["robust"] == 6327
    assert a["pair_status_by_time_scenario"]["T0_FULL_DAY_UNCERTAINTY"]["contingent"] == 21412
    assert a["pair_status_by_time_scenario"]["T0_FULL_DAY_UNCERTAINTY"]["excluded"] == 793
    assert a["pair_status_by_time_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]["robust"] == 17034
    assert a["pair_status_by_time_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]["contingent"] == 10640
    assert a["pair_status_by_time_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]["excluded"] == 858
    assert sum(a["transition_between_scenarios"].values()) == 28532
    assert a["transition_between_scenarios"]["contingent=>robust"] == 10707
    assert a["physical_elapsed_time_certified"] is False
    assert a["dense_2h_holdout_opened"] is False
    assert a["ecological_forecast_or_score_computed"] is False


def test_original_triplet_data_exhibit_pairwise_only_time_splicing():
    a = _load(TRIPLE)
    assert a["protocol_commit"] == "8221f67d86a03636a319005b58fd4c317836c42c"
    assert a["original_12h_records"] == 28953
    assert a["animal_season_groups"] == 421
    assert a["within_group_triplets"] == 28111
    t0 = a["results"]["T0_FULL_DAY_UNCERTAINTY"]
    assert t0["both_edges_pairwise_possible"] == 26764
    assert t0["globally_feasible_among_two_possible"] == 26700
    assert t0["pairwise_possible_but_globally_infeasible"] == 64
    assert t0["groups_with_any_false_chain"] == 41
    assert t0["false_chain_timestamp_precision_signatures"] == {"FDD": 59, "FDF": 5}
    t1 = a["results"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    assert t1["both_edges_pairwise_possible"] == 26637
    assert t1["pairwise_possible_but_globally_infeasible"] == 0
    for row in (t0, t1):
        assert (
            row["globally_feasible_among_two_possible"]
            + row["pairwise_possible_but_globally_infeasible"]
            == row["both_edges_pairwise_possible"]
        )
        assert (
            row["both_edges_pairwise_possible"]
            + row["at_least_one_pairwise_impossible"]
            == 28111
        )
    assert a["source_time_zone_and_DST_verified"] is False
    assert a["original_source_QC_STOP_preserved"]
    assert a["two_hour_dense_holdout_opened"] is False


def test_independent_exhaustive_integer_window_truth_table():
    func = MODULE["time_triplet_possible"]
    rng = random.Random(0)
    for _ in range(10000):
        windows = []
        for _ in range(3):
            lower = rng.randint(0, 19)
            upper = lower + rng.randint(0, 9)
            windows.append((lower, upper))
        oracle = any(
            1 <= t1 - t0 <= 5 and 1 <= t2 - t1 <= 5
            for t0 in range(windows[0][0], windows[0][1] + 1)
            for t1 in range(windows[1][0], windows[1][1] + 1)
            for t2 in range(windows[2][0], windows[2][1] + 1)
        )
        assert func(windows, max_gap=5) == oracle


def test_two_locally_possible_edges_can_have_no_common_middle_time():
    pair_ok = MODULE["_triple_pair_possible"]
    full = MODULE["time_triplet_possible"]
    bad = [(0, 0), (1, 20), (25, 25)]
    good = [(0, 0), (1, 20), (16, 16)]
    assert pair_ok(bad, max_gap=10) and not full(bad, max_gap=10)
    assert pair_ok(good, max_gap=10) and full(good, max_gap=10)


def test_pairwise_date_interval_withheld_vs_published_near_midnight_window():
    classify = MODULE["pair_status"]
    # Date-only at day0 can be anywhere in T0, 00:00..01:00 in T1.
    date = (0, 86400, 3600, "date", 0)
    noon = (43200, 43200, 43200, "full", 1)
    assert classify(date, noon, 1)[0] == "contingent"
    assert classify(date, noon, 2)[0] == "robust"


def test_invalid_windows_fail_closed_and_date_only_is_not_silently_imputed():
    with pytest.raises(ValueError, match="Exactly three"):
        MODULE["time_triplet_possible"]([(0, 1), (2, 3)])
    with pytest.raises(ValueError, match="Nonexistent"):
        MODULE["time_triplet_possible"]([(2, 1), (2, 3), (4, 5)])
    p = _load(PP)
    assert p["clock_interpretations"][0]["id"] == "T0_FULL_DAY_UNCERTAINTY"
    assert p["clock_interpretations"][1]["id"] == "T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"
    assert p["scope_boundary"]["source_time_QC_STOP_preserved"]
    assert p["scope_boundary"]["source_CRS_QC_STOP_preserved"]


def test_wrong_local_archive_rejected_without_reading_gps_data(tmp_path):
    bad = tmp_path / "GPS12hrs_Locs.zip"
    bad.write_bytes(b"not the published sparse data")
    with pytest.raises(ValueError, match="filename or byte size"):
        MODULE["_source_rows"](bad)
    for receipt in (_load(PAIR), _load(TRIPLE)):
        assert receipt["raw_data_or_identifiers_exported"] is False if (
            "raw_data_or_identifiers_exported" in receipt
        ) else receipt["animal_ids_or_exact_timestamps_exported"] is False



def test_v2_exact_integer_second_endpoint_correction_is_separate_and_auditable():
    v1 = _load(PAIR)
    p = _load(ROOT / "post_stop_time_endpoint_seconds_protocol_v2.json")
    corrected = _load(ROOT / "post_stop_time_interval_pair_receipt_v2.json")
    assert p["status"] == "FROZEN_AFTER_V1_ENDPOINT_AUDIT_BEFORE_CORRECTED_RECOMPUTATION"
    assert corrected["correction_protocol_commit"] == (
        "4cc96cfbb60051b21bcddda7831436429448f3a4"
    )
    assert corrected["source_sha256"] == SOURCE_SHA
    old0 = v1["pair_status_by_time_scenario"]["T0_FULL_DAY_UNCERTAINTY"]
    now0 = corrected["pair_status_by_time_scenario"]["T0_FULL_DAY_UNCERTAINTY"]
    old1 = v1["pair_status_by_time_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    now1 = corrected["pair_status_by_time_scenario"]["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]
    for status in ("robust", "contingent", "excluded"):
        assert now0[status] == old0[status]
        assert now1[status] == old1[status]
    assert old0["ambiguous_order"] == 10767
    assert now0["ambiguous_order"] == 10707
    assert now1["ambiguous_order"] == old1["ambiguous_order"] == 0
    assert corrected["pair_status_changes_from_historical_v1"]["T0_ambiguous_order"] == -60
    assert corrected["preserved_triple_result"]["T0_pairwise_possible_but_globally_infeasible"] == 64


def test_v2_uses_last_second_of_day_not_unattainable_next_midnight():
    status = MODULE["pair_status"]
    date = (0, 86400, 3600, "date", 0)
    next_midnight = (86400, 86400, 86400, "full", 1)
    legacy_status, legacy_ambiguous = status(date, next_midnight, 1)
    new_status, new_ambiguous = status(date, next_midnight, 1, integer_closed=True)
    assert legacy_status == new_status == "contingent"
    assert legacy_ambiguous is True
    assert new_ambiguous is False
    # Both pair classifications still respect the original 12.5h criterion.
    assert status(date, next_midnight, 2, integer_closed=True)[0] == "excluded"



def test_all_six_orderings_cannot_rescue_original_64_false_chains():
    from itertools import permutations
    p = _load(ROOT / "post_stop_triplet_order_permutation_protocol_v1.json")
    row = _load(ROOT / "post_stop_triplet_order_permutation_receipt_v1.json")
    assert p["status"] == "FROZEN_BEFORE_REORDERING_SENSITIVITY_CALCULATION"
    assert row["protocol_commit"] == "c2e8e87e5c5fbd46e322b32204fb00ef640b34d0"
    assert row["source_sha256"] == SOURCE_SHA
    assert row["all_3_factorial_permutations_checked"] is True
    t0 = row["T0_FULL_DAY_UNCERTAINTY"]
    assert t0["triples"] == 28111
    assert t0["fixed_false_chain"] == 64
    assert t0["fixed_false_chain_rescued_by_permutation"] == 0
    assert t0["fixed_false_chain_infeasible_under_all_permutations"] == 64
    assert t0["fixed_infeasible_but_reorder_feasible"] == 167
    assert t0["groups_with_any_reorder_rescue"] == 75
    assert t0["all_permutations_infeasible"] + t0["any_permutation_feasible"] == 28111
    assert row["T1_PUBLISHED_NEAR_MIDNIGHT_WINDOW"]["fixed_false_chain"] == 0
    assert row["dense_2h_holdout_opened"] is False
    assert row["individual_ids_exact_timestamps_coordinates_exported"] is False

    # This is a synthetic witness of an ordering-independent false chain.
    impossible = [(0, 0), (1, 20), (25, 25)]
    assert MODULE["_triple_pair_possible"](impossible, max_gap=10)
    assert all(
        not MODULE["time_triplet_possible"]([impossible[i] for i in order], max_gap=10)
        for order in permutations((0, 1, 2))
    )
    # Separately, a wrongly sorted but consistent physical time sequence is
    # rescued by some order: ordering matters for *other* triplets.
    wrongly_ordered = [(20, 20), (0, 0), (10, 10)]
    assert not MODULE["time_triplet_possible"](wrongly_ordered, max_gap=10)
    assert any(
        MODULE["time_triplet_possible"]([wrongly_ordered[i] for i in order], max_gap=10)
        for order in permutations((0, 1, 2))
    )
