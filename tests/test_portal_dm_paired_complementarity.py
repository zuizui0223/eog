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
RUNNER_PATH = ROOT / "benchmarks/run_portal_dm_paired_complementarity_once.py"
CONTRACT_PATH = ROOT / "validation/portal_dm_paired_complementarity/source_contract.json"


def load_runner():
    name = "portal_dm_paired_runner_test"
    spec = importlib.util.spec_from_file_location(name, RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_response_object_cannot_cross_nonresponse_firewall():
    validation = CONTRACT_PATH.parent
    spec = importlib.util.spec_from_file_location(
        "portal_dm_transport_test", validation / "transport.py"
    )
    assert spec is not None and spec.loader is not None
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    frozen = contract()
    audit = {"nonresponse_download_requests": [], "opened_nonresponse_files": []}
    with pytest.raises(RuntimeError, match="non-admitted object"):
        transport.download_nonresponse(frozen["response_file"], frozen, audit)


def test_frozen_physical_header_revalidates_without_aliases():
    runner = load_runner()
    frozen = contract()
    header = frozen["response_header_firewall"]["expected_header_text"].encode()
    result = runner.validate_physical_header(header + b"\n1,2,3\n", frozen)
    assert result["matches_pre_response_bounded_header"] is True
    assert result["terminator"] == "LF"
    assert result["bytes_consumed_including_terminator"] == 257

    changed = header.replace(b"prevlet", b"prevlt")
    with pytest.raises(RuntimeError, match="header text differs"):
        runner.validate_physical_header(changed + b"\n1,2,3\n", frozen)


def test_exact_count_gate_is_first_outcome_dependent_operation():
    runner = load_runner()
    frozen = copy.deepcopy(contract())
    for key in (
        "calibration_events",
        "calibration_non_events",
        "heldout_events",
        "heldout_non_events",
        "heldout_outer_units_with_both_classes",
        "heldout_outer_units_with_rows",
    ):
        frozen["freezes"]["count_gate"][key] = 1

    node_ids = tuple(f"plot_{index:02d}" for index in range(1, 25))
    coordinates = np.column_stack((np.arange(24, dtype=float), np.zeros(24)))
    distance = np.abs(coordinates[:, 0, None] - coordinates[:, 0])
    effort = {
        (period, plot): runner.EffortCell(date(2011 + period, 1, 1), 49, True)
        for period in (1, 2, 3)
        for plot in range(1, 25)
    }
    transitions = (
        runner.Transition(1, 1, 2, date(2011, 1, 1), date(2011, 2, 1), tuple(range(24)), "calibration"),
        runner.Transition(2, 2, 3, date(2011, 2, 1), date(2012, 1, 1), tuple(range(24)), "heldout"),
    )
    static = runner.StaticInputs(
        node_ids=node_ids,
        coordinates=coordinates,
        distance=distance,
        worlds={},
        thresholds=np.asarray([2.0, 4.0, 8.0]),
        kernel_scale=4.0,
        effort=effort,
        moon_by_period={1: (1, date(2011, 1, 1)), 2: (2, date(2011, 2, 1)), 3: (3, date(2012, 1, 1))},
        ordered_periods=(1, 2, 3),
        treatments={},
        transitions=transitions,
    )
    counts = {
        1: np.asarray([1 if index % 3 == 0 else 0 for index in range(24)]),
        2: np.asarray([1 if index % 3 == 1 else 0 for index in range(24)]),
        3: np.asarray([1 if index % 3 == 2 else 0 for index in range(24)]),
    }
    result = runner.exact_count_gate(counts, static, frozen)
    assert result["passed"] is True
    assert result["outcome_dependent_operation_index"] == 1
    assert result["executed_before_any_layer_a_update_or_model_fit"] is True


def test_same_learner_pair_differs_only_by_unchanged_layer_b():
    runner = load_runner()
    frozen = copy.deepcopy(contract())
    frozen["freezes"]["preprocessing_model_fit"]["hyperparameters"]["n_estimators"] = 20
    rng = np.random.default_rng(20260822)
    rows = []
    for index in range(160):
        baseline = rng.normal(size=len(runner.BASELINE_FEATURE_NAMES))
        layer_b = rng.normal(size=len(runner.PREDICTIVE_FEATURE_NAMES))
        rows.append(
            runner.RiskRow(
                phase="calibration",
                outer_unit_id="calibration",
                newmoonnumber=index,
                source_period=index,
                target_period=index + 1,
                target_year=2011,
                node_index=index % 24,
                label=index % 2,
                baseline=tuple(baseline),
                layer_b=tuple(layer_b),
            )
        )
    for year in range(2012, 2020):
        for label in (0, 1, 0, 1):
            baseline = rng.normal(size=len(runner.BASELINE_FEATURE_NAMES))
            layer_b = rng.normal(size=len(runner.PREDICTIVE_FEATURE_NAMES))
            rows.append(
                runner.RiskRow(
                    phase="heldout",
                    outer_unit_id=f"year_{year}",
                    newmoonnumber=year,
                    source_period=year,
                    target_period=year + 1,
                    target_year=year,
                    node_index=label,
                    label=label,
                    baseline=tuple(baseline),
                    layer_b=tuple(layer_b),
                )
            )
    result, state = runner.fit_and_score(rows, frozen)
    assert state["status"] == "completed"
    assert result["models_fit"] == 2
    assert result["heldout_scores"] == 16
    audit = result["model_feature_audit"]
    assert audit["only_augmented_difference"] == list(runner.PREDICTIVE_FEATURE_NAMES)
    assert audit["exact_plot_id_supervised"] is False
    assert audit["exact_world_id_supervised"] is False
    assert len(audit["augmented_feature_names"]) == len(audit["baseline_feature_names"]) + 10
