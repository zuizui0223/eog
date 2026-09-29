import itertools

from eog.v2.bam_identifiability_theory import (
    DiagnosticMeasurement,
    FiniteBAMState,
    bam_state_equivalence_class,
    bam_state_identified,
    brute_force_minimum_diagnostic_measurements,
    evidence_ladder,
    exact_minimum_diagnostic_measurements,
    survivor_E0,
    survivor_E1,
    survivor_E2,
    survivor_E3,
    survivor_E4,
    survivor_E5,
    survivor_E6,
)


NODE_IDS = ("a", "b")


def _subsets():
    nodes = list(NODE_IDS)
    rows = []
    for size in range(len(nodes) + 1):
        rows.extend(frozenset(combo) for combo in itertools.combinations(nodes, size))
    return tuple(rows)


def _small_universe():
    tau_rows = (
        (0, 1),
        (0, None),
        (None, 0),
        (None, None),
    )
    worlds = []
    index = 0
    for A in _subsets():
        for B in _subsets():
            for M in _subsets():
                for tau in tau_rows:
                    worlds.append(
                        FiniteBAMState(
                            world_id=f"w{index:04d}",
                            node_ids=NODE_IDS,
                            A=A,
                            B=B,
                            M=M,
                            tau=tau,
                            parameter_label=f"p{index}",
                        )
                    )
                    index += 1
    return tuple(worlds)


def test_T1_T6_exhaustively_on_two_node_bam_universe():
    worlds = _small_universe()

    for truth in worlds:
        direct_E0 = tuple(
            world.world_id
            for world in worlds
            if truth.G <= world.G
        )
        direct_E1 = tuple(
            world.world_id
            for world in worlds
            if world.G == truth.G
        )
        positive_indices = tuple(
            i for i, node_id in enumerate(NODE_IDS) if node_id in truth.G
        )
        direct_E2 = tuple(
            world.world_id
            for world in worlds
            if world.G == truth.G
            and all(world.tau[i] == truth.tau[i] for i in positive_indices)
        )
        direct_E3 = tuple(
            world.world_id
            for world in worlds
            if world.world_id in set(direct_E2) and world.A == truth.A
        )
        direct_E4 = tuple(
            world.world_id
            for world in worlds
            if world.world_id in set(direct_E3) and world.B == truth.B
        )
        direct_E5 = tuple(
            world.world_id
            for world in worlds
            if world.world_id in set(direct_E4) and world.M == truth.M
        )
        direct_E6 = tuple(
            world.world_id
            for world in worlds
            if world.world_id in set(direct_E5) and world.tau == truth.tau
        )

        assert survivor_E0(worlds, truth) == direct_E0
        assert survivor_E1(worlds, truth) == direct_E1
        assert survivor_E2(worlds, truth) == direct_E2
        assert survivor_E3(worlds, truth) == direct_E3
        assert survivor_E4(worlds, truth) == direct_E4
        assert survivor_E5(worlds, truth) == direct_E5
        assert survivor_E6(worlds, truth) == direct_E6

        ladder = evidence_ladder(worlds, truth)
        for before, after in zip(ladder, ladder[1:]):
            assert set(after) <= set(before)

        assert survivor_E6(worlds, truth) == bam_state_equivalence_class(worlds, truth)
        assert bam_state_identified(worlds, survivor_E6(worlds, truth))


def test_positive_superset_world_cannot_be_eliminated_by_complete_positive_occurrences():
    truth = FiniteBAMState(
        "truth",
        ("a", "b", "c"),
        frozenset({"a", "b"}),
        frozenset({"a", "b"}),
        frozenset({"a", "b"}),
        (0, 1, None),
    )
    permissive = FiniteBAMState(
        "permissive",
        ("a", "b", "c"),
        frozenset({"a", "b", "c"}),
        frozenset({"a", "b", "c"}),
        frozenset({"a", "b", "c"}),
        (0, 1, 2),
    )

    assert survivor_E0((truth, permissive), truth) == ("permissive", "truth")
    assert survivor_E1((truth, permissive), truth) == ("truth",)


def test_complete_map_identifies_G_not_bam_decomposition():
    left = FiniteBAMState(
        "left",
        ("a", "b"),
        frozenset({"a"}),
        frozenset({"a", "b"}),
        frozenset({"a", "b"}),
        (0, 1),
    )
    right = FiniteBAMState(
        "right",
        ("a", "b"),
        frozenset({"a", "b"}),
        frozenset({"a"}),
        frozenset({"a", "b"}),
        (0, 1),
    )

    assert left.G == right.G == frozenset({"a"})
    assert survivor_E1((left, right), left) == ("left", "right")
    assert survivor_E3((left, right), left) == ("left",)


def test_exact_hitting_set_solver_matches_brute_force():
    survivors = ("truth", "w1", "w2", "w3")
    target = ("truth",)
    measurements = (
        DiagnosticMeasurement("m1", frozenset({"w1", "w2"})),
        DiagnosticMeasurement("m2", frozenset({"w2", "w3"})),
        DiagnosticMeasurement("m3", frozenset({"w1"})),
        DiagnosticMeasurement("m4", frozenset({"w3"})),
    )

    exact = exact_minimum_diagnostic_measurements(survivors, target, measurements)
    brute = brute_force_minimum_diagnostic_measurements(survivors, target, measurements)

    assert exact == brute
    assert len(exact) == 2


def test_hitting_set_solver_returns_none_when_nuisance_world_is_not_measurably_distinct():
    survivors = ("truth", "alias")
    target = ("truth",)
    measurements = (
        DiagnosticMeasurement("m1", frozenset()),
        DiagnosticMeasurement("m2", frozenset()),
    )

    assert exact_minimum_diagnostic_measurements(survivors, target, measurements) is None
    assert brute_force_minimum_diagnostic_measurements(survivors, target, measurements) is None
