"""No actual author approval, new NEON response or submission PDF is generated."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from manuscript.neon_small_mammal_continuity import (
    build_oikos_ceiling_interpretation_review_v3 as review,
    build_oikos_initial_submission_policy_v2 as policy,
)


def test_original_32_paper_sources_and_response_fingerprint_are_immutable():
    verification = policy.integrity_guard()
    assert verification["original_imported_blobs_SHA1_verified"] == 32
    assert verification["original_response_lock_fingerprint_verified"] == (
        review.ORIGINAL_RESPONSE_FINGERPRINT
    )
    assert policy.git_blob_sha1(review.SOURCE) == (
        "ada5a84d3b862e122b1d6895c47ed3511de05854"
    )
    assert policy.git_blob_sha1(review.SIGNIFICANCE) == (
        "f1b223d9a159de37d5ab5ebe2da69266fb3da099"
    )


def test_frozen_audit_counts_and_dependency_not_new_negative_replication():
    audit = json.loads(review.REVIEW.read_text(encoding="utf-8"))
    review.validate_review_source(audit)
    assert audit["counts"]["observed_best_species_survival_equals_one"] == 16
    assert audit["counts"]["observed_aggregate_one_sided_p"] == 1
    assert audit["counts"]["sites_with_at_least_two_independently_fully_continuous_species"] == 13
    assert audit["counts"]["unique_continuity_provider_species_across_sites"] == 32
    assert audit["interpretation"]["negative_gain_and_p_one_follow_once_saturation_observed"]
    for change in (
        lambda x: x["counts"].update(observed_best_species_survival_equals_one=15),
        lambda x: x["counts"].update(sites_with_at_least_two_independently_fully_continuous_species=16),
        lambda x: x["interpretation"].update(site_null_p_one_and_aggregate_sign_p_one_not_independent_confirmation=False),
        lambda x: x["authority"].update(full_audit_canonical_sha256="0" * 64),
    ):
        bad = deepcopy(audit)
        change(bad)
        with pytest.raises(ValueError, match="audit|counts|boundaries|identity"):
            review.validate_review_source(bad)


def test_author_review_proposal_is_scientifically_conservative_and_explicitly_unapproved():
    z = review.build_proposal()
    candidate = z["candidate"]
    diff = z["diff"]
    form = z["significance"]
    status = z["receipt"]
    assert status["schema"] == review.OUTPUT_SCHEMA
    assert status["status"] == (
        "CEILING_QUALIFIED_EDITORIAL_CANDIDATE__AUTHOR_APPROVAL_PENDING__NO_PDF"
    )
    assert candidate.startswith("<!-- UNAPPROVED SCIENTIFIC REVISION")
    assert "# Species-level saturation constrains pooled" in candidate
    assert "at least one constituent species" in candidate
    assert "permutation null preserves" in candidate
    assert "not independent negative evidence" in candidate
    assert "synthetic counterexample" in candidate
    assert "Thirteen of 16 sites" in candidate
    assert "32 different species" in candidate
    assert "neither of which was observed" not in candidate
    assert "The preregistered primary hypothesis was rejected completely." not in candidate
    assert "The preregistered turnover hypothesis was rejected:" not in candidate
    assert "universal absence" not in candidate.lower() or "not" in candidate.lower()
    assert "not a claim that more biodiversity generally" in candidate
    assert "UNAPPROVED AUTHOR/COAUTHOR" in form
    assert "32 distinct species" in form
    assert "independent negative findings" in form
    assert "--- ORIGINAL_LOCKED_MANUSCRIPT_V1.md" in diff
    assert "+++ UNAPPROVED_CEILING_INTERPRETATION_DRAFT_V3.md" in diff
    assert status["author_approved_science_interpretation"] is False
    assert status["author_approved_AI_statement"] is False
    assert status["blinded_submission_pdf_created"] is False
    assert status["title_page_or_ScholarOne_data_submitted"] is False
    assert status["new_NEON_biological_response_or_scientific_score"] is False
    assert status["new_EOG_WF_endpoint_or_denominator_change"] is False


def test_methods_figure_captions_references_and_data_section_remain_exact():
    original = review.SOURCE.read_text(encoding="utf-8")
    modified = review.build_proposal()["candidate"]
    for first, next_title in [
        ("## 1. Introduction\n", "### 3.1"),
        ("### 3.2 At least one individual species", "## 4. Discussion\n"),
    ]:
        baseline = original[original.index(first):original.index(next_title)]
        revised = modified[modified.index(first):modified.index(next_title)]
        assert revised == baseline
    marker = "## Data availability\n"
    assert original[original.index(marker):] == modified[modified.index(marker):]
    assert "## AI use statement" not in modified
    assert "## References" in modified
    assert "NEON. 2026" in modified
    assert "## 2. Methods" in modified


def test_refuse_altered_or_duplicate_anchored_sections():
    with pytest.raises(ValueError, match="unique"):
        review.anchored_replace("none", "## Abstract\n", "**Keywords:**", "abc")
    with pytest.raises(ValueError, match="order"):
        review.anchored_replace("end\nstart", "start", "end", "abc")
    bad = review.REVISED_RESULTS_3_1 + (
        "\n\n### 3.2 At least one individual species was fully continuous at every site"
    ) * 2
    with pytest.raises(ValueError, match="unique"):
        review.anchored_replace(
            bad,
            "### 3.1 Observed best-species saturation constrained the primary contrast",
            "### 3.2 At least one individual species was fully continuous at every site",
            "new",
        )


def test_source_only_builder_emits_unapproved_review_packet_no_pdf(tmp_path, monkeypatch):
    old_source = review.SOURCE.read_bytes()
    old_significance = review.SIGNIFICANCE.read_bytes()
    dest = tmp_path / "AUTHOR_REVIEW_UNAPPROVED"
    monkeypatch.setattr(
        sys, "argv",
        ["review-draft", "--output-dir", str(dest)],
    )
    review.main()
    assert sorted(f.suffix for f in dest.iterdir()) == [
        ".json", ".md", ".patch", ".txt"
    ]
    assert not list(dest.glob("*.pdf"))
    assert "UNAPPROVED" in (dest / "OIKOS_CEILING_INTERPRETATION_AUTHOR_REVIEW_UNAPPROVED_V3.md").read_text()
    preflight = json.loads(
        (dest / "OIKOS_CEILING_INTERPRETATION_REVIEW_PREFLIGHT_V3.json").read_text()
    )
    assert preflight["status"].endswith("__NO_PDF")
    assert preflight["source"]["original_32_manuscript_blobs_verified"] == 32
    for name, checksum in preflight["review_only_output_sha256"].items():
        assert hashlib.sha256((dest / name).read_bytes()).hexdigest() == checksum
    assert review.SOURCE.read_bytes() == old_source
    assert review.SIGNIFICANCE.read_bytes() == old_significance
    with pytest.raises(FileExistsError, match="overwrite"):
        review.main()


def test_original_ai_gate_remains_unapproved_and_is_not_substituted():
    template = json.loads(
        (review.LANE / "OIKOS_AI_AUTHOR_APPROVAL_TEMPLATE_V2.json").read_text()
    )
    assert template["status"] == "PENDING_AUTHOR_REVIEW__DO_NOT_SUBMIT"
    assert not any(template["human_attestations"].values())
    assert not template["author_approved_AI_statement"]
    with pytest.raises(PermissionError):
        policy.validate_author_approval(template, review.ORIGINAL_BLOB)


def test_no_circumvented_science_submission_or_new_neon_response():
    src = (review.LANE / "build_oikos_ceiling_interpretation_review_v3.py").read_text()
    for name in (
        "requests", "urllib", "read_csv(", "openai.ChatCompletion",
        "NEON_API_TOKEN", "run_response_once.py", "render_using_existing_blinded_pdf_builder",
        "AUTHOR_APPROVED", "scholarone.com",
    ):
        # The explicit False "author_approved" status flags are legitimate;
        # never call a source/approval side-effect or render a final PDF.
        if name == "AUTHOR_APPROVED":
            assert 'status": "AUTHOR_APPROVED"' not in src
        else:
            assert name not in src
    assert "No biological response data" not in src or "never opens" in src
