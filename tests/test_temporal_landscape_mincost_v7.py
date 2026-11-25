"""Replay the exact finite weighted-restoration decision benchmark."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_landscape_mincost_v7"


def test_frozen_weighted_restoration_decisions():
    ns = runpy.run_path(str(HERE / "run.py"))
    actual = ns["audit"]()
    expected = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["small"]["full_checks"] == 200
    assert actual["small"]["zero_cap_checks"] == 200
    assert actual["small"]["mismatches"] == 0
    assert actual["witness"]["bounded"]["status"] == "bounded"
    assert actual["witness"]["exact"]["lower"] == actual["witness"]["exact"]["upper"] == 2
