from __future__ import annotations

import pytest

from eog.v2.candidate_preflight import (
    CandidatePreflightDeclaration,
    CandidatePreflightEvidence,
    evaluate_candidate_preflight,
)


def declaration() -> CandidatePreflightDeclaration:
    return CandidatePreflightDeclaration(
        attempt_id="fresh-system-v1",
        minimum_nodes=40,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
    )


def registry_declaration() -> CandidatePreflightDeclaration:
    return CandidatePreflightDeclaration(
        attempt_id="fresh-system-registry-v1",
        minimum_nodes=40,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
        require_closed_analysis_registry=True,
    )


def complete_evidence(**overrides) -> CandidatePreflightEvidence:
    values = dict(
        source_identity="archive:v1",
        geometry_source_identity="deployments.csv@sha256:abc",
        response_source_identity="observations.csv@sha256:def",
        geometry_response_separable=True,
        coordinate_geometry_present=True,
        node_count=100,
        outer_unit_count=8,
        repeated_node_count=75,
        layout_design="natural_irregular",
        analysis_registry_closed=None,
        response_rows_opened=False,
        response_bytes_opened=False,
        note="metadata only",
    )
    values.update(overrides)
    return CandidatePreflightEvidence(**values)


def test_ready_candidate_still_requires_geometry_gate():
    result = evaluate_candidate_preflight(declaration(), complete_evidence())
    assert result.status == "ready_for_geometry_gate"
    assert result.ready is True
    assert result.missing_metadata == ()
    assert result.warnings == ()
    assert "structural geometry" in result.reason


def test_incomplete_metadata_never_implies_pass():
    result = evaluate_candidate_preflight(
        declaration(),
        complete_evidence(node_count=None, repeated_node_count=None),
    )
    assert result.status == "incomplete_response_blind_metadata"
    assert result.ready is False
    assert result.missing_metadata == ("node_count", "repeated_node_count")


def test_disabled_requirements_do_not_create_false_missing_metadata():
    decl = CandidatePreflightDeclaration(
        attempt_id="non-coordinate-test",
        minimum_nodes=40,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
        require_separate_geometry_and_response=False,
        require_coordinate_geometry=False,
        require_closed_analysis_registry=False,
    )
    evidence = complete_evidence(
        geometry_response_separable=None,
        coordinate_geometry_present=None,
        analysis_registry_closed=None,
    )
    result = evaluate_candidate_preflight(decl, evidence)
    assert result.status == "ready_for_geometry_gate"
    assert result.missing_metadata == ()


def test_required_registry_closure_unknown_is_incomplete_not_pass():
    result = evaluate_candidate_preflight(
        registry_declaration(),
        complete_evidence(analysis_registry_closed=None),
    )
    assert result.status == "incomplete_response_blind_metadata"
    assert result.ready is False
    assert result.missing_metadata == ("analysis_registry_closed",)


def test_required_registry_known_open_is_hard_stop():
    result = evaluate_candidate_preflight(
        registry_declaration(),
        complete_evidence(analysis_registry_closed=False),
    )
    assert result.status == "stop_analysis_registry_not_closed"
    assert result.ready is False
    assert "one-to-one" in result.reason


def test_required_registry_known_closed_reaches_geometry_gate():
    result = evaluate_candidate_preflight(
        registry_declaration(),
        complete_evidence(analysis_registry_closed=True),
    )
    assert result.status == "ready_for_geometry_gate"
    assert result.ready is True
    assert result.missing_metadata == ()


@pytest.mark.parametrize("field", ["response_rows_opened", "response_bytes_opened"])
def test_any_response_access_stops_preflight(field):
    result = evaluate_candidate_preflight(
        declaration(), complete_evidence(**{field: True})
    )
    assert result.status == "stop_response_already_opened"
    assert result.ready is False


def test_inseparable_geometry_response_stops_before_missing_counts():
    result = evaluate_candidate_preflight(
        declaration(),
        complete_evidence(
            geometry_response_separable=False,
            node_count=None,
            outer_unit_count=None,
            repeated_node_count=None,
        ),
    )
    assert result.status == "stop_inseparable_geometry_response"


def test_missing_coordinate_geometry_is_hard_stop():
    result = evaluate_candidate_preflight(
        declaration(), complete_evidence(coordinate_geometry_present=False)
    )
    assert result.status == "stop_no_response_independent_coordinate_geometry"


