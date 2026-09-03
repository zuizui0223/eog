import copy
import hashlib
import json

import pytest

from eog.n2_handoff import inspect_n2_handoff_payload, verify_n2_state_artifact_bytes


BASE_AXES = [
    {"name": "x", "semantic": "projected easting", "units": "m", "reference_frame": "EPSG:3035"},
    {"name": "y", "semantic": "projected northing", "units": "m", "reference_frame": "EPSG:3035"},
]
ADDED_AXES = [
    {"name": "z", "semantic": "native GPS height above mean sea level", "units": "m", "reference_frame": "MSL"}
]


def _seal(payload):
    core = {key: value for key, value in payload.items() if key != "fingerprint"}
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return payload


def _base_payload(*, evidence_id, handoff, projection_summary, gains, artifact=None):
    return _seal(
        {
            "schema_id": "n2-to-n3-payload-v1",
            "program_id": "niche-to-survey-four-chapter-v1",
            "producer": {"chapter": "N2", "repository": "zuizui0223/odsp"},
            "evidence_id": evidence_id,
            "axes": {"base": copy.deepcopy(BASE_AXES), "added": copy.deepcopy(ADDED_AXES)},
            "handoff": handoff,
            "projection_summary": projection_summary,
            "transferability": {
                "category": handoff["transferability_category"],
                "independent_gains": list(gains),
            },
            "provenance": {
                "source_contract": None,
                "decision_receipt": None,
                "source_fingerprint": None,
            },
            "state_artifact": artifact,
        }
    )


def _bat_handoff():
    return {
        "evidence_scope": "empirical",
        "support_semantics": "species_support",
        "axis_semantics_declared": True,
        "prospective_source_boundary_frozen": True,
        "thickness_estimable": True,
        "transferability_category": "non_generalizing",
        "handoff_category": "descriptive_projection_only",
        "projection_summary_allowed": True,
        "axis_resolved_state_allowed_for_method_testing": False,
        "axis_resolved_species_state_allowed_for_empirical_n3": False,
        "reason_codes": ["independent_axis_resolved_organization_not_generalizing"],
    }


def test_bat_like_payload_is_retained_descriptively_but_rejected_as_n3_state():
    payload = _base_payload(
        evidence_id="tadarida-teniotis-n2-terminal",
        handoff=_bat_handoff(),
        projection_summary={
            "H_Z_given_XY_nats": 1.3918623004770097,
            "effective_vertical_states": 4.022333876564191,
        },
        gains=(-0.43541033813280833, -0.021938657402345435),
    )

    intake = inspect_n2_handoff_payload(payload)
    assert intake.fingerprint_verified is True
    assert intake.projection_summary_available is True
    assert intake.accepted_for_empirical_n3 is False
    assert intake.accepted_for_method_testing is False
    assert intake.state_artifact_uri is None
    assert "axis_resolved_state_not_admitted" in intake.reason_codes


def test_generalizing_empirical_species_state_is_admitted_and_integrity_checked():
    data = b"synthetic axis-resolved species support"
    sha = hashlib.sha256(data).hexdigest()
    handoff = {
        "evidence_scope": "empirical",
        "support_semantics": "species_support",
        "axis_semantics_declared": True,
        "prospective_source_boundary_frozen": True,
        "thickness_estimable": True,
        "transferability_category": "generalizing",
        "handoff_category": "empirical_axis_resolved_supported",
        "projection_summary_allowed": True,
        "axis_resolved_state_allowed_for_method_testing": False,
        "axis_resolved_species_state_allowed_for_empirical_n3": True,
        "reason_codes": [],
    }
    artifact = {
        "artifact_semantics": "empirical_species_support",
        "uri": "artifact://future-support.npz",
        "sha256": sha,
        "media_type": "application/x-npz",
        "shape": [2, 3, 4],
        "axis_order": ["x", "y", "z"],
    }
    payload = _base_payload(
        evidence_id="future-generalizing-lane",
        handoff=handoff,
        projection_summary={"effective_vertical_states": 2.5},
        gains=(0.12, 0.08),
        artifact=artifact,
    )

    intake = inspect_n2_handoff_payload(payload)
    assert intake.accepted_for_empirical_n3 is True
    assert intake.state_artifact_sha256 == sha
    assert verify_n2_state_artifact_bytes(payload, data).accepted_for_empirical_n3 is True

    with pytest.raises(ValueError, match="state artifact sha256 mismatch"):
        verify_n2_state_artifact_bytes(payload, b"tampered")


