import csv
import json
from pathlib import Path

from eog.genetic_validation_cli import main


def write_csv(path: Path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_cli_writes_fingerprinted_lopo_result(tmp_path):
    ids = [f"p{i}" for i in range(6)]
    populations = tmp_path / "populations.csv"
    predictors = tmp_path / "predictors.csv"
    response = tmp_path / "genetic.csv"
    output = tmp_path / "result.json"
    write_csv(
        populations,
        ["population_id", "latitude", "longitude"],
        [
            {"population_id": population_id, "latitude": 10 + i, "longitude": 20 + i}
            for i, population_id in enumerate(ids)
        ],
    )
    predictor_rows = []
    response_rows = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            d_geo = float(j - i)
            d_env = float(abs((i % 3) - (j % 3)))
            d_eog = d_geo + (1.0 if i < 3 <= j else 0.0)
            predictor_rows.append(
                {
                    "population_a": ids[i],
                    "population_b": ids[j],
                    "geographic_distance": d_geo,
                    "environmental_distance": d_env,
                    "eog_continuous_distance": d_eog,
                    "eog_disconnected": 0,
                }
            )
            response_rows.append(
                {
                    "population_a": ids[i],
                    "population_b": ids[j],
                    "genetic_distance": 0.02 * d_geo + 0.08 * d_eog,
                }
            )
    write_csv(
        predictors,
        [
            "population_a",
            "population_b",
            "geographic_distance",
            "environmental_distance",
            "eog_continuous_distance",
            "eog_disconnected",
        ],
        predictor_rows,
    )
    write_csv(response, ["population_a", "population_b", "genetic_distance"], response_rows)

    assert main(
        [
            "--populations", str(populations),
            "--predictors", str(predictors),
            "--genetic-response", str(response),
            "--output", str(output),
        ]
    ) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "prospective-eog-v2-independent-genetic-validation"
    assert result["n_populations"] == 6
    assert result["n_observed_genetic_pairs"] == 15
    assert len(result["predictor_fingerprint"]) == 64
    assert len(result["response_fingerprint"]) == 64
    assert len(result["validation_fingerprint"]) == 64
    assert {model["model_id"] for model in result["models"]} == {
        "ibd", "ibd_ibe", "ibd_ibe_eog"
    }
