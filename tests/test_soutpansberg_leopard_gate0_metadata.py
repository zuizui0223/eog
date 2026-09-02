import json
from pathlib import Path

import pytest

from validation.soutpansberg_leopard_endpoint3.gate0_figshare_metadata import (
    MetadataGateStop,
    evaluate_figshare_metadata,
    terminal_stop_result,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "validation" / "soutpansberg_leopard_endpoint3" / "source_contract.json"
)


def _contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _metadata():
    return {
        "id": 4235546,
        "title": "SPACECAP input files",
        "files": [
            {
                "id": 777001,
                "name": "SPACECAP input files.zip",
                "download_url": "https://ndownloader.figshare.com/files/777001",
                "size": 467240,
                "supplied_md5": "0123456789abcdef0123456789abcdef",
            }
        ],
    }


def test_gate0_accepts_exact_metadata_without_payload_access():
    result = evaluate_figshare_metadata(_metadata(), _contract())
    assert result["status"] == "gate0_metadata_ready"
    assert result["identity"]["file_name"] == "SPACECAP input files.zip"
    assert result["identity"]["size"] == 467240
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_gate0_fails_closed_on_file_name_drift():
    metadata = _metadata()
    metadata["files"][0]["name"] = "spacecap_inputs.zip"
    with pytest.raises(MetadataGateStop, match="file-name drift"):
        evaluate_figshare_metadata(metadata, _contract())


def test_gate0_fails_closed_on_extra_file():
    metadata = _metadata()
    metadata["files"].append(dict(metadata["files"][0], id=777002, name="README.txt"))
    with pytest.raises(MetadataGateStop, match="file-count drift"):
        evaluate_figshare_metadata(metadata, _contract())


def test_gate0_fails_closed_on_article_interface_drift():
    metadata = _metadata()
    metadata["id"] = "4235546"
    with pytest.raises(MetadataGateStop, match="lacks integer id"):
        evaluate_figshare_metadata(metadata, _contract())


def test_terminal_stop_never_becomes_predictive_evidence():
    result = terminal_stop_result(_contract(), "metadata transport unavailable")
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["model_fits"] == 0
    assert result["counts_as_predictive_evidence"] is False


def test_contract_freezes_endpoint3_and_paper_ready_boundaries():
    contract = _contract()
    assert contract["prospective_endpoint"]["taxon"] == "Panthera pardus"
    assert contract["prospective_endpoint"]["calibration_surveys"] == [
        f"s{i:02d}" for i in range(1, 17)
    ]
    assert contract["prospective_endpoint"]["heldout_surveys"] == [
        f"s{i:02d}" for i in range(17, 25)
    ]
    assert contract["pre_response_gates"]["capture_member_bytes_before_full_freeze"] == 0
    assert contract["pre_response_gates"]["minimum_active_nodes_per_heldout_survey"] == 20
    assert contract["pre_response_gates"]["minimum_distinct_structural_scales_per_heldout_survey"] == 3
    assert contract["transport_firewall_after_gate0"]["full_zip_download_forbidden"] is True
    assert contract["hard_stop"]["fourth_dataset_for_prestige_allowed"] is False
    assert contract["paper_ready_bindings"] == {
        "cross_ecosystem_synthesis_canonical_sha256": "1617b18b6b0c3e2797945c3d30111a4e3e6941a560a6b8a39b8d117e84c82b02",
        "feature_count_placebo_canonical_sha256": "72129df202a4d8c0203b507f82c3cbc6c612feb028d12b6386dc39abde4de8cd",
        "excluded_world_information_canonical_sha256": "7f76113602346347829378c1daaf8a3f057d1ee6fe72f0141dc998b69966a53a",
    }
