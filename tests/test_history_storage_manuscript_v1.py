from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "manuscript/history_storage/MANUSCRIPT_DRAFT_V1.md"
STRATEGY = ROOT / "manuscript/history_storage/SUBMISSION_STRATEGY_V1.md"


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


def test_submission_strategy_uses_oikos_version_of_record_year():
    text = STRATEGY.read_text(encoding="utf-8")
    assert "Alonso-Crespo et al. (2023)" in text
    assert "Alonso-Crespo et al. (2022)" not in text


def test_submission_uses_correct_microbiome_archive():
    text = DRAFT.read_text(encoding="utf-8")
    assert "10.5281/zenodo.3872145" in text
    assert "PRJNA605581" in text
    assert "10.5061/dryad.7p2cv" not in text
    assert "10.5281/zenodo.5713397" in text


def test_claim_boundaries_are_explicit():
    text = DRAFT.read_text(encoding="utf-8")
    assert (
        "not as a formal test that two target-specific partial-R² parameters are equal"
        in text
    )
    assert "The present archive has a hard mechanistic ceiling" in text
    assert "The main result is therefore structural rather than mechanistic" in text
