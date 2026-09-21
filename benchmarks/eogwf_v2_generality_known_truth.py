"""Integrated response-independent known-truth check for EOG-WF v2 generality.

This benchmark joins the portability/safety contracts without using any biological
response. It is not a predictive benchmark and cannot alter the closed EOG-WF result.
"""

from __future__ import annotations

import json

import numpy as np

from eog.v2.coordinate_registry import (
    CoordinateObservation,
    CoordinateRegistryPolicy,
    audit_coordinate_registry,
)
from eog.v2.pre_response_certificate import (
    SourceArtifactIdentity,
    fingerprint_world_family,
    freeze_adapter_source_provenance,
    freeze_pre_response_certificate,
)
from eog.v2.predictive_state_gate import (
    PredictiveStateDesign,
    evaluate_predictive_state_design,
)
from eog.v2.problem_contract import (
    CandidateUnit,
    ObservationSemantics,
    freeze_pre_response_problem,
)
from eog.v2.schema_adapter import SchemaAliasContract, SchemaRole
from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)


def _distance_matrix(coordinates: np.ndarray) -> np.ndarray:
    values = np.asarray(coordinates, dtype=float)
    return np.linalg.norm(values[:, None, :] - values[None, :, :], axis=2)


def run_benchmark() -> dict[str, object]:
    schema = SchemaAliasContract(
        roles=(
            SchemaRole("node_id", ("site_id", "SiteID")),
            SchemaRole("x", ("X_WGS84", "x_wgs84")),
            SchemaRole("y", ("Y_WGS84", "y_wgs84")),
        ),
        allow_unmapped_columns=True,
    )
    resolution = schema.resolve(("site_id", "x_wgs84", "y_wgs84", "safe_note"))
    raw_rows = (
        {"site_id": "A", "x_wgs84": 0.000, "y_wgs84": 0.0, "safe_note": "r1"},
        {"site_id": "A", "x_wgs84": 0.004, "y_wgs84": 0.0, "safe_note": "r2"},
        {"site_id": "B", "x_wgs84": 1.000, "y_wgs84": 0.0, "safe_note": "r3"},
        {"site_id": "C", "x_wgs84": 2.000, "y_wgs84": 0.0, "safe_note": "r4"},
        {"site_id": "D", "x_wgs84": 5.000, "y_wgs84": 0.0, "safe_note": "r5"},
    )
    canonical = resolution.canonicalize_records(raw_rows)

    coordinate_audit = audit_coordinate_registry(
        tuple(
            CoordinateObservation(
                str(row["node_id"]),
                float(row["x"]),
                float(row["y"]),
            )
            for row in canonical
        ),
        CoordinateRegistryPolicy(
            tolerance=0.01,
            units="synthetic_native_units",
            representative_policy="median",
        ),
    )

    node_ids = tuple(sorted(coordinate_audit.coordinates))
    coordinates = np.asarray([coordinate_audit.coordinates[node] for node in node_ids])
    distances = _distance_matrix(coordinates)
    ladder = build_structural_scale_ladder(
        node_ids,
        distances,
        StructuralScaleLadderDeclaration(
            axis_id="synthetic_geography",
            target_largest_component_fractions=(0.50, 1.00),
        ),
    )
    worlds = structural_scale_adjacencies(ladder, distances)
    structural_audit = audit_world_universe_structure(
        node_ids,
        worlds,
        horizon=3,
    )
    structural_gate = apply_structural_adequacy_gate(
        structural_audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=0.50,
            require_at_least_one_world_pass=True,
        ),
    )

    safe_design = evaluate_predictive_state_design(
        PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="sequential_preoutcome",
            serve_generator_id="sequential_preoutcome",
            refresh_policy="sequential_context",
            source_policy="symmetric_sources",
            source_label_invariant=True,
            baseline_contains_spatial_coordinates=True,
        )
    )
    tampa_like_design = evaluate_predictive_state_design(
        PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="leave_node_out_static",
            serve_generator_id="common_fold_static",
            refresh_policy="static_reused",
            source_policy="lexicographic_single_source",
            source_label_invariant=False,
            baseline_contains_spatial_coordinates=True,
        )
    )

    world_family_fingerprint = fingerprint_world_family(node_ids, worlds)
    source_bytes = json.dumps(raw_rows, sort_keys=True).encode("utf-8")
    source_provenance = freeze_adapter_source_provenance(
        artifacts=(SourceArtifactIdentity.from_bytes("safe_source", source_bytes),),
        schema_resolution=resolution,
        coordinate_registry=coordinate_audit,
    )
    problem = freeze_pre_response_problem(
        node_ids=node_ids,
        component_ids=tuple("synthetic_component" for _ in node_ids),
        context_ids=("t0",),
        candidate_units=tuple(
            CandidateUnit(
                unit_id=f"{node}|t0",
                node_id=node,
                context_id="t0",
                fold=1 + (index % 2),
            )
            for index, node in enumerate(node_ids)
        ),
        observation_semantics=ObservationSemantics(
            effort_eligible_rule="all synthetic candidate units are effort eligible",
            positive_rule="not opened in this response-independent benchmark",
            negative_rule="not opened in this response-independent benchmark",
            unsurveyed_rule="not used in this benchmark",
            zero_interpretation="no biological response is present",
        ),
        baseline_fields=(),
        split_fingerprint="synthetic-split-v1",
        world_family_fingerprint=world_family_fingerprint,
        source_fingerprint=source_provenance.fingerprint,
    )
    safe_certificate = freeze_pre_response_certificate(
        source_provenance=source_provenance,
        normalized_problem=problem,
        coordinate_registry=coordinate_audit,
        structural_gate=structural_gate,
        world_adjacencies=worlds,
        predictive_state=safe_design,
    )
    tampa_like_certificate = freeze_pre_response_certificate(
        source_provenance=source_provenance,
        normalized_problem=problem,
        coordinate_registry=coordinate_audit,
        structural_gate=structural_gate,
        world_adjacencies=worlds,
        predictive_state=tampa_like_design,
    )

    assert resolution.mapping["x"] == "x_wgs84"
    assert coordinate_audit.status == "within_frozen_tolerance"
    assert coordinate_audit.tolerance_used_node_count == 1
    assert structural_gate.passed is True
    assert safe_design.status == "predictive_complement_candidate"
    assert safe_design.predictive_use_allowed is True
    assert tampa_like_design.status == "ineligible_generation_shift"
    assert tampa_like_design.predictive_use_allowed is False
    assert safe_certificate.structural_response_access_allowed is True
    assert safe_certificate.predictive_outcome_access_allowed is True
    assert safe_certificate.predictive_use_allowed is True
    assert tampa_like_certificate.structural_response_access_allowed is True
    assert tampa_like_certificate.predictive_outcome_access_allowed is False
    assert tampa_like_certificate.predictive_use_allowed is False

    return {
        "schema": "eog.eogwf_v2_generality_known_truth.v1",
        "uses_biological_response": False,
        "counts_as_predictive_evidence": False,
        "schema_adapter": {
            "contract_fingerprint": schema.fingerprint,
            "resolution_fingerprint": resolution.fingerprint,
            "physical_header_fingerprint": resolution.physical_header_fingerprint,
            "mapping": resolution.mapping,
        },
        "coordinate_registry": {
            "status": coordinate_audit.status,
            "tolerance_used_node_count": coordinate_audit.tolerance_used_node_count,
            "fingerprint": coordinate_audit.fingerprint,
        },
        "structural_scale": {
            "thresholds": list(ladder.thresholds),
            "ladder_fingerprint": ladder.fingerprint,
            "world_family_fingerprint": world_family_fingerprint,
            "adequacy_passed": structural_gate.passed,
            "adequacy_fingerprint": structural_gate.fingerprint,
        },
        "source_provenance": {
            "fingerprint": source_provenance.fingerprint,
            "artifact_count": len(source_provenance.artifacts),
        },
        "pre_response_certificate": {
            "safe_status": safe_certificate.structural_status,
            "safe_predictive_status": safe_certificate.predictive_status,
            "safe_structural_response_access_allowed": (
                safe_certificate.structural_response_access_allowed
            ),
            "safe_predictive_outcome_access_allowed": (
                safe_certificate.predictive_outcome_access_allowed
            ),
            "safe_predictive_use_allowed": safe_certificate.predictive_use_allowed,
            "safe_fingerprint": safe_certificate.fingerprint,
            "tampa_like_predictive_status": tampa_like_certificate.predictive_status,
            "tampa_like_structural_response_access_allowed": (
                tampa_like_certificate.structural_response_access_allowed
            ),
            "tampa_like_predictive_outcome_access_allowed": (
                tampa_like_certificate.predictive_outcome_access_allowed
            ),
            "tampa_like_predictive_use_allowed": (
                tampa_like_certificate.predictive_use_allowed
            ),
            "tampa_like_fingerprint": tampa_like_certificate.fingerprint,
        },
        "predictive_state": {
            "safe_status": safe_design.status,
            "tampa_like_status": tampa_like_design.status,
            "safe_fingerprint": safe_design.fingerprint,
            "tampa_like_fingerprint": tampa_like_design.fingerprint,
        },
        "interpretation": (
            "A predeclared physical-schema alias, bounded coordinate drift, "
            "content-addressed source provenance, response-blind structural scale "
            "bracket, structural adequacy gate, and prediction-facing eligibility "
            "decision can be evaluated in one generic pre-response path without "
            "biological outcomes."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_benchmark(), indent=2, sort_keys=True))
