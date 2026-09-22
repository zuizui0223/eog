from benchmarks.louisiana_manifest_v2_portability_replay import run_replay


def test_louisiana_manifest_reproduces_shared_generic_contract_layers():
    result = run_replay()
    assert result["uses_biological_response"] is False
    assert result["reruns_frozen_endpoint"] is False
    assert result["counts_as_predictive_evidence"] is False
    assert all(result["shared_layer_fingerprint_matches"].values())
    assert result["counts"]["node_count"] == 33
    assert result["counts"]["context_count"] == 20
    assert result["counts"]["initialization_count"] == 33
    assert result["counts"]["scored_candidate_count"] == 627
    assert result["counts"]["unsurveyed_count"] == 0
    assert result["counts"]["declared_world_count"] == 7
    assert result["counts"]["structural_world_count"] == 3
    assert result["statuses"]["structural"] == "structural_ready"
    assert result["statuses"]["predictive"] == "predictive_complement_candidate"
