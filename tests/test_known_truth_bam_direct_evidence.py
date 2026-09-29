from eog.v2.known_truth_bam_direct_evidence import (
    bam_state_key,
    group_worlds_by_bam_state,
    run_direct_evidence_v22,
)
from eog.v2.known_truth_bam_v2_1 import build_v21_system


def test_bam_state_equivalence_ignores_parameter_labels_only():
    system = build_v21_system()
    groups = group_worlds_by_bam_state(system.worlds)

    assert groups
    assert sum(len(ids) for ids in groups.values()) == len(system.worlds)
    for key, ids in groups.items():
        assert ids
        assert all(bam_state_key(next(w for w in system.worlds if w.world_id == world_id)) == key for world_id in ids)


def test_direct_evidence_ladder_has_explicit_terminal_verdicts():
    result = run_direct_evidence_v22()

    assert result["candidate_world_count"] == 64
    assert result["eligible_truth_worlds"] == 64
    assert result["state_equivalence_split_violations"] == 0
    assert result["direct_A_failures"] == 0
    assert result["direct_B_failures"] == 0
    assert result["targeted_measurement_reproduction_failures"] == 0
    assert set(result["verdicts"]) == {
        "DE_H1_state_equivalence_honesty",
        "DE_H2_direct_A_contraction",
        "DE_H3_direct_B_contraction",
        "DE_H4_complete_axis_state_recovery",
        "DE_H5_targeted_measurement_efficiency",
    }
    assert len(result["fingerprint"]) == 64


def test_evidence_ladder_does_not_reduce_state_identification():
    result = run_direct_evidence_v22()

    fractions = [
        result["bam_state_unique_fraction_E0"],
        result["bam_state_unique_fraction_E1"],
        result["bam_state_unique_fraction_E2"],
        result["bam_state_unique_fraction_E3"],
        result["bam_state_unique_fraction_E4"],
    ]
    assert all(0.0 <= value <= 1.0 for value in fractions)
    assert all(left <= right for left, right in zip(fractions, fractions[1:]))
