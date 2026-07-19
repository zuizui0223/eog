import dataclasses

import numpy as np
import pytest

from eog import (
    AnalysisManifest,
    ReferenceDeclaration,
    allowed_claim_scope,
    build_result_bundle,
    compare_geometry,
    fit_robust_reference,
    manifest_fingerprint,
    reference_fingerprint,
    validate_manifest,
)


def _manifest(reference, declaration):
    return AnalysisManifest(
        analysis_id="extent-a-vs-b",
        scientific_comparison="Compare environmental extent of B against A",
        feature_names=("bio1", "bio12"),
        feature_rationale="Temperature and precipitation were selected before outcomes.",
        group_a="A",
        group_b="B",
        reference_declaration=declaration,
        reference_fingerprint=reference_fingerprint(reference),
        primary_metric="span",
        supplementary_metrics=("gap_strength",),
        support_class=None,
        resample_fraction=0.8,
        n_resamples=40,
        n_permutations=40,
        random_seed=3,
        allowed_claim=allowed_claim_scope(declaration),
        prohibited_claims=("causal niche expansion", "occupancy probability"),
        software_version="0.1.0",
        input_fingerprints=("input-a", "input-b"),
    )


def test_manifest_is_deterministic_and_sensitive():
    rng = np.random.default_rng(1)
    reference = fit_robust_reference(rng.normal(size=(100, 2)), provenance="external")
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="independent calibration sample",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
    )
    manifest = _manifest(reference, declaration)
    validate_manifest(manifest)
    assert manifest_fingerprint(manifest) == manifest_fingerprint(manifest)
    changed = dataclasses.replace(manifest, resample_fraction=0.7)
    assert manifest_fingerprint(changed) != manifest_fingerprint(manifest)


def test_bundle_rejects_undeclared_reference():
    rng = np.random.default_rng(2)
    a = rng.normal(size=(60, 2))
    b = 2 * rng.normal(size=(60, 2))
    reference = fit_robust_reference(rng.normal(size=(100, 2)), provenance="external")
    other_reference = fit_robust_reference(rng.normal(size=(100, 2)), provenance="external other")
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="independent calibration sample",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
    )
    manifest = _manifest(reference, declaration)
    contrast = compare_geometry(a, b, other_reference, n_resamples=20, n_permutations=20)
    with pytest.raises(ValueError, match="reference"):
        build_result_bundle(manifest, contrast)


def test_report_preserves_ambiguity():
    rng = np.random.default_rng(8)
    a = rng.normal(size=(70, 2))
    b = rng.normal(size=(70, 2))
    reference = fit_robust_reference(rng.normal(size=(100, 2)), provenance="external")
    declaration = ReferenceDeclaration(
        mode="external",
        intent="prospective",
        source_description="independent calibration sample",
        fitted_before_evaluation=True,
        includes_evaluation_groups=False,
    )
    manifest = _manifest(reference, declaration)
    contrast = compare_geometry(a, b, reference, n_resamples=30, n_permutations=30, random_state=5)
    bundle = build_result_bundle(manifest, contrast)
    if contrast.ambiguous:
        assert "ambiguous" in bundle.report_text
