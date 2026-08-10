"""Pre-outcome source audit and repair contract for Tanzania current flow.

The released Dryad scripts are retained as a reproducibility target, but two
source-level ambiguities make their literal outputs unsuitable for a fair
held-out benchmark:

* focal points are rasterized without an explicit ``field``, so the raster
  package assigns row indices rather than the declared ``patch_number`` IDs;
* source-patch resistance distances are divided by ``log10(area_ha)``, which
  is non-positive for patches at or below one hectare.

This module detects those conditions deterministically and freezes separate
roles for literal source reproduction and the leakage-safe held-out
competitor. It never reads a species outcome, fits a model, runs
Circuitscape, or computes predictive performance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


AUDIT_SCHEMA_VERSION = "tanzania_current_flow_source_audit_v1"
RESISTANCE_LEVELS = (1, 2, 4, 8, 16, 32, 64, 128)
PRIMARY_HELDOUT_AREA_WEIGHT = "inverse_log10_1p_area_ha"
SENSITIVITY_HELDOUT_AREA_WEIGHT = "inverse_area_ha"
RELEASED_AREA_WEIGHT = "inverse_log10_area_ha"


REGION_LANDCOVER_MAPPING: dict[str, dict[str, str]] = {
    "E": {
        "1": "other_agriculture",
        "2": "forest",
        "3": "tea",
        "4": "eucalyptus",
    },
    "W": {
        "1": "other_agriculture",
        "2": "eucalyptus",
        "3": "forest",
        "4": "tea",
    },
}


@dataclass(frozen=True)
class FocalIdentityRow:
    implicit_focal_id: int
    patch_number: int
    name: str


@dataclass(frozen=True)
class AreaWeightProblem:
    patch_number: int
    name: str
    area_ha: float
    log10_area_ha: float
    released_weight_status: str


def canonical_json(value: object) -> str:
    """Return a stable JSON representation suitable for source fingerprints."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def enumerate_resistance_combinations() -> tuple[dict[str, int], ...]:
    """Return the frozen 8 x 8 x 8 nonforest resistance grid."""
    return tuple(
        {
            "eucalyptus": int(eucalyptus),
            "tea": int(tea),
            "other_agriculture": int(other),
        }
        for eucalyptus in RESISTANCE_LEVELS
        for tea in RESISTANCE_LEVELS
        for other in RESISTANCE_LEVELS
    )


def _positive_area(value: object, label: str) -> float:
    try:
        area = float(value)
    except Exception as exc:  # pragma: no cover - defensive conversion path
        raise ValueError(f"{label} must be numeric: {value!r}") from exc
    if not math.isfinite(area) or area <= 0.0:
        raise ValueError(f"{label} must be finite and positive: {value!r}")
    return area


def released_area_weight(area_ha: float) -> float:
    """Evaluate the literal released ``1 / log10(area_ha)`` source weight.

    The function deliberately returns negative values for areas below one
    hectare and raises for the singular one-hectare case. It exists only for
    faithful source auditing and must not be used in the held-out competitor.
    """
    area = _positive_area(area_ha, "area_ha")
    transformed = math.log10(area)
    if transformed == 0.0:
        raise ValueError("released area weight is undefined at exactly one hectare")
    return 1.0 / transformed


def heldout_area_weight(area_ha: float, mode: str = PRIMARY_HELDOUT_AREA_WEIGHT) -> float:
    """Return a predeclared positive, monotone source-patch weight.

    ``inverse_log10_1p_area_ha`` is the primary minimal domain repair: it
    preserves logarithmic compression and the intended ordering that smaller
    source patches receive larger weights, while remaining finite and
    positive for every positive area. ``inverse_area_ha`` is a separately
    declared sensitivity convention.
    """
    area = _positive_area(area_ha, "area_ha")
    if mode == PRIMARY_HELDOUT_AREA_WEIGHT:
        return 1.0 / math.log10(1.0 + area)
    if mode == SENSITIVITY_HELDOUT_AREA_WEIGHT:
        return 1.0 / area
    raise ValueError(f"unknown held-out area weighting mode: {mode!r}")


