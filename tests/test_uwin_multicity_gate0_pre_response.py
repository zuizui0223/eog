import copy
import csv
import io
import json
from pathlib import Path

import pytest

from validation.uwin_multicity_endpoint3.gate0_pre_response import (
    Gate0Stop,
    _fold,
    evaluate_pre_response,
    git_blob_sha1,
    run,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation" / "uwin_multicity_endpoint3" / "source_contract.json"


def base_contract():
    value = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    value["candidate_registry"]["minimum_unique_sites"] = 50
    value["candidate_registry"]["minimum_candidate_site_seasons"] = 200
    value["focal_selection"]["minimum_in_range_cities"] = 10
    return value


def csv_bytes(header, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def synthetic_payloads(*, housing_complete=True, tie=False):
    cities = base_contract()["city_codes"]
    coord_rows = []
    cov_rows = []
    seasons = ["JA19", "AP19", "JU19", "OC19"]
    for city_index, city in enumerate(["atga", "autx"]):
        for i in range(30):
            site = f"{city.upper()}{i:03d}"
            lon = -84.5 + city_index * 1.5 + i * 0.002
            lat = 33.7 + city_index * 0.7 + (i % 7) * 0.003
            coord_rows.append([site, f"{lon:.6f}", f"{lat:.6f}", "4326", city])
            for season_index, season in enumerate(seasons):
                cov_rows.append([
                    site,
                    city,
                    season,
                    25 + i,
                    10 + i * 0.1,
                    30000 + i * 100,
                    0.2 + i * 0.001,
                    1000 + i * 10,
                    2 + season_index * 0.1,
                ])
    coords = csv_bytes(["Site", "Long", "Lat", "Crs", "City"], coord_rows)
    covs = csv_bytes(
        ["Site", "City", "Season", "Building_age", "Impervious", "Income", "Ndvi", "Population_density", "Vacancy"],
        cov_rows,
    )

    header = ["", *cities]
    coyote = ["coyote", *[float(i + 1) for i in range(len(cities))]]
    fox = ["red_fox", *[(1.0 if i < (20 if tie else 7) else -1.0) for i in range(len(cities))]]
    ranges = csv_bytes(header, [coyote, fox])

    housing_rows = []
    for city in ["atga", "autx"]:
        for season_index, season in enumerate(seasons):
            if not housing_complete and city == "autx" and season == "OC19":
                continue
            housing_rows.append([city, season, 900 + season_index * 25])
    housing = csv_bytes(["City", "Season", "Price"], housing_rows)
    return {
        "site_coordinates": coords,
        "site_covariates": covs,
        "range_availability": ranges,
        "housing_cost": housing,
    }


def bind_payloads(contract, payloads):
    contract = copy.deepcopy(contract)
    for role, raw in payloads.items():
        source = contract["source"]["safe_files"][role]
        source["size_bytes"] = len(raw)
        source["git_blob_sha1"] = git_blob_sha1(raw)
        source["raw_url"] = f"https://raw.githubusercontent.com/example/repo/frozen/{role}.csv"
    contract["gate0_firewall"]["maximum_safe_file_bytes_total"] = sum(map(len, payloads.values())) + 1
    return contract


def test_synthetic_gate0_passes_and_freezes_normalized_problem():
    payloads = synthetic_payloads()
    contract = bind_payloads(base_contract(), payloads)
    result = evaluate_pre_response(payloads, contract)
    assert result["status"] == "gate0_pre_response_ready"
    assert result["selected_focal_species"] == "coyote"
    assert result["focal_in_range_city_count"] == 20
    assert result["candidate_site_count"] == 60
    assert result["candidate_site_season_count"] == 240
    assert sorted(map(int, result["site_fold_counts"])) == [1, 2, 3, 4, 5]
    assert len(result["geometry"]["local_worlds"]) >= 3
    assert result["geometry"]["external_open"]["world_id"] == "external_open"
    assert result["housing_cost_included"] is True
    assert result["normalized_problem_contract"]["node_role"].startswith("City|Site")
    assert result["response_file_requests"] == 0
    assert result["response_values_opened"] is False


def test_focal_selection_tie_is_lexicographic():
    payloads = synthetic_payloads(tie=True)
    contract = bind_payloads(base_contract(), payloads)
    result = evaluate_pre_response(payloads, contract)
    assert result["range_selection_tie_count"] == 2
    assert result["selected_focal_species"] == "coyote"


def test_incomplete_housing_is_omitted_response_independently():
    payloads = synthetic_payloads(housing_complete=False)
    contract = bind_payloads(base_contract(), payloads)
    result = evaluate_pre_response(payloads, contract)
    assert result["status"] == "gate0_pre_response_ready"
    assert result["housing_cost_included"] is False
    assert "lack housing cost" in result["housing_cost_decision"]
    assert "housing_cost_price" not in result["baseline"]["feature_names"]


def test_duplicate_candidate_row_stops():
    payloads = synthetic_payloads()
    text = payloads["site_covariates"].decode("utf-8")
    first_data = text.splitlines()[1]
    payloads["site_covariates"] = (text + first_data + "\n").encode("utf-8")
    contract = bind_payloads(base_contract(), payloads)
    with pytest.raises(Gate0Stop, match="duplicate candidate source row"):
        evaluate_pre_response(payloads, contract)


def test_run_reads_exactly_four_safe_files_and_never_requests_response(tmp_path):
    payloads = synthetic_payloads()
    contract = bind_payloads(base_contract(), payloads)
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    by_url = {
        contract["source"]["safe_files"][role]["raw_url"]: raw
        for role, raw in payloads.items()
    }
    seen = []

    def fetch_bytes(url, maximum):
        seen.append(url)
        raw = by_url[url]
        assert len(raw) <= maximum
        return raw

    result = run(contract_path, tmp_path / "certificate.json", fetch_bytes=fetch_bytes)
    assert result["status"] == "gate0_pre_response_ready"
    assert len(seen) == 4
    assert result["safe_file_requests"] == 4
    assert result["response_file_requests"] == 0
    assert result["response_header_bytes_opened"] == 0
    assert result["response_payload_bytes_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == result["heldout_scores"] == 0


def test_source_drift_stops_without_response_access(tmp_path):
    payloads = synthetic_payloads()
    contract = bind_payloads(base_contract(), payloads)
    contract["source"]["safe_files"]["site_coordinates"]["git_blob_sha1"] = "0" * 40
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    by_url = {
        contract["source"]["safe_files"][role]["raw_url"]: raw
        for role, raw in payloads.items()
    }

    result = run(
        contract_path,
        tmp_path / "certificate.json",
        fetch_bytes=lambda url, maximum: by_url[url],
    )
    assert result["status"] == "stop_pre_response_source_registry_or_geometry"
    assert result["response_file_requests"] == 0
    assert result["response_payload_bytes_opened"] == 0
    assert result["response_values_opened"] is False


def test_synthetic_site_hashes_cover_all_folds():
    payloads = synthetic_payloads()
    rows = list(csv.DictReader(io.StringIO(payloads["site_coordinates"].decode("utf-8"))))
    folds = {_fold(row["City"], row["Site"]) for row in rows}
    assert folds == {1, 2, 3, 4, 5}
