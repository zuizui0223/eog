from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "benchmarks/run_yale_myers_woodfrog_paired_complementarity_once.py"
CONTRACT_PATH = (
    ROOT
    / "validation/yale_myers_woodfrog_paired_complementarity/source_contract.json"
)


def load_runner():
    name = "yale_myers_woodfrog_paired_runner_test"
    spec = importlib.util.spec_from_file_location(name, RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def synthetic_static(runner, frozen: dict):
    node_ids = tuple(f"pond_{index:02d}" for index in range(64))
    positions = np.arange(64, dtype=float) * 75.0
    distance = np.abs(positions[:, None] - positions[None, :])
    return runner.StaticInputs(
        node_ids=node_ids,
        distance=distance,
        area=np.linspace(24.0, 41361.0, 64),
        canopy=np.linspace(0.0, 98.0, 64),
        thresholds=np.asarray(frozen["freezes"]["world_scale"]["thresholds_m"]),
        kernel_scale=float(frozen["freezes"]["world_scale"]["kernel_scale_m"]),
    )


def test_frozen_physical_header_revalidates_without_aliases():
    runner = load_runner()
    frozen = contract()
    header = frozen["response_header_firewall"]["expected_header_text"].encode()
    content = header + b"\r\nA10,2000,40,0,0,0,50,0,NA,NA,40,0,0,0\r\n"
    result = runner.validate_physical_header(content, frozen)
    assert result["matches_pre_response_bounded_header"] is True
    assert result["terminator"] == "CR"
    assert result["bytes_consumed_including_terminator"] == 138


def test_exact_count_gate_precedes_layer_a_and_fits():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    records = runner.synthetic_response(static)
    counts = runner.exact_count_gate(records, static, frozen)
    assert counts["passed"] is True
    assert counts["executed_before_any_layer_a_update_or_model_fit"] is True
    assert counts["heldout_outer_units_with_rows"] == 9
    assert counts["heldout_outer_units_with_both_classes"] == 9


def test_same_learner_pair_differs_only_by_unchanged_layer_b():
    runner = load_runner()
    frozen = contract()
    static = synthetic_static(runner, frozen)
    records = runner.synthetic_response(static)
    assert runner.exact_count_gate(records, static, frozen)["passed"] is True
    rows, row_audit = runner.build_risk_rows(records, static, frozen)
    assert row_audit["exact_pond_id_supervised"] is False
    assert row_audit["exact_world_id_supervised"] is False

    technical = copy.deepcopy(frozen)
    technical["freezes"]["preprocessing_model_fit"]["hyperparameters"][
        "n_estimators"
    ] = 20
    result, state = runner.fit_and_score(rows, technical)
    assert state["status"] == "completed"
    assert result["models_fit"] == 2
    assert result["heldout_scores"] == 18
    audit = result["model_feature_audit"]
    assert audit["only_augmented_difference"] == list(runner.PREDICTIVE_FEATURE_NAMES)
    assert audit["exact_pond_id_supervised"] is False
    assert audit["exact_world_id_supervised"] is False
    assert len(audit["augmented_feature_names"]) == len(
        audit["baseline_feature_names"]
    ) + 10
