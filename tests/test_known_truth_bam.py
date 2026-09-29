from eog.v2.known_truth_bam import (
    BAMWorld,
    build_bam_world,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
    generate_biotic_state,
    make_bam_landscape,
)


def _manual_world(world_id, occupied_mask, arrival):
    node_ids = ("a", "b", "c")
    return BAMWorld(
        world_id=world_id,
        node_ids=node_ids,
        abiotic_mask=0b111,
        biotic_mask=0b111,
        movement_mask=0b111,
        occupied_mask=occupied_mask,
        first_arrival_steps=arrival,
        abiotic_label="manual",
        biotic_mode="none",
        movement_label="manual",
        fingerprint=world_id,
    )


def test_bam_world_keeps_A_B_M_separate_and_G_is_intersection():
    landscape = make_bam_landscape()
    state = generate_biotic_state(landscape)
    world = build_bam_world(
        landscape,
        world_id="joint",
        abiotic_label="A_narrow",
        niche_center=(0.57, 0.55),
        niche_radius=(0.42, 0.35),
        biotic_state=state,
        biotic_mode="partner_and_antagonist",
        movement_label="M_short_closed_h3",
        source_id="r1c0",
        step_radius=1.01,
        barrier_permeable=False,
        horizon=3,
    )

    assert world.occupied_mask == (
        world.abiotic_mask & world.biotic_mask & world.movement_mask
    )
    assert world.biotic_mask != world.abiotic_mask
    assert world.movement_mask != world.abiotic_mask


def test_positive_only_cannot_eliminate_positive_superset_world():
    truth = _manual_world("truth", 0b011, (0, 1, None))
    superset = _manual_world("superset", 0b111, (0, 1, 2))

    result = compatible_positive_only((truth, superset), ("a", "b"))

    assert result.compatible_world_ids == ("truth", "superset")


def test_perfect_negative_rescues_superset_ambiguity_under_explicit_contract():
    truth = _manual_world("truth", 0b011, (0, 1, None))
    superset = _manual_world("superset", 0b111, (0, 1, 2))

    result = compatible_with_perfect_negatives(
        (truth, superset),
        ("a", "b"),
        ("c",),
    )

    assert result.compatible_world_ids == ("truth",)


def test_temporal_evidence_can_separate_equal_final_G_with_different_M_arrivals():
    fast = _manual_world("fast", 0b111, (0, 1, 2))
    slow = _manual_world("slow", 0b111, (0, 2, 4))

    static = compatible_with_perfect_negatives(
        (fast, slow),
        ("a", "b", "c"),
        (),
    )
    temporal = compatible_with_temporal_arrivals(
        (fast, slow),
        ("a", "b", "c"),
        (),
        {"a": 0, "b": 1, "c": 2},
    )

    assert static.compatible_world_ids == ("fast", "slow")
    assert temporal.compatible_world_ids == ("fast",)
