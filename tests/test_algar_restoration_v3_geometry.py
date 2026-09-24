import json
from pathlib import Path

from eog.v2.git_blob_identity import git_blob_sha1
from validation.algar_restoration_v2_source_qualification.evaluate import evaluate as evaluate_source
from validation.algar_restoration_v3_geometry.evaluate_geometry import run_geometry


def contracts():
    geometry=json.loads(Path("validation/algar_restoration_v3_geometry/geometry_contract_v1_2.json").read_text())
    source=json.loads(Path("validation/algar_restoration_v2_source_qualification/source_qualification_contract.json").read_text())
    return geometry,source


def fixture():
    rows=["project_id,deployment_id,placename,longitude,latitude,start_date,end_date"]
    for i in range(38):
        for j in range(3):
            rows.append(f"P,D{i}_{j},S{i},{-112-i/1000},{56+i/1000},2018-01-01,2018-02-01")
    return ("\n".join(rows)+"\n").encode()


def test_v3_completes_ladder_before_world_generation():
    geometry,source=contracts()
    raw=fixture()
    source["source"]["safe_sources"][0]["git_blob_sha1"]=git_blob_sha1(raw)
    synthetic_source=evaluate_source(source,{"deployments":raw})
    geometry["source_qualification"]["certificate_fingerprint"]=synthetic_source["certificate_fingerprint"]
    # Synthetic geometry can differ in pass/fail, but finite-n completion itself is exact.
    result=run_geometry(geometry,source,raw)
    plan=result["adequacy_complete_plan"]
    assert plan["max_isolated_nodes"]==1
    assert 35/38 in plan["completed_targets"]
    assert 37/38 in plan["completed_targets"]
    assert plan["completed_targets"][-1]==37/38
    assert result["response_bytes_opened"]==0
    assert result["focal_species_selected"] is False
