import copy
import json
from pathlib import Path

import pytest

from validation.hokkaido_streamfish_endpoint3.pre_response_geometry import (
    PreResponseStop,
    evaluate_pre_response,
    git_blob_sha1,
    load_contract,
    parse_coordinate_registry,
)


HERE = Path(__file__).resolve().parents[1] / "validation" / "hokkaido_streamfish_endpoint3"


def _synthetic_inputs():
    rows = ["ID,river,site,longitude,latitude,source"]
    row_id = 1
    for river, lon0, lat0 in (("alpha", 141.0, 43.0), ("beta", 143.0, 42.0)):
        for site in range(1, 6):
            rows.append(
                f"{row_id},{river},{site},{lon0 + 0.01 * site:.4f},{lat0 + 0.007 * site:.4f},synthetic"
            )
            row_id += 1
    coordinate = ("\n".join(rows) + "\n").encode("utf-8")
    code = b"\n".join(
        [
            b'site_id = paste0(river, site)',
            b'latin == "Noemacheilus_barbatulus" ~ "Barbatula_oreas"',
            b'"usubetsu4", "atsuta6", "kokamotsu4"',
            b'read_csv(here::here("data_fmt/data_hkd_prtwsd_fmt.csv"))',
        ]
    ) + b"\n"
    contract = copy.deepcopy(load_contract())
    contract["source"]["coordinate_registry"]["git_blob_sha1"] = git_blob_sha1(coordinate)
    contract["source"]["coordinate_registry"]["size_bytes"] = len(coordinate)
    contract["source"]["formatting_code"]["git_blob_sha1"] = git_blob_sha1(code)
    contract["source"]["formatting_code"]["size_bytes"] = len(code)
    contract["pre_response_registry"]["expected_physical_rows"] = 10
    contract["pre_response_registry"]["expected_missing_coordinate_site_ids"] = []
    contract["pre_response_registry"]["expected_valid_coordinate_nodes"] = 10
    return coordinate, code, contract


def test_synthetic_pre_response_geometry_passes_without_response_data():
    coordinate, code, contract = _synthetic_inputs()
    result = evaluate_pre_response(coordinate, code, contract)
    assert result["status"] == "pre_response_geometry_ready"
    assert result["valid_node_count"] == 10
    assert result["fold_counts"] == {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2}
    assert len(result["world_geometry"]["local_worlds"]) >= 3
    assert result["world_geometry"]["external_open"]["world_id"] == "external_open"
    assert result["response_table_requests"] == 0
    assert result["response_table_bytes_opened"] == 0
    assert result["response_rows_opened"] == 0
    assert result["response_values_opened"] is False
    assert result["model_fits"] == 0
    assert result["heldout_scores"] == 0


def test_coordinate_registry_rejects_unfrozen_missingness():
    coordinate, _, contract = _synthetic_inputs()
    text = coordinate.decode("utf-8").replace(
        "1,alpha,1,141.0100,43.0070,synthetic",
        "1,alpha,1,NA,NA,synthetic",
    )
    mutated = text.encode("utf-8")
    contract["source"]["coordinate_registry"]["git_blob_sha1"] = git_blob_sha1(mutated)
    contract["source"]["coordinate_registry"]["size_bytes"] = len(mutated)
    with pytest.raises(PreResponseStop, match="missing-coordinate site set drift"):
        parse_coordinate_registry(mutated, contract)


def test_source_contract_keeps_response_file_forbidden_before_final_gate():
    contract = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
    response = contract["source"]["forbidden_response_table"]
    assert response["path"] == "data_fmt/data_hkd_prtwsd_fmt.csv"
    assert response["git_blob_sha1"] == "d0544a56b168511fa2c85c4199372599922e5651"
    assert response["payload_requests_before_final_response_authorization"] == 0
    assert response["payload_bytes_before_final_response_authorization"] == 0
    assert contract["hard_stop"]["response_file_open_before_final_freeze_allowed"] is False
