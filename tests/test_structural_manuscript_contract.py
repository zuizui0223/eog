from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKELETON = ROOT / "manuscript" / "structural_reachability_manuscript_skeleton.md"
HIGHLIGHTS = ROOT / "manuscript" / "structural_highlights.txt"
COMPETITOR_MATRIX = ROOT / "docs" / "structural_competitor_matrix.md"
SUBMISSION_CHECKLIST = ROOT / "manuscript" / "structural_submission_checklist.md"
FIGURE_SPEC = ROOT / "manuscript" / "structural_figure_specification.md"


def _markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        raise AssertionError(f"missing level-two section: {heading}")
    return match.group(1).strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def test_structural_abstract_stays_within_working_journal_limit() -> None:
    text = SKELETON.read_text(encoding="utf-8")
    abstract = _markdown_section(text, "Abstract")
    count = _word_count(abstract)
    assert 1 <= count <= 250, f"structural abstract has {count} words"
    assert "0.618" in abstract
    assert "increased held-out log loss by 0.032" in abstract
    assert "not a universally beneficial add-on" in abstract


def test_structural_highlights_obey_elsevier_working_contract() -> None:
    lines = [
        line.strip()
        for line in HIGHLIGHTS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert 3 <= len(lines) <= 5
    assert len(set(lines)) == len(lines)
    for line in lines:
        assert len(line) <= 85, f"highlight has {len(line)} characters: {line}"
        assert not line.startswith(("-", "•")), "editable highlight file stores plain lines"

    joined = " ".join(lines).lower()
    assert "added information" in joined
    assert "did not improve" in joined
    assert "auditable" in joined


def test_submission_documents_preserve_the_negative_boundary() -> None:
    competitor = COMPETITOR_MATRIX.read_text(encoding="utf-8")
    checklist = SUBMISSION_CHECKLIST.read_text(encoding="utf-8")
    figure_spec = FIGURE_SPEC.read_text(encoding="utf-8")

    for text in (competitor, checklist, figure_spec):
        assert "current flow" in text.lower()
        assert "A-Islands" in text
        assert "Tanzania" in text

    assert "does not guarantee a predictive gain" in competitor
    assert "EOG outperforms SDM" in checklist
    assert "No effect estimate" in figure_spec
    assert "candidate-minus-reference" in figure_spec


def test_competitor_matrix_names_required_method_families() -> None:
    text = COMPETITOR_MATRIX.read_text(encoding="utf-8").lower()
    required = (
        "spatial block cv",
        "barrier spde",
        "dynamic occupancy",
        "mechanistic sdm",
        "least-cost path",
        "circuit theory",
        "habitat-patch network",
        "superlevel-set support topology",
    )
    for method in required:
        assert method in text
