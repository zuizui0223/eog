import pytest

from eog.v2.problem_contract import (
    BaselineFieldSpec,
    CandidateUnit,
    ObservationSemantics,
    fit_numeric_baseline_state,
    freeze_pre_response_problem,
    transform_numeric_baseline_rows,
)


def semantics():
    return ObservationSemantics(
        effort_eligible_rule="effort > 0",
        positive_rule="recorded detection under eligible effort",
        negative_rule="recorded non-detection under eligible effort",
        unsurveyed_rule="effort <= 0 is outside the endpoint",
        zero_interpretation="survey-process non-detection, not biological absence",
    )


def test_normalized_problem_is_response_locked_and_content_addressed():
    units = (
        CandidateUnit("A|t1", "A", "t1", 1),
        CandidateUnit("B|t1", "B", "t1", 2),
    )
    fields = (
        BaselineFieldSpec("elevation", "numeric", "forbid"),
        BaselineFieldSpec("ndvi", "numeric", "calibration_median_plus_indicator"),
    )
    problem = freeze_pre_response_problem(
        node_ids=("A", "B"),
        component_ids=("island1", "island1"),
        context_ids=("t1",),
        candidate_units=units,
        observation_semantics=semantics(),
        baseline_fields=fields,
        split_fingerprint="split-1",
        world_family_fingerprint="worlds-1",
        source_fingerprint="source-1",
    )
    again = freeze_pre_response_problem(
        node_ids=("A", "B"),
        component_ids=("island1", "island1"),
        context_ids=("t1",),
        candidate_units=units,
        observation_semantics=semantics(),
        baseline_fields=fields,
        split_fingerprint="split-1",
        world_family_fingerprint="worlds-1",
        source_fingerprint="source-1",
    )
    assert problem.response_locked is True
    assert problem.fingerprint == again.fingerprint
    assert problem.candidate_units == units


def test_normalized_problem_rejects_unknown_node_or_context():
    with pytest.raises(ValueError, match="unknown node"):
        freeze_pre_response_problem(
            node_ids=("A",),
            component_ids=("x",),
            context_ids=("t1",),
            candidate_units=(CandidateUnit("B|t1", "B", "t1", 1),),
            observation_semantics=semantics(),
            baseline_fields=(),
            split_fingerprint="split",
            world_family_fingerprint="worlds",
            source_fingerprint="source",
        )


def test_optional_numeric_missingness_uses_calibration_median_and_indicator():
    specs = (
        BaselineFieldSpec("latitude", "numeric", "forbid"),
        BaselineFieldSpec("ndvi", "numeric", "calibration_median_plus_indicator"),
    )
    calibration = (
        {"latitude": 1.0, "ndvi": 0.2},
        {"latitude": 2.0, "ndvi": "not available"},
        {"latitude": 3.0, "ndvi": 0.6},
    )
    state = fit_numeric_baseline_state(calibration, specs)
    assert state.median_mapping["ndvi"] == pytest.approx(0.4)
    assert state.feature_names == ("latitude", "ndvi", "ndvi__missing")

    transformed = transform_numeric_baseline_rows(
        (
            {"latitude": 4.0, "ndvi": "bad heldout token"},
            {"latitude": 5.0, "ndvi": 0.9},
        ),
        state,
    )
    assert transformed[0] == pytest.approx((4.0, 0.4, 1.0))
    assert transformed[1] == pytest.approx((5.0, 0.9, 0.0))


def test_required_structural_like_numeric_role_still_fails_closed():
    specs = (BaselineFieldSpec("latitude", "numeric", "forbid"),)
    with pytest.raises(ValueError, match="required numeric"):
        fit_numeric_baseline_state(({"latitude": 1.0}, {"latitude": "NA"}), specs)


def test_all_missing_optional_numeric_role_is_not_silently_invented():
    specs = (BaselineFieldSpec("ndvi", "numeric", "calibration_median_plus_indicator"),)
    with pytest.raises(ValueError, match="all-missing"):
        fit_numeric_baseline_state(({"ndvi": "NA"}, {"ndvi": None}), specs)


def test_invalid_missingness_policy_kind_combination_is_rejected():
    with pytest.raises(ValueError, match="categorical fields"):
        BaselineFieldSpec("habitat", "categorical", "calibration_median_plus_indicator")
