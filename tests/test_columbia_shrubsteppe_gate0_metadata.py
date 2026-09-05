import json
from pathlib import Path

import pytest

from validation.columbia_shrubsteppe_endpoint3.gate0_metadata import (
    MetadataGateStop,
    evaluate_metadata,
    run,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation" / "columbia_shrubsteppe_endpoint3" / "source_contract.json"


def contract():
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def dataset():
    return {
        "identifier": "doi:10.5061/dryad.gf1vhhn0r",
        "_links": {"stash:version": {"href": "/api/v2/versions/424242"}},
    }


def version():
    # Intentionally no integer `id`: Gate0 must bind version identity from the
    # prospectively documented stash:version URL rather than a brittle schema alias.
    return {"versionNumber": 1, "_links": {"self": {"href": "/api/v2/versions/424242"}}}


def file_row(name, size=100, digest=None):
    return {
        "path": name,
        "size": size,
        "digest": digest or ("a" * 32),
        "digestType": "md5",
        "mimeType": "application/octet-stream",
        "status": "created",
        "_links": {
            "self": {"href": f"/api/v2/files/{name}"},
            "stash:download": {"href": f"/api/v2/files/{name}/download"},
        },
    }


def files_payload():
    names = ["Code.zip", "CSVs.zip", "README.md", "Raw_Data.zip"]
    return {"_embedded": {"stash:files": [file_row(name, 100 + i) for i, name in enumerate(names)]}}


def test_exact_metadata_passes_without_version_id_field():
    result = evaluate_metadata(
        contract(), dataset(), version(), files_payload(),
        version_id=424242,
        version_href="/api/v2/versions/424242",
    )
    assert result["status"] == "gate0_metadata_ready"
    assert result["current_version_id"] == 424242
    assert [row["path"] for row in result["files"]] == [
        "CSVs.zip", "Code.zip", "README.md", "Raw_Data.zip"
    ]
    assert result["file_payload_requests"] == 0
    assert result["detection_history_bytes_opened"] == 0
    assert result["response_values_opened"] is False


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d, f: d.update(identifier="doi:10.5061/dryad.other"),
        lambda d, f: f["_embedded"]["stash:files"].pop(),
        lambda d, f: f["_embedded"]["stash:files"].append(file_row("extra.zip")),
        lambda d, f: f["_embedded"]["stash:files"][0].update(size=0),
        lambda d, f: f["_embedded"]["stash:files"][0].update(digest=""),
        lambda d, f: f["_embedded"]["stash:files"][0].update(digestType=""),
    ],
)
def test_identity_or_integrity_drift_stops(mutator):
    d = dataset()
    f = files_payload()
    mutator(d, f)
    with pytest.raises(MetadataGateStop):
        evaluate_metadata(
            contract(), d, version(), f,
            version_id=424242,
            version_href="/api/v2/versions/424242",
        )


def test_run_uses_exact_three_metadata_requests_and_zero_payload(tmp_path):
    seen = []
    responses = {
        contract()["dryad"]["dataset_api"]: dataset(),
        "https://datadryad.org/api/v2/versions/424242": version(),
        "https://datadryad.org/api/v2/versions/424242/files": files_payload(),
    }

    def fetch_json(url):
        seen.append(url)
        return responses[url]

    output = tmp_path / "certificate.json"
    result = run(CONTRACT_PATH, output, fetch_json=fetch_json)
    assert result["status"] == "gate0_metadata_ready"
    assert seen == list(responses)
    assert result["metadata_requests"] == 3
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["archive_member_bytes_opened"] == 0
    assert result["camera_record_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["model_fits"] == result["heldout_scores"] == 0
    assert output.exists()


def test_unexpected_version_href_stops_before_followup_requests(tmp_path):
    d = dataset()
    d["_links"]["stash:version"]["href"] = "/api/v2/versions/current"
    seen = []

    def fetch_json(url):
        seen.append(url)
        return d

    result = run(CONTRACT_PATH, tmp_path / "certificate.json", fetch_json=fetch_json)
    assert result["status"] == "stop_pre_response_metadata_identity_or_transport"
    assert result["metadata_requests"] == 1
    assert seen == [contract()["dryad"]["dataset_api"]]
    assert result["file_payload_bytes_opened"] == 0
