"""Replay the finite restoration duality benchmark."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_landscape_restoration_v5"


def test_frozen_restoration_duality():
    p = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_BEFORE_SCORING"
    assert p["generator"]["seed"] == 20261127
    assert p["generator"]["systems"] == 240
    assert p["generator"]["worlds_per_system"] == 3
    ns = runpy.run_path(str(HERE / "run.py"))
    assert ns["NODES"] == tuple((t, s) for t in p["registry"]["times"] for s in p["registry"]["sites"])
    assert ns["SOURCE"] == tuple(p["registry"]["source"])
    assert ns["TARGETS"] == tuple(map(tuple, p["registry"]["targets"]))
    assert ns["SITES"] == tuple(p["registry"]["intervention_sites"])
    actual = ns["audit"]()
    expected = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["stress"]["local_reach_checks"] == 23040
    assert actual["stress"]["duality_checks"] == 76800
    assert actual["stress"]["mismatches"] == 0
