from dataclasses import replace

import numpy as np
import pytest

from eog.v2.coordinate_registry import (
    CoordinateObservation,
    CoordinateRegistryPolicy,
    audit_coordinate_registry,
)
from eog.v2.effort_context import (
    EffortContextRow,
    EffortEligibilityPolicy,
    evidence_fingerprint,
    freeze_effort_context_ledger,
)
from eog.v2.observation_process import BinaryObservationContract
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


def _effort_for(problem):
    return freeze_effort_context_ledger(
        node_ids=problem.node_ids,
        context_ids=problem.context_ids,
        rows=tuple(
            EffortContextRow(
                unit_id=unit.unit_id,
                node_id=unit.node_id,
                context_id=unit.context_id,
                fold=unit.fold,
                eligible=True,
                evidence_summary="frozen test effort",
                evidence_fingerprint=evidence_fingerprint(
                    {"unit_id": unit.unit_id, "eligible": True}
                ),
            )
            for unit in problem.candidate_units
        ),
        policy=EffortEligibilityPolicy(
            unit_definition="node x context",
            eligibility_rule="frozen test effort marks unit surveyed",
            unsurveyed_rule="unsurveyed units are outside endpoint",
            evidence_source="response_independent_effort",
        ),
    )


def _observation():
    return BinaryObservationContract(
        mode="complete_source_zero",
        endpoint_name="synthetic detection",
        positive_semantics="at least one focal event",
        negative_semantics="eligible unit with no focal event after complete source",
        unavailable_semantics="outside frozen scored universe",
        zero_interpretation="recorded non-detection only",
    )


def _fixture(*, source_fingerprint_override=None, structural_pass=True):
    resolution = SchemaAliasContract(
        roles=(
            SchemaRole("node_id", ("site",)),
            SchemaRole("x", ("x",)),
            SchemaRole("y", ("y",)),
        )
    ).resolve(("site", "x", "y"))
    coordinate = audit_coordinate_registry(
        (
            CoordinateObservation("A", 0.0, 0.0),
            CoordinateObservation("B", 1.0, 0.0),
        ),
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="native",
            representative_policy="median",
        ),
    )
    source = freeze_adapter_source_provenance(
        artifacts=(SourceArtifactIdentity.from_bytes("safe", b"safe-source"),),
        schema_resolution=resolution,
        coordinate_registry=coordinate,
    )
    worlds = {
        "connected": np.asarray([[False, True], [True, False]], dtype=bool),
    }
    structural = audit_world_universe_structure(("A", "B"), worlds, horizon=1)
    gate = apply_structural_adequacy_gate(
        structural,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=1.0 if structural_pass else 0.0,
            max_isolated_node_fraction=0.0 if structural_pass else 0.0,
        ),
    )
    if not structural_pass:
        worlds = {
            "disconnected": np.asarray([[False, False], [False, False]], dtype=bool),
        }
        structural = audit_world_universe_structure(("A", "B"), worlds, horizon=1)
        gate = apply_structural_adequacy_gate(
            structural,
            StructuralAdequacyDeclaration(
                min_largest_weak_component_fraction=1.0,
            ),
        )

    problem = freeze_pre_response_problem(
        node_ids=("A", "B"),
        component_ids=("c", "c"),
        context_ids=("t0",),
        candidate_units=(
            CandidateUnit("A|t0", "A", "t0", 1),
            CandidateUnit("B|t0", "B", "t0", 2),
        ),
        observation_semantics=ObservationSemantics(
            effort_eligible_rule="declared",
            positive_rule="locked",
            negative_rule="locked",
            unsurveyed_rule="declared",
            zero_interpretation="declared",
        ),
        baseline_fields=(),
        split_fingerprint="split",
        world_family_fingerprint=fingerprint_world_family(("A", "B"), worlds),
        source_fingerprint=(
            source.fingerprint
            if source_fingerprint_override is None
            else source_fingerprint_override
        ),
    )
    safe = evaluate_predictive_state_design(
        PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="sequential",
            serve_generator_id="sequential",
            refresh_policy="sequential_context",
            source_policy="symmetric_sources",
            source_label_invariant=True,
        )
    )
    unsafe = evaluate_predictive_state_design(
        PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="train_static",
            serve_generator_id="serve_static",
            refresh_policy="static_reused",
            source_policy="lexicographic",
            source_label_invariant=False,
        )
    )
    return source, coordinate, problem, gate, safe, unsafe, worlds


def test_source_artifact_identity_from_bytes_is_exact():
    artifact = SourceArtifactIdentity.from_bytes("safe", b"abc")
    assert artifact.byte_count == 3
    assert artifact.sha256 == (
        "ba7816bf8f01cfea414140de5dae2223"
        "b00361a396177a9cb410ff61f20015ad"
    )


def test_source_artifact_rejects_noninteger_byte_count():
    with pytest.raises(ValueError, match="non-negative integer"):
        SourceArtifactIdentity("bad", 1.5, "0" * 64)


