from eog.v2.known_truth_bam_v2_1 import (
    activation_audit_v21,
    build_world_grid_v21,
    run_bam_v21,
)


def test_v21_activation_gate_exercises_all_required_A_B_M_axes():
    worlds = build_world_grid_v21()
    audit = activation_audit_v21(worlds)
    counts = dict(audit.witness_counts)

    assert audit.passed
    assert 0.2 <= audit.partner_fraction <= 0.8
    assert 0.2 <= audit.antagonist_fraction <= 0.8
    assert counts["A_only"] > 0
    assert counts["B_partner_only"] > 0
    assert counts["B_antagonist_only"] > 0
    assert counts["M_distance_only"] > 0
    assert counts["M_barrier_only"] > 0
    assert audit.same_g_different_arrival_pairs > 0
    assert audit.positive_superset_negative_witness_pairs > 0
    assert audit.failed_gates == ()


def test_v21_scores_only_after_activation_pass():
    result = run_bam_v21()

    assert result["status"] == "SCORED"
    assert result["activation_audit"]["failed_gates"] == []
    assert result["candidate_world_count"] == 40
    assert result["eligible_truth_worlds"] > 0
