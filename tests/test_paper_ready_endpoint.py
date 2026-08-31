from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)
from eog.v2.outcome_access import (
    REQUIRED_FREEZE_KEYS,
    FrozenOutcomeAccessContract,
    evaluate_outcome_access_gate,
)
from eog.v2.paper_ready_endpoint import (
    FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT,
    FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT,
    FrozenPaperReadyEndpoint3Boundary,
    evaluate_paper_ready_endpoint_3_gate,
)
from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration
from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)


ROOT = Path(__file__).resolve().parents[1]


def _candidate_declaration() -> CandidatePreflightDeclaration:
    return CandidatePreflightDeclaration(
        attempt_id="endpoint-3-fresh-v1",
        minimum_nodes=40,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
        require_closed_analysis_registry=True,
    )


def _candidate_result(declaration: CandidatePreflightDeclaration):
    return evaluate_candidate_preflight(
        declaration,
        CandidatePreflightEvidence(
            source_identity="release-pinned-public-source",
            geometry_source_identity="geometry@sha256:abc",
            response_source_identity="response@sha256:def",
            geometry_response_separable=True,
            coordinate_geometry_present=True,
            node_count=100,
            outer_unit_count=8,
            repeated_node_count=75,
            analysis_registry_closed=True,
        ),
    )


def _predictive_declaration() -> PredictiveComplementarityDeclaration:
    return PredictiveComplementarityDeclaration(
        metric_name="binary_log_loss",
        lower_is_better=True,
        expected_outer_unit_count=8,
        favorable_min_augmented_wins=6,
        adverse_min_baseline_wins=6,
        learner_fit_fingerprint="same-strong-learner-v1",
        response_endpoint_fingerprint="endpoint-3-response-v1",
        split_fingerprint="outer-holdout-v1",
        external_feature_fingerprint="conventional-features-v1",
        eog_feature_fingerprint="symmetric_world_support_summary_v1",
    )


def _estimability():
    declaration = ProspectiveEstimabilityDeclaration(
        calibration_events=10,
        calibration_non_events=40,
        heldout_events=10,
        heldout_non_events=40,
        heldout_outer_units_with_both_classes=1,
    )
    intervals = {
        "calibration_events": AggregateCountInterval(lower=10),
        "calibration_non_events": AggregateCountInterval(lower=40),
        "heldout_events": AggregateCountInterval(lower=10),
        "heldout_non_events": AggregateCountInterval(lower=40),
        "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=1),
    }
    return evaluate_prospective_estimability(
        declaration,
        AggregateEstimabilityEvidence(
            source_label="published response-blind aggregate evidence",
            endpoint_definition_matches=True,
            response_rows_opened=False,
            intervals=intervals,
        ),
    )


def _outcome_contract(predictive: PredictiveComplementarityDeclaration):
    values = {key: f"sha256:{key}" for key in REQUIRED_FREEZE_KEYS}
    values["metrics_decision"] = predictive.fingerprint
    values["layer_b_representation"] = predictive.eog_feature_fingerprint
    return FrozenOutcomeAccessContract("endpoint-3-fresh-v1", values)


def _boundary(**overrides) -> FrozenPaperReadyEndpoint3Boundary:
    values = dict(
        attempt_id="endpoint-3-fresh-v1",
        cross_ecosystem_synthesis_fingerprint=(
            FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT
        ),
        feature_count_placebo_fingerprint=FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT,
    )
    values.update(overrides)
    return FrozenPaperReadyEndpoint3Boundary(**values)


def _ready_inputs():
    candidate = _candidate_declaration()
    predictive = _predictive_declaration()
    outcome_contract = _outcome_contract(predictive)
    outcome_access = evaluate_outcome_access_gate(outcome_contract, _estimability())
    return (
        _boundary(),
        candidate,
        _candidate_result(candidate),
        outcome_contract,
        outcome_access,
        predictive,
    )


def test_complete_identity_bound_receipt_authorizes_only_once_only_runner():
    result = evaluate_paper_ready_endpoint_3_gate(*_ready_inputs())
    assert result.authorized is True
    assert result.status == "ready_for_endpoint_3_once_only_runner"
    assert "exact count gate first" in result.reason


