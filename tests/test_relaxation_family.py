import pytest

from eog.dynamic_island_reachability import DynamicReachabilityEdge, build_dynamic_transition_operator
from eog.v2.relaxation_family import (
    build_monotone_relaxation_family,
    infer_basin_merge,
)
from eog.v2.world_reconstruction import FiniteWorld


NODE_IDS = ("A", "B", "C", "D")


def _operator(edges):
    return build_dynamic_transition_operator(
        NODE_IDS,
        [DynamicReachabilityEdge(source=a, target=b, geographic_support=1.0) for a, b in edges],
        loss_support=1.0,
    )


def _world(world_id, variant, level, edges):
    return FiniteWorld(
        world_id,
        _operator(edges),
        ("A",),
        environmental_relaxation=level,
        analytical_variant=variant,
    )


def _family():
    return build_monotone_relaxation_family(
        "declared_env_relaxation",
        {
            0.0: {
                "fine": _world("fine-l0", "fine", 0.0, ((0, 1),)),
                "coarse": _world("coarse-l0", "coarse", 0.0, ((0, 1),)),
            },
            1.0: {
                "fine": _world("fine-l1", "fine", 1.0, ((0, 1), (1, 2))),
                "coarse": _world("coarse-l1", "coarse", 1.0, ((0, 1),)),
            },
            2.0: {
                "fine": _world("fine-l2", "fine", 2.0, ((0, 1), (1, 2))),
                "coarse": _world("coarse-l2", "coarse", 2.0, ((0, 1), (1, 2))),
            },
        },
    )


def test_basin_merge_separates_first_possible_from_first_robust_level():
    family = _family()
    result = infer_basin_merge(
        family,
        {"upstream": ("A", "B"), "downstream": ("C",)},
        max_steps=3,
    )

    assert family.levels == (0.0, 1.0, 2.0)
    assert family.analytical_variants == ("coarse", "fine")
    assert result.first_possible_level == pytest.approx(1.0)
    assert result.first_robust_level == pytest.approx(2.0)
    assert result.possible_but_variant_dependent is True
    assert result.never_possible is False
    assert result.never_robust is False
    assert result.coverage_certificate == "exhaustive_declared_monotone_family_and_variants"

    by_level = {row.level: row for row in result.level_results}
    assert by_level[0.0].possible is False
    assert by_level[0.0].robust is False
    assert by_level[1.0].compatible_variants == ("fine",)
    assert by_level[1.0].incompatible_variants == ("coarse",)
    assert by_level[1.0].possible is True
    assert by_level[1.0].robust is False
    assert by_level[2.0].compatible_variants == ("coarse", "fine")
    assert by_level[2.0].robust is True


def test_family_does_not_create_lambda_from_component_weights():
    family = _family()
    fine_l1 = family.worlds_at(1.0)[1]

    assert fine_l1.environmental_relaxation == pytest.approx(1.0)
    assert fine_l1.geographic_relaxation == pytest.approx(0.0)
    assert fine_l1.barrier_relaxation == pytest.approx(0.0)
    with pytest.raises(KeyError):
        family.worlds_at(1.5)


def test_family_rejects_negative_relaxation_levels():
    with pytest.raises(ValueError, match="finite and non-negative"):
        build_monotone_relaxation_family(
            "negative",
            {
                -1.0: {
                    "reference": _world("reference-neg", "reference", 0.0, ((0, 1),))
                },
                0.0: {
                    "reference": _world("reference-zero", "reference", 0.0, ((0, 1),))
                },
            },
        )


def test_monotone_family_rejects_transition_support_that_disappears_at_higher_lambda():
    with pytest.raises(ValueError, match="non-decreasing"):
        build_monotone_relaxation_family(
            "bad",
            {
                0.0: {
                    "reference": _world(
                        "reference-l0", "reference", 0.0, ((0, 1), (1, 2))
                    )
                },
                1.0: {
                    "reference": _world("reference-l1", "reference", 1.0, ((0, 1),))
                },
            },
        )


def test_family_requires_the_same_analytical_variants_at_every_level():
    with pytest.raises(ValueError, match="same analytical variants"):
        build_monotone_relaxation_family(
            "incomplete",
            {
                0.0: {
                    "fine": _world("fine-l0", "fine", 0.0, ((0, 1),)),
                    "coarse": _world("coarse-l0", "coarse", 0.0, ((0, 1),)),
                },
                1.0: {
                    "fine": _world("fine-l1", "fine", 1.0, ((0, 1), (1, 2))),
                },
            },
        )


def test_basin_groups_must_be_disjoint_and_include_declared_source_in_union():
    family = _family()
    with pytest.raises(ValueError, match="disjoint"):
        infer_basin_merge(
            family,
            {"g1": ("A", "B"), "g2": ("B", "C")},
            max_steps=3,
        )

    with pytest.raises(ValueError, match="observed fixed sources"):
        infer_basin_merge(
            family,
            {"g1": ("B",), "g2": ("C",)},
            max_steps=3,
        )