def test_source_provenance_sorts_artifacts_deterministically():
    resolution = SchemaAliasContract(
        roles=(SchemaRole("node_id", ("site",)),)
    ).resolve(("site",))
    coordinate = audit_coordinate_registry(
        (CoordinateObservation("A", 0.0, 0.0),),
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="native",
            representative_policy="median",
        ),
    )
    a = SourceArtifactIdentity.from_bytes("a", b"a")
    b = SourceArtifactIdentity.from_bytes("b", b"b")
    left = freeze_adapter_source_provenance(
        artifacts=(b, a),
        schema_resolution=resolution,
        coordinate_registry=coordinate,
    )
    right = freeze_adapter_source_provenance(
        artifacts=(a, b),
        schema_resolution=resolution,
        coordinate_registry=coordinate,
    )
    assert tuple(x.artifact_id for x in left.artifacts) == ("a", "b")
    assert left.fingerprint == right.fingerprint


def test_safe_predictive_design_is_certified_separately_from_structural_readiness():
    source, coordinate, problem, gate, safe, _, worlds = _fixture()
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=gate,
        world_adjacencies=worlds,
        effort_ledger=_effort_for(problem),
        observation_contract=_observation(),
        predictive_state=safe,
    )
    assert certificate.structural_status == "structural_ready"
    assert certificate.structural_response_access_allowed is True
    assert certificate.predictive_status == "predictive_complement_candidate"
    assert certificate.predictive_outcome_access_allowed is True
    assert certificate.predictive_use_allowed is True


def test_tampa_like_predictive_state_does_not_block_layer_a_response_access():
    source, coordinate, problem, gate, _, unsafe, worlds = _fixture()
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=gate,
        world_adjacencies=worlds,
        effort_ledger=_effort_for(problem),
        observation_contract=_observation(),
        predictive_state=unsafe,
    )
    assert certificate.structural_response_access_allowed is True
    assert certificate.predictive_outcome_access_allowed is False
    assert certificate.predictive_use_allowed is False
    assert certificate.predictive_status == "ineligible_generation_shift"


def test_structural_failure_blocks_response_access_even_with_safe_predictive_design():
    source, coordinate, problem, gate, safe, _, worlds = _fixture(structural_pass=False)
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=gate,
        world_adjacencies=worlds,
        effort_ledger=_effort_for(problem),
        observation_contract=_observation(),
        predictive_state=safe,
    )
    assert certificate.structural_status == "stop_structural_adequacy"
    assert certificate.structural_response_access_allowed is False
    assert certificate.predictive_outcome_access_allowed is False


def test_normalized_problem_must_reference_exact_source_provenance():
    source, coordinate, problem, gate, safe, _, worlds = _fixture(
        source_fingerprint_override="wrong"
    )
    with pytest.raises(ValueError, match="source_fingerprint"):
        freeze_pre_response_certificate(
            source_provenance=source,
            normalized_problem=problem,
            coordinate_registry=coordinate,
            structural_gate=gate,
            world_adjacencies=worlds,
            observation_contract=_observation(),
            predictive_state=safe,
        )


def test_coordinate_registry_must_cover_same_nodes():
    source, _, problem, gate, safe, _, worlds = _fixture()
    coordinate = audit_coordinate_registry(
        (CoordinateObservation("A", 0.0, 0.0),),
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="native",
            representative_policy="median",
        ),
    )
    with pytest.raises(
        ValueError, match="coordinate registry differs from the audit frozen"
    ):
        freeze_pre_response_certificate(
            source_provenance=source,
            normalized_problem=problem,
            coordinate_registry=coordinate,
            structural_gate=gate,
            world_adjacencies=worlds,
            observation_contract=_observation(),
            predictive_state=safe,
        )


def test_coordinate_audit_must_match_source_provenance_fingerprint():
    source, _, problem, gate, safe, _, worlds = _fixture()
    coordinate = audit_coordinate_registry(
        (
            CoordinateObservation("A", 0.0, 0.0),
            CoordinateObservation("B", 1.0, 0.0),
        ),
        CoordinateRegistryPolicy(
            tolerance=0.5,
            units="different-declared-policy",
            representative_policy="mean",
        ),
    )
    with pytest.raises(ValueError, match="differs from the audit frozen"):
        freeze_pre_response_certificate(
            source_provenance=source,
            normalized_problem=problem,
            coordinate_registry=coordinate,
            structural_gate=gate,
            world_adjacencies=worlds,
            observation_contract=_observation(),
            predictive_state=safe,
        )


def test_declared_world_family_must_match_normalized_problem():
    source, coordinate, problem, gate, safe, _, worlds = _fixture()
    altered = {
        "connected": np.asarray([[False, False], [False, False]], dtype=bool),
    }
    with pytest.raises(ValueError, match="world family differs"):
        freeze_pre_response_certificate(
            source_provenance=source,
            normalized_problem=problem,
            coordinate_registry=coordinate,
            structural_gate=gate,
            world_adjacencies=altered,
            effort_ledger=_effort_for(problem),
            observation_contract=_observation(),
            predictive_state=safe,
        )


