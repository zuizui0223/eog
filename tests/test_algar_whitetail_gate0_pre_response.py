from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from validation.algar_whitetail_endpoint3 import gate0_pre_response as gate


def _csv(header: list[str], rows: list[list[object]]) -> bytes:
    def cell(value: object) -> str:
        text = str(value)
        if any(ch in text for ch in [',', '"', '\n']):
            return '"' + text.replace('"', '""') + '"'
        return text

    return (",".join(header) + "\n" + "\n".join(
        ",".join(cell(value) for value in row) for row in rows
    ) + "\n").encode("utf-8")


def _five_fold_names() -> list[str]:
    by_fold: dict[int, str] = {}
    i = 1
    while len(by_fold) < 5:
        name = f"ALG{i:03d}"
        by_fold.setdefault(gate._fold(name), name)
        i += 1
    return [by_fold[k] for k in sorted(by_fold)]


def _fixture() -> tuple[dict[str, object], dict[str, bytes], list[str]]:
    names = _five_fold_names()
    contract: dict[str, object] = {
        "attempt_id": "synthetic_algar",
        "issue": 378,
        "source": {
            "repository": "example/repo",
            "commit": "abc",
            "safe_files": {},
        },
        "source_identity": {
            "project_id": "AlgarRestorationProject",
            "project_short_name": "Algar",
            "focal_common_name": "white-tailed deer",
            "focal_species_identifier": "Odocoileus.virginianus",
        },
        "safe_schema": {
            "deployment_required_columns": [
                "project_id", "deployment_id", "placename", "longitude", "latitude",
                "start_date", "end_date", "camera_functioning",
            ],
            "camera_required_columns": ["project_id", "camera_id", "camera_name"],
            "project_required_columns": ["project_id", "project_name", "project_short_name"],
            "local_covariate_exact_columns": ["placename", "line_of_sight_m"],
            "common_names_exact_columns": ["common_name", "sp"],
        },
        "deployment_registry": {
            "valid_operational_status": "camera_functioning == Camera Functioning",
        },
        "candidate_registry": {
            "first_candidate_week_start": "2019-01-07",
            "last_candidate_week_start": "2019-02-04",
            "minimum_unique_nodes": 5,
            "minimum_candidate_units": 20,
            "minimum_distinct_contexts": 5,
        },
        "world_geometry": {
            "component_id": "AlgarRestorationProject",
            "threshold_quantiles": [0.25, 0.50, 0.75, 0.90],
            "minimum_distinct_positive_local_worlds": 3,
        },
        "baseline": {
            "required_fields": [
                {"name": "longitude", "kind": "numeric", "missing_policy": "forbid"},
                {"name": "latitude", "kind": "numeric", "missing_policy": "forbid"},
                {"name": "week_index", "kind": "numeric", "missing_policy": "forbid"},
            ],
            "optional_fields": [
                {"name": "line_of_sight_m", "kind": "numeric", "missing_policy": "calibration_median_plus_indicator"},
            ],
        },
        "observation_semantics": {
            "effort_eligible_rule": "complete seven-day operational week",
            "positive_rule": "one or more focal images",
            "negative_rule": "zero focal images in eligible week",
            "unsurveyed_rule": "incomplete week is not a candidate",
            "zero_interpretation": "recorded non-detection",
        },
        "gate0_firewall": {"maximum_safe_file_bytes_total": 100000},
    }

    deployments_header = [
        "project_id", "deployment_id", "placename", "longitude", "latitude",
        "start_date", "end_date", "camera_functioning",
    ]
    deployment_rows: list[list[object]] = []
    for i, name in enumerate(names):
        deployment_rows.append([
            "AlgarRestorationProject", f"D{i}", name,
            -112.0 + i * 0.1, 56.0 + i * 0.05,
            "2019-01-01", "2019-02-12", "Camera Functioning",
        ])
    payloads = {
        "deployments": _csv(deployments_header, deployment_rows),
        "cameras": _csv(
            ["project_id", "camera_id", "camera_name"],
            [["AlgarRestorationProject", str(i + 1), f"C{i + 1}"] for i in range(5)],
        ),
        "projects": _csv(
            ["project_id", "project_name", "project_short_name"],
            [["AlgarRestorationProject", "AlgarRestorationProject", "Algar"]],
        ),
        # Deliberately omit one candidate node and use NA for another: optional baseline
        # missingness must not stop the response-blind registry.
        "local_covariate": _csv(
            ["placename", "line_of_sight_m"],
            [[names[0], 100], [names[1], "NA"], [names[2], 200], [names[3], 300]],
        ),
        "common_names": _csv(
            ["common_name", "sp"],
            [["white-tailed deer", "Odocoileus.virginianus"], ["coyote", "Canis.latrans"]],
        ),
    }
    safe_files: dict[str, object] = {}
    for role, raw in payloads.items():
        safe_files[role] = {
            "size_bytes": len(raw),
            "git_blob_sha1": gate.git_blob_sha1(raw),
            "raw_url": f"https://raw.githubusercontent.com/example/repo/abc/{role}.csv",
        }
    contract["source"]["safe_files"] = safe_files
    return contract, payloads, names


