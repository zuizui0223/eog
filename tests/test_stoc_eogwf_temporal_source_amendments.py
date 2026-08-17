from __future__ import annotations

import json
from pathlib import Path


ROOT = Path("validation/stoc_eogwf")


def _load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_period_specific_world_rule_freezes_thresholds_on_calibration_only():
    amendment = _load("preoutcome_amendment_v1_2.json")
    assert "before" in amendment["timing"]
    rule = amendment["world_time_rule"]
    assert rule["threshold_freeze"].endswith("calibration-period inputs")
    assert "heldout-period environmental distances" in rule["heldout_operator"]
    assert "calibration operator" in rule["reconstruction"]
    assert amendment["no_retuning"] is True


def test_source_policy_uses_fixed_anchors_and_other_positives_only_as_constraints():
    amendment = _load("preoutcome_amendment_v1_3.json")
    assert "before" in amendment["timing"]
    policy = amendment["final_source_policy"]
    assert "up to 10" in policy["anchor_selection"]
    assert "do not become additional forecast sources" in policy["calibration_constraints"]
    assert "same fixed anchor set" in policy["heldout_forecast_features"]
    assert "not inferred ancestral" in policy["ecological_interpretation"]
    assert amendment["no_retuning"] is True
