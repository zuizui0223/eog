import json
from pathlib import Path

from validation.algar_restoration_v2_prelock.gate0_safe_registry import (
    run_from_safe_bytes,
)


def _contract():
    return json.loads(
        Path(
            "validation/algar_restoration_v2_prelock/source_discovery_contract.json"
        ).read_text(encoding="utf-8")
    )


def test_algar_safe_registry_gate_without_response_content():
    deployments = (
        "project_id,deployment_id,placename,longitude,latitude,start_date,end_date,feature_type\n"
        + "\n".join(
            f"P,D{i}_{j},S{i},{-112.0-i/1000},{56.0+i/1000},2018-01-01,2018-02-01,Control"
            for i in range(1, 39)
            for j in range(1, 3)
        )
        + "\n"
    )
    projects = (
        "project_id,project_name,project_objectives,project_sensor_layout,project_stratification,data_citation\n"
        "P,Algar,habitat use,Stratified,Treatments,Citation\n"
    )
    result = run_from_safe_bytes(
        _contract(),
        deployments_text=deployments,
        projects_text=projects,
    )
    assert result["status"] == "ready_for_geometry_gate"
    assert result["candidate_ready"] is True
    assert result["candidate_locked"] is False
    assert result["focal_species_selected"] is False
    assert result["response_rows_opened"] is False
    assert result["response_bytes_opened"] is False
    assert result["safe_registry"]["canonical_location_count"] == 38
    assert result["safe_registry"]["repeated_location_count"] == 38


def test_coordinate_drift_blocks_closed_registry_gate():
    rows = []
    for i in range(1, 39):
        rows.append(
            f"P,D{i}_1,S{i},{-112.0-i/1000},{56.0+i/1000},2018-01-01,2018-02-01,Control"
        )
        lon2 = -112.0 - i / 1000
        if i == 1:
            lon2 -= 0.01
        rows.append(
            f"P,D{i}_2,S{i},{lon2},{56.0+i/1000},2018-02-01,2018-03-01,Control"
        )
    deployments = (
        "project_id,deployment_id,placename,longitude,latitude,start_date,end_date,feature_type\n"
        + "\n".join(rows)
        + "\n"
    )
    projects = (
        "project_id,project_name,project_objectives,project_sensor_layout,project_stratification,data_citation\n"
        "P,Algar,habitat use,Stratified,Treatments,Citation\n"
    )
    result = run_from_safe_bytes(
        _contract(),
        deployments_text=deployments,
        projects_text=projects,
    )
    assert result["status"] == "stop_analysis_registry_not_closed"
    assert result["candidate_ready"] is False
    assert result["safe_registry"]["coordinate_drift_location_count"] == 1
