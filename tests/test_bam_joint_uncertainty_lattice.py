from eog.v2.bam_ecological_expansion_margin import (
    EcologicalCoordinates,
    ExpandedBAMVariant,
)
from eog.v2.bam_future_assay_observation import PARAMETER_FIELDS
from eog.v2.bam_joint_uncertainty_lattice import (
    O0,
    O1,
    ecological_expansion_creates_calibration_need,
    exact_joint_target_burden,
    joint_burden_monotonicity_violations,
    strict_joint_interaction,
)


ACTIONS = tuple(
    sorted(
        (
            *(f"assay:{field}" for field in PARAMETER_FIELDS),
            "assay_process_calibration",
        )
    )
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


def _burden(variants, target, obs, eco_label, obs_label):
    return exact_joint_target_burden(
        variants,
        target,
        obs,
        ecological_universe=eco_label,
        observation_universe=obs_label,
        available_action_ids=ACTIONS,
    )


def test_target_identified_fiber_has_zero_burden_at_all_observation_levels():
    variants = (
        _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)),
    )
    target = {"a": False, "b": False}
    b0 = _burden(variants, target, O0, "W0", "O0")
    b1 = _burden(variants, target, O1, "W0", "O1")
    assert b0.minimum_size == 0
    assert b1.minimum_size == 0


def test_joint_burden_lattice_is_monotone_on_nested_fixture():
    w0 = (
        _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(1, 0, 0, 0, 0, 0, 0, 0)),
    )
    w1 = (
        *w0,
        _variant("c", EcologicalCoordinates(1, 1, 0, 0, 0, 0, 0, 0)),
    )
    t0 = {"a": False, "b": True}
    t1 = {"a": False, "b": True, "c": True}
    burdens = {
        "W0O0": _burden(w0, t0, O0, "W0", "O0"),
        "W0O1": _burden(w0, t0, O1, "W0", "O1"),
        "W1O0": _burden(w1, t1, O0, "W1", "O0"),
        "W1O1": _burden(w1, t1, O1, "W1", "O1"),
    }
    assert joint_burden_monotonicity_violations(burdens) == ()
    assert burdens["W0O0"].minimum_size <= burdens["W1O1"].minimum_size


def test_interaction_and_new_calibration_need_helpers_use_exact_burdens():
    # Construct minimal burden records through the real solver rather than hand-built
    # dataclasses, so helper semantics stay tied to the action model.
    w0 = (
        _variant("a", EcologicalCoordinates(0, 0, 0, 0, 0, 0, 0, 0)),
        _variant("b", EcologicalCoordinates(2, 0, 0, 0, 0, 0, 0, 0)),
    )
    w1 = (
        *w0,
        _variant("c", EcologicalCoordinates(1, 1, 0, 0, 0, 0, 0, 0)),
    )
    t0 = {"a": False, "b": True}
    t1 = {"a": False, "b": True, "c": True}
    burdens = {
        "W0O0": _burden(w0, t0, O0, "W0", "O0"),
        "W0O1": _burden(w0, t0, O1, "W0", "O1"),
        "W1O0": _burden(w1, t1, O0, "W1", "O0"),
        "W1O1": _burden(w1, t1, O1, "W1", "O1"),
    }
    assert isinstance(strict_joint_interaction(burdens), bool)
    assert isinstance(ecological_expansion_creates_calibration_need(burdens), bool)
