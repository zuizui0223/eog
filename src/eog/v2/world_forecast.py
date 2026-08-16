"""Inverse-conditioned set-valued forecasting over finite EOG worlds.

The forecast is deliberately not a conventional occupancy-probability map.  It first
uses observed positive occurrences to retain only compatible declared worlds, then
propagates first-passage reachability support forward inside each retained world.  The
result keeps world identity attached to every prediction and reports robust,
contingent, and all-world-excluded states at every forecast horizon.

Optional node-level viability and persistence gates may be supplied through
``IslandStateLayers``.  These gates are thresholded separately; they are never
multiplied into an opaque occupancy-like score.  Unless the underlying support layers
have been externally calibrated, all reported values remain assumption-conditioned
support diagnostics rather than probabilities of colonisation, occupancy, persistence,
or ancestry.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Sequence

import numpy as np

from ..dynamic_island_reachability import summarize_first_passage
from ..island_state_layers import IslandStateLayers
from .world_reconstruction import (
    FiniteWorld,
    FiniteWorldReconstruction,
    ReconstructionUpdate,
    compare_reconstructions,
    reconstruct_compatible_worlds,
)


ForecastStatus = Literal[
    "robustly_supported",
    "contingent",
    "excluded_in_all_worlds",
]
ForecastPriorityMode = Literal["robust", "possible", "discriminating"]


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _optional_threshold(value: float | None, label: str) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not np.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must lie in [0, 1] when supplied")
    return result


@dataclass(frozen=True)
class ForecastGateDeclaration:
    """Predeclared gates defining what counts as a supported future state."""

    reachability_threshold: float = 1e-15
    viability_threshold: float | None = None
    persistence_threshold: float | None = None

    def __post_init__(self) -> None:
        reach = float(self.reachability_threshold)
        if not np.isfinite(reach) or not 0.0 <= reach <= 1.0:
            raise ValueError("reachability_threshold must lie in [0, 1]")
        object.__setattr__(self, "reachability_threshold", reach)
        object.__setattr__(
            self,
            "viability_threshold",
            _optional_threshold(self.viability_threshold, "viability_threshold"),
        )
        object.__setattr__(
            self,
            "persistence_threshold",
            _optional_threshold(self.persistence_threshold, "persistence_threshold"),
        )

    @property
    def active_gates(self) -> tuple[str, ...]:
        names = ["reachability"]
        if self.viability_threshold is not None:
            names.append("viability")
        if self.persistence_threshold is not None:
            names.append("persistence")
        return tuple(names)

    @property
    def fingerprint(self) -> str:
        return _canonical_sha256(
            {
                "reachability_threshold": self.reachability_threshold,
                "viability_threshold": self.viability_threshold,
                "persistence_threshold": self.persistence_threshold,
            }
        )


@dataclass(frozen=True)
class WorldForecastMember:
    """One retained world's horizon-by-node forecast, with world identity preserved."""

    world_id: str
    cumulative_reachability: np.ndarray
    supported_state: np.ndarray
    world_fingerprint: str
    state_layer_fingerprint: str | None
    fingerprint: str


@dataclass(frozen=True)
class ForecastNodeEnvelope:
    """Set-valued forecast summary for one node across compatible worlds."""

    node_id: str
    lower_reachability_by_step: tuple[float, ...]
    upper_reachability_by_step: tuple[float, ...]
    supporting_world_fraction_by_step: tuple[float, ...]
    status_by_step: tuple[ForecastStatus, ...]
    supporting_world_ids_at_horizon: tuple[str, ...]
    earliest_possible_step: int | None
    robust_support_step: int | None


@dataclass(frozen=True)
class WorldSetForecast:
    """Inverse-conditioned forecast cube over the retained finite world set."""

    node_ids: tuple[str, ...]
    occurrence_ids: tuple[str, ...]
    compatible_world_ids: tuple[str, ...]
    members: tuple[WorldForecastMember, ...]
    node_envelopes: tuple[ForecastNodeEnvelope, ...]
    robust_ids_by_step: tuple[tuple[str, ...], ...]
    contingent_ids_by_step: tuple[tuple[str, ...], ...]
    excluded_ids_by_step: tuple[tuple[str, ...], ...]
    gate_declaration: ForecastGateDeclaration
    state_layer_fingerprints: tuple[tuple[str, str | None], ...]
    world_fingerprints: tuple[tuple[str, str], ...]
    max_steps: int
    support_floor: float
    support_tolerance: float
    coverage_certificate: str
    reconstruction_fingerprint: str
    fingerprint: str


@dataclass(frozen=True)
class ForecastUpdate:
    """Sequential forecast update after additional positive occurrence evidence."""

    before: WorldSetForecast
    after: WorldSetForecast | None
    reconstruction_update: ReconstructionUpdate
    status: Literal["updated", "universe_falsified"]
    fingerprint: str


