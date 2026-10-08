"""Synthetic-only counterexample tests for post-exposure April boundary hypothesis."""
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
from audit_helgeland_2026_april_boundary_postexposure_v1 import inspect
from audit_helgeland_2026_upstream_byte_parity_v1 import TARGETS
from audit_helgeland_2026_two_file_headers_v1 import read_first_physical_header


def build(tmp_path,janmar_same=True):
    c=json.loads((BASE/"helgeland_2026_april_boundary_postexposure_contract_v1.json").read_text())
    f=json.loads((BASE/"helgeland_2026_source_metadata_frozen_v1.json").read_text())
    h=json.loads((BASE/"helgeland_2026_two_file_physical_headers_frozen_v1.json").read_text())
    p=json.loads((BASE/"helgeland_2026_year_date_discordance_frozen_v1.json").read_text())
    root=tmp_path/"upstream"
    vals=[
        ("2019","2020-01-03"),("2019","2020-02-10"),
        ("2020" if janmar_same else "2019","2020-03-15"),
        ("2020","2020-05-20"),("2020","2020-12-01")
    ]
    for source,dryad in TARGETS.items():
        loc=root/source
        loc.parent.mkdir(parents=True,exist_ok=True)
        if source.endswith("presence_data_1994_2022.txt"):
            names=["Year","date","scriptsex","Island","Location","stage","Least_age","Least_hatchyear","ID"]
            content=";".join(names)+"\n"
            for i,(y,d) in enumerate(vals):
                content+=f"{y};{d};X;1;FAKE;capt;1;2019;FAKE{i}\n"
        else:
            content="Location;Island;Year;N_corr;.lower;.upper;.width;N_obs\nFAKE;1;2020;1;0;2;0.9;1\n"
        data=content.encode("utf-8")
        loc.write_bytes(data)
        entry=next(z for z in f["files"] if z["name"]==dryad)
        entry["size_bytes"]=len(data)
        entry["source_declared_sha256"]=hashlib.sha256(data).hexdigest()
        if source.endswith("presence_data_1994_2022.txt"):
            names,head_sha=read_first_physical_header(loc)
            entry=next(x for x in h["headers"] if x["github_path"]==source)
            entry["column_names"]=names
            entry["first_line_sha256"]=head_sha
    prior=c["prior_exposed_qc"]
    prior.update(rows=5,discrepancies=2 if janmar_same else 3,
                 delta_minus_one=2 if janmar_same else 3)
    p["total_rows"]=5
    p["all_year_delta_bin_counts"]["-1"]=prior["delta_minus_one"]
    return root,c,f,h,p


def test_april_cutoff_candidate_with_janmar_counterexample(tmp_path):
    result=inspect(*build(tmp_path))
    assert result["total_rows"]==5
    assert result["jan_mar_minus_one"]==2
    assert result["jan_mar_same_year"]==1
    assert result["apr_dec_same_year"]==2
    assert result["overall_candidate_mapping_disagreements"]==1
    assert result["candidate_mapping_exact_on_all_rows"] is False
    assert result["observed_year_rule_confirmed_by_authors"] is False
    assert result["ecological_endpoint_authorized"] is False
    assert "FAKE" not in json.dumps(result)


def test_perfect_april_cutoff_fit_still_not_author_confirmation(tmp_path):
    result=inspect(*build(tmp_path,janmar_same=False))
    assert result["jan_mar_same_year"]==0
    assert result["overall_candidate_mapping_disagreements"]==0
    assert result["candidate_mapping_exact_on_all_rows"] is True
    assert result["observed_year_rule_confirmed_by_authors"] is False
    assert result["date_or_Year_values_recoded"] is False


def test_source_tampering_stops_before_time_rows(tmp_path):
    root,c,f,h,p=build(tmp_path)
    target=root/"Data/presence_data_1994_2022.txt"
    content=target.read_bytes()
    target.write_bytes(content.replace(b"FAKE0",b"FAKE9"))
    assert len(content)==target.stat().st_size
    with pytest.raises(ValueError,match="SHA-256"):
        inspect(root,c,f,h,p)


def test_no_silent_claim_promotion(tmp_path):
    root,c,f,h,p=build(tmp_path)
    c["claims"]["april_cutoff_semantics_author_confirmed"]=True
    with pytest.raises(ValueError,match="elevated claim"):
        inspect(root,c,f,h,p)


def test_prior_exposed_counts_must_still_agree(tmp_path):
    root,c,f,h,p=build(tmp_path)
    p["all_year_delta_bin_counts"]["-1"]=999
    with pytest.raises(ValueError,match="established exploratory QC"):
        inspect(root,c,f,h,p)


def test_reader_never_inspects_or_exports_individual_island_or_stage_fields():
    s=(ROOT/"scripts/audit_helgeland_2026_april_boundary_postexposure_v1.py").read_text()
    for prohibited in ('record["ID"]','record["Island"]','record["stage"]',
                       'record["Location"]','record["scriptsex"]','read_csv(',
                       'import pandas','socket.','urlopen('):
        assert prohibited not in s
    contract=json.loads((BASE/"helgeland_2026_april_boundary_postexposure_contract_v1.json").read_text())
    assert contract["claims"]["exposure_blind"] is False
    assert contract["claims"]["ecological_endpoint_authorized"] is False


def test_observed_universal_month_mapping_frozen_without_author_semantics():
    p=BASE/"helgeland_2026_april_year_mapping_frozen_v1.json"
    receipt=json.loads(p.read_text(encoding="utf-8"))
    assert receipt["schema"]=="eog.helgeland.2026.april_year_mapping.frozen_postexposure_observed_v1"
    assert receipt["authority"]["workflow_run_id"]==37804577337
    assert receipt["authority"]["artifact_id"]==11562470956
    assert receipt["authority"]["artifact_zip_sha256"]==(
        "3026186d8bd0d1c866e8ad7f681cf47a72e6772ac82b9e42ed45b0928f2ad11c"
    )
    observed=receipt["observed"]
    assert observed["total_rows"]==73593
    assert sum(observed["monthly_total_rows"].values())==73593
    assert sum(observed["monthly_total_rows"][f"{i:02}"] for i in range(1,4))==3517
    assert observed["jan_mar_minus_one"]==3517
    assert observed["jan_mar_same_year"]==0
    assert observed["apr_dec_same_year"]==70076
    assert observed["apr_dec_any_mismatch"]==0
    assert observed["overall_candidate_mapping_disagreements"]==0
    assert observed["candidate_mapping_exact_on_all_rows"] is True
    assert receipt["interpretation"]["year_field_definition_author_confirmed"] is False
    assert receipt["interpretation"]["post_exposure_exploratory"] is True
    assert receipt["interpretation"]["year_or_date_rewritten"] is False
    assert receipt["biology"]["ecological_endpoint_authorized"] is False
