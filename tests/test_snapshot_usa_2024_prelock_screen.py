from __future__ import annotations

from email.message import Message
import hashlib
import json
from pathlib import Path

from validation.snapshot_usa_2024_prelock_screen.screen import run


class FakeResponse:
    def __init__(self, *, url, body, content_type="application/json"):
        self.status = 200
        self._url = url
        self._body = body
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(len(body))

    def getcode(self):
        return self.status

    def geturl(self):
        return self._url

    def read(self, n=-1):
        if n < 0:
            return self._body
        return self._body[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, responses):
        self.responses = dict(responses)
        self.requested = []

    def open(self, request, timeout=90):
        url = request.full_url
        self.requested.append(url)
        if url not in self.responses:
            raise AssertionError(f"unexpected URL: {url}")
        return self.responses[url]


def _deployments():
    return (
        "Project,State,Camera_Trap_Array,Site_Name,Deployment_ID,Start_Date,"
        "End_Date,Survey_Nights,Latitude,Longitude\n"
        "P1,AA,A1,S1,D1,2024-09-01,2024-10-01,30,40.0,-80.0\n"
        "P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.0,-80.0\n"
        "P1,BB,A2,S2,D3,2024-09-01,2024-10-01,30,41.0,-81.0\n"
        "P1,CC,A3,S3,D4,2024-09-01,2024-10-01,30,42.0,-82.0\n"
    ).encode("utf-8")


def _write_contract(tmp_path):
    contract = {
        "schema": "fixture",
        "screen_id": "fixture-screen",
        "source_identity": {
            "doi": "10.5061/dryad.fixture",
            "encoded_doi": "doi%3A10.5061%2Fdryad.fixture",
            "title": "Fixture dataset",
            "api_dataset_url": (
                "https://datadryad.org/api/v2/datasets/"
                "doi%3A10.5061%2Fdryad.fixture"
            ),
        },
        "safe_file": {
            "path": "deployments.csv",
            "maximum_bytes": 100000,
        },
        "response_file": {
            "path": "sequences.csv",
            "payload_bytes_allowed": 0,
        },
        "metadata_bounds": {
            "maximum_json_bytes": 100000,
            "maximum_files_per_version": 100,
        },
        "response_independent_architecture_minima": {
            "minimum_unique_nodes": 3,
            "minimum_outer_units": 3,
            "minimum_repeated_nodes": 1,
            "minimum_arrays": 3,
            "require_all_nodes_single_coordinate_pair": True,
            "require_positive_survey_nights": True,
        },
    }
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path, contract


def _opener(contract):
    safe = _deployments()
    safe_sha = hashlib.sha256(safe).hexdigest()
    response_digest = "a" * 64

    dataset_url = contract["source_identity"]["api_dataset_url"]
    version_url = "https://datadryad.org/api/v2/versions/999"
    files_url = "https://datadryad.org/api/v2/versions/999/files?per_page=100"
    safe_url = "https://datadryad.org/api/v2/files/1/download"
    response_url = "https://datadryad.org/api/v2/files/2/download"

    dataset = {
        "identifier": "doi:10.5061/dryad.fixture",
        "title": "Fixture dataset",
        "versionNumber": 1,
        "_links": {"stash:version": {"href": "/api/v2/versions/999"}},
    }
    version = {
        "_links": {"stash:files": {"href": "/api/v2/versions/999/files"}}
    }
    files = {
        "_embedded": {
            "stash:files": [
                {
                    "path": "deployments.csv",
                    "size": len(safe),
                    "digest": safe_sha,
                    "digestType": "sha-256",
                    "_links": {
                        "stash:download": {"href": "/api/v2/files/1/download"}
                    },
                },
                {
                    "path": "sequences.csv",
                    "size": 5000000,
                    "digest": response_digest,
                    "digestType": "sha-256",
                    "_links": {
                        "stash:download": {"href": "/api/v2/files/2/download"}
                    },
                },
            ]
        }
    }

    responses = {
        dataset_url: FakeResponse(
            url=dataset_url, body=json.dumps(dataset).encode("utf-8")
        ),
        version_url: FakeResponse(
            url=version_url, body=json.dumps(version).encode("utf-8")
        ),
        files_url: FakeResponse(
            url=files_url, body=json.dumps(files).encode("utf-8")
        ),
        safe_url: FakeResponse(
            url=safe_url, body=safe, content_type="text/csv"
        ),
    }
    return FakeOpener(responses), response_url


def test_snapshot_screen_uses_only_safe_deployments_file(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    opener, response_url = _opener(contract)
    output_path = tmp_path / "result.json"

    result = run(contract_path, output_path, opener=opener)

    assert result["status"] == "source_ready_for_focal_selection_prelock"
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["response_file_requests"] == 0
    assert result["response_file_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert response_url not in opener.requested

    audit = result["deployment_audit"]
    assert audit["deployment_row_count"] == 4
    assert audit["unique_stable_node_count"] == 3
    assert audit["repeated_stable_node_count"] == 1
    assert audit["unique_outer_state_count"] == 3
    assert audit["unique_array_count"] == 3
    assert audit["nodes_with_multiple_exact_coordinates_count"] == 0

    assert result["transport_qualification"]["ready"] is True
    assert result["candidate_preflight"]["status"] == "ready_for_geometry_gate"
    assert output_path.exists()


def test_snapshot_screen_detects_inconsistent_coordinates_before_focal_selection(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    opener, _ = _opener(contract)

    safe_url = "https://datadryad.org/api/v2/files/1/download"
    altered = _deployments().replace(
        b"P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.0,-80.0",
        b"P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.5,-80.5",
    )
    # Update both payload and its Dryad metadata digest/size.
    opener.responses[safe_url] = FakeResponse(
        url=safe_url, body=altered, content_type="text/csv"
    )
    files_url = "https://datadryad.org/api/v2/versions/999/files?per_page=100"
    files_doc = json.loads(opener.responses[files_url]._body)
    files_doc["_embedded"]["stash:files"][0]["size"] = len(altered)
    files_doc["_embedded"]["stash:files"][0]["digest"] = hashlib.sha256(
        altered
    ).hexdigest()
    opener.responses[files_url] = FakeResponse(
        url=files_url, body=json.dumps(files_doc).encode("utf-8")
    )

    result = run(contract_path, tmp_path / "result2.json", opener=opener)
    assert result["status"] == "source_architecture_unqualified_prelock"
    assert (
        result["deployment_audit"]["nodes_with_multiple_exact_coordinates_count"]
        == 1
    )
    assert result["candidate_preflight"]["status"] == "stop_analysis_registry_not_closed"
    assert result["response_file_payload_bytes_opened"] == 0


def test_snapshot_screen_stops_on_safe_file_digest_drift(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    opener, response_url = _opener(contract)
    safe_url = "https://datadryad.org/api/v2/files/1/download"
    opener.responses[safe_url] = FakeResponse(
        url=safe_url,
        body=_deployments() + b"tamper",
        content_type="text/csv",
    )

    result = run(contract_path, tmp_path / "result3.json", opener=opener)
    assert result["status"] == "source_screen_stop_prelock"
    assert "byte size differs" in result["reason"]
    assert response_url not in opener.requested
    assert result["response_file_payload_bytes_opened"] == 0