@dataclass(frozen=True)
class ForecastFrontierCandidate:
    """One candidate node ranked from a chosen forecast decision perspective."""

    node_id: str
    status: ForecastStatus
    lower_reachability: float
    upper_reachability: float
    supporting_world_fraction: float
    world_split_balance: float
    earliest_possible_step: int | None
    robust_support_step: int | None


@dataclass(frozen=True)
class ForecastFrontierRanking:
    rows: tuple[ForecastFrontierCandidate, ...]
    mode: ForecastPriorityMode
    step: int
    forecast_fingerprint: str
    fingerprint: str


def _ordered_worlds_for_reconstruction(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
) -> tuple[FiniteWorld, ...]:
    declared = tuple(sorted(tuple(worlds), key=lambda world: world.world_id))
    current = tuple((world.world_id, world.fingerprint) for world in declared)
    if current != reconstruction.world_fingerprints:
        raise ValueError("world universe or world definitions changed after reconstruction")
    return declared


def _state_layers_for_world(
    world: FiniteWorld,
    declaration: ForecastGateDeclaration,
    state_layers_by_world: Mapping[str, IslandStateLayers] | None,
) -> tuple[np.ndarray, np.ndarray, str | None]:
    needs_layers = (
        declaration.viability_threshold is not None
        or declaration.persistence_threshold is not None
    )
    if not needs_layers:
        ones = np.ones(len(world.operator.node_ids), dtype=float)
        return ones, ones, None
    if state_layers_by_world is None or world.world_id not in state_layers_by_world:
        raise ValueError(
            f"state layers are required for world {world.world_id!r} because local gates are active"
        )
    layers = state_layers_by_world[world.world_id]
    if layers.node_ids != world.operator.node_ids:
        raise ValueError(f"state layer node order differs for world {world.world_id!r}")
    return (
        np.asarray(layers.viability_support, dtype=float),
        np.asarray(layers.persistence_support, dtype=float),
        layers.fingerprint,
    )


def _world_cumulative_first_passage(world: FiniteWorld, max_steps: int) -> np.ndarray:
    node_ids = world.operator.node_ids
    result = np.zeros((max_steps + 1, len(node_ids)), dtype=float)
    source_set = set(world.source_ids)
    for node_index, node_id in enumerate(node_ids):
        if node_id in source_set:
            result[:, node_index] = 1.0
            continue
        summary = summarize_first_passage(
            world.operator,
            world.source_weight_mapping,
            node_id,
            max_steps=max_steps,
            support_tolerance=0.0,
        )
        result[:, node_index] = summary.cumulative_support
    if np.any(np.diff(result, axis=0) < -1e-12):
        raise RuntimeError("cumulative first-passage support must be monotone in forecast horizon")
    return result


def _supported_state_matrix(
    cumulative: np.ndarray,
    viability: np.ndarray,
    persistence: np.ndarray,
    declaration: ForecastGateDeclaration,
) -> np.ndarray:
    supported = cumulative > declaration.reachability_threshold
    if declaration.viability_threshold is not None:
        supported &= viability[None, :] >= declaration.viability_threshold
    if declaration.persistence_threshold is not None:
        supported &= persistence[None, :] >= declaration.persistence_threshold
    return supported