@pytest.mark.parametrize(
    ("boundary", "status"),
    [
        (_boundary(reuses_terminal_candidate=True), "blocked_terminal_candidate_reuse"),
        (_boundary(response_rows_opened=True), "blocked_response_already_opened"),
        (
            _boundary(attempt_id="different-attempt"),
            "blocked_attempt_identity_mismatch",
        ),
        (
            _boundary(cross_ecosystem_synthesis_fingerprint="changed"),
            "blocked_cross_ecosystem_contract_drift",
        ),
        (
            _boundary(feature_count_placebo_fingerprint="changed"),
            "blocked_feature_count_placebo_contract_drift",
        ),
        (
            _boundary(stop_candidate_hunting_after_predictive_terminal=False),
            "blocked_missing_post_terminal_hard_stop",
        ),
    ],
)
def test_paper_boundary_failures_are_explicit(boundary, status):
    values = list(_ready_inputs())
    values[0] = boundary
    result = evaluate_paper_ready_endpoint_3_gate(*values)
    assert result.authorized is False
    assert result.status == status


def test_stopped_candidate_preflight_cannot_be_hidden_by_complete_later_contracts():
    values = list(_ready_inputs())
    declaration = values[1]
    values[2] = evaluate_candidate_preflight(
        declaration,
        CandidatePreflightEvidence(
            source_identity="source",
            geometry_source_identity="same-file",
            response_source_identity="same-file",
            geometry_response_separable=False,
            coordinate_geometry_present=None,
            node_count=None,
            outer_unit_count=None,
            repeated_node_count=None,
            analysis_registry_closed=None,
        ),
    )
    result = evaluate_paper_ready_endpoint_3_gate(*values)
    assert result.status == "blocked_candidate_preflight"


def test_outcome_access_must_be_authorized_and_bound_to_exact_contract():
    values = list(_ready_inputs())
    values[4] = replace(values[4], authorized=False, status="blocked_safety_contract")
    result = evaluate_paper_ready_endpoint_3_gate(*values)
    assert result.status == "blocked_outcome_access"


@pytest.mark.parametrize(
    ("key", "replacement", "status"),
    [
        ("metrics_decision", "detached-decision", "blocked_metrics_decision_binding"),
        ("layer_b_representation", "changed-layer-b", "blocked_layer_b_binding"),
    ],
)
def test_scientific_declarations_must_be_identity_bound(key, replacement, status):
    values = list(_ready_inputs())
    contract = values[3]
    freeze = dict(contract.freeze_fingerprints)
    freeze[key] = replacement
    changed = FrozenOutcomeAccessContract(contract.attempt_id, freeze)
    values[3] = changed
    values[4] = evaluate_outcome_access_gate(changed, _estimability())
    result = evaluate_paper_ready_endpoint_3_gate(*values)
    assert result.status == status


def _canonical_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_frozen_manifest_binds_real_synthesis_placebo_and_hard_stop():
    manifest = json.loads(
        (
            ROOT
            / "validation/paper_ready_replication/frozen_endpoint_3_boundary_manifest.json"
        ).read_text(encoding="utf-8")
    )
    contracts = manifest["contracts"]
    synthesis = contracts["cross_ecosystem_synthesis"]
    placebo = contracts["feature_count_placebo"]
    assert _canonical_json_sha256(ROOT / synthesis["path"]) == synthesis["canonical_sha256"]
    assert _canonical_json_sha256(ROOT / placebo["path"]) == placebo["canonical_sha256"]
    assert synthesis["canonical_sha256"] == FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT
    assert placebo["canonical_sha256"] == FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT
    rules = manifest["endpoint_3_rules"]
    assert rules["stop_candidate_hunting_after_predictive_terminal"] is True
    assert rules["fourth_dataset_for_journal_prestige_allowed"] is False
    assert rules["technical_or_source_stop_is_scientific_null_or_adverse"] is False


def test_validation_facade_exports_gate_without_widening_root_package():
    from eog.v2 import validation

    assert validation.FrozenPaperReadyEndpoint3Boundary is FrozenPaperReadyEndpoint3Boundary
    assert validation.evaluate_paper_ready_endpoint_3_gate is evaluate_paper_ready_endpoint_3_gate

    import eog.v2 as v2

    assert "FrozenPaperReadyEndpoint3Boundary" not in v2.__all__


def test_boundary_types_fail_closed():
    with pytest.raises(TypeError, match="response_rows_opened must be bool"):
        _boundary(response_rows_opened=1)
    with pytest.raises(ValueError, match="attempt_id must be non-empty"):
        _boundary(attempt_id=" ")
    values = list(_ready_inputs())
    values[0] = "bad"
    with pytest.raises(TypeError, match="boundary must be"):
        evaluate_paper_ready_endpoint_3_gate(*values)
