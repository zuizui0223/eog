import csv
import json

import pytest

from eog import run_hypothesis_survey_csv


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def inputs(tmp_path):
    scenarios = tmp_path / "scenarios.csv"
    families = tmp_path / "families.csv"
    candidates = tmp_path / "candidates.csv"
    write_csv(
        scenarios,
        ["scenario_id", "connected", "minimum_cost_nodes", "minimum_bottleneck_nodes"],
        [
            {"scenario_id": "north-1", "connected": "true", "minimum_cost_nodes": "source|north|target", "minimum_bottleneck_nodes": "source|north|target"},
            {"scenario_id": "north-2", "connected": "false", "minimum_cost_nodes": "", "minimum_bottleneck_nodes": ""},
            {"scenario_id": "south-1", "connected": "true", "minimum_cost_nodes": "source|south|target", "minimum_bottleneck_nodes": "source|south|target"},
            {"scenario_id": "south-2", "connected": "true", "minimum_cost_nodes": "source|south|target", "minimum_bottleneck_nodes": "source|south|target"},
        ],
    )
    write_csv(
        families,
        ["hypothesis_id", "scenario_id", "path_mode"],
        [
            {"hypothesis_id": "north", "scenario_id": "north-1", "path_mode": "minimum_cost"},
            {"hypothesis_id": "north", "scenario_id": "north-2", "path_mode": "minimum_cost"},
            {"hypothesis_id": "south", "scenario_id": "south-1", "path_mode": "minimum_cost"},
            {"hypothesis_id": "south", "scenario_id": "south-2", "path_mode": "minimum_cost"},
        ],
    )
    write_csv(
        candidates,
        ["node_id", "survey_effort", "accessibility_cost", "already_surveyed"],
        [
            {"node_id": "north", "survey_effort": "0", "accessibility_cost": "0", "already_surveyed": "false"},
            {"node_id": "south", "survey_effort": "0", "accessibility_cost": "0", "already_surveyed": "false"},
        ],
    )
    return scenarios, families, candidates


def test_csv_runner_writes_audited_outputs(tmp_path):
    scenarios, families, candidates = inputs(tmp_path)
    result = run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out")
    ranking = (tmp_path / "out" / "hypothesis_survey_ranking.csv").read_text(encoding="utf-8")
    manifest = json.loads((tmp_path / "out" / "hypothesis_survey_manifest.json").read_text(encoding="utf-8"))
    assert "node_id" in ranking
    assert set(result.input_hashes) == {"scenarios_csv", "families_csv", "candidates_csv"}
    assert manifest["pipeline_fingerprint"] == result.result.fingerprint
    assert result.fingerprint


def test_csv_runner_is_reproducible(tmp_path):
    scenarios, families, candidates = inputs(tmp_path)
    first = run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out1")
    second = run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out2")
    assert first.fingerprint == second.fingerprint
    assert first.result == second.result


def test_duplicate_scenario_ids_are_rejected(tmp_path):
    scenarios, families, candidates = inputs(tmp_path)
    with scenarios.open("a", encoding="utf-8") as handle:
        handle.write("north-1,true,source|north|target,source|north|target\n")
    with pytest.raises(ValueError, match="duplicate scenario_id"):
        run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out")


def test_incomplete_assignment_is_rejected_by_default(tmp_path):
    scenarios, families, candidates = inputs(tmp_path)
    rows = list(csv.DictReader(families.open(encoding="utf-8")))[:-1]
    write_csv(families, ["hypothesis_id", "scenario_id", "path_mode"], rows)
    with pytest.raises(ValueError, match="all sensitivity scenarios"):
        run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out")
