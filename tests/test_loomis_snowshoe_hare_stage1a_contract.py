from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation" / "loomis_snowshoe_hare_endpoint3" / "gate1a_header_contract.json"


def test_stage1a_contract_is_header_only_and_bound_to_gate0():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert x["attempt_id"] == "loomis_snowshoe_hare_endpoint3_v1"
    assert x["gate0_recording_merge"] == "8145d069f8dec727d5df8301d38a74edf77fed66"
    assert x["gate0_certificate_git_blob_sha1"] == "5d8408112fa494bce75fb33aba53f9f519007158"
    assert [f["key"] for f in x["allowed_files"]] == [
        "camera_info_new.csv",
        "deployment_2022.csv",
        "deployment_2023.csv",
        "deployment_2024.csv",
    ]
    assert x["transport"]["range_requests_only"] is True
    assert x["transport"]["require_http_206"] is True
    assert x["transport"]["one_byte_ranges_until_first_CR_or_LF"] is True
    assert x["transport"]["full_file_download_forbidden"] is True
    forbidden = " ".join(x["stage1a_outputs_forbidden"])
    assert "deployment data row" in forbidden
    assert "detection-file header" in forbidden
    assert "hare response" in forbidden
    assert x["post_header_semantic_rescue_with_row_values_allowed"] is False
    assert x["post_header_detection_access_allowed"] is False
    assert "Stage1A header evidence only" in x["stage1b_rule"]
