from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRATEGY = ROOT / "manuscript/submission/novelty_submission_strategy_2026-08-12.md"
ADDITIONS = ROOT / "manuscript/submission/closest_prior_reference_additions.md"
CHECKLIST = ROOT / "manuscript/structural_submission_checklist.md"
GATE = ROOT / "manuscript/submission/closest_prior_revision_gate.json"
ISLAND_CONTRACT = ROOT / "validation/aislands_isolation_adequacy_20260812/preoutcome_contract.json"
OUTCOME = ROOT / "validation/aislands_isolation_adequacy_20260812/authoritative_outcome.json"


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
    assert "authorized exactly once" in text.lower()
    assert "C − R3" in text


def test_closest_prior_audit_covers_general_and_island_method_families() -> None:
    text = ADDITIONS.read_text(encoding="utf-8")
    required_dois = (
        "10.1890/08-1524.1",
        "10.1016/j.ecolmodel.2011.02.011",
        "10.1007/s10531-011-0049-5",
        "10.1371/journal.pone.0072200",
        "10.1002/ece3.5567",
        "10.1111/1365-2664.14118",
        "10.1371/journal.pone.0293966",
        "10.1002/ecy.4105",
        "10.1111/1365-2745.14403",
        "10.1016/j.ecoinf.2024.102464",
        "10.1111/2041-210X.14444",
        "10.1016/j.scitotenv.2024.178204",
        "10.1016/j.ecoinf.2026.103740",
        "10.1890/08-1337.1",
        "10.1111/j.1600-0587.2012.07669.x",
        "10.1093/biolinnean/bly033",
        "10.1111/jbi.13778",
        "10.1111/cobi.14047",
    )
    for doi in required_dois:
        assert doi in text
    for concept in (
        "nearest occupied",
        "source patches",
        "source quality",
        "inverse suitability",
        "network topology",
        "dispersal thresholds",
        "uncertainty",
        "stepping-stone isolation",
        "surrounding land-area",
        "insular network position",
        "independent presence–absence and genetic data sets",
    ):
        assert concept.lower() in text.lower()


def test_machine_gate_was_frozen_before_the_single_island_execution() -> None:
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    island = json.loads(ISLAND_CONTRACT.read_text(encoding="utf-8"))
    outcome = json.loads(OUTCOME.read_text(encoding="utf-8"))
    assert gate["schema_version"] == "eog_structural_closest_prior_gate_v2"
    assert gate["original_frozen_outcomes_reopen_allowed"] is False
    assert gate["new_outcome_analysis_required"] is True
    assert gate["authorized_new_outcome_analysis"] == "aislands_isolation_adequacy_v1_3_exactly_once"
    assert island["schema_version"] == "eog_aislands_isolation_adequacy_v1_3"
    assert island["reference_design_status"] == "final_before_extension_species_outcomes"
    assert island["outcomes_inspected_for_this_extension"] is False
    assert gate["island_extension_preoutcome_fingerprints"]["species_outcomes_used_when_frozen"] is False
    assert gate["island_extension_preoutcome_fingerprints"]["area_table_sha256"] == "496789783a98e55e1b9552f6f6d28e7b4567ef0f52c795657c7e2fea9c60aae2"
    assert gate["island_extension_preoutcome_fingerprints"]["mainland_distance_table_sha256"] == "7d6f52f03702dd0cfae061023a1b2f405e39397de73eaad21b97d24176c4f869"
    assert outcome["result_fingerprint"] == "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"


def test_submission_checklist_records_completed_execution_and_remaining_incorporation_gate() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")
    assert "Island-isolation adequacy extension executed exactly once" in text
    assert "Island extension result incorporated into manuscript prose, figures, tables and cover letter without weakening R3" in text
    assert "Verified closest-prior additions ledger expanded" in text
    assert re.search(r"- \[x\] \*\*Island-isolation adequacy extension executed exactly once", text)
    assert re.search(r"- \[ \] \*\*Island extension result incorporated into manuscript prose, figures, tables and cover letter without weakening R3", text)


def test_predeclared_result_dependent_journal_strategy_is_explicit() -> None:
    text = STRATEGY.read_text(encoding="utf-8")
    assert "Route A — robust residual island increment: *Journal of Biogeography* first" in text
    assert "Route B — no residual island increment: *Ecological Informatics* first" in text
    assert "*Methods in Ecology and Evolution*: NO-GO for this empirical paper" in text
    assert "*Ecological Modelling*: conditional backup" in text
    assert "HOLD manuscript release, DOI reservation and journal submission" in text
