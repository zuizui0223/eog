#!/usr/bin/env python3
"""Non-destructive 2026 NSO/Oikos initial-submission preparation.

Original 32 manuscript source files, earlier rendered PDFs and scientific
results MUST retain their original Git blob identities. This builder
moves a DATA AVAILABILITY STATEMENT to a ScholarOne-only field and adds an
AI USE STATEMENT to a *new* anonymous main-text artifact ONLY after explicit
human author approval. Unapproved drafts may NOT generate an allegedly
submission-ready PDF. No biological response data or model fits are accessed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
LANE=ROOT/"manuscript"/"neon_small_mammal_continuity"
MANUSCRIPT=LANE/"MANUSCRIPT_V1.md"
PORT=LANE/"MAINLINE_PORT_REPRODUCIBILITY_RECEIPT_V1.json"
RESPONSE=ROOT/"validation/neon_metacommunity_connectivity_v1/response_lock_v1.json"
SIGNIFICANCE=LANE/"OIKOS_SIGNIFICANCE_STATEMENT_V1.md"
APPROVAL_SCHEMA="eog.neon_small_mammal_continuity.oikos_author_ai_approval.v2"
PREP_SCHEMA="eog.neon_small_mammal_continuity.oikos_policy_preflight.v2"
SPLIT_MARKER="## Data availability"
NEXT_MARKER="## Figure captions"
AI_MARKER="## AI use statement"
OFFICIAL_GUIDE="https://nso-journals.org/author-guidelines"
JOURNAL_GUIDE="https://nso-journals.org/oikos-for-authors"
SCIENTIFIC_RESULT="c845289d6ad8caf8e932adb90340237b01b120acce52ca2ccb4e6f1d9c10b860"


def git_blob_sha1(path:Path)->str:
    raw=path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii")+raw).hexdigest()


def integrity_guard()->dict:
    frozen=json.loads(PORT.read_text(encoding="utf-8"))
    if (
        frozen.get("schema")!="eog.neon_small_mammal_continuity.source_preserving_mainline_port.v1"
        or frozen.get("status")!="VERIFIED_CONTENT_EQUIVALENCE_OF_REBASED_PAPER_ASSETS__NOT_SUBMITTED"
        or frozen.get("source",{}).get("response_fingerprint")!=SCIENTIFIC_RESULT
        or frozen.get("source",{}).get("fixed_sites")!=16
        or frozen.get("source",{}).get("scored_sites")!=16
    ):
        raise ValueError("Original NEON response or manuscript handoff identity changed")
    files=frozen.get("original_32_imported_files")
    if not isinstance(files,list) or len(files)!=32 or len({x["path"] for x in files})!=32:
        raise ValueError("Original 32 scientific-paper file roster drifted")
    for entry in files:
        name=entry["path"]
        if not name.startswith(("manuscript/neon_small_mammal_continuity/",
                                "tests/test_neon_small_mammal_continuity_",
                                ".github/workflows/neon-small-mammal-continuity-paper-assets.yml")):
            raise ValueError("Unexpected historical source to overwrite")
        if git_blob_sha1(ROOT/name)!=entry["blob_sha1"]:
            raise ValueError("Original imported manuscript science/source blob changed: "+name)
    response=json.loads(RESPONSE.read_text(encoding="utf-8"))
    if (
        response.get("result_fingerprint")!=SCIENTIFIC_RESULT
        or response["denominator"]!={"fixed_sites":16,"scored_sites":16,"response_consumed_stops":0}
        or response["primary"]["positive_null_adjusted_site_count"]!=0
        or response["primary"]["one_sided_sign_test_p"]!=1
        or response["rerun_allowed"] is not False
    ):
        raise ValueError("Original scientific response lock was altered")
    return {
        "original_imported_blobs_SHA1_verified":32,
        "original_response_lock_fingerprint_verified":SCIENTIFIC_RESULT,
        "no_source_file_rewritten":True,
    }


def split_authoritative_sections(original:str)->tuple[str,str]:
    """Extract exactly one already-written Data availability section."""
    if original.count(SPLIT_MARKER)!=1 or original.count(NEXT_MARKER)!=1:
        raise ValueError("Cannot unambiguously separate scientific/main-text sections")
    start=original.index(SPLIT_MARKER)
    end=original.index(NEXT_MARKER)
    if end<=start or "## 4. Discussion" not in original[:start] or "## References" not in original[end:]:
        raise ValueError("Original source section order or figure citations changed")
    statement=original[start+len(SPLIT_MARKER):end].strip()
    if len(statement)<100 or "NEON" not in statement:
        raise ValueError("Original data availability content not supported")
    blind_without_statement=original[:start]+original[end:]
    if SPLIT_MARKER in blind_without_statement or len(blind_without_statement)<15000:
        raise ValueError("Scientific main-text source was unexpectedly lost")
    return blind_without_statement,statement


def significance_for_form(raw:str)->str:
    if not raw.startswith("# Oikos significance statement\n"):
        raise ValueError("Original author prepared significance statement changed")
    text=raw.split("\n",1)[1].strip()
    if len(text)<100:
        raise ValueError("Significance statement empty")
    return text


def _check_blind_text(text:str)->None:
    lowered=text.lower()
    for forbidden in ("github.com/","orcid", "mailto:", "corresponding author",
                      "zuizui0223","sk-proj","ghp_"):
        if forbidden in lowered:
            raise ValueError("Potential identity/source token in blinded material: "+forbidden)
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",text):
        raise ValueError("Email present in blinded material")


def validate_author_approval(data:dict,manuscript_sha1:str)->str:
    """Reject any inferred approval, unverified disclosure, or author identity."""
    if (
        data.get("schema")!=APPROVAL_SCHEMA
        or data.get("source_manuscript_git_blob_sha1")!=manuscript_sha1
        or data.get("approved_scope")!="anonymous_main_text_AI_declaration_only"
        or data.get("status")!="AUTHOR_APPROVED"
    ):
        raise PermissionError("Explicit final-manuscript author approval is missing")
    att=data.get("human_attestations",{})
    expected={
        "actual_AI_tools_names_versions_and_dates_verified":True,
        "AI_use_purpose_and_extent_personally_checked":True,
        "all_coauthors_reviewed_and_approved_AI_wording":True,
        "author_accountability_and_fact_checks_confirmed":True,
        "no_author_identifiers_in_blinded_AI_declaration":True,
    }
    if att!=expected:
        raise PermissionError("All author-level AI declaration attestations must be true")
    statement=data.get("author_approved_AI_statement","").strip()
    if (
        len(statement)<80
        or "\n## " in statement
        or "\n# " in statement
        or any(s in statement.lower() for s in (
            "[insert","[author","todo","placeholder","tbc","to be confirmed",
            "not yet approved","pending", "xxxxx"
        ))
    ):
        raise PermissionError("The exact author-verified AI declaration is not provided")
    _check_blind_text(statement)
    return statement


def compose_blinded_main(source:str, ai_approved:str)->tuple[str,str]:
    without_data,data_statement=split_authoritative_sections(source)
    _check_blind_text(without_data)
    if AI_MARKER in without_data:
        raise ValueError("Source already has an AI declaration; dual disclosure prohibited")
    insertion=AI_MARKER+"\n\n"+ai_approved.strip()+"\n\n"
    prepared=without_data.replace(NEXT_MARKER,insertion+NEXT_MARKER,1)
    if (
        prepared.count(AI_MARKER)!=1
        or prepared.count("## References")!=1
        or prepared.index("## 4. Discussion")>prepared.index(AI_MARKER)
        or prepared.index(AI_MARKER)>prepared.index(NEXT_MARKER)
        or "## Data availability" in prepared
    ):
        raise ValueError("Author-approved disclosure not at end of blinded main text")
    _check_blind_text(prepared)
    return prepared,data_statement


def source_only_preflight()->dict:
    check=integrity_guard()
    source=MANUSCRIPT.read_text(encoding="utf-8")
    without_data,data=split_authoritative_sections(source)
    _check_blind_text(without_data)
    significance=significance_for_form(SIGNIFICANCE.read_text(encoding="utf-8"))
    return {
        "schema":PREP_SCHEMA,
        "status":"SCIENCE_AND_POLICY_FIELDS_PREPARED__AUTHOR_APPROVAL_AND_ADMIN_STILL_REQUIRED",
        "checked_date":"2026-10-27",
        "official_author_guideline":OFFICIAL_GUIDE,
        "official_oikos_page":JOURNAL_GUIDE,
        "historical_32_source_blob_identity":check,
        "scientific_response_lock_unchanged":True,
        "source_manuscript_git_blob_sha1":git_blob_sha1(MANUSCRIPT),
        "data_availability_statement_for_ScholarOne_only":data,
        "significance_statement_for_ScholarOne_only":significance,
        "original_blinded_main_has_data_availability_heading":True,
        "original_blinded_main_has_approved_AI_statement":False,
        "historical_v1_pdf_for_final_submission_approved":False,
        "blinded_policy_v2_pdf_generated":False,
        "separate_title_page_final":False,
        "corresponding_author_ORCID_approved":False,
        "conflicts_funding_acknowledgements_approved":False,
        "AI_use_disclosure_author_approved":False,
        "reviewer_zip_existing_identity_scanned_not_published_as_permanent_archive":True,
        "submission_completed":False,
        "EOG_WF_empirical_denominator_changed":False,
        "neon_16_site_response_reopened":False,
    }


def render_using_existing_blinded_pdf_builder(source:Path,out:Path)->None:
    """Reuse original ReportLab formatting in a separate process-scoped module."""
    import importlib.util
    generator=LANE/"build_oikos_blinded_pdf.py"
    spec=importlib.util.spec_from_file_location("_original_oikos_v1_pdf_renderer",generator)
    if spec is None or spec.loader is None:
        raise RuntimeError("Original audited PDF renderer unavailable")
    old=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    old.SOURCE=source
    old.OUT=out
    old.main()
    if not out.is_file() or out.stat().st_size<10000:
        raise RuntimeError("Author-approved blinded PDF was not rendered correctly")


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--approval-json",type=Path,help="PRIVATE author-signoff file outside the repository; not the public template")
    args=ap.parse_args()
    if args.output_dir.exists() or args.output_dir.is_symlink():
        raise FileExistsError("Refuse to overwrite existing manuscript submission-preflight directory")
    preflight=source_only_preflight()
    approval=None
    if args.approval_json is not None:
        if args.approval_json.is_symlink() or not args.approval_json.is_file():
            raise PermissionError("Explicit private author approval JSON file unavailable")
        approval=json.loads(args.approval_json.read_text(encoding="utf-8"))
        ai=validate_author_approval(approval,preflight["source_manuscript_git_blob_sha1"])
        source_text=MANUSCRIPT.read_text(encoding="utf-8")
        new_main,original_data=compose_blinded_main(source_text,ai)
        if original_data!=preflight["data_availability_statement_for_ScholarOne_only"]:
            raise ValueError("Mismatch in originally supported data availability text")
    args.output_dir.mkdir(parents=True)
    (args.output_dir/"OIKOS_SCHOLARONE_DATA_AVAILABILITY_V2.txt").write_text(
        preflight["data_availability_statement_for_ScholarOne_only"]+"\n",encoding="utf-8")
    (args.output_dir/"OIKOS_SCHOLARONE_SIGNIFICANCE_V2.txt").write_text(
        preflight["significance_statement_for_ScholarOne_only"]+"\n",encoding="utf-8")
    if approval is not None:
        paper=args.output_dir/"OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.md"
        pdf=args.output_dir/"OIKOS_ANONYMOUS_MAIN_AI_APPROVED_V2.pdf"
        paper.write_text(new_main,encoding="utf-8")
        render_using_existing_blinded_pdf_builder(paper,pdf)
        preflight["status"]="ANONYMOUS_MAIN_AI_DECLARATION_AUTHOR_APPROVED__OTHER_AUTHOR_ADMIN_STILL_REQUIRED"
        preflight["blinded_policy_v2_pdf_generated"]=True
        preflight["AI_use_disclosure_author_approved"]=True
        preflight["approved_ai_text_sha256"]=hashlib.sha256(ai.encode("utf-8")).hexdigest()
        preflight["prepared_main_markdown_sha256"]=hashlib.sha256(new_main.encode("utf-8")).hexdigest()
        preflight["prepared_main_pdf_sha256"]=hashlib.sha256(pdf.read_bytes()).hexdigest()
        preflight["source_science_unchanged"]=True
    # No private approval file, personal author details, or original biological response.
    (args.output_dir/"OIKOS_SUBMISSION_POLICY_PREFLIGHT_V2.json").write_text(
        json.dumps(preflight,indent=2,sort_keys=True,ensure_ascii=False)+"\n",
        encoding="utf-8")
    print(json.dumps({
        "status":preflight["status"],
        "author_approved_blinded_main_pdf_written":preflight["blinded_policy_v2_pdf_generated"],
        "all_original_scientific_blobs_preserved":True,
        "final_submission_completed":False,
    }))


if __name__=="__main__":
    main()
