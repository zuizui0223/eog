import json
from pathlib import Path

from eog.v2.git_blob_identity import git_blob_sha1
from validation.algar_restoration_v2_source_qualification.evaluate import evaluate


def contract():
    return json.loads(
        Path(
            "validation/algar_restoration_v2_source_qualification/"
            "source_qualification_contract.json"
        ).read_text(encoding="utf-8")
    )


def test_response_blind_source_qualification_can_reach_candidate_lock():
    value = contract()
    rows = [
        "project_id,deployment_id,placename,longitude,latitude,start_date,end_date"
    ]
    for i in range(38):
        for j in range(3):
            rows.append(
                f"P,D{i}_{j},S{i},{-112-i/1000},{56+i/1000},2018-01-01,2018-02-01"
            )
    payload = ("\n".join(rows) + "\n").encode()
    value["source"]["safe_sources"][0]["git_blob_sha1"] = git_blob_sha1(payload)
    result = evaluate(value, {"deployments": payload})
    assert result["status"] == "ready_for_candidate_lock"
    assert result["candidate_lock_allowed"] is True
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["response_bytes_opened"] == 0
    assert result["registry"]["canonical_node_count"] == 38
    assert result["registry"]["repeated_node_count"] == 38


def test_strict_mode_accepts_one_coordinate_outlier_with_two_of_three_support():
    value = contract()
    rows = [
        "project_id,deployment_id,placename,longitude,latitude,start_date,end_date"
    ]
    for i in range(38):
        for j in range(3):
            lon = -112 - i / 1000
            if i == 0 and j == 0:
                lon -= 1
            rows.append(
                f"P,D{i}_{j},S{i},{lon},{56+i/1000},2018-01-01,2018-02-01"
            )
    payload = ("\n".join(rows) + "\n").encode()
    value["source"]["safe_sources"][0]["git_blob_sha1"] = git_blob_sha1(payload)
    result = evaluate(value, {"deployments": payload})
    assert result["candidate_lock_allowed"] is True
    audit = next(
        row for row in result["registry"]["coordinate_audit"]
        if row["placename"] == "S0"
    )
    assert audit["coordinate_variant_count"] == 2
    assert audit["modal_support"] == 2 / 3
    assert audit["accepted"] is True


def test_coordinate_tie_stops_closed_registry():
    value = contract()
    rows = [
        "project_id,deployment_id,placename,longitude,latitude,start_date,end_date"
    ]
    for i in range(38):
        count = 2 if i == 0 else 3
        for j in range(count):
            lon = -112 - i / 1000
            if i == 0 and j == 1:
                lon -= 1
            rows.append(
                f"P,D{i}_{j},S{i},{lon},{56+i/1000},2018-01-01,2018-02-01"
            )
    payload = ("\n".join(rows) + "\n").encode()
    value["source"]["safe_sources"][0]["git_blob_sha1"] = git_blob_sha1(payload)
    result = evaluate(value, {"deployments": payload})
    assert result["candidate_lock_allowed"] is False
    assert result["layers"]["candidate_preflight"] == "stop_analysis_registry_not_closed"
