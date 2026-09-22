"""Real response-blind Louisiana translation through the generic EOG-WF v2 contracts.

The site and sampling rows below are copied from the authoritative Gate0 workflow log:
run 32809608720 / job 97686313502. That run opened only response-independent
Sites.csv and Samples.csv and recorded zero biological-response header/payload/rows.

This replay does not open KIRA.csv, does not rerun the frozen endpoint, and cannot
change the closed favorable Louisiana result.
"""

from __future__ import annotations

from datetime import datetime
import json
import math

import numpy as np

from eog.v2.coordinate_registry import (
    CoordinateObservation,
    CoordinateRegistryPolicy,
    audit_coordinate_registry,
)
from eog.v2.effort_context import (
    EffortContextRow,
    EffortEligibilityPolicy,
    evidence_fingerprint,
    freeze_effort_context_ledger,
)
from eog.v2.observation_process import BinaryObservationContract
from eog.v2.pre_response_certificate import (
    SourceArtifactIdentity,
    fingerprint_world_family,
    freeze_adapter_source_provenance,
    freeze_pre_response_certificate,
)
from eog.v2.predictive_state_gate import (
    PredictiveStateDesign,
    evaluate_predictive_state_design,
)
from eog.v2.problem_contract import (
    BaselineFieldSpec,
    ObservationSemantics,
    freeze_pre_response_problem,
)
from eog.v2.schema_adapter import SchemaAliasContract, SchemaRole
from eog.v2.tabular_adapter import parse_response_blind_csv
from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)

GATE0_RUN_ID = 32809608720
GATE0_JOB_ID = 97686313502
GATE0_FINGERPRINT = "5ce556acd5b119a7b451a3b8cca0fdb254ded2461014c1e2e8388abdaf6802cf"
HISTORICAL_SITE_REGISTRY_FINGERPRINT = (
    "c6a4c8dcf458dca881d6e8c67c51b6910fd055d089df563210ee575db8f3b131"
)
HISTORICAL_DISTANCE_MATRIX_FINGERPRINT = (
    "a5b1e432f024812592037da94b73103b046ddf97d7817a58f0e158cd6aa198ac"
)
HISTORICAL_STRUCTURAL_LADDER_FINGERPRINT = (
    "4c8e4ce50dd05788bc2311318a6473d736351f11217545ccd8e3b870b29dd2de"
)
HISTORICAL_SPLIT_FINGERPRINT = (
    "c2a2ba4767bac907f2d007de4164967acae7c6ee055cf96f3dd1b0cc96b18084"
)
HISTORICAL_PREDICTIVE_EVALUATION_FINGERPRINT = (
    "d97a7062f71d1c2f6aab73bbef77d13737cb00a5c93f524d5c07e85657b26d8e"
)
EXPECTED_DISTINCT_THRESHOLDS_KM = (
    2.728021756372908,
    2.976793133666009,
    17.008648432743254,
)

