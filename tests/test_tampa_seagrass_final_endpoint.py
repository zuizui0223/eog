from __future__ import annotations

import copy
import csv
import io
import json
from pathlib import Path

import numpy as np
import pytest

from validation.tampa_seagrass_endpoint3.final_endpoint import (
    FinalEndpointTerminal,
    build_frozen_operators,
    encode_baseline_fold,
    evaluate_final_endpoint,
    parse_occurrence_response,
    precompute_cumulative_hitting,
    training_occurrence_set,
)
from validation.tampa_seagrass_endpoint3.gate0_pre_response import (
    canonical_sha256,
    git_blob_sha1,
)


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONTRACT = ROOT / "validation/tampa_seagrass_endpoint3/final_endpoint_contract.json"
DECLARATION = ROOT / "validation/tampa_seagrass_endpoint3/final_endpoint_declaration.json"
HEADERS_PASS = ROOT / "validation/tampa_seagrass_endpoint3/response_headers_pass_certificate.json"


def load_json(path: Path):
    return json.loads(path.read_text())


def occurrence_bytes(rows):
    header = load_json(FINAL_CONTRACT)["response_parser"]["header_exact_order"]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([row.get(name, "") for name in header])
    return buffer.getvalue().encode()


def synthetic_state_and_contract():
    contract = copy.deepcopy(load_json(FINAL_CONTRACT))
    declaration = load_json(DECLARATION)
    node_ids = tuple(f"N{i:02d}" for i in range(15))
    coords = {node_id: (-82.50 + i * 0.01, 27.80) for i, node_id in enumerate(node_ids)}
    rows = []
    child_to_parent = {}
    response_rows = []
    for i, node_id in enumerate(node_ids):
        fold = 1 + (i % 5)
        for suffix, positive in (("a", True), ("b", False)):
            unit_id = f"P{i:02d}_{suffix}"
            child_id = f"C{i:02d}_{suffix}"
            child_to_parent[child_id] = unit_id
            lon, lat = coords[node_id]
            rows.append(
                {
                    "unit_id": unit_id,
                    "node_id": node_id,
                    "event_date": "2024-04-01",
                    "context_id": "2024",
                    "survey_year": 2024,
                    "day_of_year": 92,
                    "longitude": lon,
                    "latitude": lat,
                    "water_body": "Tampa Bay",
                    "fold": fold,
                    "child_point_count": 3,
                    "depth_min_m": 0.5,
                    "depth_median_m": 1.0,
                    "depth_max_m": 1.5,
                }
            )
            response_rows.append(
                {
                    "occurrenceID": f"O{i:02d}_{suffix}",
                    "eventID": child_id,
                    "basisOfRecord": "HumanObservation",
                    "occurrenceStatus": "present" if positive else "absent",
                    "scientificName": "Thalassia testudinum" if positive else "Alismatales",
                }
            )
    rows.sort(key=lambda row: row["unit_id"])
    event_state = {
        "candidate_rows": rows,
        "child_to_parent": child_to_parent,
        "node_ids": node_ids,
        "node_coords": coords,
    }
    raw = occurrence_bytes(response_rows)
    contract["source"]["occurrence_response"]["size_bytes"] = len(raw)
    contract["source"]["occurrence_response"]["git_blob_sha1"] = git_blob_sha1(raw)
    contract["worlds"]["local_worlds"] = [
        {"world_id": "haversine_q25", "threshold_km": 2.0},
        {"world_id": "haversine_q50", "threshold_km": 5.0},
        {"world_id": "haversine_q75", "threshold_km": 10.0},
        {"world_id": "haversine_q90", "threshold_km": 20.0},
    ]
    contract["worlds"]["max_steps"] = 14
    contract["layer_b"]["forecast_step"] = 14
    contract["worlds"]["world_family_fingerprint"] = canonical_sha256(
        {
            "metric": "haversine_km",
            "local_thresholds_km": [2.0, 5.0, 10.0, 20.0],
            "external_open": True,
            "pair_distance_count": 105,
        }
    )
    contract["candidate_and_split"]["fold_ids"] = [1, 2, 3, 4, 5]
    estimability = contract["estimability"]
    estimability["minimum_total_positive_candidate_units"] = 5
    estimability["minimum_total_negative_candidate_units"] = 5
    estimability["minimum_total_ever_positive_nodes"] = 5
    estimability["minimum_calibration_positive_candidate_units_each_fold"] = 2
    estimability["minimum_calibration_negative_candidate_units_each_fold"] = 2
    estimability["minimum_calibration_ever_positive_nodes_each_fold"] = 2
    estimability["minimum_heldout_folds_with_both_classes"] = 5
    contract["learner"]["n_estimators"] = 3
    contract["learner"]["n_jobs"] = 1
    operators, graph_audit = build_frozen_operators(node_ids, coords, contract)
    hitting = {
        world_id: precompute_cumulative_hitting(op, max_steps=14)
        for world_id, op in operators.items()
    }
    baseline_folds = {}
    for fold in range(1, 6):
        train_rows = [row for row in rows if row["fold"] != fold]
        heldout_rows = [row for row in rows if row["fold"] == fold]
        x_train, x_heldout, audit = encode_baseline_fold(train_rows, heldout_rows, contract)
        baseline_folds[fold] = {
            "train_rows": train_rows,
            "heldout_rows": heldout_rows,
            "x_train": x_train,
            "x_heldout": x_heldout,
            "audit": audit,
        }
    prepared = {
        "event_state": event_state,
        "operators": operators,
        "hitting_history": hitting,
        "world_graph_audit": graph_audit,
        "baseline_folds": baseline_folds,
    }
    return prepared, contract, declaration, raw


