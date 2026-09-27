from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "manuscript" / "neon_small_mammal_continuity"
MANUSCRIPT = LANE / "MANUSCRIPT_V1.md"


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9.'-]*", text))


def test_oikos_blinded_main_text_and_abstract_limit():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    match = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Keywords:", text, re.S)
    assert match is not None
    abstract = match.group(1)

    assert _word_count(abstract) <= 300
    assert "**Keywords:**" in text

    lowered = text.lower()
    assert "github.com/" not in lowered
    assert "orcid" not in lowered
    assert "corresponding author" not in lowered
    assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)


def test_oikos_initial_submission_support_files_exist():
    required = [
        "OIKOS_TITLE_PAGE_TEMPLATE_V1.md",
        "OIKOS_SIGNIFICANCE_STATEMENT_V1.md",
        "OIKOS_DECLARATIONS_PACKET_V1.md",
        "AI_USE_STATEMENT_V1.md",
        "DATA_CODE_AVAILABILITY_V1.md",
        "FIGURE_CAPTIONS_ACCESSIBILITY_V1.md",
        "ANONYMOUS_REVIEW_PACKAGE_V1.md",
        "ANONYMOUS_REVIEW_BUNDLE_RECEIPT_V1.json",
        "OIKOS_INITIAL_SUBMISSION_AUDIT_V1.json",
        "SUBMISSION_CHECKLIST_V1.md",
    ]
    for name in required:
        path = LANE / name
        assert path.is_file()
        assert path.stat().st_size > 0


def test_anonymous_review_bundle_was_identity_scanned():
    receipt = json.loads(
        (LANE / "ANONYMOUS_REVIEW_BUNDLE_RECEIPT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    scan = receipt["manual_identity_scan"]

    assert receipt["contains_api_token"] is False
    assert receipt["contains_raw_neon_response_files"] is False
    assert scan["author_name_found"] is False
    assert scan["email_found"] is False
    assert scan["orcid_found"] is False
    assert scan["github_owner_link_found"] is False
    assert len(receipt["inner_zip_sha256"]) == 64


def test_oikos_submission_audit_has_only_admin_or_packaging_blockers():
    audit = json.loads(
        (LANE / "OIKOS_INITIAL_SUBMISSION_AUDIT_V1.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit["current_status"]["science_closed"] is True
    assert audit["current_status"]["abstract_within_limit"] is True
    assert audit["current_status"]["reviewer_data_code_anonymous_package"] == (
        "generated_and_identity_scanned"
    )
    assert audit["current_status"]["initial_submission_science_files"] == "ready"

    blockers = " ".join(audit["remaining_initial_submission_inputs"]).lower()
    assert "author" in blockers
    assert "orcid" in blockers
    assert "funding" in blockers
    assert "conflict" in blockers
    assert "response access" not in blockers
    assert "retun" not in blockers
