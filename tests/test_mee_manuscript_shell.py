from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "manuscript/paper_ready"


def test_manuscript_shell_preserves_frozen_scientific_direction() -> None:
    text = (PAPER / "manuscript_shell.md").read_text(encoding="utf-8")
    assert text.startswith("# Environmental Occupancy Geometry separates structural falsification from context-dependent predictive complementarity")
    assert "Methods in Ecology and Evolution" in text
    assert "0.1422727" in text and "0.1322871" in text
    assert "0.2463173" in text and "0.2453455" in text
    assert "0.3377354" in text and "0.4387640" in text
    assert "5/5" in text
    assert "7/8" in text
    assert "1/5" in text
    assert "31 scientific/protocol STOPs" in text
    assert "three administrative exclusions" in text
    assert "structural_diagnostic_plus_context_dependent_predictive_complement" in text
    assert "No fourth fresh endpoint is permitted" in text


def test_manuscript_does_not_reopen_forbidden_claims_or_old_structural_story() -> None:
    text = (PAPER / "manuscript_shell.md").read_text(encoding="utf-8")
    forbidden = [
        "universal predictive superiority",
        "recovering a unique dispersal history",
        "A-Islands",
        "Tanzania forest-fragment",
        "candidate general predictive complement",
    ]
    # The first two concepts may appear only as explicit non-claims.
    assert "does not support universal predictive superiority" in text or "not as a universally superior" in text
    assert "not for recovering a unique dispersal history" in text or "neither a unique dispersal history" in text
    assert "A-Islands" not in text
    assert "Tanzania forest-fragment" not in text
    assert "candidate general predictive complement" not in text


def test_prior_art_positioning_acknowledges_established_accessibility_and_connectivity() -> None:
    text = (PAPER / "manuscript_shell.md").read_text(encoding="utf-8")
    for citation in [
        "Barve et al., 2011",
        "Broms et al., 2016",
        "Merow et al., 2011",
        "McRae et al., 2008",
        "Prugh, 2009",
        "Ortiz-Rodríguez et al., 2019",
        "Van Moorter et al., 2023",
        "Prima et al., 2024",
    ]:
        assert citation in text
    assert "does not introduce accessibility" in text
    assert "The narrower contribution" in text


def test_figure_captions_match_frozen_assets_and_denominator() -> None:
    text = (PAPER / "figure_captions.md").read_text(encoding="utf-8")
    for figure in range(1, 5):
        assert f"## Figure {figure}." in text
        assert f"figure_{figure}_" in text
    assert "37 handled records" in text
    assert "three valid scored predictive endpoints and 31" in text
    assert "favorable / favorable / adverse" in text
    assert "0.1010287" in text


def test_cover_letter_is_honest_about_adverse_result_and_method_scope() -> None:
    text = (PAPER / "cover_letter_draft.md").read_text(encoding="utf-8")
    assert "Methods in Ecology and Evolution" in text
    assert "Azores yellow eel acoustic telemetry" in text
    assert "Southwest Louisiana King Rail passive acoustics" in text
    assert "Tampa Bay seagrass transect monitoring" in text
    assert "was adverse" in text
    assert "31 scientific/protocol STOPs" in text
    assert "No additional favorable endpoint will be sought" in text
    assert "does **not** claim universal predictive superiority" in text


def test_submission_readiness_keeps_external_author_metadata_and_live_rules_pending() -> None:
    text = (PAPER / "submission_readiness.md").read_text(encoding="utf-8")
    assert "## Scientific state — closed" in text
    assert "## Author-supplied metadata — pending external input" in text
    assert "These items must not be inferred from Git history." in text
    assert "Live journal requirements — not yet frozen" in text
    assert "external web lookup and container DNS were temporarily unavailable" in text
    assert "Do not search for a fourth favorable dataset." in text
