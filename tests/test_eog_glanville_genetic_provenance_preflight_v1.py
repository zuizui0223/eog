"""Source-only Glanville genetic / occupancy bridge: no biological response access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "validation" / "eog_virtual_world_ecology_synthesis_v1" / "glanville_genetic_origin_preflight_v1.json"
REPORT = ROOT / "docs" / "eog_glanville_genetic_provenance_preflight_v1.md"


def read_catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def git_blob_sha(raw: bytes):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def undirected_two_patch_sibship_observation(maternal_patch_a, maternal_patch_b):
    # A cross-patch full-sib link constrains an unordered pair of sampled patches.
    return tuple(sorted((maternal_patch_a, maternal_patch_b)))


def proposed_directional_first_origin(source, recipient):
    # NOT observed by contemporaneous full-sibs; demonstrates the loss of orientation.
    return (source, recipient)


def test_kinship_link_is_non_identifying_for_direction():
    assert undirected_two_patch_sibship_observation("patch_A", "patch_B") == \
           undirected_two_patch_sibship_observation("patch_B", "patch_A")
    assert proposed_directional_first_origin("patch_A", "patch_B") != \
           proposed_directional_first_origin("patch_B", "patch_A")
    assert len(set([
        proposed_directional_first_origin("patch_A", "patch_B"),
        proposed_directional_first_origin("patch_B", "patch_A"),
    ])) == 2


def test_prior_glanville_eog_input_identities_and_window_remain_frozen():
    info=read_catalog()
    assert info["schema"]=="eog.source_provenance_external_bridge.metadata_preflight.v1"
    assert info["status"]=="METADATA_ONLY_HOLD_NOT_SOURCE_ORIGIN_QUALIFIED"

    survey=info["source_inventory"]["occupancy"]
    f=ROOT / survey["frozen_source_file"]
    assert git_blob_sha(f.read_bytes())==survey["frozen_source_git_blob_sha"]
    a=json.loads(f.read_text(encoding="utf-8"))
    assert a["status"]=="authoritative_independent_outcome_frozen"
    assert a["source"]["dryad_doi"]=="10.5061/dryad.ksn02v707"
    assert a["source"]["archive_sha256"]==survey["verified_archive_sha256_from_prior_EOG_gate0"]
    assert a["authoritative_run"]["workflow_run_id"]==32017872743

    protocol=ROOT / survey["temporal_protocol_file"]
    assert git_blob_sha(protocol.read_bytes())==survey["temporal_protocol_git_blob_sha"]
    q=json.loads(protocol.read_text(encoding="utf-8"))
    assert q["temporal_split_rule"]["heldout_rule"] == \
           "last 6 consecutive annual transitions are heldout; every earlier consecutive transition is calibration"
    assert survey["calibration_transition_first"]=="1999→2000"
    assert survey["calibration_transition_last"]=="2011→2012"
    assert survey["holdout_transition_first"]=="2012→2013"
    assert survey["holdout_transition_last"]=="2017→2018"


def test_genetic_sample_years_are_inside_old_calibration_not_fresh_holdout():
    info=read_catalog()
    x=info["source_inventory"]["sibship"]
    z=info["longitudinal_overlap"]
    assert x["public_dryad_doi"]=="10.5061/dryad.d461s"
    assert x["zenodo_record"]==5010194
    assert x["paper_doi"]=="10.1111/eva.12552"
    assert x["archived_period"]==[2007,2012]
    assert x["larval_group_sample_count_published"]==3732
    assert x["snp_marker_count_published"]==272
    assert x["zenodo_advertised_tar_gz_md5"]=="11e63736667e492a13f822960d48a329"
    assert z["genetic_sample_years"]==[2007,2008,2009,2010,2011,2012]
    assert all(z["eog_calibration_years"][0] <= y <= z["eog_calibration_years"][1]
               for y in z["genetic_sample_years"])
    assert all(y < z["eog_heldout_target_years"][0] for y in z["genetic_sample_years"])
    assert z["genetic_supports_any_of_frozen_eog_heldout_target_years"] is False
    assert z["new-independent-eog-holdout-confirmation"] is False


def test_claim_gates_prevent_turning_undirected_full_sibs_into_ideal_first_origin():
    x=read_catalog()
    q=x["qualification_gates"]
    for key in (
        "GENETIC_ARCHIVE_BYTE_DIGEST_VERIFIED_FROM_FILE",
        "GENETIC_FILE_HEADER_VERIFIED_RESPONSE_BLIND",
        "CROSS_ARCHIVE_PATCH_UID_CROSSWALK_INDEPENDENTLY_VERIFIED",
        "MATERNAL_DISPERSAL_DIRECTION_WITHIN_SEASON_IDENTIFIED",
        "FIRST_ARRIVAL_SOURCE_PER_RECIPIENT_PATCH_IDENTIFIED",
        "FUTURE_HOLDOUT_GENETIC_ORIGIN_OBSERVATIONS_AVAILABLE",
        "INDEPENDENT_ECOLOGICAL_CONFIRMATORY_PROGRAMME",
        "NEW_GENETIC_RESPONSE_REUSE_AUTHORIZED",
    ):
        assert q[key] is False, key
    assert q["PUBLISHED_GENETIC_SIBSHIP_SOURCE_LOCATED"] is True
    assert q["PUBLISHED_OCCUPANCY_SOURCE_IDENTITY_PINNED"] is True

    source=x["source_inventory"]["sibship"]
    assert source["direction_observed_from_same_year_crosspatch_full_sibs"] is False
    assert source["directly_measures_first_arriving_source_of_newly_colonized_patch"] is False
    assert source["exact_patch_id_namespace_crosswalk_to_EOG_registry_verified"] is False
    assert source["physical_file_bytes_or_headers_checked_in_this_preflight"] is False
    assert x["formal_observation_equivalence"]["directional_first_origin_identified"] is False
    assert x["formal_observation_equivalence"]["patch_source_history_identified"] is False
    assert x["decision"]["target_status"]=="HOLD_SOURCE_DIRECTION_NOT_IDENTIFIED_AND_NOT_FRESH"
    for k in ("zero_genotype_rows_opened_during_this_preflight",
              "zero_occupancy_rows_opened_during_this_preflight",
              "no_eogwf_denominator_change",
              "do_not_reuse_same_EOG_Glanville_endpoint_as_fresh_validation"):
        assert x["decision"][k] is True
    assert x["decision"]["zero_models_fitted"] is True

    doc=REPORT.read_text(encoding="utf-8")
    assert "2007–2012" in doc
    assert "1999–2012" in doc
    assert "2013–2018" in doc
    assert "A → B" in doc and "B → A" in doc
    assert "NOT a new independent external validation" in doc
