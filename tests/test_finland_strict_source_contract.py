import hashlib
import json
from pathlib import Path

from benchmarks import finland_strict_source_prepare as strict


LIST_PATH = Path("benchmarks/frozen/finland_strict_source_cohort/exact_complement_species.txt")
SUMMARY_PATH = Path("benchmarks/frozen/finland_strict_source_cohort/response_free_summary.json")
EXPECTED_SHA = "e218f94e5facd4ed330a80b0fead0012b31fd5cb7b7b026f2ee0ff326277b2bc"
ZERO_SOURCE_EXACT = {
    "Epilobium adenocaulon",
    "Epilobium ciliatum",
    "Galium album",
    "Senecio viscosus",
}


def test_strict_cohort_excludes_zero_source_exact_complements_before_outcome_access():
    species = LIST_PATH.read_text(encoding="utf-8").splitlines()
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    assert len(species) == len(set(species)) == 180
    assert ZERO_SOURCE_EXACT.isdisjoint(species)
    assert hashlib.sha256(LIST_PATH.read_bytes()).hexdigest() == EXPECTED_SHA
    assert summary["outcome_values_accessed"] is False
    assert summary["n_exact_complement_species"] == 184
    assert summary["n_zero_source_exact_complement_species"] == 4
    assert summary["n_strict_sourceful_exact_complement_species"] == 180
    assert set(summary["zero_source_exact_complement_species"]) == ZERO_SOURCE_EXACT
    assert strict.EXPECTED_STRICT_SPECIES == 180
    assert strict.EXPECTED_STRICT_LIST_SHA256 == EXPECTED_SHA
