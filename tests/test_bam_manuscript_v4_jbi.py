import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = (
    ROOT
    / "manuscript"
    / "bam_identifiability"
    / "MANUSCRIPT_DRAFT_V4_JBI.md"
)


def _words(text: str):
    return re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'’+\-/]*", text)


def test_jbi_title_and_running_title_limits():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].removeprefix("# ")
    running = next(
        line.split(":", 1)[1].strip()
        for line in lines
        if line.startswith("**Running title:**")
    )

    assert len(title) <= 115
    assert len(running) < 40


def test_jbi_structured_abstract_and_keywords():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("## 1. Introduction", 1)[0]

    assert len(_words(abstract)) <= 300
    for heading in (
        "**Aim:**",
        "**Location:**",
        "**Taxon:**",
        "**Methods:**",
        "**Results:**",
        "**Main conclusions:**",
    ):
        assert heading in abstract

    keyword_line = next(
        line for line in abstract.splitlines() if line.startswith("**Keywords:**")
    )
    keywords = [value.strip() for value in keyword_line.split(":", 1)[1].split(",")]
    assert 6 <= len(keywords) <= 10
    assert keywords == sorted(keywords, key=str.lower)


def test_jbi_main_structure_and_length():
    text = MANUSCRIPT.read_text(encoding="utf-8")

    required = (
        "## 1. Introduction",
        "## 2. Methods",
        "## 3. Results",
        "## 4. Discussion",
        "## References",
        "## Data Accessibility Statement",
        "## Figure legends",
    )
    positions = [text.index(marker) for marker in required]
    assert positions == sorted(positions)

    assert len(_words(text)) <= 6000


def test_jbi_main_document_is_anonymized_and_not_eog_wf_mixed():
    text = MANUSCRIPT.read_text(encoding="utf-8").lower()

    for forbidden in (
        "zhang ruiqi",
        "zuizui0223",
        "tohoku university",
        "azores yellow eel",
        "king rail",
        "tampa bay",
        "layer b",
        "macro log loss",
        "3/31/3",
    ):
        assert forbidden not in text


def test_jbi_figure_legends_cover_all_main_figures():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    legends = text.split("## Figure legends", 1)[1]

    for number in range(1, 7):
        assert f"**Figure {number}." in legends


def test_jbi_data_accessibility_keeps_double_anonymous_boundary():
    text = MANUSCRIPT.read_text(encoding="utf-8")
    statement = text.split("## Data Accessibility Statement", 1)[1].split(
        "## Figure legends", 1
    )[0]

    assert "anonymized review repository" in statement
    assert "github.com/" not in statement.lower()
    assert "permanent public archive and DOI" in statement
