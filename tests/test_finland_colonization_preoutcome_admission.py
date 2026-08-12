import csv

import numpy as np

from benchmarks.finland_colonization_preoutcome_admission import (
    _best_affine_transform_r2,
    _deterministic_spatial_folds,
    _gabriel_edges,
    _load_response_free_projection,
)


def test_release_transform_recovery_handles_logged_and_standardized_values():
    counts = np.asarray([1, 2, 4, 8, 16, 32], dtype=float)
    released = 1.7 + 0.43 * np.log10(counts)
    fit = _best_affine_transform_r2(counts, released)
    assert fit["r2"] > 0.999999999999
    assert fit["transform"] in {"log10", "ln"}


def test_gabriel_graph_and_spatial_folds_are_deterministic():
    ids = ("a", "b", "c", "d", "e", "f")
    coordinates = np.asarray(
        [(0, 0), (1, 0), (2, 0), (0, 2), (1, 2), (2, 2)], dtype=float
    )
    first_edges = _gabriel_edges(coordinates)
    second_edges = _gabriel_edges(coordinates)
    assert first_edges == second_edges
    assert first_edges
    first_folds = _deterministic_spatial_folds(ids, coordinates, n_folds=3)
    second_folds = _deterministic_spatial_folds(ids, coordinates, n_folds=3)
    assert np.array_equal(first_folds, second_folds)
    assert set(first_folds.tolist()) == {0, 1, 2}


def _write_projection_fixture(path, outcome_values):
    fields = [
        "outcome",
        "spp.name",
        "holmkod",
        "Euref_X_original",
        "Euref_Y_original",
        "Historical_total_log",
        "Dist_to_historical_log",
        "Buildings",
        "Meadow_or_pasture",
        "Deciduous_forest",
        "Coniferous_forest",
        "Mixed_forest",
        "Sand",
        "Open_rock_or_bare_ground",
        "Marsh",
        "Shore_meadow",
        "Limestone",
    ]
    islands = {
        "i0": (0.0, 0.0),
        "i1": (1.0, 0.0),
        "i2": (2.0, 0.0),
    }
    rows = []
    index = 0
    for species, targets, historical_total in (
        ("sp1", ("i1", "i2"), 1.0),
        ("sp2", ("i0", "i2"), 1.0),
    ):
        source = next(value for value in islands if value not in targets)
        for island in targets:
            x, y = islands[island]
            sx, sy = islands[source]
            distance = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
            rows.append(
                {
                    "outcome": outcome_values[index],
                    "spp.name": species,
                    "holmkod": island,
                    "Euref_X_original": x,
                    "Euref_Y_original": y,
                    "Historical_total_log": historical_total,
                    "Dist_to_historical_log": distance,
                    "Buildings": 0.1 + 0.01 * x,
                    "Meadow_or_pasture": 0.2,
                    "Deciduous_forest": 0.1,
                    "Coniferous_forest": 0.2,
                    "Mixed_forest": 0.1,
                    "Sand": 0.05,
                    "Open_rock_or_bare_ground": 0.1,
                    "Marsh": 0.05,
                    "Shore_meadow": 0.05,
                    "Limestone": 0,
                }
            )
            index += 1
    # Add rows from a third species so every island appears in the target projection and
    # island-level coordinate/habitat invariance can be checked without an outcome model.
    for island in ("i0", "i1", "i2"):
        x, y = islands[island]
        rows.append(
            {
                "outcome": outcome_values[index % len(outcome_values)],
                "spp.name": "sp_zero_source",
                "holmkod": island,
                "Euref_X_original": x,
                "Euref_Y_original": y,
                "Historical_total_log": "",
                "Dist_to_historical_log": "",
                "Buildings": 0.1 + 0.01 * x,
                "Meadow_or_pasture": 0.2,
                "Deciduous_forest": 0.1,
                "Coniferous_forest": 0.2,
                "Mixed_forest": 0.1,
                "Sand": 0.05,
                "Open_rock_or_bare_ground": 0.1,
                "Marsh": 0.05,
                "Shore_meadow": 0.05,
                "Limestone": 0,
            }
        )
        index += 1
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_response_free_projection_is_invariant_to_outcome_contents(tmp_path):
    first_path = tmp_path / "first.csv"
    second_path = tmp_path / "second.csv"
    _write_projection_fixture(first_path, ["0", "1", "0", "1", "0", "1", "0"])
    _write_projection_fixture(second_path, ["garbage", "?", "success", "fail", "x", "y", "z"])
    first = _load_response_free_projection(first_path)
    second = _load_response_free_projection(second_path)
    assert first["row_count"] == second["row_count"]
    assert first["island_ids"] == second["island_ids"]
    assert first["species_ids"] == second["species_ids"]
    assert first["species_targets"] == second["species_targets"]
    assert np.array_equal(first["coordinates"], second["coordinates"])
    assert np.array_equal(first["habitat"], second["habitat"])
