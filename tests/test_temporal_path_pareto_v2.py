"""Replay the isolated temporal path frontier benchmark."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_path_pareto_v2"


def test_frozen_path_pareto_replay():
    p = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_BEFORE_BENCHMARK_SCORING"
    assert p["stress"]["systems"] == 240
    assert p["stress"]["worlds_per_system"] == 2
    actual = runpy.run_path(str(HERE / "run.py"))["audit"]()
    frozen = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert actual == frozen
    assert actual["oracle_disagreements"] == 0
    assert actual["stress"]["world_oracle_comparisons"] == 480
    assert actual["stress"]["aggregate_oracle_comparisons"] == 480
