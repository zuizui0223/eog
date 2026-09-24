import json
from pathlib import Path

from eog.v2.git_blob_identity import git_blob_sha1
from validation.algar_restoration_v2_source_qualification.evaluate import (
    evaluate as evaluate_source,
)
from validation.algar_restoration_v3_preresponse.build_manifest import (
    build_preresponse,
)


COORDINATES = {
    "ALG027": (-112.4735026, 56.33279633),
    "ALG029": (-112.548348, 56.3947384),
    "ALG031": (-112.4819778, 56.30899115),
    "ALG032": (-112.3967723, 56.40196543),
    "ALG035": (-112.4760892, 56.38427981),
    "ALG036": (-112.4057856, 56.23177668),
    "ALG037": (-112.4449259, 56.27897671),
    "ALG038": (-112.4791766, 56.27038626),
    "ALG039": (-112.4094357, 56.30127467),
    "ALG043": (-112.5842114, 56.38715078),
    "ALG044": (-112.6046929, 56.47314996),
    "ALG045": (-112.5018971, 56.43667907),
    "ALG046": (-112.5607123, 56.33379516),
    "ALG047": (-112.4563346, 56.21704844),
    "ALG048": (-112.4553341, 56.23532818),
    "ALG049": (-112.5483653, 56.37320857),
    "ALG052": (-112.4453138, 56.34019101),
    "ALG053": (-112.5515799, 56.45544966),
    "ALG054": (-112.6467312, 56.421884),
    "ALG055": (-112.5868312, 56.35276482),
    "ALG056": (-112.605999, 56.42602126),
    "ALG057": (-112.4266152, 56.16541237),
    "ALG058": (-112.6308865, 56.41724102),
    "ALG059": (-112.4953724, 56.36631122),
    "ALG060": (-112.5180163, 56.35477698),
    "ALG061": (-112.4415123, 56.15983008),
    "ALG062": (-112.4104105, 56.20002261),
    "ALG063": (-112.4785381, 56.2308028),
    "ALG064": (-112.3965139, 56.27622558),
    "ALG065": (-112.3847975, 56.35152984),
    "ALG066": (-112.3950852, 56.3239189),
    "ALG067": (-112.5517103, 56.35670497),
    "ALG068": (-112.4737099, 56.36418948),
    "ALG069": (-112.5074726, 56.49351647),
    "ALG070": (-112.5314177, 56.45203396),
    "ALG071": (-112.5802163, 56.42405201),
    "ALG072": (-112.5465368, 56.42079233),
    "ALG073": (-112.436108, 56.30917208),
}


def _safe_fixture() -> bytes:
    header = (
        "project_id,deployment_id,placename,longitude,latitude,"
        "start_date,end_date,feature_type"
    )
    rows = [header]
    phase_dates = (
        ("2018-04-08", "2018-11-14"),
        ("2018-11-15", "2019-04-03"),
        ("2019-04-03", "2019-11-20"),
    )
    for node_id in sorted(COORDINATES):
        lon, lat = COORDINATES[node_id]
        for phase, (start, end) in enumerate(phase_dates, start=1):
            observed_lon = lon
            if node_id == "ALG069" and phase == 1:
                observed_lon = -113.5075
            observed_end = "NA" if node_id == "ALG027" and phase == 3 else end
            rows.append(
                f"P,{node_id}_D{phase},{node_id},{observed_lon},{lat},"
                f"{start},{observed_end},Offline"
            )
    return ("\n".join(rows) + "\n").encode("utf-8")


def _contracts(raw: bytes):
    source = json.loads(
        Path(
            "validation/algar_restoration_v2_source_qualification/"
            "source_qualification_contract.json"
        ).read_text(encoding="utf-8")
    )
    pre = json.loads(
        Path(
            "validation/algar_restoration_v3_preresponse/"
            "preresponse_contract.json"
        ).read_text(encoding="utf-8")
    )
    source["source"]["safe_sources"][0]["git_blob_sha1"] = git_blob_sha1(raw)
    source_result = evaluate_source(source, {"deployments": raw})
    pre["predecessor"]["source_qualification_certificate_fingerprint"] = (
        source_result["certificate_fingerprint"]
    )
    return source, pre


def test_algar_v3_preresponse_manifest_reaches_layer_b_eligibility(tmp_path):
    raw = _safe_fixture()
    source, pre = _contracts(raw)
    result = build_preresponse(
        pre,
        source,
        raw,
        output_dir=tmp_path,
    )

    assert result["status"] == "preresponse_manifest_ready"
    assert result["response_bytes_opened"] == 0
    assert result["focal_species_selected"] is False
    assert sorted(result["folds"]["fold_counts"]) == [9, 9, 10, 10]

    manifest = result["manifest_result"]
    assert manifest["counts"] == {
        "node_count": 38,
        "context_count": 3,
        "scored_candidate_count": 75,
        "initialization_count": 38,
        "unsurveyed_count": 1,
        "declared_world_count": 6,
        "structural_world_count": 5,
    }
    assert manifest["statuses"]["structural"] == "structural_ready"
    assert (
        manifest["statuses"]["effort"]
        == "response_independent_effort_declared"
    )
    assert manifest["statuses"]["observation"] == "complete_source_zero"
    assert (
        manifest["statuses"]["predictive"]
        == "predictive_complement_candidate"
    )
    assert manifest["statuses"]["predictive_use_allowed"] is True
    assert manifest["statuses"]["predictive_outcome_access_allowed"] is False
    assert (
        manifest["fingerprints"]["structural_gate"]
        == "5d36e3a67c731e1ba841019ce0e44cc44d721aa6963ef91051cc15d85c15dbe6"
    )


def test_algar_v3_unsurveyed_unit_is_frozen_before_response(tmp_path):
    raw = _safe_fixture()
    source, pre = _contracts(raw)
    result = build_preresponse(
        pre,
        source,
        raw,
        output_dir=tmp_path,
    )
    effort = (tmp_path / "effort.csv").read_text(encoding="utf-8")
    assert "ALG027|phase3,ALG027,phase3" in effort
    assert ",false,unsurveyed," in effort
    assert result["manifest_result"]["counts"]["unsurveyed_count"] == 1