def build_worldset_forecast(
    reconstruction: FiniteWorldReconstruction,
    worlds: Sequence[FiniteWorld],
    *,
    gate_declaration: ForecastGateDeclaration | None = None,
    state_layers_by_world: Mapping[str, IslandStateLayers] | None = None,
) -> WorldSetForecast:
    """Build an identity-preserving forecast over the compatible world set.

    The algorithm performs no world averaging.  Every retained world is propagated to
    the reconstruction horizon; node-level forecasts are then summarized by finite-set
    lower/upper support envelopes and robust/contingent/excluded classes.
    """

    if not reconstruction.compatible_world_ids:
        raise ValueError("cannot forecast when the reconstruction has no compatible worlds")
    declaration = gate_declaration or ForecastGateDeclaration(
        reachability_threshold=reconstruction.support_tolerance
    )
    ordered = _ordered_worlds_for_reconstruction(reconstruction, worlds)
    world_by_id = {world.world_id: world for world in ordered}
    selected = tuple(world_by_id[world_id] for world_id in reconstruction.compatible_world_ids)

    members: list[WorldForecastMember] = []
    state_fingerprints: list[tuple[str, str | None]] = []
    for world in selected:
        cumulative = _world_cumulative_first_passage(world, reconstruction.max_steps)
        viability, persistence, state_fingerprint = _state_layers_for_world(
            world, declaration, state_layers_by_world
        )
        supported = _supported_state_matrix(
            cumulative, viability, persistence, declaration
        )

        occurrence_index = [world.operator.node_ids.index(node_id) for node_id in reconstruction.occurrence_ids]
        if not np.all(supported[-1, occurrence_index]):
            raise ValueError(
                f"active forecast gates contradict observed occurrences in compatible world {world.world_id!r}"
            )

        payload = {
            "world_id": world.world_id,
            "world_fingerprint": world.fingerprint,
            "state_layer_fingerprint": state_fingerprint,
            "cumulative_reachability": cumulative.tolist(),
            "supported_state": supported.astype(int).tolist(),
            "gate_fingerprint": declaration.fingerprint,
            "reconstruction_fingerprint": reconstruction.fingerprint,
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

    node_ids = ordered[0].operator.node_ids
    node_rows: list[ForecastNodeEnvelope] = []
    for node_index, node_id in enumerate(node_ids):
        statuses: list[ForecastStatus] = []
        for step in range(reconstruction.max_steps + 1):
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
                status_by_step=tuple(statuses),
                supporting_world_ids_at_horizon=horizon_worlds,
                earliest_possible_step=None if possible_hits.size == 0 else int(possible_hits[0]),
                robust_support_step=None if robust_hits.size == 0 else int(robust_hits[0]),
            )
        )

    robust_by_step: list[tuple[str, ...]] = []
    contingent_by_step: list[tuple[str, ...]] = []
    excluded_by_step: list[tuple[str, ...]] = []
    for step in range(reconstruction.max_steps + 1):
        robust_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "robustly_supported")
        )
        contingent_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "contingent")
        )
        excluded_by_step.append(
            tuple(row.node_id for row in node_rows if row.status_by_step[step] == "excluded_in_all_worlds")
        )

    certificate = "inverse_conditioned_exhaustive_finite_world_forecast"
    payload = {
        "reconstruction_fingerprint": reconstruction.fingerprint,
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
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
        "coverage_certificate": certificate,
    }
    return WorldSetForecast(
        node_ids=node_ids,
        occurrence_ids=reconstruction.occurrence_ids,
        compatible_world_ids=reconstruction.compatible_world_ids,
        members=tuple(members),
        node_envelopes=tuple(node_rows),
        robust_ids_by_step=tuple(robust_by_step),
        contingent_ids_by_step=tuple(contingent_by_step),
        excluded_ids_by_step=tuple(excluded_by_step),
        gate_declaration=declaration,
        state_layer_fingerprints=tuple(state_fingerprints),
        world_fingerprints=reconstruction.world_fingerprints,
        max_steps=reconstruction.max_steps,
        support_floor=reconstruction.support_floor,
        support_tolerance=reconstruction.support_tolerance,
        coverage_certificate=certificate,
        reconstruction_fingerprint=reconstruction.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )


def forecast_from_occurrences(
    worlds: Sequence[FiniteWorld],
    occurrence_ids: Sequence[str],
    *,
    max_steps: int,
    support_floor: float = 1e-12,
    support_tolerance: float = 1e-15,
    gate_declaration: ForecastGateDeclaration | None = None,
    state_layers_by_world: Mapping[str, IslandStateLayers] | None = None,
) -> WorldSetForecast:
    """Convenience entry point: inverse world reconstruction followed by forecasting."""

    reconstruction = reconstruct_compatible_worlds(
        worlds,
        occurrence_ids,
        max_steps=max_steps,
        support_floor=support_floor,
        support_tolerance=support_tolerance,
    )
    return build_worldset_forecast(
        reconstruction,
        worlds,
        gate_declaration=gate_declaration,
        state_layers_by_world=state_layers_by_world,
    )


