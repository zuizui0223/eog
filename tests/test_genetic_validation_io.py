import csv
import json
from pathlib import Path

import numpy as np
import pytest

from eog.genetic_validation import GeneticValidationConfig
from eog.genetic_validation_io import (
    load_genetic_response_pair_csv,
    load_population_csv,
    load_predictor_pair_csv,
    run_genetic_validation_from_csv,
)


def write_csv(path: Path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fixtures(tmp_path: Path, n=6):
    ids = [f"p{i}" for i in range(n)]
    population_path = tmp_path / "populations.csv"
    write_csv(
        population_path,
        ["population_id", "latitude", "longitude", "island_id"],
        [
            {
                "population_id": population_id,
                "latitude": 20 + i,
                "longitude": -20 + i,
                "island_id": f"island_{i}",
            }
            for i, population_id in enumerate(ids)
        ],
    )
    predictor_path = tmp_path / "predictors.csv"
    predictor_rows = []
    response_rows = []
    for i in range(n):
        for j in range(i + 1, n):
            d_geo = float(j - i)
            d_env = float(abs((i % 2) - (j % 2)))
            d_eog = d_geo + (1.5 if i < n // 2 <= j else 0.0)
            disconnected = int(i == 0 and j == n - 1)
            predictor_rows.append(
                {
                    "population_a": ids[i],
                    "population_b": ids[j],
                    "geographic_distance": d_geo,
                    "environmental_distance": d_env,
                    "eog_continuous_distance": d_eog,
                    "eog_disconnected": disconnected,
                    "strong_reference_distance": d_geo + 0.2 * d_env,
                }
            )
            response_rows.append(
                {
                    "population_a": ids[i],
                    "population_b": ids[j],
                    "genetic_distance": 0.02 * d_geo + 0.08 * d_eog + 0.04 * disconnected,
                }
            )
    write_csv(
        predictor_path,
        [
            "population_a",
            "population_b",
            "geographic_distance",
            "environmental_distance",
            "eog_continuous_distance",
            "eog_disconnected",
            "strong_reference_distance",
        ],
        predictor_rows,
    )
    response_path = tmp_path / "genetic.csv"
    write_csv(
        response_path,
        ["population_a", "population_b", "genetic_distance"],
        response_rows,
    )
    return population_path, predictor_path, response_path, predictor_rows, response_rows


def test_csv_intake_separates_predictor_and_response_fingerprints(tmp_path):
    population_path, predictor_path, response_path, _, _ = fixtures(tmp_path)
    bundle = run_genetic_validation_from_csv(
        population_path,
        predictor_path,
        response_path,
    )
    assert bundle.predictors.fingerprint != bundle.response.fingerprint
    assert bundle.validation.n_observed_pairs == 15
    assert len(bundle.fingerprint) == 64
    assert len(bundle.validation.fingerprint) == 64
    assert bundle.predictors.strong_reference_distance is not None


def test_response_change_does_not_change_predictor_fingerprint(tmp_path):
    population_path, predictor_path, response_path, _, response_rows = fixtures(tmp_path)
    populations = load_population_csv(population_path)
    predictors = load_predictor_pair_csv(predictor_path, populations)
    original = load_genetic_response_pair_csv(response_path, populations)
    response_rows[0] = dict(response_rows[0])
    response_rows[0]["genetic_distance"] = float(response_rows[0]["genetic_distance"]) + 0.1
    write_csv(
        response_path,
        ["population_a", "population_b", "genetic_distance"],
        response_rows,
    )
    changed = load_genetic_response_pair_csv(response_path, populations)
    predictors_again = load_predictor_pair_csv(predictor_path, populations)
    assert predictors.fingerprint == predictors_again.fingerprint
    assert original.fingerprint != changed.fingerprint


def test_missing_genetic_pair_remains_missing(tmp_path):
    population_path, predictor_path, response_path, _, response_rows = fixtures(tmp_path)
    response_rows.pop()
    write_csv(
        response_path,
        ["population_a", "population_b", "genetic_distance"],
        response_rows,
    )
    populations = load_population_csv(population_path)
    response = load_genetic_response_pair_csv(response_path, populations)
    assert response.n_observed_pairs == 14
    assert np.isnan(response.genetic_distance[4, 5])
    bundle = run_genetic_validation_from_csv(population_path, predictor_path, response_path)
    assert bundle.validation.n_observed_pairs == 14


def test_duplicate_unordered_pairs_and_self_pairs_are_rejected(tmp_path):
    population_path, predictor_path, response_path, predictor_rows, response_rows = fixtures(tmp_path)
    populations = load_population_csv(population_path)
    duplicate = dict(response_rows[0])
    duplicate["population_a"], duplicate["population_b"] = duplicate["population_b"], duplicate["population_a"]
    response_rows.append(duplicate)
    write_csv(response_path, ["population_a", "population_b", "genetic_distance"], response_rows)
    with pytest.raises(ValueError, match="duplicate unordered genetic pair"):
        load_genetic_response_pair_csv(response_path, populations)

    predictor_rows[0] = dict(predictor_rows[0])
    predictor_rows[0]["population_b"] = predictor_rows[0]["population_a"]
    write_csv(
        predictor_path,
        ["population_a", "population_b", "geographic_distance", "environmental_distance", "eog_continuous_distance", "eog_disconnected", "strong_reference_distance"],
        predictor_rows,
    )
    with pytest.raises(ValueError, match="self pair"):
        load_predictor_pair_csv(predictor_path, populations)


def test_predictor_pair_table_must_be_complete(tmp_path):
    population_path, predictor_path, _, predictor_rows, _ = fixtures(tmp_path)
    predictor_rows.pop()
    write_csv(
        predictor_path,
        ["population_a", "population_b", "geographic_distance", "environmental_distance", "eog_continuous_distance", "eog_disconnected", "strong_reference_distance"],
        predictor_rows,
    )
    with pytest.raises(ValueError, match="every unordered population pair"):
        load_predictor_pair_csv(predictor_path, load_population_csv(population_path))


def test_incomplete_optional_strong_reference_is_rejected(tmp_path):
    population_path, predictor_path, _, predictor_rows, _ = fixtures(tmp_path)
    predictor_rows[3] = dict(predictor_rows[3])
    predictor_rows[3]["strong_reference_distance"] = ""
    write_csv(
        predictor_path,
        ["population_a", "population_b", "geographic_distance", "environmental_distance", "eog_continuous_distance", "eog_disconnected", "strong_reference_distance"],
        predictor_rows,
    )
    with pytest.raises(ValueError, match="strong_reference_distance must be complete"):
        load_predictor_pair_csv(predictor_path, load_population_csv(population_path))


def test_population_coordinate_contract_and_minimum_size(tmp_path):
    path = tmp_path / "populations.csv"
    write_csv(
        path,
        ["population_id", "latitude", "longitude"],
        [
            {"population_id": "a", "latitude": "10", "longitude": "20"},
            {"population_id": "b", "latitude": "11", "longitude": "21"},
            {"population_id": "c", "latitude": "12", "longitude": "22"},
            {"population_id": "d", "latitude": "13", "longitude": "23"},
        ],
    )
    with pytest.raises(ValueError, match="at least five"):
        load_population_csv(path)


def test_linearized_fst_config_passes_through_csv_runner(tmp_path):
    population_path, predictor_path, response_path, _, _ = fixtures(tmp_path)
    result = run_genetic_validation_from_csv(
        population_path,
        predictor_path,
        response_path,
        config=GeneticValidationConfig(response_transform="linearized_fst", ridge_penalty=1.0),
    )
    assert result.validation.config.response_transform == "linearized_fst"
