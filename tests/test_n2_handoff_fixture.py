import json
from pathlib import Path

import pytest

from eog.n2_handoff import inspect_n2_handoff_payload


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "odsp_n2_bat_handoff_payload.json"


def test_frozen_odsp_bat_payload_is_compatible_with_eog_intake():
    payload = json.loads(FIXTURE.read_text())
    intake = inspect_n2_handoff_payload(payload)

    assert intake.evidence_id == "tadarida-teniotis-n2-terminal"
    assert intake.fingerprint_verified is True
    assert intake.handoff_category == "descriptive_projection_only"
    assert intake.projection_summary_available is True
    assert intake.accepted_for_empirical_n3 is False
    assert intake.accepted_for_method_testing is False
    assert intake.state_artifact_uri is None
    assert intake.state_artifact_sha256 is None


def test_frozen_odsp_bat_payload_preserves_terminal_n2_numbers():
    payload = json.loads(FIXTURE.read_text())

    assert payload["projection_summary"]["H_Z_given_XY_nats"] == pytest.approx(
        1.3918623004770097
    )
    assert payload["projection_summary"]["effective_vertical_states"] == pytest.approx(
        4.022333876564191
    )
    assert payload["transferability"]["independent_gains"] == pytest.approx(
        [-0.43541033813280833, -0.021938657402345435]
    )
    assert payload["state_artifact"] is None
