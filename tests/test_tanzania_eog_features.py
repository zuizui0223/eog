import copy

import pytest

from eog.tanzania_eog_features import (
    NodeRecord,
    SiteRecord,
    TanzaniaRegionGraph,
    canonical_jsonl_sha256,
    evaluate_structural_target,
    generate_tanzania_eog_features,
)


def _nodes():
    east = [
        {
            "patch_number": "1",
            "name": "A",
            "centroid_lat": "0",
            "centroid_long": "0",
        },
        {
            "patch_number": "2",
            "name": "X",
            "centroid_lat": "0",
            "centroid_long": "0.5",
        },
        {
            "patch_number": "3",
            "name": "B",
            "centroid_lat": "0",
            "centroid_long": "1",
        },
    ]
    west = [
        {
            "patch_number": "1",
            "name": "C",
            "centroid_lat": "1",
            "centroid_long": "0",
        },
        {
            "patch_number": "2",
            "name": "D",
            "centroid_lat": "1",
            "centroid_long": "1",
        },
    ]
    return east, west


def _sites():
    return [
        {
            "region": "E",
            "name": "A",
            "patch_number": "1",
            "centroid_lat": "0",
            "centroid_long": "0",
        },
        {
            "region": "E",
            "name": "B",
            "patch_number": "3",
            "centroid_lat": "0",
            "centroid_long": "1",
        },
        {
            "region": "W",
            "name": "C",
            "patch_number": "1",
            "centroid_lat": "1",
            "centroid_long": "0",
        },
        {
            "region": "W",
            "name": "D",
            "patch_number": "2",
            "centroid_lat": "1",
            "centroid_long": "1",
        },
    ]


def _occurrence(heldout_value=0):
    values = {"A": 1, "B": heldout_value, "C": 0, "D": 0}
    return [
        {"species": "sp", "name": site, "occur": str(value)}
        for site, value in values.items()
    ]


def _design():
    fold = {"fold_id": "FOLD_B", "held_out_sites": ["B"]}
    return {
        "status": "tanzania_geometry_and_formula_contract_frozen_before_outcomes",
        "source": {
            "eligible_species": ["sp"],
            "eligible_species_sha256": "synthetic",
        },
        "cross_validation": {
            "primary": {"folds": [fold]},
            "spatial_sensitivity": {"folds": [fold]},
        },
        "eog_graph": {
            "regions": {
                "E": {"scenario_radii_km": {"near": 60.0, "wide": 120.0}},
                "W": {"scenario_radii_km": {"near": 60.0, "wide": 120.0}},
            }
        },
        "design_fingerprint": "synthetic",
        "species_outcomes_inspected": False,
        "model_fitted": False,
        "current_flow_computed": False,
        "eog_score_computed": False,
    }


def _generate(heldout_value=0, reverse=False):
    east, west = _nodes()
    sites = _sites()
    occurrence = _occurrence(heldout_value)
    if reverse:
        east = list(reversed(east))
        west = list(reversed(west))
        sites = list(reversed(sites))
        occurrence = list(reversed(occurrence))
    return generate_tanzania_eog_features(
        sites_rows=sites,
        east_node_rows=east,
        west_node_rows=west,
        occurrence_rows=occurrence,
        design=_design(),
        enforce_frozen_contract=False,
        strict_source_shape=False,
    )


def _record(records, partition, site):
    return next(
        row
        for row in records
        if row["analysis_partition"] == partition and row["site_id"] == site
    )


def test_heldout_label_is_not_used_or_exported():
    records_zero, applicability_zero = _generate(heldout_value=0)
    records_one, applicability_one = _generate(heldout_value=1)
    assert records_zero == records_one
    assert applicability_zero == applicability_one
    assert all("observed_presence" not in row for row in records_zero)
    assert all(row["heldout_label_used_in_construction"] is False for row in records_zero)


def test_training_presence_cannot_anchor_itself():
    records, _ = _generate()
    training_anchor = _record(records, "primary_loso", "A")
    assert training_anchor["role"] == "training"
    assert training_anchor["row_exclusion_applied"] is True
    assert training_anchor["feature_valid"] is False
    assert training_anchor["failure_reason"] == (
        "no_training_presence_anchor_after_row_exclusion"
    )


def test_same_nearest_distance_can_have_different_graph_configuration():
    records, _ = _generate()
    connected = _record(records, "primary_loso", "B")
    detached_other_region = _record(records, "primary_loso", "C")
    assert connected["nearest_anchor_distance_km"] == pytest.approx(
        detached_other_region["nearest_anchor_distance_km"], rel=1e-4
    )
    assert connected["eog_connected_frequency"] == pytest.approx(1.0)
    assert detached_other_region["same_region_anchor_count"] == 0
    assert detached_other_region["eog_connected_frequency"] == pytest.approx(0.0)
    assert detached_other_region["eog_median_normalized_bottleneck"] is None


def test_target_self_anchor_is_a_hard_failure():
    east, _ = _nodes()
    nodes = [
        NodeRecord(
            node_id=f"E:{int(row['patch_number']):02d}:{row['name']}",
            site_name=row["name"],
            region="E",
            patch_number=int(row["patch_number"]),
            latitude=float(row["centroid_lat"]),
            longitude=float(row["centroid_long"]),
        )
        for row in east
    ]
    graph = TanzaniaRegionGraph("E", nodes, {"near": 60.0})
    sites = {
        "A": SiteRecord("A", "E", 1, 0.0, 0.0, "E:01:A"),
        "B": SiteRecord("B", "E", 3, 0.0, 1.0, "E:03:B"),
    }
    with pytest.raises(ValueError, match="excluded from its own anchor"):
        evaluate_structural_target(
            target_site_id="A",
            anchor_site_ids=["A"],
            sites=sites,
            graphs={"E": graph},
        )


def test_no_global_anchor_is_explicitly_invalid():
    east, _ = _nodes()
    graph = TanzaniaRegionGraph(
        "E",
        [
            NodeRecord(
                node_id=f"E:{int(row['patch_number']):02d}:{row['name']}",
                site_name=row["name"],
                region="E",
                patch_number=int(row["patch_number"]),
                latitude=float(row["centroid_lat"]),
                longitude=float(row["centroid_long"]),
            )
            for row in east
        ],
        {"near": 60.0},
    )
    result = evaluate_structural_target(
        target_site_id="B",
        anchor_site_ids=[],
        sites={"B": SiteRecord("B", "E", 3, 0.0, 1.0, "E:03:B")},
        graphs={"E": graph},
    )
    assert result.feature_valid is False
    assert result.eog_connected_frequency is None
    assert result.nearest_anchor_distance_km is None


def test_feature_output_is_invariant_to_input_order():
    records_a, applicability_a = _generate(reverse=False)
    records_b, applicability_b = _generate(reverse=True)
    assert canonical_jsonl_sha256(records_a) == canonical_jsonl_sha256(records_b)
    assert canonical_jsonl_sha256(applicability_a) == canonical_jsonl_sha256(
        applicability_b
    )


def test_applicability_uses_training_labels_only():
    records, applicability = _generate()
    primary = next(
        row
        for row in applicability
        if row["analysis_partition"] == "primary_loso"
    )
    assert primary["heldout_labels_used"] is False
    assert primary["performance_metric_computed"] is False
    assert primary["anchor_feature_model_estimable"] is False
    assert primary["failure_reason"] == "valid_training_structural_rows_single_class"
    assert _record(records, "primary_loso", "B")["feature_valid"] is True
