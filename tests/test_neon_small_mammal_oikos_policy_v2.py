"""Oikos Oct-2026 policy + author-approval regression, without new NEON response.

All rendered PDFs in tests use explicitly INVENTED synthetic approved text,
not any author approval or submission-ready user artifact.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from manuscript.neon_small_mammal_continuity import build_oikos_initial_submission_policy_v2 as submit


def test_original_science_and_32_historical_manuscript_blobs_are_untouched():
    identity=submit.integrity_guard()
    assert identity["original_imported_blobs_SHA1_verified"]==32
    assert identity["original_response_lock_fingerprint_verified"]==(
        "c845289d6ad8caf8e932adb90340237b01b120acce52ca2ccb4e6f1d9c10b860")
    assert identity["no_source_file_rewritten"] is True
    assert submit.git_blob_sha1(submit.MANUSCRIPT)=="ada5a84d3b862e122b1d6895c47ed3511de05854"


def test_existing_historical_v1_scientific_source_contains_data_availability_but_no_approved_ai():
    source=submit.MANUSCRIPT.read_text(encoding="utf-8")
    assert source.count("## Data availability")==1
    assert "## AI use statement" not in source
    assert "## Figure captions" in source
    assert "## References" in source
    assert "0/16" in source
    without,data=submit.split_authoritative_sections(source)
    assert "## Data availability" not in without
    assert "Raw NEON response files are not redistributed." in data
    assert "13 of 16" in without
    assert "32 species" in without
    assert "## 4. Discussion" in without


def test_preflight_exports_policy_fields_but_denies_real_pdf_or_author_approval():
    audit=submit.source_only_preflight()
    assert audit["schema"]==submit.PREP_SCHEMA
    assert audit["historical_32_source_blob_identity"]["original_imported_blobs_SHA1_verified"]==32
    assert audit["original_blinded_main_has_data_availability_heading"] is True
    assert audit["original_blinded_main_has_approved_AI_statement"] is False
    assert audit["historical_v1_pdf_for_final_submission_approved"] is False
    assert audit["blinded_policy_v2_pdf_generated"] is False
    assert audit["AI_use_disclosure_author_approved"] is False
    assert audit["separate_title_page_final"] is False
    assert audit["submission_completed"] is False
    assert audit["neon_16_site_response_reopened"] is False
    assert audit["EOG_WF_empirical_denominator_changed"] is False
    assert "github.com/" not in audit["data_availability_statement_for_ScholarOne_only"]
    assert "Species turnover" in audit["significance_statement_for_ScholarOne_only"]


def test_public_author_template_must_fail_closed_and_be_kept_separate():
    p=submit.LANE/"OIKOS_AI_AUTHOR_APPROVAL_TEMPLATE_V2.json"
    pending=json.loads(p.read_text(encoding="utf-8"))
    assert pending["status"]!="AUTHOR_APPROVED"
    assert not any(pending["human_attestations"].values())
    assert not pending["author_approved_AI_statement"]
    with pytest.raises(PermissionError,match="approval"):
        submit.validate_author_approval(pending,submit.git_blob_sha1(submit.MANUSCRIPT))


def synthetic_private_ai_approval():
    return {
        "schema":submit.APPROVAL_SCHEMA,
        "status":"AUTHOR_APPROVED",
        "approved_scope":"anonymous_main_text_AI_declaration_only",
        "source_manuscript_git_blob_sha1":submit.git_blob_sha1(submit.MANUSCRIPT),
        "author_approved_AI_statement":(
            "INVENTED SYNTHETIC TEST DECLARATION ONLY. A fictional test assistant "
            "helped with formatting and code review during 2026. In this invented "
            "test fixture, all simulated authors reviewed the generated text, "
            "checked statistical claims and took final responsibility."
        ),
        "human_attestations":{
            "actual_AI_tools_names_versions_and_dates_verified":True,
            "AI_use_purpose_and_extent_personally_checked":True,
            "all_coauthors_reviewed_and_approved_AI_wording":True,
            "author_accountability_and_fact_checks_confirmed":True,
            "no_author_identifiers_in_blinded_AI_declaration":True,
        },
    }


@pytest.mark.parametrize("edit",[
    lambda x:x.update(status="PENDING"),
    lambda x:x.update(source_manuscript_git_blob_sha1="f"*40),
    lambda x:x.update(approved_scope="all_author_details"),
    lambda x:x["human_attestations"].update(all_coauthors_reviewed_and_approved_AI_wording=False),
    lambda x:x["human_attestations"].update(actual_AI_tools_names_versions_and_dates_verified=False),
    lambda x:x.update(author_approved_AI_statement="PENDING"),
    lambda x:x.update(author_approved_AI_statement="Placeholder, to be confirmed later."),
])
def test_missing_author_verified_ai_language_or_source_version_denied(edit):
    a=synthetic_private_ai_approval()
    edit(a)
    with pytest.raises(PermissionError):
        submit.validate_author_approval(a,submit.git_blob_sha1(submit.MANUSCRIPT))


@pytest.mark.parametrize("bad",[
    "contact the scientist at sample@example.com to request the code",
    "the authors are named in https://github.com/owner/repository",
    "corresponding author ORCID details are disclosed here",
])
def test_blind_statement_rejects_email_repo_and_author_identifiers(bad):
    a=synthetic_private_ai_approval()
    a["author_approved_AI_statement"]=a["author_approved_AI_statement"]+" "+bad
    with pytest.raises(ValueError,match="Potential identity|Email"):
        submit.validate_author_approval(a,submit.git_blob_sha1(submit.MANUSCRIPT))


def test_new_anonymous_markdown_preserves_science_and_places_only_author_approved_ai():
    approved=submit.validate_author_approval(
        synthetic_private_ai_approval(),submit.git_blob_sha1(submit.MANUSCRIPT))
    source=submit.MANUSCRIPT.read_text(encoding="utf-8")
    rendered,data=submit.compose_blinded_main(source,approved)
    assert rendered.count("## AI use statement")==1
    assert rendered.index("## 4. Discussion")<rendered.index("## AI use statement")
    assert rendered.index("## AI use statement")<rendered.index("## Figure captions")
    assert rendered.index("## Figure captions")<rendered.index("## References")
    assert "## Data availability" not in rendered
    assert "The primary data are the NSF National Ecological Observatory Network" in data
    assert approved in rendered
    assert "13 of 16 sites" in rendered
    assert "ORNL" in rendered
    without,_=submit.split_authoritative_sections(source)
    assert rendered==without.replace("## Figure captions",
                                    "## AI use statement\n\n"+approved+"\n\n## Figure captions",1)
    assert submit.git_blob_sha1(submit.MANUSCRIPT)=="ada5a84d3b862e122b1d6895c47ed3511de05854"


def test_non_author_approved_mode_only_exports_anonymous_form_statements(tmp_path,monkeypatch):
    output=tmp_path/"source-only-preflight"
    monkeypatch.setattr(sys,"argv",["builder","--output-dir",str(output)])
    submit.main()
    assert (output/"OIKOS_SCHOLARONE_DATA_AVAILABILITY_V2.txt").is_file()
    assert (output/"OIKOS_SCHOLARONE_SIGNIFICANCE_V2.txt").is_file()
    status=json.loads((output/"OIKOS_SUBMISSION_POLICY_PREFLIGHT_V2.json").read_text())
    assert status["AI_use_disclosure_author_approved"] is False
    assert status["submission_completed"] is False
    assert not list(output.glob("*.pdf"))
    assert not list(output.glob("*AI_APPROVED*"))
    with pytest.raises(FileExistsError,match="overwrite"):
        submit.main()


def test_private_synthetic_author_approval_builds_a_different_anonymous_pdf(tmp_path,monkeypatch):
    pytest.importorskip("reportlab")
    from pypdf import PdfReader
    test_ai=synthetic_private_ai_approval()
    private=tmp_path/"NOT_ACTUAL_AUTHOR_APPROVAL_Synthetic_Private_Test.json"
    private.write_text(json.dumps(test_ai),encoding="utf-8")
    target=tmp_path/"invented-approved-test-only"
    monkeypatch.setattr(sys,"argv",[
        "builder","--output-dir",str(target),"--approval-json",str(private)
    ])
    submit.main()
    ready=json.loads((target/"OIKOS_SUBMISSION_POLICY_PREFLIGHT_V2.json").read_text())
    pdf=target/"OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.pdf"
    md=target/"OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.md"
    assert ready["AI_use_disclosure_author_approved"] is True
    assert ready["blinded_policy_v2_pdf_generated"] is True
    assert ready["submission_completed"] is False
    assert ready["separate_title_page_final"] is False
    assert pdf.stat().st_size>10000
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()==ready["prepared_main_pdf_sha256"]
    assert len(PdfReader(str(pdf)).pages)>=8
    pdfreader=PdfReader(str(pdf))
    pdftext="\n".join(page.extract_text() for page in pdfreader.pages)
    assert "AI use statement" in pdftext
    assert "INVENTED SYNTHETIC TEST DECLARATION" in pdftext
    assert "Data availability" not in pdftext
    assert "Species turnover" in pdftext
    assert "Figure captions" in pdftext
    assert "References" in pdftext
    assert "The primary data are the NSF" not in pdftext
    assert "github.com/" not in pdftext
    assert "sample@example.com" not in pdftext
    assert "Author" not in str(pdfreader.metadata.get("/Author",""))
    assert "## Data availability" not in md.read_text(encoding="utf-8")
    assert private.name not in md.read_text(encoding="utf-8")
    assert (target/"OIKOS_SCHOLARONE_DATA_AVAILABILITY_V2.txt").is_file()
    assert submit.git_blob_sha1(submit.MANUSCRIPT)=="ada5a84d3b862e122b1d6895c47ed3511de05854"


def test_no_new_neon_response_import_or_author_metadata_autofill():
    script=(submit.LANE/"build_oikos_initial_submission_policy_v2.py").read_text()
    for forbidden in ("requests", "urllib", "read_csv(", "run_response_once.py",
                      "NEON_API_TOKEN","fetch_workflow","openai.ChatCompletion"):
        assert forbidden not in script
    assert "MANUSCRIPT_V1.md" in script
    assert "MAINLINE_PORT_REPRODUCIBILITY_RECEIPT_V1.json" in script
    assert "submission_completed" in script
