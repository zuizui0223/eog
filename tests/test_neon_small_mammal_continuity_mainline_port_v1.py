"""Read-only provenance and scientific-boundary regression for archived Oikos draft.

All 32 original paper files must retain exact source Git blob identities.
The independent empirical NEON programme is already response-consumed and
must never be rescored to repair its rejected primary hypothesis.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/"manuscript/neon_small_mammal_continuity"
RECEIPT=PAPER/"MAINLINE_PORT_REPRODUCIBILITY_RECEIPT_V1.json"
RESPONSE=ROOT/"validation/neon_metacommunity_connectivity_v1/response_lock_v1.json"
CLOSURE=ROOT/"validation/neon_metacommunity_connectivity_v1/programme_closure_v1.json"
MODULE=ROOT/"src/eog/v2/metacommunity_connectivity.py"
SITES=PAPER/"site_metrics_v1.csv"


def original_blob_sha1(path:Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()


def receipt():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_all_32_imported_blobs_are_original_unmodified_paper_sources():
    z=receipt()
    assert z["schema"]=="eog.neon_small_mammal_continuity.source_preserving_mainline_port.v1"
    assert z["status"]=="VERIFIED_CONTENT_EQUIVALENCE_OF_REBASED_PAPER_ASSETS__NOT_SUBMITTED"
    original=z["original_32_imported_files"]
    assert len(original)==32 and len({x["path"] for x in original})==32
    assert all(x["path"].startswith(("manuscript/neon_small_mammal_continuity/",
                                     "tests/test_neon_small_mammal_continuity_"))
               or x["path"]==".github/workflows/neon-small-mammal-continuity-paper-assets.yml"
               for x in original)
    for entry in original:
        path=ROOT/entry["path"]
        assert path.is_file(), entry["path"]
        assert original_blob_sha1(path)==entry["blob_sha1"],entry["path"]
    assert z["source"]["paper_source_commit"]=="20814bf254359dac2ff8152fc85e8b773d065e8d"
    assert z["source"]["initial_rebased_commit"]=="862963faf35eac5e186bfb46491e744b7dc669c1"


def test_archived_original_scientific_source_and_16_site_response_are_unchanged():
    z=receipt()
    source=z["source"]
    assert original_blob_sha1(MODULE)==source["original_module_blob_sha1"]
    assert original_blob_sha1(RESPONSE)==source["response_lock_blob_sha1"]
    r=json.loads(RESPONSE.read_text())
    c=json.loads(CLOSURE.read_text())
    assert r["result_fingerprint"]==source["response_fingerprint"]
    assert r["denominator"]=={"fixed_sites":16,"scored_sites":16,"response_consumed_stops":0}
    assert r["primary"]["primary_supported"] is False
    assert r["primary"]["positive_null_adjusted_site_count"]==0
    assert r["primary"]["one_sided_sign_test_p"]==1
    assert r["ecological_pattern"]["sites_with_positive_emergent_gain"]==0
    assert r["ecological_pattern"]["strict_emergent_world_fraction_positive_sites"]==0
    assert c["scientific_state"]=="closed_after_once_only_fresh_response"
    assert c["further_response_access_allowed"] is False
    assert c["threshold_retuning_allowed"] is False
    assert source["fixed_sites"]==16
    assert source["scored_sites"]==16


def test_original_16_site_metrics_preserve_negative_primary_and_redundancy():
    with SITES.open(encoding="utf-8",newline="") as f:
        rows=list(csv.DictReader(f))
    z=receipt()
    assert len(rows)==16
    assert len({r["site_code"] for r in rows})==16
    assert sorted(r["site_code"] for r in rows)==sorted(r["site_code"] for r in rows)
    assert all(float(r["max_species_survival_fraction"])==1 for r in rows)
    assert all(float(r["emergent_connectivity_gain"])<=0 for r in rows)
    assert all(float(r["null_adjusted_gain"])<=0 for r in rows)
    assert all(float(r["strict_emergent_world_fraction"])==0 for r in rows)
    assert sum(int(r["best_species_count"])>=2 for r in rows)==13
    species=Counter()
    for row in rows:
        species.update(row["best_species_names"].split(";"))
    assert len(species)==32
    assert max(species.values())==3
    assert z["source"]["distinct_individually_continuous_species"]==len(species)
    ornl=next(r for r in rows if r["site_code"]=="ORNL")
    assert float(ornl["community_survival_fraction"])==0.25
    assert float(ornl["max_species_survival_fraction"])==1.0
    assert float(ornl["emergent_connectivity_gain"])==-0.75


def test_rendered_content_audit_explicitly_distinguishes_timestamp_variance():
    asset=receipt()["new_asset"]
    previous=receipt()["old_asset"]
    assert asset["workflow_run_id"]==40261735987
    assert asset["artifact_id"]==12625000500
    assert asset["pdf_pages"]==9
    assert asset["pdf_author_field_empty"] is True
    assert asset["pdf_text_extracted_layout_sha256"]==(
        "bede658b1eb597537e0fec37ada7f774e8eefe867ee560a0b8d140717ba332f2"
    )
    assert asset["pdf_extracted_text_identical_to_original"] is True
    assert asset["review_member_count"]==23
    assert asset["review_member_content_identical_to_original"] is True
    assert asset["all_four_figures_byte_identical_to_original"] is True
    assert len(asset["figures_png_sha256"])==4
    assert asset["pdf_creation_metadata_timestamp_variant"] is True
    assert asset["review_zip_container_timestamp_variant"] is True
    assert asset["pdf_sha256"]!=previous["pdf_sha256"]
    assert asset["review_zip_inner_sha256"]!=previous["anonymous_inner_zip_sha256"]
    assert asset["review_member_content_manifest_sha256"]==(
        "2585d15b01d336b8a20f852da26842c39325d8ed159b8a9d0d43e51c96408db9"
    )


def test_author_submission_and_empirical_fourth_endpoint_remain_blocked():
    limits=receipt()["boundaries"]
    assert limits["no_biological_data_reopened"] is True
    assert limits["no_scientific_refit"] is True
    assert limits["no_endpoint_rescored"] is True
    assert limits["original_paper_files_preserved_byte_for_byte"] is True
    assert limits["this_receipt_does_not_claim_bitwise_reproduction_of_timestamped_PDF_or_ZIP"] is True
    assert limits["human_author_list_and_title_page_not_confirmed"] is True
    assert limits["funding_ethics_conflicts_and_disclosure_not_confirmed"] is True
    assert limits["paper_not_submitted"] is True
    assert limits["permanent_public_data_code_archive_DOI_not_minted"] is True
    assert limits["EOG_WF_3_31_3_unchanged"] is True
    text=(PAPER/"SUBMISSION_BOUNDARY_V1.json").read_text()
    assert '"scientific_state": "closed"' in text
    assert '"journal_route"' in text
