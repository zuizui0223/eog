from benchmarks.run_eog_original_idea_cost_uncertain_policy_v16 import (
    PolicyOption,
    _dominates,
    _policy_frontier,
    _prune,
    _prune_vectors,
)


def test_componentwise_dominance_prunes_cost_blind_policies():
    options = (
        PolicyOption((2, 2, 2, 2), "a", "A"),
        PolicyOption((3, 2, 2, 2), "b", "B"),
        PolicyOption((1, 4, 1, 4), "c", "C"),
    )
    kept = _prune(options)
    assert {row.serialization for row in kept} == {"a", "c"}


def test_equal_cost_vector_keeps_lexicographically_first_tree():
    options = (
        PolicyOption((2, 2, 2, 2), "z", "Z"),
        PolicyOption((2, 2, 2, 2), "a", "A"),
    )
    kept = _prune(options)
    assert len(kept) == 1
    assert kept[0].serialization == "a"


def test_small_fixture_has_exact_cost_blind_frontier_and_nonnegative_regret():
    target = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5)
    actions = {
        "REL:a": tuple(range(12)),
        "FP:b": (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5),
        "KO:c": (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1),
    }
    result = _policy_frontier(target, actions)
    assert result["resolvable"] is True
    assert result["frontier"]
    selected = result["selected"]
    oracle = result["oracle_costs"]
    assert all(
        cost >= lower
        for cost, lower in zip(selected.costs, oracle, strict=True)
    )


def test_incremental_vector_prune_matches_bruteforce_dominance():
    vectors = (
        (0, 4, 4, 4),
        (1, 1, 5, 5),
        (1, 2, 2, 5),
        (2, 2, 2, 2),
        (3, 2, 2, 2),
        (4, 4, 0, 4),
        (4, 4, 4, 0),
        (2, 3, 1, 3),
        (2, 3, 1, 3),
    )
    expected = tuple(
        sorted(
            {
                vector
                for vector in vectors
                if not any(
                    other != vector and _dominates(other, vector)
                    for other in vectors
                )
            },
            key=lambda row: (sum(row), row),
        )
    )
    assert _prune_vectors(vectors) == expected
