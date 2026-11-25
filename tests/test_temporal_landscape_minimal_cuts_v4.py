"""Replay the frozen finite temporal multi-site cut benchmark."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_landscape_minimal_cuts_v4"


def test_frozen_temporal_landscape_minimal_cuts():
    ns = runpy.run_path(str(HERE / "run.py"))
    actual = ns["audit"]()
    expected = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["stress"]["reachability_oracle_checks"] == 17280
    assert actual["stress"]["subset_monotonicity_checks"] == 43740
    assert actual["stress"]["oracle_disagreements"] == 0
    assert actual["stress"]["monotonicity_violations"] == 0
