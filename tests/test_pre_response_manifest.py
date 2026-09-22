import json
import sys

import pytest

from eog.v2.cli import pre_response_freeze_main
from eog.v2.pre_response_manifest import compile_pre_response_manifest_file


def _write_fixture(tmp_path, *, tampa_like=False, include_evaluation=True):
    (tmp_path / "registry.csv").write_text(
        "site,x,y,component\n"
        "A,0,0,c\n"
        "B,1,0,c\n"
        "C,2,0,c\n",
        encoding="utf-8",
    )
    (tmp_path / "effort.csv").write_text(
        "unit,node,context,fold,eligible,analysis_role,effort_days\n"
        "A|t0,A,t0,1,true,initialization_only,7\n"
        "B|t0,B,t0,2,true,initialization_only,7\n"
        "C|t0,C,t0,3,true,initialization_only,7\n"
        "A|t1,A,t1,1,true,scored,7\n"
        "B|t1,B,t1,2,true,scored,7\n"
        "C|t1,C,t1,3,true,scored,7\n",
        encoding="utf-8",
    )
    worlds = {
        "schema": "eog.test_world_family.v1",
        "node_ids": ["A", "B", "C"],
        "worlds": {
            "local": [
                [0, 1, 0],
                [1, 0, 0],
                [0, 0, 0],
            ],
            "open": [
                [0, 1, 1],
                [1, 0, 1],
                [1, 1, 0],
            ],
        },
        "world_semantics": {
            "local": {"kind": "local"},
            "open": {"kind": "external_open"},
        },
        "structural_world_ids": ["local", "open"],
    }
    (tmp_path / "worlds.json").write_text(
        json.dumps(worlds, indent=2),
        encoding="utf-8",
    )

    manifest = {
        "schema": "eog.pre_response_manifest.v1",
        "registry_table": {
            "path": "registry.csv",
            "artifact_id": "registry",
            "schema": {
                "roles": [
                    {"role": "node_id", "aliases": ["site"]},
                    {"role": "x", "aliases": ["x"]},
                    {"role": "y", "aliases": ["y"]},
                    {"role": "component_id", "aliases": ["component"]},
                ],
                "allow_unmapped_columns": False,
            },
            "coordinate_policy": {
                "tolerance": 0.0,
                "units": "synthetic",
                "representative_policy": "median",
            },
        },
        "effort_table": {
            "path": "effort.csv",
            "artifact_id": "effort",
            "schema": {
                "roles": [
                    {"role": "unit_id", "aliases": ["unit"]},
                    {"role": "node_id", "aliases": ["node"]},
                    {"role": "context_id", "aliases": ["context"]},
                    {"role": "fold", "aliases": ["fold"]},
                    {"role": "eligible", "aliases": ["eligible"]},
                    {"role": "analysis_role", "aliases": ["analysis_role"]},
                    {"role": "effort_days", "aliases": ["effort_days"]},
                ],
                "allow_unmapped_columns": False,
            },
            "eligible_true_tokens": ["true"],
            "eligible_false_tokens": ["false"],
            "evidence_fields": ["effort_days"],
            "context_order": ["t0", "t1"],
            "policy": {
                "unit_definition": "node x context",
                "eligibility_rule": "effort_days >= 7",
                "unsurveyed_rule": "effort_days < 7 is outside endpoint",
                "evidence_source": "response_independent_effort",
            },
        },
        "world_family": {
            "path": "worlds.json",
            "artifact_id": "worlds",
            "horizon": 2,
        },
        "structural_adequacy": {
            "min_largest_weak_component_fraction": 1.0,
            "max_isolated_node_fraction": 0.0,
            "require_at_least_one_world_pass": True,
        },
        "observation_contract": {
            "mode": "explicit_binary_tokens",
            "endpoint_name": "node-context detection",
            "positive_semantics": "explicit token 1",
            "negative_semantics": "explicit token 0",
            "unavailable_semantics": "explicit unavailable token",
            "zero_interpretation": "recorded non-detection only",
        },
        "predictive_state": {
            "repeated_measure_endpoint": True,
            "train_generator_id": (
                "train_static" if tampa_like else "sequential_preoutcome"
            ),
            "serve_generator_id": (
                "serve_static" if tampa_like else "sequential_preoutcome"
            ),
            "refresh_policy": "static_reused" if tampa_like else "sequential_context",
            "source_policy": (
                "lexicographic_single_source"
                if tampa_like
                else "symmetric_sources"
            ),
            "source_label_invariant": not tampa_like,
            "baseline_contains_spatial_coordinates": True,
        },
        "baseline_fields": [],
    }
    if include_evaluation:
        manifest["predictive_evaluation"] = {
            "learner": "frozen_test_learner",
            "metric": "binary_log_loss",
            "split": "declared_fold",
        }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def test_manifest_compiles_complete_generic_pre_response_path(tmp_path):
    manifest = _write_fixture(tmp_path)
    result = compile_pre_response_manifest_file(manifest)

    assert result["counts"] == {
        "node_count": 3,
        "context_count": 2,
        "scored_candidate_count": 3,
        "initialization_count": 3,
        "unsurveyed_count": 0,
        "declared_world_count": 2,
        "structural_world_count": 2,
    }
    assert result["statuses"]["structural"] == "structural_ready"
    assert result["statuses"]["effort"] == "response_independent_effort_declared"
    assert result["statuses"]["observation"] == "explicit_binary_tokens"
    assert result["statuses"]["predictive"] == "predictive_complement_candidate"
    assert result["statuses"]["structural_response_access_allowed"] is True
    assert result["statuses"]["predictive_outcome_access_allowed"] is True
    assert result["statuses"]["predictive_use_allowed"] is True
    assert len(result["result_fingerprint"]) == 64


