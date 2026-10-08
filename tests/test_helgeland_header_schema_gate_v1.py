"""Guard Helgeland's pre-response physical header entrypoint without reading source data."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
SCRIPT=ROOT/"scripts/qualify_helgeland_header_attestations_v1.py"


def load():
    spec=importlib.util.spec_from_file_location("helgeland_headers",SCRIPT)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs():
    return (
        json.loads((BASE/"helgeland_header_schema_contract_v1.json").read_text()),
        json.loads((BASE/"helgeland_source_metadata_frozen_v1.json").read_text()),
    )


def fake_attestation(catalog,metadata):
    records=[]
    for key,role in catalog["expected_header_roles"].items():
        src,name=key.split("/",1)
        source=metadata["inventories"][src]
        pinned=next(v for v in source["files"] if v["name"]==name)
        records.append({
            "file_key":key,
            "doi":source["doi"],
            "dryad_version_id":source["dryad_version_id"],
            "dryad_file_id":pinned["file_metadata_id"],
            "header_tokens":role["required_exact"]+["placeholder_header_name"],
            "delimiter":"TAB",
            "first_line_only":True,
            "contains_response_values":False,
            "independent_extraction_reference":"SYNTHETIC-TEST-HEADER-ONLY",
        })
    return {"schema":"eog.helgeland.header_only_attestation.v1","records":records}


def test_unopened_original_files_remain_hold():
    m=load()
    a,b=inputs()
    out=m.qualification(a,b,None)
    assert out["status"]=="HOLD_PHYSICAL_HEADERS_NOT_ATTESTED"
    assert out["counts"]["expected_physical_headers"]==4
    assert out["counts"]["attested_header_files"]==0
    assert len(out["counts"]["unresolved_header_files"])==4
    assert out["dryad_file_bytes_opened_by_this_script"] is False
    assert out["individual_values_or_genotypes_opened_by_this_script"] is False
    assert out["id_and_island_value_join_verified"] is False
    assert out["ecological_endpoint_authorized"] is False
    assert out["first_island_founder_identified"] is False


def test_header_names_alone_never_qualify_join_or_biological_prediction():
    m=load()
    contract,metadata=inputs()
    fake=fake_attestation(contract,metadata)
    verdict=m.qualification(contract,metadata,fake)
    assert verdict["status"]=="HEADER_NAMES_ATTESTED_KEYS_STILL_UNJOINED"
    assert verdict["counts"]["attested_header_files"]==4
    assert verdict["counts"]["unresolved_header_files"]==[]
    assert verdict["id_and_island_value_join_verified"] is False
    assert verdict["header_matches_not_physical_byte_checksums"] is True
    assert verdict["ecological_endpoint_authorized"] is False
    assert verdict["source_loss_or_recolonization_identified"] is False
    assert "NOT joined" in verdict["interpretation"]

    # Removing an attested physical header never silently passes a 3-file join.
    missing=copy.deepcopy(fake)
    missing["records"].pop()
    out=m.qualification(contract,metadata,missing)
    assert out["status"]=="HOLD_INCOMPLETE_PHYSICAL_HEADER_SET"
    assert out["counts"]["attested_header_files"]==3


@pytest.mark.parametrize("mutation",[
    "wrong_version","wrong_file","unknown_delimiter","data_row","extra_record_field",
    "unknown_key","duplicate_field","aliased_ID","newline","duplicate_record",
])
def test_fails_closed_on_bad_header_attestations(mutation):
    m=load()
    contract,metadata=inputs()
    att=fake_attestation(contract,metadata)
    row=att["records"][0]
    if mutation=="wrong_version":
        row["dryad_version_id"]=0
    elif mutation=="wrong_file":
        row["dryad_file_id"]=999
    elif mutation=="unknown_delimiter":
        row["delimiter"]="UNKNOWN"
    elif mutation=="data_row":
        row["contains_response_values"]=True
    elif mutation=="extra_record_field":
        row["fitness_data"]=[1,2,3]
    elif mutation=="unknown_key":
        row["file_key"]="fitness_2025/not-registered.txt"
    elif mutation=="duplicate_field":
        row["header_tokens"].append("ID")
    elif mutation=="aliased_ID":
        row["header_tokens"]=["individual" if x=="ID" else x for x in row["header_tokens"]]
    elif mutation=="newline":
        row["header_tokens"][0]="ID\n123"
    elif mutation=="duplicate_record":
        att["records"].append(copy.deepcopy(row))
    with pytest.raises(ValueError):
        m.qualification(contract,metadata,att)


def test_contract_keeps_different_documented_2024_and_2025_id_roles():
    a,b=inputs()
    roles=a["expected_header_roles"]
    assert "ID" in roles["fitness_2025/LRS.txt"]["required_exact"]
    assert "ID" in roles["pedigree_2024/GGAM_data_GeneticArchitecture.txt"]["required_exact"]
    assert "individual" in roles["pedigree_2024/SNPpedigree_GeneticArchitecture.txt"]["required_exact"]
    assert "ID" not in roles["pedigree_2024/SNPpedigree_GeneticArchitecture.txt"]["required_exact"]
    assert a["header_evidence_requirements"]["no_auto_join_of_ID_and_individual"] is True
    assert a["cross_file_join_contract"]["do_not_auto_correct_spelling_27"] is True
    assert a["cross_file_join_contract"]["source_documented_spelling_27"]=="Hestmannøly"
    assert b["inventories"]["fitness_2025"]["dryad_version_number"]==2
    assert b["inventories"]["pedigree_2024"]["dryad_version_number"]==3


def test_auditor_cannot_download_or_parse_original_bird_record_files():
    code=SCRIPT.read_text(encoding="utf-8")
    for banned in (
        "import requests","import urllib","import pandas","import numpy",
        "urlopen(","read_csv(","pd.read_","/download","import sklearn",
        "import subprocess","socket."
    ):
        assert banned not in code
    assert "header-attestation-json" in code
    assert "source_loss_or_recolonization_identified" in code
