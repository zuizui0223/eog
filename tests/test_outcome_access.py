import pytest

from eog.v2.outcome_access import (
    REQUIRED_FREEZE_KEYS,
    FrozenOutcomeAccessContract,
    evaluate_outcome_access_gate,
)
from eog.v2.prospective_estimability import (
    AggregateCountInterval,
    AggregateEstimabilityEvidence,
    ProspectiveEstimabilityDeclaration,
    evaluate_prospective_estimability,
)


def _declaration():
    return ProspectiveEstimabilityDeclaration(
        calibration_events=10,
        calibration_non_events=40,
        heldout_events=10,
        heldout_non_events=40,
        heldout_outer_units_with_both_classes=1,
    )


def _estimability(status):
    if status == "plausible":
        intervals = {
            "calibration_events": AggregateCountInterval(lower=10),
            "calibration_non_events": AggregateCountInterval(lower=40),
            "heldout_events": AggregateCountInterval(lower=10),
            "heldout_non_events": AggregateCountInterval(lower=40),
            "heldout_outer_units_with_both_classes": AggregateCountInterval(lower=1),
        }
    elif status == "ineligible":
        intervals = {
            "calibration_events": AggregateCountInterval(upper=8),
        }
    elif status == "uncertain":
        intervals = {
            "calibration_events": AggregateCountInterval(lower=10),
        }
    else:
        raise ValueError(status)
    return evaluate_prospective_estimability(
        _declaration(),
        AggregateEstimabilityEvidence(
            source_label="frozen published aggregate evidence",
            endpoint_definition_matches=True,
            response_rows_opened=False,
            intervals=intervals,
        ),
    )


def _freeze_map():
    return {key: f"sha256:{key}" for key in REQUIRED_FREEZE_KEYS}


def test_uncertain_candidate_can_authorize_once_only_count_gate_after_full_freeze():
    result = evaluate_outcome_access_gate(
        FrozenOutcomeAccessContract("fresh-system-001", _freeze_map()),
        _estimability("uncertain"),
    )
    assert result.authorized is True
    assert result.status == "authorized_once_only_exact_count_gate_required"
    assert result.prospective_disposition == "continue_response_blind_exact_gate_required"
    assert result.missing_freeze_keys == ()
    assert result.exact_count_gate_first is True
    assert result.zero_fit_on_count_failure is True


def test_plausibly_eligible_candidate_still_requires_same_once_only_count_gate():
    result = evaluate_outcome_access_gate(
        FrozenOutcomeAccessContract("fresh-system-002", _freeze_map()),
        _estimability("plausible"),
    )
    assert result.authorized is True
    assert result.status == "authorized_once_only_exact_count_gate_required"
    assert result.prospective_disposition == "continue_response_blind_with_pre_response_support"


def test_known_ineligible_candidate_is_blocked_even_with_complete_freeze():
    result = evaluate_outcome_access_gate(
        FrozenOutcomeAccessContract("fresh-system-003", _freeze_map()),
        _estimability("ineligible"),
    )
    assert result.authorized is False
    assert result.status == "blocked_known_ineligible_pre_response"


def test_missing_freeze_blocks_outcome_access_and_names_missing_key():
    freeze_map = _freeze_map()
    del freeze_map["comparators"]
    result = evaluate_outcome_access_gate(
        FrozenOutcomeAccessContract("fresh-system-004", freeze_map),
        _estimability("uncertain"),
    )
    assert result.authorized is False
    assert result.status == "blocked_incomplete_freeze_contract"
    assert result.missing_freeze_keys == ("comparators",)


def test_safety_invariant_false_blocks_outcome_access():
    result = evaluate_outcome_access_gate(
        FrozenOutcomeAccessContract(
            "fresh-system-005",
            _freeze_map(),
            zero_fit_on_count_failure=False,
        ),
        _estimability("uncertain"),
    )
    assert result.authorized is False
    assert result.status == "blocked_safety_contract"


def test_contract_cannot_be_created_after_response_rows_are_opened():
    with pytest.raises(ValueError, match="before row-level response access"):
        FrozenOutcomeAccessContract(
            "fresh-system-006",
            _freeze_map(),
            response_rows_opened=True,
        )


def test_unknown_freeze_key_is_rejected():
    values = _freeze_map()
    values["posthoc_tuning"] = "bad"
    with pytest.raises(ValueError, match="unsupported outcome-access freeze keys"):
        FrozenOutcomeAccessContract("fresh-system-007", values)


def test_gate_fingerprint_is_deterministic():
    contract = FrozenOutcomeAccessContract("fresh-system-008", _freeze_map())
    estimability = _estimability("uncertain")
    a = evaluate_outcome_access_gate(contract, estimability)
    b = evaluate_outcome_access_gate(contract, estimability)
    assert a.fingerprint == b.fingerprint
    assert a.contract_fingerprint == b.contract_fingerprint
