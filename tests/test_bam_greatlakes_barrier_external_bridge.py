import pandas as pd

from eog.v2.bam_greatlakes_barrier_external_bridge import (
    all_worlds,
    build_period_graph,
    calibration_species,
    evaluate_species,
    fit_habitat_scaling,
    graph_reachable,
    join_catch_to_habitat,
    validate_catch_frame,
    validate_habitat_frame,
)


def _habitat():
    rows = []
    for period, shift in (("90s", 0.0), ("2023", 0.1)):
        for stream, barrier in (("BarrierCreek", 1), ("ReferenceCreek", 0)):
            for position, pshift in (("downstream", 0.0), ("upstream", 0.2)):
                for segment in (1, 2, 3):
                    x = segment + pshift + shift + (0.3 if stream == "ReferenceCreek" else 0)
                    rows.append(
                        {
                            "period": period,
                            "pair_id": 1,
                            "Stream.Name": stream,
                            "barrier": barrier,
                            "position": position,
                            "segment": segment,
                            "width": 2.0 + x,
                            "max_depth": 0.2 + 0.1 * x,
                            "prop_clay": 0.05 + 0.005 * x,
                            "prop_silt": 0.10 + 0.006 * x,
                            "prop_sand": 0.20 + 0.007 * x,
                            "prop_gravel": 0.30 + 0.008 * x,
                            "prop_boulder": 0.35 + 0.009 * x,
                        }
                    )
    return pd.DataFrame(rows)


def _catch():
    rows = []
    positives_90 = {
        ("BarrierCreek", "downstream", 1),
        ("BarrierCreek", "downstream", 2),
    }
    positives_23 = positives_90 | {
        ("BarrierCreek", "upstream", 1),
    }
    for period, year, positives in (
        ("90s", 1997, positives_90),
        ("2023", 2023, positives_23),
    ):
        for stream, barrier in (("BarrierCreek", 1), ("ReferenceCreek", 0)):
            for position in ("downstream", "upstream"):
                for segment in (1, 2, 3):
                    rows.append(
                        {
                            "pair_id": 1,
                            "Year": year,
                            "Stream.Name": stream,
                            "barrier": barrier,
                            "position": position,
                            "segment": segment,
                            "survey_length": 50,
                            "species": "Species alpha",
                            "total_caught": int((stream, position, segment) in positives),
                            "yearBuilt": 1950,
                            "barrierAgeAtSample": year - 1950,
                            "period": period,
                        }
                    )
    return pd.DataFrame(rows)


def test_frozen_world_product_has_35_worlds():
    worlds = all_worlds()
    assert len(worlds) == 35
    assert len({world.world_id for world in worlds}) == 35


def test_barrier_graph_differs_only_at_crossing():
    habitat = _habitat()
    closed = build_period_graph(habitat, "90s", barrier_open=False)
    opened = build_period_graph(habitat, "90s", barrier_open=True)

    down = "1|BarrierCreek|downstream|1"
    up = "1|BarrierCreek|upstream|1"
    assert up not in closed[down]
    assert up in opened[down]

    rdown = "1|ReferenceCreek|downstream|1"
    rup = "1|ReferenceCreek|upstream|1"
    assert rup in closed[rdown]
    assert rup in opened[rdown]


def test_graph_horizon_reachability_is_monotone():
    graph = build_period_graph(_habitat(), "90s", barrier_open=True)
    source = ["1|BarrierCreek|downstream|2"]
    h1 = graph_reachable(graph, source, 1)
    h2 = graph_reachable(graph, source, 2)
    hall = graph_reachable(graph, source, None)
    assert h1 <= h2 <= hall


def test_species_bridge_uses_heldout_positive_as_world_witness():
    habitat = validate_habitat_frame(_habitat())
    catch = validate_catch_frame(_catch())
    joined = join_catch_to_habitat(catch, habitat)
    scaling = fit_habitat_scaling(habitat)

    assert calibration_species(joined) == ("Species alpha",)
    result = evaluate_species(
        joined,
        habitat,
        scaling,
        "Species alpha",
    )
    assert len(result.calibration_world_ids) == 35
    assert "1|BarrierCreek|upstream|1" in result.heldout_positive_nodes
    assert len(result.heldout_witness_rows) == 3
    assert len(result.final_survivor_world_ids) <= 35
    crossing = next(
        row
        for row in result.heldout_witness_rows
        if row["node_id"] == "1|BarrierCreek|upstream|1"
    )
    assert crossing["eliminated_world_count"] > 0
