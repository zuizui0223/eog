import runpy

import pytest


_NAMESPACE = runpy.run_path("benchmarks/evaluate_aislands_worldset_exploratory_gate.py")
evaluate_rows = _NAMESPACE["evaluate_rows"]


WORLDS = tuple(f"w{i}" for i in range(12))


def _row(supporting, *, disagreement=False, extra=None):
    supporting = tuple(supporting)
    unsupported = tuple(world for world in WORLDS if world not in supporting)
    count = len(supporting)
    if count == 0:
        world_class = "excluded_under_declared_scenarios"
    elif count == len(WORLDS):
        world_class = "robust"
    else:
        world_class = "contingent"
    row = {
        "world_count": len(WORLDS),
        "support_count": count,
        "connected_frequency": count / len(WORLDS),
        "world_class": world_class,
        "geo_environment_class_disagreement": int(disagreement),
        "supporting_world_ids": ";".join(supporting),
        "unsupported_world_ids": ";".join(unsupported),
    }
    if extra:
        row.update(extra)
    return row


def test_gate_passes_only_when_frequency_compression_hides_interpretable_world_identity():
    rows = [
        _row(WORLDS),
        _row(WORLDS[:6], disagreement=True),
        _row((*WORLDS[:5], WORLDS[6])),
        _row(()),
    ]

    result = evaluate_rows(rows)

    assert result["gate_pass"] is True
    assert result["status"] == "exploratory_world_identity_added_information"
    assert result["support_counts_with_multiple_world_identities"] == [6]
    assert result["rows_in_frequency_collision_groups"] == 2
    assert result["interpretable_collision_rows"] == 1
    assert result["n_contingent_rows"] == 2


def test_gate_fails_when_frequency_fully_determines_world_identity():
    rows = [
        _row(WORLDS[:6], disagreement=True),
        _row(WORLDS[:6]),
    ]

    result = evaluate_rows(rows)

    assert result["gate_pass"] is False
    assert result["support_counts_with_multiple_world_identities"] == []
    assert result["status"] == "exploratory_no_world_identity_added_information"


def test_gate_fails_when_identity_differs_but_has_no_geo_environment_interpretation():
    rows = [
        _row(WORLDS[:6]),
        _row((*WORLDS[:5], WORLDS[6])),
    ]

    result = evaluate_rows(rows)

    assert result["support_counts_with_multiple_world_identities"] == [6]
    assert result["interpretable_collision_rows"] == 0
    assert result["gate_pass"] is False


def test_gate_rejects_response_bearing_columns():
    rows = [_row(WORLDS[:6], extra={"heldout_presence": 1})]
    with pytest.raises(ValueError, match="response-bearing columns are forbidden"):
        evaluate_rows(rows)


def test_gate_rejects_support_count_identity_mismatch():
    row = _row(WORLDS[:6])
    row["support_count"] = 5
    with pytest.raises(ValueError, match="support_count does not match"):
        evaluate_rows([row])
