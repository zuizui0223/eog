import runpy
import sys
from pathlib import Path


BENCHMARK_DIR = str(Path("benchmarks").resolve())
if BENCHMARK_DIR not in sys.path:
    sys.path.insert(0, BENCHMARK_DIR)

_NAMESPACE = runpy.run_path("benchmarks/run_aislands_worldset_exploratory.py")
_training_anchor_ids = _NAMESPACE["_training_anchor_ids"]
OUTPUT_FIELDS = _NAMESPACE["OUTPUT_FIELDS"]


def test_heldout_presence_perturbation_cannot_change_training_anchor_ids():
    fold_by_island = {
        "A": 1,
        "B": 2,
        "C": 2,
        "D": 1,
    }
    with_heldout_presence = {"A", "B", "C"}
    without_heldout_presence = {"B", "C"}

    first = _training_anchor_ids(with_heldout_presence, fold_by_island, 1)
    second = _training_anchor_ids(without_heldout_presence, fold_by_island, 1)

    assert first == {"B", "C"}
    assert second == {"B", "C"}
    assert first == second


def test_exploratory_output_schema_contains_no_response_or_accuracy_columns():
    forbidden = {
        "heldout_presence",
        "heldout_absence",
        "response",
        "label",
        "auc",
        "concordance",
        "support_score",
        "pointwise_support",
    }
    assert forbidden.isdisjoint(OUTPUT_FIELDS)
    assert "supporting_world_ids" in OUTPUT_FIELDS
    assert "unsupported_world_ids" in OUTPUT_FIELDS
    assert "world_class" in OUTPUT_FIELDS
    assert "geo_environment_class_disagreement" in OUTPUT_FIELDS


def test_exploratory_schema_keeps_world_identity_not_only_frequency():
    assert "connected_frequency" in OUTPUT_FIELDS
    assert "support_count" in OUTPUT_FIELDS
    assert "world_count" in OUTPUT_FIELDS
    assert "supporting_world_ids" in OUTPUT_FIELDS
    assert "unsupported_world_ids" in OUTPUT_FIELDS
