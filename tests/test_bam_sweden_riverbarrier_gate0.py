import json
from pathlib import Path

import pytest

from validation.bam_sweden_riverbarrier_external_bridge_v1.gate0_dryad_identity import (
    Gate0Stop,
    EXPECTED_ROSTER,
    evaluate,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_sweden_riverbarrier_external_bridge_v1"
)


def _protocol():
    return json.loads((HERE / "source_protocol_v1.json").read_text(encoding="utf-8"))


def _fixture():
    dataset = {
        "id": 1,
        "identifier": "doi:10.5061/dryad.05qfttf9z",
        "title": _protocol()["source"]["title"],
    }
    versions = {
        "_embedded": {
            "stash:versions": [{
                "versionNumber": 1,
                "_links": {"self": {"href": "/api/v2/versions/123"}},
            }]
        }
    }
    files = {
        "_embedded": {
            "stash:files": [
                {
                    "path": name,
                    "size": 100+i,
                    "digestType": "sha-256",
                    "digest": f"{i+1:064x}",
                    "_links": {
                        "self": {"href": f"/api/v2/files/{100+i}"},
                        "stash:download": {"href": f"/api/v2/files/{100+i}/download"},
                    },
                }
                for i, name in enumerate(EXPECTED_ROSTER)
            ]
        }
    }
    return dataset, versions, files


def test_exact_frozen_roster_passes():
    dataset, versions, files = _fixture()
    result = evaluate(dataset, versions, files, _protocol())
    assert result["status"] == "dryad_source_identity_ready"
    assert result["file_count"] == 7
    assert result["data_file_payload_bytes_opened"] == 0


def test_roster_drift_fails_closed():
    dataset, versions, files = _fixture()
    files["_embedded"]["stash:files"].pop()
    with pytest.raises(Gate0Stop, match="roster drift"):
        evaluate(dataset, versions, files, _protocol())


def test_title_drift_fails_closed():
    dataset, versions, files = _fixture()
    dataset["title"] = "wrong"
    with pytest.raises(Gate0Stop, match="title mismatch"):
        evaluate(dataset, versions, files, _protocol())
