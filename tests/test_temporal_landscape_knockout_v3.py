"""Replay the frozen time-expanded site/state knockout witness and stress audit."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_landscape_knockout_v3"


def test_frozen_temporal_landscape_knockout():
    p = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    assert p["status"] == "FROZEN_BEFORE_SYNTHETIC_SCORING"
    ns = runpy.run_path(str(HERE / "run.py"))
    assert ns["NODES"] == tuple((t, s) for t in p["registry"]["times"] for s in p["registry"]["sites"])
    assert ns["SOURCE"] == tuple(p["registry"]["source"])
    assert ns["TARGETS"] == tuple(map(tuple, p["registry"]["final_targets"]))
    assert ns["SITES"] == tuple(p["registry"]["site_removals"])
    assert [p["constraints"][k] for k in ("max_gap", "max_speed", "max_environment_transition", "max_barrier_requirement")] == [2, 2, 2, 1]
    assert p["graph_generator"]["seed"] == 20261126
    actual = ns["audit"]()
    frozen = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert actual == frozen
    assert all(actual["canonical"].values())
    assert actual["stress"]["world_intervention_checks"] == 4800
    assert actual["stress"]["projection_checks"] == 4800
    assert actual["stress"]["oracle_disagreements"] == 0
    assert actual["stress"]["deletion_monotonicity_violations"] == 0
