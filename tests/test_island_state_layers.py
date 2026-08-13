import numpy as np
import pytest

from eog.island_state_layers import (
    AreaSupportDeclaration,
    area_support_layers,
    assemble_island_state_layers,
)


def test_area_capture_and_persistence_use_separate_declared_scales():
    result = area_support_layers(
        [0.0, 10.0, 100.0],
        AreaSupportDeclaration(
            capture_half_saturation_area=10.0,
            persistence_half_saturation_area=100.0,
        ),
    )
    assert result.target_capture_support[0] == pytest.approx(0.0)
    assert result.persistence_support[0] == pytest.approx(0.0)
    assert result.target_capture_support[1] == pytest.approx(0.5)
    assert result.persistence_support[2] == pytest.approx(0.5)
    assert result.target_capture_support[1] > result.persistence_support[1]
    assert np.all(np.diff(result.target_capture_support) >= 0.0)
    assert np.all(np.diff(result.persistence_support) >= 0.0)


def test_viability_reachability_mismatch_classes_are_explicit():
    layers = assemble_island_state_layers(
        ("both", "viable_only", "reachable_only", "neither"),
        viability_support=(0.9, 0.9, 0.2, 0.2),
        reachability_support=(0.8, 0.1, 0.8, 0.1),
        persistence_support=(0.7, 0.7, 0.7, 0.7),
        viability_threshold=0.5,
        reachability_threshold=0.5,
    )
    assert layers.state_class == (
        "high_viability_high_reachability",
        "high_viability_low_reachability",
        "low_viability_high_reachability",
        "low_viability_low_reachability",
    )


def test_persistence_does_not_change_viability_reachability_class():
    low_p = assemble_island_state_layers(
        ("island",),
        viability_support=(0.8,),
        reachability_support=(0.8,),
        persistence_support=(0.1,),
        viability_threshold=0.5,
        reachability_threshold=0.5,
    )
    high_p = assemble_island_state_layers(
        ("island",),
        viability_support=(0.8,),
        reachability_support=(0.8,),
        persistence_support=(0.9,),
        viability_threshold=0.5,
        reachability_threshold=0.5,
    )
    assert low_p.state_class == high_p.state_class
    assert low_p.fingerprint != high_p.fingerprint


def test_observation_layer_is_optional_and_separate():
    layers = assemble_island_state_layers(
        ("a", "b"),
        viability_support=(0.6, 0.6),
        reachability_support=(0.6, 0.6),
        persistence_support=(0.6, 0.6),
        observation_support=(0.2, 0.9),
        viability_threshold=0.5,
        reachability_threshold=0.5,
    )
    assert np.array_equal(layers.observation_support, np.array([0.2, 0.9]))
    assert layers.state_class[0] == layers.state_class[1]
