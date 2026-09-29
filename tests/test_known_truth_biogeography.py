import json
from pathlib import Path

from eog.v2.known_truth_biogeography import (
    VirtualProcess,
    build_virtual_world,
    make_gradient_landscape,
    positive_witness_set,
    run_canonical_known_truth_benchmark,
    simulate_true_positive_state,
)


def test_virtual_process_generates_niche_and_process_conditioned_reachability():
    landscape = make_gradient_landscape()
    open_process = VirtualProcess(
        world_id="open",
        source_id="r1c0",
        niche_center=(0.65, 0.5),
        niche_radius=(1.5, 1.5),
        dispersal_radius=1.01,
        environmental_transition_limit=1.0,
        barrier_permeable=True,
        max_steps=8,
    )
    blocked_process = VirtualProcess(
        world_id="blocked",
        source_id="r1c0",
        niche_center=(0.65, 0.5),
        niche_radius=(1.5, 1.5),
        dispersal_radius=1.01,
        environmental_transition_limit=0.25,
        barrier_permeable=True,
        max_steps=8,
    )

    open_state = set(simulate_true_positive_state(landscape, open_process))
    blocked_state = set(simulate_true_positive_state(landscape, blocked_process))

    assert "r1c6" in open_state
    assert "r1c6" not in blocked_state
    assert blocked_state < open_state


def test_positive_witnesses_are_true_occurrences_and_eliminate_distinguishable_false_worlds():
    landscape = make_gradient_landscape()
    truth_process = VirtualProcess(
        world_id="truth",
        source_id="r1c0",
        niche_center=(0.65, 0.5),
        niche_radius=(1.5, 1.5),
        dispersal_radius=1.01,
        environmental_transition_limit=1.0,
        barrier_permeable=True,
        max_steps=8,
    )
    env_blocked = VirtualProcess(
        world_id="env_blocked",
        source_id=truth_process.source_id,
        niche_center=truth_process.niche_center,
        niche_radius=truth_process.niche_radius,
        dispersal_radius=truth_process.dispersal_radius,
        environmental_transition_limit=0.25,
        barrier_permeable=True,
        max_steps=truth_process.max_steps,
    )
    barrier_blocked = VirtualProcess(
        world_id="barrier_blocked",
        source_id=truth_process.source_id,
        niche_center=truth_process.niche_center,
        niche_radius=truth_process.niche_radius,
        dispersal_radius=truth_process.dispersal_radius,
        environmental_transition_limit=truth_process.environmental_transition_limit,
        barrier_permeable=False,
        max_steps=truth_process.max_steps,
    )
    truth = build_virtual_world(landscape, truth_process)
    false_worlds = (
        build_virtual_world(landscape, env_blocked),
        build_virtual_world(landscape, barrier_blocked),
    )

    witnesses = positive_witness_set(
        truth,
        false_worlds,
        max_steps=truth_process.max_steps,
    )
    truth_state = set(simulate_true_positive_state(landscape, truth_process))

    assert witnesses
    assert set(witnesses) <= truth_state


def test_frozen_canonical_known_truth_hypotheses_have_explicit_verdicts():
    result = run_canonical_known_truth_benchmark()

    assert result["verdicts"] == {
        "H1_truth_retention": "SUPPORTED",
        "H2_discriminating_contraction": "SUPPORTED",
        "H3_omitted_truth_falsification": "SUPPORTED",
        "H4_nonidentification_honesty": "SUPPORTED",
        "H5_observation_error_boundary": "BOUNDARY_CONFIRMED",
    }
    assert result["h1_prefix_count"] > 0
    assert result["h2_compatible_world_ids"] == ["truth_open"]
    assert result["h3_compatible_world_ids"] == []
    assert set(result["h4_compatible_world_ids"]) == {"short_step", "long_step"}
    assert result["h5_compatible_world_ids"] == []
    assert len(result["fingerprint"]) == 64


def test_protocol_was_frozen_before_benchmark_implementation():
    protocol_path = Path("validation/known_truth_biogeography_v1/protocol_v1.json")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    assert protocol["status"] == "frozen_before_benchmark_implementation"
    assert protocol["scope"]["separate_from_eog_wf"] is True
    assert protocol["scope"]["changes_closed_eog_wf_denominator"] is False
    assert protocol["reference_implementation"]["language"] == "Python"
    assert len(protocol["primary_hypotheses"]) == 4
    assert all("decision_rule" in row for row in protocol["primary_hypotheses"])
