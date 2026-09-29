from eog.v2.known_truth_bam_v2_2 import run_bam_v22


def test_direct_bam_evidence_result_is_well_formed():
    result = run_bam_v22()

    assert result["eligible_truth_worlds"] == 64
    assert set(result["unique_truth_fractions"]) == {
        "baseline",
        "A_direct",
        "B_direct",
        "M_direct",
        "AB_direct",
        "AM_direct",
        "BM_direct",
        "ABM_direct",
    }
    assert set(result["verdicts"]) == {
        "D1_axis_exactness",
        "D2_combined_state_ceiling",
        "D3_unique_state_recovery",
    }
    assert all(
        verdict in {"SUPPORTED", "REFUTED"}
        for verdict in result["verdicts"].values()
    )
    assert len(result["fingerprint"]) == 64
