import json
import sys

from eog.v3.cli import joint_evaluate_main, plan_evidence_main


def _payload():
    return {
        "ecological_worlds": [
            {
                "world_id": "eco_absent",
                "state_by_target": {"site": "absent"},
            },
            {
                "world_id": "eco_present",
                "state_by_target": {"site": "present"},
            },
        ],
        "observation_worlds": [
            {
                "world_id": "perfect",
                "supports": [
                    {
                        "channel_id": "survey",
                        "ecological_state": "absent",
                        "possible_outcomes": ["zero"],
                    },
                    {
                        "channel_id": "survey",
                        "ecological_state": "present",
                        "possible_outcomes": ["positive"],
                    },
                ],
            },
            {
                "world_id": "imperfect",
                "supports": [
                    {
                        "channel_id": "survey",
                        "ecological_state": "absent",
                        "possible_outcomes": ["zero"],
                    },
                    {
                        "channel_id": "survey",
                        "ecological_state": "present",
                        "possible_outcomes": ["zero", "positive"],
                    },
                ],
            },
        ],
        "evidence_events": [
            {
                "target_id": "site",
                "channel_id": "survey",
                "observed_outcome": "zero",
            }
        ],
    }


def test_v3_joint_evaluate_cli_writes_fingerprinted_json(tmp_path, monkeypatch):
    input_path = tmp_path / "input.json"
    output_path = tmp_path / "evaluation.json"
    input_path.write_text(json.dumps(_payload()), encoding="utf-8")

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
    assert result["schema"] == "eog.v3.joint_evaluation.v1"
    assert result["surviving_joint_world_ids"] == [
        "eco_absent::imperfect",
        "eco_absent::perfect",
        "eco_present::imperfect",
    ]
    assert result["ecological_projection"] == ["eco_absent", "eco_present"]
    assert result["observation_projection"] == ["imperfect", "perfect"]
    assert result["universe_falsified"] is False
    assert len(result["fingerprint"]) == 64


def test_v3_plan_evidence_cli_respects_declared_objective(tmp_path, monkeypatch):
    payload = _payload()
    payload["action_supports"] = {
        "calibrate": {
            "eco_absent::imperfect": ["imperfect"],
            "eco_absent::perfect": ["perfect"],
            "eco_present::imperfect": ["imperfect"],
        },
        "gold_state": {
            "eco_absent::imperfect": ["absent"],
            "eco_absent::perfect": ["absent"],
            "eco_present::imperfect": ["present"],
        },
        "noop": {
            "eco_absent::imperfect": ["same"],
            "eco_absent::perfect": ["same"],
            "eco_present::imperfect": ["same"],
        },
    }

    input_path = tmp_path / "plan_input.json"
    output_path = tmp_path / "plan.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v3-plan-evidence",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--objective",
            "ecological",
        ],
    )
    assert plan_evidence_main() == 0

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["schema"] == "eog.v3.evidence_plan.v1"
    assert result["objective"] == "ecological"
    assert result["best_action_ids"] == ["gold_state"]
    assert result["fail_closed_no_improvement"] is False
    assert len(result["fingerprint"]) == 64
