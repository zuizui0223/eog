import runpy

import pytest


def _benchmark():
    namespace = runpy.run_path("benchmarks/history_matching_nroy_boundary.py")
    return namespace["run_history_matching_nroy_boundary"]()


def test_history_matching_boundary_records_primary_references_and_finite_scope():
    result = _benchmark()
    boundary = result["literature_boundary"]
    assert boundary["method"] == (
        "history matching / Not-Ruled-Out-Yet (NROY) model-space reduction"
    )
    assert boundary["primary_climate_reference"] == (
        "Williamson et al. 2013, Climate Dynamics 41:1703-1729"
    )
    assert boundary["primary_climate_doi"] == "10.1007/s00382-013-1896-4"
    assert boundary["environmental_emulation_reference"] == (
        "Salter et al. 2016, Environmetrics 27:507-523"
    )
    assert boundary["environmental_emulation_doi"] == "10.1002/env.2405"
    assert "deterministic finite worlds" in result["finite_special_case_boundary"]


def test_wave1_history_matching_and_eog_keep_the_same_two_worlds():
    result = _benchmark()
    history = result["history_matching_baseline"]["wave1"]
    eog = result["eog_reconstruction"]

    assert history["observations"] == ["A", "C"]
    assert history["nroy_world_ids"] == ["world_B", "world_D"]
    assert history["ruled_out_world_ids"] == ["world_fail"]
    assert eog["wave1_compatible_world_ids"] == ["world_B", "world_D"]
    assert eog["wave1_incompatible_world_ids"] == ["world_fail"]


def test_adding_B_contracts_both_nroy_and_eog_to_world_B():
    result = _benchmark()
    history = result["history_matching_baseline"]
    eog = result["eog_reconstruction"]

    assert history["wave2"]["observations"] == ["A", "B", "C"]
    assert history["wave2"]["nroy_world_ids"] == ["world_B"]
    assert history["wave2"]["ruled_out_world_ids"] == ["world_D", "world_fail"]
    assert history["eliminated_between_waves"] == ["world_D"]
    assert history["contraction_fraction"] == pytest.approx(0.5)

    assert eog["wave2_compatible_world_ids"] == ["world_B"]
    assert eog["wave2_incompatible_world_ids"] == ["world_D", "world_fail"]
    assert eog["eliminated_between_waves"] == ["world_D"]
    assert eog["contraction_fraction"] == pytest.approx(0.5)
    assert eog["became_identifiable"] is True


def test_finite_nroy_and_eog_compatible_world_filtering_are_exactly_equivalent():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["wave1_nroy_equals_eog_compatible_set"] is True
    assert boundary["wave2_nroy_equals_eog_compatible_set"] is True
    assert boundary["sequential_contraction_matches"] is True


def test_generic_history_matching_operations_are_removed_from_eog_novelty_claim():
    boundary = _benchmark()["negative_boundary"]
    assert boundary["do_not_claim_generic_world_filtering_as_unique"] is True
    assert boundary["do_not_claim_compatible_world_set_as_unique"] is True
    assert boundary["do_not_claim_sequential_world_set_contraction_as_unique"] is True
    assert "biogeographic reachability worlds are declared" in boundary[
        "remaining_eog_question"
    ]
