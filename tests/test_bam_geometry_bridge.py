"""Contract tests for the experimental BAM/geometry adapter.

These do not score ecological predictive endpoints or change frozen BAM results.
"""
from dataclasses import replace

import numpy as np
import pytest

from eog.bam_geometry import profile_bam_geometry, profile_known_truth_bam_world
from eog.comparative import fit_robust_reference
from eog.reference_policy import ReferenceDeclaration
from eog.v2.known_truth_bam import (
    build_bam_world,
    generate_biotic_state,
    make_bam_landscape,
)


def _reference(values):
    ref = fit_robust_reference(values, provenance="frozen full virtual landscape")
    policy = ReferenceDeclaration(
        mode="pooled-descriptive",
        intent="retrospective",
        source_description="full synthetic node environment (includes compared masks)",
        fitted_before_evaluation=False,
        includes_evaluation_groups=True,
        outcome_informed=False,
    )
    return ref, policy


def _bool_indices(n, indices):
    return np.array([i in indices for i in range(n)], dtype=bool)


def test_eight_constraint_subsets_and_fingerprint_are_reproducible():
    x = np.array([[0.0], [0.1], [0.2], [0.3], [2.0], [2.1], [2.2], [3.0]])
    reference, policy = _reference(x)
    a = _bool_indices(8, {0, 1, 2, 3, 4, 5})
    b = _bool_indices(8, {0, 1, 2, 4, 6, 7})
    m = np.ones(8, dtype=bool)
    p = dict(A=a, B=b, M=m, reference=reference, declaration=policy, n_draws=24)
    first = profile_bam_geometry(x, **p)
    second = profile_bam_geometry(x, **p)
    assert first == second
    assert len(first["fingerprint"]) == 64
    assert list(first["groups"]) == ["U", "A", "B", "M", "AB", "AM", "BM", "ABM"]
    assert first["groups"]["ABM"]["n_nodes"] == 4
    assert first["groups"]["ABM"]["matched"]["sample_size"] == 4
    assert first["groups"]["ABM"]["full"]["span"] > 0
    assert first["groups"]["U"]["matched"]["n_draws"] == 24
    assert first["contrasts"]["ABM_vs_U_matched_log_span_ratio"] is not None


def test_same_G_distinct_BAM_states_are_not_identified_by_geometry():
    x = np.arange(8.0).reshape(-1, 1)
    ref, policy = _reference(x)
    common = dict(reference=ref, declaration=policy, n_draws=20, seed=11)
    one = profile_bam_geometry(
        x,
        A=_bool_indices(8, {0, 1, 2, 3, 4, 5}),
        B=_bool_indices(8, {0, 1, 2, 4, 6, 7}),
        M=np.ones(8, dtype=bool),
        **common,
    )
    two = profile_bam_geometry(
        x,
        A=np.ones(8, dtype=bool),
        B=_bool_indices(8, {0, 1, 2, 4}),
        M=_bool_indices(8, {0, 1, 2, 3, 4, 5}),
        **common,
    )
    assert one["mask_sha256"]["ABM"] == two["mask_sha256"]["ABM"]
    assert one["groups"]["ABM"] == two["groups"]["ABM"]
    assert one["groups"]["A"] != two["groups"]["A"]
    assert one["groups"]["B"] != two["groups"]["B"]
    assert one["fingerprint"] != two["fingerprint"]


def test_small_or_empty_G_is_not_silently_reported_as_zero_extent():
    x = np.arange(6.0).reshape(-1, 1)
    ref, policy = _reference(x)
    report = profile_bam_geometry(
        x,
        A=_bool_indices(6, {0, 1, 2}),
        B=_bool_indices(6, {2, 3, 4}),
        M=_bool_indices(6, {2, 4, 5}),
        reference=ref, declaration=policy,
    )
    assert report["groups"]["ABM"]["n_nodes"] == 1
    assert report["groups"]["ABM"]["full"] is None
    assert report["groups"]["ABM"]["full_status"] == "not_estimable_lt2"
    assert report["groups"]["U"]["full"] is not None
    assert report["groups"]["U"]["matched"] is None
    assert report["contrasts"]["ABM_vs_A_matched_log_span_ratio"] is None


def test_bad_masks_and_reference_policy_fail_closed():
    x = np.arange(6.0).reshape(-1, 1)
    ref, policy = _reference(x)
    good = np.ones(6, dtype=bool)
    with pytest.raises(ValueError, match="boolean mask"):
        profile_bam_geometry(
            x, A=np.ones(6, dtype=int), B=good, M=good,
            reference=ref, declaration=policy,
        )
    with pytest.raises(ValueError, match="reference"):
        profile_bam_geometry(
            np.ones((6, 2)), A=good, B=good, M=good,
            reference=ref, declaration=policy,
        )
    with pytest.raises(ValueError, match="n_draws"):
        profile_bam_geometry(
            x, A=good, B=good, M=good, reference=ref,
            declaration=policy, n_draws=0,
        )
    forbidden = replace(policy, outcome_informed=True)
    with pytest.raises(ValueError, match="outcome-informed"):
        profile_bam_geometry(
            x, A=good, B=good, M=good, reference=ref,
            declaration=forbidden,
        )


def test_known_truth_bam_adapter_preserves_original_mask_contract():
    landscape = make_bam_landscape()
    biotic = generate_biotic_state(landscape)
    world = build_bam_world(
        landscape,
        world_id="synthetic_world",
        abiotic_label="wide",
        niche_center=(0.55, 0.55),
        niche_radius=(0.8, 0.8),
        biotic_state=biotic,
        biotic_mode="none",
        movement_label="long_open",
        source_id="r1c0",
        step_radius=1.01,
        barrier_permeable=True,
        horizon=10,
    )
    x = np.asarray(landscape.environment, dtype=float)
    ref, policy = _reference(x)
    report = profile_known_truth_bam_world(
        world, x, reference=ref, declaration=policy, n_draws=8,
    )
    assert report["groups"]["ABM"]["n_nodes"] == world.occupied_mask.bit_count()
    assert report["groups"]["A"]["n_nodes"] == world.abiotic_mask.bit_count()
    assert report["source_world_fingerprint"] == world.fingerprint
    assert report["groups"]["ABM"]["n_nodes"] >= 2

    with pytest.raises(ValueError, match="not A & B & M"):
        profile_known_truth_bam_world(
            replace(world, occupied_mask=0),
            x, reference=ref, declaration=policy,
        )
    with pytest.raises(ValueError, match="within node universe"):
        profile_known_truth_bam_world(
            replace(world, movement_mask=1 << len(world.node_ids)),
            x, reference=ref, declaration=policy,
        )

def test_canonical_demo_runner_produces_valid_noncausal_receipt():
    import json
    from pathlib import Path
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[1] / "benchmarks/run_bam_geometry_bridge_v0.py"
    payload = json.loads(subprocess.check_output([sys.executable, str(script)], text=True))
    assert payload["n_synthetic_nodes"] == 21
    assert payload["n_features"] == 2
    worlds = payload["worlds"]
    assert len(worlds) == 3
    assert worlds[1]["node_counts"]["ABM"] <= worlds[0]["node_counts"]["ABM"]
    assert worlds[2]["node_counts"]["ABM"] <= worlds[0]["node_counts"]["ABM"]
    assert all(len(row["geometry_fingerprint"]) == 64 for row in worlds)
    assert "no causal attribution" in payload["interpretation_limit"]
