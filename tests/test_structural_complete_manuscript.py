from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "structural_reachability_manuscript.md"
TABLE3 = ROOT / "manuscript" / "result_tables" / "table_3_main_sensitivity_results.csv"
TABLE_S1 = ROOT / "manuscript" / "result_tables" / "table_s1_applicability_accounting.csv"


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


def test_complete_manuscript_has_submission_sections_and_no_scaffold_notes() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    for heading in (
        "## Abstract",
        "## 1. Introduction",
        "## 2. Methods",
        "## 3. Results",
        "## 4. Discussion",
        "## 5. Conclusions",
        "## References",
    ):
        assert heading in text
    assert "Report the proportion of species" not in text
    assert "Discuss only as hypotheses" not in text
    assert "The manuscript should state plainly" not in text
    assert "## 6. Figure plan" not in text
    assert "## 8. Evidence map" not in text


def test_results_and_discussion_are_full_prose() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    results = section(text, "3. Results", "4. Discussion")
    discussion = section(text, "4. Discussion", "5. Conclusions")
    assert 900 <= words(results) <= 1800
    assert 1500 <= words(discussion) <= 3200
    for token in (
        "672 had concordance above 0.5",
        "42 equalled 0.5",
        "131 were below 0.5",
        "Seventeen species",
        "43 had a positive difference",
        "66 single-class training cases",
        "56 folds",
        "0.0306296",
        "0.0109538",
        "0.0057016",
    ):
        assert token in results
    assert "reference model" in discussion
    assert "prospective tests" in discussion.lower()
    assert "post-outcome trait-specific radii" in discussion


def test_primary_and_sensitivity_values_match_frozen_table3() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    with TABLE3.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    lookup = {(row["system"], row["analysis"], row["metric"]): row for row in rows}
    narrative = {
        ("A-Islands", "Combined connected frequency", "conditional concordance"): (
            "0.6177466", "0.6086806", "0.6269445"
        ),
        ("Tanzania", "Primary weighting | LOSO", "log loss difference"): (
            "0.0321131", "0.0174580", "0.0486750"
        ),
        ("Tanzania", "Inverse-area weighting | LOSO", "log loss difference"): (
            "0.0306296", "0.0162138", "0.0469375"
        ),
        ("Tanzania", "Primary weighting | spatial MST blocks", "log loss difference"): (
            "0.0109538", "-0.0121714", "0.0334313"
        ),
        ("Tanzania", "Inverse-area weighting | spatial MST blocks", "log loss difference"): (
            "0.0057016", "-0.0155325", "0.0258239"
        ),
    }
    for key, rendered_values in narrative.items():
        row = lookup[key]
        for field, rendered in zip(("effect", "ci_low", "ci_high"), rendered_values):
            # Table 3 is a six-decimal display projection; the manuscript retains
            # more digits from the same frozen result. They must agree to rounding.
            assert abs(float(rendered) - float(row[field])) <= 5.1e-7
            assert rendered in text


def test_applicability_failure_accounting_is_retained() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    with TABLE_S1.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    expected_counts = {
        ("A-Islands", "bottleneck_secondary", "evaluable"): "2,591",
        ("A-Islands", "bottleneck_secondary", "no_finite_comparable_pairs_within_frozen_strata"): "1,640",
        ("A-Islands", "primary_combined", "evaluable"): "3,041",
        ("A-Islands", "primary_combined", "no_comparable_pairs_within_frozen_strata"): "1,190",
        ("Tanzania", "primary::primary_loso", "matched"): "826",
        ("Tanzania", "primary::spatial_mst_block", "matched"): "718",
    }
    lookup = {(r["system"], r["analysis"], r["status"]): r for r in rows}
    for key, rendered in expected_counts.items():
        assert int(lookup[key]["count"]) == int(rendered.replace(",", ""))
        assert rendered in text


def test_claim_boundary_survives_complete_manuscript() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    for prohibited in (
        "EOG outperforms SDM",
        "connected frequency estimates colonisation probability",
        "Tanzania shows current flow is better in general",
    ):
        assert prohibited not in text
    for required in (
        "not a colonisation or dispersal probability",
        "not as confirmation of the adverse primary LOSO effect",
        "does not establish a historical colonisation route",
        "not estimates of realised dispersal or colonisation probability",
    ):
        assert required.lower() in text.lower()
