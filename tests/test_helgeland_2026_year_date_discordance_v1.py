"""Fully synthetic source bytes; no actual house-sparrow values in unit tests."""
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
from audit_helgeland_2026_year_date_discordance_v1 import analyze
from audit_helgeland_2026_upstream_byte_parity_v1 import TARGETS
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header


def fake_sources(tmp_path):
    contract=copy.deepcopy(json.loads((BASE/"helgeland_2026_year_date_exploratory_contract_v1.json").read_text()))
    frozen=copy.deepcopy(json.loads((BASE/"helgeland_2026_source_metadata_frozen_v1.json").read_text()))
    headers=copy.deepcopy(json.loads((BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json").read_text()))
    root=tmp_path/"checkout"
    original_rows=[
        ("2000","2000-05-01"),
        ("2001","2000-12-31"),
        ("1999","2000-01-01"),
        ("2023","2023-01-05"),
        ("1998","2000-01-01"),
        ("2002","2000-06-01"),
    ]
    for name,dryad in TARGETS.items():
        f=root/name
        f.parent.mkdir(parents=True,exist_ok=True)
        if name.endswith("/presence_data_1994_2022.txt"):
            col=["Year","date","scriptsex","Island","Location","stage","Least_age","Least_hatchyear","ID"]
            content=";".join(col)+"\n"
            for n,(y,d) in enumerate(original_rows):
                content+=f"{y};{d};X;0;SYNTHETIC;nest;0;{y};fake{n}\n"
        else:
            content="Location;Island;Year;N_corr;.lower;.upper;.width;N_obs\nSYNTHETIC;0;2000;1;0;2;0.9;1\n"
        raw=content.encode()
        f.write_bytes(raw)
        element=next(x for x in frozen["files"] if x["name"]==dryad)
        element["size_bytes"]=len(raw)
        element["source_declared_sha256"]=hashlib.sha256(raw).hexdigest()
        if name.endswith("/presence_data_1994_2022.txt"):
            physical, firstline_sha=read_first_physical_header(f)
            hdr=next(h for h in headers["headers"] if h["github_path"]==name)
            hdr["column_names"]=physical
            hdr["first_line_sha256"]=firstline_sha
    contract["prior_exposed_counts"]={
        "row_count":6,"year_date_disagreement_count":4,
        "year_date_matching_outside_1994_2022_count":1}
    return root,contract,frozen,headers


def test_deltas_months_and_outside_years_without_ids(tmp_path):
    root,c,f,h=fake_sources(tmp_path)
    r=analyze(root,c,f,h)
    assert r["status"]=="YEAR_DATE_DISCREPANCY_DESCRIBED__MEANING_UNRESOLVED"
    assert r["total_rows"]==6
    assert r["all_year_delta_bin_counts"]=={
        "<=-2":1,"-1":1,"0":2,"+1":1,">=+2":1}
    assert r["discordant_by_calendar_month"]=={
        "01":2,"02":0,"03":0,"04":0,"05":0,"06":1,
        "07":0,"08":0,"09":0,"10":0,"11":0,"12":1}
    assert r["consistent_year_outside_window"]==1
    assert r["out_of_range_year_value_counts"]=={"before_1994":0,"after_2022":1}
    assert r["source_year_date_semantics_resolved"] is False
    assert r["ecological_endpoint_authorized"] is False
    assert "fake0" not in json.dumps(r) and "SYNTHETIC" not in json.dumps(r)


def test_unmatched_source_byte_hash_stops_before_observations(tmp_path):
    root,c,f,h=fake_sources(tmp_path)
    target=root/"Data/presence_data_1994_2022.txt"
    old=target.read_bytes()
    target.write_bytes(old.replace(b"fake0",b"FAKE0"))
    assert target.stat().st_size==len(old)
    with pytest.raises(ValueError,match="SHA256 parity"):
        analyze(root,c,f,h)


def test_post_exposure_status_cannot_be_changed(tmp_path):
    root,c,f,h=fake_sources(tmp_path)
    c["status"]="BEFORE_EVER_READING_REAL_BIRD_DATA"
    with pytest.raises(ValueError,match="exploratory contract"):
        analyze(root,c,f,h)


def test_earlier_known_discordance_counts_must_not_silently_change(tmp_path):
    root,c,f,h=fake_sources(tmp_path)
    c["prior_exposed_counts"]["year_date_disagreement_count"]=0
    with pytest.raises(ValueError,match="previously frozen"):
        analyze(root,c,f,h)


def test_only_year_date_inspected_and_individual_data_never_emitted():
    s=(ROOT/"scripts/audit_helgeland_2026_year_date_discordance_v1.py").read_text()
    assert 'row["Year"]' in s and 'row["date"]' in s
    for forbidden in ('row["ID"]','row["Island"]','row["Location"]',
                      'row["stage"]','read_csv(', 'import pandas', 'import numpy',
                      'urlopen(', 'requests.get('):
        assert forbidden not in s
    c=json.loads((BASE/"helgeland_2026_year_date_exploratory_contract_v1.json").read_text())
    assert c["status"]=="FROZEN_AFTER_STRUCTURAL_QC_RESULT_EXPOSURE__BEFORE_THIS_FOLLOWUP"
    assert c["read_only_columns"]==["Year","date"]
    assert c["flags"]["as_of_t_qualified"] is False


def test_first_real_exploratory_month_offset_receipt_frozen_without_inference():
    frozen=json.loads((BASE/"helgeland_2026_year_date_discordance_frozen_v1.json").read_text())
    assert frozen["schema"]=="eog.helgeland.2026.observation_year_date_postexposure.frozen_observed_v1"
    assert frozen["authority"]["github_actions_run_id"]==37801160828
    assert frozen["authority"]["artifact_id"]==11560154008
    assert frozen["authority"]["artifact_zip_sha256"]==(
        "9a1f4ab9c511ecc7343cfd5eedcf3cf731a7336588b82310fdd9b3a89f661d02"
    )
    assert frozen["all_year_delta_bin_counts"]=={
        "<=-2":0,"-1":3517,"0":70076,"+1":0,">=+2":0}
    assert sum(frozen["discordant_by_calendar_month"].values())==3517
    assert [frozen["discordant_by_calendar_month"][f"{i:02}"] for i in range(1,4)]==[1007,1180,1330]
    assert all(frozen["discordant_by_calendar_month"][f"{i:02}"]==0 for i in range(4,13))
    assert frozen["consistent_year_outside_window"]==914
    assert frozen["interpretation"]["source_year_date_semantics_resolved"] is False
    assert frozen["interpretation"]["correction_approved"] is False
    assert frozen["interpretation"]["post_exposure_exploratory"] is True
    assert frozen["ecological_endpoint_authorized"] is False
