import numpy as np

from benchmarks.geometry_offset_comparison import build_design, geometry_state


def test_outer_only_reversal_does_not_change_selection(monkeypatch):
    from benchmarks import geometry_offset_comparison as benchmark

    monkeypatch.setattr(benchmark, "SEEDS", (801,))
    result = benchmark.run_comparison()
    assert len(result["rows"]) == 3
    rows = {row["regime"]: row for row in result["rows"]}
    assert rows["route_signal"]["promoted"] == rows["unseen_route_reversal"]["promoted"]
    assert result["uses_biological_response"] is False
    for row in rows.values():
        for name, selected in row["selected_loss"].items():
            assert np.isfinite(selected)
            assert selected == (
                row["always_on_loss"][name]
                if row["promoted"][name]
                else row["baseline_loss"]
            )


def test_archive_is_complete_and_summaries_match_all_rows():
    import json
    from pathlib import Path

    from benchmarks.geometry_offset_comparison import REGIMES, SEEDS

    path = (
        Path(__file__).resolve().parents[1]
        / "validation/layer_b_mechanism_v2/geometry_offset_development_result_v1.json"
    )
    result = json.loads(path.read_text(encoding="utf-8"))
    assert {(r["seed"], r["regime"]) for r in result["rows"]} == {
        (s, r) for s in SEEDS for r in REGIMES
    }
    assert len(result["rows"]) == 12
    assert set(result["geometry_provenance_sha256"]) == {str(s) for s in SEEDS}
    for regime, summary in result["summaries"].items():
        rows = [r for r in result["rows"] if r["regime"] == regime]
        for name, value in summary.items():
            assert np.isclose(
                value["selected_delta"],
                np.mean([r["selected_loss"][name] - r["baseline_loss"] for r in rows]),
                atol=1e-12,
            )
            assert value["promotions"] == sum(r["promoted"][name] for r in rows)


def test_truth_route_is_not_the_four_step_eog_support():
    xy = np.c_[np.arange(8) * 0.4, np.zeros(8)]
    summary, routes, _, _ = geometry_state(xy)
    assert np.isclose(routes[-1], 2.4)
    # Six edges from the nearer source: finite shortest route, but unreachable
    # within the separately declared four-step EOG horizon in either world.
    assert summary.feature_matrix[-1, 1] == 0


def test_geometry_is_translation_invariant_and_disconnects_far_targets():
    xy = np.array(
        [[0, 0], [0, 0.1], [10, 10], [11, 11], [12, 12], [13, 13], [14, 14], [15, 15]],
        dtype=float,
    )
    summary, routes, _, _ = geometry_state(xy)
    np.testing.assert_array_equal(summary.feature_matrix[2:, 1], 0)
    np.testing.assert_array_equal(routes[2:], 4)
    translated, translated_routes, _, _ = geometry_state(xy + [4, -3])
    np.testing.assert_allclose(
        summary.feature_matrix, translated.feature_matrix, atol=1e-12
    )
    np.testing.assert_allclose(routes, translated_routes)


def test_graph_design_is_repeatable_and_has_six_targets_per_group():
    first, second = build_design(801, graph_count=3), build_design(801, graph_count=3)
    assert first["x"].shape == (18, 6)
    assert first["z"].shape == (18, 10)
    for key in ("x", "z", "absolute", "route_change", "groups", "uniforms"):
        np.testing.assert_array_equal(first[key], second[key])
    assert first["provenance"] == second["provenance"]
    np.testing.assert_array_equal(np.bincount(first["groups"]), [6, 6, 6])
