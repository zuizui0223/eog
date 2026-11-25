"""Replay the frozen synthetic joint clock/gap/speed audit."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/joint_clock_gap_speed_frontier_v1"


def test_frozen_joint_relaxation_cases_and_oracle():
    audit = runpy.run_path(str(HERE / "run.py"))["audit"]
    protocol = json.loads((HERE / "protocol_v1.json").read_text(encoding="utf-8"))
    frozen = json.loads((HERE / "result_v1.json").read_text(encoding="utf-8"))
    replay = json.loads(json.dumps(audit(protocol)))
    assert replay == frozen
    assert all(replay["hypotheses"].values())
    assert replay["stress"]["oracle_comparisons"] == 18000
    assert replay["stress"]["oracle_disagreements"] == 0
    assert replay["stress"]["monotonicity_violations"] == 0
