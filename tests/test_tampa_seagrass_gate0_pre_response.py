import copy
import csv
import io
import json
from pathlib import Path

import pytest

from validation.tampa_seagrass_endpoint3 import gate0_pre_response as gate0


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "validation" / "tampa_seagrass_endpoint3" / "source_contract.json"


def _fold_covering_nodes():
    by_fold = {}
    i = 0
    while len(by_fold) < 5:
        node = f"TBEP:seagrass:loc:SYN{i:03d}"
        by_fold.setdefault(gate0.deterministic_fold(node), node)
        i += 1
    return [by_fold[fold] for fold in range(1, 6)]


def _row(header, **values):
    return {name: str(values.get(name, "")) for name in header}


def _synthetic_event_bytes(*, coordinate_drift=False, orphan_child=False, duplicate_event=False, empty_depth=False):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    header = contract["event_header"]
    rows = []
    nodes = _fold_covering_nodes()
    years = [2018, 2019, 2020]
    for node_index, node in enumerate(nodes):
        transect = node.rsplit(":", 1)[-1]
        lon0 = -82.70 + node_index * 0.035
        lat0 = 27.45 + node_index * 0.021
        water_body = f"Bay{node_index % 2 + 1}"
        for year_index, year in enumerate(years):
            lon = lon0
            if coordinate_drift and node_index == 0 and year_index == 1:
                lon += 0.0001
            parent_id = f"TBEP:seagrass:event:{transect}:{year}-06-15"
            rows.append(
                _row(
                    header,
                    eventID=parent_id,
                    parentEventID="",
                    eventType="Transect",
                    eventDate=f"{year}-06-15",
                    year=year,
                    month=6,
                    day=15,
                    decimalLatitude=lat0,
                    decimalLongitude=lon,
                    geodeticDatum="EPSG:4326",
                    country="United States",
                    countryCode="US",
                    stateProvince="Florida",
                    waterBody=water_body,
                    locality=f"{water_body} {transect}",
                    locationID=node,
                    samplingProtocol="seagrass transect survey",
                    institutionCode="TBEP",
                    datasetName="Synthetic Tampa",
                    datasetID="",
                    license="https://creativecommons.org/licenses/by/4.0/",
                    locationRemarks="synthetic",
                )
            )
            for child_index in range(3):
                child_parent = parent_id
                if orphan_child and node_index == 0 and year_index == 0 and child_index == 0:
                    child_parent = "UNKNOWN_PARENT"
                child_id = f"{parent_id}:{child_index}"
                if duplicate_event and node_index == 0 and year_index == 0 and child_index == 1:
                    child_id = f"{parent_id}:0"
                rows.append(
                    _row(
                        header,
                        eventID=child_id,
                        parentEventID=child_parent,
                        eventType="Point",
                        eventDate=f"{year}-06-15T10:{child_index:02d}:00",
                        year=year,
                        month=6,
                        day=15,
                        decimalLatitude=lat0,
                        decimalLongitude=lon,
                        geodeticDatum="EPSG:4326",
                        minimumDepthInMeters="" if empty_depth else 0.5 + child_index * 0.1,
                        maximumDepthInMeters="" if empty_depth else 0.5 + child_index * 0.1,
                        country="United States",
                        countryCode="US",
                        stateProvince="Florida",
                        waterBody=water_body,
                        locality=f"{water_body} {transect}",
                        locationID=f"{node}:{child_index}",
                        samplingProtocol="seagrass transect survey",
                        institutionCode="TBEP",
                        datasetName="Synthetic Tampa",
                        datasetID="",
                        license="https://creativecommons.org/licenses/by/4.0/",
                        locationRemarks="synthetic",
                    )
                )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _synthetic_contract(data):
    contract = copy.deepcopy(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")))
    contract["safe_files"]["event"]["size_bytes"] = len(data)
    contract["safe_files"]["event"]["git_blob_sha1"] = gate0.git_blob_sha1(data)
    contract["candidate_registry"]["minimum_unique_nodes"] = 5
    contract["candidate_registry"]["minimum_candidate_units"] = 15
    contract["candidate_registry"]["minimum_contexts"] = 3
    return contract


def _state():
    return {
        "safe_file_requests": 1,
        "safe_file_bytes_opened": 0,
        "occurrence_requests": 0,
        "occurrence_bytes_opened": 0,
        "occurrence_rows_opened": 0,
        "occurrence_values_opened": False,
        "emof_requests": 0,
        "emof_bytes_opened": 0,
        "emof_rows_opened": 0,
        "emof_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }


def test_git_blob_sha1_matches_git_object_formula():
    data = b"eventID,eventType\na,Transect\n"
    expected = __import__("hashlib").sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data
    ).hexdigest()
    assert gate0.git_blob_sha1(data) == expected


def test_synthetic_gate0_builds_normalized_response_locked_problem():
    data = _synthetic_event_bytes()
    contract = _synthetic_contract(data)
    state = _state()
    state["safe_file_bytes_opened"] = len(data)
    result = gate0.build_gate0_certificate(data, contract, state)

    assert result["status"] == "gate0_pre_response_ready"
    assert result["candidate_node_count"] == 5
    assert result["candidate_unit_count"] == 15
    assert result["context_ids"] == ["2018", "2019", "2020"]
    assert sorted(int(key) for key in result["fold_node_counts"]) == [1, 2, 3, 4, 5]
    assert all(result["fold_node_counts"][str(fold)] >= 1 for fold in range(1, 6))
    assert len(result["world_family"]["local_thresholds_km"]) >= 3
    assert result["world_family"]["external_open"] is True
    assert result["normalized_problem"]["schema"] == "eog.normalized_pre_response_problem.v1"
    assert result["normalized_problem"]["response_locked"] is True
    assert result["occurrence_requests"] == result["occurrence_bytes_opened"] == 0
    assert result["emof_requests"] == result["emof_bytes_opened"] == 0
    assert result["model_fits"] == result["heldout_scores"] == 0


def test_optional_depth_can_be_missing_without_adapter_stop():
    data = _synthetic_event_bytes(empty_depth=True)
    contract = _synthetic_contract(data)
    result = gate0.build_gate0_certificate(data, contract)
    assert result["status"] == "gate0_pre_response_ready"
    fields = {field["name"]: field for field in result["normalized_problem"]["baseline_fields"]}
    assert fields["depth_median_m"]["missing_policy"] == "calibration_median_plus_indicator"


def test_coordinate_drift_fails_closed():
    data = _synthetic_event_bytes(coordinate_drift=True)
    contract = _synthetic_contract(data)
    with pytest.raises(ValueError, match="stable transect coordinate drift"):
        gate0.build_gate0_certificate(data, contract)


def test_orphan_child_link_fails_closed():
    data = _synthetic_event_bytes(orphan_child=True)
    contract = _synthetic_contract(data)
    with pytest.raises(ValueError, match="unknown parent event"):
        gate0.build_gate0_certificate(data, contract)


def test_duplicate_event_id_fails_closed():
    data = _synthetic_event_bytes(duplicate_event=True)
    contract = _synthetic_contract(data)
    with pytest.raises(ValueError, match="duplicate eventID"):
        gate0.build_gate0_certificate(data, contract)


def test_wrong_blob_stops_without_response_access():
    data = _synthetic_event_bytes()
    contract = _synthetic_contract(data)
    contract["safe_files"]["event"]["git_blob_sha1"] = "0" * 40

    def fake_fetcher(file_spec, state):
        assert file_spec["path"] == "dwc/event.csv"
        state["safe_file_requests"] += 1
        state["safe_file_bytes_opened"] += len(data)
        return data

    result = gate0.execute_gate0(contract, fake_fetcher)
    assert result["status"] == "stop_pre_response_event_registry_geometry_or_schema"
    assert "Git blob mismatch" in result["reason"]
    assert result["occurrence_requests"] == result["occurrence_bytes_opened"] == 0
    assert result["occurrence_values_opened"] is False
    assert result["emof_requests"] == result["emof_bytes_opened"] == 0
    assert result["emof_values_opened"] is False
    assert result["model_fits"] == result["heldout_scores"] == 0


def test_execute_gate0_fetches_only_the_single_safe_event_file():
    data = _synthetic_event_bytes()
    contract = _synthetic_contract(data)
    calls = []

    def fake_fetcher(file_spec, state):
        calls.append(file_spec["path"])
        state["safe_file_requests"] += 1
        state["safe_file_bytes_opened"] += len(data)
        return data

    result = gate0.execute_gate0(contract, fake_fetcher)
    assert result["status"] == "gate0_pre_response_ready"
    assert calls == ["dwc/event.csv"]
    assert result["safe_file_requests"] == 1
    assert result["occurrence_requests"] == 0
    assert result["emof_requests"] == 0
