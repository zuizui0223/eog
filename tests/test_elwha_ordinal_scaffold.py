"""Replay conditional ordinal scaffold only; no biological data."""
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parents[1] / "validation/river_barrier_restoration_source_gate_v1"


def test_elwha_ordinal_scaffold():
    actual = runpy.run_path(str(HERE / "ordinal_scaffold.py"))["audit"]()
    expected = json.loads((HERE / "ordinal_scaffold_result.json").read_text(encoding="utf-8"))
    assert actual == expected
    assert actual["oracle_target_checks"] == 176
    assert actual["geometry_verified"] is False
    assert actual["fish_response_rows_parsed"] == 0
    assert actual["ecological_scores"] == 0