@pytest.mark.parametrize(
    ("override", "status"),
    [
        ({"node_count": 39, "repeated_node_count": 30}, "stop_insufficient_nodes"),
        ({"outer_unit_count": 5}, "stop_insufficient_outer_units"),
        ({"repeated_node_count": 29}, "stop_insufficient_repeated_nodes"),
    ],
)
def test_known_count_failures_are_explicit(override, status):
    result = evaluate_candidate_preflight(declaration(), complete_evidence(**override))
    assert result.status == status
    assert result.ready is False


def test_regular_grid_is_warning_not_automatic_stop():
    result = evaluate_candidate_preflight(
        declaration(), complete_evidence(layout_design="regular_grid")
    )
    assert result.status == "ready_for_geometry_gate"
    assert result.warnings == ("regular_grid_structural_scale_collapse_risk",)


def test_linear_layout_warns_but_defers_to_geometry_gate():
    result = evaluate_candidate_preflight(
        declaration(), complete_evidence(layout_design="linear_transect")
    )
    assert result.status == "ready_for_geometry_gate"
    assert result.warnings == ("linear_layout_requires_geometry_gate_for_scale_diversity",)


def test_fingerprints_change_with_scientific_contract_and_evidence():
    d1 = declaration()
    d2 = CandidatePreflightDeclaration(
        attempt_id="fresh-system-v1",
        minimum_nodes=41,
        minimum_outer_units=6,
        minimum_repeated_nodes=30,
    )
    d3 = registry_declaration()
    e1 = complete_evidence()
    e2 = complete_evidence(layout_design="regular_grid")
    e3 = complete_evidence(analysis_registry_closed=True)
    assert d1.fingerprint != d2.fingerprint
    assert d1.fingerprint != d3.fingerprint
    assert e1.fingerprint != e2.fingerprint
    assert e1.fingerprint != e3.fingerprint
    assert evaluate_candidate_preflight(d1, e1).fingerprint != evaluate_candidate_preflight(d1, e2).fingerprint


def test_boolean_and_count_types_fail_closed():
    with pytest.raises(TypeError, match="minimum_nodes must be int"):
        CandidatePreflightDeclaration(
            attempt_id="x",
            minimum_nodes=True,  # type: ignore[arg-type]
            minimum_outer_units=6,
            minimum_repeated_nodes=30,
        )
    with pytest.raises(TypeError, match="require_closed_analysis_registry must be bool"):
        CandidatePreflightDeclaration(
            attempt_id="x",
            minimum_nodes=40,
            minimum_outer_units=6,
            minimum_repeated_nodes=30,
            require_closed_analysis_registry=1,  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="node_count must be int"):
        complete_evidence(node_count=40.0)
    with pytest.raises(TypeError, match="analysis_registry_closed must be bool"):
        complete_evidence(analysis_registry_closed=1)
    with pytest.raises(TypeError, match="response_rows_opened must be bool"):
        complete_evidence(response_rows_opened=1)


def test_contradictory_separable_same_identity_fails_closed():
    with pytest.raises(ValueError, match="contradicts identical"):
        complete_evidence(
            geometry_source_identity="same.csv@sha256:abc",
            response_source_identity="same.csv@sha256:abc",
            geometry_response_separable=True,
        )


def test_repeated_node_count_cannot_exceed_node_count():
    with pytest.raises(ValueError, match="must not exceed node_count"):
        complete_evidence(node_count=50, repeated_node_count=51)


def test_invalid_layout_and_empty_identities_fail_closed():
    with pytest.raises(ValueError, match="unsupported layout_design"):
        complete_evidence(layout_design="hexagonal")
    with pytest.raises(ValueError, match="source_identity must be non-empty"):
        complete_evidence(source_identity="  ")


def test_evaluator_input_types_fail_closed():
    with pytest.raises(TypeError, match="declaration must be"):
        evaluate_candidate_preflight("bad", complete_evidence())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="evidence must be"):
        evaluate_candidate_preflight(declaration(), "bad")  # type: ignore[arg-type]


def test_validation_facade_exports_preflight_without_root_widening():
    from eog.v2 import validation
    from eog.v2.candidate_preflight import CandidatePreflightDeclaration as Decl

    assert validation.CandidatePreflightDeclaration is Decl
    assert validation.evaluate_candidate_preflight is evaluate_candidate_preflight

    import eog.v2 as v2

    assert "CandidatePreflightDeclaration" not in v2.__all__
