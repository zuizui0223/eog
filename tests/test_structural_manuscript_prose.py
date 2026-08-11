from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "structural_reachability_manuscript_skeleton.md"
REFERENCE_LEDGER = ROOT / "manuscript" / "structural_verified_references.md"


def section(text: str, start: str, end: str) -> str:
    match = re.search(
        rf"^## {re.escape(start)}\s*$\n(.*?)(?=^## {re.escape(end)}\s*$)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"missing section boundary {start!r} -> {end!r}"
    return match.group(1).strip()


def words(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def test_introduction_and_methods_are_full_prose_not_scaffold_notes() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    introduction = section(text, "1. Introduction", "2. Methods")
    methods = section(text, "2. Methods", "3. Results")
    assert 800 <= words(introduction) <= 1800
    assert 1800 <= words(methods) <= 5000
    for stale in (
        "The related-work section must explicitly compare EOG with",
        "Report the complete frozen contract",
        "For both benchmarks report:",
        "Do not hide failed protocol proposals",
    ):
        assert stale not in introduction
        assert stale not in methods


def test_introduction_preserves_method_role_separation() -> None:
    text = section(MANUSCRIPT.read_text(encoding="utf-8"), "1. Introduction", "2. Methods")
    required = (
        "Valavi et al. 2019",
        "Milà et al. 2022",
        "Bakka et al. 2019",
        "Broms et al. 2016",
        "Merow et al. 2011",
        "Adriaensen et al. 2003",
        "McRae et al. 2008",
        "Ortiz-Rodríguez et al. 2019",
        "not a colonisation or dispersal probability",
        "negative incremental result",
    )
    for token in required:
        assert token in text


def test_methods_preserve_frozen_empirical_contracts() -> None:
    methods = section(MANUSCRIPT.read_text(encoding="utf-8"), "2. Methods", "3. Results")
    required = (
        "842 model-linked surveyed islands",
        "886 Australian Plant Census-native taxa",
        "BIO1",
        "BIO5",
        "BIO6",
        "BIO12",
        "BIO15",
        "25, 50, 125 and 250 km",
        "5 × 5 pointwise-support × nearest-anchor-distance strata",
        "10,000 species-cluster bootstrap replicates",
        "14-fold leave-one-fragment-out",
        "8^3=512",
        "resistance combinations",
        "0.511808",
        "0.417907",
        "candidate minus reference",
        "100,000 replicates",
        "training-only",
        "non-estimable",
    )
    for token in required:
        assert token in methods


def test_verified_reference_ledger_covers_all_current_intro_method_citations() -> None:
    ledger = REFERENCE_LEDGER.read_text(encoding="utf-8")
    dois = (
        "10.1111/2041-210X.13107",
        "10.1111/2041-210X.13851",
        "10.1016/j.spasta.2019.01.002",
        "10.1890/15-0416.1",
        "10.1086/660295",
        "10.1016/S0169-2046(02)00242-6",
        "10.1890/07-1861.1",
        "10.1002/ece3.5567",
        "10.1111/jvs.70019",
        "10.1038/sdata.2017.122",
        "10.1086/702589",
    )
    assert "Verification date: **2026-08-12**" in ledger
    for doi in dois:
        assert doi in ledger
