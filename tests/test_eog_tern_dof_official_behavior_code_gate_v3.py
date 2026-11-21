"""Synthetic DOF behavior vocabulary + location-QC tests, no real observations."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from scripts import eog_tern_dof_official_behavior_code_gate_v3 as v3

P=json.loads(Path("validation/tern_independent_dofbasen_behavior_semantics_v3/protocol_v3.json").read_text(encoding="utf-8"))
P2=json.loads(Path("validation/tern_independent_dofbasen_breeding_field_gate_v2/protocol_v2.json").read_text(encoding="utf-8"))
P2_RECEIPT=json.loads(Path("validation/tern_independent_dofbasen_breeding_field_gate_v2/frozen_field_receipt_v2.json").read_text(encoding="utf-8"))
SOURCE=json.loads(Path("validation/tern_independent_dofbasen_breeding_gate_v1/frozen_count_receipt_v1.json").read_text(encoding="utf-8"))


def publisher_fixture(*,all_unknown=False,drift_count=False,bad_species=False,notes=False):
    calls=[]
    windows=P2["source_sample_design"]["windows"]
    by={(w["from"],w["to"]):w for w in windows}
    def get(url,byte_cap,timeout):
        from urllib.parse import urlsplit,parse_qs
        parts=urlsplit(url)
        assert parts.hostname=="api.gbif.org"
        q=parse_qs(parts.query)
        assert q["datasetKey"]==["95db4db8-f762-11e1-a439-00145eb45e9a"]
        assert q["taxonKey"]==["5229230"]
        assert q["country"]==["DK"] and q["hasCoordinate"]==["true"]
        year=tuple(map(int,q["year"][0].split(",")))
        w=by[year]
        offset=int(q["offset"][0])
        assert offset in w["offsets"]
        wi=windows.index(w)
        pi=w["offsets"].index(offset)
        pageidx=wi*3+pi
        records=[]
        for i in range(100):
            n=pageidx*100+i
            uncertainty=1000 if n<304 else (1500 if n<1001 else (3000 if n<1488 else 15000))
            code="YF UR" if n%10==0 else ("YF B" if n%10==1 else ("YF" if n%10==2 else "R"))
            records.append({
                "gbifID":f"sensitive_row_{n}",
                "datasetKey":"95db4db8-f762-11e1-a439-00145eb45e9a",
                "speciesKey":0 if bad_species else 5229230,
                "taxonKey":5229230,
                "countryCode":"DK",
                "behavior":"Sensitive freeform observer and GPS info" if all_unknown else code,
                "coordinateUncertaintyInMeters":uncertainty,
                "lifeStage":"adult" if n<403 else None,
                "reproductiveCondition":None,
                "occurrenceRemarks":"private_resting_site_name" if notes else None,
                "decimalLatitude":55.167238,
                "decimalLongitude":12.8762345,
            })
        calls.append(url)
        return {"count":w["count"]+int(drift_count),"results":records},f"synthetic_sha_{pageidx}"
    return get,calls


def run_fixture(**args):
    fetch,calls=publisher_fixture(**args)
    result=v3.inspect_behavior_codebook(P,P2,SOURCE,P2_RECEIPT,fetch=fetch)
    return result,calls


def test_codebook_and_source_protocol_precede_original_behavior_values():
    assert P["status"]=="FROZEN_BEFORE_V3_BEHAVIOR_VALUE_READ"
    assert len(P["codebook"]["official_codes_to_report"])==31
    assert P["codebook"]["nest_evidence_codes"]==["YF B","YF BR","YF UR"]
    assert P["sources"]["parent_stage2_schema_sha"]==(
        P2_RECEIPT["execution"]["original_result_receipt_sha256_without_self"])
    assert P["output"]["observed_site_years_matched"]==0
    assert P["output"]["source_colonies_certified"]==0
    assert P["output"]["new_eogwf_endpoints"]==0


def test_synthetic_source_vocabulary_and_uncertainty_full_sample():
    data,calls=run_fixture()
    assert data["status"]=="DOF_OFFICIAL_BEHAVIOR_CODE_MATCHES_NOT_YET_SITE_YEAR_VALIDATION"
    assert len(calls)==15
    assert data["original_records_read_ephemerally"]==1500
    assert data["original_allowed_behavior_code_matches"]==1500
    assert data["unrecognized_behavior_count"]==0
    assert data["known_public_DOFBasen_code_histogram"]=={
        "R":1050, "YF":150, "YF B":150, "YF UR":150
    }
    assert data["reproduced_parent_field_presence_counts"]=={
        "behavior":1500,"lifeStage":403
    }
    assert data["reproduced_parent_coordinate_uncertainty_bins"]=={
        "MISSING":0,"LE_1000":304,"GT_1000_LE_2000":697,"GT_2000_LE_5000":487,
        "GT_5000_LE_20000":12,"GT_20000":0,"NONFINITE_OR_INVALID":0
    }
    assert data["tier_with_coordinate_uncertainty_LE_2km"]["NEST_EVIDENCE_POTENTIAL"]>0
    assert data["source_site_years_verified"]==0
    assert data["new_EOG_WF_endpoints"]==0
    assert "sensitive_row_" not in json.dumps(data)
    assert "55.167238" not in json.dumps(data)
    assert "12.8762345" not in json.dumps(data)


def test_unknown_behavior_is_not_promoted_to_breeding():
    result,calls=run_fixture(all_unknown=True)
    assert result["status"]=="STOP_GBIF_ALL_BEHAVIOR_VALUES_OUTSIDE_FROZEN_CODEBOOK"
    assert len(calls)==15
    assert result["unrecognized_behavior_count"]==1500
    assert result["source_breeding_colonies_verified"]==0
    assert "Sensitive freeform" not in json.dumps(result)


def test_original_source_count_drift_is_a_STOP():
    result,calls=run_fixture(drift_count=True)
    assert result["status"]=="STOP_GBIF_COUNT_DRIFT_AFTER_PREVIOUS_FIELD_GATE"
    assert len(calls)==1


def test_specimen_source_taxon_contamination_is_a_STOP():
    result,calls=run_fixture(bad_species=True)
    assert result["status"]=="STOP_DOFBASEN_RECORD_IDENTITY_CROSS_CONTAMINATION"
    assert result["source_breeding_colonies_verified"]==0


def test_new_occurrence_remarks_cannot_be_exported_or_silently_retrofit():
    data,calls=run_fixture(notes=True)
    assert data["status"]=="STOP_GBIF_SAMPLE_CHANGED_AFTER_PARENT_FIELD_RECEIPT"
    assert "private_resting_site_name" not in json.dumps(data)


def test_tampered_codebook_parent_or_sample_is_STOP_without_requests():
    changes=(
        lambda p:p.update(status="POST_FIELD_READ"),
        lambda p:p["sources"].update(parent_stage1_count_sha="0"*64),
        lambda p:p["codebook"]["official_codes_to_report"].append(
            {"code":"YF PRIVATE OWNER", "tier":"NEST_EVIDENCE_POTENTIAL"}),
        lambda p:p["codebook"]["nest_evidence_codes"].append("YF P"),
        lambda p:p["sample"].update(max_rows=15000),
    )
    for action in changes:
        tampered=deepcopy(P)
        action(tampered)
        fetch,calls=publisher_fixture()
        result=v3.inspect_behavior_codebook(tampered,P2,SOURCE,P2_RECEIPT,fetch=fetch)
        assert result["status"].startswith("STOP_")
        assert calls==[]


def test_normalization_no_fuzzy_breeding_codes():
    assert v3._normalize_code("  yf   ur ")=="YF UR"
    assert v3._normalize_code("Rastende")=="RASTENDE"
    assert v3._normalize_code("Somewhere nesting? Sensitive source") not in {
        "YF B", "YF BR", "YF UR"
    }
    assert v3._normalize_code(None) is None
