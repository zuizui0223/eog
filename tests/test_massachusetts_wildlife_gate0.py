from __future__ import annotations

import json
from pathlib import Path

from validation.massachusetts_wildlife_selective_promotion import gate0_metadata


def test_contract_keeps_response_closed():
    contract = json.loads(gate0_metadata.CONTRACT.read_text(encoding="utf-8"))
    assert contract["gate0_authorized_metadata_only"]["file_payload_requests_allowed"] == 0
    assert contract["gate0_authorized_metadata_only"]["file_payload_bytes_allowed"] == 0
    assert contract["gate0_authorized_metadata_only"]["csv_header_bytes_allowed"] == 0
    assert contract["response_firewall"]["response_values_opened_before_contract"] is False
    assert "annotations.csv payload or header" in contract["response_firewall"]["forbidden_until_full_freeze"]
    assert contract["future_selective_promotion_invariants"]["outer_heldout_outcomes_must_never_participate_in_arm_selection"] is True
    assert contract["future_selective_promotion_invariants"]["layer_a_trajectory_persistence_required"] is True


def test_metadata_inventory_drops_unknown_or_payload_fields():
    item = {
        "id": "6672de8dd34e84915adbb4f3",
        "title": "Massachusetts Wildlife Monitoring Project (2022 - 2024)",
        "files": [
            {
                "name": "dictionary.csv",
                "id": "f1",
                "size": 123,
                "checksum": "abc",
                "checksumType": "md5",
                "contentType": "text/csv",
                "url": "https://example.invalid/dictionary.csv",
                "payload": "MUST_NOT_SURVIVE",
            }
        ],
        "childIds": ["child-1"],
        "annotations": "MUST_NOT_SURVIVE",
    }
    got = gate0_metadata._metadata_inventory(item)
    assert got["item_id"] == item["id"]
    assert got["child_ids"] == ["child-1"]
    assert got["files"][0]["name"] == "dictionary.csv"
    assert "payload" not in got["files"][0]
    assert "annotations" not in got
