import pytest

from eog.tanzania_design import MstEdge
from eog.tanzania_survey_ladder import (
    build_tanzania_survey_ladder_contract,
    survey_component_ladder,
)


ELIGIBLE_SPECIES = [
    "ab", "ac", "af", "ag", "bbpb", "bfbs", "bgs", "bha", "bhk", "bltc",
    "brw", "bta", "btt", "btwe", "cf", "cs", "cw", "d", "dbw", "df",
    "edcs", "fb", "gb", "kl", "ld", "lh", "lsh", "mgt", "nc", "not",
    "nt", "of", "ogt", "omg", "ow", "pbi", "pf", "pk", "pt", "rcfw",
    "rcrc", "sa", "scg", "st", "std", "sth", "sw", "tb", "td", "tg",
    "uvbs", "vs", "wbrc", "wca", "web", "wtcf", "ybg", "ytww", "yvb", "ywe",
]


def test_component_ladder_selects_exact_distinct_partitions():
    edges = (
        MstEdge("a", "b", 1.0),
        MstEdge("b", "c", 2.0),
        MstEdge("c", "d", 3.0),
        MstEdge("d", "e", 4.0),
    )
    survey = {name: name.upper() for name in "abcde"}
    ladder = survey_component_ladder(edges, survey)
    assert [item.scenario_id for item in ladder] == [
        "survey_c04",
        "survey_c03",
        "survey_c02",
        "survey_c01",
    ]
    assert [item.radius_km for item in ladder] == [1.0, 2.0, 3.0, 4.0]
    assert [len(item.survey_partition) for item in ladder] == [4, 3, 2, 1]
    assert len({item.survey_partition for item in ladder}) == 4


def test_component_ladder_rejects_structurally_degenerate_ensemble():
    edges = (
        MstEdge("a", "b", 1.0),
        MstEdge("b", "c", 1.0),
        MstEdge("c", "d", 1.0),
        MstEdge("d", "e", 1.0),
    )
    with pytest.raises(ValueError, match="distinct survey-component"):
        survey_component_ladder(edges, {name: name for name in "abcde"})


def _nodes(region):
    rows = []
    longitude = 38.0 if region == "E" else 37.0
    latitude = -5.0 if region == "E" else -4.0
    for index in range(1, 43):
        if index > 1:
            longitude += index * 0.0001
        rows.append(
            {
                "patch_number": str(index),
                "name": f"{region}{index}",
                "Area_ha": str(2.0 + index),
                "centroid_lat": str(latitude),
                "centroid_long": str(longitude),
            }
        )
    return rows


def _sites():
    rows = []
    for region, count in (("E", 9), ("W", 5)):
        for node in _nodes(region)[:count]:
            rows.append(
                {
                    "region": region,
                    "name": node["name"],
                    "patch_number": node["patch_number"],
                    "area_ha": node["Area_ha"],
                    "centroid_lat": node["centroid_lat"],
                    "centroid_long": node["centroid_long"],
                }
            )
    return rows


def test_wrapper_replaces_quantile_radii_with_geometry_only_ladder():
    contract = build_tanzania_survey_ladder_contract(
        sites=_sites(),
        east_nodes=_nodes("E"),
        west_nodes=_nodes("W"),
        eligible_species=ELIGIBLE_SPECIES,
        source_formula_evidence={"synthetic_source_formula": True},
    )
    assert contract["eog_graph"]["radius_selection_audit"]["label_use"].startswith(
        "none"
    )
    for region in ("E", "W"):
        region_contract = contract["eog_graph"]["regions"][region]
        assert list(region_contract["scenario_radii_km"]) == [
            "survey_c04",
            "survey_c03",
            "survey_c02",
            "survey_c01",
        ]
        assert list(region_contract["survey_component_counts"].values()) == [
            4,
            3,
            2,
            1,
        ]
        partitions = region_contract["survey_component_partitions"]
        assert len({str(partitions[key]) for key in partitions}) == 4
    assert contract["species_outcomes_inspected"] is False
    assert contract["model_fitted"] is False
    assert contract["current_flow_computed"] is False
    assert contract["eog_score_computed"] is False
