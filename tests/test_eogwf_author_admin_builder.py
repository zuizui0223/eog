import json
from pathlib import Path

import pytest

from manuscript.build_eogwf_author_admin import (
    AuthorAdminError,
    build,
    validate_admin_receipt,
)


def confirmed_payload():
    return {
        "schema": "eog.eogwf_author_admin_confirmation.v1",
        "manuscript": {
            "title": (
                "Environmental Occupancy Geometry: auditable finite-world "
                "falsification with a prospectively stress-tested prediction interface"
            ),
            "journal": "Methods in Ecology and Evolution",
            "article_type": "Research Article",
            "running_headline_suggestion": "Environmental Occupancy Geometry",
            "review_snapshot_commit": "91125ae68004f298fcd45027566506772a3688d5",
            "review_snapshot_url": (
                "https://github.com/zuizui0223/eog/tree/"
                "91125ae68004f298fcd45027566506772a3688d5"
            ),
        },
        "authors": [
            {
                "id": "A1",
                "full_name": "Author One",
                "orcid": "0000-0001-2345-678X",
                "affiliation_ids": ["F1"],
                "credit_roles": ["Conceptualization", "Software", "Writing – original draft"],
            }
        ],
        "affiliations": [
            {
                "id": "F1",
                "institution": "Example University",
                "department": "Department of Ecology",
                "city": "Example City",
                "country": "Exampleland",
            }
        ],
        "corresponding_author": {
            "author_id": "A1",
            "email": "author@example.org",
            "postal_address": "1 Example Road, Example City",
        },
        "running_headline": "Environmental Occupancy Geometry",
        "acknowledgements": "No additional acknowledgements.",
        "funding": {
            "confirmed_by_all_authors": True,
            "statement": "No external or dedicated funding to declare.",
        },
        "competing_interests": {
            "confirmed_by_all_authors": True,
            "statement": "The authors declare no competing interests.",
        },
        "ethics_and_permits": {
            "reviewed_by_all_authors": True,
            "statement": "No additional ethics or permit statement is required.",
        },
        "originality_and_submission": {
            "approved_by_all_authors": True,
            "not_published_previously_confirmed": True,
            "not_under_consideration_elsewhere_confirmed": True,
        },
        "inclusion_statement": {
            "approved_by_all_authors": True,
            "statement": "Author-approved inclusion statement.",
        },
        "ai_llm": {
            "application": "ChatGPT",
            "provider": "OpenAI",
            "model_or_version": "Author-confirmed model/version",
            "approximate_period": "Author-confirmed period",
            "assistance_categories": [
                "code review and generation",
                "reproducibility checks",
                "literature triage",
                "manuscript organization",
                "language editing",
            ],
            "other_assistance": None,
            "specific_code_or_text_annotations": None,
            "responsible_author_id": "A1",
            "final_methods_disclosure": (
                "During manuscript preparation, the authors used an author-confirmed "
                "AI-assisted workflow. All generated material was reviewed by the authors."
            ),
            "contribution_statement": (
                "Author One reviewed all AI-assisted code and text and accepts "
                "responsibility for the final manuscript."
            ),
            "reviewed_by_all_authors": True,
            "author_accountability_confirmed": True,
            "live_journal_policy_checked": True,
        },
        "confirmations": {
            "author_order_approved": True,
            "affiliations_approved": True,
            "corresponding_author_approved": True,
            "credit_roles_approved": True,
            "acknowledgements_approved": True,
            "running_headline_approved": True,
            "final_title_page_approved": True,
            "final_ai_llm_disclosure_approved": True,
        },
    }


def test_unconfirmed_template_fails_closed(tmp_path):
    payload = confirmed_payload()
    payload["confirmations"]["final_title_page_approved"] = False
    path = tmp_path / "confirmation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AuthorAdminError, match="final_title_page_approved"):
        build(
            path,
            tmp_path / "title.md",
            tmp_path / "ai.md",
            Path("manuscript/EOG_WF_MANUSCRIPT_V1.md"),
            tmp_path / "final.md",
            tmp_path / "receipt.json",
        )


def test_confirmed_payload_generates_all_admin_outputs(tmp_path):
    path = tmp_path / "confirmation.json"
    path.write_text(json.dumps(confirmed_payload()), encoding="utf-8")
    title = tmp_path / "title.md"
    ai = tmp_path / "ai.md"
    final = tmp_path / "final.md"
    receipt = tmp_path / "receipt.json"

    result = build(
        path,
        title,
        ai,
        Path("manuscript/EOG_WF_MANUSCRIPT_V1.md"),
        final,
        receipt,
    )
    assert result["status"] == "author_admin_outputs_generated"
    assert title.exists()
    assert ai.exists()
    assert final.exists()
    assert receipt.exists()
    assert "Author One" in title.read_text(encoding="utf-8")
    assert "### AI / LLM use in manuscript preparation" in final.read_text(
        encoding="utf-8"
    )
    assert validate_admin_receipt(
        receipt,
        title_path=title,
        ai_path=ai,
        manuscript_path=final,
    ) is True


def test_receipt_detects_postapproval_output_mutation(tmp_path):
    path = tmp_path / "confirmation.json"
    path.write_text(json.dumps(confirmed_payload()), encoding="utf-8")
    title = tmp_path / "title.md"
    ai = tmp_path / "ai.md"
    final = tmp_path / "final.md"
    receipt = tmp_path / "receipt.json"
    build(
        path,
        title,
        ai,
        Path("manuscript/EOG_WF_MANUSCRIPT_V1.md"),
        final,
        receipt,
    )
    title.write_text(title.read_text(encoding="utf-8") + "\nMUTATED\n", encoding="utf-8")
    assert validate_admin_receipt(
        receipt,
        title_path=title,
        ai_path=ai,
        manuscript_path=final,
    ) is False


def test_running_headline_limit_is_enforced(tmp_path):
    payload = confirmed_payload()
    payload["running_headline"] = "X" * 46
    path = tmp_path / "confirmation.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(AuthorAdminError, match="45 characters"):
        build(
            path,
            tmp_path / "title.md",
            tmp_path / "ai.md",
            Path("manuscript/EOG_WF_MANUSCRIPT_V1.md"),
            tmp_path / "final.md",
            tmp_path / "receipt.json",
        )
