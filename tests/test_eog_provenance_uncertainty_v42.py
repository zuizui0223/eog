"""Synthetic finite-candidate controls; never downloads biological observations."""
from __future__ import annotations
import math
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks.run_eog_provenance_uncertainty_v42 import (
    deterministic_risk, uncertainty_partition, classify_uncertainty,
)


def test_three_indistinguishable_histories_have_known_entropy_and_error():
    obs = {"a": (), "b": (), "c": ()}
    target = {h: h for h in obs}
    r = deterministic_risk(obs, target)
    assert r["entropy_bits"] == pytest.approx(math.log2(3))
    assert r["bayes_error"] == pytest.approx(2 / 3)


def test_target_compression_uses_target_mass_not_history_mass():
    obs = {"a": (), "b": (), "c": ()}
    t = {"a": "mature", "b": "mature", "c": "young"}
    r = deterministic_risk(obs, t)
    assert r["entropy_bits"] == pytest.approx(-(2/3)*math.log2(2/3)-(1/3)*math.log2(1/3))
    assert r["bayes_error"] == pytest.approx(1/3)
    assert deterministic_risk(t, t) == {"entropy_bits": 0.0, "bayes_error": 0.0}


def test_conditioning_weights_observation_groups_by_probability():
    o = {"a": "one", "b": "one", "c": "two"}
    t = {h: h for h in o}
    assert deterministic_risk(o, t)["entropy_bits"] == pytest.approx(2/3)
    assert deterministic_risk(o, t)["bayes_error"] == pytest.approx(1/3)


def test_exact_telescope_splits_noise_coverage_and_type():
    risks = [
        {"entropy_bits":1.2,"bayes_error":.5},
        {"entropy_bits":.9,"bayes_error":.4},
        {"entropy_bits":.7,"bayes_error":.3},
        {"entropy_bits":.2,"bayes_error":.1},
    ]
    z = uncertainty_partition(*risks)
    assert z["entropy"]["recovered"] == pytest.approx(.3)
    assert z["entropy"]["measurement_loss"] == pytest.approx(.2)
    assert z["entropy"]["site_coverage_loss"] == pytest.approx(.5)
    assert z["entropy"]["source_type_floor"] == pytest.approx(.2)
    assert sum(z["entropy"].values()) == pytest.approx(1.2)
    assert sum(z["error"].values()) == pytest.approx(.5)


def test_structural_floor_can_survive_all_source_measurements():
    constant = {h: () for h in ('a','b','c')}
    t = {"a": 0, "b": 1, "c": 1}
    r = deterministic_risk(constant, t)
    z = uncertainty_partition(r, r, r, r)
    assert z["entropy"]["source_type_floor"] == r["entropy_bits"]
    assert z["entropy"]["measurement_loss"] == 0
    assert z["entropy"]["site_coverage_loss"] == 0
    assert classify_uncertainty(r,r,r,r) == "different_measurement_class_required"


def test_different_targets_not_raw_accuracy_comparison():
    o = {"a": (), "b": (), "c": ()}
    t = {h: "fixed" for h in o}
    r = deterministic_risk(o,t)
    z = uncertainty_partition(r,r,r,r)
    assert all(x == 0 for x in z["entropy"].values())
    assert all(x == 0 for x in z["error"].values())
    assert classify_uncertainty(r,r,r,r) == "target_already_determined_by_occupancy"


def test_impossible_nested_risk_increase_is_rejected():
    b = {"entropy_bits": .2, "bayes_error": .1}
    worse = {"entropy_bits": .3, "bayes_error": .1}
    with pytest.raises(ValueError, match="nested"):
        uncertainty_partition(b,worse,b,b)
    with pytest.raises(ValueError):
        deterministic_risk({"a": ()},{"b": "x"})
    with pytest.raises(ValueError):
        deterministic_risk({}, {})


def test_distinct_resolution_classes_are_exhaustive():
    full={"entropy_bits":1.,"bayes_error":.5}
    part={"entropy_bits":.5,"bayes_error":.25}
    zero={"entropy_bits":0.,"bayes_error":0.}
    assert classify_uncertainty(full,zero,zero,zero)=="selected_noisy_tags_sufficient"
    assert classify_uncertainty(full,part,zero,zero)=="perfect_same_site_tags_sufficient"
    assert classify_uncertainty(full,part,part,zero)=="additional_perfect_source_sites_needed"
