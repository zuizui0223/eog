from eog.v2.known_truth_bam_v2_2 import (
    activation_audit_v22,
    build_world_grid_v22,
    run_bam_v22,
)


def test_v22_activation_requires_all_B_modes_as_truth_and_distinct_masks():
    worlds = build_world_grid_v22()
    audit = activation_audit_v22(worlds)

    assert audit.passed
    assert audit.focal_source_in_partner
    assert audit.biotic_masks_pairwise_distinct
    assert 0.2 <= audit.partner_fraction <= 0.8
    assert 0.2 <= audit.antagonist_fraction <= 0.8
    assert all(count > 0 for _, count in audit.eligible_truth_counts_by_B)
    assert all(count > 0 for _, count in audit.eligible_truth_counts_by_A)
    assert all(count > 0 for _, count in audit.eligible_truth_counts_by_M)
    assert all(count > 0 for _, count in audit.witness_counts)
    assert audit.same_g_different_arrival_pairs > 0
    assert audit.positive_superset_negative_witness_pairs > 0
    assert audit.failed_gates == ()


def test_v22_partner_truth_is_actually_scored():
    result = run_bam_v22()

    assert result["status"] == "SCORED"
    assert result["partner_dependency_diagnostic_cases"] > 0
    assert result["antagonist_dependency_diagnostic_cases"] > 0
    assert result["eligible_truth_worlds"] > 20
