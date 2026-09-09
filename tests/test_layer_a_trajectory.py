import pytest

from eog.v2.layer_a_trajectory import certify_layer_a_trajectory


def test_layer_a_trajectory_records_calibration_contraction_and_exact_ids():
    cert = certify_layer_a_trajectory(
        declared_world_ids=["a", "b", "c"],
        context_ids=["t1", "t2", "t3", "t4"],
        surviving_world_ids_by_context=[
            ["a", "b", "c"],
            ["b", "c"],
            ["b", "c"],
            ["c"],
        ],
        calibration_context_count=3,
    )
    assert cert.surviving_world_counts == (3, 2, 2, 1)
    assert cert.contraction_event_count == 2
    assert cert.calibration_contraction_event_count == 1
    assert cert.calibration_ever_contracted is True
    assert cert.elimination_events == (("t2", ("a",)), ("t4", ("b",)))
    assert cert.final_surviving_world_ids == ("c",)
    assert cert.terminal_universe_falsified is False
    assert cert.to_dict()["schema"] == "eog.layer_a_trajectory_certificate.v1"


def test_layer_a_trajectory_allows_terminal_falsification():
    cert = certify_layer_a_trajectory(
        declared_world_ids=["a", "b"],
        context_ids=["t1", "t2", "t3"],
        surviving_world_ids_by_context=[["a", "b"], [], []],
        calibration_context_count=2,
    )
    assert cert.terminal_universe_falsified is True
    assert cert.final_surviving_world_ids == ()


def test_layer_a_trajectory_rejects_world_return():
    with pytest.raises(ValueError, match="eliminated world returned"):
        certify_layer_a_trajectory(
            declared_world_ids=["a", "b"],
            context_ids=["t1", "t2", "t3"],
            surviving_world_ids_by_context=[["a", "b"], ["b"], ["a", "b"]],
            calibration_context_count=2,
        )


def test_layer_a_trajectory_rejects_unknown_world():
    with pytest.raises(ValueError, match="outside declared universe"):
        certify_layer_a_trajectory(
            declared_world_ids=["a", "b"],
            context_ids=["t1"],
            surviving_world_ids_by_context=[["a", "x"]],
            calibration_context_count=1,
        )
