from __future__ import annotations

from email.message import Message
import hashlib
import json

from validation.snapshot_usa_2024_prelock_screen.screen_v2 import run


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
        "schema": "fixture-v2",
        "screen_id": "fixture-v2-screen",
        "source_identity": {
            "doi": "10.5061/dryad.fixture",
            "title": "Fixture dataset",
            "api_dataset_url": (
                "https://datadryad.org/api/v2/datasets/"
                "doi%3A10.5061%2Fdryad.fixture"
            ),
        },
        "safe_file": {
            "path": "deployments.csv",
            "maximum_bytes": 100000,
            "public_route_template": (
                "https://datadryad.org/stash/downloads/file_stream/{file_id}"
            ),
        },
        "response_file": {
            "path": "sequences.csv",
            "payload_requests_allowed": 0,
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
    path = tmp_path / "contract_v2.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path, contract


def _opener(contract, safe_bytes=None):
    safe = _deployments() if safe_bytes is None else safe_bytes
    safe_sha = hashlib.sha256(safe).hexdigest()
    response_digest = "b" * 64

    dataset_url = contract["source_identity"]["api_dataset_url"]
    version_url = "https://datadryad.org/api/v2/versions/999"
    files_url = "https://datadryad.org/api/v2/versions/999/files?per_page=100"
    public_safe_url = "https://datadryad.org/stash/downloads/file_stream/12345"
    public_response_url = "https://datadryad.org/stash/downloads/file_stream/67890"
    api_safe_url = "https://datadryad.org/api/v2/files/12345/download"
    api_response_url = "https://datadryad.org/api/v2/files/67890/download"

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
                        "self": {"href": "/api/v2/files/12345"},
                        "stash:download": {
                            "href": "/api/v2/files/12345/download"
                        },
                    },
                },
                {
                    "path": "sequences.csv",
                    "size": 5_000_000,
                    "digest": response_digest,
                    "digestType": "sha-256",
                    "_links": {
                        "self": {"href": "/api/v2/files/67890"},
                        "stash:download": {
                            "href": "/api/v2/files/67890/download"
                        },
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
        public_safe_url: FakeResponse(
            url=public_safe_url, body=safe, content_type="text/csv"
        ),
    }
    return (
        FakeOpener(responses),
        public_safe_url,
        public_response_url,
        api_safe_url,
        api_response_url,
    )


def test_v2_public_route_reaches_safe_file_without_response_or_api_download(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    opener, public_safe, public_response, api_safe, api_response = _opener(contract)

    result = run(contract_path, tmp_path / "result.json", opener=opener)

    assert result["status"] == "source_ready_for_focal_selection_prelock"
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["response_file_requests"] == 0
    assert result["response_file_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False

    assert public_safe in opener.requested
    assert public_response not in opener.requested
    assert api_safe not in opener.requested
    assert api_response not in opener.requested

    assert result["safe_file"]["file_id"] == 12345
    assert result["safe_file"]["payload_bytes_opened"] == len(_deployments())
    assert result["response_file"]["file_id"] == 67890
    assert result["response_file"]["payload_requests"] == 0
    assert result["response_file"]["payload_bytes_opened"] == 0

    assert result["transport_qualification"]["ready"] is True
    assert result["candidate_preflight"]["status"] == "ready_for_geometry_gate"
    assert result["deployment_audit"]["unique_stable_node_count"] == 3
    assert result["deployment_audit"]["repeated_stable_node_count"] == 1


def test_v2_public_route_still_fails_closed_on_repository_identity_drift(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    opener, public_safe, public_response, api_safe, api_response = _opener(contract)

    opener.responses[public_safe] = FakeResponse(
        url=public_safe,
        body=_deployments() + b"tamper",
        content_type="text/csv",
    )
    result = run(contract_path, tmp_path / "drift.json", opener=opener)

    assert result["status"] == "source_screen_stop_prelock"
    assert "byte-size drift" in result["reason"]
    assert public_response not in opener.requested
    assert api_safe not in opener.requested
    assert api_response not in opener.requested
    assert result["response_file_payload_bytes_opened"] == 0


def test_v2_coordinate_conflict_rejects_architecture_before_focal_selection(tmp_path):
    contract_path, contract = _write_contract(tmp_path)
    altered = _deployments().replace(
        b"P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.0,-80.0",
        b"P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.5,-80.5",
    )
    opener, _, public_response, api_safe, api_response = _opener(
        contract, safe_bytes=altered
    )

    result = run(contract_path, tmp_path / "conflict.json", opener=opener)

    assert result["status"] == "source_architecture_unqualified_prelock"
    assert (
        result["candidate_preflight"]["status"]
        == "stop_analysis_registry_not_closed"
    )
    assert result["deployment_audit"]["nodes_with_multiple_exact_coordinates_count"] == 1
    assert public_response not in opener.requested
    assert api_safe not in opener.requested
    assert api_response not in opener.requested
    assert result["focal_species_selected"] is False
    assert result["candidate_locked"] is False
