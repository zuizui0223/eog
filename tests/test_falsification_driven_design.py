from eog.v2.falsification_driven_design import (
    augmented_equivalence_classes,
    build_v23_intervention_library,
    exact_minimum_separating_set,
    pair_coverage_holds,
    passive_unresolved_pairs,
    plan_v24,
)


def test_passive_unresolved_pairs_match_v22_alias_structure():
    passive, interventions = build_v23_intervention_library()
    unresolved = passive_unresolved_pairs(passive)

    assert len(passive) == 64
    assert len(unresolved) == 16
    assert exact_minimum_separating_set(passive, interventions) == (
        "H_long_corridor_challenge",
        "P_barrier_challenge",
    )


def test_pair_cover_matches_augmented_injectivity_for_all_subsets():
    passive, interventions = build_v23_intervention_library()
    unresolved = passive_unresolved_pairs(passive)
    ids = tuple(sorted(interventions))

    subsets = [
        (),
        (ids[0],),
        (ids[1],),
        (ids[2],),
        (ids[0], ids[1]),
        (ids[0], ids[2]),
        (ids[1], ids[2]),
        ids,
    ]
    for subset in subsets:
        cover = pair_coverage_holds(unresolved, interventions, subset)
        classes = augmented_equivalence_classes(passive, interventions, subset)
        injective = all(len(group) == 1 for group in classes)
        assert cover is injective


def test_frozen_intervention_library_has_expected_exact_structure():
    result = plan_v24()
    rows = {row["intervention_id"]: row for row in result["ranked_interventions"]}

    assert rows["P_barrier_challenge"]["split_unresolved_pairs"] == 8
    assert rows["H_long_corridor_challenge"]["split_unresolved_pairs"] == 8
    assert rows["repeat_passive_state"]["split_unresolved_pairs"] == 0
    assert result["minimum_separating_set"] == [
        "H_long_corridor_challenge",
        "P_barrier_challenge",
    ]
    assert result["minimum_set_size"] == 2
    assert result["all_worlds_separated"] is True
    assert result["final_class_size_distribution"] == {1: 64} or result["final_class_size_distribution"] == {"1": 64}
    assert result["verdicts"] == {
        "E1_pair_cover_equivalence": "SUPPORTED",
        "E2_current_library_structure": "SUPPORTED",
        "E3_minimum_design": "SUPPORTED",
    }
