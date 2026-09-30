from eog.v2.bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
)
from eog.v2.bam_future_assay_observation import (
    PARAMETER_FIELDS,
    build_action_supports,
    build_joint_hypotheses,
    exact_minimum_robust_target_design,
    observed_assay_code,
    repeat_equivalence_violations,
)


def _variant(variant_id, coords):
    return ExpandedBAMVariant(
        variant_id=variant_id,
        coordinates=coords,
        abiotic_mask=1,
        biotic_mask=1,
        movement_mask=1,
        occupied_mask=1,
    )


def test_assay_observation_world_mappings_are_frozen():
    c = EcologicalCoordinates(1, 1, 0, -1, 1, 2, 1, 0)
    assert observed_assay_code(c, "A_level", "calibrated") == "1"
    assert observed_assay_code(
        c, "A_level", "systematically_miscalibrated"
    ) == "2"
    assert observed_assay_code(c, "partner_required", "calibrated") == "1"
    assert observed_assay_code(
        c, "partner_required", "systematically_miscalibrated"
    ) == "0"


def test_repeat_same_assay_has_identical_robust_pair_coverage():
    variants = (
        _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(1, 1, 0, 0, 0, 0, 0, 0)),
    )
    target = {"a": False, "b": True}
    hypotheses = build_joint_hypotheses(variants, target)
    actions = build_action_supports(variants, hypotheses)
    assert repeat_equivalence_violations(hypotheses, actions) == 0


def test_calibration_plus_ordinal_assay_restores_robust_target_separation():
    variants = (
        _variant("a", EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(2, 0, 0, 0, 0, 0, 0, 0)),
    )
    target = {"a": False, "b": True}
    hypotheses = build_joint_hypotheses(variants, target)
    actions = build_action_supports(variants, hypotheses)

    assay_only = exact_minimum_robust_target_design(
        hypotheses,
        actions,
        available_action_ids=("assay:A_level",),
    )
    assert assay_only.minimum_action_ids is None

    repeat_only = exact_minimum_robust_target_design(
        hypotheses,
        actions,
        available_action_ids=("assay:A_level", "repeat2:A_level"),
    )
    assert repeat_only.minimum_action_ids is None

    calibrated = exact_minimum_robust_target_design(
        hypotheses,
        actions,
        available_action_ids=("assay:A_level", "assay_process_calibration"),
    )
    assert calibrated.minimum_action_ids == (
        "assay:A_level",
        "assay_process_calibration",
    )
    assert calibrated.minimum_size == 2


def test_full_action_library_can_target_decision_without_world_identification():
    variants = (
        _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)),
        _variant("c", EcologicalCoordinates(1, 1, 0, 0, 0, 0, 0, 0)),
    )
    target = {"a": False, "b": True, "c": True}
    hypotheses = build_joint_hypotheses(variants, target)
    actions = build_action_supports(variants, hypotheses)
    plan = exact_minimum_robust_target_design(hypotheses, actions)
    assert plan.minimum_size is not None
    assert plan.all_target_pairs_separated
    assert set(plan.minimum_action_ids or ()) <= set(actions)
    assert len(PARAMETER_FIELDS) == 8
