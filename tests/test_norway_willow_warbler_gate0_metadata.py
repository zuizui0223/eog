import json
from pathlib import Path

import pytest

from validation.norway_willow_warbler_endpoint3.gate0_zenodo_metadata import (
    MetadataGateStop,
    evaluate_zenodo_metadata,
    load_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    ROOT / "validation" / "norway_willow_warbler_endpoint3" / "source_contract.json"
)


def _metadata():
    return {
        "id": 18452203,
        "doi": "10.5281/zenodo.18452203",
        "metadata": {
            "title": "National-scale acoustic monitoring of avian biodiversity and migration"
        },
        "files": [
            {
                "key": "National_PAM_of_Biodiversity_Bick_et_al_2026.zip",
                "size": 491_572_428,
                "checksum": "md5:47a757dd5aae5974498e3b953d684282",
                "links": {
                    "content": "https://zenodo.org/api/records/18452203/files/archive/content",
                    "self": "https://zenodo.org/api/records/18452203/files/archive",
                },
            }
        ],
    }


def test_gate0_accepts_only_frozen_record_and_archive():
    result = evaluate_zenodo_metadata(_metadata(), load_contract(CONTRACT_PATH))
    assert result["status"] == "gate0_metadata_ready"
    assert result["identity"]["record_id"] == 18452203
    assert result["identity"]["archive_name"] == (
        "National_PAM_of_Biodiversity_Bick_et_al_2026.zip"
    )
    assert result["identity"]["archive_md5"] == "47a757dd5aae5974498e3b953d684282"
    assert result["archive_payload_requests"] == 0
    assert result["member_payload_requests"] == 0
    assert result["response_rows_opened"] == 0
    assert result["model_fits"] == 0


def test_alternate_record_is_rejected():
    metadata = _metadata()
    metadata["id"] = 14254172
    with pytest.raises(MetadataGateStop, match="record id drift"):
        evaluate_zenodo_metadata(metadata, load_contract(CONTRACT_PATH))


def test_archive_md5_drift_is_rejected():
    metadata = _metadata()
    metadata["files"][0]["checksum"] = "md5:" + "0" * 32
    with pytest.raises(MetadataGateStop, match="MD5 drift"):
        evaluate_zenodo_metadata(metadata, load_contract(CONTRACT_PATH))


def test_archive_name_substitution_is_rejected():
    metadata = _metadata()
    metadata["files"][0]["key"] = "National_PAM_of_Biodiversity_Bick_et_al_2024_v2.zip"
    with pytest.raises(MetadataGateStop, match="occurs 0 times"):
        evaluate_zenodo_metadata(metadata, load_contract(CONTRACT_PATH))


def test_duplicate_frozen_archive_identity_is_rejected():
    metadata = _metadata()
    metadata["files"].append(dict(metadata["files"][0]))
    with pytest.raises(MetadataGateStop, match="occurs 2 times"):
        evaluate_zenodo_metadata(metadata, load_contract(CONTRACT_PATH))


def test_content_link_is_required_before_archive_transport():
    metadata = _metadata()
    del metadata["files"][0]["links"]["content"]
    with pytest.raises(MetadataGateStop, match="non-empty string content"):
        evaluate_zenodo_metadata(metadata, load_contract(CONTRACT_PATH))


def test_contract_locks_taxon_calendar_effort_and_member_roles():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    endpoint = contract["prospective_endpoint"]
    split = contract["calendar_split"]
    effort = contract["pre_response_effort_and_geometry"]
    members = contract["frozen_archive_member_roles"]
    paired = contract["paired_prediction_boundary"]

    assert endpoint["taxon_scientific_name"] == "Phylloscopus trochilus"
    assert endpoint["birdnet_minimum_confidence"] == 0.80
    assert endpoint["expected_released_recorder_count"] == 28
    assert len(split["calibration_week_starts"]) == 6
    assert len(split["heldout_week_starts"]) == 6
    assert split["heldout_denominator"] == 6
    assert effort["active_recorder_week_minimum_audio_hours"] == 96.0
    assert effort["minimum_nodes_active_in_both_halves"] == 20
    assert effort["minimum_active_nodes_each_primary_week"] == 15
    assert effort["lcc_targets"] == [0.25, 0.50, 0.75, 0.90]
    assert effort["minimum_distinct_positive_structural_scales"] == 3
    assert members["geometry"] == "Data/Sites/sites.csv"
    assert members["effort"].endswith("audio-export-proj_sound-of-norway-yr2complete.csv")
    assert members["biological_response"].endswith(
        "birdnet_lite_detections-proj_sound-of-norway-yr2complete-fixedSiteName.csv"
    )
    assert paired["minimum_calibration_events"] == 10
    assert paired["minimum_calibration_non_events"] == 40
    assert paired["minimum_heldout_events"] == 10
    assert paired["minimum_heldout_non_events"] == 40
    assert paired["minimum_heldout_weeks_with_both_classes"] == 4
