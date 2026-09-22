"""Replay the authoritative response-blind Tampa Gate0 state through the v2 manifest.

The compressed fixture contains only fields recovered from the once-only Gate0 artifact
(run 34023723427, artifact 9986361240): frozen node coordinates, candidate-unit IDs,
contexts, baseline declarations, and pre-response fingerprints. It contains no focal
occurrence or eMoF response values.

This replay asks whether the same declarative manifest surface that accepts Louisiana
also classifies the frozen Tampa prediction-facing design as ineligible before outcome
access.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import zlib

import numpy as np

from benchmarks.tampa_predictive_state_v2_translation import (
    run_replay as run_predictive_gate_replay,
)
from eog.v2.pre_response_manifest import compile_pre_response_manifest_file


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "tampa_gate0_safe_subset.b85"
FIXTURE_RAW_SHA256 = "de4b7fddc7a97f35505687542c1e9a106dafa0c2f083d9b857fa81eea3f140af"
ARTIFACT_DIGEST = (
    "sha256:0860e262f5ce07baafdfd2ea2514bd94d1155b2a14a817a3e559acfd7f906240"
)
GATE0_FINGERPRINT = "3f1936f04416fa369ff315d214db7690b6d0882d31a43d64dc496323a84f1159"


def _load_fixture() -> dict[str, object]:
    compressed = base64.b85decode(FIXTURE.read_text(encoding="utf-8").strip())
    raw = zlib.decompress(compressed)
    if hashlib.sha256(raw).hexdigest() != FIXTURE_RAW_SHA256:
        raise AssertionError("Tampa safe fixture raw fingerprint drift")
    payload = json.loads(raw.decode("utf-8"))
    if payload["artifact_digest"] != ARTIFACT_DIGEST:
        raise AssertionError("Tampa Gate0 artifact digest drift")
    if payload["gate0_fingerprint"] != GATE0_FINGERPRINT:
        raise AssertionError("Tampa Gate0 result fingerprint drift")
    return payload


def _csv_text(header, rows) -> str:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue()


def _haversine_matrix(node_rows) -> np.ndarray:
    radius_km = 6371.0088
    lat = np.radians(np.asarray([float(row["latitude"]) for row in node_rows]))
    lon = np.radians(np.asarray([float(row["longitude"]) for row in node_rows]))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + (
        np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    return 2 * radius_km * np.arcsin(np.sqrt(a))


def _build_world_document(payload):
    nodes = payload["node_coordinates"]
    node_ids = [row["node_id"] for row in nodes]
    distances = _haversine_matrix(nodes)
    thresholds = tuple(payload["world_family"]["local_thresholds_km"])
    world_ids = ("haversine_q25", "haversine_q50", "haversine_q75", "haversine_q90")
    worlds = {}
    semantics = {}
    for world_id, threshold in zip(world_ids, thresholds, strict=True):
        adjacency = distances <= float(threshold) + 1e-12
        np.fill_diagonal(adjacency, False)
        worlds[world_id] = adjacency.astype(int).tolist()
        semantics[world_id] = {
            "kind": "local",
            "geometry_threshold_km": float(threshold),
            "operator_rule": (
                "undirected threshold edge becomes two directed unit-support edges"
            ),
        }

    external = np.ones((len(node_ids), len(node_ids)), dtype=int)
    np.fill_diagonal(external, 0)
    worlds["external_open"] = external.tolist()
    semantics["external_open"] = {
        "kind": "external_open",
        "supports_every_frozen_site": True,
    }
    return {
        "schema": "eog.tampa_manifest_worlds.v1",
        "node_ids": node_ids,
        "worlds": worlds,
        "world_semantics": semantics,
        "structural_world_ids": list(world_ids),
    }


def _write_manifest(tmp_path: Path, payload) -> Path:
    node_rows = payload["node_coordinates"]
    registry_rows = [
        (
            row["node_id"],
            repr(float(row["longitude"])),
            repr(float(row["latitude"])),
            row["water_body"],
        )
        for row in node_rows
    ]
    (tmp_path / "registry.csv").write_text(
        _csv_text(("node_id", "x", "y", "water_body"), registry_rows),
        encoding="utf-8",
    )

    effort_rows = [
        (
            row["unit_id"],
            row["node_id"],
            row["context_id"],
            str(row["fold"]),
            "true",
            "scored",
            payload["gate0_fingerprint"],
            payload["candidate_registry_fingerprint"],
            payload["child_linkage_fingerprint"],
            "eligible parent Transect with at least three linked child Point events",
        )
        for row in payload["candidate_units"]
    ]
    (tmp_path / "effort.csv").write_text(
        _csv_text(
            (
                "unit_id",
                "node_id",
                "context_id",
                "fold",
                "eligible",
                "analysis_role",
                "gate0_fingerprint",
                "candidate_registry_fingerprint",
                "child_linkage_fingerprint",
                "survey_design",
            ),
            effort_rows,
        ),
        encoding="utf-8",
    )

    world_document = _build_world_document(payload)
    (tmp_path / "worlds.json").write_text(
        json.dumps(world_document, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    observation = payload["observation_semantics"]
    manifest = {
        "schema": "eog.pre_response_manifest.v1",
        "registry_table": {
            "path": "registry.csv",
            "artifact_id": "tampa_gate0_node_registry",
            "schema": {
                "roles": [
                    {"role": "node_id", "aliases": ["node_id"]},
                    {"role": "x", "aliases": ["x"]},
                    {"role": "y", "aliases": ["y"]},
                    {"role": "water_body", "aliases": ["water_body"]},
                ],
                "allow_unmapped_columns": False,
            },
            "coordinate_policy": {
                "tolerance": 0.0,
                "units": "decimal_degrees",
                "representative_policy": "first",
            },
            "default_component_id": "tampa_bay",
        },
        "effort_table": {
            "path": "effort.csv",
            "artifact_id": "tampa_gate0_candidate_registry",
            "schema": {
                "roles": [
                    {"role": "unit_id", "aliases": ["unit_id"]},
                    {"role": "node_id", "aliases": ["node_id"]},
                    {"role": "context_id", "aliases": ["context_id"]},
                    {"role": "fold", "aliases": ["fold"]},
                    {"role": "eligible", "aliases": ["eligible"]},
                    {"role": "analysis_role", "aliases": ["analysis_role"]},
                    {"role": "gate0_fingerprint", "aliases": ["gate0_fingerprint"]},
                    {
                        "role": "candidate_registry_fingerprint",
                        "aliases": ["candidate_registry_fingerprint"],
                    },
                    {
                        "role": "child_linkage_fingerprint",
                        "aliases": ["child_linkage_fingerprint"],
                    },
                    {"role": "survey_design", "aliases": ["survey_design"]},
                ],
                "allow_unmapped_columns": False,
            },
            "eligible_true_tokens": ["true"],
            "eligible_false_tokens": ["false"],
            "evidence_fields": [
                "gate0_fingerprint",
                "candidate_registry_fingerprint",
                "child_linkage_fingerprint",
                "survey_design",
            ],
            "context_order": list(payload["context_ids"]),
            "policy": {
                "unit_definition": "eligible parent Transect visit",
                "eligibility_rule": observation["effort_eligible_rule"],
                "unsurveyed_rule": observation["unsurveyed_rule"],
                "evidence_source": "response_independent_registry",
            },
        },
        "world_family": {
            "path": "worlds.json",
            "artifact_id": "tampa_declared_world_family",
            "horizon": 70,
        },
        "structural_adequacy": {
            "min_largest_weak_component_fraction": 1.0,
            "max_isolated_node_fraction": 0.0,
            "require_at_least_one_world_pass": True,
        },
        "observation_contract": {
            "mode": "complete_source_zero",
            "endpoint_name": "eligible parent Transect visit x focal detection",
            "positive_semantics": observation["positive_rule"],
            "negative_semantics": observation["negative_rule"],
            "unavailable_semantics": observation["unsurveyed_rule"],
            "zero_interpretation": observation["zero_interpretation"],
        },
        "predictive_state": {
            "repeated_measure_endpoint": True,
            "train_generator_id": "leave_entire_stable_node_out_static_reconstruction",
            "serve_generator_id": "common_fold_static_reconstruction",
            "refresh_policy": "static_reused",
            "source_policy": "lexicographic_single_source",
            "source_label_invariant": False,
            "baseline_contains_spatial_coordinates": True,
        },
        "predictive_evaluation": {
            "status": "portability_replay_only",
            "historical_outcome_not_consulted": True,
        },
        "baseline_fields": list(payload["baseline_fields"]),
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _fold_counts(candidate_units):
    node_fold = {}
    candidate_counts = {}
    for row in candidate_units:
        node = row["node_id"]
        fold = int(row["fold"])
        previous = node_fold.setdefault(node, fold)
        if previous != fold:
            raise AssertionError("Tampa candidate node changes fold across visits")
        candidate_counts[fold] = candidate_counts.get(fold, 0) + 1
    node_counts = {}
    for fold in node_fold.values():
        node_counts[fold] = node_counts.get(fold, 0) + 1
    return node_counts, candidate_counts


def run_replay() -> dict[str, object]:
    payload = _load_fixture()
    historical_gate = run_predictive_gate_replay()

    node_counts, candidate_counts = _fold_counts(payload["candidate_units"])
    expected_node_counts = {int(k): int(v) for k, v in payload["fold_node_counts"].items()}
    expected_candidate_counts = {
        int(k): int(v) for k, v in payload["fold_candidate_counts"].items()
    }
    if node_counts != expected_node_counts:
        raise AssertionError((node_counts, expected_node_counts))
    if candidate_counts != expected_candidate_counts:
        raise AssertionError((candidate_counts, expected_candidate_counts))

    with TemporaryDirectory(prefix="eog-tampa-manifest-") as directory:
        manifest_path = _write_manifest(Path(directory), payload)
        manifest = compile_pre_response_manifest_file(manifest_path)

    gate = historical_gate["v2_predictive_state_gate"]
    if manifest["fingerprints"]["predictive_state"] != gate["fingerprint"]:
        raise AssertionError(
            (
                manifest["fingerprints"]["predictive_state"],
                gate["fingerprint"],
            )
        )

    counts = manifest["counts"]
    expected_counts = {
        "node_count": 71,
        "context_count": 29,
        "scored_candidate_count": 1497,
        "initialization_count": 0,
        "unsurveyed_count": 0,
        "declared_world_count": 5,
        "structural_world_count": 4,
    }
    if counts != expected_counts:
        raise AssertionError((counts, expected_counts))

    statuses = manifest["statuses"]
    if statuses["structural"] != "structural_ready":
        raise AssertionError(statuses)
    if statuses["structural_response_access_allowed"] is not True:
        raise AssertionError(statuses)
    if statuses["predictive"] != "ineligible_generation_shift":
        raise AssertionError(statuses)
    if statuses["predictive_use_allowed"] is not False:
        raise AssertionError(statuses)
    if statuses["predictive_outcome_access_allowed"] is not False:
        raise AssertionError(statuses)

    return {
        "schema": "eog.tampa_manifest_v2_portability_replay.v1",
        "uses_biological_response": False,
        "uses_observed_tampa_predictive_score": False,
        "reruns_frozen_endpoint": False,
        "counts_as_predictive_evidence": False,
        "authoritative_gate0": {
            "artifact_digest": payload["artifact_digest"],
            "gate0_fingerprint": payload["gate0_fingerprint"],
            "fixture_raw_sha256": FIXTURE_RAW_SHA256,
        },
        "counts": counts,
        "fold_node_counts": node_counts,
        "fold_candidate_counts": candidate_counts,
        "statuses": statuses,
        "predictive_state_fingerprint_matches_existing_v2_replay": True,
        "manifest_result_fingerprint": manifest["result_fingerprint"],
        "interpretation": (
            "The same declarative manifest path used for the favorable Louisiana "
            "translation accepts Tampa's response-independent registry and local world "
            "geometry as structurally ready, but reproduces the prospective v2 "
            "ineligible_generation_shift decision for the frozen Tampa Layer-B design "
            "without opening focal occurrence outcomes or consulting the adverse score."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
