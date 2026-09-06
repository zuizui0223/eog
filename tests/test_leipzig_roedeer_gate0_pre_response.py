from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from datetime import datetime
from pathlib import Path

import pytest

from validation.leipzig_roedeer_endpoint3.gate0_pre_response import (
    Gate0Stop,
    _fold,
    derive_world_family,
    freeze_from_safe_bytes,
    git_blob_sha1,
    interval_effort_days,
    parse_deployments,
    parse_source_code,
    run,
    union_intervals,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation" / "leipzig_roedeer_endpoint3" / "source_contract.json"


def _csv_bytes(header: list[str], rows: list[list[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _source_code_bytes() -> bytes:
    return b'''# frozen synthetic source\n# Change year to 2024\nspecies_of_interest <- c("Capreolus capreolus", "Martes", "Felis silvestris", "Sus scrofa", "Procyon lotor", "Meles meles", "Vulpes vulpes")\n# LE39 manual correction exists in source but EOG must not apply it\n'''


def _deployment_bytes(n: int = 65, *, short_index: int | None = None) -> bytes:
    header = [
        "deploymentID", "locationID", "locationName", "latitude", "longitude",
        "deploymentStart", "deploymentEnd", "cameraHeight", "deploymentGroups",
    ]
    rows: list[list[object]] = []
    for i in range(n):
        start = "2023-03-01T00:00:00+01:00" if i == 0 else "2024-03-01T00:00:00+01:00"
        if i == short_index:
            end = "2024-03-10T00:00:00+01:00"
        elif i == 0:
            end = "2023-04-01T00:00:00+02:00"
        else:
            end = "2024-04-01T00:00:00+02:00"
        rows.append(
            [
                f"dep-{i:03d}", f"loc-{i:03d}", "LE39" if i == 0 else f"LE{i+1}",
                51.0 + i * 0.001, 12.0 + i * 0.0015,
                start, end, "0.45" if i % 7 else "", "Urban Matrix" if i % 2 else "Agricultural Matrix",
            ]
        )
    return _csv_bytes(header, rows)


def _covariate_bytes(n: int = 12) -> bytes:
    header = ["locationName", "TreeDensity", "VegetationCover", "ForestType"]
    rows = [
        ["LE39" if i == 0 else f"LE{i+1}", "mid", "low" if i % 2 else "high", "Deciduous"]
        for i in range(n)
    ]
    return _csv_bytes(header, rows)


def _contract(
    deployments: bytes,
    covariates: bytes,
    source_code: bytes,
    *,
    minimum_locations: int = 60,
    minimum_effort_days: float = 20.0,
) -> dict[str, object]:
    contract = copy.deepcopy(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    payloads = {
        "deployments": deployments,
        "covariates": covariates,
        "source_code": source_code,
    }
    for role, payload in payloads.items():
        entry = contract["source"]["safe_files"][role]
        entry["size_bytes"] = len(payload)
        entry["git_blob_sha1"] = git_blob_sha1(payload)
        entry["raw_url"] = f"https://raw.githubusercontent.com/example/repo/frozen/{role}.txt"
    contract["source"]["forbidden_response"]["raw_url"] = (
        "https://raw.githubusercontent.com/example/repo/frozen/observations.csv"
    )
    contract["deployment_registry"]["minimum_stable_locations"] = minimum_locations
    contract["deployment_registry"]["minimum_effort_days_per_retained_location"] = minimum_effort_days
    return contract


def test_git_blob_sha1_uses_exact_git_object_framing():
    payload = b"abc\n"
    expected = hashlib.sha1(b"blob 4\0abc\n").hexdigest()
    assert git_blob_sha1(payload) == expected


def test_source_vector_freezes_roe_deer_first_and_records_but_does_not_apply_repairs():
    source = _source_code_bytes()
    contract = _contract(_deployment_bytes(), _covariate_bytes(), source)
    audit = parse_source_code(source, contract)
    assert audit["focal_taxon"] == "Capreolus capreolus"
    assert audit["focal_vector"][0] == "Capreolus capreolus"
    assert audit["source_contains_year_rewrite_logic"] is True
    assert audit["source_contains_LE39_manual_repair"] is True
    assert audit["eog_applies_year_rewrite"] is False
    assert audit["eog_applies_LE39_manual_repair"] is False


def test_raw_year_and_LE39_timestamp_are_preserved_without_source_repair():
    deployments = _deployment_bytes(n=1)
    contract = _contract(deployments, _covariate_bytes(), _source_code_bytes(), minimum_locations=1)
    registry, audit = parse_deployments(deployments, contract)
    assert audit["raw_start_year_counts"] == {"2023": 1}
    assert audit["raw_year_values_preserved"] is True
    assert audit["LE39_manual_repair_applied"] is False
    assert registry["loc-000"]["location_name"] == "LE39"
    assert registry["loc-000"]["merged_intervals"][0][0].startswith("2023-02-28T23:00:00+00:00")


def test_coordinate_drift_for_same_location_id_fails_closed():
    header = [
        "deploymentID", "locationID", "locationName", "latitude", "longitude",
        "deploymentStart", "deploymentEnd", "cameraHeight", "deploymentGroups",
    ]
    rows = [
        ["d1", "loc", "LE1", 51.0, 12.0, "2024-01-01T00:00:00+01:00", "2024-02-01T00:00:00+01:00", 0.4, "Urban Matrix"],
        ["d2", "loc", "LE1", 51.0, 12.000001, "2024-02-01T00:00:00+01:00", "2024-03-01T00:00:00+01:00", 0.4, "Urban Matrix"],
    ]
    deployments = _csv_bytes(header, rows)
    contract = _contract(deployments, _covariate_bytes(), _source_code_bytes(), minimum_locations=1)
    with pytest.raises(Gate0Stop, match="coordinate drift"):
        parse_deployments(deployments, contract)


def test_empty_structural_id_fails_closed():
    deployments = _deployment_bytes(n=1).replace(b"loc-000", b"       ", 1)
    contract = _contract(deployments, _covariate_bytes(), _source_code_bytes(), minimum_locations=1)
    with pytest.raises(Gate0Stop, match="locationID"):
        parse_deployments(deployments, contract)


def test_interval_union_merges_overlapping_or_adjacent_effort_without_calendar_repair():
    values = [
        (datetime.fromisoformat("2024-01-01T00:00:00+01:00"), datetime.fromisoformat("2024-01-11T00:00:00+01:00")),
        (datetime.fromisoformat("2024-01-10T00:00:00+01:00"), datetime.fromisoformat("2024-01-21T00:00:00+01:00")),
        (datetime.fromisoformat("2024-01-21T00:00:00+01:00"), datetime.fromisoformat("2024-01-26T00:00:00+01:00")),
    ]
    merged = union_intervals(values)
    assert len(merged) == 1
    assert interval_effort_days(values) == pytest.approx(25.0)


def test_effort_threshold_excludes_short_location_response_blindly():
    deployments = _deployment_bytes(n=65, short_index=10)
    contract = _contract(deployments, _covariate_bytes(), _source_code_bytes(), minimum_locations=60)
    registry, audit = parse_deployments(deployments, contract)
    assert "loc-010" not in registry
    assert audit["excluded_below_effort_count"] == 1
    assert audit["retained_location_count"] == 64


def test_full_synthetic_gate_freezes_all_folds_worlds_and_optional_covariate_missingness():
    deployments = _deployment_bytes(n=65)
    covariates = _covariate_bytes(n=8)
    source = _source_code_bytes()
    contract = _contract(deployments, covariates, source)
    frozen = freeze_from_safe_bytes(deployments, covariates, source, contract)
    assert frozen["candidate_node_count"] == 65
    assert set(frozen["site_fold_counts"]) == {"1", "2", "3", "4", "5"}
    assert len(frozen["world_family"]["local_worlds"]) >= 3
    assert frozen["normalized_problem"]["response_locked"] is True
    assert frozen["normalized_problem"]["schema"] == "eog.normalized_pre_response_problem.v1"
    missing_rows = [row for row in frozen["baseline_rows"] if row["TreeDensity"] is None]
    assert missing_rows
    assert any(field["missing_policy"] == "explicit_missing_category" for field in frozen["normalized_problem"]["baseline_fields"])


def test_world_family_fingerprint_is_repeatable_for_frozen_node_order():
    deployments = _deployment_bytes(n=65)
    contract = _contract(deployments, _covariate_bytes(), _source_code_bytes())
    registry, _ = parse_deployments(deployments, contract)
    nodes = sorted(registry)
    a = derive_world_family(nodes, registry, contract)
    b = derive_world_family(nodes, registry, contract)
    assert a["fingerprint"] == b["fingerprint"]
    assert [row["graph_fingerprint"] for row in a["local_worlds"]] == [
        row["graph_fingerprint"] for row in b["local_worlds"]
    ]


def test_fold_rule_is_stable_and_spans_all_five_for_synthetic_registry():
    folds = {_fold(f"loc-{i:03d}") for i in range(65)}
    assert folds == {1, 2, 3, 4, 5}
    assert _fold("loc-001") == _fold("loc-001")


def test_gate0_run_fetches_only_three_safe_urls_and_never_observations(tmp_path: Path):
    deployments = _deployment_bytes(n=65)
    covariates = _covariate_bytes(n=8)
    source = _source_code_bytes()
    contract = _contract(deployments, covariates, source)
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "certificate.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    payload_by_url = {
        contract["source"]["safe_files"]["deployments"]["raw_url"]: deployments,
        contract["source"]["safe_files"]["covariates"]["raw_url"]: covariates,
        contract["source"]["safe_files"]["source_code"]["raw_url"]: source,
    }
    calls: list[str] = []

    def fake_fetcher(url: str, expected_size: int) -> bytes:
        calls.append(url)
        assert "observations" not in url
        payload = payload_by_url[url]
        assert len(payload) == expected_size
        return payload

    result = run(contract_path, output_path, fetcher=fake_fetcher)
    assert result["status"] == "gate0_pre_response_ready"
    assert result["safe_file_requests"] == 3
    assert result["observations_requests"] == 0
    assert result["observations_header_bytes_opened"] == 0
    assert result["observations_payload_bytes_opened"] == 0
    assert result["observations_rows_opened"] == 0
    assert result["observations_values_opened"] is False
    assert len(calls) == 3
    assert output_path.exists()
