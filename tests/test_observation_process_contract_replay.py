from benchmarks.observation_process_contract_replay import run_replay


def test_frozen_modalities_map_to_two_generic_observation_modes_without_response_access():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert result["modality_count"] == 3
    assert result["mode_count"] == 2
    assert (
        result["systems"]["azores_yellow_eel_telemetry"]["mode"]
        == "complete_source_zero"
    )
    assert (
        result["systems"]["louisiana_king_rail_acoustics"]["mode"]
        == "explicit_binary_tokens"
    )
    assert (
        result["systems"]["tampa_seagrass_transects"]["mode"]
        == "complete_source_zero"
    )
