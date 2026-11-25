"""Replay the frozen finite antichain scale audit."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/temporal_landscape_antichain_v6"


def test_frozen_temporal_landscape_antichain():
    protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "FROZEN_BEFORE_SCORING"
    ns = runpy.run_path(str(HERE / "run.py"))
    assert ns["CAP"] == protocol["resource_limit"]["max_labels"]
    result = ns["audit"]()
    expected = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
    assert result == expected
    assert result["small"]["frontier_checks"] == 800
    assert result["small"]["mismatches"] == 0
    assert all(row["complete"] for row in result["large"])
    assert not result["adversarial"][-1]["complete"]
    assert result["adversarial"][-1]["status"] == "label_cap_exceeded_no_certificate"