def test_interval_union_merges_adjacent_half_open_deployments():
    from datetime import date

    values = [
        (date(2019, 1, 1), date(2019, 1, 10)),
        (date(2019, 1, 10), date(2019, 1, 20)),
        (date(2019, 2, 1), date(2019, 2, 2)),
    ]
    assert gate.union_intervals(values) == [
        (date(2019, 1, 1), date(2019, 1, 20)),
        (date(2019, 2, 1), date(2019, 2, 2)),
    ]


def test_gate0_emits_normalized_problem_and_all_five_folds():
    contract, payloads, names = _fixture()
    result = gate.evaluate_pre_response(payloads, contract)
    assert result["status"] == "gate0_pre_response_ready"
    assert result["candidate_node_count"] == 5
    assert result["candidate_unit_count"] == 25
    assert result["context_count"] == 5
    assert sorted(int(k) for k in result["site_fold_counts"]) == [1, 2, 3, 4, 5]
    assert set(result["site_fold_counts"].values()) == {1}
    assert result["normalized_problem"]["response_locked"] is True
    assert result["normalized_problem"]["node_count"] == len(names)
    assert result["normalized_problem"]["candidate_unit_count"] == 25
    assert result["images_requests"] == 0
    assert result["images_values_opened"] is False
    assert result["model_fits"] == result["heldout_scores"] == 0


def test_optional_line_of_sight_missingness_does_not_stop_gate0():
    contract, payloads, _ = _fixture()
    result = gate.evaluate_pre_response(payloads, contract)
    audit = result["optional_baseline_audit"]
    assert audit["candidate_nodes_missing_or_nonnumeric_line_of_sight"] == 2
    assert audit["missing_policy"] == "calibration_median_plus_indicator"
    assert audit["missingness_causes_gate0_stop"] is False


def test_structural_coordinate_drift_stops():
    contract, payloads, names = _fixture()
    header, rows = gate._csv_rows(payloads["deployments"], "synthetic")
    extra = dict(rows[0])
    extra["deployment_id"] = "extra"
    extra["longitude"] = str(float(extra["longitude"]) + 0.01)
    rebuilt = _csv(header, [[row[column] for column in header] for row in [*rows, extra]])
    payloads = dict(payloads)
    payloads["deployments"] = rebuilt
    source = contract["source"]["safe_files"]["deployments"]
    source["size_bytes"] = len(rebuilt)
    source["git_blob_sha1"] = gate.git_blob_sha1(rebuilt)
    with pytest.raises(gate.Gate0Stop, match=f"coordinate drift across deployments for {names[0]}"):
        gate.evaluate_pre_response(payloads, contract)


def test_source_blob_drift_stops_before_interpretation():
    contract, payloads, _ = _fixture()
    payloads = dict(payloads)
    payloads["projects"] = payloads["projects"] + b"x"
    with pytest.raises(gate.Gate0Stop, match="projects byte-size drift"):
        gate.evaluate_pre_response(payloads, contract)


def test_runner_requests_only_five_safe_files_and_never_images(tmp_path: Path):
    contract, payloads, _ = _fixture()
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "certificate.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    by_url = {
        contract["source"]["safe_files"][role]["raw_url"]: raw
        for role, raw in payloads.items()
    }
    requested: list[str] = []

    def fetch(url: str, maximum: int) -> bytes:
        requested.append(url)
        raw = by_url[url]
        assert len(raw) <= maximum
        return raw

    result = gate.run(contract_path, output_path, fetch)
    assert result["status"] == "gate0_pre_response_ready"
    assert len(requested) == 5
    assert set(requested) == set(by_url)
    assert all("images" not in url for url in requested)
    assert result["images_requests"] == 0
    assert result["images_header_bytes_opened"] == 0
    assert result["images_payload_bytes_opened"] == 0
    assert result["images_rows_opened"] == 0
    assert result["images_values_opened"] is False
    assert json.loads(output_path.read_text())["fingerprint"] == result["fingerprint"]
