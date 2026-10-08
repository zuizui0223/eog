"""Publication-facing, result-neutral checks for the inferential-openness draft."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "manuscript" / "inferential_openness" / "MANUSCRIPT_DRAFT_V2.md"
LEGENDS = ROOT / "manuscript" / "inferential_openness" / "FIGURE_LEGENDS_V1.md"


def test_all_figures_and_supplements_are_called_out_in_text():
    text = PAPER.read_text(encoding="utf-8")
    for label in (
        "(Fig. 1)", "(Fig. 2)", "(Fig. 3)", "(Fig. 4)",
        "Supplementary Fig. S1", "Supplementary Table S1",
    ):
        assert label in text
    legends = LEGENDS.read_text(encoding="utf-8")
    for heading in (
        "## Figure 1.", "## Figure 2.", "## Figure 3.",
        "## Figure 4.", "## Supplementary Figure S1.",
        "## Supplementary Table S1.",
    ):
        assert heading in legends


def test_source_ledger_and_unminted_doi_boundary_are_explicit():
    text = PAPER.read_text(encoding="utf-8")
    assert "## Data and code availability" in text
    assert "https://github.com/zuizui0223/eog" in text
    assert "https://github.com/zuizui0223/284b" in text
    assert "CROSS_PROJECT_EVIDENCE_LEDGER_V2.json" in text
    assert "will be inserted before submission" in text
    assert "Bishop et al. 2019; Bokulich & Parker 2021" in text


def test_original_workflow_scopes_remain_explicit():
    text = PAPER.read_text(encoding="utf-8")
    assert "34 scientific candidate attempts" in text
    assert "31 scientific/protocol STOPs" in text
    assert "30/31 STOPs" in text
    assert "Neither outcome is a biological negative" in text
    assert "not prevalence estimates for ecology" in text
