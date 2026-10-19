"""Synthetic methodological fixtures, never individual sparrow observations."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
sys.path.insert(0,str(ROOT/"scripts"))
from audit_helgeland_saatoglu2021_provenance_preflight_v1 import (
    EIGHT, OFFICIAL, TENS, audit, map_codes, parse_author_code,
    validate_frozen_manifest,
)


def protocol():
    return json.loads((
        BASE/"helgeland_saatoglu2021_provenance_preflight_v1.json"
    ).read_text(encoding="utf-8"))


def test_official_two_repositories_and_five_original_source_declared_hashes():
    p=protocol()
    validate_frozen_manifest(p)
    assert p["official_dryad"]["first_publication"]=="2021-07-15"
    assert p["official_dryad"]["dataset_id"]==72603
    assert p["official_dryad"]["version_id"]==130231
    assert set(x["name"] for x in p["official_dryad"]["files"])==set(OFFICIAL)
    assert sum(x["size_bytes"] for x in p["official_dryad"]["files"])==81837
    assert p["official_zenodo"]["record_id"]==5095667
    assert p["official_zenodo"]["bytes"]==10758
    assert p["verification_gate"]["dryad_2021_data_rows_accessed"] is False
    assert p["strong_stop_rules"]["do_not_add_fourth_EOG_WF_endpoint"] is True


def test_provenance_roster_in_eight_existing_source_internal_labels():
    p=protocol()
    bridge=map_codes(p)
    assert [x["raw_code"] for x in bridge]==list(EIGHT)
    assert len(bridge)==8
    assert [x["source_2026_name_label"] for x in bridge]==[
        "nesøy","myken","træna","selvær","gjerøy","hestmannøy",
        "indre kvarøy","aldra"
    ]
    assert "33" not in EIGHT
    assert "77" in TENS and "88" in TENS
    assert all(x["2021_natal_and_adult_ID_domain_verified"] is False for x in bridge)


def test_metadata_only_audit_never_creates_genetic_or_movement_claim():
    a=audit(None,protocol())
    assert a["status"]=="OFFICIAL_SOURCE_METADATA_ONLY__GENETIC_DATA_HOLD"
    assert a["source"]["source_bytes_author_md5_verified"] is False
    assert a["source"]["five_original_source_file_bytes_verified"] is False
    assert a["source"]["actual_2021_genetic_assignment_rows_read"] is False
    assert a["source"]["2021_record_2026_bird_ID_join_verified"] is False
    assert a["genetic_origin_is_true_source_without_calibration"] is False
    assert a["EOG_WF_denominator_modified"] is False
    assert "natal.island" not in json.dumps(a)


def test_invalid_author_code_bytes_fail_before_semantic_parsing():
    with pytest.raises(ValueError,match="byte-size mismatch"):
        audit(b"fake author code",protocol())
    with pytest.raises(ValueError,match="MD5 mismatch"):
        audit(b"0"*10758,protocol())


def test_synthetic_source_code_indicators_and_fail_closed_conditions():
    fake='''Dispersal.data = read.table("Dispersaldata.txt", header=T)
    natal.island adult.island hatch.year dispersal.status
    sample.size Population.size pw.Fst Ho
    Genpattern.data Habitat.data
    2004–2012
    # (Island codes: 20,22,23,24,26,27,28,38)
    natal codes: "20" "22" "23" "24" "26" "27" "28" "38" "77" "88"
    '''
    x=parse_author_code(fake)
    assert x["eight_named_code_comparable_subset_text_present"] is True
    assert x["author_2004_to_2012_sampling_restriction_text_present"] is True
    assert x["sampling_fraction_misassignment_models_present"] is True
    with pytest.raises(ValueError,match="frozen variables"):
        parse_author_code(fake.replace("adult.island","removed"))
    with pytest.raises(ValueError,match="eight SNP codes"):
        parse_author_code(fake.replace("20,22,23,24,26,27,28,38","badlist"))


def test_readme_or_genetic_source_can_never_be_silently_considered_verified():
    p=protocol()
    p["verification_gate"]["dryad_2021_data_rows_accessed"]=True
    with pytest.raises(ValueError,match="evidence gate"):
        audit(None,p)
    p=protocol()
    p["official_zenodo"]["declared_md5"]="f"*32
    with pytest.raises(ValueError,match="Zenodo public author"):
        audit(None,p)
    p=protocol()
    p["EOG_2026_previous_11island_context"]["code_33_is_valid_named_Luroy_Onoy"]=False
    with pytest.raises(ValueError,match="code mapping"):
        audit(None,p)
    p=protocol()
    p["strong_stop_rules"]["do_not_add_fourth_EOG_WF_endpoint"]=False
    with pytest.raises(ValueError,match="evidence gate"):
        audit(None,p)


def test_2021_individual_data_and_2026_individual_id_join_still_not_verified():
    p=protocol()
    assert p["documented_author_script_design"]["latent_true_origin_must_not_be_assumed_from_genetic_assignment_probabilities"] is True
    assert p["strong_stop_rules"]["sampled_fraction_is_fidelity_process_not_exogenous_ecological_dispersal_driver"] is True
    assert p["strong_stop_rules"]["do_not_confuse_saatoglu_sample_and_2021_ranke_recruit_pool"] is True
    assert p["strong_stop_rules"]["first_followup_proxies_not_equated_with_adult_island"] is True
    assert p["EOG_2026_previous_11island_context"]["source_file_published_2026_cannot_be_as_of_2014"] is True


def test_exact_independently_attested_public_Zenodo_author_code_receipt_no_bird_rows():
    p=protocol()
    a=json.loads((
        BASE/"helgeland_saatoglu2021_provenance_result_frozen_v1.json"
    ).read_text(encoding="utf-8"))
    assert a["schema"]=="eog.helgeland.saatoglu2021_genetic_cmr_code_audit.frozen_evidence_v1"
    assert a["authority"]["github_actions_run_id"]==39217762475
    assert a["authority"]["github_actions_artifact_id"]==12170526675
    assert a["authority"]["artifact_zip_sha256"]==(
        "124e69b6d7caeae9e48007b08b620d829f0283b399b255bcddf4eb324d9e4648"
    )
    assert a["authority"]["source_script_original_MD5_verified"] is True
    assert a["authority"]["Dryad_five_data_file_bodies_read"] is False
    x=a["receipt"]
    assert x["status"]=="AUTHOR_ZENODO_METHOD_SCRIPT_BYTE_VERIFIED__BIOLOGICAL_DATA_HOLD"
    assert x["source"]["source_bytes_author_md5_verified"] is True
    assert x["source"]["five_original_source_file_bytes_verified"] is False
    assert x["source"]["2021_record_2026_bird_ID_join_verified"] is False
    assert len(x["eog_2026_to_2021_eight_code_name_text_bridge"])==8
    assert [v["raw_code"] for v in x["eog_2026_to_2021_eight_code_name_text_bridge"]]==list(EIGHT)
    assert all(v["2021_natal_and_adult_ID_domain_verified"] is False
               for v in x["eog_2026_to_2021_eight_code_name_text_bridge"])
    assert x["author_methods_source_code_signals"]["sampling_fraction_misassignment_models_present"] is True
    assert x["breeding_recruitment_or_colonization_inferred"] is False
    assert x["EOG_WF_denominator_modified"] is False
