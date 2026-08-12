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
    for stale in (
        "Report the proportion of species",
        "Discuss only as hypotheses",
        "The manuscript should state plainly",
        "## 6. Figure plan",
        "## 8. Evidence map",
    ):
        assert stale not in text


def test_results_and_discussion_are_full_prose_and_keep_both_aislands_endpoints() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    results = section(text, "3. Results", "4. Discussion")
    discussion = section(text, "4. Discussion", "5. Conclusions")
    assert 900 <= words(results) <= 2000
    assert 1500 <= words(discussion) <= 3400
    for token in (
        "672 had concordance above 0.5",
        "42 equalled 0.5",
        "131 were below 0.5",
        "886",
        "4,231",
        "712,515",
        "+0.0034852",
        "341",
        "545",
        "Seventeen species",
        "43 had a positive difference",
        "66 single-class training cases",
        "56 folds",
        "0.0306296",
        "0.0109538",
        "0.0057016",
    ):
        assert token in results
    for token in (
        "Reference content and endpoint are part of the estimand",
        "declared reference",
        "original A-Islands result remains valid within its frozen estimand",
        "causally explains the original concordance",
        "one-time execution",
        "should not be added now to rescue the adverse island result",
    ):
        assert token.lower() in discussion.lower()


def test_primary_and_sensitivity_values_match_frozen_table3() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    with TABLE3.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    lookup = {(row["system"], row["analysis"], row["metric"]): row for row in rows}
    narrative = {
        ("A-Islands", "Combined connected frequency", "conditional concordance"): (
            "0.6177466", "0.6086806", "0.6269445"
        ),
        ("A-Islands", "Prospective strong island reference | C vs R3", "log loss difference"): (
            "0.0034852", "0.0024664", "0.0045082"
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
            assert abs(float(rendered) - float(row[field])) <= 5.1e-7
            assert rendered in text or rendered.replace("-", "−") in text


def test_applicability_failure_accounting_is_retained() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    with TABLE_S1.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    expected_counts = {
        ("A-Islands", "bottleneck_secondary", "evaluable"): "2,591",
        ("A-Islands", "bottleneck_secondary", "no_finite_comparable_pairs_within_frozen_strata"): "1,640",
        ("A-Islands", "primary_combined", "evaluable"): "3,041",
        ("A-Islands", "primary_combined", "no_comparable_pairs_within_frozen_strata"): "1,190",
        ("A-Islands", "isolation_adequacy_C_vs_R3", "evaluable_folds"): "4,231",
        ("A-Islands", "isolation_adequacy_C_vs_R3", "insufficient_training_class_count_5_5"): "199",
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
        "R3 causally explains the original A-Islands conditional-concordance signal",
    ):
        assert prohibited not in text
    for required in (
        "not a colonisation or dispersal probability",
        "not as confirmation of the adverse primary LOSO effect",
        "cannot be interpreted as realised movement",
        "does not by itself imply improved probability prediction",
        "cannot be used to claim that EOG captures a generally predictive",
        "not a controlled one-factor ablation",
    ):
        assert required.lower() in text.lower()
