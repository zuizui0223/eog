from eog.v2.bam_counterfactual_identifiability import (
    axis_release_outcome,
    counterfactual_classes,
    exact_minimum_truth_target_measurements,
    joint_release_signature,
    release_expands_current,
    target_identified,
    truth_relative_direct_measurements,
)
from eog.v2.known_truth_bam import BAMWorld
from eog.v2.known_truth_bam_direct_evidence import bam_state_key


NODES = ("a", "b")


def _world(
    world_id,
    *,
    A,
    B,
    M,
    tau=(0, 1),
):
    mask = lambda ids: sum(1 << NODES.index(node) for node in ids)
    a = mask(A)
    b = mask(B)
    m = mask(M)
    return BAMWorld(
        world_id=world_id,
        node_ids=NODES,
        abiotic_mask=a,
        biotic_mask=b,
        movement_mask=m,
        occupied_mask=a & b & m,
        first_arrival_steps=tau,
        abiotic_label=world_id,
        biotic_mode="none",
        movement_label=world_id,
        fingerprint=world_id,
    )


def _alias_fixture():
    # All four worlds have current G={a}; their hidden limiting axes differ.
    truth = _world("truth", A={"a"}, B={"a", "b"}, M={"a", "b"})
    b_limited = _world("b_limited", A={"a", "b"}, B={"a"}, M={"a", "b"})
    m_limited = _world("m_limited", A={"a", "b"}, B={"a", "b"}, M={"a"})
    tau_alias = _world(
        "tau_alias",
        A={"a"},
        B={"a", "b"},
        M={"a", "b"},
        tau=(0, 2),
    )
    return (truth, b_limited, m_limited, tau_alias), truth


def test_same_current_distribution_can_diverge_under_axis_release():
    worlds, truth = _alias_fixture()
    assert len({world.occupied_mask for world in worlds}) == 1

    outcomes = {world.world_id: axis_release_outcome(world, "A") for world in worlds}
    assert not target_identified(tuple(outcomes), outcomes)
    assert release_expands_current(truth, "A") is True
    assert release_expands_current(next(w for w in worlds if w.world_id == "b_limited"), "A") is False


def test_mechanism_nonidentification_can_be_counterfactually_harmless():
    worlds, truth = _alias_fixture()
    tau_alias = next(world for world in worlds if world.world_id == "tau_alias")
    assert bam_state_key(truth) != bam_state_key(tau_alias)
    assert joint_release_signature(truth) == joint_release_signature(tau_alias)


def test_counterfactual_classes_are_exact_partitions():
    worlds, _ = _alias_fixture()
    ids = tuple(world.world_id for world in worlds)
    target = {world.world_id: release_expands_current(world, "A") for world in worlds}
    classes = counterfactual_classes(ids, target)
    flattened = sorted(world_id for group in classes for world_id in group)
    assert flattened == sorted(ids)
    assert len(classes) == 2


def test_truth_target_solver_matches_expected_minimum_and_target_coarsening():
    worlds, truth = _alias_fixture()
    survivors = tuple(world.world_id for world in worlds)
    measurements = truth_relative_direct_measurements(worlds, truth, survivors)

    state_target = {world.world_id: bam_state_key(world) for world in worlds}
    map_target = {world.world_id: axis_release_outcome(world, "A") for world in worlds}
    decision_target = {world.world_id: release_expands_current(world, "A") for world in worlds}

    state_plan = exact_minimum_truth_target_measurements(
        survivors, truth.world_id, state_target, measurements
    )
    map_plan = exact_minimum_truth_target_measurements(
        survivors, truth.world_id, map_target, measurements
    )
    decision_plan = exact_minimum_truth_target_measurements(
        survivors, truth.world_id, decision_target, measurements
    )

    assert state_plan.minimum_size is not None
    assert map_plan.minimum_size is not None
    assert decision_plan.minimum_size is not None
    assert decision_plan.minimum_size <= map_plan.minimum_size <= state_plan.minimum_size


def test_solver_returns_zero_when_target_already_identified():
    worlds, truth = _alias_fixture()
    harmless = (truth, next(world for world in worlds if world.world_id == "tau_alias"))
    survivors = tuple(world.world_id for world in harmless)
    measurements = truth_relative_direct_measurements(harmless, truth, survivors)
    decision_target = {
        world.world_id: release_expands_current(world, "A")
        for world in harmless
    }
    plan = exact_minimum_truth_target_measurements(
        survivors, truth.world_id, decision_target, measurements
    )
    assert plan.target_already_identified is True
    assert plan.minimum_measurement_ids == ()
    assert plan.minimum_size == 0