def aggregate_weighted_resistance(
    resistance_distances: Sequence[float],
    source_areas_ha: Sequence[float],
    *,
    mode: str = PRIMARY_HELDOUT_AREA_WEIGHT,
) -> float:
    """Aggregate pairwise resistance distances with a frozen source-area rule."""
    if len(resistance_distances) != len(source_areas_ha) or not resistance_distances:
        raise ValueError("resistance distances and source areas must align and be non-empty")
    total = 0.0
    for index, (distance_raw, area_raw) in enumerate(
        zip(resistance_distances, source_areas_ha, strict=True)
    ):
        try:
            distance = float(distance_raw)
        except Exception as exc:  # pragma: no cover - defensive conversion path
            raise ValueError(f"resistance distance {index} must be numeric") from exc
        if not math.isfinite(distance) or distance < 0.0:
            raise ValueError("resistance distances must be finite and non-negative")
        total += distance * heldout_area_weight(area_raw, mode)
    if not math.isfinite(total) or total < 0.0:
        raise RuntimeError("held-out weighted resistance must be finite and non-negative")
    return float(total)


def audit_focal_identity(
    rows: Sequence[Mapping[str, object]],
    *,
    region: str,
) -> dict[str, Any]:
    """Compare raster-package implicit point IDs with declared patch numbers."""
    if region not in {"E", "W"}:
        raise ValueError(f"unexpected region: {region!r}")
    if len(rows) < 2:
        raise ValueError("at least two node rows are required")

    mapping: list[FocalIdentityRow] = []
    seen_patch: set[int] = set()
    seen_name: set[str] = set()
    for implicit_id, row in enumerate(rows, start=1):
        patch_number = int(row["patch_number"])
        name = str(row["name"]).strip()
        if patch_number <= 0 or patch_number in seen_patch:
            raise ValueError(f"duplicate or invalid patch_number in region {region}")
        if not name or name in seen_name:
            raise ValueError(f"duplicate or blank node name in region {region}")
        mapping.append(FocalIdentityRow(implicit_id, patch_number, name))
        seen_patch.add(patch_number)
        seen_name.add(name)

    expected = set(range(1, len(rows) + 1))
    if seen_patch != expected:
        raise ValueError(
            f"region {region} patch_number values must be exactly 1..{len(rows)}"
        )
    mapping_payload = [row.__dict__ for row in mapping]
    mismatches = [row for row in mapping if row.implicit_focal_id != row.patch_number]
    return {
        "region": region,
        "n_nodes": len(mapping),
        "implicit_field_rule": "attribute_index_1_to_n",
        "explicit_benchmark_field": "patch_number",
        "n_identity_matches": len(mapping) - len(mismatches),
        "n_identity_mismatches": len(mismatches),
        "implicit_identity_matches_patch_number": not mismatches,
        "row_to_patch_mapping_sha256": canonical_sha256(mapping_payload),
        "row_to_patch_mapping": mapping_payload,
    }


def audit_area_weights(
    rows: Sequence[Mapping[str, object]],
    *,
    region: str,
) -> dict[str, Any]:
    """Audit the released and repaired source-area weighting domains."""
    if region not in {"E", "W"}:
        raise ValueError(f"unexpected region: {region!r}")
    problems: list[AreaWeightProblem] = []
    all_areas: list[float] = []
    for row in rows:
        patch_number = int(row["patch_number"])
        name = str(row["name"]).strip()
        area = _positive_area(row["Area_ha"], f"{region} Area_ha")
        all_areas.append(area)
        transformed = math.log10(area)
        if transformed < 0.0:
            status = "negative"
        elif transformed == 0.0:
            status = "undefined"
        else:
            status = "positive"
        if status != "positive":
            problems.append(
                AreaWeightProblem(
                    patch_number=patch_number,
                    name=name,
                    area_ha=area,
                    log10_area_ha=transformed,
                    released_weight_status=status,
                )
            )

    for mode in (PRIMARY_HELDOUT_AREA_WEIGHT, SENSITIVITY_HELDOUT_AREA_WEIGHT):
        ordered = sorted((area, heldout_area_weight(area, mode)) for area in all_areas)
        if any(not math.isfinite(weight) or weight <= 0.0 for _, weight in ordered):
            raise RuntimeError(f"{mode} did not produce finite positive weights")
        for (area_a, weight_a), (area_b, weight_b) in zip(ordered, ordered[1:]):
            if area_a < area_b and not weight_a > weight_b:
                raise RuntimeError(f"{mode} is not strictly decreasing with patch area")

    return {
        "region": region,
        "n_nodes": len(rows),
        "released_formula": RELEASED_AREA_WEIGHT,
        "released_nonpositive_or_undefined_count": len(problems),
        "released_problem_patch_numbers": sorted(problem.patch_number for problem in problems),
        "released_problem_rows": [problem.__dict__ for problem in problems],
        "primary_heldout_formula": PRIMARY_HELDOUT_AREA_WEIGHT,
        "sensitivity_heldout_formula": SENSITIVITY_HELDOUT_AREA_WEIGHT,
        "heldout_formulas_positive_for_all_nodes": True,
        "heldout_formulas_strictly_decrease_with_area": True,
    }


