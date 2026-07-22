import csv

from eog.hypothesis_survey_io import run_hypothesis_survey_csv
from eog.hypothesis_survey_verify import verify_hypothesis_survey_bundle


def _write(path, fieldnames, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _inputs(tmp_path):
    scenarios = tmp_path / "scenarios.csv"
    families = tmp_path / "families.csv"
    candidates = tmp_path / "candidates.csv"
    _write(scenarios, ["scenario_id", "connected", "minimum_cost_nodes", "minimum_bottleneck_nodes"], [
        {"scenario_id": "n1", "connected": "true", "minimum_cost_nodes": "source|north|target", "minimum_bottleneck_nodes": "source|north|target"},
        {"scenario_id": "s1", "connected": "true", "minimum_cost_nodes": "source|south|target", "minimum_bottleneck_nodes": "source|south|target"},
    ])
    _write(families, ["hypothesis_id", "scenario_id", "path_mode"], [
        {"hypothesis_id": "north", "scenario_id": "n1", "path_mode": "minimum_cost"},
        {"hypothesis_id": "south", "scenario_id": "s1", "path_mode": "minimum_cost"},
    ])
    _write(candidates, ["node_id", "survey_effort", "accessibility_cost", "already_surveyed"], [
        {"node_id": "north", "survey_effort": "0", "accessibility_cost": "0", "already_surveyed": "false"},
        {"node_id": "south", "survey_effort": "0", "accessibility_cost": "0", "already_surveyed": "false"},
    ])
    return scenarios, families, candidates


def test_verifier_accepts_untampered_bundle(tmp_path):
    scenarios, families, candidates = _inputs(tmp_path)
    bundle = run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out")
    result = verify_hypothesis_survey_bundle(
        scenarios, families, candidates, bundle.ranking_csv_path, bundle.manifest_json_path
    )
    assert result.valid
    assert all(result.checks.values())


def test_verifier_rejects_modified_ranking(tmp_path):
    scenarios, families, candidates = _inputs(tmp_path)
    bundle = run_hypothesis_survey_csv(scenarios, families, candidates, tmp_path / "out")
    ranking = tmp_path / "out" / "hypothesis_survey_ranking.csv"
    ranking.write_text(ranking.read_text(encoding="utf-8").replace("north", "tampered", 1), encoding="utf-8")
    result = verify_hypothesis_survey_bundle(
        scenarios, families, candidates, ranking, bundle.manifest_json_path
    )
    assert not result.valid
    assert not result.checks["ranking_rows"]
