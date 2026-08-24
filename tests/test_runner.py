import csv
import os
import subprocess
import sys
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


def test_ri_raccoon_response_blind_deployment_preflight():
    """Candidate-only execution route through a workflow already present on main.

    The scientific contract and executable live under validation/.  This test runs only
    for the dedicated fresh-candidate PR branch and therefore cannot silently become a
    network dependency of ordinary package tests.
    """
    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or ""
    if branch != "agent/ri-raccoon-fresh-paired-preflight":
        pytest.skip("Rhode Island fresh-candidate preflight is branch-scoped")
    script = Path(__file__).resolve().parents[1] / "validation/ri_raccoon_paired_complementarity/deployment_preflight.py"
    completed = subprocess.run([sys.executable, str(script)], check=False)
    assert completed.returncode == 0
