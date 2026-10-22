import numpy as np

from benchmarks.matched_information_offset import (
    best_path_support,
    build_design,
    simulate_hits,
)


def test_single_path_and_diffusion_differ_on_parallel_routes():
    transition = np.array([[0, 0.5, 0.5, 0], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 0]])
    assert best_path_support(transition, 0, 3) == 0.5
    # Both sources 0 and 1 reach target3 surely, but by different routes.
    assert simulate_hits(transition, np.random.default_rng(7))[3] == 1
    assert best_path_support(transition, 0, 3, steps=1) == 0


def test_killed_walk_never_reappears():
    transition = np.zeros((4, 4))
    np.testing.assert_array_equal(
        simulate_hits(transition, np.random.default_rng(9)), [0.5, 0.5, 0, 0]
    )


def test_simulation_agrees_with_independent_absorbing_recursion():
    transition = np.array(
        [[0, 0.2, 0.3, 0.1], [0.1, 0, 0.2, 0.3], [0.1, 0.1, 0, 0.4], [0.2, 0.1, 0.1, 0]]
    )
    expected = []
    for target in range(4):
        per_source = []
        for source in (0, 1):
            mass = np.zeros(4)
            mass[source] = 1
            arrival = mass[target]
            mass[target] = 0
            for _ in range(4):
                mass = mass @ transition
                arrival += mass[target]
                mass[target] = 0
            per_source.append(arrival)
        expected.append(np.mean(per_source))
    actual = simulate_hits(transition, np.random.default_rng(103), trajectories=32768)
    np.testing.assert_allclose(actual, expected, atol=0.012, rtol=0)


def test_design_reproducible_and_no_world_identity_predictor():
    first, second = build_design(901, 2), build_design(901, 2)
    assert first["x"].shape == (12, 6)
    assert first["path"].shape == (12, 2)
    assert first["eog"].shape == (12, 10)
    assert first["provenance"] == second["provenance"]
    assert "world" not in first
    for key in (
        "x",
        "path",
        "eog",
        "diffusion_change",
        "path_change",
        "uniforms",
        "groups",
    ):
        np.testing.assert_array_equal(first[key], second[key])


def test_complete_archive_and_primary_paired_summary():
    import json
    from pathlib import Path

    from benchmarks.matched_information_offset import REGIMES, SEEDS

    path = (
        Path(__file__).resolve().parents[1]
        / "validation/layer_b_mechanism_v2/matched_information_offset_result_v1.json"
    )
    result = json.loads(path.read_text(encoding="utf-8"))
    assert len(result["rows"]) == 32
    assert {(r["seed"], r["regime"]) for r in result["rows"]} == {
        (s, r) for s in SEEDS for r in REGIMES
    }
    for regime, summary in result["summaries"].items():
        subset = [r for r in result["rows"] if r["regime"] == regime]
        delta = [
            r["selected_loss"]["eog_two"] - r["selected_loss"]["path_two"]
            for r in subset
        ]
        assert np.isclose(
            summary["eog_minus_path_selected"]["mean"], np.mean(delta), atol=1e-12
        )
        assert summary["eog_minus_path_selected"]["eog_wins"] == sum(
            v < 0 for v in delta
        )
        for name, values in summary["methods"].items():
            assert np.isclose(
                values["selected_delta"],
                np.mean(
                    [r["selected_loss"][name] - r["baseline_loss"] for r in subset]
                ),
                atol=1e-12,
            )


def test_outer_reversal_does_not_leak_into_selection(monkeypatch):
    from benchmarks import matched_information_offset as benchmark

    monkeypatch.setattr(benchmark, "SEEDS", (901,))
    result = benchmark.run_comparison()
    assert len(result["rows"]) == 4
    rows = {r["regime"]: r for r in result["rows"]}
    assert (
        rows["diffusion"]["promoted"] == rows["unseen_diffusion_reversal"]["promoted"]
    )
    for row in rows.values():
        for name, value in row["selected_loss"].items():
            assert value == (
                row["always_on_loss"][name]
                if row["promoted"][name]
                else row["baseline_loss"]
            )
