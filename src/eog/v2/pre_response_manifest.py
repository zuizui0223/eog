"""Declarative pre-response manifest runner for EOG-WF v2.

Version 1 intentionally supports only local response-independent CSV input and the
existing response-blind geographic scale ladder. It never downloads a response,
discovers aliases, invents effort, or tunes a predictive representation.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

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
from eog.v2.tabular_adapter import StrictCSVPolicy, parse_response_blind_csv
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


MANIFEST_SCHEMA = "eog.pre_response_manifest.v1"
RESULT_SCHEMA = "eog.pre_response_manifest_result.v1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a JSON array")
    return value


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _strict_bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be boolean")
    return value


def _strict_int(value: object, label: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    return value


def _safe_local_path(manifest_path: Path, declared: object) -> Path:
    text = _text(declared, "safe_source.path")
    relative = Path(text)
    if relative.is_absolute():
        raise ValueError("safe_source.path must be relative to the manifest directory")
    base = manifest_path.parent.resolve()
    resolved = (base / relative).resolve()
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise ValueError("safe_source.path must not escape the manifest directory") from exc
    if not resolved.is_file():
        raise ValueError(f"safe_source.path does not exist as a file: {text}")
    return resolved


def _haversine_matrix(coordinates: np.ndarray) -> np.ndarray:
    values = np.asarray(coordinates, dtype=float)
    if values.ndim != 2 or values.shape[1] != 2:
        raise ValueError("haversine coordinates must be an n x 2 lon/lat matrix")
    lon = values[:, 0]
    lat = values[:, 1]
    if np.any(lon < -180) or np.any(lon > 180) or np.any(lat < -90) or np.any(lat > 90):
        raise ValueError("haversine_km requires valid longitude/latitude degrees")
    lon_r = np.radians(lon)
    lat_r = np.radians(lat)
    dlon = lon_r[:, None] - lon_r[None, :]
    dlat = lat_r[:, None] - lat_r[None, :]
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat_r[:, None])
        * np.cos(lat_r[None, :])
        * np.sin(dlon / 2) ** 2
    )
    a = np.clip(a, 0.0, 1.0)
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def _distance_matrix(coordinates: np.ndarray, metric: str) -> np.ndarray:
    values = np.asarray(coordinates, dtype=float)
    if metric == "euclidean":
        return np.linalg.norm(values[:, None, :] - values[None, :, :], axis=2)
    if metric == "haversine_km":
        return _haversine_matrix(values)
    raise ValueError("coordinate_registry.distance_metric must be euclidean or haversine_km")


def _split_fingerprint(candidate_units: Sequence[object]) -> str:
    return _canonical_sha256(
        {
            "schema": "eog.manifest_split.v1",
            "units": [
                {"unit_id": unit.unit_id, "fold": int(unit.fold)}
                for unit in candidate_units
            ],
        }
    )


def _component_ids(
    node_ids: tuple[str, ...],
    manifest: Mapping[str, object],
) -> tuple[str, ...]:
    components = _mapping(manifest.get("components", {}), "components")
    by_node_raw = components.get("by_node")
    if by_node_raw is not None:
        by_node = _mapping(by_node_raw, "components.by_node")
        if set(by_node) != set(node_ids):
            raise ValueError("components.by_node keys must exactly match frozen node_ids")
        return tuple(_text(by_node[node], f"component for {node}") for node in node_ids)
    default = _text(components.get("default_component_id", "all"), "default_component_id")
    return tuple(default for _ in node_ids)


def _baseline_fields(manifest: Mapping[str, object]) -> tuple[BaselineFieldSpec, ...]:
    rows = _sequence(manifest.get("baseline_fields", []), "baseline_fields")
    return tuple(
        BaselineFieldSpec(
            name=_text(_mapping(row, "baseline field").get("name"), "baseline field name"),
            kind=_mapping(row, "baseline field").get("kind"),  # type: ignore[arg-type]
            missing_policy=_mapping(row, "baseline field").get("missing_policy"),  # type: ignore[arg-type]
        )
        for row in rows
    )


def run_pre_response_manifest(
    manifest_path: Path,
) -> dict[str, object]:
    """Build one response-locked generic certificate from a local manifest."""

    manifest_path = Path(manifest_path)
    raw_manifest = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw_manifest.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("manifest must be valid UTF-8 JSON") from exc
    manifest = _mapping(manifest, "manifest")
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"manifest schema must equal {MANIFEST_SCHEMA!r}")

    source_spec = _mapping(manifest.get("safe_source"), "safe_source")
    source_path = _safe_local_path(manifest_path, source_spec.get("path"))
    source_bytes = source_path.read_bytes()
    expected_size = _strict_int(
        source_spec.get("expected_size_bytes"),
        "safe_source.expected_size_bytes",
        minimum=0,
    )
    expected_sha256 = _text(
        source_spec.get("expected_sha256"), "safe_source.expected_sha256"
    ).lower()
    if len(expected_sha256) != 64 or any(
        char not in "0123456789abcdef" for char in expected_sha256
    ):
        raise ValueError("safe_source.expected_sha256 must be a 64-character hex digest")
    observed_sha256 = _sha256_bytes(source_bytes)
    if len(source_bytes) != expected_size:
        raise ValueError("safe source byte-size differs from manifest")
    if observed_sha256 != expected_sha256:
        raise ValueError("safe source SHA-256 differs from manifest")

    role_rows = _sequence(manifest.get("schema_roles"), "schema_roles")
    roles = []
    for row in role_rows:
        item = _mapping(row, "schema role")
        aliases = tuple(
            _text(value, "schema alias")
            for value in _sequence(item.get("aliases"), "schema aliases")
        )
        required = item.get("required", True)
        roles.append(
            SchemaRole(
                role=_text(item.get("role"), "schema role"),
                aliases=aliases,
                required=_strict_bool(required, "schema role required"),
            )
        )
    schema_contract = SchemaAliasContract(
        roles=tuple(roles),
        allow_unmapped_columns=_strict_bool(
            manifest.get("allow_unmapped_columns", True),
            "allow_unmapped_columns",
        ),
    )

    csv_raw = _mapping(source_spec.get("csv_policy", {}), "safe_source.csv_policy")
    csv_policy = StrictCSVPolicy(
        encoding=str(csv_raw.get("encoding", "utf-8")),
        allow_utf8_bom=_strict_bool(
            csv_raw.get("allow_utf8_bom", False),
            "safe_source.csv_policy.allow_utf8_bom",
        ),
        require_data_rows=_strict_bool(
            csv_raw.get("require_data_rows", True),
            "safe_source.csv_policy.require_data_rows",
        ),
    )
    table = parse_response_blind_csv(
        source_bytes,
        schema_contract=schema_contract,
        policy=csv_policy,
    )

    coordinate_spec = _mapping(
        manifest.get("coordinate_registry"), "coordinate_registry"
    )
    node_role = _text(coordinate_spec.get("node_role"), "coordinate_registry.node_role")
    x_role = _text(coordinate_spec.get("x_role"), "coordinate_registry.x_role")
    y_role = _text(coordinate_spec.get("y_role"), "coordinate_registry.y_role")
    known_roles = set(table.canonical_roles)
    if not {node_role, x_role, y_role} <= known_roles:
        raise ValueError("coordinate roles must be present in the canonical schema")

    coordinate_policy = CoordinateRegistryPolicy(
        tolerance=float(coordinate_spec.get("tolerance")),
        units=_text(coordinate_spec.get("units"), "coordinate_registry.units"),
        representative_policy=coordinate_spec.get("representative_policy"),  # type: ignore[arg-type]
    )
    coordinate_audit = audit_coordinate_registry(
        tuple(
            CoordinateObservation(
                node_id=_text(row[node_role], node_role),
                x=float(row[x_role]),
                y=float(row[y_role]),
            )
            for row in table.records()
        ),
        coordinate_policy,
    )
    node_ids = tuple(node.node_id for node in coordinate_audit.nodes)

    contexts = tuple(
        _text(value, "context_id")
        for value in _sequence(manifest.get("contexts"), "contexts")
    )
    if not contexts or len(contexts) != len(set(contexts)):
        raise ValueError("contexts must contain unique non-empty IDs")

    effort_spec = _mapping(manifest.get("effort"), "effort")
    effort_policy_raw = _mapping(effort_spec.get("policy"), "effort.policy")
    effort_policy = EffortEligibilityPolicy(
        unit_definition=_text(
            effort_policy_raw.get("unit_definition"), "effort.policy.unit_definition"
        ),
        eligibility_rule=_text(
            effort_policy_raw.get("eligibility_rule"), "effort.policy.eligibility_rule"
        ),
        unsurveyed_rule=_text(
            effort_policy_raw.get("unsurveyed_rule"), "effort.policy.unsurveyed_rule"
        ),
        evidence_source=effort_policy_raw.get("evidence_source"),  # type: ignore[arg-type]
    )
    effort_rows = []
    for row in _sequence(effort_spec.get("rows"), "effort.rows"):
        item = _mapping(row, "effort row")
        evidence_payload = item.get("evidence_payload")
        summary = item.get("evidence_summary")
        if summary is None:
            summary = json.dumps(
                evidence_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        effort_rows.append(
            EffortContextRow(
                unit_id=_text(item.get("unit_id"), "effort unit_id"),
                node_id=_text(item.get("node_id"), "effort node_id"),
                context_id=_text(item.get("context_id"), "effort context_id"),
                fold=_strict_int(item.get("fold"), "effort fold", minimum=1),
                eligible=_strict_bool(item.get("eligible"), "effort eligible"),
                evidence_summary=_text(summary, "effort evidence_summary"),
                evidence_fingerprint=evidence_fingerprint(evidence_payload),
            )
        )
    effort_ledger = freeze_effort_context_ledger(
        node_ids=node_ids,
        context_ids=contexts,
        rows=tuple(effort_rows),
        policy=effort_policy,
    )

    coords = np.asarray(
        [coordinate_audit.coordinates[node_id] for node_id in node_ids],
        dtype=float,
    )
    metric = _text(
        coordinate_spec.get("distance_metric"), "coordinate_registry.distance_metric"
    )
    distances = _distance_matrix(coords, metric)

    scale_spec = _mapping(manifest.get("world_scale"), "world_scale")
    scale_declaration = StructuralScaleLadderDeclaration(
        axis_id=_text(scale_spec.get("axis_id"), "world_scale.axis_id"),
        target_largest_component_fractions=tuple(
            float(value)
            for value in _sequence(
                scale_spec.get("target_largest_component_fractions"),
                "world_scale.target_largest_component_fractions",
            )
        ),
    )
    ladder = build_structural_scale_ladder(
        node_ids,
        distances,
        scale_declaration,
    )
    worlds = structural_scale_adjacencies(ladder, distances)
    horizon = _strict_int(scale_spec.get("horizon"), "world_scale.horizon", minimum=1)
    structural_audit = audit_world_universe_structure(
        node_ids,
        worlds,
        horizon=horizon,
    )
    adequacy_raw = _mapping(scale_spec.get("adequacy"), "world_scale.adequacy")
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=adequacy_raw.get(
            "min_largest_weak_component_fraction"
        ),
        max_isolated_node_fraction=adequacy_raw.get("max_isolated_node_fraction"),
        min_median_horizon_reachable_fraction=adequacy_raw.get(
            "min_median_horizon_reachable_fraction"
        ),
        require_at_least_one_world_pass=_strict_bool(
            adequacy_raw.get("require_at_least_one_world_pass", True),
            "world_scale.adequacy.require_at_least_one_world_pass",
        ),
    )
    structural_gate = apply_structural_adequacy_gate(structural_audit, adequacy)

    observation_raw = manifest.get("observation_contract")
    observation_contract = None
    if observation_raw is not None:
        observation_raw = _mapping(observation_raw, "observation_contract")
        observation_contract = BinaryObservationContract(
            mode=observation_raw.get("mode"),  # type: ignore[arg-type]
            endpoint_name=_text(
                observation_raw.get("endpoint_name"),
                "observation_contract.endpoint_name",
            ),
            positive_semantics=_text(
                observation_raw.get("positive_semantics"),
                "observation_contract.positive_semantics",
            ),
            negative_semantics=_text(
                observation_raw.get("negative_semantics"),
                "observation_contract.negative_semantics",
            ),
            unavailable_semantics=_text(
                observation_raw.get("unavailable_semantics"),
                "observation_contract.unavailable_semantics",
            ),
            zero_interpretation=_text(
                observation_raw.get("zero_interpretation"),
                "observation_contract.zero_interpretation",
            ),
        )

    predictive_raw = manifest.get("predictive_state")
    predictive_state = None
    if predictive_raw is not None:
        predictive_raw = _mapping(predictive_raw, "predictive_state")
        predictive_state = evaluate_predictive_state_design(
            PredictiveStateDesign(
                repeated_measure_endpoint=_strict_bool(
                    predictive_raw.get("repeated_measure_endpoint"),
                    "predictive_state.repeated_measure_endpoint",
                ),
                train_generator_id=_text(
                    predictive_raw.get("train_generator_id"),
                    "predictive_state.train_generator_id",
                ),
                serve_generator_id=_text(
                    predictive_raw.get("serve_generator_id"),
                    "predictive_state.serve_generator_id",
                ),
                refresh_policy=predictive_raw.get("refresh_policy"),  # type: ignore[arg-type]
                source_policy=_text(
                    predictive_raw.get("source_policy"),
                    "predictive_state.source_policy",
                ),
                source_label_invariant=_strict_bool(
                    predictive_raw.get("source_label_invariant"),
                    "predictive_state.source_label_invariant",
                ),
                baseline_contains_spatial_coordinates=_strict_bool(
                    predictive_raw.get(
                        "baseline_contains_spatial_coordinates", False
                    ),
                    "predictive_state.baseline_contains_spatial_coordinates",
                ),
                static_predictive_opt_in=_strict_bool(
                    predictive_raw.get("static_predictive_opt_in", False),
                    "predictive_state.static_predictive_opt_in",
                ),
            )
        )

    source_provenance = freeze_adapter_source_provenance(
        artifacts=(
            SourceArtifactIdentity.from_bytes(
                _text(source_spec.get("artifact_id"), "safe_source.artifact_id"),
                source_bytes,
            ),
        ),
        schema_resolution=table.schema_resolution,
        coordinate_registry=coordinate_audit,
    )
    world_family_fingerprint = fingerprint_world_family(node_ids, worlds)
    if observation_contract is None:
        positive_rule = "not declared"
        negative_rule = "not declared"
        zero_interpretation = "not declared"
    else:
        positive_rule = observation_contract.positive_semantics
        negative_rule = observation_contract.negative_semantics
        zero_interpretation = observation_contract.zero_interpretation

    problem = freeze_pre_response_problem(
        node_ids=node_ids,
        component_ids=_component_ids(node_ids, manifest),
        context_ids=contexts,
        candidate_units=effort_ledger.candidate_units,
        observation_semantics=ObservationSemantics(
            effort_eligible_rule=effort_policy.eligibility_rule,
            positive_rule=positive_rule,
            negative_rule=negative_rule,
            unsurveyed_rule=effort_policy.unsurveyed_rule,
            zero_interpretation=zero_interpretation,
        ),
        baseline_fields=_baseline_fields(manifest),
        split_fingerprint=_split_fingerprint(effort_ledger.candidate_units),
        world_family_fingerprint=world_family_fingerprint,
        source_fingerprint=source_provenance.fingerprint,
    )
    certificate = freeze_pre_response_certificate(
        source_provenance=source_provenance,
        normalized_problem=problem,
        coordinate_registry=coordinate_audit,
        structural_gate=structural_gate,
        world_adjacencies=worlds,
        effort_ledger=effort_ledger,
        observation_contract=observation_contract,
        predictive_state=predictive_state,
    )

    return {
        "schema": RESULT_SCHEMA,
        "uses_biological_response": False,
        "manifest_sha256": _sha256_bytes(raw_manifest),
        "manifest_semantic_fingerprint": _canonical_sha256(manifest),
        "source": {
            "artifact_id": source_spec["artifact_id"],
            "byte_count": len(source_bytes),
            "sha256": observed_sha256,
            "tabular_fingerprint": table.fingerprint,
            "schema_resolution_fingerprint": table.schema_resolution.fingerprint,
        },
        "coordinate_registry": {
            "status": coordinate_audit.status,
            "node_count": len(node_ids),
            "tolerance_used_node_count": coordinate_audit.tolerance_used_node_count,
            "fingerprint": coordinate_audit.fingerprint,
        },
        "effort_context": {
            "candidate_count": effort_ledger.candidate_count,
            "unsurveyed_count": effort_ledger.unsurveyed_count,
            "fingerprint": effort_ledger.fingerprint,
        },
        "world_scale": {
            "distance_metric": metric,
            "thresholds": list(ladder.thresholds),
            "ladder_fingerprint": ladder.fingerprint,
            "world_family_fingerprint": world_family_fingerprint,
        },
        "structural_gate": {
            "passed": structural_gate.passed,
            "passing_world_ids": list(structural_gate.passing_world_ids),
            "fingerprint": structural_gate.fingerprint,
        },
        "observation_contract": (
            None
            if observation_contract is None
            else {
                "mode": observation_contract.mode,
                "fingerprint": observation_contract.fingerprint,
            }
        ),
        "predictive_state": (
            None
            if predictive_state is None
            else {
                "status": predictive_state.status,
                "predictive_use_allowed": predictive_state.predictive_use_allowed,
                "fingerprint": predictive_state.fingerprint,
            }
        ),
        "normalized_problem": {
            "candidate_unit_count": len(problem.candidate_units),
            "fingerprint": problem.fingerprint,
        },
        "certificate": {
            "structural_status": certificate.structural_status,
            "effort_status": certificate.effort_status,
            "observation_status": certificate.observation_status,
            "predictive_status": certificate.predictive_status,
            "structural_response_access_allowed": (
                certificate.structural_response_access_allowed
            ),
            "predictive_outcome_access_allowed": (
                certificate.predictive_outcome_access_allowed
            ),
            "predictive_use_allowed": certificate.predictive_use_allowed,
            "fingerprint": certificate.fingerprint,
        },
    }


def write_pre_response_manifest_result(
    manifest_path: Path,
    output_path: Path,
) -> dict[str, object]:
    result = run_pre_response_manifest(Path(manifest_path))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result
