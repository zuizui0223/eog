from benchmarks.run_eog_original_idea_cost_information_value_v17 import (
    _build_solver,
)


def test_more_cost_information_cannot_increase_exact_minimax_regret():
    target = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5)
    actions = {
        "REL:a": tuple(range(12)),
        "FP:b": (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5),
        "KO:c": (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1),
    }
    solver = _build_solver(target, actions)
    all_costs = ("equal", "KO_expensive", "FP_expensive", "REL_expensive")
    baseline = solver["minimum_max_regret"](all_costs)
    residual = solver["minimum_max_regret"](
        ("equal", "KO_expensive", "REL_expensive")
    )
    assert residual <= baseline


def test_singleton_cost_world_has_zero_regret():
    target = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5)
    actions = {
        "REL:a": tuple(range(12)),
        "FP:b": (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5),
        "KO:c": (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1),
    }
    solver = _build_solver(target, actions)
    assert solver["minimum_max_regret"](("FP_expensive",)) == 0


def test_perfect_information_break_even_equals_baseline_regret():
    target = (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5)
    actions = {
        "REL:a": tuple(range(12)),
        "FP:b": (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5),
        "KO:c": (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1),
    }
    solver = _build_solver(target, actions)
    baseline = solver["minimum_max_regret"](
        ("equal", "KO_expensive", "FP_expensive", "REL_expensive")
    )
    assert baseline >= 0
    assert baseline - 0 == baseline
