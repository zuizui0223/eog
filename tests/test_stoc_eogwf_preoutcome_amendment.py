from __future__ import annotations

import json
from pathlib import Path


AMENDMENT = Path("validation/stoc_eogwf/preoutcome_amendment_v1_1.json")


def _load():
    return json.loads(AMENDMENT.read_text(encoding="utf-8"))


def test_identity_endpoint_is_fixed_before_response_open():
    amendment = _load()
    assert "before DataSTOC response rows were fetched" in amendment["timing"]
    assert amendment["nonresponse_numerics"]["environment_standardisation"].endswith("pre-model failure")

    calibration = amendment["identity_calibration"]
    assert calibration["frequency_model"].startswith("L2 logistic regression")
    assert calibration["identity_model"].startswith("L2 logistic regression")
    assert "frequency_feature" in calibration["identity_model"]
    assert "ordered surviving-world bit columns" in calibration["identity_model"]


def test_identity_and_external_decision_rules_are_not_interchangeable():
    amendment = _load()
    identity = amendment["primary_identity_endpoint"]
    external = amendment["external_prediction_endpoint"]

    assert identity["contrast"].startswith("heldout logloss(identity_model) - heldout logloss(frequency_model)")
    assert identity["favourable_direction"] == "negative"
    assert any("60%" in rule for rule in identity["favourable_family_rule"])

    assert external["eog_candidate"] == "identity_model"
    assert external["primary_external_reference"].startswith("fixed equal-weight mean")
    assert external["favourable_direction"] == "negative"
    assert amendment["no_retuning"] is True
