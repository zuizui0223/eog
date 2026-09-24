from __future__ import annotations

import csv
from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Mapping

from eog.v2.balanced_spatial_folds import build_balanced_spatial_folds
from eog.v2.pre_response_manifest import compile_pre_response_manifest
from validation.algar_restoration_v2_source_qualification.evaluate import (
    evaluate as evaluate_source,
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _csv_bytes(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _parse_source_rows(raw: bytes) -> list[dict[str, str]]:
    text = raw.decode("utf-8-sig")
    from io import StringIO

    reader = csv.DictReader(StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("deployments source has no header")
    rows = list(reader)
    if not rows:
        raise ValueError("deployments source is empty")
    return rows


def _valid_interval(start: str, end: str) -> bool:
    if not start or not end or start == "NA" or end == "NA":
        return False
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        return False
    return end_date > start_date


def _derived_identity(raw: bytes) -> dict[str, object]:
    return {"sha256": _sha256(raw), "bytes": len(raw)}


def build_preresponse(
    contract: Mapping[str, object],
    source_contract: dict[str, object],
    deployments_raw: bytes,
    *,
    output_dir: Path,
) -> dict[str, object]:
    """Build and compile the response-unopened Algar v3 pre-response manifest."""

    source_result = evaluate_source(
        source_contract,
        {"deployments": deployments_raw},
    )
    predecessor = contract["predecessor"]
    if not source_result["candidate_lock_allowed"]:
        raise ValueError("source qualification no longer permits candidate lock")
    if (
        source_result["certificate_fingerprint"]
        != predecessor["source_qualification_certificate_fingerprint"]
    ):
        raise ValueError("source qualification certificate fingerprint drift")

    canonical = source_result["registry"]["canonical_nodes"]
    node_ids = tuple(sorted(canonical))
    coordinates = {
        node_id: (
            float(canonical[node_id]["longitude"]),
            float(canonical[node_id]["latitude"]),
        )
        for node_id in node_ids
    }
    fold_contract = contract["spatial_outer_folds"]
    folds = build_balanced_spatial_folds(
        node_ids,
        coordinates,
        n_folds=int(fold_contract["n_folds"]),
        metric=str(fold_contract["metric"]),
    )

    source_rows = _parse_source_rows(deployments_raw)
    by_node: dict[str, list[dict[str, str]]] = {}
    for row in source_rows:
        node_id = str(row.get("placename", "")).strip()
        if not node_id:
            raise ValueError("source deployment row has blank placename")
        by_node.setdefault(node_id, []).append(row)

    if set(by_node) != set(node_ids):
        raise ValueError("deployment placenames differ from locked canonical nodes")

    registry_rows: list[dict[str, object]] = []
    effort_rows: list[dict[str, object]] = []
    unsurveyed_ids: list[str] = []
    feature_type_by_node: dict[str, str] = {}

    context_order = tuple(contract["effort_context"]["context_order"])
    if context_order != ("phase1", "phase2", "phase3"):
        raise ValueError("Algar v3 context order drift")

    for node_id in node_ids:
        rows = sorted(
            by_node[node_id],
            key=lambda row: (
                str(row.get("start_date", "")),
                str(row.get("deployment_id", "")),
            ),
        )
        if len(rows) != 3:
            raise ValueError(
                f"node {node_id!r} expected exactly 3 deployments, observed {len(rows)}"
            )

        feature_types = {
            str(row.get("feature_type", "")).strip()
            for row in rows
        }
        if "" in feature_types or len(feature_types) != 1:
            raise ValueError(f"node {node_id!r} has unstable feature_type")
        feature_type = next(iter(feature_types))
        feature_type_by_node[node_id] = feature_type

        registry_rows.append(
            {
                "node_id": node_id,
                "longitude": coordinates[node_id][0],
                "latitude": coordinates[node_id][1],
                "component_id": "algar_restoration",
                "feature_type": feature_type,
            }
        )

        fold = folds.mapping[node_id]
        for phase_index, row in enumerate(rows, start=1):
            context_id = f"phase{phase_index}"
            unit_id = f"{node_id}|{context_id}"
            start = str(row.get("start_date", "")).strip()
            end = str(row.get("end_date", "")).strip()
            eligible = _valid_interval(start, end)
            if phase_index == 1:
                if not eligible:
                    raise ValueError(
                        f"initialization deployment is ineligible for {node_id!r}"
                    )
                role = "initialization_only"
            elif eligible:
                role = "scored"
            else:
                role = "unsurveyed"
                unsurveyed_ids.append(unit_id)

            effort_rows.append(
                {
                    "unit_id": unit_id,
                    "node_id": node_id,
                    "context_id": context_id,
                    "fold": fold,
                    "eligible": "true" if eligible else "false",
                    "analysis_role": role,
                    "deployment_id": str(row.get("deployment_id", "")).strip(),
                    "start_date": start,
                    "end_date": end,
                    "feature_type": feature_type,
                    "phase": context_id,
                }
            )

    effort_contract = contract["effort_context"]
    initialization_count = sum(
        row["analysis_role"] == "initialization_only" for row in effort_rows
    )
    scored_count = sum(row["analysis_role"] == "scored" for row in effort_rows)
    unsurveyed_count = sum(row["analysis_role"] == "unsurveyed" for row in effort_rows)
    if initialization_count != int(effort_contract["expected_initialization_count"]):
        raise ValueError("initialization denominator drift")
    if scored_count != int(effort_contract["expected_scored_candidate_count"]):
        raise ValueError("scored candidate denominator drift")
    if unsurveyed_count != int(effort_contract["expected_unsurveyed_count"]):
        raise ValueError("unsurveyed denominator drift")
    if unsurveyed_ids != [effort_contract["expected_unsurveyed_unit_id"]]:
        raise ValueError(f"unexpected unsurveyed units: {unsurveyed_ids!r}")

    output_dir.mkdir(parents=True, exist_ok=True)
    registry_bytes = _csv_bytes(
        ["node_id", "longitude", "latitude", "component_id", "feature_type"],
        registry_rows,
    )
    effort_bytes = _csv_bytes(
        [
            "unit_id",
            "node_id",
            "context_id",
            "fold",
            "eligible",
            "analysis_role",
            "deployment_id",
            "start_date",
            "end_date",
            "feature_type",
            "phase",
        ],
        effort_rows,
    )
    registry_path = output_dir / "registry.csv"
    effort_path = output_dir / "effort.csv"
    registry_path.write_bytes(registry_bytes)
    effort_path.write_bytes(effort_bytes)

    world = contract["world_family"]
    observation = contract["observation_contract"]
    predictive = contract["predictive_state"]
    manifest = {
        "schema": "eog.pre_response_manifest.v1",
        "artifact_identity_policy": {
            "require_expected_identity": True,
        },
        "registry_table": {
            "path": "registry.csv",
            "artifact_id": "algar_v3_canonical_registry",
            "expected_identity": _derived_identity(registry_bytes),
            "schema": {
                "roles": [
                    {"role": "node_id", "aliases": ["node_id"]},
                    {"role": "x", "aliases": ["longitude"]},
                    {"role": "y", "aliases": ["latitude"]},
                    {"role": "component_id", "aliases": ["component_id"]},
                    {"role": "feature_type", "aliases": ["feature_type"]},
                ],
                "allow_unmapped_columns": False,
            },
            "coordinate_policy": {
                "tolerance": 0.0,
                "units": "decimal_degrees",
                "representative_policy": "median",
            },
        },
        "effort_table": {
            "path": "effort.csv",
            "artifact_id": "algar_v3_effort_context",
            "expected_identity": _derived_identity(effort_bytes),
            "schema": {
                "roles": [
                    {"role": "unit_id", "aliases": ["unit_id"]},
                    {"role": "node_id", "aliases": ["node_id"]},
                    {"role": "context_id", "aliases": ["context_id"]},
                    {"role": "fold", "aliases": ["fold"]},
                    {"role": "eligible", "aliases": ["eligible"]},
                    {"role": "analysis_role", "aliases": ["analysis_role"]},
                    {"role": "deployment_id", "aliases": ["deployment_id"]},
                    {"role": "start_date", "aliases": ["start_date"]},
                    {"role": "end_date", "aliases": ["end_date"]},
                    {"role": "feature_type", "aliases": ["feature_type"]},
                    {"role": "phase", "aliases": ["phase"]},
                ],
                "allow_unmapped_columns": False,
            },
            "eligible_true_tokens": ["true"],
            "eligible_false_tokens": ["false"],
            "evidence_fields": [
                "deployment_id",
                "start_date",
                "end_date",
                "feature_type",
                "phase",
            ],
            "evidence_types": {},
            "context_order": list(context_order),
            "policy": {
                "unit_definition": "locked camera placename x chronological deployment phase",
                "eligibility_rule": effort_contract["eligibility_rule"],
                "unsurveyed_rule": (
                    "node-context with missing/invalid deployment interval is outside "
                    "the scored endpoint and is never converted to a zero response"
                ),
                "evidence_source": "response_independent_effort",
            },
        },
        "world_family": {
            "artifact_id": "algar_v3_world_family",
            "horizon": int(world["horizon"]),
            "generator": {
                "type": "coordinate_threshold_worlds_v1",
                "metric": world["metric"],
                "construction_mode": "declared_thresholds",
                "thresholds": list(world["local_thresholds_km"]),
                "threshold_semantics_key": "geometry_threshold_km",
                "local_semantics": {
                    "source": "locked_algar_v3_camera_coordinates",
                    "positive_falsification": (
                        "unsupported eligible positive eliminates local world only "
                        "after current-context prediction is formed"
                    ),
                    "negative_falsification": "none",
                },
                "include_external_open": True,
                "external_open_world_id": world["external_open_world_id"],
                "external_open_semantics": {
                    "supports_every_frozen_node": True,
                    "positive_falsification": "never",
                    "negative_falsification": "none",
                },
            },
        },
        "structural_adequacy": dict(contract["structural_adequacy"]),
        "observation_contract": dict(observation),
        "predictive_state": {
            "repeated_measure_endpoint": predictive["repeated_measure_endpoint"],
            "train_generator_id": predictive["train_generator_id"],
            "serve_generator_id": predictive["serve_generator_id"],
            "refresh_policy": predictive["refresh_policy"],
            "source_policy": predictive["source_policy"],
            "source_label_invariant": predictive["source_label_invariant"],
            "baseline_contains_spatial_coordinates": (
                predictive["baseline_contains_spatial_coordinates"]
            ),
            "static_predictive_opt_in": predictive["static_predictive_opt_in"],
        },
        "baseline_fields": [
            {"name": "longitude", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "latitude", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "feature_type", "kind": "categorical", "missing_policy": "forbid"},
            {"name": "phase", "kind": "categorical", "missing_policy": "forbid"},
        ],
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = compile_pre_response_manifest(
        manifest,
        base_dir=output_dir,
    )

    expected = {
        "node_count": 38,
        "context_count": 3,
        "scored_candidate_count": 75,
        "initialization_count": 38,
        "unsurveyed_count": 1,
        "declared_world_count": 6,
        "structural_world_count": 5,
    }
    if result["counts"] != expected:
        raise ValueError(("manifest denominator drift", result["counts"], expected))
    if result["statuses"]["structural"] != "structural_ready":
        raise ValueError("manifest structural gate no longer passes")
    if (
        result["fingerprints"]["structural_gate"]
        != predecessor["structural_gate_fingerprint"]
    ):
        raise ValueError("manifest structural gate fingerprint differs from v3 PASS")
    if result["statuses"]["predictive"] != predictive["expected_status"]:
        raise ValueError("Layer-B predictive-state eligibility drift")
    if result["statuses"]["predictive_use_allowed"] is not True:
        raise ValueError("Layer-B representation should be eligible for predictive use")
    if result["statuses"]["predictive_outcome_access_allowed"] is not False:
        raise ValueError("predictive outcome access must remain closed before evaluation freeze")

    return {
        "schema": "eog.algar_restoration_v3_preresponse.result.v1",
        "status": "preresponse_manifest_ready",
        "response_bytes_opened": 0,
        "focal_species_selected": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "folds": {
            "fingerprint": folds.fingerprint,
            "fold_counts": list(folds.fold_counts),
            "node_to_fold": {node_id: fold for node_id, fold in folds.node_to_fold},
            "split_history": [
                {
                    "path": item.path,
                    "node_count": item.node_count,
                    "axis": item.axis,
                    "axis_span": item.axis_span,
                    "left_count": item.left_count,
                    "right_count": item.right_count,
                    "fingerprint": item.fingerprint,
                }
                for item in folds.split_history
            ],
        },
        "generated_artifacts": {
            "registry": _derived_identity(registry_bytes),
            "effort": _derived_identity(effort_bytes),
            "manifest_sha256": _sha256(manifest_path.read_bytes()),
        },
        "manifest_result": result,
        "counts_as_predictive_evidence": False,
        "changes_closed_eog_wf_synthesis": False,
    }
