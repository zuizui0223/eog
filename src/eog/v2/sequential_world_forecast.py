"""Sequential EOG-WF forecasting with frozen rule worlds and changing source state.

This module handles repeated transition forecasts such as annual metapopulation
colonisation.  The transition rule/world is frozen, while the realised current source
state may change between transitions.  This is deliberately different from the older
static positive-occurrence updater, which keeps one fixed source definition and adds
positive constraints to the same reconstruction.

A transition at time ``t`` is evaluated only as:

    current realised sources at t -> positive transition targets at t+1

Past targets are *not* re-evaluated from later source states.  What accumulates through
time is the surviving set of frozen rule identities.  This prevents a historical
positive occurrence from being incorrectly required to remain reachable from a future
current-state source set.

The module introduces no new connectivity operator.  It reuses declared
``DynamicTransitionOperator`` objects and first-passage support.  Source-state changes
are state updates, not rule retuning.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Sequence

import numpy as np

from ..dynamic_island_reachability import summarize_first_passage
from ..island_state_layers import IslandStateLayers
from .world_forecast import (
    ForecastGateDeclaration,
    ForecastNodeEnvelope,
    WorldForecastMember,
    _state_layers_for_world,
    _supported_state_matrix,
    _world_cumulative_first_passage,
)
from .world_reconstruction import FiniteWorld


SequentialUpdateStatus = Literal["updated", "universe_falsified"]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite_nonnegative(value: float, label: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0.0:
        raise ValueError(f"{label} must be finite and non-negative")
    return result


def finite_world_rule_fingerprint(world: FiniteWorld) -> str:
    """Fingerprint a frozen transition rule while deliberately excluding source state.

    ``FiniteWorld.fingerprint`` remains the full reproducibility fingerprint and still
    includes source IDs/weights.  This rule fingerprint is a second identity used only
    when the scientific design explicitly permits the *current realised source state*
    to change between repeated transition forecasts.
    """

    return _canonical_sha256(
        {
            "world_id": world.world_id,
            "operator_fingerprint": world.operator.fingerprint,
            "geographic_relaxation": world.geographic_relaxation,
            "environmental_relaxation": world.environmental_relaxation,
            "barrier_relaxation": world.barrier_relaxation,
            "analytical_variant": world.analytical_variant,
        }
    )


def _ordered_worlds(worlds: Sequence[FiniteWorld]) -> tuple[FiniteWorld, ...]:
    declared = tuple(worlds)
    if not declared:
        raise ValueError("at least one finite world is required")
    ids = [world.world_id for world in declared]
    if len(set(ids)) != len(ids):
        raise ValueError("world IDs must be unique")
    ordered = tuple(sorted(declared, key=lambda world: world.world_id))
    node_ids = ordered[0].operator.node_ids
    if any(world.operator.node_ids != node_ids for world in ordered[1:]):
        raise ValueError("all worlds must share the same node IDs and order")
    return ordered


def _source_signature(world: FiniteWorld) -> tuple[tuple[str, ...], tuple[float, ...]]:
    return world.source_ids, tuple(float(value) for value in world.source_weights)


def _common_source_state(
    worlds: Sequence[FiniteWorld],
) -> tuple[tuple[str, ...], tuple[float, ...], str]:
    ordered = tuple(worlds)
    if not ordered:
        raise ValueError("at least one current-source world is required")
    signature = _source_signature(ordered[0])
    if any(_source_signature(world) != signature for world in ordered[1:]):
        raise ValueError(
            "all rule worlds must share the same current source IDs and weights; "
            "source uncertainty must be declared as a separate world dimension"
        )
    payload = {
        "node_ids": list(ordered[0].operator.node_ids),
        "source_ids": list(signature[0]),
        "source_weights": list(signature[1]),
    }
    return signature[0], signature[1], _canonical_sha256(payload)


def _ordered_targets(node_ids: tuple[str, ...], values: Sequence[str]) -> tuple[str, ...]:
    requested = tuple(str(value).strip() for value in values)
    if not requested or any(not value for value in requested) or len(set(requested)) != len(requested):
        raise ValueError("positive_target_ids must contain unique non-empty node IDs")
    missing = set(requested).difference(node_ids)
    if missing:
        raise ValueError(f"positive targets are outside the node universe: {sorted(missing)}")
    requested_set = set(requested)
    return tuple(node_id for node_id in node_ids if node_id in requested_set)


@dataclass(frozen=True)
class SequentialWorldRuleState:
    """Cumulative surviving *rule* identities across repeated transition evidence."""

    node_ids: tuple[str, ...]
    rule_fingerprints: tuple[tuple[str, str], ...]
    surviving_world_ids: tuple[str, ...]
    transition_ids: tuple[str, ...]
    evidence_fingerprints: tuple[str, ...]
    support_floor: float
    support_tolerance: float
    coverage_certificate: str
    fingerprint: str


@dataclass(frozen=True)
class TransitionRuleCompatibility:
    world_id: str
    compatible: bool
    source_state_fingerprint: str
    positive_target_ids: tuple[str, ...]
    target_support: tuple[tuple[str, float], ...]
    unsupported_target_ids: tuple[str, ...]
    rule_fingerprint: str
    current_world_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class TransitionEvidenceResult:
    transition_id: str
    source_ids: tuple[str, ...]
    source_weights: tuple[float, ...]
    source_state_fingerprint: str
    positive_target_ids: tuple[str, ...]
    world_results: tuple[TransitionRuleCompatibility, ...]
    retained_world_ids: tuple[str, ...]
    eliminated_world_ids: tuple[str, ...]
    before_state_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class SequentialWorldRuleUpdate:
    before: SequentialWorldRuleState
    after: SequentialWorldRuleState
    evidence: TransitionEvidenceResult
    status: SequentialUpdateStatus
    fingerprint: str


@dataclass(frozen=True)
class SequentialWorldSetForecast:
    """Forecast over surviving frozen rules instantiated with one current source state."""

    transition_id: str
    node_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_weights: tuple[float, ...]
    source_state_fingerprint: str
    surviving_world_ids: tuple[str, ...]
    rule_fingerprints: tuple[tuple[str, str], ...]
    current_world_fingerprints: tuple[tuple[str, str], ...]
    members: tuple[WorldForecastMember, ...]
    node_envelopes: tuple[ForecastNodeEnvelope, ...]
    robust_ids_by_step: tuple[tuple[str, ...], ...]
    contingent_ids_by_step: tuple[tuple[str, ...], ...]
    excluded_ids_by_step: tuple[tuple[str, ...], ...]
    gate_declaration: ForecastGateDeclaration
    state_layer_fingerprints: tuple[tuple[str, str | None], ...]
    max_steps: int
    support_tolerance: float
    rule_state_fingerprint: str
    coverage_certificate: str
    fingerprint: str


def initialize_sequential_world_rule_state(
    worlds: Sequence[FiniteWorld],
    *,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
) -> SequentialWorldRuleState:
    """Freeze rule identity before repeated transition evidence is accumulated."""

    ordered = _ordered_worlds(worlds)
    floor = float(support_floor)
    if not np.isfinite(floor) or not 0.0 < floor < 1.0:
        raise ValueError("support_floor must lie strictly between 0 and 1")
    tolerance = _finite_nonnegative(support_tolerance, "support_tolerance")
    rule_fingerprints = tuple(
        (world.world_id, finite_world_rule_fingerprint(world)) for world in ordered
    )
    surviving = tuple(world.world_id for world in ordered)
    certificate = "exhaustive_frozen_rule_world_set_sequential_transition_state"
    payload = {
        "node_ids": list(ordered[0].operator.node_ids),
        "rule_fingerprints": [list(row) for row in rule_fingerprints],
        "surviving_world_ids": list(surviving),
        "transition_ids": [],
        "evidence_fingerprints": [],
        "support_floor": floor,
        "support_tolerance": tolerance,
        "coverage_certificate": certificate,
    }
    return SequentialWorldRuleState(
        node_ids=ordered[0].operator.node_ids,
        rule_fingerprints=rule_fingerprints,
        surviving_world_ids=surviving,
        transition_ids=(),
        evidence_fingerprints=(),
        support_floor=floor,
        support_tolerance=tolerance,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )


def _validate_rule_universe(
    state: SequentialWorldRuleState,
    worlds: Sequence[FiniteWorld],
) -> tuple[FiniteWorld, ...]:
    ordered = _ordered_worlds(worlds)
    if ordered[0].operator.node_ids != state.node_ids:
        raise ValueError("node universe differs from the frozen sequential rule state")
    current = tuple(
        (world.world_id, finite_world_rule_fingerprint(world)) for world in ordered
    )
    if current != state.rule_fingerprints:
        raise ValueError("transition rule universe changed since sequential state freeze")
    return ordered


def _target_support(
    world: FiniteWorld,
    target_id: str,
    *,
    max_steps: int,
    support_tolerance: float,
) -> float:
    if target_id in set(world.source_ids):
        return 1.0
    summary = summarize_first_passage(
        world.operator,
        world.source_weight_mapping,
        target_id,
        max_steps=max_steps,
        support_tolerance=support_tolerance,
    )
    return float(summary.horizon_support)


def update_sequential_world_rules(
    state: SequentialWorldRuleState,
    worlds: Sequence[FiniteWorld],
    positive_target_ids: Sequence[str],
    *,
    transition_id: str,
    max_steps: int,
) -> SequentialWorldRuleUpdate:
    """Filter surviving rule worlds using only one transition's current sources/targets.

    The supplied ``FiniteWorld`` objects instantiate the *same frozen rule universe*
    with the current transition's realised source IDs/weights.  Source state may differ
    from prior transitions.  Only ``positive_target_ids`` for this transition are
    evaluated; past positives are represented by prior rule contractions and are not
    re-tested from the new source state.
    """

    transition = str(transition_id).strip()
    if not transition:
        raise ValueError("transition_id must be non-empty")
    if transition in set(state.transition_ids):
        raise ValueError("transition_id has already been used in this sequential state")
    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")

    ordered = _validate_rule_universe(state, worlds)
    source_ids, source_weights, source_fingerprint = _common_source_state(ordered)
    targets = _ordered_targets(state.node_ids, positive_target_ids)
    world_by_id = {world.world_id: world for world in ordered}

    results: list[TransitionRuleCompatibility] = []
    retained: list[str] = []
    eliminated: list[str] = []
    for world_id in state.surviving_world_ids:
        world = world_by_id[world_id]
        supports = tuple(
            (
                target_id,
                _target_support(
                    world,
                    target_id,
                    max_steps=int(max_steps),
                    support_tolerance=state.support_tolerance,
                ),
            )
            for target_id in targets
        )
        unsupported = tuple(
            target_id for target_id, support in supports if support <= state.support_tolerance
        )
        compatible = not unsupported
        if compatible:
            retained.append(world_id)
        else:
            eliminated.append(world_id)
        payload = {
            "world_id": world_id,
            "source_state_fingerprint": source_fingerprint,
            "positive_target_ids": list(targets),
            "target_support": [[target_id, support] for target_id, support in supports],
            "unsupported_target_ids": list(unsupported),
            "rule_fingerprint": finite_world_rule_fingerprint(world),
            "current_world_fingerprint": world.fingerprint,
            "max_steps": int(max_steps),
            "support_tolerance": state.support_tolerance,
        }
        results.append(
            TransitionRuleCompatibility(
                world_id=world_id,
                compatible=compatible,
                source_state_fingerprint=source_fingerprint,
                positive_target_ids=targets,
                target_support=supports,
                unsupported_target_ids=unsupported,
                rule_fingerprint=finite_world_rule_fingerprint(world),
                current_world_fingerprint=world.fingerprint,
                fingerprint=_canonical_sha256(payload),
            )
        )

    evidence_payload = {
        "transition_id": transition,
        "source_ids": list(source_ids),
        "source_weights": list(source_weights),
        "source_state_fingerprint": source_fingerprint,
        "positive_target_ids": list(targets),
        "world_results": [(row.world_id, row.fingerprint) for row in results],
        "retained_world_ids": retained,
        "eliminated_world_ids": eliminated,
        "before_state_fingerprint": state.fingerprint,
    }
    evidence = TransitionEvidenceResult(
        transition_id=transition,
        source_ids=source_ids,
        source_weights=source_weights,
        source_state_fingerprint=source_fingerprint,
        positive_target_ids=targets,
        world_results=tuple(results),
        retained_world_ids=tuple(retained),
        eliminated_world_ids=tuple(eliminated),
        before_state_fingerprint=state.fingerprint,
        fingerprint=_canonical_sha256(evidence_payload),
    )

    after_payload = {
        "node_ids": list(state.node_ids),
        "rule_fingerprints": [list(row) for row in state.rule_fingerprints],
        "surviving_world_ids": retained,
        "transition_ids": [*state.transition_ids, transition],
        "evidence_fingerprints": [*state.evidence_fingerprints, evidence.fingerprint],
        "support_floor": state.support_floor,
        "support_tolerance": state.support_tolerance,
        "coverage_certificate": state.coverage_certificate,
    }
    after = SequentialWorldRuleState(
        node_ids=state.node_ids,
        rule_fingerprints=state.rule_fingerprints,
        surviving_world_ids=tuple(retained),
        transition_ids=(*state.transition_ids, transition),
        evidence_fingerprints=(*state.evidence_fingerprints, evidence.fingerprint),
        support_floor=state.support_floor,
        support_tolerance=state.support_tolerance,
        coverage_certificate=state.coverage_certificate,
        fingerprint=_canonical_sha256(after_payload),
    )
    if not set(after.surviving_world_ids).issubset(state.surviving_world_ids):
        raise RuntimeError("transition evidence must not create new surviving rule worlds")

    status: SequentialUpdateStatus = (
        "updated" if after.surviving_world_ids else "universe_falsified"
    )
    update_payload = {
        "before": state.fingerprint,
        "after": after.fingerprint,
        "evidence": evidence.fingerprint,
        "status": status,
    }
    return SequentialWorldRuleUpdate(
        before=state,
        after=after,
        evidence=evidence,
        status=status,
        fingerprint=_canonical_sha256(update_payload),
    )


def build_sequential_worldset_forecast(
    state: SequentialWorldRuleState,
    worlds: Sequence[FiniteWorld],
    *,
    transition_id: str,
    max_steps: int,
    gate_declaration: ForecastGateDeclaration | None = None,
    state_layers_by_world: Mapping[str, IslandStateLayers] | None = None,
) -> SequentialWorldSetForecast:
    """Forecast from a new current source state over the cumulatively surviving rules."""

    transition = str(transition_id).strip()
    if not transition:
        raise ValueError("transition_id must be non-empty")
    if isinstance(max_steps, bool) or not isinstance(max_steps, (int, np.integer)) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if not state.surviving_world_ids:
        raise ValueError("cannot forecast after the frozen rule universe is falsified")

    ordered = _validate_rule_universe(state, worlds)
    source_ids, source_weights, source_fingerprint = _common_source_state(ordered)
    world_by_id = {world.world_id: world for world in ordered}
    selected = tuple(world_by_id[world_id] for world_id in state.surviving_world_ids)
    declaration = gate_declaration or ForecastGateDeclaration(
        reachability_threshold=state.support_tolerance
    )

    members: list[WorldForecastMember] = []
    state_fingerprints: list[tuple[str, str | None]] = []
    for world in selected:
        cumulative = _world_cumulative_first_passage(world, int(max_steps))
        viability, persistence, state_fingerprint = _state_layers_for_world(
            world, declaration, state_layers_by_world
        )
        supported = _supported_state_matrix(cumulative, viability, persistence, declaration)
        source_index = [world.operator.node_ids.index(node_id) for node_id in source_ids]
        if not np.all(supported[0, source_index]):
            raise ValueError(
                f"active forecast gates contradict current source state in world {world.world_id!r}"
            )
        payload = {
            "transition_id": transition,
            "world_id": world.world_id,
            "rule_fingerprint": finite_world_rule_fingerprint(world),
            "current_world_fingerprint": world.fingerprint,
            "source_state_fingerprint": source_fingerprint,
            "state_layer_fingerprint": state_fingerprint,
            "cumulative_reachability": cumulative.tolist(),
            "supported_state": supported.astype(int).tolist(),
            "gate_fingerprint": declaration.fingerprint,
            "rule_state_fingerprint": state.fingerprint,
        }
        members.append(
            WorldForecastMember(
                world_id=world.world_id,
                cumulative_reachability=cumulative,
                supported_state=supported,
                world_fingerprint=world.fingerprint,
                state_layer_fingerprint=state_fingerprint,
                fingerprint=_canonical_sha256(payload),
            )
        )
        state_fingerprints.append((world.world_id, state_fingerprint))

    cumulative_stack = np.stack([member.cumulative_reachability for member in members], axis=0)
    support_stack = np.stack([member.supported_state for member in members], axis=0)
    lower = np.min(cumulative_stack, axis=0)
    upper = np.max(cumulative_stack, axis=0)
    fractions = np.mean(support_stack, axis=0)
    n_worlds = len(members)

    node_rows: list[ForecastNodeEnvelope] = []
    for node_index, node_id in enumerate(state.node_ids):
        statuses: list[str] = []
        for step in range(int(max_steps) + 1):
            count = int(np.sum(support_stack[:, step, node_index]))
            if count == 0:
                statuses.append("excluded_in_all_worlds")
            elif count == n_worlds:
                statuses.append("robustly_supported")
            else:
                statuses.append("contingent")
        possible_hits = np.flatnonzero(np.any(support_stack[:, :, node_index], axis=0))
        robust_hits = np.flatnonzero(np.all(support_stack[:, :, node_index], axis=0))
        horizon_worlds = tuple(
            member.world_id
            for member, flag in zip(members, support_stack[:, -1, node_index], strict=True)
            if bool(flag)
        )
        node_rows.append(
            ForecastNodeEnvelope(
                node_id=node_id,
                lower_reachability_by_step=tuple(float(v) for v in lower[:, node_index]),
                upper_reachability_by_step=tuple(float(v) for v in upper[:, node_index]),
                supporting_world_fraction_by_step=tuple(float(v) for v in fractions[:, node_index]),
                status_by_step=tuple(statuses),  # type: ignore[arg-type]
                supporting_world_ids_at_horizon=horizon_worlds,
                earliest_possible_step=None if possible_hits.size == 0 else int(possible_hits[0]),
                robust_support_step=None if robust_hits.size == 0 else int(robust_hits[0]),
            )
        )

    robust_by_step: list[tuple[str, ...]] = []
    contingent_by_step: list[tuple[str, ...]] = []
    excluded_by_step: list[tuple[str, ...]] = []
    for step in range(int(max_steps) + 1):
        robust_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "robustly_supported")
        )
        contingent_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "contingent")
        )
        excluded_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "excluded_in_all_worlds")
        )

    certificate = "sequential_frozen_rule_world_forecast_with_current_source_state"
    payload = {
        "transition_id": transition,
        "source_state_fingerprint": source_fingerprint,
        "surviving_world_ids": list(state.surviving_world_ids),
        "rule_fingerprints": [list(row) for row in state.rule_fingerprints],
        "current_world_fingerprints": [[world.world_id, world.fingerprint] for world in ordered],
        "member_fingerprints": [member.fingerprint for member in members],
        "node_envelopes": [
            {
                "node_id": row.node_id,
                "lower": list(row.lower_reachability_by_step),
                "upper": list(row.upper_reachability_by_step),
                "fraction": list(row.supporting_world_fraction_by_step),
                "status": list(row.status_by_step),
                "supporting_world_ids_at_horizon": list(row.supporting_world_ids_at_horizon),
                "earliest_possible_step": row.earliest_possible_step,
                "robust_support_step": row.robust_support_step,
            }
            for row in node_rows
        ],
        "gate_fingerprint": declaration.fingerprint,
        "state_layer_fingerprints": state_fingerprints,
        "max_steps": int(max_steps),
        "support_tolerance": state.support_tolerance,
        "rule_state_fingerprint": state.fingerprint,
        "coverage_certificate": certificate,
    }
    return SequentialWorldSetForecast(
        transition_id=transition,
        node_ids=state.node_ids,
        source_ids=source_ids,
        source_weights=source_weights,
        source_state_fingerprint=source_fingerprint,
        surviving_world_ids=state.surviving_world_ids,
        rule_fingerprints=state.rule_fingerprints,
        current_world_fingerprints=tuple((world.world_id, world.fingerprint) for world in ordered),
        members=tuple(members),
        node_envelopes=tuple(node_rows),
        robust_ids_by_step=tuple(robust_by_step),
        contingent_ids_by_step=tuple(contingent_by_step),
        excluded_ids_by_step=tuple(excluded_by_step),
        gate_declaration=declaration,
        state_layer_fingerprints=tuple(state_fingerprints),
        max_steps=int(max_steps),
        support_tolerance=state.support_tolerance,
        rule_state_fingerprint=state.fingerprint,
        coverage_certificate=certificate,
        fingerprint=_canonical_sha256(payload),
    )
