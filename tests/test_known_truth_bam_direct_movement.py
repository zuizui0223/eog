from eog.v2.known_truth_bam_direct_movement import run_direct_movement_v23


def test_direct_movement_ladder_has_explicit_verdicts():
    result = run_direct_movement_v23()

    assert result["candidate_world_count"] == 64
    assert result["eligible_truth_worlds"] == 64
    assert result["M_accessibility_failures"] == 0
    assert result["M_arrival_failures"] == 0
    assert result["parameter_alias_split_violations"] == 0
    assert result["targeted_M_reproduction_failures"] == 0
    assert set(result["verdicts"]) == {
        "DM_H1_M_accessibility_contraction",
        "DM_H2_M_arrival_contraction",
        "DM_H3_complete_BAM_state_recovery",
        "DM_H4_parameter_alias_honesty",
        "DM_H5_targeted_M_efficiency",
    }
    assert len(result["fingerprint"]) == 64


def test_direct_movement_evidence_is_monotone_for_bam_state_identification():
    result = run_direct_movement_v23()

    fractions = [
        result["bam_state_unique_fraction_E4"],
        result["bam_state_unique_fraction_E5"],
        result["bam_state_unique_fraction_E6"],
    ]
    assert all(0.0 <= value <= 1.0 for value in fractions)
    assert fractions[0] <= fractions[1] <= fractions[2]
