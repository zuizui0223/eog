import json
from pathlib import Path

import pytest

from validation.bam_greatlakes_barrier_external_bridge_v1.gate1_readme import (
    Gate1Stop,
    evaluate_readme_text,
)


HERE = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "bam_greatlakes_barrier_external_bridge_v1"
)


def _inputs():
    gate0 = json.loads(
        (HERE / "gate0_dryad_identity_certificate.json").read_text(encoding="utf-8")
    )
    auth = json.loads(
        (HERE / "gate1_execution_authorization.json").read_text(encoding="utf-8")
    )
    return gate0, auth


def _fixture_readme(auth):
    exp = auth["readme_expectations"]
    return "\n".join(
        [
            "# files",
            *exp["required_file_names"],
            "# habitat columns",
            ", ".join(exp["required_habitat_columns"]),
            "# catch columns",
            ", ".join(exp["required_catch_columns"]),
            "# periods",
            " and ".join(exp["required_period_tokens"]),
        ]
    )


def test_readme_schema_passes_only_when_all_frozen_tokens_present():
    gate0, auth = _inputs()
    result = evaluate_readme_text(_fixture_readme(auth), gate0, auth)
    assert result["status"] == "readme_schema_ready"
    assert result["rds_payload_requests"] == 0
    assert result["rds_payload_bytes_opened"] == 0
    assert result["model_fits"] == 0


def test_missing_habitat_field_stops():
    gate0, auth = _inputs()
    text = _fixture_readme(auth).replace("prop_boulder", "removed_field")
    with pytest.raises(Gate1Stop, match="habitat schema tokens"):
        evaluate_readme_text(text, gate0, auth)


def test_missing_period_semantics_stops():
    gate0, auth = _inputs()
    text = _fixture_readme(auth).replace("90s", "old_period")
    with pytest.raises(Gate1Stop, match="period tokens"):
        evaluate_readme_text(text, gate0, auth)
