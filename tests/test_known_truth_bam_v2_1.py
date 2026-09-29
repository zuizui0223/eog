from eog.v2.known_truth_bam_v2_1 import (
    audit_v21_activation,
    build_v21_system,
    run_bam_v21,
)


def test_v21_activation_is_checked_before_scoring():
    system = build_v21_system()
    receipt = audit_v21_activation(system)

    assert receipt.status in {"PASS", "DESIGN_STOP"}
    assert 0.0 <= receipt.partner_fraction <= 1.0
    assert 0.0 <= receipt.antagonist_fraction <= 1.0
    assert len(receipt.fingerprint) == 64


def test_v21_truth_worlds_preserve_explicit_bam_intersection():
    system = build_v21_system()

    assert len(system.worlds) == 64
    for world in system.worlds:
        assert world.occupied_mask == (
            world.abiotic_mask & world.biotic_mask & world.movement_mask
        )


def test_v21_terminal_result_obeys_activation_gate():
    result = run_bam_v21()

    assert result["status"] in {"DESIGN_STOP", "SCORED"}
    assert result["activation"]["status"] == result["status"] if result["status"] == "DESIGN_STOP" else "PASS"
    if result["status"] == "DESIGN_STOP":
        assert result["scoring_performed"] is False
        assert result["activation"]["failed_gates"]
    else:
        assert result["scoring_performed"] is True
        assert result["truth_retention_failures"] == 0
        assert result["axis_witness_mismatches"] == 0
        assert result["equivalence_violations"] == 0
        assert result["positive_superset_violations"] == 0
        assert result["negative_rescue_failures"] == 0
        assert result["temporal_rescue_failures"] == 0
        assert set(result["verdicts"]) == {
            "BAM_H1_truth_retention",
            "BAM_H2_axis_witness_attribution",
            "BAM_H3_intersection_nonidentifiability",
            "BAM_H4_positive_superset_ceiling",
            "BAM_H5_perfect_negative_rescue",
            "BAM_H6_temporal_M_rescue",
        }
