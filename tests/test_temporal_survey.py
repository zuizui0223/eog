import pytest

from eog.v2.reachability import (
    DynamicReachabilityEdge,
    TemporalWorld,
    build_dynamic_transition_operator,
    rank_positive_temporal_occurrence_candidates,
    reconstruct_temporal_worlds,
)


def _operator(node_ids, edges):
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    return build_dynamic_transition_operator(
        node_ids,
        [
            DynamicReachabilityEdge(
                source=index[source],
                target=index[target],
                geographic_support=float(support),
            )
            for source, target, support in edges
        ],
        loss_support=1.0,
    )


def _empty(node_ids):
    return build_dynamic_transition_operator(node_ids, (), loss_support=1.0)


def _early_and_late_worlds():
    nodes = ("A", "B", "C", "D")
    ab = _operator(nodes, (("A", "B", 1.0),))
    bc = _operator(nodes, (("B", "C", 1.0),))
    ad = _operator(nodes, (("A", "D", 1.0),))
    db = _operator(nodes, (("D", "B", 1.0),))
    empty = _empty(nodes)
    return (
        TemporalWorld("early", ("t0", "t1", "t2", "t3"), (ab, bc, empty), ("A",)),
        TemporalWorld("late", ("t0", "t1", "t2", "t3"), (ad, db, bc), ("A",)),
    )


def _underidentified_reconstruction():
    worlds = _early_and_late_worlds()
    return worlds, reconstruct_temporal_worlds(worlds, (("C", "t3"),))


def _row_by_candidate(ranking):
    return {(row.node_id, row.time_label): row for row in ranking.rows}


def test_temporal_survey_candidates_split_the_remaining_worlds_by_positive_reachability():
    worlds, reconstruction = _underidentified_reconstruction()
    ranking = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("C", "t2"), ("B", "t1"), ("D", "t1"), ("B", "t0"), ("A", "t0")),
    )
    rows = _row_by_candidate(ranking)

    c_t2 = rows[("C", "t2")]
    assert c_t2.status == "discriminating"
    assert c_t2.reachable_world_ids == ("early",)
    assert c_t2.unreachable_world_ids == ("late",)
    assert c_t2.positive_elimination_fraction == pytest.approx(0.5)
    assert c_t2.split_balance == pytest.approx(0.5)

    b_t1 = rows[("B", "t1")]
    assert b_t1.status == "discriminating"
    assert b_t1.reachable_world_ids == ("early",)
    assert b_t1.unreachable_world_ids == ("late",)

    d_t1 = rows[("D", "t1")]
    assert d_t1.status == "discriminating"
    assert d_t1.reachable_world_ids == ("late",)
    assert d_t1.unreachable_world_ids == ("early",)

    b_t0 = rows[("B", "t0")]
    assert b_t0.status == "unsupported_by_compatible_worlds"
    assert b_t0.reachable_world_ids == ()
    assert b_t0.unreachable_world_ids == ("early", "late")
    assert b_t0.positive_elimination_fraction == pytest.approx(1.0)

    a_t0 = rows[("A", "t0")]
    assert a_t0.status == "non_discriminating"
    assert a_t0.reachable_world_ids == ("early", "late")
    assert a_t0.unreachable_world_ids == ()
    assert a_t0.positive_elimination_fraction == pytest.approx(0.0)


def test_positive_temporal_survey_ranking_is_consistent_with_applying_the_observation():
    worlds, reconstruction = _underidentified_reconstruction()
    ranking = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("C", "t2"),),
    )
    row = ranking.rows[0]
    after = reconstruct_temporal_worlds(worlds, (("C", "t3"), ("C", "t2")))

    assert row.status == "discriminating"
    assert row.reachable_world_ids == after.compatible_world_ids == ("early",)
    assert row.unreachable_world_ids == ("late",)


def test_candidate_input_order_does_not_change_ranking_or_fingerprint():
    worlds, reconstruction = _underidentified_reconstruction()
    first = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("C", "t2"), ("D", "t1"), ("A", "t0")),
    )
    second = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("A", "t0"), ("D", "t1"), ("C", "t2")),
    )

    assert first == second


def test_ranking_prioritizes_discrimination_not_universe_challenge():
    worlds, reconstruction = _underidentified_reconstruction()
    ranking = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("B", "t0"), ("A", "t0"), ("C", "t2")),
    )

    assert [(row.node_id, row.time_label, row.status) for row in ranking.rows] == [
        ("C", "t2", "discriminating"),
        ("B", "t0", "unsupported_by_compatible_worlds"),
        ("A", "t0", "non_discriminating"),
    ]


def test_identifiable_world_has_no_discriminating_positive_candidate():
    worlds = _early_and_late_worlds()
    reconstruction = reconstruct_temporal_worlds(worlds, (("C", "t2"),))
    assert reconstruction.compatible_world_ids == ("early",)

    ranking = rank_positive_temporal_occurrence_candidates(
        reconstruction,
        worlds,
        (("B", "t1"), ("D", "t1")),
    )
    rows = _row_by_candidate(ranking)

    assert rows[("B", "t1")].status == "non_discriminating"
    assert rows[("D", "t1")].status == "unsupported_by_compatible_worlds"
    assert all(row.status != "discriminating" for row in ranking.rows)


def test_temporal_survey_rejects_observed_duplicate_invalid_and_mismatched_candidates():
    worlds, reconstruction = _underidentified_reconstruction()

    with pytest.raises(ValueError, match="at least one"):
        rank_positive_temporal_occurrence_candidates(reconstruction, worlds, ())
    with pytest.raises(ValueError, match="unique"):
        rank_positive_temporal_occurrence_candidates(
            reconstruction, worlds, (("C", "t2"), ("C", "t2"))
        )
    with pytest.raises(ValueError, match="outside"):
        rank_positive_temporal_occurrence_candidates(reconstruction, worlds, (("E", "t2"),))
    with pytest.raises(ValueError, match="undeclared"):
        rank_positive_temporal_occurrence_candidates(reconstruction, worlds, (("C", "t9"),))
    with pytest.raises(ValueError, match="already contain observed"):
        rank_positive_temporal_occurrence_candidates(reconstruction, worlds, (("C", "t3"),))

    different_universe = (worlds[0],)
    with pytest.raises(ValueError, match="same frozen temporal world universe"):
        rank_positive_temporal_occurrence_candidates(
            reconstruction, different_universe, (("C", "t2"),)
        )
