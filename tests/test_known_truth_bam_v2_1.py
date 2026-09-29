from eog.v2.known_truth_bam_v2_1 import (
    audit_v21_activation,
    build_v21_system,
    run_bam_v21,
)


def test_v21_activation_must_pass_before_scoring():
    system = build_v21_system()
    receipt = audit_v21_activation(system)

    assert receipt.status == "PASS"
    assert 0.20 < receipt.partner_fraction < 0.80
    assert 0.20 < receipt.antagonist_fraction < 0.80
    assert receipt.A_only_pairs > 0
    assert receipt.partner_B_only_pairs > 0
    assert receipt.antagonist_B_only_pairs > 0
    assert receipt.M_distance_only_pairs > 0
    assert receipt.M_barrier_only_pairs > 0
    assert receipt.same_G_different_arrival_pairs > 0
    assert receipt.positive_superset_negative_witness_pairs > 0
    assert receipt.failed_gates == ()


def test_v21_bam_scoring_runs_only_after_activation_pass():
    result = run_bam_v21()

    assert result["status"] == "SCORED"
    assert result["activation"]["status"] == "PASS"
    assert result["scoring_performed"] is True
    assert result["candidate_world_count"] == 64
    assert result["truth_retention_failures"] == 0
    assert result["axis_witness_mismatches"] == 0
    assert result["equivalence_violations"] == 0
    assert result["positive_superset_violations"] == 0
    assert result["negative_rescue_failures"] == 0
    assert result["temporal_rescue_failures"] == 0
    expected_keys = {
        "BAM_H1_truth_retention",
        "BAM_H2_axis_witness_attribution",
        "BAM_H3_intersection_nonidentifiability",
        "BAM_H4_positive_superset_ceiling",
        "BAM_H5_perfect_negative_rescue",
        "BAM_H6_temporal_M_rescue",
    }
    assert set(result["verdicts"]) == expected_keys
    assert all(
        verdict in {"SUPPORTED", "REFUTED", "NOT_TESTED"}
        for verdict in result["verdicts"].values()
    )