def test_world_family_fingerprint_preserves_self_loop_identity():
    no_loop = {"w": np.asarray([[0.0, 1.0], [1.0, 0.0]])}
    with_loop = {"w": np.asarray([[0.5, 1.0], [1.0, 0.0]])}
    assert fingerprint_world_family(("A", "B"), no_loop) != fingerprint_world_family(
        ("A", "B"), with_loop
    )


def test_structural_gate_is_reapplied_not_trusted_by_stored_pass_flag():
    source, coordinate, problem, gate, safe, _, worlds = _fixture()
    tampered_gate = replace(gate, passed=False)
    with pytest.raises(ValueError, match="differs from reapplication"):
        freeze_pre_response_certificate(
            source_provenance=source,
            normalized_problem=problem,
            coordinate_registry=coordinate,
            structural_gate=tampered_gate,
            world_adjacencies=worlds,
            observation_contract=_observation(),
            predictive_state=safe,
        )


def test_predictive_outcome_access_requires_machine_readable_observation_contract():
    source, coordinate, problem, gate, safe, _, worlds = _fixture()
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=gate,
        world_adjacencies=worlds,
        effort_ledger=_effort_for(problem),
        predictive_state=safe,
    )
    assert certificate.structural_response_access_allowed is True
    assert certificate.effort_status == "response_independent_effort_declared"
    assert certificate.observation_status == "not_declared"
    assert certificate.predictive_use_allowed is True
    assert certificate.predictive_outcome_access_allowed is False


def test_predictive_outcome_access_requires_response_independent_effort_ledger():
    source, coordinate, problem, gate, safe, _, worlds = _fixture()
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=gate,
        world_adjacencies=worlds,
        observation_contract=_observation(),
        predictive_state=safe,
    )
    assert certificate.structural_response_access_allowed is True
    assert certificate.effort_status == "not_declared"
    assert certificate.observation_status == "complete_source_zero"
    assert certificate.predictive_use_allowed is True
    assert certificate.predictive_outcome_access_allowed is False


def test_world_family_fingerprint_includes_rule_semantics():
    worlds = {"w": np.asarray([[0.0, 1.0], [1.0, 0.0]])}
    immediate = fingerprint_world_family(
        ("A", "B"),
        worlds,
        world_semantics={"w": {"source_mode": "immediate_previous_observed"}},
    )
    historical = fingerprint_world_family(
        ("A", "B"),
        worlds,
        world_semantics={"w": {"source_mode": "cumulative_observed_history"}},
    )
    assert immediate != historical


def test_world_semantics_keys_must_match_declared_worlds():
    worlds = {"w": np.asarray([[0.0, 1.0], [1.0, 0.0]])}
    with pytest.raises(ValueError, match="world_semantics keys"):
        fingerprint_world_family(
            ("A", "B"),
            worlds,
            world_semantics={"other": {"source_mode": "x"}},
        )


def test_structural_adequacy_can_exclude_external_open_world_from_gate():
    source, coordinate, _, _, safe, _, _ = _fixture()
    worlds = {
        "local": np.asarray([[False, False], [False, False]], dtype=bool),
        "external_open": np.asarray([[False, True], [True, False]], dtype=bool),
    }
    semantics = {
        "local": {"kind": "local", "source_mode": "previous"},
        "external_open": {"kind": "external_open"},
    }
    local_audit = audit_world_universe_structure(
        ("A", "B"), {"local": worlds["local"]}, horizon=1
    )
    local_gate = apply_structural_adequacy_gate(
        local_audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=1.0,
        ),
    )
    problem = freeze_pre_response_problem(
        node_ids=("A", "B"),
        component_ids=("c", "c"),
        context_ids=("t0",),
        candidate_units=(
            CandidateUnit("A|t0", "A", "t0", 1),
            CandidateUnit("B|t0", "B", "t0", 2),
        ),
        observation_semantics=ObservationSemantics(
            effort_eligible_rule="declared",
            positive_rule="locked",
            negative_rule="locked",
            unsurveyed_rule="declared",
            zero_interpretation="declared",
        ),
        baseline_fields=(),
        split_fingerprint="split",
        world_family_fingerprint=fingerprint_world_family(
            ("A", "B"), worlds, world_semantics=semantics
        ),
        source_fingerprint=source.fingerprint,
    )
    certificate = freeze_pre_response_certificate(
        source_provenance=source,
        normalized_problem=problem,
        coordinate_registry=coordinate,
        structural_gate=local_gate,
        world_adjacencies=worlds,
        world_semantics=semantics,
        structural_world_ids=("local",),
        observation_contract=_observation(),
        predictive_state=safe,
    )
    assert certificate.structural_status == "stop_structural_adequacy"
    assert certificate.structural_world_ids == ("local",)
    assert certificate.structural_response_access_allowed is False
