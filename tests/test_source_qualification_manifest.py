import json
import sys

from eog.v2.cli import source_qualify_main
from eog.v2.source_qualification_manifest import (
    compile_source_qualification_manifest,
)


def manifest():
    return {
        "schema": "eog.source_qualification_manifest.v1",
        "discovery": {
            "sources": [
                {
                    "source_id": "registry",
                    "path_or_name": "deployments.csv",
                    "declared_schema_fields": [
                        "deploymentID",
                        "latitude",
                        "longitude",
                    ],
                    "role": "registry",
                }
            ],
            "requirements": [{"role": "registry", "minimum_sources": 1}],
        },
        "source_identity_fingerprints": {"registry": "a" * 64},
        "transport": {
            "routes": [
                {
                    "route_id": "safe",
                    "route_type": "separate_safe_assets",
                    "qualified": True,
                    "safe_payload_bytes_opened": 100,
                    "response_payload_bytes_opened": 0,
                    "reason": "safe registry blob",
                }
            ]
        },
        "candidate_preflight": {
            "declaration": {
                "attempt_id": "test",
                "minimum_nodes": 30,
                "minimum_outer_units": 4,
                "minimum_repeated_nodes": 20,
                "require_response_blind_transport_qualification": True,
            },
            "evidence": {
                "source_identity": "source",
                "geometry_source_identity": "registry",
                "response_source_identity": "response",
                "geometry_response_separable": True,
                "coordinate_geometry_present": True,
                "node_count": 40,
                "outer_unit_count": 5,
                "repeated_node_count": 30,
                "response_blind_transport_qualified": True,
                "transport_qualification_fingerprint": "transport",
                "response_rows_opened": False,
                "response_bytes_opened": False,
            },
        },
    }


def test_manifest_compiles_ready_candidate_lock_certificate():
    result = compile_source_qualification_manifest(manifest())
    assert result["status"] == "ready_for_candidate_lock"
    assert result["candidate_lock_allowed"] is True
    assert result["blocking_layer"] is None


def test_manifest_preserves_transport_stop():
    value = manifest()
    value["transport"]["routes"][0]["qualified"] = False
    value["transport"]["routes"][0]["safe_payload_bytes_opened"] = 0
    value["transport"]["routes"][0]["reason"] = "route failed"
    result = compile_source_qualification_manifest(value)
    assert result["status"] == "stop_transport"
    assert result["candidate_lock_allowed"] is False
    assert result["blocking_layer"] == "transport"


def test_cli_writes_joined_certificate(tmp_path, monkeypatch, capsys):
    manifest_path = tmp_path / "manifest.json"
    output_path = tmp_path / "certificate.json"
    manifest_path.write_text(json.dumps(manifest()), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v2-source-qualify",
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
        ],
    )
    assert source_qualify_main() == 0
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["candidate_lock_allowed"] is True
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "ready_for_candidate_lock"
    assert printed["certificate_fingerprint"] == result["certificate"]["fingerprint"]
