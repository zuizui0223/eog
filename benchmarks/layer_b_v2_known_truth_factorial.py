"""Deterministic known-truth benchmark for Layer-B v2 representation contracts.

Run from repository root:

    python benchmarks/layer_b_v2_known_truth_factorial.py

The benchmark is response-independent.  It validates predeclared representation
properties only; it does not evaluate ecological predictive superiority.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from eog.v2.predictive_state_gate import (
    PredictiveStateDesign,
    audit_predictive_state_refresh,
    evaluate_predictive_state_design,
)
from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support
from eog.v2.worldset_contraction_audit import audit_worldset_contraction


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "build" / "layer_b_v2_known_truth_factorial.json"


def run_benchmark() -> dict[str, object]:
    designs = {
        "tampa_like": PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="leave_node_out_static",
            serve_generator_id="common_fold_static",
            refresh_policy="static_reused",
            source_policy="lexicographic_single_source",
            source_label_invariant=False,
            baseline_contains_spatial_coordinates=True,
        ),
        "matched_static": PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="static_node",
            serve_generator_id="static_node",
            refresh_policy="static_reused",
            source_policy="symmetric_sources",
            source_label_invariant=True,
        ),
        "matched_sequential": PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="sequential_preoutcome",
            serve_generator_id="sequential_preoutcome",
            refresh_policy="sequential_context",
            source_policy="symmetric_sources",
            source_label_invariant=True,
            baseline_contains_spatial_coordinates=True,
        ),
        "dynamic_label_dependent_source": PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="sequential_preoutcome",
            serve_generator_id="sequential_preoutcome",
            refresh_policy="sequential_context",
            source_policy="lexicographic_single_source",
            source_label_invariant=False,
        ),
    }
    eligibility = {
        name: evaluate_predictive_state_design(design) for name, design in designs.items()
    }

    static_features = np.asarray(
        [
            [0.2, 0.8],
            [0.2, 0.8],
            [0.2, 0.8],
            [0.7, 0.1],
            [0.7, 0.1],
            [0.7, 0.1],
        ],
        dtype=float,
    )
    sequential_features = np.asarray(
        [
            [0.2, 0.8],
            [0.3, 0.7],
            [0.4, 0.6],
            [0.7, 0.1],
            [0.6, 0.2],
            [0.5, 0.3],
        ],
        dtype=float,
    )
    entity_ids = ["a", "a", "a", "b", "b", "b"]
    refresh = {
        "static": audit_predictive_state_refresh(static_features, entity_ids),
        "sequential": audit_predictive_state_refresh(sequential_features, entity_ids),
    }

    source_support = np.asarray(
        [
            [[1.0, 0.2, 0.0], [1.0, 0.8, 0.0]],
            [[0.0, 0.6, 1.0], [0.0, 0.4, 1.0]],
        ],
        dtype=float,
    )
    source_original = summarize_source_symmetric_support(
        source_support,
        source_ids=("source_a", "source_b"),
        world_ids=("world_1", "world_2"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    source_reordered_renamed = summarize_source_symmetric_support(
        source_support[::-1, ::-1, :],
        source_ids=("banana", "saffron"),
        world_ids=("renamed_2", "renamed_1"),
        node_ids=("a", "b", "c"),
        declared_world_count=2,
    )
    source_invariance = {
        "feature_matrix_equal": bool(
            np.array_equal(
                source_original.feature_matrix, source_reordered_renamed.feature_matrix
            )
        ),
        "feature_fingerprint_equal": (
            source_original.feature_fingerprint
            == source_reordered_renamed.feature_fingerprint
        ),
        "latent_state_fingerprint_equal": (
            source_original.latent_state_fingerprint
            == source_reordered_renamed.latent_state_fingerprint
        ),
    }

    worldsets = {
        "saturated": audit_worldset_contraction(5, [5, 5, 5, 5]),
        "contracting": audit_worldset_contraction(5, [5, 5, 4, 2]),
        "falsified": audit_worldset_contraction(5, [5, 4, 2, 0]),
    }

    # Contract assertions are deliberately representation-level, not score-level.
    assert eligibility["tampa_like"].status == "ineligible_generation_shift"
    assert eligibility["matched_static"].status == "structural_only_static_reuse"
    assert eligibility["matched_sequential"].status == "predictive_complement_candidate"
    assert eligibility["dynamic_label_dependent_source"].status == "ineligible_source_label_dependence"
    assert refresh["static"].refresh_fraction == 0.0
    assert refresh["sequential"].refresh_fraction == 1.0
    assert source_invariance["feature_matrix_equal"] is True
    assert source_invariance["feature_fingerprint_equal"] is True
    assert source_invariance["latent_state_fingerprint_equal"] is False
    assert worldsets["saturated"].fully_saturated_context_fraction == 1.0
    assert worldsets["saturated"].contraction_event_count == 0
    assert worldsets["contracting"].contraction_event_count == 2
    assert worldsets["falsified"].terminal_universe_falsified is True

    result = {
        "schema": "eog.layer_b_mechanism_v2.known_truth_factorial_result.v1",
        "counts_as_fresh_predictive_endpoint": False,
        "uses_biological_response": False,
        "eligibility": {
            name: {
                "status": value.status,
                "predictive_use_allowed": value.predictive_use_allowed,
                "generator_parity": value.generator_parity,
                "repeated_static_reuse": value.repeated_static_reuse,
                "source_label_invariant": value.source_label_invariant,
                "reasons": list(value.reasons),
                "warnings": list(value.warnings),
                "fingerprint": value.fingerprint,
            }
            for name, value in eligibility.items()
        },
        "refresh": {
            name: {
                "constant_repeated_entity_fraction": value.constant_repeated_entity_fraction,
                "refresh_fraction": value.refresh_fraction,
                "exact_unique_state_count": value.exact_unique_state_count,
                "fingerprint": value.fingerprint,
            }
            for name, value in refresh.items()
        },
        "source_symmetric_invariance": source_invariance,
        "worldsets": {
            name: {
                "surviving_world_counts": list(value.surviving_world_counts),
                "contraction_event_count": value.contraction_event_count,
                "fully_saturated_context_fraction": value.fully_saturated_context_fraction,
                "terminal_universe_falsified": value.terminal_universe_falsified,
                "fingerprint": value.fingerprint,
            }
            for name, value in worldsets.items()
        },
        "interpretation": "The frozen v2 safeguards distinguish generator shift, static repeated-state reuse, source-label dependence, context refresh, and world-set saturation without using biological outcomes. No predictive-benefit claim is tested here.",
    }
    return result


def main(output_path: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    result = run_benchmark()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
