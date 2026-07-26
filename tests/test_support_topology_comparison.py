import numpy as np
import pytest

from eog.support_topology_comparison import (
    HeldoutCandidate,
    SupportTopologyComparisonConfig,
    compare_support_topology_heldout,
)


def fixture_inputs():
    support = np.full((3, 7), 0.05)
    mask = np.ones_like(support, dtype=bool)
    mask[:, 0:2] = False
    mask[:, 4:6] = False
    support[:, 0:2] = np.array([[0.8, 0.85], [0.9, 0.88], [0.78, 0.82]])
    support[:, 4:6] = support[:, 0:2]
    anchors = {"west": (1, 0)}
    candidates = (
        HeldoutCandidate("east_a", 0, 4, 1),
        HeldoutCandidate("east_b", 1, 4, 1),
        HeldoutCandidate("west_a", 0, 0, 0),
        HeldoutCandidate("west_b", 1, 0, 0),
    )
    config = SupportTopologyComparisonConfig(
        thresholds=(0.8, 0.7),
        single_threshold=0.7,
        minimum_persistence_steps=2,
    )
    return support, mask, anchors, candidates, config


def test_comparison_is_deterministic_and_topology_separates_matched_support():
    inputs = fixture_inputs()
    first = compare_support_topology_heldout(*inputs)
    second = compare_support_topology_heldout(*inputs)
    assert first.fingerprint == second.fingerprint
    assert first.metrics["support_only"].roc_auc == 0.5
    assert first.metrics["multi_threshold_persistent"].roc_auc == 1.0
    assert first.metrics["multi_threshold_persistent"].brier_score == 0.0


def test_multiple_anchors_use_nearest_distance():
    support, mask, _, candidates, config = fixture_inputs()
    result = compare_support_topology_heldout(
        support,
        mask,
        {"west": (1, 0), "east": (1, 5)},
        candidates,
        config,
    )
    rows = {row["candidate_id"]: row for row in result.candidates}
    assert rows["east_b"]["distance_to_nearest_anchor"] == 1.0


def test_invalid_candidates_are_rejected():
    support, mask, anchors, _, config = fixture_inputs()
    with pytest.raises(ValueError, match="zero or one"):
        compare_support_topology_heldout(
            support,
            mask,
            anchors,
            (HeldoutCandidate("bad", 0, 0, 2),),
            config,
        )
    with pytest.raises(ValueError, match="masked cell"):
        compare_support_topology_heldout(
            support,
            mask,
            anchors,
            (HeldoutCandidate("masked", 0, 3, 1), HeldoutCandidate("ok", 0, 0, 0)),
            config,
        )


def test_claim_limit_is_explicit():
    result = compare_support_topology_heldout(*fixture_inputs())
    assert "does not establish occupancy probability" in result.claim_limit
    assert "general superiority" in result.claim_limit