SITE_ROWS = (
    ("J02","29.65007","-92.73457","Brackish","Brackish-Salt Marsh"),
    ("J03","29.64617","-92.72298","Brackish","Brackish-Salt Marsh"),
    ("J07","29.91964","-92.51378","Fresh","Fresh-Intermediate Marsh"),
    ("J09","29.6938","-92.6588","Intermediate","Fresh-Intermediate Marsh"),
    ("J10","29.70023","-92.76107","Brackish","Brackish-Salt Marsh"),
    ("J12","29.79888","-92.45082","Fresh","Fresh-Intermediate Marsh"),
    ("J14","29.66672","-92.74795","Brackish","Brackish-Salt Marsh"),
    ("J15","29.5934","-92.64217","Salt","Brackish-Salt Marsh"),
    ("J16","29.70473","-92.71307","Intermediate","Fresh-Intermediate Marsh"),
    ("J17","29.66868","-92.6793","Intermediate","Fresh-Intermediate Marsh"),
    ("J18","29.63984","-92.60405","Brackish","Brackish-Salt Marsh"),
    ("J20","29.71493","-92.76667","Brackish","Brackish-Salt Marsh"),
    ("J21","29.6922","-92.6424","Intermediate","Fresh-Intermediate Marsh"),
    ("J22","29.60552","-92.68623","Salt","Brackish-Salt Marsh"),
    ("J23","29.83821","-92.58988","Fresh","Fresh-Intermediate Marsh"),
    ("J24","29.68688","-92.67808","Intermediate","Fresh-Intermediate Marsh"),
    ("J26","29.67187","-92.69175","Intermediate","Fresh-Intermediate Marsh"),
    ("J27","29.68788","-92.7635","Brackish","Brackish-Salt Marsh"),
    ("J28","29.85966","-92.60618","Fresh","Fresh-Intermediate Marsh"),
    ("J29","29.58583","-92.61533","Brackish","Brackish-Salt Marsh"),
    ("J30","29.69335","-92.81015","Brackish","Brackish-Salt Marsh"),
    ("J31","29.82403","-92.47778","Fresh","Fresh-Intermediate Marsh"),
    ("J32","29.66345","-92.71827","Brackish","Brackish-Salt Marsh"),
    ("J33","29.67979","-92.82159","Brackish","Brackish-Salt Marsh"),
    ("J34","29.68968","-92.63322","Intermediate","Fresh-Intermediate Marsh"),
    ("J35","29.69703","-92.67577","Intermediate","Fresh-Intermediate Marsh"),
    ("J36","29.6831","-92.79382","Brackish","Brackish-Salt Marsh"),
    ("J38","29.84771","-92.55371","Fresh","Fresh-Intermediate Marsh"),
    ("J39","29.84842","-92.58451","Fresh","Fresh-Intermediate Marsh"),
    ("J41","29.85374","-92.56396","Fresh","Fresh-Intermediate Marsh"),
    ("J42","29.87943","-92.59423","Fresh","Fresh-Intermediate Marsh"),
    ("J45","29.86386","-92.54842","Fresh","Fresh-Intermediate Marsh"),
    ("J48","29.85701","-92.53729","Fresh","Fresh-Intermediate Marsh"),
)

SAMPLE_ROWS = (
    ("1","2/13/2012","11.2","4.4"),
    ("2","2/20/2012","0","8.4"),
    ("3","2/26/2012","0","8.3"),
    ("4","3/5/2012","0","7.8"),
    ("5","3/13/2012","27.7","18.3"),
    ("6","3/23/2012","1.7","12.5"),
    ("7","3/30/2012","1.9","17.2"),
    ("8","4/2/2012","0","20.6"),
    ("9","4/9/2012","0","17.8"),
    ("10","4/17/2012","16.9","20.9"),
    ("11","4/23/2012","0","11.7"),
    ("12","4/30/2012","0","20.6"),
    ("13","5/7/2012","0","22.3"),
    ("14","5/14/2012","1","17.8"),
    ("15","5/21/2012","0","21.4"),
    ("16","5/28/2012","0","22"),
    ("17","5/4/2012","0","24.2"),
    ("18","5/11/2012","0.9","22.8"),
    ("19","5/18/2012","13.7","21.1"),
    ("20","5/25/2012","0","24.2"),
)


