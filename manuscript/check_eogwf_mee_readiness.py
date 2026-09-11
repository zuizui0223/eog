#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript/EOG_WF_MANUSCRIPT_V1.md"
TITLE_PAGE = ROOT / "manuscript/EOG_WF_TITLE_PAGE.md"
BOUNDARY = ROOT / "manuscript/paper_ready/submission_boundary.json"
OUT = ROOT / "build/eogwf_mee_submission_readiness.json"

WORD_RE = re.compile(r"\b[\w’'/-]+\b", re.UNICODE)


def _section(text: str, heading: str, next_heading: str | None = None) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    if next_heading is None:
        return text[start:]
    end = text.find(next_heading, start)
    return text[start:] if end < 0 else text[start:end]


def main() -> int:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    abstract = _section(text, "## Abstract", "## Introduction")

    abstract_numbers = [bool(re.search(rf"(?m)^\*\*{i}\.\*\*", abstract)) for i in range(1, 5)]
    abstract_word_count = len(WORD_RE.findall(abstract.split("**Keywords:**", 1)[0]))
    whole_word_count = len(WORD_RE.findall(text))
    ref_placeholders = text.count("[REF]")
    final_placeholders = len(re.findall(r"\[FINAL[^\]]*\]", text))

    abstract_pos = text.find("## Abstract")
    data_code_pos = text.find("**Data and code for peer review:**")
    keywords_pos = text.find("**Keywords:**")
    intro_pos = text.find("## Introduction")
    benchmark_pos = text.find("### Deterministic known-truth method benchmark")
    results_pos = text.find("## Results")

    scientific_checks = {
        "closed_denominator_three": boundary.get("fresh_predictive_endpoints_with_scores") == 3,
        "fourth_endpoint_forbidden": boundary.get("fourth_fresh_endpoint_allowed") is False,
        "candidate_hunting_hard_stop": boundary.get("candidate_hunting_hard_stop") is True,
        "abstract_numbered_1_to_4": all(abstract_numbers),
        "abstract_at_most_350_words": abstract_word_count <= 350,
        "data_code_statement_after_abstract_before_intro": abstract_pos < data_code_pos < intro_pos,
        "keywords_after_abstract_before_intro": abstract_pos < keywords_pos < intro_pos,
        "known_truth_benchmark_before_empirical_results": 0 <= benchmark_pos < results_pos,
        "no_reference_placeholders": ref_placeholders == 0,
        "references_section_present": "## References" in text,
        "word_count_at_most_8000": whole_word_count <= 8000,
    }

    author_admin_checks = {
        "title_page_present": TITLE_PAGE.exists(),
        "final_archive_doi_placeholder_resolved": final_placeholders == 0,
    }

    result = {
        "schema": "eog.eogwf_mee_submission_readiness.v1",
        "manuscript": str(MANUSCRIPT.relative_to(ROOT)),
        "journal": "Methods in Ecology and Evolution",
        "article_type": "Research Article",
        "word_count_method": "regex word tokens over the complete Markdown manuscript, including abstract, statements, captions/references if present and checklist",
        "whole_manuscript_word_count": whole_word_count,
        "abstract_word_count": abstract_word_count,
        "reference_placeholders": ref_placeholders,
        "final_placeholders": final_placeholders,
        "scientific_checks": scientific_checks,
        "author_admin_checks": author_admin_checks,
        "scientific_desk_fit_ready": all(scientific_checks.values()),
        "submission_ready": all(scientific_checks.values()) and all(author_admin_checks.values()),
        "unresolved_scientific": [k for k, v in scientific_checks.items() if not v],
        "unresolved_author_admin": [k for k, v in author_admin_checks.items() if not v],
        "boundary_snapshot": {
            "fresh_scored_endpoints": boundary.get("fresh_predictive_endpoints_with_scores"),
            "favorable_endpoints": boundary.get("favorable_endpoints"),
            "adverse_endpoints": boundary.get("adverse_endpoints"),
            "scientific_protocol_stops": boundary.get("scientific_protocol_stops"),
            "administrative_exclusions": boundary.get("administrative_exclusions"),
            "primary_submission_route": boundary.get("primary_submission_route"),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scientific_desk_fit_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
