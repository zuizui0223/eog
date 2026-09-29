from eog.v2.known_truth_bam_v2_3 import run_bam_intervention_v23


def test_interventions_activate_all_frozen_movement_aliases():
    result = run_bam_intervention_v23()

    assert result["candidate_world_count"] == 64
    assert result["number_of_passive_equivalence_classes"] == 48
    assert result["passive_class_size_distribution"] == {"1": 32, "2": 16}
    assert result["P_only_alias_classes"] == 8
    assert result["H_only_alias_classes"] == 8
    assert result["P_alias_classes_split"] == 8
    assert result["H_alias_classes_split"] == 8
    assert result["I1_failures"] == 0
    assert result["I2_failures"] == 0
    assert result["axis_specificity_violations"] == 0


def test_intervention_augmented_state_is_injective_in_frozen_world_universe():
    result = run_bam_intervention_v23()

    assert result["number_of_intervention_augmented_classes"] == 64
    assert result["intervention_augmented_class_size_distribution"] == {"1": 64}
    assert result["world_fraction_uniquely_identified_after_intervention"] == 1.0
    assert result["verdicts"] == {
        "I1_P_alias_activation": "SUPPORTED",
        "I2_H_alias_activation": "SUPPORTED",
        "I3_axis_specificity": "SUPPORTED",
        "I4_full_parameter_recovery": "SUPPORTED",
    }
