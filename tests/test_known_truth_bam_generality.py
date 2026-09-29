from eog.v2.known_truth_bam_generality import (
    SYSTEM_SPECS,
    build_generality_system,
    audit_system_activation,
    run_bam_generality_v3,
)


def test_v3_roster_is_finite_and_fixed():
    assert len(SYSTEM_SPECS) == 12
    assert [spec.seed for spec in SYSTEM_SPECS] == list(range(12))
    assert len({spec.system_id for spec in SYSTEM_SPECS}) == 12


def test_each_v3_system_has_frozen_64_world_universe():
    for spec in SYSTEM_SPECS:
        system = build_generality_system(spec)
        assert len(system.worlds) == 64
        assert len(system.fingerprint) == 64
        activation = audit_system_activation(system)
        assert activation.status in {"PASS", "DESIGN_STOP"}
        assert len(activation.fingerprint) == 64


def test_v3_result_has_explicit_generality_verdicts():
    result = run_bam_generality_v3()

    assert result["system_roster_size"] == 12
    assert result["scored_system_count"] + result["design_stop_count"] == 12
    assert set(result["verdicts"]) == {
        "G1_positive_zero_bound",
        "G2_M_final_bottleneck",
        "G3_AB_three_node_bound",
        "G4_M_two_node_bound",
        "G5_complete_state_recovery",
        "G6_monotone_evidence_ladder",
    }
    assert all(
        verdict in {"SUPPORTED", "REFUTED"}
        for verdict in result["verdicts"].values()
    )
    assert len(result["fingerprint"]) == 64


def test_v3_evidence_ladder_is_well_formed_when_systems_score():
    result = run_bam_generality_v3()
    pooled = result["pooled_bam_state_unique_fraction"]
    values = [pooled[f"E{i}"] for i in range(7)]
    assert all(0.0 <= value <= 1.0 for value in values)
    if result["scored_system_count"] > 0:
        assert all(left <= right for left, right in zip(values, values[1:]))