def test_final_contract_keeps_emof_full_payload_sealed():
    c = load_json(FINAL_CONTRACT)
    assert c["source"]["maximum_live_full_gets"] == 2
    assert c["source"]["event_full_gets"] == 1
    assert c["source"]["occurrence_full_gets"] == 1
    assert c["source"]["emof_full_gets"] == 0
    assert c["source"]["emof_header_only"]["full_payload_needed_for_endpoint"] is False
    assert c["hard_stop"]["emof_full_payload_may_be_opened_after_occurrence_result"] is False


def test_header_pass_certificate_records_zero_response_rows():
    p = load_json(HEADERS_PASS)
    assert p["status"] == "response_headers_ready"
    assert p["total_header_bytes_opened"] == 307
    assert p["response_data_row_bytes_opened"] == 0
    assert p["response_rows_opened"] == 0
    assert p["response_values_opened"] is False


def test_training_crossfit_removes_entire_node_history():
    node_ids = ("A", "B", "C", "D")
    assert training_occurrence_set(("A", "B", "C"), "B", node_ids) == ("A", "C")
    assert training_occurrence_set(("A", "B", "C"), "D", node_ids) == ("A", "B", "C")


def test_occurrence_parser_maps_child_to_parent_and_preserves_negative():
    prepared, contract, _, raw = synthetic_state_and_contract()
    labels, audit = parse_occurrence_response(raw, prepared["event_state"], contract)
    assert labels["P00_a"] == 1
    assert labels["P00_b"] == 0
    assert audit["positive_candidate_count"] == 15
    assert audit["negative_candidate_count"] == 15
    assert audit["ever_positive_node_count"] == 15


def test_occurrence_parser_rejects_unknown_child_without_repair():
    prepared, contract, _, _ = synthetic_state_and_contract()
    raw = occurrence_bytes(
        [
            {
                "occurrenceID": "O1",
                "eventID": "UNKNOWN",
                "basisOfRecord": "HumanObservation",
                "occurrenceStatus": "present",
                "scientificName": "Thalassia testudinum",
            }
        ]
    )
    contract["source"]["occurrence_response"]["size_bytes"] = len(raw)
    contract["source"]["occurrence_response"]["git_blob_sha1"] = git_blob_sha1(raw)
    with pytest.raises(FinalEndpointTerminal, match="unknown/invalid child eventID"):
        parse_occurrence_response(raw, prepared["event_state"], contract)


def test_occurrence_parser_rejects_focal_absent_semantics():
    prepared, contract, _, _ = synthetic_state_and_contract()
    raw = occurrence_bytes(
        [
            {
                "occurrenceID": "O1",
                "eventID": "C00_a",
                "basisOfRecord": "HumanObservation",
                "occurrenceStatus": "absent",
                "scientificName": "Thalassia testudinum",
            }
        ]
    )
    contract["source"]["occurrence_response"]["size_bytes"] = len(raw)
    contract["source"]["occurrence_response"]["git_blob_sha1"] = git_blob_sha1(raw)
    with pytest.raises(FinalEndpointTerminal, match="exact focal row is not present"):
        parse_occurrence_response(raw, prepared["event_state"], contract)


def test_baseline_preprocessing_is_calibration_only_and_unseen_safe():
    c = load_json(FINAL_CONTRACT)
    train = [
        {"longitude": 1, "latitude": 2, "survey_year": 2020, "day_of_year": 1, "child_point_count": 3, "depth_min_m": 1.0, "depth_median_m": 2.0, "depth_max_m": 3.0, "water_body": "A"},
        {"longitude": 2, "latitude": 3, "survey_year": 2021, "day_of_year": 2, "child_point_count": 4, "depth_min_m": "", "depth_median_m": "", "depth_max_m": "", "water_body": "B"},
    ]
    held = [
        {"longitude": 3, "latitude": 4, "survey_year": 2022, "day_of_year": 3, "child_point_count": 5, "depth_min_m": None, "depth_median_m": None, "depth_max_m": None, "water_body": "C"}
    ]
    x_train, x_held, audit = encode_baseline_fold(train, held, c)
    assert np.isfinite(x_train).all() and np.isfinite(x_held).all()
    assert audit["categorical_levels"]["water_body"] == ["A", "B"]
    assert audit["feature_names"][-1] == "water_body__UNSEEN"
    assert x_held[0, -1] == 1.0


def test_synthetic_end_to_end_runs_all_five_folds_and_placebos():
    prepared, contract, declaration, raw = synthetic_state_and_contract()
    result = evaluate_final_endpoint(prepared, raw, contract, declaration)
    assert result["terminal_class"] == "predictive_result"
    assert result["status"] in {
        "favorable_complementary_added_value",
        "adverse_complementary_added_value",
        "no_confirmed_complementary_added_value",
    }
    assert result["candidate_unit_count"] == 30
    assert result["node_count"] == 15
    assert result["total_positive_candidate_units"] == 15
    assert result["total_negative_candidate_units"] == 15
    assert result["heldout_folds_with_both_classes"] == 5
    assert result["primary_model_fits"] == 10
    assert result["placebo_model_fits"] == 100
    assert result["model_fits_total"] == 110
    assert len(result["fold_results"]) == 5
    assert result["emof_full_gets"] == 0
    assert result["emof_full_bytes_opened"] == 0
    assert result["candidate_hunting_hard_stop"] is True
