"""Replay the real response-blind Louisiana v2 translation through the manifest compiler.

This benchmark uses only the same Gate0-recovered Sites/Samples rows and frozen
pre-response declarations already embedded in louisiana_real_pre_response_v2_translation.
It does not open KIRA.csv or any biological response.

The purpose is portability validation: the declarative manifest surface should reproduce
the same generic contract-layer fingerprints as the bespoke response-free translation
where the two paths share an estimand.
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from benchmarks.louisiana_real_pre_response_v2_translation import (
    EXPECTED_DISTINCT_THRESHOLDS_KM,
    GATE0_FINGERPRINT,
    HISTORICAL_SITE_REGISTRY_FINGERPRINT,
    SAMPLE_ROWS,
    SITE_ROWS,
    _deduplicated_geometry,
    _haversine_distance_matrix,
    run_replay as run_bespoke_replay,
)
from eog.v2.pre_response_manifest import compile_pre_response_manifest_file
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)


def _csv_text(header, rows):
    lines = [",".join(header)]
    lines.extend(",".join(str(value) for value in row) for row in rows)
    return "\n".join(lines) + "\n"


def _build_worlds():
    site_records = tuple(
        {
            "node_id": row[0],
            "latitude": row[1],
            "longitude": row[2],
            "marsh": row[3],
            "habitat": row[4],
        }
        for row in SITE_ROWS
    )
    node_ids = tuple(row["node_id"] for row in site_records)
    distances = _haversine_distance_matrix(site_records)
    ladder = build_structural_scale_ladder(
        node_ids,
        distances,
        StructuralScaleLadderDeclaration(
            axis_id="southwest_louisiana_marsh_site_haversine_km",
            target_largest_component_fractions=(0.25, 0.50, 0.75, 0.90),
        ),
    )
    geometry = _deduplicated_geometry(ladder, distances)
    thresholds = tuple(item[0] for item in geometry)
    if len(thresholds) != 3 or not np.allclose(
        thresholds,
        EXPECTED_DISTINCT_THRESHOLDS_KM,
        rtol=0.0,
        atol=1e-9,
    ):
        raise AssertionError("Louisiana geometry threshold drift")

    worlds = {}
    semantics = {}
    structural_ids = []
    for index, (threshold, adjacency) in enumerate(geometry, start=1):
        for source_mode in (
            "immediate_previous_observed",
            "cumulative_observed_history",
        ):
            world_id = f"local_geo{index}::{source_mode}"
            worlds[world_id] = adjacency.astype(int).tolist()
            semantics[world_id] = {
                "kind": "local",
                "geometry_threshold_km": float(threshold),
                "source_mode": source_mode,
                "positive_falsification": "unsupported_positive_eliminates_world",
                "negative_falsification": "none",
            }
        structural_ids.append(
            f"local_geo{index}::immediate_previous_observed"
        )
    external = np.ones((len(node_ids), len(node_ids)), dtype=int)
    np.fill_diagonal(external, 0)
    worlds["external_open"] = external.tolist()
    semantics["external_open"] = {
        "kind": "external_open",
        "supports_every_frozen_site": True,
        "positive_falsification": "never",
        "negative_falsification": "none",
    }
    return node_ids, worlds, semantics, structural_ids


def _effort_rows(node_ids):
    sample_by_period = {int(row[0]): row for row in SAMPLE_ROWS}
    chronological = tuple(
        sorted(
            sample_by_period,
            key=lambda period: (
                datetime.strptime(sample_by_period[period][1], "%m/%d/%Y"),
                period,
            ),
        )
    )
    expected = (1,2,3,4,5,6,7,8,9,10,11,12,17,13,18,14,19,15,20,16)
    if chronological != expected:
        raise AssertionError("Louisiana chronological occasion order drift")

    header = (
        "unit_id",
        "node_id",
        "context_id",
        "fold",
        "eligible",
        "analysis_role",
        "gate0_fingerprint",
        "site_registry_fingerprint",
        "sample_period",
        "date",
        "survey_design",
    )
    rows = []
    for site in node_ids:
        for period in chronological:
            context = f"period_{period}"
            role = "initialization_only" if period == 1 else "scored"
            rows.append(
                (
                    f"{site}|{context}",
                    site,
                    context,
                    str(period),
                    "true",
                    role,
                    GATE0_FINGERPRINT,
                    HISTORICAL_SITE_REGISTRY_FINGERPRINT,
                    str(period),
                    sample_by_period[period][1],
                    "official 33-site x 20-occasion matrix",
                )
            )
    return header, tuple(rows), tuple(f"period_{period}" for period in chronological)


def _manifest(tmp_path: Path) -> Path:
    node_ids, worlds, semantics, structural_ids = _build_worlds()
    effort_header, effort_rows, context_order = _effort_rows(node_ids)

    (tmp_path / "sites.csv").write_text(
        _csv_text(
            ("Site", "Latitude", "Longitude", "Marsh", "Habitat"),
            SITE_ROWS,
        ),
        encoding="utf-8",
    )
    (tmp_path / "effort.csv").write_text(
        _csv_text(effort_header, effort_rows),
        encoding="utf-8",
    )
    (tmp_path / "worlds.json").write_text(
        json.dumps(
            {
                "schema": "eog.louisiana_manifest_worlds.v1",
                "node_ids": list(node_ids),
                "worlds": worlds,
                "world_semantics": semantics,
                "structural_world_ids": structural_ids,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    manifest = {
        "schema": "eog.pre_response_manifest.v1",
        "registry_table": {
            "path": "sites.csv",
            "artifact_id": "gate0_log_sites_rows",
            "schema": {
                "roles": [
                    {"role": "node_id", "aliases": ["Site"]},
                    {"role": "y", "aliases": ["Latitude"]},
                    {"role": "x", "aliases": ["Longitude"]},
                    {"role": "marsh", "aliases": ["Marsh"]},
                    {"role": "habitat", "aliases": ["Habitat"]},
                ],
                "allow_unmapped_columns": False,
            },
            "coordinate_policy": {
                "tolerance": 0.0,
                "units": "decimal_degrees",
                "representative_policy": "first",
            },
            "default_component_id": "southwest_louisiana_marsh",
        },
        "effort_table": {
            "path": "effort.csv",
            "artifact_id": "derived_response_independent_effort",
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
                        "role": "site_registry_fingerprint",
                        "aliases": ["site_registry_fingerprint"],
                    },
                    {"role": "sample_period", "aliases": ["sample_period"]},
                    {"role": "date", "aliases": ["date"]},
                    {"role": "survey_design", "aliases": ["survey_design"]},
                ],
                "allow_unmapped_columns": False,
            },
            "eligible_true_tokens": ["true"],
            "eligible_false_tokens": ["false"],
            "evidence_fields": [
                "gate0_fingerprint",
                "site_registry_fingerprint",
                "sample_period",
                "date",
                "survey_design",
            ],
            "evidence_types": {
                "sample_period": "int",
            },
            "context_order": list(context_order),
            "policy": {
                "unit_definition": "site x official sampling occasion",
                "eligibility_rule": (
                    "all 33 official Sites.csv nodes are sampled on each of the 20 "
                    "official Samples.csv occasions before focal response tokens are opened"
                ),
                "unsurveyed_rule": (
                    "no pre-response unsurveyed units in the official matrix; response-level "
                    "unavailable tokens are handled separately and never converted to zero"
                ),
                "evidence_source": "response_independent_design",
            },
        },
        "world_family": {
            "path": "worlds.json",
            "artifact_id": "declared_world_family",
            "horizon": 1,
        },
        "structural_adequacy": {
            "min_largest_weak_component_fraction": 0.90,
            "max_isolated_node_fraction": 0.05,
            "require_at_least_one_world_pass": True,
        },
        "observation_contract": {
            "mode": "explicit_binary_tokens",
            "endpoint_name": "site-occasion observed King Rail detection",
            "positive_semantics": "KIRA.csv cell token 1 at frozen site and occasion",
            "negative_semantics": (
                "KIRA.csv cell token 0; observed non-detection under released acoustic "
                "sampling design, never biological absence"
            ),
            "unavailable_semantics": (
                "case-sensitive unavailable tokens are excluded from model/count risk sets"
            ),
            "zero_interpretation": (
                "recorded acoustic non-detection at a surveyed site-occasion"
            ),
        },
        "predictive_state": {
            "repeated_measure_endpoint": True,
            "train_generator_id": "sequential_preoutcome",
            "serve_generator_id": "sequential_preoutcome",
            "refresh_policy": "sequential_context",
            "source_policy": (
                "immediate_previous_or_cumulative_observed_positive_source_sets"
            ),
            "source_label_invariant": True,
            "baseline_contains_spatial_coordinates": True,
        },
        "predictive_evaluation": {
            "status": "manifest_portability_replay_only",
            "does_not_replace_historical_freeze": True,
        },
        "baseline_fields": [
            {"name": "longitude", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "latitude", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "precipitation", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "min_air_temp", "kind": "numeric", "missing_policy": "forbid"},
            {"name": "marsh", "kind": "categorical", "missing_policy": "forbid"},
            {"name": "habitat", "kind": "categorical", "missing_policy": "forbid"},
        ],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def run_replay() -> dict[str, object]:
    bespoke = run_bespoke_replay()
    with TemporaryDirectory(prefix="eog-louisiana-manifest-") as directory:
        manifest_path = _manifest(Path(directory))
        manifest = compile_pre_response_manifest_file(manifest_path)

    shared = {
        "coordinate_registry": (
            manifest["fingerprints"]["coordinate_registry"],
            bespoke["registry"]["coordinate_fingerprint"],
        ),
        "effort_context": (
            manifest["fingerprints"]["effort_context"],
            bespoke["effort"]["fingerprint"],
        ),
        "world_family": (
            manifest["fingerprints"]["world_family"],
            bespoke["worlds"]["world_family_fingerprint_v2"],
        ),
        "observation_contract": (
            manifest["fingerprints"]["observation_contract"],
            bespoke["observation"]["fingerprint"],
        ),
        "predictive_state": (
            manifest["fingerprints"]["predictive_state"],
            bespoke["predictive_state"]["fingerprint"],
        ),
    }
    matches = {name: left == right for name, (left, right) in shared.items()}
    if not all(matches.values()):
        raise AssertionError({"shared_layer_matches": matches, "shared": shared})

    counts = manifest["counts"]
    if (
        counts["node_count"],
        counts["context_count"],
        counts["initialization_count"],
        counts["scored_candidate_count"],
        counts["unsurveyed_count"],
        counts["declared_world_count"],
        counts["structural_world_count"],
    ) != (33, 20, 33, 627, 0, 7, 3):
        raise AssertionError(("Louisiana manifest denominator drift", counts))

    if manifest["statuses"]["predictive"] != "predictive_complement_candidate":
        raise AssertionError(manifest["statuses"]["predictive"])
    if manifest["statuses"]["structural"] != "structural_ready":
        raise AssertionError(manifest["statuses"]["structural"])

    return {
        "schema": "eog.louisiana_manifest_v2_portability_replay.v1",
        "uses_biological_response": False,
        "reruns_frozen_endpoint": False,
        "counts_as_predictive_evidence": False,
        "shared_layer_fingerprint_matches": matches,
        "counts": counts,
        "statuses": manifest["statuses"],
        "manifest_result_fingerprint": manifest["result_fingerprint"],
        "interpretation": (
            "The declarative manifest compiler reproduces the same response-independent "
            "Louisiana coordinate, effort, world-family, observation and predictive-state "
            "contract fingerprints as the bespoke v2 translation. Source-provenance, "
            "split and final certificate identities are intentionally not claimed equal "
            "because the manifest replay introduces a derived effort artifact and a new "
            "portability-only predictive-evaluation declaration."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
