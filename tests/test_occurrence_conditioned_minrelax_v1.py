import runpy

import pytest


def _module():
    return runpy.run_path("benchmarks/occurrence_conditioned_minrelax_v1.py")


def _result():
    return _module()["run_benchmark"]()


def _frontier_vectors(rows):
    return {
        (r["relaxations"]["geographic_km"],
         r["relaxations"]["environmental_units"],
         r["relaxations"]["barrier_permission"])
        for r in rows
    }


def test_protocol_primary_has_three_incomparable_needs_from_actual_edge_requirements():
    p = _result()["primary"]
    assert p["schema_version"] == 1
    assert p["world_count"] == 8
    assert p["compatible_world_count"] == 7
    assert p["status"] == "rescued_by_declared_relaxation"
    assert not p["coordinatewise_minima_jointly_feasible"]
    assert p["coordinatewise_minima"] == {
        "geographic_km": 0.0, "environmental_units": 0.0, "barrier_permission": 0.0
    }
    assert _frontier_vectors(p["frontier"]) == {
        (20.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    }
    assert p["independent_bfs_agrees_for_every_world"]
    assert p["coverage_certificate"] == (
        "all_declared_finite_edge_breakpoints_enumerated_within_fixed_candidate_graph"
    )


def test_frontier_points_have_explicit_feasible_witness_routes_not_unique_history():
    p = _result()["primary"]
    witness = {
        tuple(r["witness_paths_not_historical"]["B"])
        for r in p["frontier"]
    }
    assert witness == {
        ("A", "B"), ("A", "X", "B"), ("A", "Y", "B")
    }
    assert "not observed dispersal history" in p["claim_boundary"]


def test_added_positive_requires_additional_geographic_relaxation_on_all_rescues():
    r = _result()["additional_positive"]
    assert r["world_count"] == 12
    assert r["compatible_world_count"] == 7
    assert _frontier_vectors(r["frontier"]) == {
        (20.0, 0.0, 0.0), (5.0, 1.0, 0.0), (5.0, 0.0, 1.0)
    }
    assert all("C" in point["witness_paths_not_historical"] for point in r["frontier"])
    assert r["independent_bfs_agrees_for_every_world"]


def test_repeated_positive_constraints_contract_compatibility_only_on_same_fixed_graph():
    m = _module()
    run = m["infer_required_relaxations"]
    edge = m["DirectedRequirement"]
    requirements = m["_example_requirements"]() + (edge("A", "C", 15.0, 1.0),)
    before = run(
        node_ids=("A", "B", "C", "X", "Y"),
        requirements=requirements,
        source_ids=("A",),
        observed_positive_ids=("A", "B"),
        baseline=(10.0, 1.0, 0.0),
        max_steps=3,
    )
    after = run(
        node_ids=("A", "B", "C", "X", "Y"),
        requirements=requirements,
        source_ids=("A",),
        observed_positive_ids=("A", "B", "C"),
        baseline=(10.0, 1.0, 0.0),
        max_steps=3,
    )
    assert before["world_count"] == after["world_count"] == 12
    assert before["compatible_world_count"] == 10
    assert after["compatible_world_count"] == 7
    assert _frontier_vectors(before["frontier"]) == {
        (20.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    }


def test_immutable_hard_barrier_is_never_rescued_by_permission():
    r = _result()["hard_unavailable_stop"]
    assert r["world_count"] == 1
    assert r["compatible_world_count"] == 0
    assert r["frontier"] == []
    assert r["status"] == "no_feasible_world_within_declared_graph_and_step_limit"
    assert r["coordinatewise_minima"] is None
    assert r["independent_bfs_agrees_for_every_world"]


def test_already_feasible_under_baseline_has_zero_requirement():
    m = _module()
    r = m["infer_required_relaxations"](
        node_ids=("A", "B"),
        requirements=(m["DirectedRequirement"]("A", "B", 5, 0),),
        source_ids=("A",),
        observed_positive_ids=("A", "B"),
        baseline=(10., 1., 0.),
        max_steps=1,
    )
    assert r["status"] == "baseline_compatible"
    assert _frontier_vectors(r["frontier"]) == {(0.0, 0.0, 0.0)}
    assert r["coordinatewise_minima_jointly_feasible"]


def test_edge_order_cannot_change_frozen_world_fingerprints_or_frontier():
    m = _module()
    run = m["infer_required_relaxations"]
    edges = m["_example_requirements"]()
    kw = dict(node_ids=("A", "B", "X", "Y"), source_ids=("A",),
              observed_positive_ids=("A", "B"), baseline=(10., 1., 0.),
              max_steps=3)
    a = run(requirements=edges, **kw)
    b = run(requirements=tuple(reversed(edges)), **kw)
    assert a == b


def test_horizon_changes_which_rescue_routes_exist():
    m = _module()
    run = m["infer_required_relaxations"]
    kw = dict(node_ids=("A", "B", "X", "Y"),
              requirements=m["_example_requirements"](),
              source_ids=("A",), observed_positive_ids=("A", "B"),
              baseline=(10., 1., 0.))
    at_one = run(max_steps=1, **kw)
    at_two = run(max_steps=2, **kw)
    assert _frontier_vectors(at_one["frontier"]) == {(20.0, 0.0, 0.0)}
    assert _frontier_vectors(at_two["frontier"]) == {
        (20.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
    }


def test_fail_closed_when_universe_or_source_contract_is_undefined():
    m = _module()
    run = m["infer_required_relaxations"]
    edge = m["DirectedRequirement"]
    kw = dict(node_ids=("A", "B", "X", "Y"),
              requirements=m["_example_requirements"](),
              source_ids=("A",), observed_positive_ids=("A", "B"),
              baseline=(10., 1., 0.), max_steps=3)
    with pytest.raises(ValueError, match="max_worlds"):
        run(max_worlds=4, **kw)
    with pytest.raises(ValueError, match="sources must be observed"):
        run(**{**kw, "source_ids": ("X",)})
    with pytest.raises(ValueError, match="at least one non-source"):
        run(**{**kw, "observed_positive_ids": ("A",)})
    with pytest.raises(ValueError, match="unique endpoints"):
        run(**{**kw, "requirements": (edge("A", "B", 5, 1), edge("A", "B", 6, 1))})
    with pytest.raises(ValueError, match="categorical"):
        edge("A", "B", 4, 0, 0.5)
    with pytest.raises(ValueError, match="finite and nonnegative"):
        edge("A", "B", float("nan"), 1)
