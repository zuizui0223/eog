from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "manuscript/submission/author_metadata.template.json"
MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"


def test_author_metadata_template_is_linked_and_unapproved_by_default() -> None:
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["author_metadata_template"] == "manuscript/submission/author_metadata.template.json"
    assert template["schema_version"] == "eog_structural_author_metadata_v1"
    assert template["authors"][0]["name"] == "<AUTHOR_NAME>"
    assert template["corresponding_author"]["email"] == "<EMAIL>"
    assert template["competing_interests"]["confirmed_by_all_authors"] is False
    assert template["ethics_and_permits"]["review_completed"] is False
    assert template["originality_and_submission"]["approved_by_all_authors"] is False
    assert template["originality_and_submission"]["not_published_previously_confirmed"] is False
    assert template["originality_and_submission"]["not_under_consideration_elsewhere_confirmed"] is False
    assert template["generative_ai_disclosure"]["reviewed_by_all_authors"] is False
    assert template["generative_ai_disclosure"]["live_journal_policy_checked"] is False
    assert template["release_metadata"]["creator_order_confirmed"] is False
    assert template["release_metadata"]["software_citation_metadata_approved"] is False


def test_template_does_not_infer_real_author_identity_or_funding() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    for placeholder in (
        "<AUTHOR_NAME>",
        "<ORCID_OR_EMPTY>",
        "<AFFILIATION_ID>",
        "<FUNDER_OR_NONE>",
        "<AUTHOR_APPROVED_STATEMENT>",
        "<FINAL_JOURNAL_COMPLIANT_DISCLOSURE>",
    ):
        assert placeholder in text
