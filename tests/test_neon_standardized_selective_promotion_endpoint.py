import numpy as np

from validation.neon_standardized_selective_promotion.final_endpoint import (
    frozen_thresholds,
    match_focal_deployments,
    resolve_header,
    support_summary,
    update_worlds,
)


def test_response_alias_resolution_is_frozen_and_exact():
    header = ["deploymentID", "scientificName", "commonName"]
    assert resolve_header(header, ["deployment_id", "deploymentID", "deploymentId"]) == "deploymentID"
    assert resolve_header(header, ["scientific_name", "scientificName", "species"]) == "scientificName"
    assert resolve_header(header, ["missing"], required=False) is None


def test_scientific_exact_match_blocks_common_name_fallback_globally():
    rows = [
        {"deployment_id": "a", "scientific_name": "Odocoileus virginianus", "common_name": "other"},
        {"deployment_id": "b", "scientific_name": "", "common_name": "white-tailed deer"},
    ]
    positives, exact_n, common_n = match_focal_deployments(
        rows,
        {"a", "b"},
        "deployment_id",
        "scientific_name",
        "common_name",
        "odocoileus virginianus",
        {"white-tailed deer"},
    )
    assert positives == {"a"}
    assert exact_n == 1
    assert common_n == 0


def test_common_name_fallback_only_when_no_scientific_exact_match_exists():
    rows = [
        {"deployment_id": "a", "scientific_name": "", "common_name": "white-tailed deer"},
        {"deployment_id": "b", "scientific_name": "Other taxon", "common_name": "other"},
    ]
    positives, exact_n, common_n = match_focal_deployments(
        rows,
        {"a", "b"},
        "deployment_id",
        "scientific_name",
        "common_name",
        "odocoileus virginianus",
        {"white-tailed deer"},
    )
    assert positives == {"a"}
    assert exact_n == 0
    assert common_n == 1


def test_world_contraction_is_sequential_and_irreversible():
    thresholds = [1.0, 10.0, 100.0, 1000.0]
    sources, surviving = update_worlds((0.0, 0.0), set(), [0, 1, 2, 3], thresholds)
    assert surviving == [0, 1, 2, 3]
    sources, surviving = update_worlds((0.0, 0.05), sources, surviving, thresholds)
    assert surviving == [1, 2, 3]
    sources, surviving = update_worlds((0.0, 0.5), sources, surviving, thresholds)
    assert surviving == [2, 3]


def test_support_summary_is_source_label_invariant():
    thresholds = [1.0, 10.0, 100.0, 1000.0]
    target = (0.0, 0.02)
    a = {(0.0, 0.0), (0.0, 0.03)}
    b = {(0.0, 0.03), (0.0, 0.0)}
    np.testing.assert_allclose(
        support_summary(target, a, [0, 1, 2, 3], thresholds),
        support_summary(target, b, [0, 1, 2, 3], thresholds),
    )


def test_geometry_thresholds_ignore_row_order():
    rows = [
        {"latitude": "0.0", "longitude": "0.0"},
        {"latitude": "0.0", "longitude": "0.01"},
        {"latitude": "0.0", "longitude": "0.03"},
        {"latitude": "0.0", "longitude": "0.08"},
        {"latitude": "0.0", "longitude": "0.20"},
        {"latitude": "0.0", "longitude": "0.50"},
    ]
    np.testing.assert_allclose(frozen_thresholds(rows), frozen_thresholds(list(reversed(rows))))
