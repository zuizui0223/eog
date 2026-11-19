import io
import json
import runpy
import urllib.error
import urllib.request
import zipfile

import pytest


def _module():
    return runpy.run_path("scripts/glanville_minrelax_source_gate_v1.py")


def _csv(header, rows):
    return (",".join(header) + "\n" + "".join(",".join(map(str, row)) + "\n" for row in rows)).encode()


def _archive():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(
            "release/empirical_models/data/RAWDATA/fall_survey_2004_2013.csv",
            _csv(["Patch", "Year", "Network", "Area", "Centroid_X", "Centroid_Y",
                  "Occupancy", "Nest_count", "Vs", "Pl"], [
                      ["10", 2007, "N1", 50, 200000, 6700000, 1, 2, 3, 2],
                      ["11", 2008, "N1", 60, 200100, 6700100, 0, 0, 1, 2],
                  ]),
        )
        z.writestr(
            "release/empirical_models/data/RAWDATA/raw.snps.csv",
            _csv(["DNA", "Year", "Patch", "Centroid_X", "Centroid_Y"],
                 [["g001", 2007, "10", 200000, 6700000]]),
        )
        z.writestr(
            "release/empirical_models/data/RAWDATA/colonyFamilies.csv",
            _csv(["ID", "Year", "Region", "COLONY2 Family ID"],
                 [["g001", 2007, "Sottunga", "f1"]]),
        )
    return buffer.getvalue()


def _protocol():
    p = {
        "source": {
            "doi": "10.5061/dryad.905qfttrg",
            "file_stream_id": 3349312,
            "version_date": "2024-07-25",
            "download_url": "https://datadryad.org/downloads/file_stream/3349312",
        },
        "limits": {
            "archive_bytes_max": 25000000, "uncompressed_bytes_max": 160000000,
            "archive_members_max": 3000, "table_rows_max": 100000, "timeout_seconds": 40,
        },
        "expected_tables": {},
    }
    keys = {
        "fall_survey_2004_2013.csv": (2, ["Patch", "Year", "Network", "Area",
                                                "Centroid_X", "Centroid_Y",
                                                "Occupancy", "Nest_count", "Vs", "Pl"]),
        "raw.snps.csv": (1, ["DNA", "Year", "Patch", "Centroid_X", "Centroid_Y"]),
        "colonyFamilies.csv": (1, ["ID", "Year", "Region", "COLONY2 Family ID"]),
    }
    for name, (n, cols) in keys.items():
        p["expected_tables"][name] = {
            "expected_rows_publisher_readme": n, "required_columns": cols,
        }
    return p


class _FakeResponse(io.BytesIO):
    status = 200

    def geturl(self):
        return "https://datadryad.org/downloads/file_stream/3349312"


def test_source_header_and_join_gate_on_inline_synthetic_zip(monkeypatch, tmp_path):
    module = _module()
    data = _archive()
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: _FakeResponse(data))
    target = tmp_path / "receipt.json"
    result = module["qualify"](_protocol(), target)
    assert result["status"] == "SOURCE_STRUCTURE_JOIN_POSSIBLE_NOT_ECOLOGICAL_READY"
    assert result["archive_sha256"]
    assert result["scored_ecological_outcomes"] == 0
    assert result["model_fits"] == 0
    assert result["new_eogwf_predictive_endpoints"] == 0
    assert result["join_checks"]["genotype_patch_year_overlap_with_survey"] == 1
    assert result["join_checks"]["genotype_dna_year_overlap_with_family"] == 1
    assert all(row["matches_readme_row_count"] for row in result["tables"].values())
    assert json.loads(target.read_text()) == result


def test_http_forbidden_is_scientific_stop_not_source_success(monkeypatch, tmp_path):
    module = _module()

    def fail(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    result = module["qualify"](_protocol(), tmp_path / "stop.json")
    assert result["status"] == "STOP_TRANSPORT_HTTP_403"
    assert result["model_fits"] == 0
    assert result["new_eogwf_predictive_endpoints"] == 0


def test_schema_mismatch_blocks_inference(monkeypatch, tmp_path):
    module = _module()
    data = _archive()
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: _FakeResponse(data))
    contract = _protocol()
    contract["expected_tables"]["raw.snps.csv"]["required_columns"].append("missing_column")
    r = module["qualify"](contract, tmp_path / "schema_stop.json")
    assert r["status"].startswith("STOP_SCHEMA_MISSING_HEADERS")


def test_resource_limits_fail_closed(monkeypatch, tmp_path):
    module = _module()
    data = _archive()
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout: _FakeResponse(data))
    protocol = _protocol()
    protocol["limits"]["archive_bytes_max"] = 64
    r = module["qualify"](protocol, tmp_path / "budget_stop.json")
    assert r["status"] == "STOP_ARCHIVE_OVER_BYTE_LIMIT"
    assert "archive_sha256" not in r
