from eog.v2.bam_target_quotient import (
    joint_value_partition,
    partition_from_values,
    partition_relation,
    refines,
    singleton_parameter_partition,
    target_sufficient,
)


IDS = ("a", "b", "c", "d")


def test_partition_refinement_and_relation():
    parameter = singleton_parameter_partition(IDS)
    current = partition_from_values(
        IDS,
        {"a": 0, "b": 0, "c": 1, "d": 1},
    )
    decision = partition_from_values(
        IDS,
        {"a": False, "b": False, "c": True, "d": True},
    )
    assert refines(parameter, current)
    assert refines(current, decision)
    assert target_sufficient(current, decision)
    assert partition_relation(current, decision, left_label="current", right_label="decision") == "equal"


def test_incomparable_partitions_capture_both_over_and_under_distinction():
    current = partition_from_values(
        IDS,
        {"a": 0, "b": 0, "c": 1, "d": 1},
    )
    decision = partition_from_values(
        IDS,
        {"a": False, "b": True, "c": True, "d": True},
    )
    assert not refines(current, decision)
    assert not refines(decision, current)
    assert partition_relation(
        current,
        decision,
        left_label="current_state",
        right_label="decision",
    ) == "incomparable"


def test_joint_target_partition_refines_each_component():
    one = {"a": 0, "b": 0, "c": 1, "d": 1}
    two = {"a": False, "b": True, "c": False, "d": True}
    p1 = partition_from_values(IDS, one)
    p2 = partition_from_values(IDS, two)
    joint = joint_value_partition(IDS, (one, two))
    assert refines(joint, p1)
    assert refines(joint, p2)
    assert joint.block_count >= max(p1.block_count, p2.block_count)


def test_compression_factor_is_worlds_per_target_class():
    p = partition_from_values(
        IDS,
        {"a": 0, "b": 0, "c": 0, "d": 1},
    )
    assert p.world_count == 4
    assert p.block_count == 2
    assert p.compression_factor == 2.0
