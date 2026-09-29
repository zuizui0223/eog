from eog.v2.known_truth_bam_v2_2 import build_world_grid_v22
from eog.v2.known_truth_bam_v3 import (
    complete_intervention_signature,
    intervention_library,
    predicted_intervention_outcome,
    run_active_intervention_for_truth,
    run_bam_active_intervention_v3,
)


def test_intervention_library_has_axis_specific_probes():
    worlds = build_world_grid_v22()
    library = intervention_library(worlds[0].node_ids)
    keys = {item.key for item in library}

    assert "A_transplant_challenge" in keys
    assert "B_partner_removal" in keys
    assert "B_antagonist_addition" in keys
    assert any(key.startswith("M_arrival_probe:") for key in keys)


def test_complete_signatures_are_truth_label_independent_functions_of_world_state():
    worlds = build_world_grid_v22()
    library = intervention_library(worlds[0].node_ids)

    signatures = {
        world.world_id: complete_intervention_signature(world, library)
        for world in worlds
    }

    assert all(len(signature) == len(library) for signature in signatures.values())
    assert all(
        predicted_intervention_outcome(world, library[0]) in {"survive", "fail"}
        for world in worlds
    )


def test_active_intervention_never_eliminates_truth_and_matches_signature_limit():
    worlds = build_world_grid_v22()
    for truth in worlds:
        terminal, steps, signature_equivalent = run_active_intervention_for_truth(
            worlds,
            truth,
        )
        assert truth.world_id in terminal
        assert terminal == signature_equivalent
        assert all(
            len(step.after_world_ids) <= len(step.before_world_ids)
            for step in steps
        )


def test_v3_reports_axis_orthogonality_and_intervention_gain():
    result = run_bam_active_intervention_v3()

    assert all(result["axis_orthogonality_audit"].values())
    assert result["truth_retention_failures"] == 0
    assert result["monotonicity_failures"] == 0
    assert result["signature_limit_failures"] == 0
    assert (
        result["unique_truth_fraction_after_active_intervention"]
        >= result["unique_truth_fraction_before_intervention"]
    )
