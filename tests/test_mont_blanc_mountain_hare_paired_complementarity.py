from __future__ import annotations

import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


pytest.importorskip("sklearn")


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    ROOT / "benchmarks/run_mont_blanc_mountain_hare_paired_complementarity_once.py"
)
CONTRACT_PATH = (
    ROOT
    / "validation/mont_blanc_mountain_hare_paired_complementarity/source_contract.json"
)


def load_runner():
    name = "mont_blanc_mountain_hare_paired_runner_test"
    spec = importlib.util.spec_from_file_location(name, RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def synthetic_static(runner, frozen: dict):
    count = 46
    node_ids = tuple(f"station_{index:02d}" for index in range(count))
    xy = np.asarray(
        [[400.0 * (index % 8), 400.0 * (index // 8)] for index in range(count)]
    )
    delta = xy[:, None, :] - xy[None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    coordinates = np.column_stack(
        (6.8 + xy[:, 0] / 80_000.0, 45.8 + xy[:, 1] / 111_000.0)
    )
    attributes = {
        "elevation": np.linspace(1200.0, 2400.0, count),
        "slope": np.linspace(5.0, 40.0, count),
        "setup_dates": tuple(date(2018, 1, 1) for _ in range(count)),
        "aspect": tuple(("NO", "S", "SE", "SO", "O")[index % 5] for index in range(count)),
        "habitat": tuple(
            ("forest", "shrubland", "grassland", "prairie", "shrubland sur crete")[
                index % 5
            ]
            for index in range(count)
        ),
        "model": tuple(
            frozen["freezes"]["preprocessing_model_fit"]["model_tokens"][index % 5]
            for index in range(count)
        ),
    }
    return runner.StaticInputs(
        node_ids=node_ids,
        attributes=attributes,
        coordinates=coordinates,
        distance=distance,
        active_days=np.full((count, 42), 30.0),
        thresholds=np.asarray(frozen["freezes"]["world_scale"]["thresholds_m"]),
        kernel_scale=float(frozen["freezes"]["world_scale"]["kernel_scale_m"]),
    )


def test_forbidden_ancillary_object_cannot_cross_nonresponse_firewall():
    validation = CONTRACT_PATH.parent
    spec = importlib.util.spec_from_file_location(
        "mont_blanc_hare_transport_test", validation / "transport.py"
    )
    assert spec is not None and spec.loader is not None
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    frozen = contract()
    with pytest.raises(RuntimeError, match="non-admitted object"):
        transport.download_nonresponse_member("out_contact.csv", frozen, {}, {})


def test_physical_header_and_duplicate_identity_policy_are_exact():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    content = (
        b"Station;Date\r\n"
        b"station_00;01/01/2019\r\n"
        b"station_00;01/01/2019\r\n"
        b"station_01;2019-02-02\r\n"
    )
    records, audit = runner.parse_response(content, static, frozen)
    assert len(records) == 2
    assert audit["raw_row_count"] == 3
    assert audit["exact_duplicate_rows_collapsed"] == 1
    assert audit["physical_header"]["terminator"] == "CR"
    assert audit["physical_header"]["bytes_consumed_including_terminator"] == 13


def test_exact_count_gate_precedes_layer_a_and_fits():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    synthetic = runner.synthetic_response(static)
    counts, _, _ = runner.exact_count_gate(None, static, frozen, synthetic=synthetic)
    assert counts["passed"] is True
    assert counts["executed_before_any_layer_a_update_or_model_fit"] is True
    assert counts["heldout_outer_units_with_rows"] == 6
    assert counts["heldout_outer_units_with_both_classes"] == 6


def test_same_learner_pair_differs_only_by_unchanged_layer_b():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    synthetic = runner.synthetic_response(static)
    counts, state_matrix, contact_days = runner.exact_count_gate(
        None, static, frozen, synthetic=synthetic
    )
    assert counts["passed"] is True
    rows, row_audit = runner.build_risk_rows(
        state_matrix, contact_days, static, frozen
    )
    assert row_audit["exact_site_id_supervised"] is False
    assert row_audit["exact_world_id_supervised"] is False

    technical = copy.deepcopy(frozen)
    technical["freezes"]["preprocessing_model_fit"]["hyperparameters"][
        "n_estimators"
    ] = 20
    result, status = runner.fit_and_score(rows, technical)
    assert status["status"] == "completed"
    assert result["models_fit"] == 2
    assert result["heldout_scores"] == 12
    audit = result["model_feature_audit"]
    assert audit["only_augmented_difference"] == list(runner.PREDICTIVE_FEATURE_NAMES)
    assert audit["exact_site_id_supervised"] is False
    assert audit["exact_world_id_supervised"] is False
    assert len(audit["augmented_feature_names"]) == len(audit["baseline_feature_names"]) + 10
