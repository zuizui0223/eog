import csv
import json

import pytest

from eog.v2_empirical_occurrence_freeze_cli import main as freeze_main
from eog.v2_empirical_occurrence_io import read_feature_bundle
from eog.v2_empirical_occurrence_validate_cli import main as validate_main


def _write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _inputs(tmp_path):
    nodes = tmp_path / "nodes.csv"
    edges = tmp_path / "edges.csv"
    responses = tmp_path / "responses.csv"
    node_rows = []
    for i, viability in enumerate((0.8, 0.7, 0.6, 0.5, 0.45, 0.55, 0.65, 0.75)):
        node_rows.append(
            {
                "node_id": f"n{i}",
                "viability": viability,
                "source": int(i in (0, 7)),
                "ref_nearest": min(i, 7 - i),
            }
        )
    _write_csv(nodes, ["node_id", "viability", "source", "ref_nearest"], node_rows)

    edge_rows = []
    for i in range(7):
        edge_rows.append({"source_id": f"n{i}", "target_id": f"n{i+1}", "geographic_support": 0.65})
        edge_rows.append({"source_id": f"n{i+1}", "target_id": f"n{i}", "geographic_support": 0.65})
    _write_csv(edges, ["source_id", "target_id", "geographic_support"], edge_rows)

    response_values = ("", "1", "0", "1", "0", "1", "0", "")
    fold_values = ("source", "a", "b", "c", "a", "b", "c", "source")
    _write_csv(
        responses,
        ["node_id", "response", "fold_id"],
        [
            {"node_id": f"n{i}", "response": response_values[i], "fold_id": fold_values[i]}
            for i in range(8)
        ],
    )
    return nodes, edges, responses


def test_two_stage_cli_freezes_then_scores_separate_response_file(tmp_path):
    nodes, edges, responses = _inputs(tmp_path)
    features_path = tmp_path / "features.json"
    result_path = tmp_path / "result.json"
    freeze_main(
        [
            "--nodes", str(nodes),
            "--edges", str(edges),
            "--max-steps", "5",
            "--loss-support", "0.5",
            "--output", str(features_path),
        ]
    )
    features = read_feature_bundle(features_path)
    assert len(features.feature_fingerprint) == 64
    assert features.reference_names == ("nearest",)

    validate_main(
        [
            "--features", str(features_path),
            "--responses", str(responses),
            "--output", str(result_path),
        ]
    )
    result = json.loads(result_path.read_text())
    assert result["schema"] == "eog_v2_fixed_source_occurrence_validation_v1"
    assert result["feature_fingerprint"] == features.feature_fingerprint
    assert result["n_evaluated"] == 6
    assert result["n_missing_response"] == 2
    names = {row["model_name"] for row in result["model_scores"]}
    assert "viability_ref_nearest_dynamic" in names


def test_freeze_stage_rejects_response_column(tmp_path):
    nodes, edges, _ = _inputs(tmp_path)
    rows = list(csv.DictReader(nodes.open(encoding="utf-8")))
    contaminated = tmp_path / "contaminated.csv"
    for row in rows:
        row["response"] = "0"
    _write_csv(
        contaminated,
        ["node_id", "viability", "source", "ref_nearest", "response"],
        rows,
    )
    with pytest.raises(ValueError, match="unexpected columns"):
        freeze_main(
            [
                "--nodes", str(contaminated),
                "--edges", str(edges),
                "--max-steps", "5",
                "--output", str(tmp_path / "features.json"),
            ]
        )


def test_feature_bundle_tampering_is_rejected(tmp_path):
    nodes, edges, _ = _inputs(tmp_path)
    features_path = tmp_path / "features.json"
    freeze_main(
        [
            "--nodes", str(nodes),
            "--edges", str(edges),
            "--max-steps", "5",
            "--output", str(features_path),
        ]
    )
    payload = json.loads(features_path.read_text())
    payload["viability"][3] += 0.01
    features_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        read_feature_bundle(features_path)