def test_descriptive_lane_cannot_smuggle_state_artifact_even_with_valid_fingerprint():
    payload = _base_payload(
        evidence_id="bat-no-rescue",
        handoff=_bat_handoff(),
        projection_summary={"effective_vertical_states": 4.0},
        gains=(-0.1, -0.2),
        artifact={
            "artifact_semantics": "empirical_species_support",
            "uri": "artifact://forbidden.npz",
            "sha256": "a" * 64,
            "media_type": "application/x-npz",
            "shape": [2, 3, 4],
            "axis_order": ["x", "y", "z"],
        },
    )

    with pytest.raises(ValueError, match="must not contain state_artifact"):
        inspect_n2_handoff_payload(payload)


def test_serialized_empirical_permission_is_rederived_not_trusted():
    handoff = _bat_handoff()
    handoff["handoff_category"] = "empirical_axis_resolved_supported"
    handoff["transferability_category"] = "generalizing"
    handoff["axis_resolved_species_state_allowed_for_empirical_n3"] = True
    # Deliberately leave no independently generalizing evidence in the gains.
    payload = _base_payload(
        evidence_id="forged-promotion",
        handoff=handoff,
        projection_summary={"effective_vertical_states": 4.0},
        gains=(-0.1, -0.2),
        artifact={
            "artifact_semantics": "empirical_species_support",
            "uri": "artifact://forged.npz",
            "sha256": "b" * 64,
            "media_type": "application/x-npz",
            "shape": [2, 3, 4],
            "axis_order": ["x", "y", "z"],
        },
    )

    with pytest.raises(ValueError, match="all supplied gains > 0"):
        inspect_n2_handoff_payload(payload)


def test_payload_fingerprint_tampering_fails_before_intake():
    payload = _base_payload(
        evidence_id="fingerprint-test",
        handoff=_bat_handoff(),
        projection_summary={"effective_vertical_states": 4.0},
        gains=(-0.1, -0.2),
    )
    payload["projection_summary"]["effective_vertical_states"] = 99.0

    with pytest.raises(ValueError, match="fingerprint mismatch"):
        inspect_n2_handoff_payload(payload)


def test_known_truth_state_is_only_admitted_for_method_testing():
    data = b"known truth state"
    handoff = {
        "evidence_scope": "known_truth",
        "support_semantics": "species_support",
        "axis_semantics_declared": True,
        "prospective_source_boundary_frozen": False,
        "thickness_estimable": True,
        "transferability_category": "generalizing",
        "handoff_category": "known_truth_method_state_only",
        "projection_summary_allowed": True,
        "axis_resolved_state_allowed_for_method_testing": True,
        "axis_resolved_species_state_allowed_for_empirical_n3": False,
        "reason_codes": ["known_truth_state_not_empirical_species_evidence"],
    }
    payload = _base_payload(
        evidence_id="known-truth-method-fixture",
        handoff=handoff,
        projection_summary={"effective_vertical_states": 3.0},
        gains=(),
        artifact={
            "artifact_semantics": "known_truth_method_state",
            "uri": "artifact://known-truth.npz",
            "sha256": hashlib.sha256(data).hexdigest(),
            "media_type": "application/x-npz",
            "shape": [2, 3, 4],
            "axis_order": ["x", "y", "z"],
        },
    )

    intake = inspect_n2_handoff_payload(payload)
    assert intake.accepted_for_method_testing is True
    assert intake.accepted_for_empirical_n3 is False
