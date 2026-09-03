import hashlib
import json

import pytest

from eog.n2_handoff import inspect_n2_handoff_payload


def _seal(payload):
    core = {key: value for key, value in payload.items() if key != "fingerprint"}
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    return payload


def _descriptive_payload(category, gains):
    return _seal(
        {
            "schema_id": "n2-to-n3-payload-v1",
            "program_id": "niche-to-survey-four-chapter-v1",
            "producer": {"chapter": "N2", "repository": "zuizui0223/odsp"},
            "evidence_id": "transferability-integrity-test",
            "axes": {
                "base": [
                    {"name": "x", "semantic": "easting", "units": "m", "reference_frame": "EPSG:3035"},
                    {"name": "y", "semantic": "northing", "units": "m", "reference_frame": "EPSG:3035"},
                ],
                "added": [
                    {"name": "z", "semantic": "height", "units": "m", "reference_frame": "MSL"}
                ],
            },
            "handoff": {
                "evidence_scope": "empirical",
                "support_semantics": "species_support",
                "axis_semantics_declared": True,
                "prospective_source_boundary_frozen": True,
                "thickness_estimable": True,
                "transferability_category": category,
                "handoff_category": "descriptive_projection_only",
                "projection_summary_allowed": True,
                "axis_resolved_state_allowed_for_method_testing": False,
                "axis_resolved_species_state_allowed_for_empirical_n3": False,
                "reason_codes": [],
            },
            "projection_summary": {"effective_vertical_states": 2.0},
            "transferability": {"category": category, "independent_gains": gains},
            "provenance": {
                "source_contract": None,
                "decision_receipt": None,
                "source_fingerprint": None,
            },
            "state_artifact": None,
        }
    )


def test_non_generalizing_category_rejects_any_positive_gain():
    payload = _descriptive_payload("non_generalizing", [-0.2, 0.1])
    with pytest.raises(ValueError, match="all supplied gains <= 0"):
        inspect_n2_handoff_payload(payload)


def test_mixed_category_requires_both_sides_of_zero_rule():
    with pytest.raises(ValueError, match="both positive and non-positive"):
        inspect_n2_handoff_payload(_descriptive_payload("mixed", [0.2, 0.1]))

    intake = inspect_n2_handoff_payload(_descriptive_payload("mixed", [0.2, -0.1]))
    assert intake.accepted_for_empirical_n3 is False
    assert intake.handoff_category == "descriptive_projection_only"


def test_generalizing_category_rejects_supplied_nonpositive_gain_even_if_not_promoted():
    payload = _descriptive_payload("generalizing", [0.2, 0.0])
    with pytest.raises(ValueError, match="all supplied gains > 0"):
        inspect_n2_handoff_payload(payload)