def _csv_bytes(header, rows):
    lines = [",".join(header)]
    lines.extend(",".join(row) for row in rows)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _haversine_distance_matrix(site_records):
    radius_km = 6371.0088
    lat = np.radians(np.asarray([float(row["latitude"]) for row in site_records]))
    lon = np.radians(np.asarray([float(row["longitude"]) for row in site_records]))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + (
        np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    return 2 * radius_km * np.arcsin(np.sqrt(a))


def _deduplicated_geometry(ladder, distances):
    adjacencies = structural_scale_adjacencies(ladder, distances)
    by_threshold = {}
    for level in ladder.levels:
        by_threshold.setdefault(level.distance_threshold, adjacencies[level.level_id])
    return tuple((threshold, by_threshold[threshold]) for threshold in sorted(by_threshold))


def run_replay() -> dict[str, object]:
    sites_schema = SchemaAliasContract(
        roles=(
            SchemaRole("node_id", ("Site",)),
            SchemaRole("latitude", ("Latitude",)),
            SchemaRole("longitude", ("Longitude",)),
            SchemaRole("marsh", ("Marsh",)),
            SchemaRole("habitat", ("Habitat",)),
        ),
        allow_unmapped_columns=False,
    )
    samples_schema = SchemaAliasContract(
        roles=(
            SchemaRole("sample_period", ("Sample Period",)),
            SchemaRole("date", ("Date",)),
            SchemaRole("precipitation", ("Precipitation",)),
            SchemaRole("min_air_temp", ("MinAirTemp",)),
        ),
        allow_unmapped_columns=False,
    )
    sites_bytes = _csv_bytes(
        ("Site","Latitude","Longitude","Marsh","Habitat"), SITE_ROWS
    )
    samples_bytes = _csv_bytes(
        ("Sample Period","Date","Precipitation","MinAirTemp"), SAMPLE_ROWS
    )
    sites = parse_response_blind_csv(sites_bytes, schema_contract=sites_schema)
    samples = parse_response_blind_csv(samples_bytes, schema_contract=samples_schema)
    site_records = sites.records()
    sample_records = samples.records()

    if len(site_records) != 33 or len(sample_records) != 20:
        raise AssertionError("authoritative Gate0 row recovery drift")

    coordinate_audit = audit_coordinate_registry(
        tuple(
            CoordinateObservation(
                row["node_id"], float(row["longitude"]), float(row["latitude"])
            )
            for row in site_records
        ),
        CoordinateRegistryPolicy(
            tolerance=0.0,
            units="decimal_degrees",
            representative_policy="first",
        ),
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
    if ladder.distance_matrix_fingerprint != HISTORICAL_DISTANCE_MATRIX_FINGERPRINT:
        raise AssertionError(
            (
                ladder.distance_matrix_fingerprint,
                HISTORICAL_DISTANCE_MATRIX_FINGERPRINT,
            )
        )
    if ladder.fingerprint != HISTORICAL_STRUCTURAL_LADDER_FINGERPRINT:
        raise AssertionError(
            (ladder.fingerprint, HISTORICAL_STRUCTURAL_LADDER_FINGERPRINT)
        )

    geometry = _deduplicated_geometry(ladder, distances)
    observed_thresholds = tuple(value[0] for value in geometry)
    if len(observed_thresholds) != 3 or not np.allclose(
        observed_thresholds,
        EXPECTED_DISTINCT_THRESHOLDS_KM,
        rtol=0.0,
        atol=1e-9,
    ):
        raise AssertionError((observed_thresholds, EXPECTED_DISTINCT_THRESHOLDS_KM))

    world_adjacencies = {}
    world_semantics = {}
    structural_world_ids = []
    for index, (threshold, adjacency) in enumerate(geometry, start=1):
        for source_mode in (
            "immediate_previous_observed",
            "cumulative_observed_history",
        ):
            world_id = f"local_geo{index}::{source_mode}"
            world_adjacencies[world_id] = adjacency
            world_semantics[world_id] = {
                "kind": "local",
                "geometry_threshold_km": float(threshold),
                "source_mode": source_mode,
                "positive_falsification": "unsupported_positive_eliminates_world",
                "negative_falsification": "none",
            }
        structural_world_ids.append(
            f"local_geo{index}::immediate_previous_observed"
        )
    external = np.ones((len(node_ids), len(node_ids)), dtype=bool)
    np.fill_diagonal(external, False)
    world_adjacencies["external_open"] = external
    world_semantics["external_open"] = {
        "kind": "external_open",
        "supports_every_frozen_site": True,
        "positive_falsification": "never",
        "negative_falsification": "none",
    }
    if len(world_adjacencies) != 7:
        raise AssertionError("Louisiana world count drift")

    structural_adjacencies = {
        world_id: world_adjacencies[world_id] for world_id in structural_world_ids
    }
    structural_audit = audit_world_universe_structure(
        node_ids, structural_adjacencies, horizon=1
    )
    structural_gate = apply_structural_adequacy_gate(
        structural_audit,
        StructuralAdequacyDeclaration(
            min_largest_weak_component_fraction=0.90,
            max_isolated_node_fraction=0.05,
            require_at_least_one_world_pass=True,
        ),
    )
    if not structural_gate.passed:
        raise AssertionError("frozen Louisiana geometry should pass structural adequacy")

    sample_by_period = {int(row["sample_period"]): row for row in sample_records}
    chronological_periods = tuple(
        sorted(
            sample_by_period,
            key=lambda period: (
                datetime.strptime(sample_by_period[period]["date"], "%m/%d/%Y"),
                period,
            ),
        )
    )
    expected_order = (1,2,3,4,5,6,7,8,9,10,11,12,17,13,18,14,19,15,20,16)
    if chronological_periods != expected_order:
        raise AssertionError((chronological_periods, expected_order))
    context_ids = tuple(f"period_{period}" for period in chronological_periods)

    effort_rows = []
    for site in node_ids:
        for period in chronological_periods:
            context_id = f"period_{period}"
            role = "initialization_only" if period == 1 else "scored"
            payload = {
                "gate0_fingerprint": GATE0_FINGERPRINT,
                "site_registry_fingerprint": HISTORICAL_SITE_REGISTRY_FINGERPRINT,
                "sample_period": period,
                "date": sample_by_period[period]["date"],
                "survey_design": "official 33-site x 20-occasion matrix",
            }
            effort_rows.append(
                EffortContextRow(
                    unit_id=f"{site}|{context_id}",
                    node_id=site,
                    context_id=context_id,
                    fold=period,
                    eligible=True,
                    analysis_role=role,
                    evidence_summary=json.dumps(payload, sort_keys=True),
                    evidence_fingerprint=evidence_fingerprint(payload),
                )
            )
    effort_ledger = freeze_effort_context_ledger(
        node_ids=node_ids,
        context_ids=context_ids,
        rows=tuple(effort_rows),
        policy=EffortEligibilityPolicy(
            unit_definition="site x official sampling occasion",
            eligibility_rule=(
                "all 33 official Sites.csv nodes are sampled on each of the 20 "
                "official Samples.csv occasions before focal response tokens are opened"
            ),
            unsurveyed_rule=(
                "no pre-response unsurveyed units in the official matrix; response-level "
                "unavailable tokens are handled separately and never converted to zero"
            ),
            evidence_source="response_independent_design",
        ),
    )
    if (
        effort_ledger.surveyed_count != 660
        or effort_ledger.initialization_count != 33
        or effort_ledger.candidate_count != 627
        or effort_ledger.unsurveyed_count != 0
    ):
        raise AssertionError("Louisiana effort projection drift")

    observation_contract = BinaryObservationContract(
        mode="explicit_binary_tokens",
        endpoint_name="site-occasion observed King Rail detection",
        positive_semantics="KIRA.csv cell token 1 at frozen site and occasion",
        negative_semantics=(
            "KIRA.csv cell token 0; observed non-detection under released acoustic "
            "sampling design, never biological absence"
        ),
        unavailable_semantics=(
            "case-sensitive unavailable tokens are excluded from model/count risk sets"
        ),
        zero_interpretation=(
            "recorded acoustic non-detection at a surveyed site-occasion"
        ),
    )

    source_provenance = freeze_adapter_source_provenance(
        artifacts=(
            SourceArtifactIdentity.from_bytes("gate0_log_sites_rows", sites_bytes),
            SourceArtifactIdentity.from_bytes("gate0_log_samples_rows", samples_bytes),
        ),
        schema_resolutions={
            "sites": sites.schema_resolution,
            "samples": samples.schema_resolution,
        },
        coordinate_registry=coordinate_audit,
    )

    world_family_fingerprint = fingerprint_world_family(
        node_ids,
        world_adjacencies,
        world_semantics=world_semantics,
    )
    problem = freeze_pre_response_problem(
        node_ids=node_ids,
        component_ids=tuple("southwest_louisiana_marsh" for _ in node_ids),
        context_ids=context_ids,
        candidate_units=effort_ledger.candidate_units,
        observation_semantics=ObservationSemantics(
            effort_eligible_rule=(
                "official site x occasion matrix fixed before KIRA response access"
            ),
            positive_rule="explicit KIRA token 1",
            negative_rule="explicit KIRA token 0",
            unsurveyed_rule=(
                "response-level unavailable token excluded; never silently encoded zero"
            ),
            zero_interpretation="observed non-detection, not biological absence",
        ),
        baseline_fields=(
            BaselineFieldSpec("longitude", "numeric", "forbid"),
            BaselineFieldSpec("latitude", "numeric", "forbid"),
            BaselineFieldSpec("precipitation", "numeric", "forbid"),
            BaselineFieldSpec("min_air_temp", "numeric", "forbid"),
            BaselineFieldSpec("marsh", "categorical", "forbid"),
            BaselineFieldSpec("habitat", "categorical", "forbid"),
        ),
        split_fingerprint=HISTORICAL_SPLIT_FINGERPRINT,
        world_family_fingerprint=world_family_fingerprint,
        source_fingerprint=source_provenance.fingerprint,
    )

    predictive_state = evaluate_predictive_state_design(
        PredictiveStateDesign(
            repeated_measure_endpoint=True,
            train_generator_id="sequential_preoutcome",
            serve_generator_id="sequential_preoutcome",
            refresh_policy="sequential_context",
            source_policy=(
                "immediate_previous_or_cumulative_observed_positive_source_sets"
            ),
            source_label_invariant=True,
            baseline_contains_spatial_coordinates=True,
        )
    )
    if not predictive_state.predictive_use_allowed:
        raise AssertionError("Louisiana sequential source-set design should be v2 eligible")

    certificate = freeze_pre_response_certificate(
        source_provenance=source_provenance,
        normalized_problem=problem,
        coordinate_registry=coordinate_audit,
        structural_gate=structural_gate,
        world_adjacencies=world_adjacencies,
        world_semantics=world_semantics,
        structural_world_ids=tuple(structural_world_ids),
        effort_ledger=effort_ledger,
        observation_contract=observation_contract,
        predictive_state=predictive_state,
        predictive_evaluation_fingerprint=(
            HISTORICAL_PREDICTIVE_EVALUATION_FINGERPRINT
        ),
    )
    if not certificate.predictive_outcome_access_allowed:
        raise AssertionError("fully frozen Louisiana translation should authorize outcome gate")

    return {
        "schema": "eog.louisiana_real_pre_response_v2_translation.v1",
        "uses_biological_response": False,
        "reruns_frozen_endpoint": False,
        "counts_as_predictive_evidence": False,
        "source_rows_recovered_from_authoritative_gate0_log": True,
        "uses_original_safe_file_bytes": False,
        "authoritative_gate0": {
            "run_id": GATE0_RUN_ID,
            "job_id": GATE0_JOB_ID,
            "fingerprint": GATE0_FINGERPRINT,
            "historical_site_registry_fingerprint": (
                HISTORICAL_SITE_REGISTRY_FINGERPRINT
            ),
            "historical_distance_matrix_fingerprint": (
                HISTORICAL_DISTANCE_MATRIX_FINGERPRINT
            ),
            "historical_structural_ladder_fingerprint": (
                HISTORICAL_STRUCTURAL_LADDER_FINGERPRINT
            ),
        },
        "registry": {
            "node_count": len(node_ids),
            "context_count": len(context_ids),
            "chronological_periods": list(chronological_periods),
            "coordinate_fingerprint": coordinate_audit.fingerprint,
        },
        "effort": {
            "surveyed_count": effort_ledger.surveyed_count,
            "initialization_count": effort_ledger.initialization_count,
            "scored_candidate_count": effort_ledger.candidate_count,
            "unsurveyed_count": effort_ledger.unsurveyed_count,
            "fingerprint": effort_ledger.fingerprint,
        },
        "worlds": {
            "declared_world_count": len(world_adjacencies),
            "distinct_geometry_thresholds_km": list(observed_thresholds),
            "structural_world_ids": list(certificate.structural_world_ids),
            "world_family_fingerprint_v2": world_family_fingerprint,
            "distance_matrix_fingerprint_matches_historical": True,
            "structural_ladder_fingerprint_matches_historical": True,
            "structural_gate_passed": structural_gate.passed,
        },
        "observation": {
            "mode": observation_contract.mode,
            "fingerprint": observation_contract.fingerprint,
        },
        "predictive_state": {
            "status": predictive_state.status,
            "predictive_use_allowed": predictive_state.predictive_use_allowed,
            "fingerprint": predictive_state.fingerprint,
        },
        "certificate": {
            "predictive_outcome_access_allowed": (
                certificate.predictive_outcome_access_allowed
            ),
            "predictive_evaluation_fingerprint": (
                certificate.predictive_evaluation_fingerprint
            ),
            "fingerprint": certificate.fingerprint,
        },
        "interpretation": (
            "The historical Louisiana response-blind registry translates into the "
            "generic v2 contracts without opening KIRA.csv: 33 initialization-only "
            "units seed state, 627 units are scored, the three frozen geometry scales "
            "are recovered, two source-update rules remain distinct worlds despite "
            "sharing adjacency, external_open is excluded from structural adequacy, "
            "and the sequential label-invariant Layer-B design is eligible."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
