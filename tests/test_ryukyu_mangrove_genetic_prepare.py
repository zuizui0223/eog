import csv
import json

from benchmarks.ryukyu_mangrove_genetic_prepare import POPULATIONS, prepare
from eog.genetic_validation_io import load_population_csv, load_predictor_pair_csv


def test_ryukyu_predictor_freeze_is_complete_deterministic_and_response_free(tmp_path):
    populations = tmp_path / "populations.csv"
    predictors = tmp_path / "predictors.csv"
    manifest = tmp_path / "manifest.json"
    first = prepare(populations, predictors, manifest)
    first_text = predictors.read_text()
    second = prepare(populations, predictors, manifest)
    assert first["predictor_manifest_fingerprint"] == second["predictor_manifest_fingerprint"]
    assert predictors.read_text() == first_text
    assert first["n_populations"] == 16
    assert first["genetic_response_attached"] is False
    assert first["environmental_distance_policy"] == "all-zero; no IBE claim"
    assert first["gabriel_edge_count"] >= 15

    population_records = load_population_csv(populations)
    bundle = load_predictor_pair_csv(predictors, population_records)
    assert len(population_records) == 16
    assert bundle.strong_reference_distance is not None
    assert bundle.environmental_distance.max() == 0.0
    assert bundle.eog_continuous_distance.shape == (16, 16)
    assert len(bundle.fingerprint) == 64


def test_ryukyu_population_table_matches_frozen_primary_article_sites(tmp_path):
    populations = tmp_path / "populations.csv"
    prepare(populations, tmp_path / "predictors.csv", tmp_path / "manifest.json")
    with populations.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["population_id"] for row in rows] == [row[0] for row in POPULATIONS]
    assert rows[0] == {
        "population_id": "OKI",
        "latitude": "26.604000",
        "longitude": "128.143000",
        "island_id": "Okinawa",
    }
    assert rows[-1] == {
        "population_id": "IRMg",
        "latitude": "24.309000",
        "longitude": "123.683000",
        "island_id": "Iriomote",
    }


def test_ryukyu_manifest_contains_no_genetic_outcome_fields(tmp_path):
    path = tmp_path / "manifest.json"
    prepare(tmp_path / "populations.csv", tmp_path / "predictors.csv", path)
    payload = json.loads(path.read_text())
    text = json.dumps(payload).lower()
    assert "fst_value" not in text
    assert "migration_rate" not in text
    assert payload["status"] == "retrospective-external-response-not-attached"
