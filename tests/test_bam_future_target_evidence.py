from eog.v2.bam_counterfactual_identifiability import (
    exact_minimum_truth_target_measurements,
)
from eog.v2.bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
    build_expanded_ecological_lattice,
)
from eog.v2.bam_future_target_evidence import (
    PARAMETER_FIELDS,
    exact_future_target_evidence_plan,
    parameter_measurements,
    parameter_target_plan,
)
from eog.v2.bam_structured_counterfactuals import expanded_variant_bam_state_key
from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    build_generality_system,
)


def _variant(variant_id, coords, A=1, B=1, M=1):
    return ExpandedBAMVariant(
        variant_id=variant_id,
        coordinates=coords,
        abiotic_mask=A,
        biotic_mask=B,
        movement_mask=M,
        occupied_mask=A & B & M,
    )


def _real_state_alias_pair(system):
    lattice = build_expanded_ecological_lattice(system)
    groups = {}
    for row in lattice:
        key = expanded_variant_bam_state_key(system, row)
        groups.setdefault(key, []).append(row)
    for rows in groups.values():
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda row: row.variant_id)
        truth = ordered[0]
        for alias in ordered[1:]:
            if alias.coordinates != truth.coordinates:
                return truth, alias
    raise AssertionError("expected at least one parameter alias with identical current state")


def test_parameter_library_has_exact_frozen_coordinate_channels():
    base = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    other = EcologicalCoordinates(1, 1, 1, 1, -1, 1, 1, 1)
    variants = (
        _variant("truth", base),
        _variant("other", other),
    )
    rows = parameter_measurements(variants, ("truth", "other"), "truth")
    assert tuple(row.measurement_id for row in rows) == tuple(
        f"param:{field}" for field in PARAMETER_FIELDS
    )
    assert all("truth" not in row.eliminated_world_ids for row in rows)


def test_state_identical_future_alias_is_not_state_resolvable_but_parameter_resolvable():
    system = build_generality_system(SYSTEM_SPECS[0])
    truth, alias = _real_state_alias_pair(system)
    variants = (truth, alias)
    assert truth.occupied_mask == alias.occupied_mask
    assert expanded_variant_bam_state_key(system, truth) == expanded_variant_bam_state_key(
        system, alias
    )

    target = {truth.variant_id: False, alias.variant_id: True}
    plan = exact_future_target_evidence_plan(
        system,
        variants,
        (truth.variant_id, alias.variant_id),
        truth.variant_id,
        target,
    )
    assert plan.state_only.minimum_size is None
    assert plan.state_only.evidence_library_sufficient is False
    assert plan.parameter_only.minimum_size == 1
    assert plan.parameter_only.evidence_library_sufficient is True
    assert plan.combined.minimum_size == 1


def test_target_specific_parameter_design_can_be_smaller_than_world_identification():
    truth = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    v1 = EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)
    v2 = EcologicalCoordinates(0, 1, 0, 0, 0, 0, 0, 0)
    variants = (
        _variant("truth", truth),
        _variant("a_alias", v1),
        _variant("b_alias", v2),
    )
    ids = tuple(row.variant_id for row in variants)
    decision_target = {"truth": False, "a_alias": True, "b_alias": False}
    measurements = parameter_measurements(variants, ids, "truth")
    target_plan = exact_minimum_truth_target_measurements(
        ids,
        "truth",
        decision_target,
        measurements,
    )
    world_plan = parameter_target_plan(
        variants,
        ids,
        "truth",
    )
    assert target_plan.minimum_measurement_ids == ("param:A_level",)
    assert target_plan.minimum_size == 1
    assert world_plan.minimum_size == 2
