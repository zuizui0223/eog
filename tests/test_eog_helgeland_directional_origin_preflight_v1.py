"""Public-metadata-only qualification of directional Helgeland natal dispersal."""

from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=(ROOT/"validation/eog_virtual_world_ecology_synthesis_v1"
         /"helgeland_directional_origin_preflight_v1.json")
DOC=ROOT/"docs/eog_helgeland_directional_origin_preflight_v1.md"


def data():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def natal_to_adult_island_observation(natal, adult):
    # A known natal and adult island does orient individual natal dispersal.
    return (natal,adult)


def island_first_colonizer_target(natal, adult, previous_recipient_occupancy_unknown=True):
    # A bird's individual movement alone cannot establish founding of an island.
    if previous_recipient_occupancy_unknown:
        return None
    # This test helper must not invent a founder even with occupancy metadata:
    # additional evidence of first establishment would still be necessary.
    return None


def test_source_has_documented_individual_direction_but_not_island_founder():
    d=data()
    assert d["schema"]=="eog.external_provenance.helgeland_metadata_gate.v1"
    assert d["status"]=="DIRECTIONAL_NATAL_DISPERSAL_FIELDS_DOCUMENTED__ECOLOGICAL_ENDPOINT_HOLD"
    assert d["external_system"]["taxon"]=="Passer domesticus"
    assert d["external_system"]["ecologically_independent_of_prior_EOG_Glanville"] is True
    a=d["sources"]["annual_recruitment"]
    assert a["dryad_doi"]=="10.5061/dryad.qfttdz0sx"
    assert a["paper_doi"]=="10.1111/1365-2656.70049"
    assert a["birth_to_adult_direction_documented_by_metadata"] is True
    assert {"ID","natal.island","adult.island","year","LRS"}.issubset(
        set(a["source_advertised_LRS_keys"])
    )
    assert {"fiflok","laflok","obs.year","recruits","survival"}.issubset(
        set(a["source_advertised_ARS_keys"])
    )
    assert len(a["advertised_files"])==5
    assert natal_to_adult_island_observation("island_A","island_B") != \
           natal_to_adult_island_observation("island_B","island_A")
    assert island_first_colonizer_target("A","B") is None
    assert d["observation_contract"]["exact_first_founder_of_entire_recipient_island_identified"] is False
    assert d["observation_contract"]["no_inference_that_a_breeding_island_was_unoccupied_before_immigrant_arrived"] is True


def test_pedigree_metadata_is_separate_and_no_file_identity_or_crosswalk_is_assumed():
    d=data()
    x=d["sources"]["pedigree"]
    assert x["dryad_doi"]=="10.5061/dryad.80gb5mkxh"
    assert x["paper_doi"]=="10.1111/mec.17295"
    assert x["cross_archival_individual_and_island_key_join_qualified"] is False
    assert x["independently_unique_natal_source_assignment_for_every_individual"] is False
    assert x["raw_genotype_or_pedigree_rows_opened_in_this_audit"] is False
    assert x["physical_header_verified"] is False
    assert {"20","22","23","24","26","27","28","34","35","38","331","332"} == \
           set(x["archived_island_code_to_name_dictionary"])
    assert "SNPpedigree_GeneticArchitecture.txt" in x["source_advertised_files"]
    assert x["archived_island_code_to_name_dictionary"]["20"]=="Nesøy"
    assert x["archived_island_code_to_name_dictionary"]["27"]=="Hestmannøly"
    assert "not silently substituted" in x["island_name_spelling_boundary"]
    assert x["archived_island_code_to_name_dictionary"]["38"]=="Aldra"


def test_response_gate_prevents_retrospective_public_results_becoming_new_confirmation():
    d=data()
    gates=d["gates"]
    for x in (
        "SOURCE_DOIS_AND_README_FIELD_ROLES_DOCUMENTED",
        "DIRECTIONAL_INDIVIDUAL_NATAL_AND_ADULT_FIELDS_ADVERTISED",
        "ECOLOGICAL_SYSTEM_INDEPENDENT_OF_CLOSED_GLANVILLE",
    ):
        assert gates[x] is True,x
    for x in (
        "DATA_ARCHIVE_SHA256_VERIFIED_IN_THIS_AUDIT",
        "EXACT_PHYSICAL_COLUMN_NAMES_VERIFIED",
        "BIRD_AND_ISLAND_UID_CONCORDANCE_VERIFIED",
        "INDEPENDENT_FUTURE_NATAL_ORIGIN_LABEL_VERIFIED",
        "DETECTION_AND_YEARLY_SURVEY_OPPORTUNITY_CONTRACT_VERIFIED",
        "FIRST_SOURCE_OF_RECIPIENT_ISLAND_FOUNDING_VERIFIED",
        "SOURCE_LOSS_RECOLONIZATION_EVENTS_REGISTERED",
        "NEW_EOG_PREDICTIVE_ENDPOINT_AUTHORIZED",
        "BIOLOGICAL_RESPONSE_ROWS_OPENED_IN_THIS_AUDIT",
    ):
        assert gates[x] is False,x
    assert d["sources"]["genetic_assignment"]["dryad_doi"]=="10.5061/dryad.gqnk98sh8"
    assert d["sources"]["genetic_assignment"]["published_2019_genotyped_individuals_after_QC"]==3116
    assert d["terminal_decision"]["status"]=="HOLD_DIRECTIONAL_INDIVIDUAL_PROXY_ONLY"
    assert d["terminal_decision"]["EOG_WF_FROZEN_3_31_3_DENOMINATOR_UNCHANGED"] is True
    assert d["terminal_decision"]["no_biological_model_fit"] is True
    assert d["terminal_decision"]["no_genetic_or_fitness_row_read"] is True
    assert "The first colonizing island source was identified." in d["terminal_decision"]["excluded_claims"]


def test_temporal_leakage_is_explicit_and_published_fitness_claim_is_prior_art():
    d=data()
    x=d["observation_contract"]
    assert x["future_information_must_not_be_used_to_build_time_t_predictor"] is True
    assert x["natal_origin_exposure_before_breeding_outcome_verified"] is False
    assert x["birth_island_direct_or_genetically_inferred_must_be_separated"] is True
    assert x["genetic_assignment_error_and_missingness_per_record_verified"] is False
    assert d["sources"]["annual_recruitment"]["source_data_opened_in_this_audit"] is False
    assert "Published analyses already compare fitness outcomes" in \
           d["sources"]["annual_recruitment"]["ecological_target_prior_art"]
    t=DOC.read_text(encoding="utf-8")
    assert "natal.island" in t and "adult.island" in t
    assert "初回定着" in t
    assert "heldout" in t
    assert "未実施" in t
