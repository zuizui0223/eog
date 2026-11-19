import runpy


def _engine():
    return runpy.run_path("benchmarks/occurrence_conditioned_source_analyst_v2.py")


def _run():
    return _engine()["run_benchmark"]()


def _frontier(result):
    return {tuple(p) for p in result}


def test_protocol_v2_uses_four_explicit_source_graph_hypotheses():
    r = _run()
    assert r["schema_version"] == 1
    assert r["source_hypotheses"] == ["A", "B"]
    assert r["analyst_variants"] == ["hard_sea_mask", "soft_crossing"]
    assert r["shared_absolute_threshold_axes"] == [[10.0, 25.0, 30.0], [1.0, 2.0], [0.0, 1.0]]
    assert r["threshold_worlds"] == 12
    assert r["source_graph_hypotheses"] == 4
    assert r["tested_hypothesis_threshold_pairs"] == 48
    assert r["independent_bfs_agreed_with_eog_for_all_pairs"] is True
    assert r["exact_finite_world_coverage"] is True


def test_per_source_frontiers_separate_historical_source_assumptions():
    r = _run()
    f = r["per_hypothesis"]
    assert _frontier(f["soft_crossing__source_A"]["source_specific_frontier"]) == {
        (20.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    }
    assert _frontier(f["hard_sea_mask__source_A"]["source_specific_frontier"]) == {
        (20.0, 0.0, 0.0), (0.0, 1.0, 0.0)
    }
    for variant in ("soft_crossing", "hard_sea_mask"):
        assert _frontier(f[f"{variant}__source_B"]["source_specific_frontier"]) == {
            (15.0, 0.0, 0.0)
        }
    assert f["soft_crossing__source_A"]["native_compatible_worlds"] == 10
    assert f["hard_sea_mask__source_A"]["native_compatible_worlds"] == 8
    assert f["soft_crossing__source_B"]["native_compatible_worlds"] == 8
    assert f["hard_sea_mask__source_B"]["native_compatible_worlds"] == 4


def test_existential_possible_is_not_universal_source_and_analyst_necessity():
    r = _run()
    assert _frontier(r["possible_at_least_one_hypothesis_frontier"]) == {
        (15.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    }
    assert _frontier(r["compatible_every_hypothesis_frontier"]) == {
        (20.0, 0.0, 0.0), (15.0, 1.0, 0.0)
    }
    assert _frontier(r["compatible_both_sources_soft_graph_frontier"]) == {
        (20.0, 0.0, 0.0), (15.0, 1.0, 0.0), (15.0, 0.0, 1.0)
    }
    assert r["possible_threshold_count"] == 11
    assert r["universal_threshold_count"] == 6
    assert r["source_analyst_unresolved_threshold_count"] == 5


def test_hard_sea_crossing_never_reopens_under_analyst_permissiveness():
    r = _run()
    assert r["hard_graph_barrier_only_rescue_never_compatible_for_source_A"]
    assert (0.0, 0.0, 1.0) not in _frontier(r["compatible_every_hypothesis_frontier"])


def test_threshold_monotonicity_and_reordered_declarations():
    m = _engine()
    r = m["run_benchmark"]()
    assert r["monotone_ordered_pairs_checked"] > 48
    assert m["_run_matrix"](
        source_hypotheses=("B", "A"),
        analyst_variants=("hard_sea_mask", "soft_crossing"),
        reverse_edges=True,
    ) == r
