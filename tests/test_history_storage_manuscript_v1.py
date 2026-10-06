from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "manuscript/history_storage/MANUSCRIPT_DRAFT_V1.md"


def test_manuscript_has_no_broken_math_markers():
    text = DRAFT.read_text(encoding="utf-8")
    forbidden = [
        "(R^2)",
        "operatorname{",
        "\n[\nE =",
        "\n[\nD_h =",
        "(p=",
        "(E=",
    ]
    for token in forbidden:
        assert token not in text


def test_manuscript_uses_oikos_version_of_record_year():
    text = DRAFT.read_text(encoding="utf-8")
    assert "Alonso-Crespo et al. 2023" in text
    assert "Alonso-Crespo et al. 2022" not in text
    assert "(2023). Assembly history modulates vertical root distribution" in text


def test_claim_boundary_is_explicit():
    text = DRAFT.read_text(encoding="utf-8")
    assert "not as a formal test that two target-specific partial-R² parameters are equal" in text
    assert "The present archive has a hard mechanistic ceiling" in text
    assert "The main result is therefore structural rather than mechanistic" in text
