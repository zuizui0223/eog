from itertools import combinations

from eog.v2.falsification_driven_design import (
    build_v23_intervention_library,
    plan_v24,
)
from eog.v2.generic_evidence_design import (
    equivalence_classes,
    plan_finite_evidence_design,
)
from eog.v2.known_truth_bam_v2_1 import build_v21_system


def _generic_inputs():
    return build_v23_intervention_library()


def _p_only_contracted_active_worlds():
    passive, _ = _generic_inputs()
    system = build_v21_system()
    axes_by = system.axes_by_world

    classes = equivalence_classes(
        passive,
        {
            "placeholder": {world_id: 0 for world_id in passive},
        },
    )

    keep = set(passive)
    for group in classes:
        if len(group) != 2:
            continue
        left, right = group
        l = axes_by[left]
        r = axes_by[right]
        varying = []
        if l.abiotic_label != r.abiotic_label:
            varying.append("A")
        if l.biotic_mode != r.biotic_mode:
            varying.append("B")
        if l.step_radius != r.step_radius:
            varying.append("D")
        if l.barrier_permeable != r.barrier_permeable:
            varying.append("P")
        if l.horizon != r.horizon:
            varying.append("H")
        if varying == ["P"]:
            keep.remove(max(group))
    return tuple(sorted(keep))


def test_g1_generic_api_reproduces_frozen_v24_outputs():
    passive, interventions = _generic_inputs()
    generic = plan_finite_evidence_design(passive, interventions)
    frozen = plan_v24()

    assert len(generic.active_world_ids) == frozen["world_count"] == 64
    assert len(generic.unresolved_world_pairs) == frozen["passive_unresolved_pair_count"] == 16

    generic_rank = {
        row.evidence_id: row.split_unresolved_pairs for row in generic.rankings
    }
    frozen_rank = {
        row["intervention_id"]: row["split_unresolved_pairs"]
        for row in frozen["ranked_interventions"]
    }
    assert generic_rank == frozen_rank

    assert list(generic.minimum_separating_set or ()) == frozen["minimum_separating_set"]
    assert generic.minimum_set_size == frozen["minimum_set_size"] == 2
    assert generic.all_active_worlds_separated is frozen["all_worlds_separated"] is True
    assert {len(group) for group in generic.final_equivalence_classes} == {1}


def test_g2_insufficient_library_returns_unresolved_instead_of_inventing_evidence():
    passive, interventions = _generic_inputs()
    limited = {
        key: interventions[key]
        for key in ("P_barrier_challenge", "repeat_passive_state")
    }

    plan = plan_finite_evidence_design(passive, limited)

    assert len(plan.unresolved_world_pairs) == 16
    assert plan.minimum_separating_set is None
    assert plan.minimum_set_size is None
    assert plan.insufficient_library is True
    assert plan.all_active_worlds_separated is False

    sizes = sorted(len(group) for group in plan.final_equivalence_classes)
    assert sizes.count(2) == 8
    assert sizes.count(1) == 48


def test_g3_replanning_after_world_contraction_uses_only_surviving_worlds():
    passive, interventions = _generic_inputs()
    active = _p_only_contracted_active_worlds()

    assert len(active) == 56

    plan = plan_finite_evidence_design(
        passive,
        interventions,
        active_world_ids=active,
    )

    assert set(plan.active_world_ids) == set(active)
    assert len(plan.unresolved_world_pairs) == 8
    assert plan.minimum_separating_set == ("H_long_corridor_challenge",)
    assert plan.minimum_set_size == 1
    assert plan.all_active_worlds_separated is True
    assert all(len(group) == 1 for group in plan.final_equivalence_classes)


def test_g4_appending_evidence_never_merges_previously_separated_classes():
    passive, interventions = _generic_inputs()
    evidence_ids = tuple(sorted(interventions))

    previous_partitions = {}
    for size in range(len(evidence_ids) + 1):
        for subset in combinations(evidence_ids, size):
            classes = equivalence_classes(
                passive,
                interventions,
                selected_evidence_ids=subset,
            )
            class_by_world = {
                world_id: frozenset(group)
                for group in classes
                for world_id in group
            }
            previous_partitions[subset] = class_by_world

    for subset, before in previous_partitions.items():
        remaining = [evidence_id for evidence_id in evidence_ids if evidence_id not in subset]
        for evidence_id in remaining:
            after_subset = tuple(sorted((*subset, evidence_id)))
            after = previous_partitions[after_subset]
            for world_id in passive:
                assert after[world_id].issubset(before[world_id])
