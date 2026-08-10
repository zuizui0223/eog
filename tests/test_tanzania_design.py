import random

import pytest

from eog.tanzania_design import (
    EXPECTED_ELIGIBLE_SPECIES_SHA256,
    GeometryPoint,
    build_tanzania_design_contract,
    eligible_species_sha256,
    mst_quantile_radii,
    mst_spatial_blocks,
    stable_mst,
)


ELIGIBLE_SPECIES = [
    "ab", "ac", "af", "ag", "bbpb", "bfbs", "bgs", "bha", "bhk", "bltc",
    "brw", "bta", "btt", "btwe", "cf", "cs", "cw", "d", "dbw", "df",
    "edcs", "fb", "gb", "kl", "ld", "lh", "lsh", "mgt", "nc", "not",
    "nt", "of", "ogt", "omg", "ow", "pbi", "pf", "pk", "pt", "rcfw",
    "rcrc", "sa", "scg", "st", "std", "sth", "sw", "tb", "td", "tg",
    "uvbs", "vs", "wbrc", "wca", "web", "wtcf", "ybg", "ytww", "yvb", "ywe",
]


def test_eligible_species_fingerprint_is_frozen():
    assert eligible_species_sha256(ELIGIBLE_SPECIES) == EXPECTED_ELIGIBLE_SPECIES_SHA256


def test_stable_mst_is_order_invariant():
    points = [
        GeometryPoint("a", 0.0, 0.0),
        GeometryPoint("b", 0.0, 1.0),
        GeometryPoint("c", 1.0, 1.0),
        GeometryPoint("d", 2.0, 1.0),
    ]
    expected = stable_mst(points)
    shuffled = points.copy()
    random.Random(17).shuffle(shuffled)
    assert stable_mst(shuffled) == expected
    assert len(expected) == len(points) - 1


def test_mst_radii_are_monotonic_and_end_at_connectivity_threshold():
    points = [
        GeometryPoint("a", 0.0, 0.0),
        GeometryPoint("b", 0.0, 1.0),
        GeometryPoint("c", 0.0, 3.0),
        GeometryPoint("d", 0.0, 6.0),
    ]
    edges = stable_mst(points)
    radii = mst_quantile_radii(edges)
    values = list(radii.values())
    assert values == sorted(values)
    assert values[-1] == pytest.approx(max(edge.distance_km for edge in edges))


def test_mst_blocks_are_contiguous_deterministic_components():
    points = [
        GeometryPoint("a", 0.0, 0.0),
        GeometryPoint("b", 0.0, 0.01),
        GeometryPoint("c", 0.0, 1.0),
        GeometryPoint("d", 0.0, 1.01),
    ]
    assert mst_spatial_blocks(points, 2) == (("a", "b"), ("c", "d"))


def test_duplicate_geometry_is_rejected():
    with pytest.raises(ValueError, match="duplicate geometry"):
        stable_mst(
            [
                GeometryPoint("a", 0.0, 0.0),
                GeometryPoint("b", 0.0, 0.0),
            ]
        )


def _nodes(region):
    return [
        {
            "patch_number": str(i),
            "name": f"{region}{i}",
            "Area_ha": str(2.0 + i),
            "centroid_lat": str((-5.0 if region == "E" else -4.0) + i * 0.001),
            "centroid_long": str((38.5 if region == "E" else 38.0) + i * 0.002),
        }
        for i in range(1, 43)
    ]


def _sites():
    rows = []
    for region, n in (("E", 9), ("W", 5)):
        nodes = _nodes(region)
        for row in nodes[:n]:
            rows.append(
                {
                    "region": region,
                    "name": row["name"],
                    "patch_number": row["patch_number"],
                    "area_ha": row["Area_ha"],
                    "centroid_lat": row["centroid_lat"],
                    "centroid_long": row["centroid_long"],
                }
            )
    return rows


def test_design_contract_freezes_loso_blocks_radii_and_strict_anchor_control():
    contract = build_tanzania_design_contract(
        sites=_sites(),
        east_nodes=_nodes("E"),
        west_nodes=_nodes("W"),
        eligible_species=ELIGIBLE_SPECIES,
        source_formula_evidence={"synthetic_formula_gate": True},
    )
    assert contract["cross_validation"]["primary"]["n_folds"] == 14
    assert contract["cross_validation"]["spatial_sensitivity"]["n_folds"] == 5
    assert set(contract["eog_graph"]["regions"]) == {"E", "W"}
    for region in ("E", "W"):
        radii = contract["eog_graph"]["regions"][region]["scenario_radii_km"]
        assert list(radii) == ["mst_q50", "mst_q75", "mst_q90", "mst_q100"]
        assert list(radii.values()) == sorted(radii.values())
    models = contract["heldout_probability_models"]
    assert models["strict_incremental_reference"] == "current_flow_plus_anchor_distance"
    assert models["strict_incremental_candidate"] == (
        "current_flow_plus_anchor_distance_plus_eog"
    )
    assert contract["species_outcomes_inspected"] is False
    assert contract["model_fitted"] is False


def test_design_contract_rejects_missing_source_formula_evidence():
    with pytest.raises(ValueError, match="formula evidence missing"):
        build_tanzania_design_contract(
            sites=_sites(),
            east_nodes=_nodes("E"),
            west_nodes=_nodes("W"),
            eligible_species=ELIGIBLE_SPECIES,
            source_formula_evidence={"required_source_expression": False},
        )
