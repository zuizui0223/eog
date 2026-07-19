"""Frozen analysis manifests and result-bundle validation for comparative EOG."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

from .reference_policy import ReferenceDeclaration, allowed_claim_scope, validate_reference_declaration
from .uncertainty import ComparativeContrast


@dataclass(frozen=True)
class AnalysisManifest:
    analysis_id: str
    scientific_comparison: str
    feature_names: tuple[str, ...]
    feature_rationale: str
    group_a: str
    group_b: str
    reference_declaration: ReferenceDeclaration
    reference_fingerprint: str
    primary_metric: str
    supplementary_metrics: tuple[str, ...]
    support_class: str | None
    resample_fraction: float
    n_resamples: int
    n_permutations: int
    random_seed: int
    allowed_claim: str
    prohibited_claims: tuple[str, ...]
    software_version: str
    input_fingerprints: tuple[str, str]
    frozen_before_outcomes: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["reference_declaration"] = self.reference_declaration.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AnalysisManifest":
        values = dict(payload)
        values["reference_declaration"] = ReferenceDeclaration.from_dict(
            values["reference_declaration"]
        )
        for field in ("feature_names", "supplementary_metrics", "prohibited_claims", "input_fingerprints"):
            values[field] = tuple(values[field])
        return cls(**values)


@dataclass(frozen=True)
class ResultBundle:
    manifest_fingerprint: str
    contrast: ComparativeContrast
    report_text: str


def manifest_fingerprint(manifest: AnalysisManifest) -> str:
    payload = json.dumps(manifest.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_manifest(manifest: AnalysisManifest) -> None:
    if not manifest.analysis_id.strip() or not manifest.scientific_comparison.strip():
        raise ValueError("analysis_id and scientific_comparison must be non-empty")
    if not manifest.feature_names or len(set(manifest.feature_names)) != len(manifest.feature_names):
        raise ValueError("feature_names must be non-empty and unique")
    if not manifest.feature_rationale.strip():
        raise ValueError("feature_rationale must be non-empty")
    if manifest.group_a == manifest.group_b:
        raise ValueError("group labels must differ")
    if manifest.primary_metric not in {"span", "continuity", "gap_strength"}:
        raise ValueError("unsupported primary_metric")
    allowed_supplementary = {"span", "continuity", "gap_strength", "silhouette", "core_bridge"}
    if not set(manifest.supplementary_metrics).issubset(allowed_supplementary):
        raise ValueError("unsupported supplementary metric")
    if manifest.primary_metric != "span" and not str(manifest.support_class or "").strip():
        raise ValueError("tree-sensitive primary metrics require support_class")
    if not 0.25 <= manifest.resample_fraction <= 1.0:
        raise ValueError("resample_fraction must lie in [0.25, 1]")
    if manifest.n_resamples < 20 or manifest.n_permutations < 20:
        raise ValueError("resampling counts must each be at least 20")
    if len(manifest.input_fingerprints) != 2 or not all(manifest.input_fingerprints):
        raise ValueError("two non-empty input fingerprints are required")
    if not manifest.reference_fingerprint.strip():
        raise ValueError("reference_fingerprint must be non-empty")
    if not manifest.frozen_before_outcomes:
        raise ValueError("manifest must be frozen before outcomes are inspected")
    validate_reference_declaration(manifest.reference_declaration)
    expected_claim = allowed_claim_scope(manifest.reference_declaration)
    if manifest.allowed_claim != expected_claim:
        raise ValueError("allowed_claim does not match the reference declaration")
    if not manifest.prohibited_claims:
        raise ValueError("at least one prohibited claim must be declared")


def render_result_text(manifest: AnalysisManifest, contrast: ComparativeContrast) -> str:
    validate_manifest(manifest)
    if contrast.metric != manifest.primary_metric:
        raise ValueError("contrast metric was not declared as primary")
    if contrast.reference_fingerprint != manifest.reference_fingerprint:
        raise ValueError("contrast reference does not match the manifest")
    if contrast.support_class != manifest.support_class:
        raise ValueError("contrast support class does not match the manifest")
    direction = "B greater than A" if contrast.estimate > 0 else "B lower than A" if contrast.estimate < 0 else "no directional contrast"
    status = "direction supported under the declared diagnostics" if contrast.direction_supported else "ambiguous under the declared diagnostics"
    return (
        f"{manifest.scientific_comparison}: {direction}; effect={contrast.estimate:.6g}, "
        f"sensitivity interval=[{contrast.interval_low:.6g}, {contrast.interval_high:.6g}], "
        f"direction stability={contrast.direction_stability:.3f}, "
        f"permutation p={contrast.permutation_pvalue:.3f}; {status}. "
        f"Claim scope: {manifest.allowed_claim}"
    )


def build_result_bundle(manifest: AnalysisManifest, contrast: ComparativeContrast) -> ResultBundle:
    text = render_result_text(manifest, contrast)
    return ResultBundle(
        manifest_fingerprint=manifest_fingerprint(manifest),
        contrast=contrast,
        report_text=text,
    )
