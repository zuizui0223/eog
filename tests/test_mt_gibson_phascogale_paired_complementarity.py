from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "benchmarks/run_mt_gibson_phascogale_paired_complementarity_once.py"
CONTRACT_PATH = (
    ROOT
    / "validation/mt_gibson_phascogale_paired_complementarity/source_contract.json"
)


def load_runner():
    name = "mt_gibson_phascogale_paired_runner_test"
    spec = importlib.util.spec_from_file_location(name, RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_ancillary_capture_response_is_not_a_nonresponse_input():
    validation = CONTRACT_PATH.parent
    spec = importlib.util.spec_from_file_location(
        "mt_gibson_transport_test", validation / "transport.py"
    )
    assert spec is not None and spec.loader is not None
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    frozen = contract()
    try:
        transport.download_nonresponse_member(
            "Arboreal_trapping_capture_data.csv", frozen, {}, {}
        )
    except RuntimeError as exc:
        assert "non-admitted object" in str(exc)
    else:
        raise AssertionError("ancillary capture response crossed the firewall")


def synthetic_static(runner, frozen: dict):
    node_ids = tuple(f"site_{index:02d}" for index in range(70))
    coordinates = np.asarray(
        [[500.0 * (index % 10), 500.0 * (index // 10)] for index in range(70)]
    )
    delta = coordinates[:, None, :] - coordinates[None, :, :]
    distance = np.sqrt(np.sum(delta * delta, axis=2))
    return runner.StaticInputs(
        node_ids=node_ids,
        coordinates=coordinates,
        distance=distance,
        deployment_intervals={},
        effort_days=np.full((70, 7), 24.0),
        campaign_mid_day=np.tile(np.arange(7, dtype=float), (70, 1)) + 100.0,
        thresholds=np.asarray(frozen["freezes"]["world_scale"]["thresholds_m"]),
        kernel_scale=float(frozen["freezes"]["world_scale"]["kernel_scale_m"]),
    )


def test_frozen_physical_header_revalidates_without_aliases():
    runner = load_runner()
    frozen = contract()
    header = frozen["response_header_firewall"]["expected_header_text"].encode()
    content = header + b"\r\n01/01/2020,site_00\r\n"
    result = runner.validate_physical_header(content, frozen)
    assert result["matches_pre_response_bounded_header"] is True
    assert result["terminator"] == "CR"
    assert result["bytes_consumed_including_terminator"] == 27


def test_exact_count_gate_precedes_layer_a_and_fits():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    synthetic = runner.synthetic_response(static)
    counts, _, _ = runner.exact_count_gate(
        None, static, frozen, synthetic=synthetic
    )
    assert counts["passed"] is True
    assert counts["executed_before_any_layer_a_update_or_model_fit"] is True
    assert counts["heldout_outer_units_with_rows"] == 2
    assert counts["heldout_outer_units_with_both_classes"] == 2


def test_same_learner_pair_differs_only_by_unchanged_layer_b():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    synthetic = runner.synthetic_response(static)
    counts, state_matrix, detection_days = runner.exact_count_gate(
        None, static, frozen, synthetic=synthetic
    )
    assert counts["passed"] is True
    rows, row_audit = runner.build_risk_rows(
        state_matrix, detection_days, static, frozen
    )
    assert row_audit["exact_site_id_supervised"] is False
    assert row_audit["exact_world_id_supervised"] is False

    technical = copy.deepcopy(frozen)
    technical["freezes"]["preprocessing_model_fit"]["hyperparameters"][
        "n_estimators"
    ] = 20
    result, state = runner.fit_and_score(rows, technical)
    assert state["status"] == "completed"
    assert result["models_fit"] == 2
    assert result["heldout_scores"] == 4
    audit = result["model_feature_audit"]
    assert audit["only_augmented_difference"] == list(runner.PREDICTIVE_FEATURE_NAMES)
    assert audit["exact_site_id_supervised"] is False
    assert audit["exact_world_id_supervised"] is False
    assert len(audit["augmented_feature_names"]) == len(
        audit["baseline_feature_names"]
    ) + 10
