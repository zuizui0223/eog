from eog.v2.bam_targeted_measurement_audit import (
    run_targeted_measurement_exact_audit,
)


def test_exact_measurement_audit_has_no_solver_failures():
    result = run_targeted_measurement_exact_audit()

    assert result["systems_scored"] == 12
    assert result["truth_cases"] == 768
    assert result["failures"] == []
    assert result["all_greedy_counts_valid_upper_bounds"] is True
    assert len(result["fingerprint"]) == 64


def test_exact_measurement_bounds_are_finite():
    result = run_targeted_measurement_exact_audit()

    for key in (
        "max_exact_A",
        "max_exact_B",
        "max_exact_AB_joint",
        "max_exact_M",
        "max_exact_tau",
        "max_exact_M_tau_joint",
    ):
        assert isinstance(result[key], int)
        assert result[key] >= 0
