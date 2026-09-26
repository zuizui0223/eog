import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "validation" / "world_survival_regime_v1"
PROTOCOL = BASE / "protocol_v1.json"
LOCK = BASE / "protocol_lock_v1.json"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha1(path):
    raw = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def test_regime_protocol_is_locked_before_candidate_or_response_access():
    protocol = _load(PROTOCOL)
    lock = _load(LOCK)

    assert lock["protocol_git_blob_sha1"] == _git_blob_sha1(PROTOCOL)
    assert lock["lock_state"] == "frozen_before_candidate_roster_or_response_access"
    assert lock["candidate_roster_captured"] is False
    assert lock["biological_response_payload_requests"] == 0
    assert lock["model_fits"] == 0
    assert lock["scored_systems"] == 0

    counters = protocol["access_counters_at_freeze"]
    assert counters["candidate_roster_captured"] is False
    assert counters["biological_response_payload_requests"] == 0
    assert counters["model_fits"] == 0
    assert counters["scored_systems"] == 0


def test_adequacy_and_regime_prediction_are_separate_by_contract():
    protocol = _load(PROTOCOL)
    adequacy = protocol["world_construction"]["adequacy_declaration"]
    prediction = protocol["prediction_rule"]

    assert adequacy["min_largest_weak_component_fraction"] == 0.90
    assert adequacy["max_isolated_node_fraction"] == 0.05
    assert adequacy["min_median_horizon_reachable_fraction"] is None

    assert prediction["per_world_score"] == (
        "median_horizon_reachable_fraction / largest_weak_component_fraction"
    )
    assert prediction["horizon_realization_cutoff"] == 0.5
    assert prediction["cutoff_fit_to_historical_outcomes"] is False
    assert prediction["alternative_cutoff_search_after_response"] is False


def test_non_falsifiable_sentinels_cannot_contaminate_primary_denominator():
    protocol = _load(PROTOCOL)
    denominator = protocol["denominator"]
    forbidden = protocol["forbidden"]

    assert denominator["primary_worlds"] == "falsifiable worlds only"
    assert denominator["non_falsifiable_sentinels_excluded"] is True
    assert denominator["non_falsifiable_world_ids_must_be_declared_before_response"] is True
    assert any("external_open" in rule for rule in forbidden)


def test_primary_response_is_only_positive_node_membership_not_predictive_skill():
    protocol = _load(PROTOCOL)
    response = protocol["response_contract"]
    endpoints = protocol["endpoints"]

    assert response["required_primary_response"] == (
        "stable node identity plus ever-positive focal-taxon indicator"
    )
    assert response["minimum_ever_positive_nodes"] == 2
    assert response["default_source_policy"] == "self_excluded_peer_positive_sources"
    assert response["arbitrary_lexicographic_single_source_forbidden"] is True

    assert endpoints["primary"] == [
        "system-level exact three-state regime match",
        "aggregate exact-match fraction",
    ]
    assert endpoints["chance_reference"] == 1 / 3
