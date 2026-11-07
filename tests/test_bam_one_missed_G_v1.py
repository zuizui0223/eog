"""Finite one-omission observational fibres and truth-blind BAM assay contracts."""
import itertools
import pytest

from benchmarks import bam_one_missed_G_v1 as m
from benchmarks import audit_bam_one_missed_exact_queries_v1 as exact


def test_every_one_cell_deletion_is_enumerated_once():
    assert m.enumerated_observations(0b1101) == (13, 12, 9, 5)
    assert len(set(m.enumerated_observations(0b1101))) == 4
    assert m.compatible(0b0011, 0b0111)
    assert m.compatible(0b0011, 0b0011)
    assert not m.compatible(0b0011, 0b1111)  # two missed positives
    assert m.compatible(0b0101, 0b0111)  # one missed positive


def test_no_false_positives_or_two_omissions_are_admitted():
    assert not m.compatible(0b1001, 0b0111)
    assert not m.compatible(0b0011, 0b1111)
    assert m.compatible(0b0110, 0b0111)


def test_one_d_can_hide_two_true_G_maps_with_distinct_targets():
    worlds = [
        {"world_id": "w1", "A_bits": 3, "B_bits": 3, "M_bits": 3, "G_bits": 3},
        {"world_id": "w2", "A_bits": 7, "B_bits": 7, "M_bits": 7, "G_bits": 7},
    ]
    D = 3
    candidates = [r for r in worlds if m.compatible(D, r["G_bits"])]
    assert {r["G_bits"] for r in candidates} == {3, 7}
    states = m.unique_states(candidates, {"w1": -1, "w2": 1})
    assert len({s["sign"] for s in states}) == 2
    for truth in states:
        path = m.simulate(states, 3, "toy", D, "M",
                          "greedy_all", 0, truth)
        assert path[0][0] is False
        assert path[1][0] is True
        assert path[2][0] is True


def test_site_selection_does_not_consult_true_mask():
    states = [
        {"masks": (3, 3, 3), "sign": -1, "n_labels": 2},
        {"masks": (7, 3, 3), "sign": 1, "n_labels": 1},
        {"masks": (11, 3, 3), "sign": 1, "n_labels": 1},
    ]
    assert m.choose(states, 4, [], "greedy_all", 0, "toy", 3, "M") == ("A", 2)
    assert m.test_score(states, "A", 2) == 1
    first = m.choose(states, 4, [], "hash_all", 20261107, "toy", 3, "M")
    second = m.choose(states, 4, [], "hash_all", 20261107, "toy", 3, "M")
    assert first == second
    assert first in {("A", 2), ("A", 3)}
    # All completely observed occupied D nodes are fixed positive on every axis.
    assert all(node >= 2 for _, node in m.candidate_tests(states, 4, m.AXES))


def test_identical_mask_triplicates_are_not_reweighted():
    rows = [
        {"world_id": "a", "A_bits": 3, "B_bits": 3, "M_bits": 3},
        {"world_id": "a2", "A_bits": 3, "B_bits": 3, "M_bits": 3},
        {"world_id": "b", "A_bits": 7, "B_bits": 3, "M_bits": 3},
    ]
    states = m.unique_states(rows, {"a": -1, "a2": -1, "b": 1})
    assert len(states) == 2
    assert sorted(s["n_labels"] for s in states) == [1, 2]
    with pytest.raises(ValueError, match="conflicting"):
        m.unique_states(rows, {"a": -1, "a2": 1, "b": 1})


def test_exact_minimum_depth_two_for_xor_of_two_local_bits():
    states = [
        {"masks": (a, b, 3), "sign": sign, "n_labels": 1}
        for a, b, sign in [
            (3, 3, -1), (7, 3, 1), (3, 11, 1), (7, 11, -1)
        ]
    ]
    assert exact.exact_min_queries(states, 4) == 2


def test_exact_minimum_depth_three_for_xor_of_three_local_bits():
    states = []
    for i, j, k in itertools.product((0, 1), repeat=3):
        masks = (3 | (i << 2), 3 | (j << 3), 3 | (k << 4))
        states.append({
            "masks": masks,
            "sign": 1 if (i + j + k) % 2 else -1,
            "n_labels": 1,
        })
    assert exact.exact_min_queries(states, 5) == 3


def test_source_protocol_has_not_changed():
    import json
    from pathlib import Path
    contract = json.loads(
        Path("validation/bam_one_missed_G_v1/protocol_v1.json").read_text()
    )
    assert contract["source"]["parameter_worlds"] == 768
    assert contract["source"]["exact_G_fibres"] == 129
    assert contract["observation"]["name"].startswith("at most one")
    assert contract["assays"]["budgets"] == [0, 1, 2, 3]
    assert len(m.SEEDS) == 16
