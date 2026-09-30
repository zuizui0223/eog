import math

from eog.v2.bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
)
from eog.v2.bam_stochastic_assay_risk import (
    FIELD_DOMAINS,
    bhattacharyya_affinity,
    categorical_assay_kernel,
    minimum_repeat_plan,
    single_assay_affinity,
    worst_target_pair_risk,
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


def test_categorical_kernel_is_full_support_and_normalized():
    for field, domain in FIELD_DOMAINS.items():
        kernel = categorical_assay_kernel(field, domain[0], 0.7)
        assert set(kernel) == set(domain)
        assert all(value > 0 for value in kernel.values())
        assert math.isclose(sum(kernel.values()), 1.0)


def test_affinity_is_one_for_identical_distribution_and_below_one_for_distinct_truths():
    coords0 = EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)
    coords1 = EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)
    same = single_assay_affinity(
        coords0, "moderate_accuracy", coords0, "moderate_accuracy", "A_level"
    )
    different = single_assay_affinity(
        coords0, "moderate_accuracy", coords1, "moderate_accuracy", "A_level"
    )
    assert math.isclose(same, 1.0)
    assert 0.0 < different < 1.0


def test_repetition_reduces_pairwise_bound_but_not_exact_support_overlap():
    a = _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0))
    b = _variant("b", EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0))
    target = {"a": False, "b": True}
    one = worst_target_pair_risk(
        (a, b), target, ("A_level",), repeat_depth=1, quality_calibrated=False
    )
    five = worst_target_pair_risk(
        (a, b), target, ("A_level",), repeat_depth=5, quality_calibrated=False
    )
    assert 0 < five.worst_bhattacharyya_affinity < one.worst_bhattacharyya_affinity < 1
    plan = minimum_repeat_plan((a, b), target, ("A_level",), repeat_cap=30)
    assert plan.exact_robust_separation_possible_finite_repeats is False
    assert plan.quality_calibration_min_repeat is not None


def test_quality_calibration_can_only_improve_worst_pair_bound():
    a = _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0))
    b = _variant("b", EcologicalCoordinates(1, 1, 0, 0, 0, 0, 0, 0))
    target = {"a": False, "b": True}
    no_cal = worst_target_pair_risk(
        (a, b),
        target,
        ("A_level", "partner_required"),
        repeat_depth=2,
        quality_calibrated=False,
    )
    calibrated = worst_target_pair_risk(
        (a, b),
        target,
        ("A_level", "partner_required"),
        repeat_depth=2,
        quality_calibrated=True,
    )
    assert calibrated.worst_pair_error_upper_bound <= no_cal.worst_pair_error_upper_bound


def test_bhattacharyya_affinity_is_symmetric():
    p = {0: 0.7, 1: 0.3}
    q = {0: 0.3, 1: 0.7}
    assert math.isclose(
        bhattacharyya_affinity(p, q),
        bhattacharyya_affinity(q, p),
    )
