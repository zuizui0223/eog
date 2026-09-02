from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from validation.loomis_snowshoe_hare_endpoint3.gate0_zenodo_metadata import (
    MetadataGateStop,
    evaluate_zenodo_metadata,
    terminal_stop_result,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "validation" / "loomis_snowshoe_hare_endpoint3" / "source_contract.json"
)


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _metadata() -> dict[str, object]:
    contract = _contract()
    required = contract["source"]["required_files"]
    files = []
    for i, (name, checksum) in enumerate(required.items(), start=1):
        files.append(
            {
                "id": f"file-{i}",
                "key": name,
                "checksum": checksum,
                "size": 1000 + i,
                "links": {"self": f"https://zenodo.org/api/records/21796558/files/{i}/content"},
            }
        )
    files.append(
        {
            "id": "extra",
            "key": "simulation_only_extra.csv",
            "checksum": "md5:00000000000000000000000000000000",
            "size": 77,
            "links": {"self": "https://zenodo.org/api/records/21796558/files/extra/content"},
        }
    )
    return {"id": 21796558, "files": files}


def test_gate0_accepts_exact_required_files_and_ignores_extra_record_files() -> None:
    result = evaluate_zenodo_metadata(_metadata(), _contract())
    assert result["status"] == "gate0_metadata_ready"
    assert result["metadata_only"] is True
    assert result["required_file_count"] == 7
    assert result["record_file_count"] == 8
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["deployment_header_bytes_opened"] == 0
    assert result["deployment_rows_opened"] == 0
    assert result["detection_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_gate0_missing_required_file_stops() -> None:
    metadata = _metadata()
    metadata["files"] = [
        row for row in metadata["files"] if row["key"] != "deployment_2024.csv"
    ]
    with pytest.raises(MetadataGateStop, match="required Zenodo file missing"):
        evaluate_zenodo_metadata(metadata, _contract())


def test_gate0_checksum_drift_stops() -> None:
    metadata = _metadata()
    row = next(row for row in metadata["files"] if row["key"] == "final_data_2024.csv")
    row["checksum"] = "md5:11111111111111111111111111111111"
    with pytest.raises(MetadataGateStop, match="checksum drift"):
        evaluate_zenodo_metadata(metadata, _contract())


def test_gate0_duplicate_file_key_stops() -> None:
    metadata = _metadata()
    metadata["files"].append(deepcopy(metadata["files"][0]))
    with pytest.raises(MetadataGateStop, match="duplicate Zenodo file key"):
        evaluate_zenodo_metadata(metadata, _contract())


def test_gate0_non_https_file_link_stops_before_payload() -> None:
    metadata = _metadata()
    metadata["files"][0]["links"] = {"self": "http://example.test/file"}
    with pytest.raises(MetadataGateStop, match="no absolute HTTPS link"):
        evaluate_zenodo_metadata(metadata, _contract())


def test_terminal_stop_never_becomes_predictive_evidence() -> None:
    result = terminal_stop_result(_contract(), "metadata transport failed")
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_source_contract_preserves_endpoint3_and_no_rescue_boundaries() -> None:
    contract = _contract()
    assert contract["attempt_id"] == "loomis_snowshoe_hare_endpoint3_v1"
    assert contract["issue"] == 340
    assert contract["prospective_endpoint"]["taxon"] == "Lepus americanus"
    assert contract["prospective_endpoint"]["calibration_years"] == [2022, 2023]
    assert contract["prospective_endpoint"]["heldout_years"] == [2024]
    assert contract["prospective_endpoint"]["source_paper_blind"] is False
    assert contract["deployment_geometry_rules_to_freeze_before_rows"]["minimum_total_camera_nodes"] == 20
    assert contract["deployment_geometry_rules_to_freeze_before_rows"]["minimum_repeated_nodes_calibration_to_heldout"] == 15
    assert contract["deployment_geometry_rules_to_freeze_before_rows"]["active_camera_week_minimum_overlap_hours"] == 96
    assert contract["deployment_geometry_rules_to_freeze_before_rows"]["minimum_heldout_outer_weeks"] == 4
    assert contract["deployment_geometry_rules_to_freeze_before_rows"]["minimum_distinct_response_blind_structural_scales"] == 3
    assert contract["paper_ready_bindings"] == {
        "cross_ecosystem_synthesis_canonical_sha256": "1617b18b6b0c3e2797945c3d30111a4e3e6941a560a6b8a39b8d117e84c82b02",
        "feature_count_placebo_canonical_sha256": "72129df202a4d8c0203b507f82c3cbc6c612feb028d12b6386dc39abde4de8cd",
        "excluded_world_information_canonical_sha256": "7f76113602346347829378c1daaf8a3f057d1ee6fe72f0141dc998b69966a53a",
    }
    assert contract["hard_stop"]["terminal_candidate_reuse_allowed"] is False
    assert contract["hard_stop"]["post_response_retuning_allowed"] is False
    assert contract["hard_stop"]["species_switch_allowed"] is False
    assert contract["hard_stop"]["fourth_dataset_for_prestige_allowed"] is False
