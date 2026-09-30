import json
from pathlib import Path

import pytest

from validation.bam_round_goby_external_bridge_v1.gate0_source_identity import (
    Gate0Stop,
    evaluate_metadata,
    frozen_files,
    load_protocol,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_round_goby_external_bridge_v1"
)


def _fixture_metadata():
    protocol = load_protocol(HERE / "source_protocol_v1.json")
    files = [
        {
            "key": row.name,
            "checksum": f"md5:{row.md5}",
            "size": 100 + i,
        }
        for i, row in enumerate(frozen_files(protocol))
    ]
    return {
        "id": protocol["source"]["zenodo_record_id"],
        "metadata": {"title": protocol["source"]["title"]},
        "files": files,
    }


def test_gate0_accepts_exact_frozen_identity():
    protocol = load_protocol(HERE / "source_protocol_v1.json")
    result = evaluate_metadata(_fixture_metadata(), protocol)
    assert result["status"] == "source_identity_ready"
    assert result["file_count"] == 10
    assert result["response_payload_bytes_opened"] == 0
    assert result["file_payload_requests"] == 0
    assert result["metadata_only"] is True


def test_gate0_fails_closed_on_checksum_change():
    protocol = load_protocol(HERE / "source_protocol_v1.json")
    metadata = _fixture_metadata()
    metadata["files"][0]["checksum"] = "md5:" + "0" * 32
    with pytest.raises(Gate0Stop, match="checksum mismatch"):
        evaluate_metadata(metadata, protocol)


def test_gate0_fails_closed_on_roster_change():
    protocol = load_protocol(HERE / "source_protocol_v1.json")
    metadata = _fixture_metadata()
    metadata["files"].pop()
    with pytest.raises(Gate0Stop, match="file roster mismatch"):
        evaluate_metadata(metadata, protocol)
