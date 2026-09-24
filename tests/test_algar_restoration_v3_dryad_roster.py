import hashlib
import json
from pathlib import Path

from validation.algar_restoration_v3_response_roster.dryad_roster import run


def _file(path, file_id, version_id=42, raw=b"abc"):
    return {
        "path": path,
        "size": len(raw),
        "mimeType": "text/csv",
        "status": "copied",
        "digest": hashlib.md5(raw).hexdigest(),
        "digestType": "md5",
        "_links": {
            "self": {"href": f"/api/v2/files/{file_id}"},
            "stash:version": {"href": f"/api/v2/versions/{version_id}"},
            "stash:download": {"href": f"/api/v2/downloads/{file_id}"},
        },
    }


def _documents():
    dataset = {
        "identifier": "doi:10.5061/dryad.8pk0p2nnz",
        "title": (
            "Data from: Multispecies modelling reveals potential for habitat "
            "restoration to re-establish boreal vertebrate community dynamics"
        ),
        "publicationDate": "2021-01-01",
        "versionNumber": 1,
        "_links": {
            "stash:version": {"href": "/api/v2/versions/42"},
        },
    }
    version = {
        "versionNumber": 1,
        "versionStatus": "submitted",
        "visibility": "public",
        "lastModificationDate": "2021-01-02",
        "_links": {
            "self": {"href": "/api/v2/versions/42"},
            "stash:files": {"href": "/api/v2/versions/42/files"},
        },
    }
    files = {
        "_embedded": {
            "stash:files": [
                _file("deployments.csv", 1),
                _file("observations.csv", 2),
                _file("README.md", 3),
            ]
        },
        "_links": {},
    }
    return dataset, version, files


def test_metadata_roster_resolves_without_any_file_payload(tmp_path):
    contract = json.loads(
        Path(
            "validation/algar_restoration_v3_response_roster/"
            "roster_contract.json"
        ).read_text(encoding="utf-8")
    )
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    dataset, version, files = _documents()
    queue = [dataset, version, files]
    calls = []

    def fetcher(url, maximum_bytes, role):
        calls.append((url, role))
        payload = queue.pop(0)
        raw = json.dumps(payload).encode("utf-8")
        return payload, {
            "role": role,
            "url": url,
            "final_url": url,
            "status": 200,
            "bytes_opened": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    result = run(
        contract_path,
        output_path,
        fetcher=fetcher,
    )
    assert result["status"] == "dryad_response_roster_resolved_metadata_only"
    assert result["file_count"] == 3
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
    assert result["biological_response_values_opened"] is False
    assert "observations.csv" in result["response_bearing_paths"]
    assert "deployments.csv" in result["safe_candidate_paths"]
    assert "README.md" in result["ambiguous_do_not_open_paths"]
    assert len(calls) == 3


def test_file_roster_paginates_metadata_only(tmp_path):
    contract = json.loads(
        Path(
            "validation/algar_restoration_v3_response_roster/"
            "roster_contract.json"
        ).read_text(encoding="utf-8")
    )
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    dataset, version, _ = _documents()
    page1 = {
        "_embedded": {"stash:files": [_file("deployments.csv", 1)]},
        "_links": {"next": {"href": "/api/v2/versions/42/files?page=2"}},
    }
    page2 = {
        "_embedded": {"stash:files": [_file("detections.csv", 2)]},
        "_links": {},
    }
    queue = [dataset, version, page1, page2]

    def fetcher(url, maximum_bytes, role):
        payload = queue.pop(0)
        raw = json.dumps(payload).encode("utf-8")
        return payload, {
            "role": role,
            "url": url,
            "final_url": url,
            "status": 200,
            "bytes_opened": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    result = run(contract_path, output_path, fetcher=fetcher)
    assert result["file_count"] == 2
    assert "detections.csv" in result["response_bearing_paths"]
    assert result["metadata_requests"] == 4
    assert result["file_payload_requests"] == 0


def test_wrong_doi_stops_before_file_payload(tmp_path):
    contract = json.loads(
        Path(
            "validation/algar_restoration_v3_response_roster/"
            "roster_contract.json"
        ).read_text(encoding="utf-8")
    )
    contract_path = tmp_path / "contract.json"
    output_path = tmp_path / "result.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    dataset, _, _ = _documents()
    dataset["identifier"] = "doi:10.5061/dryad.wrong"

    def fetcher(url, maximum_bytes, role):
        raw = json.dumps(dataset).encode("utf-8")
        return dataset, {
            "role": role,
            "url": url,
            "final_url": url,
            "status": 200,
            "bytes_opened": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    result = run(contract_path, output_path, fetcher=fetcher)
    assert result["status"] == "stop_dryad_metadata_roster"
    assert "DOI identity drift" in result["reason"]
    assert result["file_payload_requests"] == 0
    assert result["file_payload_bytes_opened"] == 0
