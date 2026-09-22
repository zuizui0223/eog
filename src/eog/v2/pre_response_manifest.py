"""Declarative manifest compiler for the generic EOG-WF v2 pre-response path.

The manifest surface intentionally consumes only response-independent inputs. It
orchestrates existing schema, coordinate, effort, observation, structural and
prediction-eligibility contracts; it does not invent any of those policies.

All referenced files must be relative to the manifest directory and must remain inside
that directory tree. This keeps a manifest portable and prevents hidden external inputs.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
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


MANIFEST_SCHEMA = "eog.pre_response_manifest.v1"


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    return value


def _sequence(value: object, label: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError(f"{label} must be a JSON array")
    return value


def _resolve_relative(base_dir: Path, value: object, label: str) -> Path:
    text = _text(value, label)
    candidate = Path(text)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be relative to the manifest directory")
    root = base_dir.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"{label} escapes the manifest directory") from exc
    if not resolved.is_file():
        raise ValueError(f"{label} does not exist as a file: {text}")
    return resolved


def _schema_contract(payload: object) -> SchemaAliasContract:
    value = _mapping(payload, "schema contract")
    roles_raw = _sequence(value.get("roles"), "schema roles")
    roles: list[SchemaRole] = []
    for index, raw in enumerate(roles_raw):
        row = _mapping(raw, f"schema role {index}")
        aliases = tuple(
            _text(alias, f"schema role {index} alias")
            for alias in _sequence(row.get("aliases"), f"schema role {index} aliases")
        )
        roles.append(
            SchemaRole(
                role=_text(row.get("role"), f"schema role {index} name"),
                aliases=aliases,
                required=bool(row.get("required", True)),
            )
        )
    return SchemaAliasContract(
        roles=tuple(roles),
        allow_unmapped_columns=bool(value.get("allow_unmapped_columns", True)),
    )


def _csv_policy(payload: object | None) -> StrictCSVPolicy:
    if payload is None:
        return StrictCSVPolicy()
    value = _mapping(payload, "csv_policy")
    return StrictCSVPolicy(
        encoding=str(value.get("encoding", "utf-8")),
        allow_utf8_bom=bool(value.get("allow_utf8_bom", False)),
        require_data_rows=bool(value.get("require_data_rows", True)),
    )


def _load_table(
    base_dir: Path,
    payload: object,
    *,
    label: str,
):
    value = _mapping(payload, label)
    path = _resolve_relative(base_dir, value.get("path"), f"{label}.path")
    raw = path.read_bytes()
    table = parse_response_blind_csv(
        raw,
        schema_contract=_schema_contract(value.get("schema")),
        policy=_csv_policy(value.get("csv_policy")),
    )
    return value, path, raw, table


def _parse_bool_token(
    token: object,
    *,
    true_tokens: set[str],
    false_tokens: set[str],
    label: str,
) -> bool:
    text = str(token)
    if text in true_tokens:
        return True
    if text in false_tokens:
        return False
    raise ValueError(
        f"{label} token {text!r} is neither a declared true nor false token"
    )


def _registry_state(registry_config: Mapping[str, object], table):
    records = table.records()
    required_roles = {"node_id", "x", "y"}
    missing = required_roles - set(table.canonical_roles)
    if missing:
        raise ValueError(f"registry schema is missing canonical roles: {sorted(missing)!r}")

    observations = tuple(
        CoordinateObservation(
            node_id=str(row["node_id"]),
            x=float(row["x"]),
            y=float(row["y"]),
        )
        for row in records
    )
    policy_raw = _mapping(
        registry_config.get("coordinate_policy"),
        "registry_table.coordinate_policy",
    )
    coordinate_policy = CoordinateRegistryPolicy(
        tolerance=float(policy_raw.get("tolerance")),
        units=_text(policy_raw.get("units"), "coordinate_policy.units"),
        representative_policy=str(policy_raw.get("representative_policy")),
    )
    audit = audit_coordinate_registry(observations, coordinate_policy)

    default_component = registry_config.get("default_component_id")
    has_component_role = "component_id" in table.canonical_roles
    if not has_component_role and default_component is None:
        raise ValueError(
            "registry requires canonical component_id role or default_component_id"
        )
    component_by_node: dict[str, str] = {}
    for row in records:
        node_id = _text(row["node_id"], "registry node_id")
        raw_component = row.get("component_id") if has_component_role else default_component
        component = _text(raw_component, f"component_id for node {node_id}")
        previous = component_by_node.get(node_id)
        if previous is not None and previous != component:
            raise ValueError(
                f"node {node_id!r} has inconsistent component IDs: "
                f"{previous!r} and {component!r}"
            )
        component_by_node[node_id] = component
    if set(component_by_node) != set(audit.coordinates):
        raise ValueError("registry component mapping differs from coordinate node set")
    return audit, component_by_node


def _effort_ledger(
    effort_config: Mapping[str, object],
    table,
    *,
    node_ids: Sequence[str],
):
    required_roles = {
        "unit_id",
        "node_id",
        "context_id",
        "fold",
        "eligible",
        "analysis_role",
    }
    missing = required_roles - set(table.canonical_roles)
    if missing:
        raise ValueError(f"effort schema is missing canonical roles: {sorted(missing)!r}")

    true_tokens = {
        str(value)
        for value in _sequence(
            effort_config.get("eligible_true_tokens", ["true", "1"]),
            "effort_table.eligible_true_tokens",
        )
    }
    false_tokens = {
        str(value)
        for value in _sequence(
            effort_config.get("eligible_false_tokens", ["false", "0"]),
            "effort_table.eligible_false_tokens",
        )
    }
    if not true_tokens or not false_tokens or true_tokens & false_tokens:
        raise ValueError("eligible true/false token sets must be non-empty and disjoint")

    evidence_fields = tuple(
        _text(value, "effort evidence field")
        for value in _sequence(
            effort_config.get("evidence_fields"),
            "effort_table.evidence_fields",
        )
    )
    if not evidence_fields or len(evidence_fields) != len(set(evidence_fields)):
        raise ValueError("effort evidence_fields must be non-empty and unique")
    unknown_evidence = set(evidence_fields) - set(table.canonical_roles)
    if unknown_evidence:
        raise ValueError(
            f"effort evidence_fields are not canonical roles: {sorted(unknown_evidence)!r}"
        )

    records = table.records()
    context_values = {_text(row["context_id"], "effort context_id") for row in records}
    context_order_raw = _sequence(
        effort_config.get("context_order"),
        "effort_table.context_order",
    )
    context_order = tuple(_text(value, "context_order value") for value in context_order_raw)
    if len(context_order) != len(set(context_order)):
        raise ValueError("context_order must be unique")
    if set(context_order) != context_values:
        raise ValueError(
            "context_order must exactly cover contexts present in the effort table"
        )

    rows: list[EffortContextRow] = []
    for index, record in enumerate(records, start=1):
        evidence_payload = {field: record.get(field) for field in evidence_fields}
        eligible = _parse_bool_token(
            record["eligible"],
            true_tokens=true_tokens,
            false_tokens=false_tokens,
            label=f"effort row {index} eligible",
        )
        try:
            fold = int(str(record["fold"]))
        except ValueError as exc:
            raise ValueError(f"effort row {index} fold is not an integer") from exc
        rows.append(
            EffortContextRow(
                unit_id=_text(record["unit_id"], f"effort row {index} unit_id"),
                node_id=_text(record["node_id"], f"effort row {index} node_id"),
                context_id=_text(
                    record["context_id"], f"effort row {index} context_id"
                ),
                fold=fold,
                eligible=eligible,
                analysis_role=_text(
                    record["analysis_role"], f"effort row {index} analysis_role"
                ),
                evidence_summary=json.dumps(
                    evidence_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=True,
                ),
                evidence_fingerprint=evidence_fingerprint(evidence_payload),
            )
        )

    policy_raw = _mapping(
        effort_config.get("policy"),
        "effort_table.policy",
    )
    policy = EffortEligibilityPolicy(
        unit_definition=_text(
            policy_raw.get("unit_definition"), "effort policy unit_definition"
        ),
        eligibility_rule=_text(
            policy_raw.get("eligibility_rule"), "effort policy eligibility_rule"
        ),
        unsurveyed_rule=_text(
            policy_raw.get("unsurveyed_rule"), "effort policy unsurveyed_rule"
        ),
        evidence_source=str(policy_raw.get("evidence_source")),
    )
    ledger = freeze_effort_context_ledger(
        node_ids=tuple(node_ids),
        context_ids=context_order,
        rows=tuple(rows),
        policy=policy,
    )
    return ledger, context_order


def _load_world_family(base_dir: Path, payload: object, node_ids: Sequence[str]):
    value = _mapping(payload, "world_family")
    path = _resolve_relative(base_dir, value.get("path"), "world_family.path")
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("world_family.path must contain UTF-8 JSON") from exc
    world_doc = _mapping(data, "world family document")
    declared_nodes = tuple(
        _text(item, "world family node_id")
        for item in _sequence(world_doc.get("node_ids"), "world family node_ids")
    )
    if tuple(node_ids) != declared_nodes:
        raise ValueError(
            "world family node_ids must exactly equal the manifest registry node order"
        )
    worlds_raw = _mapping(world_doc.get("worlds"), "world family worlds")
    worlds: dict[str, np.ndarray] = {}
    for world_id, matrix in worlds_raw.items():
        name = _text(world_id, "world_id")
        worlds[name] = np.asarray(matrix, dtype=float)
    semantics_raw = world_doc.get("world_semantics")
    semantics = None
    if semantics_raw is not None:
        semantics_map = _mapping(semantics_raw, "world_semantics")
        semantics = {str(key): value for key, value in semantics_map.items()}

    structural_ids_raw = world_doc.get("structural_world_ids")
    structural_ids = None
    if structural_ids_raw is not None:
        structural_ids = tuple(
            _text(value, "structural_world_id")
            for value in _sequence(structural_ids_raw, "structural_world_ids")
        )
    try:
        horizon = int(value.get("horizon"))
    except (TypeError, ValueError) as exc:
        raise ValueError("world_family.horizon must be a positive integer") from exc
    if horizon <= 0:
        raise ValueError("world_family.horizon must be a positive integer")
    return path, raw, worlds, semantics, structural_ids, horizon


def _observation_contract(payload: object) -> BinaryObservationContract:
    value = _mapping(payload, "observation_contract")
    return BinaryObservationContract(
        mode=str(value.get("mode")),
        endpoint_name=_text(value.get("endpoint_name"), "observation endpoint_name"),
        positive_semantics=_text(
            value.get("positive_semantics"), "observation positive_semantics"
        ),
        negative_semantics=_text(
            value.get("negative_semantics"), "observation negative_semantics"
        ),
        unavailable_semantics=_text(
            value.get("unavailable_semantics"), "observation unavailable_semantics"
        ),
        zero_interpretation=_text(
            value.get("zero_interpretation"), "observation zero_interpretation"
        ),
    )


def _predictive_state(payload: object | None):
    if payload is None:
        return None
    value = _mapping(payload, "predictive_state")
    design = PredictiveStateDesign(
        repeated_measure_endpoint=bool(value.get("repeated_measure_endpoint")),
        train_generator_id=_text(
            value.get("train_generator_id"), "predictive train_generator_id"
        ),
        serve_generator_id=_text(
            value.get("serve_generator_id"), "predictive serve_generator_id"
        ),
        refresh_policy=str(value.get("refresh_policy")),
        source_policy=_text(value.get("source_policy"), "predictive source_policy"),
        source_label_invariant=bool(value.get("source_label_invariant")),
        baseline_contains_spatial_coordinates=bool(
            value.get("baseline_contains_spatial_coordinates", False)
        ),
        static_predictive_opt_in=bool(value.get("static_predictive_opt_in", False)),
    )
    return evaluate_predictive_state_design(design)


def _baseline_fields(payload: object | None) -> tuple[BaselineFieldSpec, ...]:
    if payload is None:
        return ()
    values = _sequence(payload, "baseline_fields")
    result = []
    for index, raw in enumerate(values):
        row = _mapping(raw, f"baseline field {index}")
        result.append(
            BaselineFieldSpec(
                name=_text(row.get("name"), f"baseline field {index} name"),
                kind=str(row.get("kind")),
                missing_policy=str(row.get("missing_policy")),
            )
        )
    return tuple(result)


def _certificate_dict(certificate) -> dict[str, object]:
    return asdict(certificate)


def compile_pre_response_manifest(
    manifest: Mapping[str, object],
    *,
    base_dir: Path,
) -> dict[str, object]:
    """Compile a declarative manifest to the generic pre-response certificate."""

    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"manifest schema must be {MANIFEST_SCHEMA!r}")

    registry_cfg, registry_path, registry_bytes, registry_table = _load_table(
        base_dir,
        manifest.get("registry_table"),
        label="registry_table",
    )
    effort_cfg, effort_path, effort_bytes, effort_table = _load_table(
        base_dir,
        manifest.get("effort_table"),
        label="effort_table",
    )
    coordinate_audit, component_by_node = _registry_state(
        registry_cfg,
        registry_table,
    )

    world_cfg = _mapping(manifest.get("world_family"), "world_family")
    world_path_value = world_cfg.get("path")
    # World node order is part of the declared geometry identity.
    world_path = _resolve_relative(base_dir, world_path_value, "world_family.path")
    world_doc = json.loads(world_path.read_text(encoding="utf-8"))
    world_node_ids = tuple(
        _text(value, "world family node_id")
        for value in _sequence(
            _mapping(world_doc, "world family document").get("node_ids"),
            "world family node_ids",
        )
    )
    if set(world_node_ids) != set(coordinate_audit.coordinates):
        raise ValueError("world family node set differs from coordinate registry")

    effort_ledger, context_order = _effort_ledger(
        effort_cfg,
        effort_table,
        node_ids=world_node_ids,
    )
    (
        world_path,
        world_bytes,
        worlds,
        world_semantics,
        structural_world_ids,
        horizon,
    ) = _load_world_family(base_dir, manifest.get("world_family"), world_node_ids)

    source_artifacts = (
        SourceArtifactIdentity.from_bytes(
            _text(registry_cfg.get("artifact_id", "registry"), "registry artifact_id"),
            registry_bytes,
        ),
        SourceArtifactIdentity.from_bytes(
            _text(effort_cfg.get("artifact_id", "effort"), "effort artifact_id"),
            effort_bytes,
        ),
        SourceArtifactIdentity.from_bytes(
            _text(world_cfg.get("artifact_id", "world_family"), "world artifact_id"),
            world_bytes,
        ),
    )
    source_provenance = freeze_adapter_source_provenance(
        artifacts=source_artifacts,
        schema_resolutions={
            "registry": registry_table.schema_resolution,
            "effort": effort_table.schema_resolution,
        },
        coordinate_registry=coordinate_audit,
    )

    world_family_fingerprint = fingerprint_world_family(
        world_node_ids,
        worlds,
        world_semantics=world_semantics,
    )
    split_fingerprint = _sha256(
        {
            "schema": "eog.manifest_split.v1",
            "candidate_units": [
                [unit.unit_id, unit.fold] for unit in effort_ledger.candidate_units
            ],
        }
    )
    observation = _observation_contract(manifest.get("observation_contract"))
    problem = freeze_pre_response_problem(
        node_ids=world_node_ids,
        component_ids=tuple(component_by_node[node] for node in world_node_ids),
        context_ids=context_order,
        candidate_units=effort_ledger.candidate_units,
        observation_semantics=ObservationSemantics(
            effort_eligible_rule=effort_ledger.rows[0].evidence_summary
            if manifest.get("observation_semantics") is None
            else _text(
                _mapping(
                    manifest.get("observation_semantics"),
                    "observation_semantics",
                ).get("effort_eligible_rule"),
                "observation_semantics.effort_eligible_rule",
            ),
            positive_rule=observation.positive_semantics,
            negative_rule=observation.negative_semantics,
            unsurveyed_rule=_text(
                _mapping(effort_cfg.get("policy"), "effort_table.policy").get(
                    "unsurveyed_rule"
                ),
                "effort policy unsurveyed_rule",
            ),
            zero_interpretation=observation.zero_interpretation,
        ),
        baseline_fields=_baseline_fields(manifest.get("baseline_fields")),
        split_fingerprint=split_fingerprint,
        world_family_fingerprint=world_family_fingerprint,
        source_fingerprint=source_provenance.fingerprint,
    )

    structural_ids = (
        tuple(sorted(worlds))
        if structural_world_ids is None
        else tuple(structural_world_ids)
    )
    structural_adjacencies = {world_id: worlds[world_id] for world_id in structural_ids}
    structural_audit = audit_world_universe_structure(
        world_node_ids,
        structural_adjacencies,
        horizon=horizon,
    )
    adequacy_raw = _mapping(
        manifest.get("structural_adequacy"),
        "structural_adequacy",
    )
    adequacy = StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=adequacy_raw.get(
            "min_largest_weak_component_fraction"
        ),
        max_isolated_node_fraction=adequacy_raw.get("max_isolated_node_fraction"),
        min_median_horizon_reachable_fraction=adequacy_raw.get(
            "min_median_horizon_reachable_fraction"
        ),
        require_at_least_one_world_pass=bool(
            adequacy_raw.get("require_at_least_one_world_pass", True)
        ),
    )
    structural_gate = apply_structural_adequacy_gate(structural_audit, adequacy)

    predictive = _predictive_state(manifest.get("predictive_state"))
    evaluation_payload = manifest.get("predictive_evaluation")
    evaluation_fingerprint = (
        None if evaluation_payload is None else _sha256(evaluation_payload)
    )
    certificate = freeze_pre_response_certificate(
        source_provenance=source_provenance,
        normalized_problem=problem,
        coordinate_registry=coordinate_audit,
        structural_gate=structural_gate,
        world_adjacencies=worlds,
        world_semantics=world_semantics,
        structural_world_ids=structural_ids,
        effort_ledger=effort_ledger,
        observation_contract=observation,
        predictive_state=predictive,
        predictive_evaluation_fingerprint=evaluation_fingerprint,
    )

    result = {
        "schema": "eog.pre_response_manifest_result.v1",
        "manifest_fingerprint": _sha256(manifest),
        "inputs": {
            "registry_path": str(registry_path.relative_to(base_dir.resolve())),
            "effort_path": str(effort_path.relative_to(base_dir.resolve())),
            "world_family_path": str(world_path.relative_to(base_dir.resolve())),
        },
        "counts": {
            "node_count": len(world_node_ids),
            "context_count": len(context_order),
            "scored_candidate_count": effort_ledger.candidate_count,
            "initialization_count": effort_ledger.initialization_count,
            "unsurveyed_count": effort_ledger.unsurveyed_count,
            "declared_world_count": len(worlds),
            "structural_world_count": len(structural_ids),
        },
        "fingerprints": {
            "registry_table": registry_table.fingerprint,
            "effort_table": effort_table.fingerprint,
            "coordinate_registry": coordinate_audit.fingerprint,
            "effort_context": effort_ledger.fingerprint,
            "source_provenance": source_provenance.fingerprint,
            "world_family": world_family_fingerprint,
            "normalized_problem": problem.fingerprint,
            "structural_gate": structural_gate.fingerprint,
            "observation_contract": observation.fingerprint,
            "predictive_state": None if predictive is None else predictive.fingerprint,
            "predictive_evaluation": evaluation_fingerprint,
            "certificate": certificate.fingerprint,
        },
        "statuses": {
            "structural": certificate.structural_status,
            "effort": certificate.effort_status,
            "observation": certificate.observation_status,
            "predictive": certificate.predictive_status,
            "structural_response_access_allowed": (
                certificate.structural_response_access_allowed
            ),
            "predictive_outcome_access_allowed": (
                certificate.predictive_outcome_access_allowed
            ),
            "predictive_use_allowed": certificate.predictive_use_allowed,
        },
        "certificate": _certificate_dict(certificate),
    }
    result["result_fingerprint"] = _sha256(result)
    return result


def compile_pre_response_manifest_file(path: Path) -> dict[str, object]:
    manifest_path = path.resolve()
    if not manifest_path.is_file():
        raise ValueError(f"manifest file does not exist: {path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("manifest must be UTF-8 JSON") from exc
    manifest = _mapping(payload, "manifest")
    return compile_pre_response_manifest(manifest, base_dir=manifest_path.parent)
