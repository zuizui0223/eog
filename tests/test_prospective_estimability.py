import pytest

from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
    prospective_estimability_disposition,
)


def _declaration():
    return ProspectiveEstimabilityDeclaration(
        calibration_events=10,
        calibration_non_events=40,
        heldout_events=10,
        heldout_non_events=40,
        heldout_outer_units_with_both_classes=4,
    )


def test_pass_requires_all_published_lower_bounds_to_clear_frozen_minima():
    evidence = AggregateEstimabilityEvidence(
        source_label="published aggregate table",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=20),
            "calibration_non_events": AggregateCountInterval(lower=100),
            "heldout_events": AggregateCountInterval(lower=12),
            "heldout_non_events": AggregateCountInterval(lower=70),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=5),
        },
    )
    result = evaluate_prospective_estimability(_declaration(), evidence)
    assert result.status == "plausibly_eligible_pre_response"
    assert result.failing_keys == ()
    assert result.unresolved_keys == ()
    assert (
        prospective_estimability_disposition(result)
        == "continue_response_blind_with_pre_response_support"
    )


def test_known_upper_bound_below_minimum_stops_candidate_pre_response():
    evidence = AggregateEstimabilityEvidence(
        source_label="published event counts",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(upper=8),
            "calibration_non_events": AggregateCountInterval(lower=100),
            "heldout_events": AggregateCountInterval(lower=20),
            "heldout_non_events": AggregateCountInterval(lower=80),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=5),
        },
    )
    result = evaluate_prospective_estimability(_declaration(), evidence)
    assert result.status == "ineligible_pre_response"
    assert result.failing_keys == ("calibration_events",)
    assert prospective_estimability_disposition(result) == "stop_known_ineligible_pre_response"


def test_missing_lower_bound_is_uncertain_not_silent_pass():
    evidence = AggregateEstimabilityEvidence(
        source_label="abstract-only reporting",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=20),
        },
    )
    result = evaluate_prospective_estimability(_declaration(), evidence)
    assert result.status == "uncertain_pre_response"
    assert "heldout_events" in result.unresolved_keys
    assert (
        prospective_estimability_disposition(result)
        == "continue_response_blind_exact_gate_required"
    )


def test_mismatched_endpoint_definition_is_uncertain_even_with_large_counts():
    evidence = AggregateEstimabilityEvidence(
        source_label="different endpoint",
        endpoint_definition_matches=False,
        response_rows_opened=False,
        intervals={key: AggregateCountInterval(lower=1000) for key in (
            "calibration_events",
            "calibration_non_events",
            "heldout_events",
            "heldout_non_events",
            "heldout_outer_units_with_both_classes",
        )},
    )
    result = evaluate_prospective_estimability(_declaration(), evidence)
    assert result.status == "uncertain_pre_response"
    assert len(result.unresolved_keys) == 5
    assert (
        prospective_estimability_disposition(result)
        == "continue_response_blind_exact_gate_required"
    )


def test_uncertain_disposition_never_turns_uncertainty_into_pass():
    evidence = AggregateEstimabilityEvidence(
        source_label="partial published counts",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=10),
            "heldout_events": AggregateCountInterval(lower=10),
        },
    )
    result = evaluate_prospective_estimability(_declaration(), evidence)
    assert result.status == "uncertain_pre_response"
    assert result.unresolved_keys
    assert (
        prospective_estimability_disposition(result)
        == "continue_response_blind_exact_gate_required"
    )
    # Continuing response-blind work does not authorize outcome access or erase the
    # unresolved evidence state; the exact once-only gate remains downstream.
    assert result.status != "plausibly_eligible_pre_response"


def test_response_opened_evidence_is_rejected():
    with pytest.raises(ValueError, match="before row-level response access"):
        AggregateEstimabilityEvidence(
            source_label="post-open counts",
            endpoint_definition_matches=True,
            response_rows_opened=True,
            intervals={},
        )


def test_invalid_intervals_and_unknown_keys_are_rejected():
    with pytest.raises(ValueError, match="cannot exceed"):
        AggregateCountInterval(lower=5, upper=4)

    with pytest.raises(ValueError, match="unsupported"):
        AggregateEstimabilityEvidence(
            source_label="bad key",
            endpoint_definition_matches=True,
            response_rows_opened=False,
            intervals={"auc": AggregateCountInterval(lower=1)},
        )


def test_disposition_rejects_non_result_input():
    with pytest.raises(TypeError, match="ProspectiveEstimabilityResult"):
        prospective_estimability_disposition("uncertain_pre_response")  # type: ignore[arg-type]


def test_same_inputs_have_deterministic_fingerprint():
    evidence = AggregateEstimabilityEvidence(
        source_label="published counts",
        endpoint_definition_matches=True,
        response_rows_opened=False,
        intervals={
            "calibration_events": AggregateCountInterval(lower=11),
            "calibration_non_events": AggregateCountInterval(lower=41),
            "heldout_events": AggregateCountInterval(lower=11),
            "heldout_non_events": AggregateCountInterval(lower=41),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=4),
        },
        note="fixed before response",
    )
    a = evaluate_prospective_estimability(_declaration(), evidence)
    b = evaluate_prospective_estimability(_declaration(), evidence)
    assert a.fingerprint == b.fingerprint
