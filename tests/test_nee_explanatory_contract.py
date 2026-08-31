from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

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
    FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT,
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


def _canonical_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _ready_gate_inputs():
    attempt_id = "endpoint-3-nature-frame-v1"
    candidate = CandidatePreflightDeclaration(
        attempt_id=attempt_id,
        minimum_nodes=40,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
        require_closed_analysis_registry=True,
    )
    candidate_result = evaluate_candidate_preflight(
        candidate,
        CandidatePreflightEvidence(
            source_identity="release-pinned-source",
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
    predictive = PredictiveComplementarityDeclaration(
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
    freeze = {key: f"sha256:{key}" for key in REQUIRED_FREEZE_KEYS}
    freeze["metrics_decision"] = predictive.fingerprint
    freeze["layer_b_representation"] = predictive.eog_feature_fingerprint
    outcome_contract = FrozenOutcomeAccessContract(attempt_id, freeze)
    estimability = evaluate_prospective_estimability(
        ProspectiveEstimabilityDeclaration(
            calibration_events=10,
            calibration_non_events=40,
            heldout_events=10,
            heldout_non_events=40,
            heldout_outer_units_with_both_classes=1,
        ),
        AggregateEstimabilityEvidence(
            source_label="published response-blind aggregates",
            endpoint_definition_matches=True,
            response_rows_opened=False,
            intervals={
                "calibration_events": AggregateCountInterval(lower=10),
                "calibration_non_events": AggregateCountInterval(lower=40),
                "heldout_events": AggregateCountInterval(lower=10),
                "heldout_non_events": AggregateCountInterval(lower=40),
                "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=1),
            },
        ),
    )
    outcome_access = evaluate_outcome_access_gate(outcome_contract, estimability)
    boundary = FrozenPaperReadyEndpoint3Boundary(
        attempt_id=attempt_id,
        cross_ecosystem_synthesis_fingerprint=(
            FROZEN_CROSS_ECOSYSTEM_SYNTHESIS_FINGERPRINT
        ),
        feature_count_placebo_fingerprint=FROZEN_FEATURE_COUNT_PLACEBO_FINGERPRINT,
        excluded_world_information_fingerprint=(
            FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT
        ),
    )
    return (
        boundary,
        candidate,
        candidate_result,
        outcome_contract,
        outcome_access,
        predictive,
    )


def test_manifest_binds_exact_excluded_world_explanatory_contract():
    manifest = json.loads(
        (
            ROOT
            / "validation/paper_ready_replication/frozen_endpoint_3_boundary_manifest.json"
        ).read_text(encoding="utf-8")
    )
    entry = manifest["contracts"]["excluded_world_information_explanatory"]
    assert _canonical_json_sha256(ROOT / entry["path"]) == entry["canonical_sha256"]
    assert entry["canonical_sha256"] == FROZEN_EXCLUDED_WORLD_INFORMATION_FINGERPRINT
    rules = manifest["endpoint_3_rules"]
    assert rules["excluded_world_explanatory_may_change_primary_terminal_status"] is False
    assert rules["existing_endpoint_reanalysis_may_upgrade_fresh_claim"] is False


def test_exact_explanatory_contract_allows_ready_receipt():
    result = evaluate_paper_ready_endpoint_3_gate(*_ready_gate_inputs())
    assert result.authorized is True
    assert result.status == "ready_for_endpoint_3_once_only_runner"


def test_explanatory_contract_drift_blocks_endpoint_three_before_response_access():
    values = list(_ready_gate_inputs())
    values[0] = replace(
        values[0],
        excluded_world_information_fingerprint="changed-after-outcome",
    )
    result = evaluate_paper_ready_endpoint_3_gate(*values)
    assert result.authorized is False
    assert result.status == "blocked_excluded_world_information_contract_drift"
    assert "explanatory contract" in result.reason


def test_explanatory_contract_changes_boundary_identity_even_though_primary_is_unchanged():
    boundary = _ready_gate_inputs()[0]
    changed = replace(boundary, excluded_world_information_fingerprint="different")
    assert boundary.fingerprint != changed.fingerprint
