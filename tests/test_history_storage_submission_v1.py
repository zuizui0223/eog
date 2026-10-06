from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "manuscript/history_storage"

DRAFTS = [
    HISTORY / "MANUSCRIPT_DRAFT_V1.md",
    HISTORY / "MANUSCRIPT_ECOLOGY_LETTERS_V1.md",
]


def test_submission_manuscripts_have_no_broken_math_markers():
    forbidden = [
        "(R^2)",
        "operatorname{",
        "\n[\nE =",
        "\n[\nD_h =",
        "(p=",
        "(E=",
    ]
    for path in DRAFTS:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, (path, token)


def test_submission_manuscripts_use_oikos_version_of_record_year():
    for path in DRAFTS:
        text = path.read_text(encoding="utf-8")
        assert "Alonso-Crespo et al. 2023" in text
        assert "Alonso-Crespo et al. 2022" not in text
        assert "(2023). Assembly history modulates vertical root distribution" in text


def test_submission_manuscripts_use_correct_microbiome_archive():
    for path in DRAFTS:
        text = path.read_text(encoding="utf-8")
        assert "10.5281/zenodo.3872145" in text
        assert "PRJNA605581" in text
        assert "10.5061/dryad.7p2cv" not in text
        assert "10.5281/zenodo.5713397" in text


def test_target_comparison_boundary_is_explicit():
    for path in DRAFTS:
        text = path.read_text(encoding="utf-8")
        assert (
            "not as a formal test that two target-specific partial-R² parameters are equal"
            in text
        )
        assert "The present archive has a hard mechanistic ceiling" in text
        assert "The main result is therefore structural rather than mechanistic" in text


def test_submission_checklist_uses_correct_source_archives():
    text = (HISTORY / "ECOLOGY_LETTERS_SUBMISSION_CHECKLIST_V1.md").read_text(
        encoding="utf-8"
    )
    assert "10.5281/zenodo.3872145" in text
    assert "PRJNA605581" in text
    assert "10.5061/dryad.7p2cv" not in text
    assert "10.5281/zenodo.5713397" in text


def test_source_metadata_correction_is_explicit_and_non_mutating():
    correction = (
        ROOT
        / "validation/eog_original_idea_leopold_history_retention_v28"
        / "source_metadata_correction_v1.json"
    ).read_text(encoding="utf-8")
    assert '"frozen_value": "10.5061/dryad.7p2cv"' in correction
    assert '"zenodo_archive_doi": "10.5281/zenodo.3872145"' in correction
    assert '"raw_reads_bioproject": "PRJNA605581"' in correction
    assert '"scoring_impact": "none"' in correction