def test_manifest_is_deterministic_for_identical_files(tmp_path):
    manifest = _write_fixture(tmp_path)
    left = compile_pre_response_manifest_file(manifest)
    right = compile_pre_response_manifest_file(manifest)
    assert left["result_fingerprint"] == right["result_fingerprint"]
    assert left["fingerprints"]["certificate"] == right["fingerprints"]["certificate"]


def test_tampa_like_predictive_design_is_withheld_before_outcome_access(tmp_path):
    manifest = _write_fixture(tmp_path, tampa_like=True)
    result = compile_pre_response_manifest_file(manifest)
    assert result["statuses"]["structural_response_access_allowed"] is True
    assert result["statuses"]["predictive"] == "ineligible_generation_shift"
    assert result["statuses"]["predictive_use_allowed"] is False
    assert result["statuses"]["predictive_outcome_access_allowed"] is False


def test_predictive_evaluation_contract_is_required_for_predictive_access(tmp_path):
    manifest = _write_fixture(tmp_path, include_evaluation=False)
    result = compile_pre_response_manifest_file(manifest)
    assert result["statuses"]["predictive"] == "predictive_complement_candidate"
    assert result["statuses"]["predictive_use_allowed"] is True
    assert result["statuses"]["predictive_outcome_access_allowed"] is False


def test_manifest_rejects_paths_outside_its_directory(tmp_path):
    outside = tmp_path.parent / "outside.csv"
    outside.write_text("site,x,y,component\nA,0,0,c\n", encoding="utf-8")
    manifest_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["registry_table"]["path"] = "../outside.csv"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="escapes the manifest directory"):
        compile_pre_response_manifest_file(manifest_path)


def test_manifest_rejects_undeclared_eligible_token(tmp_path):
    manifest_path = _write_fixture(tmp_path)
    effort = (tmp_path / "effort.csv").read_text(encoding="utf-8")
    (tmp_path / "effort.csv").write_text(
        effort.replace("A|t1,A,t1,1,true,scored,7", "A|t1,A,t1,1,YES,scored,7"),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="neither a declared true nor false token"):
        compile_pre_response_manifest_file(manifest_path)


def test_cli_writes_certificate_result(tmp_path, monkeypatch, capsys):
    manifest = _write_fixture(tmp_path)
    output = tmp_path / "certificate.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v2-pre-response-freeze",
            "--manifest",
            str(manifest),
            "--output",
            str(output),
        ],
    )
    assert pre_response_freeze_main() == 0
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["statuses"]["predictive_outcome_access_allowed"] is True
    printed = json.loads(capsys.readouterr().out)
    assert printed["result_fingerprint"] == saved["result_fingerprint"]


def test_cli_refuses_overwrite_without_force(tmp_path, monkeypatch):
    manifest = _write_fixture(tmp_path)
    output = tmp_path / "certificate.json"
    output.write_text("existing", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "eog-v2-pre-response-freeze",
            "--manifest",
            str(manifest),
            "--output",
            str(output),
        ],
    )
    with pytest.raises(SystemExit):
        pre_response_freeze_main()
    assert output.read_text(encoding="utf-8") == "existing"


def test_manifest_rejects_string_boolean_instead_of_json_boolean(tmp_path):
    manifest_path = _write_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["predictive_state"]["source_label_invariant"] = "false"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(TypeError, match="must be a JSON boolean"):
        compile_pre_response_manifest_file(manifest_path)
