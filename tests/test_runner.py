import csv
import json
import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from eog import (
    AnalysisManifest,
    ReferenceDeclaration,
    allowed_claim_scope,
    fit_robust_reference,
    load_audited_csv,
    reference_fingerprint,
    run_frozen_analysis,
)


def _manifest(reference, fingerprints=("pending-a", "pending-b")):
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="synthetic frozen reference",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
    )
    return AnalysisManifest(
        analysis_id="synthetic-runner-test",
        scientific_comparison="Synthetic B versus A extent",
        feature_names=("x", "y"),
        feature_rationale="Synthetic audit fixture",
        group_a="A",
        group_b="B",
        reference_declaration=declaration,
        reference_fingerprint=reference_fingerprint(reference),
        primary_metric="span",
        supplementary_metrics=(),
        support_class=None,
        resample_fraction=0.8,
        n_resamples=30,
        n_permutations=30,
        random_seed=4,
        allowed_claim=allowed_claim_scope(declaration),
        prohibited_claims=("suitability",),
        software_version="0.1.0",
        input_fingerprints=fingerprints,
    )


def _write(path, rows, header=("row_id", "group", "x", "y")):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_runner_is_deterministic_and_fingerprint_bound(tmp_path):
    rng = np.random.default_rng(5)
    reference = fit_robust_reference(rng.normal(size=(100, 2)), provenance="external")
    rows = []
    for i, values in enumerate(rng.normal(size=(30, 2))):
        rows.append((f"a{i}", "A", *values))
    for i, values in enumerate(2 * rng.normal(size=(30, 2))):
        rows.append((f"b{i}", "B", *values))
    path = tmp_path / "input.csv"
    _write(path, rows)
    draft = _manifest(reference)
    loaded = load_audited_csv(path, draft)
    manifest = replace(draft, input_fingerprints=(loaded.fingerprint_a, loaded.fingerprint_b))
    first = run_frozen_analysis(manifest, reference, loaded)
    second = run_frozen_analysis(manifest, reference, loaded)
    assert first == second
    assert first["contrast"]["estimate"] > 0


def test_runner_rejects_feature_order_and_duplicate_ids(tmp_path):
    reference = fit_robust_reference(np.arange(20, dtype=float).reshape(10, 2), provenance="external")
    manifest = _manifest(reference)
    wrong_order = tmp_path / "wrong.csv"
    _write(wrong_order, [("a", "A", 1, 2), ("b", "B", 3, 4)], header=("row_id", "group", "y", "x"))
    with pytest.raises(ValueError, match="columns"):
        load_audited_csv(wrong_order, manifest)
    duplicate = tmp_path / "duplicate.csv"
    _write(duplicate, [("same", "A", 1, 2), ("same", "B", 3, 4)])
    with pytest.raises(ValueError, match="duplicate row_id"):
        load_audited_csv(duplicate, manifest)


def test_azores_yellow_eel_pre_response_certificates_are_frozen_and_offline():
    """Validate committed pre-response evidence and authorization without remote access."""
    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or ""
    if branch != "agent/azores-yellow-eel-fresh-paired":
        pytest.skip("Azores yellow eel certificate check is branch-scoped")

    repository_root = Path(__file__).resolve().parents[1]
    root = repository_root / "validation/azores_yellow_eel_paired_complementarity"
    stage1 = json.loads((root / "stage1_certificate.json").read_text(encoding="utf-8"))
    header = json.loads((root / "header_certificate.json").read_text(encoding="utf-8"))
    full_freeze = json.loads((root / "full_freeze_spec.json").read_text(encoding="utf-8"))

    assert stage1["attempt_id"] == header["attempt_id"] == "azores_yellow_eel_receiver_week_fresh_paired_v1"
    assert stage1["status"] == "stage1_registry_availability_and_structural_pass"
    assert stage1["registry"]["study_station_count"] == 10
    assert stage1["animal_sources"]["yellow_target_tag_count"] == 36
    assert stage1["temporal_availability"]["full_scored_week_count"] == 49
    assert stage1["temporal_availability"]["calibration_week_count"] == 26
    assert stage1["temporal_availability"]["heldout_week_count"] == 23
    assert stage1["temporal_availability"]["full_four_week_heldout_block_count"] == 5
    assert stage1["structure"]["deduplicated_geometry_world_count"] == 3
    stage1_availability = stage1["temporal_availability"]["availability_fingerprint"]
    assert len(stage1_availability) == 64
    assert stage1_availability == full_freeze["node_geometry"]["availability_fingerprint"]
    assert stage1["response_firewall"] == {
        "response_payload_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }

    assert header["status"] == "response_header_schema_pass"
    assert header["authoritative_ci"]["run_id"] == 32798983182
    assert header["response_identity"]["md5"] == "20253e15293f8f06472f393f050f7c4a"
    assert header["response_header_bytes_opened"] == 163
    assert header["response_payload_requests"] == 0
    assert header["response_payload_bytes_opened"] == 0
    assert header["response_rows_opened"] is False
    assert header["response_values_opened"] is False
    assert header["model_fits"] == 0
    assert header["heldout_scores"] == 0

    from validation.azores_yellow_eel_paired_complementarity.pre_response_finalize import main

    main()
    finalized = json.loads(
        (repository_root / "build/azores_yellow_eel_pre_response/pre_response_finalize.json").read_text(
            encoding="utf-8"
        )
    )
    assert finalized["status"] == "authorized_once_only_exact_count_gate_required"
    assert len(finalized["required_freeze_keys"]) == 16
    assert len(finalized["section_fingerprints"]) == 16
    assert finalized["prospective_estimability_status"] == "uncertain_pre_response"
    assert finalized["response_rows_opened"] is False
    assert finalized["response_values_opened"] is False
    assert finalized["model_fits"] == 0
    assert finalized["heldout_scores"] == 0
