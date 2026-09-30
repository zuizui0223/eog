from eog.v2.bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
)
from eog.v2.bam_future_target_evidence import (
    PARAMETER_FIELDS,
    exact_future_target_evidence_plan,
    parameter_measurements,
    parameter_target_plan,
)
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    build_generality_system,
)


def _variant(variant_id, coords, A, B, M):
    return ExpandedBAMVariant(
        variant_id=variant_id,
        coordinates=coords,
        abiotic_mask=A,
        biotic_mask=B,
        movement_mask=M,
        occupied_mask=A & B & M,
    )


def test_parameter_library_has_exact_frozen_coordinate_channels():
    system = build_generality_system(SYSTEM_SPECS[0])
    base = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    other = EcologicalCoordinates(1, 1, 1, 1, -1, 1, 1, 1)
    variants = (
        _variant("truth", base, 1, 1, 1),
        _variant("other", other, 1, 1, 1),
    )
    rows = parameter_measurements(variants, ("truth", "other"), "truth")
    assert tuple(row.measurement_id for row in rows) == tuple(
        f"param:{field}" for field in PARAMETER_FIELDS
    )
    assert all("truth" not in row.eliminated_world_ids for row in rows)


def test_state_identical_future_alias_is_not_state_resolvable_but_parameter_resolvable():
    system = build_generality_system(SYSTEM_SPECS[0])
    c0 = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    c1 = EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)
    # Same current A/B/M masks, different latent A_level.
    variants = (
        _variant("truth", c0, 1, 1, 1),
        _variant("alias", c1, 1, 1, 1),
    )
    target = {"truth": False, "alias": True}
    plan = exact_future_target_evidence_plan(
        system,
        variants,
        ("truth", "alias"),
        "truth",
        target,
    )
    assert plan.state_only.minimum_size is None
    assert plan.state_only.evidence_library_sufficient is False
    assert plan.parameter_only.minimum_measurement_ids == ("param:A_level",)
    assert plan.parameter_only.minimum_size == 1
    assert plan.combined.minimum_size == 1


def test_target_specific_parameter_design_can_be_smaller_than_world_identification():
    system = build_generality_system(SYSTEM_SPECS[0])
    truth = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    v1 = EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)
    v2 = EcologicalCoordinates(0, 1, 0, 0, 0, 0, 0, 0)
    variants = (
        _variant("truth", truth, 1, 1, 1),
        _variant("a_alias", v1, 1, 1, 1),
        _variant("b_alias", v2, 1, 1, 1),
    )
    decision_target = {"truth": False, "a_alias": True, "b_alias": False}
    target_plan = exact_future_target_evidence_plan(
        system,
        variants,
        tuple(row.variant_id for row in variants),
        "truth",
        decision_target,
    )
    world_plan = parameter_target_plan(
        variants,
        tuple(row.variant_id for row in variants),
        "truth",
    )
    assert target_plan.parameter_only.minimum_measurement_ids == ("param:A_level",)
    assert target_plan.parameter_only.minimum_size == 1
    assert world_plan.minimum_size == 2
