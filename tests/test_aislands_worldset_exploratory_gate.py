import runpy

import pytest


_NAMESPACE = runpy.run_path("benchmarks/evaluate_aislands_worldset_exploratory_gate.py")
evaluate_rows = _NAMESPACE["evaluate_rows"]


WORLDS = (
    "g10_env_none",
    "g20_env_none",
    "g30_env_none",
    "g40_env_none",
    "g10_env_q90",
    "g20_env_q90",
    "g30_env_q90",
    "g40_env_q90",
    "g10_env_q75",
    "g20_env_q75",
    "g30_env_q75",
    "g40_env_q75",
)


def _class(count, total):
    if count == 0:
        return "excluded_under_declared_scenarios"
    if count == total:
        return "robust"
    return "contingent"


def _row(supporting, *, extra=None):
    supporting = tuple(supporting)
    unsupported = tuple(world for world in WORLDS if world not in supporting)
    count = len(supporting)
    geo_count = sum(world.endswith("env_none") for world in supporting)
    env_count = count - geo_count
    geo_class = _class(geo_count, 4)
    env_class = _class(env_count, 8)
    row = {
        "world_count": len(WORLDS),
        "support_count": count,
        "connected_frequency": count / len(WORLDS),
        "world_class": _class(count, len(WORLDS)),
        "geography_support_count": geo_count,
        "geography_world_count": 4,
        "geography_world_class": geo_class,
        "environment_support_count": env_count,
        "environment_world_count": 8,
        "environment_world_class": env_class,
        "geo_environment_class_disagreement": int(geo_class != env_class),
        "supporting_world_ids": ";".join(supporting),
        "unsupported_world_ids": ";".join(unsupported),
    }
    if extra:
        row.update(extra)
    return row


def test_gate_passes_only_when_frequency_hides_distinct_ecological_decompositions():
    # Both candidates have support_count=6 / connected_frequency=0.5.
    # The first is geography-robust + environment-contingent (4+2); the second is
    # geography-contingent + environment-contingent (2+4). Aggregate frequency alone
    # cannot distinguish those structures.
    first = WORLDS[:4] + WORLDS[4:6]
    second = WORLDS[:2] + WORLDS[4:8]
    rows = [_row(WORLDS), _row(first), _row(second), _row(())]

    result = evaluate_rows(rows)

    assert result["gate_pass"] is True
    assert result["status"] == "exploratory_world_identity_added_information"
    assert result["support_counts_with_multiple_world_identities"] == [6]
    assert result["support_counts_with_multiple_geo_environment_decompositions"] == [6]
    assert result["informative_frequency_collision_levels"] == [6]
    assert result["rows_in_informative_frequency_collision_groups"] == 2
    assert result["interpretable_collision_rows"] == 1
    assert result["n_contingent_rows"] == 2


def test_gate_fails_when_frequency_fully_determines_world_identity():
    supporting = WORLDS[:4] + WORLDS[4:6]
    rows = [_row(supporting), _row(supporting)]

    result = evaluate_rows(rows)

    assert result["gate_pass"] is False
    assert result["support_counts_with_multiple_world_identities"] == []
    assert result["informative_frequency_collision_levels"] == []
    assert result["status"] == "exploratory_no_world_identity_added_information"


def test_gate_fails_when_identity_differs_but_family_decomposition_is_the_same():
    first = WORLDS[:2] + WORLDS[4:8]
    second = WORLDS[2:4] + WORLDS[8:12]
    rows = [_row(first), _row(second)]

    result = evaluate_rows(rows)

    assert result["support_counts_with_multiple_world_identities"] == [6]
    assert result["support_counts_with_multiple_geo_environment_decompositions"] == []
    assert result["informative_frequency_collision_levels"] == []
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


def test_gate_rejects_family_counts_inconsistent_with_world_ids():
    row = _row(WORLDS[:6])
    row["geography_support_count"] = 3
    with pytest.raises(ValueError, match="geography_support_count does not match"):
        evaluate_rows([row])
