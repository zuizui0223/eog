from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
GENERIC = ROOT / "manuscript/history_storage/MANUSCRIPT_DRAFT_V1.md"
EL = ROOT / "manuscript/history_storage/MANUSCRIPT_ECOLOGY_LETTERS_V1.md"


def _word_count(text: str) -> int:
    cleaned = re.sub(r"[\\*_\`#>\[\](){}]", " ", text)
    return len([word for word in cleaned.split() if word])


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start) + len(start)
    j = text.index(end, i)
    return text[i:j].strip()


def test_current_claim_boundary_and_source_reconciliation():
    text = GENERIC.read_text(encoding="utf-8")

    assert "The present archive has a hard mechanistic ceiling" in text
    assert "The main result is therefore structural rather than mechanistic" in text
    assert "first-arriver-role explanation failed a complete specificity audit" in text
    assert "Alonso-Crespo et al. (2023)" in text
    assert "Alonso-Crespo et al. (2022)" not in text

    el_text = EL.read_text(encoding="utf-8")
    assert "Alonso-Crespo et al. (2023)" in el_text
    assert "Alonso-Crespo et al. (2022)" not in el_text

    assert "10.5281/zenodo.3872145" in text
    assert "10.5061/dryad.7p2cv" not in text
    assert "10.5281/zenodo.3872145" in el_text
    assert "10.5061/dryad.7p2cv" not in el_text
    assert "10.5281/zenodo.5713397" in text


def test_ecology_letters_length_contract():
    text = EL.read_text(encoding="utf-8")

    abstract = _section(text, "## Abstract\n", "\n## Introduction\n")
    main = _section(text, "## Introduction\n", "\n## Data and code availability")

    assert _word_count(abstract) <= 150
    assert _word_count(main) <= 5000

    assert "**Article type:** Letter" in text
    assert "**Figures:** 4" in text
    assert "**Tables:** 0" in text
    assert "**Text boxes:** 0" in text


def test_failed_mechanism_is_not_resurrected():
    text = GENERIC.read_text(encoding="utf-8")

    assert "We retained the numerical role-alignment results as descriptive transformations but rejected the interpretation" in text
    assert "does not reveal the interaction process that generates that pattern" in text
