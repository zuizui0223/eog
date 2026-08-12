from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATEGY = ROOT / "manuscript/submission/novelty_submission_strategy_2026-08-12.md"
ADDITIONS = ROOT / "manuscript/submission/closest_prior_reference_additions.md"
CHECKLIST = ROOT / "manuscript/structural_submission_checklist.md"


def test_novelty_strategy_preserves_frozen_empirical_boundary() -> None:
    text = STRATEGY.read_text(encoding="utf-8")
    for token in (
        "0.6177466",
        "0.6086806–0.6269445",
        "672/845",
        "+0.0321131",
        "+0.0174580 to +0.0486750",
        "17 species favourable to EOG and 43 adverse",
        "spatial-block sensitivity is smaller and uncertain",
    ):
        assert token in text
    assert "Do not reopen the frozen outcome analyses" in text


def test_closest_prior_audit_covers_required_method_families() -> None:
    text = ADDITIONS.read_text(encoding="utf-8")
    required_dois = (
        "10.1016/j.ecolmodel.2011.02.011",
        "10.1371/journal.pone.0072200",
        "10.1371/journal.pone.0293966",
        "10.1002/ecy.4105",
        "10.1111/1365-2745.14403",
        "10.1016/j.ecoinf.2024.102464",
        "10.1111/2041-210X.14444",
        "10.1016/j.scitotenv.2024.178204",
        "10.1016/j.ecoinf.2026.103740",
    )
    for doi in required_dois:
        assert doi in text
    for concept in (
        "accessible",
        "nearest occupied patch",
        "network topology",
        "dispersal thresholds",
        "environmental-space suitability",
        "patch area/configuration/diversity",
        "incidence-function/species-distribution",
        "uncertainty",
        "source points",
    ):
        assert concept.lower() in text.lower()


def test_submission_is_blocked_until_closest_prior_revision_is_merged() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "Closest-prior framing revision merged before release" in text
    assert "Verified-reference ledger expanded" in text
    for overclaim in (
        "EOG is the first framework to integrate suitability and connectivity",
        "occurrence anchoring is novel",
        "scenario sensitivity or connectivity uncertainty analysis is novel",
    ):
        assert overclaim in text
    assert re.search(r"- \[ \] \*\*Closest-prior framing revision merged before release", text)


def test_journal_strategy_is_explicit() -> None:
    text = STRATEGY.read_text(encoding="utf-8")
    assert "First target — *Ecological Informatics*: GO" in text
    assert "*Methods in Ecology and Evolution*: NO-GO for the current version" in text
    assert "Backup — *Ecological Modelling*: CONDITIONAL" in text
    assert "workflow composed of existing tools" in text
