"""Response-unopened, frozen-DOI Dryad metadata transport gate tests."""
import json
from pathlib import Path

from benchmarks.run_pyrgus_bam_metadata_gate_v1 import evaluate


PROTOCOL = json.loads(
    Path("validation/pyrgus_bam_metadata_gate_v1/protocol_v1.json").read_text()
)
VERSION = 999


def version_doc():
    return {"_embedded": {"stash:versions": [{
        "versionNumber": 1, "versionStatus": "submitted", "visibility": "public",
        "_links": {
            "self": {"href": f"/api/v2/versions/{VERSION}"},
            "stash:files": {"href": f"/api/v2/versions/{VERSION}/files"},
        },
    }]}}


def file_doc():
    rows = []
    for idx, (name, size) in enumerate((
        ("Site_data.csv", 2760), ("Monitoring_data.csv", 8380)
    )):
        file_id = 3001 + idx
        rows.append({
            "path": name, "size": size, "status": "copied",
            "digestType": "sha-256", "digest": ("%064x" % (idx + 1)),
            "_links": {
                "self": {"href": f"/api/v2/files/{file_id}"},
                "stash:version": {"href": f"/api/v2/versions/{VERSION}"},
                "stash:download": {"href": f"/api/v2/files/{file_id}/download"},
            },
        })
    return {"_embedded": {"stash:files": rows}}


def test_fixture_verifies_metadata_and_never_opens_data_rows():
    calls = []
    def fetch(url):
        calls.append(url)
        return version_doc() if len(calls) == 1 else file_doc()
    r = evaluate(PROTOCOL, fetch)
    assert r["status"].startswith("SOURCE_METADATA_QUALIFIED")
    assert len(calls) == 2
    assert calls[0] == PROTOCOL["dataset"]["api_versions_url"]
    assert calls[1] == f"https://datadryad.org/api/v2/versions/{VERSION}/files"
    assert {x["path"] for x in r["files"]} == {
        "Monitoring_data.csv", "Site_data.csv"
    }
    assert r["response_rows_opened"] == 0
    assert r["data_files_downloaded"] == 0
    assert r["scored_ecological_endpoints"] == 0


def test_duplicate_versions_stop_before_file_list():
    v = version_doc()
    v["_embedded"]["stash:versions"].append(dict(v["_embedded"]["stash:versions"][0]))
    calls = []
    def fetch(url):
        calls.append(url)
        return v
    r = evaluate(PROTOCOL, fetch)
    assert r["status"] == "SOURCE_STOP_NOT_EXACTLY_ONE_PUBLIC_VERSION"
    assert len(calls) == 1


def test_extra_file_stops_at_file_roster_without_downloading():
    calls = []
    def fetch(url):
        calls.append(url)
        if len(calls) == 1:
            return version_doc()
        data = file_doc()
        extra = dict(data["_embedded"]["stash:files"][0])
        extra["path"] = "unknown_extra.csv"
        extra["_links"] = dict(extra["_links"])
        extra["_links"]["self"] = {"href": "/api/v2/files/9999"}
        data["_embedded"]["stash:files"].append(extra)
        return data
    r = evaluate(PROTOCOL, fetch)
    assert r["status"] == "SOURCE_STOP_FILE_ROSTER_MISMATCH"
    assert len(calls) == 2
    assert r["response_rows_opened"] == 0


def test_unauthorized_transport_stops_cleanly():
    def fetch(url):
        raise ValueError("SOURCE_STOP_UNAUTHORIZED_HOST")
    r = evaluate(PROTOCOL, fetch)
    assert r["status"] == "SOURCE_STOP_UNAUTHORIZED_HOST"
    assert r["response_rows_opened"] == 0
    assert r["requests_attempted"] == [PROTOCOL["dataset"]["api_versions_url"]]
