import copy
import json
from pathlib import Path

import pytest

from validation.bam_greatlakes_barrier_external_bridge_v1.gate0_dryad_identity import (
    EXPECTED_ROSTER,
    Gate0Stop,
    DOI,
    evaluate,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_greatlakes_barrier_external_bridge_v1"
)


def _protocol():
    return json.loads((HERE / "source_protocol_v1.json").read_text(encoding="utf-8"))


def _fixture():
    protocol = _protocol()
    dataset = {
        "id": 123,
        "identifier": "doi:" + DOI,
        "title": protocol["source"]["title"],
    }
    versions = {
        "_embedded": {
            "stash:versions": [
                {
                    "versionNumber": 1,
                    "_links": {"self": {"href": "/api/v2/versions/456"}}
                }
            ]
        }
    }
    files = {
        "_embedded": {
            "stash:files": [
                {
                    "path": path,
                    "size": 100 + i,
                    "digest": f"{i+1:064x}"[-64:],
                    "digestType": "sha-256",
                    "_links": {
                        "self": {"href": f"/api/v2/files/{1000+i}"},
                        "stash:download": {"href": f"/api/v2/files/{1000+i}/download"},
                    },
                }
                for i, path in enumerate(EXPECTED_ROSTER)
            ]
        }
    }
    return dataset, versions, files, protocol


def test_gate0_accepts_exact_dryad_identity():
    dataset, versions, files, protocol = _fixture()
    result = evaluate(dataset, versions, files, protocol)
    assert result["status"] == "dryad_source_identity_ready"
    assert result["file_count"] == 10
    assert result["data_file_payload_requests"] == 0
    assert result["data_file_payload_bytes_opened"] == 0
    assert sum(row["required_for_bridge"] for row in result["files"]) == 3


def test_gate0_fails_closed_on_roster_drift():
    dataset, versions, files, protocol = _fixture()
    files = copy.deepcopy(files)
    files["_embedded"]["stash:files"].pop()
    with pytest.raises(Gate0Stop, match="roster drift"):
        evaluate(dataset, versions, files, protocol)


def test_gate0_fails_closed_on_multiple_versions():
    dataset, versions, files, protocol = _fixture()
    versions = copy.deepcopy(versions)
    versions["_embedded"]["stash:versions"].append(
        {
            "versionNumber": 2,
            "_links": {"self": {"href": "/api/v2/versions/999"}}
        }
    )
    with pytest.raises(Gate0Stop, match="exactly one"):
        evaluate(dataset, versions, files, protocol)


def test_gate0_fails_closed_on_unparseable_version_self_link():
    dataset, versions, files, protocol = _fixture()
    versions = copy.deepcopy(versions)
    versions["_embedded"]["stash:versions"][0]["_links"]["self"]["href"] = (
        "/api/v2/versions/not-an-id"
    )
    with pytest.raises(Gate0Stop, match="version self href"):
        evaluate(dataset, versions, files, protocol)
