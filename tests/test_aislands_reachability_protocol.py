import json
from pathlib import Path


def test_aislands_reachability_protocol_keeps_islands_as_test_case_not_algorithm_class():
    path = Path("validation/aislands_preoutcome_20260808/reachability_protocol.json")
    protocol = json.loads(path.read_text(encoding="utf-8"))

    assert protocol["status"] == "corrected_before_sdm_or_eog_outcomes"
    assert protocol["primary_taxa"] == 886
    assert protocol["frozen_cohort_sha256"] == (
        "cf645d55b8bcc46be8a8dc5399db736bbcc20bb7114a72c79a5dee61ec918e12"
    )
    assert protocol["frozen_climate_sha256"] == (
        "6ae7f4a78eea28f074ef3c3399368a4886b09d2d0714e723e957d0a99b524285"
    )
    assert "not as a special algorithm class" in protocol["scientific_target"]

    support = protocol["upstream_support"]
    assert support["predictor_family"] == "climate_only"
    assert support["climate_source"]["dataset"] == "CHELSA-bioclim"
    assert support["climate_source"]["version"] == "2.1"
    assert support["climate_source"]["variables"] == ["bio1", "bio5", "bio6", "bio12", "bio15"]
    assert support["island_extraction"].startswith("direct CHELSA source-raster sample")
    assert support["primary_model"]["class_weight"] == "balanced"
    assert support["primary_model"]["l2_penalty"] == 1.0
    assert "distance_to_mainland" in support["excluded_predictors"]
    assert "bridge_or_reachability_outputs" in support["excluded_predictors"]

    graph = protocol["reachability"]
    assert graph["implementation"] == "existing eog.bridge and eog.bridge_builder only"
    assert graph["environmental_state"].startswith("the same five standardized frozen CHELSA")
    assert graph["primary_graph"]["k_nearest"] == 5
    assert graph["primary_graph"]["directed_by_time"] is False
    assert graph["barrier_cost"].startswith("zero in the primary")
    assert graph["held_out_labels_used_in_graph_construction"] is False

    assert protocol["required_comparators"] == [
        "local_support_only",
        "nearest_training_presence_geographic_distance",
        "local_support_plus_distance",
        "geographic_only_bridge",
        "geographic_plus_environmental_bridge",
    ]
