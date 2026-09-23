from benchmarks.source_transport_preflight_replay import run_replay


def test_transport_preflight_rejects_endure_before_candidate_lock_but_keeps_safe_systems():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["changes_closed_eog_wf_synthesis"] is False

    assert result["systems"]["louisiana"]["transport_status"] == "ready_for_candidate_lock"
    assert result["systems"]["louisiana"]["candidate_status"] == "ready_for_geometry_gate"

    assert result["systems"]["tampa"]["transport_status"] == "ready_for_candidate_lock"
    assert result["systems"]["tampa"]["candidate_status"] == "ready_for_geometry_gate"

    assert (
        result["systems"]["endure"]["transport_status"]
        == "stop_no_response_blind_transport_route"
    )
    assert (
        result["systems"]["endure"]["candidate_status"]
        == "stop_response_blind_transport_unqualified"
    )