def update_worldset_forecast(
    before: WorldSetForecast,
    worlds: Sequence[FiniteWorld],
    added_occurrence_ids: Sequence[str],
    *,
    state_layers_by_world: Mapping[str, IslandStateLayers] | None = None,
) -> ForecastUpdate:
    """Update the forecast after new positive occurrence evidence without retuning worlds."""

    added = tuple(str(value).strip() for value in added_occurrence_ids)
    if not added or any(not value for value in added) or len(set(added)) != len(added):
        raise ValueError("added_occurrence_ids must contain unique non-empty IDs")
    combined = tuple(dict.fromkeys((*before.occurrence_ids, *added)))

    ordered = tuple(sorted(tuple(worlds), key=lambda world: world.world_id))
    current_fingerprints = tuple((world.world_id, world.fingerprint) for world in ordered)
    if current_fingerprints != before.world_fingerprints:
        raise ValueError("world universe or world definitions changed since the previous forecast")

    if before.state_layer_fingerprints:
        expected_state = dict(before.state_layer_fingerprints)
        for world_id, expected in before.state_layer_fingerprints:
            if expected is None:
                continue
            if state_layers_by_world is None or world_id not in state_layers_by_world:
                raise ValueError("the previous forecast used state layers that were not supplied for update")
            if state_layers_by_world[world_id].fingerprint != expected_state[world_id]:
                raise ValueError("state layers changed since the previous forecast")

    after_reconstruction = reconstruct_compatible_worlds(
        ordered,
        combined,
        max_steps=before.max_steps,
        support_floor=before.support_floor,
        support_tolerance=before.support_tolerance,
    )

    before_reconstruction = reconstruct_compatible_worlds(
        ordered,
        before.occurrence_ids,
        max_steps=before.max_steps,
        support_floor=before.support_floor,
        support_tolerance=before.support_tolerance,
    )
    if before_reconstruction.fingerprint != before.reconstruction_fingerprint:
        raise ValueError("previous forecast reconstruction cannot be reproduced from the frozen inputs")
    update = compare_reconstructions(before_reconstruction, after_reconstruction)

    if after_reconstruction.compatible_world_ids:
        after = build_worldset_forecast(
            after_reconstruction,
            ordered,
            gate_declaration=before.gate_declaration,
            state_layers_by_world=state_layers_by_world,
        )
        status: Literal["updated", "universe_falsified"] = "updated"
        after_fingerprint: str | None = after.fingerprint
    else:
        after = None
        status = "universe_falsified"
        after_fingerprint = None

    payload = {
        "before": before.fingerprint,
        "after": after_fingerprint,
        "reconstruction_update": update.fingerprint,
        "status": status,
    }
    return ForecastUpdate(
        before=before,
        after=after,
        reconstruction_update=update,
        status=status,
        fingerprint=_canonical_sha256(payload),
    )


def rank_worldset_forecast_frontier(
    forecast: WorldSetForecast,
    *,
    mode: ForecastPriorityMode = "discriminating",
    step: int | None = None,
    exclude_observed: bool = True,
) -> ForecastFrontierRanking:
    """Rank nodes for robust forecast, possible expansion, or world discrimination.

    ``world_split_balance`` is maximal when half the retained worlds support the node
    and half do not.  It is an information-targeting heuristic, not an occurrence
    probability.
    """

    if mode not in {"robust", "possible", "discriminating"}:
        raise ValueError("mode must be 'robust', 'possible', or 'discriminating'")
    resolved_step = forecast.max_steps if step is None else int(step)
    if resolved_step < 0 or resolved_step > forecast.max_steps:
        raise ValueError("step must lie within the forecast horizon")
    observed = set(forecast.occurrence_ids) if exclude_observed else set()

    rows: list[ForecastFrontierCandidate] = []
    for row in forecast.node_envelopes:
        if row.node_id in observed:
            continue
        fraction = row.supporting_world_fraction_by_step[resolved_step]
        split = float(1.0 - abs(2.0 * fraction - 1.0))
        rows.append(
            ForecastFrontierCandidate(
                node_id=row.node_id,
                status=row.status_by_step[resolved_step],
                lower_reachability=row.lower_reachability_by_step[resolved_step],
                upper_reachability=row.upper_reachability_by_step[resolved_step],
                supporting_world_fraction=fraction,
                world_split_balance=split,
                earliest_possible_step=row.earliest_possible_step,
                robust_support_step=row.robust_support_step,
            )
        )

    if mode == "robust":
        rows.sort(
            key=lambda row: (
                row.status != "robustly_supported",
                -row.lower_reachability,
                -row.supporting_world_fraction,
                row.node_id,
            )
        )
    elif mode == "possible":
        rows.sort(
            key=lambda row: (
                row.status == "excluded_in_all_worlds",
                -row.upper_reachability,
                -row.supporting_world_fraction,
                row.node_id,
            )
        )
    else:
        rows.sort(
            key=lambda row: (
                row.status != "contingent",
                -row.world_split_balance,
                -(row.upper_reachability - row.lower_reachability),
                row.node_id,
            )
        )

    payload = {
        "forecast": forecast.fingerprint,
        "mode": mode,
        "step": resolved_step,
        "rows": [
            {
                "node_id": row.node_id,
                "status": row.status,
                "lower": row.lower_reachability,
                "upper": row.upper_reachability,
                "fraction": row.supporting_world_fraction,
                "split": row.world_split_balance,
            }
            for row in rows
        ],
    }
    return ForecastFrontierRanking(
        rows=tuple(rows),
        mode=mode,
        step=resolved_step,
        forecast_fingerprint=forecast.fingerprint,
        fingerprint=_canonical_sha256(payload),
    )
