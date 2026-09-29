import json
import sys
from pathlib import Path

from eog.v3.cli import joint_evaluate_main, plan_evidence_main


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "eog_v3"
SCHEMA = ROOT / "schemas" / "eog_v3_joint_input.schema.json"


def test_repository_joint_evaluation_example_runs(tmp_path, monkeypatch):
    input_path = EXAMPLES / "joint_evaluation_input.json"
    output_path = tmp_path / "joint_result.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v3-joint-evaluate",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
    )
    assert joint_evaluate_main() == 0

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["surviving_joint_world_ids"] == [
        "eco_absent::imperfect",
        "eco_absent::perfect",
        "eco_present::imperfect",
    ]
    assert result["ecological_projection"] == ["eco_absent", "eco_present"]
    assert result["universe_falsified"] is False


def test_repository_evidence_planning_example_runs_for_both_objectives(
    tmp_path,
    monkeypatch,
):
    input_path = EXAMPLES / "evidence_planning_input.json"

    ecological_output = tmp_path / "ecological_plan.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v3-plan-evidence",
            "--input",
            str(input_path),
            "--output",
            str(ecological_output),
            "--objective",
            "ecological",
        ],
    )
    assert plan_evidence_main() == 0
    ecological = json.loads(ecological_output.read_text(encoding="utf-8"))
    assert ecological["best_action_ids"] == ["gold_standard_target_state"]

    joint_output = tmp_path / "joint_plan.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v3-plan-evidence",
            "--input",
            str(input_path),
            "--output",
            str(joint_output),
            "--objective",
            "joint",
        ],
    )
    assert plan_evidence_main() == 0
    joint = json.loads(joint_output.read_text(encoding="utf-8"))
    assert joint["best_action_ids"] == ["calibrate_detection_world"]


def test_repository_v3_input_schema_matches_documented_surface():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(schema["required"]) == {
        "ecological_worlds",
        "observation_worlds",
    }
    assert {
        "ecological_worlds",
        "observation_worlds",
        "evidence_events",
        "action_supports",
    } <= set(schema["properties"])
