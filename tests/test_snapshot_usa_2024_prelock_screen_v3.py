from __future__ import annotations

from email.message import Message
import hashlib
import json

from validation.snapshot_usa_2024_prelock_screen.screen_v3 import run


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
        return self._body if n < 0 else self._body[:n]

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


def deployments():
    return (
        "Project,State,Camera_Trap_Array,Site_Name,Deployment_ID,Start_Date,"
        "End_Date,Survey_Nights,Latitude,Longitude\n"
        "P1,AA,A1,S1,D1,2024-09-01,2024-10-01,30,40.0,-80.0\n"
        "P1,AA,A1,S1,D2,2024-10-02,2024-11-01,30,40.0,-80.0\n"
        "P1,BB,A2,S2,D3,2024-09-01,2024-10-01,30,41.0,-81.0\n"
        "P1,CC,A3,S3,D4,2024-09-01,2024-10-01,30,42.0,-82.0\n"
    ).encode()


def write_contract(tmp_path):
    payload = {
        "screen_id": "fixture-v3",
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
                "https://datadryad.org/downloads/file_stream/{file_id}"
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
    path = tmp_path / "v3.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path, payload


def make_opener(contract):
    safe = deployments()
    safe_digest = hashlib.sha256(safe).hexdigest()
    dataset_url = contract["source_identity"]["api_dataset_url"]
    version_url = "https://datadryad.org/api/v2/versions/999"
    files_url = "https://datadryad.org/api/v2/versions/999/files?per_page=100"
    current_safe = "https://datadryad.org/downloads/file_stream/12345"
    current_response = "https://datadryad.org/downloads/file_stream/67890"
    old_safe = "https://datadryad.org/stash/downloads/file_stream/12345"
    api_safe = "https://datadryad.org/api/v2/files/12345/download"

    dataset = {
        "identifier": "doi:10.5061/dryad.fixture",
        "title": "Fixture dataset",
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
                    "digest": safe_digest,
                    "digestType": "sha-256",
                    "_links": {
                        "self": {"href": "/api/v2/files/12345"},
                        "stash:download": {"href": "/api/v2/files/12345/download"},
                    },
                },
                {
                    "path": "sequences.csv",
                    "size": 5_000_000,
                    "digest": "b" * 64,
                    "digestType": "sha-256",
                    "_links": {
                        "self": {"href": "/api/v2/files/67890"},
                        "stash:download": {"href": "/api/v2/files/67890/download"},
                    },
                },
            ]
        }
    }
    opener = FakeOpener({
        dataset_url: FakeResponse(
            url=dataset_url, body=json.dumps(dataset).encode()
        ),
        version_url: FakeResponse(
            url=version_url, body=json.dumps(version).encode()
        ),
        files_url: FakeResponse(
            url=files_url, body=json.dumps(files).encode()
        ),
        current_safe: FakeResponse(
            url=current_safe, body=safe, content_type="text/csv"
        ),
    })
    return opener, current_safe, current_response, old_safe, api_safe


def test_v3_uses_current_public_route_only(tmp_path):
    contract_path, contract = write_contract(tmp_path)
    opener, current_safe, current_response, old_safe, api_safe = make_opener(contract)

    result = run(contract_path, tmp_path / "out.json", opener=opener)

    assert result["status"] == "source_ready_for_focal_selection_prelock"
    assert current_safe in opener.requested
    assert current_response not in opener.requested
    assert old_safe not in opener.requested
    assert api_safe not in opener.requested
    assert result["response_file_requests"] == 0
    assert result["response_file_payload_bytes_opened"] == 0
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["candidate_preflight"]["status"] == "ready_for_geometry_gate"


def test_v3_keeps_dryad_sha_as_scientific_identity(tmp_path):
    contract_path, contract = write_contract(tmp_path)
    opener, current_safe, current_response, _, _ = make_opener(contract)
    opener.responses[current_safe] = FakeResponse(
        url=current_safe,
        body=deployments() + b"tamper",
        content_type="text/csv",
    )

    result = run(contract_path, tmp_path / "drift.json", opener=opener)

    assert result["status"] == "source_screen_stop_prelock"
    assert "byte-size drift" in result["reason"]
    assert current_response not in opener.requested
    assert result["response_file_payload_bytes_opened"] == 0
