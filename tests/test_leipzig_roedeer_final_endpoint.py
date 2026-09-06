import copy
import csv
import io
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest

from validation.leipzig_roedeer_endpoint3.final_endpoint import (
    FinalEndpointTerminal,
    _validate_frozen_declaration,
    encode_baseline_fold,
    parse_response_table,
    permute_layer_b_partition,
    training_occurrence_set,
)
from validation.leipzig_roedeer_endpoint3.gate0_pre_response import git_blob_sha1

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "leipzig_roedeer_endpoint3"


def load(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def test_final_contract_is_bound_before_response_rows():
    c = load("final_endpoint_contract.json")
    assert c["attempt_id"] == "leipzig_roedeer_endpoint3_v1"
    assert c["issue"] == 384
    assert c["prerequisites"]["gate0_result_fingerprint"] == "cd34456362a1f35742f7158adb7acbbab928bf125ddd121db274b174fd51855d"
    assert c["prerequisites"]["response_header_result_fingerprint"] == "e3a9620c2e91ce239b160de1d01ed338b9c4f1f648f2ecb846a7b76b2b9558a8"
    assert c["prerequisites"]["response_rows_opened_before_this_contract"] == 0
    assert c["prerequisites"]["response_values_opened_before_this_contract"] is False
    assert c["node_and_split"]["valid_node_count"] == 71
    assert c["worlds"]["max_steps"] == 70
    assert c["layer_b"]["feature_count"] == 10
    assert c["learner"]["n_estimators"] == 500
    assert c["paired_decision"]["favorable_min_augmented_wins"] == 4
    assert c["placebo"]["secondary_only"] is True
    assert len(c["placebo"]["replicate_seeds"]) == 20
    assert c["hard_stop"]["retry_after_full_response_consumption_allowed"] is False


def test_declaration_fingerprints_are_self_consistent():
    _validate_frozen_declaration(load("final_endpoint_declaration.json"))


def test_training_positive_self_exclusion_and_negative_noop():
    nodes = ("A", "B", "C", "D")
    positives = ("A", "C")
    assert training_occurrence_set(positives, "A", nodes) == ("C",)
    assert training_occurrence_set(positives, "B", nodes) == ("A", "C")


def test_baseline_preprocessing_is_calibration_only_and_handles_unseen_category():
    c = load("final_endpoint_contract.json")
    train = [
        {"longitude": 1.0, "latitude": 2.0, "log_effort_days": 3.0, "camera_height": 0.4,
         "deployment_group": "Urban", "TreeDensity": "dense", "VegetationCover": "low", "ForestType": "Deciduous"},
        {"longitude": 2.0, "latitude": 3.0, "log_effort_days": 4.0, "camera_height": None,
         "deployment_group": "Agricultural", "TreeDensity": "open", "VegetationCover": None, "ForestType": "Deciduous"},
        {"longitude": 3.0, "latitude": 4.0, "log_effort_days": 5.0, "camera_height": 0.6,
         "deployment_group": "Urban", "TreeDensity": "dense", "VegetationCover": "high", "ForestType": "Deciduous"},
    ]
    held = [
        {"longitude": 4.0, "latitude": 5.0, "log_effort_days": 6.0, "camera_height": None,
         "deployment_group": "NeverSeen", "TreeDensity": "dense", "VegetationCover": "low", "ForestType": None}
    ]
    x_train, x_held, audit = encode_baseline_fold(train, held, c)
    assert x_train.shape[0] == 3 and x_held.shape[0] == 1
    assert np.isfinite(x_train).all() and np.isfinite(x_held).all()
    assert audit["categorical_levels"]["deployment_group"] == ["Agricultural", "Urban"]
    unseen_index = audit["feature_names"].index("deployment_group__UNSEEN")
    assert x_held[0, unseen_index] == 1.0
    height_index = audit["feature_names"].index("camera_height")
    height_missing_index = audit["feature_names"].index("camera_height__missing")
    assert x_held[0, height_index] == pytest.approx(0.5)
    assert x_held[0, height_missing_index] == 1.0


def test_placebo_permutation_is_seeded_columnwise_and_preserves_marginals():
    train = np.arange(60, dtype=float).reshape(6, 10)
    held = np.arange(40, dtype=float).reshape(4, 10) + 1000
    a_train, a_held = permute_layer_b_partition(train, held, 2026082601)
    b_train, b_held = permute_layer_b_partition(train, held, 2026082601)
    assert np.array_equal(a_train, b_train)
    assert np.array_equal(a_held, b_held)
    for col in range(10):
        assert sorted(a_train[:, col]) == sorted(train[:, col])
        assert sorted(a_held[:, col]) == sorted(held[:, col])
    assert not np.array_equal(a_train, train)


def _response_bytes(header, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _row(header, **values):
    return [str(values.get(name, "")) for name in header]


def synthetic_response_contract(raw):
    c = copy.deepcopy(load("final_endpoint_contract.json"))
    c["source"]["response_table"]["size_bytes"] = len(raw)
    c["source"]["response_table"]["git_blob_sha1"] = git_blob_sha1(raw)
    return c


def test_response_parser_maps_focal_ever_detection_only_to_frozen_retained_nodes():
    c0 = load("final_endpoint_contract.json")
    header = c0["response_parser"]["header_exact_order"]
    rows = [
        _row(header, observationID="1", deploymentID="depA", eventStart="2024-03-01T12:00:00+01:00",
             eventEnd="2024-03-01T12:01:00+01:00", scientificName="Capreolus capreolus"),
        _row(header, observationID="2", deploymentID="depB", eventStart="2024-03-02T12:00:00+01:00",
             eventEnd="2024-03-02T12:01:00+01:00", scientificName="Vulpes vulpes"),
        _row(header, observationID="3", deploymentID="depX", eventStart="2024-03-03T12:00:00+01:00",
             eventEnd="2024-03-03T12:01:00+01:00", scientificName="Capreolus capreolus"),
    ]
    raw = _response_bytes(header, rows)
    c = synthetic_response_contract(raw)
    linkage = {
        "depA": {"location_id": "A", "start": datetime.fromisoformat("2024-02-01T00:00:00+01:00"), "end": datetime.fromisoformat("2024-04-01T00:00:00+01:00")},
        "depB": {"location_id": "B", "start": datetime.fromisoformat("2024-02-01T00:00:00+01:00"), "end": datetime.fromisoformat("2024-04-01T00:00:00+01:00")},
        "depX": {"location_id": "EXCLUDED", "start": datetime.fromisoformat("2024-02-01T00:00:00+01:00"), "end": datetime.fromisoformat("2024-04-01T00:00:00+01:00")},
    }
    labels, audit = parse_response_table(raw, linkage, ("A", "B"), c)
    assert labels == {"A": 1, "B": 0}
    assert audit["focal_rows_at_retained_locations"] == 1
    assert audit["focal_rows_at_excluded_locations"] == 1


def test_response_parser_stops_on_unknown_deployment_or_out_of_interval_focal():
    c0 = load("final_endpoint_contract.json")
    header = c0["response_parser"]["header_exact_order"]
    unknown = _response_bytes(header, [
        _row(header, deploymentID="unknown", eventStart="2024-03-01T12:00:00+01:00",
             eventEnd="2024-03-01T12:01:00+01:00", scientificName="Vulpes vulpes")
    ])
    with pytest.raises(FinalEndpointTerminal, match="deploymentID"):
        parse_response_table(unknown, {}, ("A",), synthetic_response_contract(unknown))

    outside = _response_bytes(header, [
        _row(header, deploymentID="depA", eventStart="2025-03-01T12:00:00+01:00",
             eventEnd="2025-03-01T12:01:00+01:00", scientificName="Capreolus capreolus")
    ])
    linkage = {"depA": {"location_id": "A", "start": datetime.fromisoformat("2024-02-01T00:00:00+01:00"), "end": datetime.fromisoformat("2024-04-01T00:00:00+01:00")}}
    with pytest.raises(FinalEndpointTerminal, match="outside raw deployment"):
        parse_response_table(outside, linkage, ("A",), synthetic_response_contract(outside))
