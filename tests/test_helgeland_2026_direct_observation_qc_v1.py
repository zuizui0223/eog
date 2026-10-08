"""All tests use fabricated ring/encounter records, never published bird outcomes."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_2026_direct_observation_qc_v1 import structural_qc
from audit_helgeland_2026_upstream_byte_parity_v1 import TARGETS
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header


def fixtures(tmp_path):
    protocol=json.loads((BASE/"helgeland_2026_direct_observation_qc_protocol_v1.json").read_text())
    frozen=copy.deepcopy(json.loads((BASE/"helgeland_2026_source_metadata_frozen_v1.json").read_text()))
    head=copy.deepcopy(json.loads((BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json").read_text()))
    upstream=tmp_path/"upstream"
    by_name={x["name"]:x for x in frozen["files"]}
    presence_header=';'.join(f'"{x}"' for x in protocol["required_exact_columns"])+"\n"
    rows=[
        ["2000","2000-05-01","F","11","Aldra","nest","0","2000","nest01"],
        ["2001","2001-05-02","F","11","Aldra","capt","1","2000","nest01"],
        ["2001","2001-05-02","F","11","Aldra","capt","1","2000","nest01"],
        ["2000","2000-04-01","M","11","Aldra","nest","0","2000","nest02"],
        ["2000","2000-04-02","M","22","Elsewhere","nest","0","2000","nest02"],
        ["2001","2001-05-03","M","22","Elsewhere","obs","1","2000","nest02"],
        ["2001","bad-date","F","11","Aldra","capt","1","2000","bad01"],
        ["2002","2001-07-02","F","11","Aldra","obs","1","2000","bad02"],
        ["2001","2001-07-02","F","11","Aldra","unclassified","1","2000","unknown"],
    ]
    data=(presence_header+"".join(";".join(f'"{v}"' for v in row)+"\n" for row in rows)).encode()
    for path_name,dryad_name in TARGETS.items():
        output=upstream/path_name
        output.parent.mkdir(parents=True,exist_ok=True)
        raw=data if path_name.endswith("presence_data_1994_2022.txt") else (
            "Location;Island;Year;N_corr;.lower;.upper;.width;N_obs\nA;11;2000;1;0;2;0.9;1\n"
        ).encode()
        output.write_bytes(raw)
        meta=by_name[dryad_name]
        meta["source_declared_sha256"]=hashlib.sha256(raw).hexdigest()
        meta["size_bytes"]=len(raw)
        if path_name.endswith("presence_data_1994_2022.txt"):
            col,sha=read_first_physical_header(output)
            hdr=next(x for x in head["headers"] if x["github_path"]==path_name)
            hdr["column_names"]=col
            hdr["first_line_sha256"]=sha
    return upstream,frozen,head,protocol


def test_structural_quality_receipt_emits_only_aggregates_and_never_licenses_ecology(tmp_path):
    root,dryad,headers,contract=fixtures(tmp_path)
    report=structural_qc(root,dryad,headers,contract)
    assert report["status"]=="STRUCTURAL_QC_ONLY__TEMPORAL_AND_ECOLOGICAL_HOLD"
    counts=report["counts"]
    assert counts["row_count"]==9
    assert counts["duplicate_exact_observation_count"]==1
    assert counts["multi_nest_island_id_count"]==1
    assert counts["unparseable_date_count"]==1
    assert counts["date_year_disagreement_count"]==1
    assert counts["unrecognized_stage_count"]==1
    assert counts["ids_with_one_nest_island_and_any_later_direct_observation"]==1
    assert report["ecological_endpoint_authorized"] is False
    assert report["surveyed_zero_panel_verified"] is False
    assert report["individual_ids_or_row_values_exported"] is False
    assert "nest01" not in json.dumps(report)
    assert "Elsewhere" not in json.dumps(report)


def test_equal_length_source_row_tamper_fails_source_byte_identity(tmp_path):
    root,dryad,headers,contract=fixtures(tmp_path)
    p=root/"Data/presence_data_1994_2022.txt"
    before=p.read_bytes()
    p.write_bytes(before.replace(b"nest01",b"other1"))
    assert len(before)==p.stat().st_size
    with pytest.raises(ValueError,match="Source byte identity"):
        structural_qc(root,dryad,headers,contract)


def test_source_header_mismatch_fails_before_record_qc(tmp_path):
    root,dryad,headers,contract=fixtures(tmp_path)
    headers["headers"][0]["first_line_sha256"]="0"*64
    with pytest.raises(ValueError,match="Physical header differs"):
        structural_qc(root,dryad,headers,contract)


def test_unsupported_protocol_does_not_enable_scoring(tmp_path):
    root,dryad,headers,contract=fixtures(tmp_path)
    contract["claim_boundary"]["biological_scoring_authorized"]=True
    with pytest.raises(ValueError,match="Biological scoring"):
        structural_qc(root,dryad,headers,contract)


def test_preregistered_output_contract_has_no_per_bird_data_fields():
    contract=json.loads((BASE/"helgeland_2026_direct_observation_qc_protocol_v1.json").read_text())
    assert "observed_cross_island_dispersal_count" in contract["prohibited_outputs"]
    assert "individual_ID_values" in contract["prohibited_outputs"]
    assert "column_count_mismatch_rows" in contract["allowed_output_aggregates"]
    assert contract["claim_boundary"]["biological_scoring_authorized"] is False
