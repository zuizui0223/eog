import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from eog.v2.world_adequacy import StructuralAdequacyDeclaration
from eog.v2.world_survival_regime_v2 import (
    deduplicate_structural_worlds,
    prepare_world_survival_regime_v2,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "validation" / "world_survival_regime_v2" / "protocol_v2.json"
LOCK = ROOT / "validation" / "world_survival_regime_v2" / "protocol_lock_v2.json"


def _symmetric(n, edges):
    adjacency = np.zeros((n, n), dtype=bool)
    for left, right in edges:
        adjacency[left, right] = True
        adjacency[right, left] = True
    return adjacency


def _star(n, center=0):
    return _symmetric(n, [(center, node) for node in range(n) if node != center])


def _ring(n):
    return _symmetric(n, [(node, (node + 1) % n) for node in range(n)])


def _complete(n):
    adjacency = np.ones((n, n), dtype=bool)
    np.fill_diagonal(adjacency, False)
    return adjacency


def _adequacy():
    return StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.9,
        max_isolated_node_fraction=0.1,
    )


def _blob_sha1(path):
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def test_v2_protocol_blob_is_locked_before_candidate_forecasts():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))

    assert lock["protocol_git_blob_sha1"] == _blob_sha1(PROTOCOL)
    assert lock["lock_state"] == (
        "frozen_before_any_v2_candidate_forecast_or_biological_response"
    )
    assert lock["candidate_forecasts_computed"] == 0
    assert lock["biological_response_payload_requests"] == 0
    assert protocol["forecast"]["structural_horizon"] == 1
    assert protocol["forecast"]["cutoff"] == 0.5
    assert protocol["forecast"]["cutoff_changed_from_v1"] is False


def test_exact_duplicate_adjacencies_count_once_and_keep_aliases():
    complete = _complete(6)
    star = _star(6)
    result = deduplicate_structural_worlds(
        {
            "lcc750": complete,
            "lcc900": complete.copy(),
            "local": star,
        }
    )

    assert result.declared_world_count == 3
    assert result.distinct_world_count == 2
    groups = {row.canonical_world_id: row for row in result.alias_groups}
    assert groups["lcc750"].alias_world_ids == ("lcc750", "lcc900")
    assert groups["local"].alias_world_ids == ("local",)


def test_v2_one_step_rule_can_express_all_three_regimes():
    nodes = tuple(f"n{i}" for i in range(6))

    failed = prepare_world_survival_regime_v2(
        nodes,
        {"star_a": _star(6, 0), "star_b": _star(6, 1)},
        adequacy=_adequacy(),
    )
    assert failed.forecast.regime == "falsified_universe"
    assert failed.forecast.predicted_surviving_world_fraction == 0.0

    contracting = prepare_world_survival_regime_v2(
        nodes,
        {"star": _star(6), "complete": _complete(6)},
        adequacy=_adequacy(),
    )
    assert contracting.forecast.regime == "contracting"
    assert contracting.forecast.predicted_surviving_world_fraction == 0.5

    saturated = prepare_world_survival_regime_v2(
        nodes,
        {"ring": _ring(6), "complete": _complete(6)},
        adequacy=_adequacy(),
    )
    assert saturated.forecast.regime == "saturated"
    assert saturated.forecast.predicted_surviving_world_fraction == 1.0


def test_v2_keeps_cutoff_at_half_and_one_step_audit():
    nodes = tuple(f"n{i}" for i in range(6))
    result = prepare_world_survival_regime_v2(
        nodes,
        {"star": _star(6), "complete": _complete(6)},
        adequacy=_adequacy(),
        horizon_realization_cutoff=0.5,
    )

    assert result.audit.horizon == 1
    assert result.forecast.cutoff == 0.5
    by_id = {row.world_id: row for row in result.forecast.structural_rows}
    assert by_id["star"].horizon_realization_ratio == pytest.approx(1 / 3)
    assert by_id["complete"].horizon_realization_ratio == 1.0


def test_v2_rejects_horizon_reachability_in_adequacy_gate():
    nodes = tuple(f"n{i}" for i in range(6))
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=0.9,
        min_median_horizon_reachable_fraction=0.5,
    )
    with pytest.raises(ValueError, match="reserves one-step horizon reachability"):
        prepare_world_survival_regime_v2(
            nodes,
            {"complete": _complete(6)},
            adequacy=adequacy,
        )
