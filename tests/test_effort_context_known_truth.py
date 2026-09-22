from benchmarks.effort_context_known_truth import run_benchmark


def test_two_effort_modalities_share_one_candidate_unit_ledger_interface():
    result = run_benchmark()
    assert result["uses_biological_response"] is False
    assert result["systems"]["telemetry"]["candidate_unit_ids"] == [
        "R1|w1",
        "R1|w2",
        "R2|w2",
    ]
    assert result["systems"]["telemetry"]["unsurveyed_unit_ids"] == ["R2|w1"]
    assert result["systems"]["transect"]["candidate_unit_ids"] == [
        "T1|v1",
        "T1|v2",
        "T2|v2",
    ]
    assert result["systems"]["transect"]["unsurveyed_unit_ids"] == ["T2|v1"]
