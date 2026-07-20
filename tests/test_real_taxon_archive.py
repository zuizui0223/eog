import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "benchmarks" / "expected" / "real_taxon_mode_summary.csv"
DECISION = ROOT / "benchmarks" / "expected" / "real_taxon_mode_decision.json"


def test_real_taxon_archive_completion_gate() -> None:
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    assert decision == {
        "declared_pairs": 6,
        "status_rows": 6,
        "eligible_pairs": 6,
        "failed_pairs": 0,
        "ineligible_pairs": 0,
        "eligible_with_stability": 6,
        "passes_completion_gate": True,
    }


def test_real_taxon_archive_has_declared_taxa_and_diagnostic_disagreement() -> None:
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    assert len(rows) == 6
    by_name = {row["scientific_name"]: row for row in rows}
    assert set(by_name) == {
        "Fagus sylvatica",
        "Quercus robur",
        "Pinus sylvestris",
        "Bombus terrestris",
        "Vanessa atalanta",
        "Vulpes vulpes",
    }
    assert all(row["status"] == "eligible" for row in rows)
    assert all(int(row["complete_chelsa_count"]) == 240 for row in rows)
    assert by_name["Quercus robur"]["within_cohort_agreement_class"] == "bridge_high_silhouette_low"
    assert by_name["Bombus terrestris"]["within_cohort_agreement_class"] == "silhouette_high_bridge_low"
    assert by_name["Vulpes vulpes"]["within_cohort_agreement_class"] == "both_high"


def test_real_taxon_archive_preserves_metric_specific_interpretation() -> None:
    rows = list(csv.DictReader(SUMMARY.open(encoding="utf-8")))
    by_name = {row["scientific_name"]: row for row in rows}
    assert float(by_name["Bombus terrestris"]["kmeans_silhouette"]) > float(
        by_name["Quercus robur"]["kmeans_silhouette"]
    )
    assert float(by_name["Quercus robur"]["core_bridge_score"]) > float(
        by_name["Bombus terrestris"]["core_bridge_score"]
    )