def summarize_current_flow_source_contract(
    *,
    east_rows: Sequence[Mapping[str, object]],
    west_rows: Sequence[Mapping[str, object]],
    script_evidence: Mapping[str, bool],
    raster_evidence: Mapping[str, object],
) -> dict[str, Any]:
    """Build the complete outcome-free current-flow source audit report."""
    if not script_evidence or not all(bool(value) for value in script_evidence.values()):
        missing = sorted(key for key, value in script_evidence.items() if not value)
        raise ValueError(f"official current-flow script evidence missing: {missing}")

    combinations = enumerate_resistance_combinations()
    focal = {
        "E": audit_focal_identity(east_rows, region="E"),
        "W": audit_focal_identity(west_rows, region="W"),
    }
    area = {
        "E": audit_area_weights(east_rows, region="E"),
        "W": audit_area_weights(west_rows, region="W"),
    }
    report: dict[str, Any] = {
        "status": "tanzania_current_flow_source_contract_frozen_before_outcomes",
        "schema_version": AUDIT_SCHEMA_VERSION,
        "source": {
            "doi": "10.5061/dryad.p042h0c",
            "version_id": 23134,
            "script_evidence": dict(sorted(script_evidence.items())),
            "raster_evidence": dict(raster_evidence),
        },
        "resistance_grid": {
            "levels": list(RESISTANCE_LEVELS),
            "axes": ["eucalyptus", "tea", "other_agriculture"],
            "n_combinations": len(combinations),
            "combinations_sha256": canonical_sha256(list(combinations)),
            "regional_landcover_mapping": REGION_LANDCOVER_MAPPING,
        },
        "released_source_audit": {
            "focal_identity": focal,
            "source_area_weighting": area,
            "literal_released_script_role": "source_reproduction_diagnostic_only",
            "literal_released_script_admissible_for_heldout_comparison": False,
        },
        "heldout_competitor_repairs": {
            "focal_raster_field": "patch_number",
            "primary_source_area_weighting": PRIMARY_HELDOUT_AREA_WEIGHT,
            "sensitivity_source_area_weighting": SENSITIVITY_HELDOUT_AREA_WEIGHT,
            "primary_weight_formula": "1 / log10(1 + area_ha)",
            "sensitivity_weight_formula": "1 / area_ha",
            "repair_selection_basis": (
                "source code and geometry only; chosen before current-flow, EOG, "
                "probability, loss, AUC, or species-performance calculation"
            ),
            "rationale": (
                "explicit patch identities preserve downstream patch_number joins; "
                "log10(1 + area_ha) is a positive monotone domain repair that "
                "preserves logarithmic compression and the declared smaller-source "
                "patch weighting direction"
            ),
        },
        "scientific_boundary": {
            "species_outcomes_inspected": False,
            "circuitscape_run": False,
            "current_flow_computed": False,
            "resistance_selected": False,
            "occurrence_model_fitted": False,
            "eog_performance_inspected": False,
        },
    }
    report["audit_fingerprint"] = canonical_sha256(report)
    return report
