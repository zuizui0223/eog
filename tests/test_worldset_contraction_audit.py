import pytest

from eog.v2.worldset_contraction_audit import audit_worldset_contraction


def test_saturated_worldset_is_reported_without_fake_contraction():
    audit = audit_worldset_contraction(5, [5, 5, 5, 5, 5])
    assert audit.ever_contracted is False
    assert audit.contraction_event_count == 0
    assert audit.total_worlds_eliminated == 0
    assert audit.fully_saturated_context_fraction == 1.0
    assert audit.final_surviving_world_fraction == 1.0
    assert audit.terminal_universe_falsified is False


def test_monotone_contraction_and_terminal_falsification_are_distinct_states():
    audit = audit_worldset_contraction(5, [5, 5, 4, 2, 2, 0])
    assert audit.ever_contracted is True
    assert audit.contraction_event_count == 3
    assert audit.total_worlds_eliminated == 5
    assert audit.fully_saturated_context_count == 2
    assert audit.final_surviving_world_fraction == 0.0
    assert audit.terminal_universe_falsified is True


def test_surviving_worlds_cannot_return_after_elimination():
    with pytest.raises(ValueError, match="eliminated worlds cannot return"):
        audit_worldset_contraction(5, [5, 3, 4])
