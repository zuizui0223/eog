"""Domain-agnostic exact finite ecological x observation world engine.

EOG v3 treats ecological and observation-process uncertainty as separate finite axes.
An ecological world maps targets to latent ecological states.
An observation world maps (channel, ecological state) to a finite support set of
possible outcomes.
A joint world survives an evidence sequence exactly when every observed outcome is
contained in the relevant support set.

The engine uses support/possibility only. It assigns no priors, posterior weights,
or hard-falsification thresholds to nonzero-probability events.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import combinations
from typing import Mapping, Sequence


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EcologicalWorld:
    world_id: str
    state_by_target: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        world_id = str(self.world_id).strip()
        if not world_id:
            raise ValueError("ecological world_id must be non-empty")
        rows = tuple(
            (str(target).strip(), str(state).strip())
            for target, state in self.state_by_target
        )
        if not rows or any(not target or not state for target, state in rows):
            raise ValueError("state_by_target must contain non-empty target/state pairs")
        targets = [target for target, _ in rows]
        if len(set(targets)) != len(targets):
            raise ValueError("state_by_target target IDs must be unique")
        object.__setattr__(self, "world_id", world_id)
        object.__setattr__(self, "state_by_target", tuple(sorted(rows)))

    @property
    def states(self) -> dict[str, str]:
        return dict(self.state_by_target)


@dataclass(frozen=True)
class ObservationSupport:
    channel_id: str
    ecological_state: str
    possible_outcomes: tuple[str, ...]

    def __post_init__(self) -> None:
        channel = str(self.channel_id).strip()
        state = str(self.ecological_state).strip()
        outcomes = tuple(sorted({str(value) for value in self.possible_outcomes}))
        if not channel or not state:
            raise ValueError("channel_id and ecological_state must be non-empty")
        if not outcomes or any(not value for value in outcomes):
            raise ValueError("possible_outcomes must contain non-empty values")
        object.__setattr__(self, "channel_id", channel)
        object.__setattr__(self, "ecological_state", state)
        object.__setattr__(self, "possible_outcomes", outcomes)


@dataclass(frozen=True)
class ObservationWorld:
    world_id: str
    supports: tuple[ObservationSupport, ...]

    def __post_init__(self) -> None:
        world_id = str(self.world_id).strip()
        if not world_id:
            raise ValueError("observation world_id must be non-empty")
        rows = tuple(self.supports)
        if not rows:
            raise ValueError("observation world must contain at least one support row")
        keys = [(row.channel_id, row.ecological_state) for row in rows]
        if len(set(keys)) != len(keys):
            raise ValueError("observation support channel/state keys must be unique")
        object.__setattr__(self, "world_id", world_id)
        object.__setattr__(
            self,
            "supports",
            tuple(sorted(rows, key=lambda row: (row.channel_id, row.ecological_state))),
        )

    @property
    def support_mapping(self) -> dict[tuple[str, str], tuple[str, ...]]:
        return {
            (row.channel_id, row.ecological_state): row.possible_outcomes
            for row in self.supports
        }


@dataclass(frozen=True)
class EvidenceEvent:
    target_id: str
    channel_id: str
    observed_outcome: str

    def __post_init__(self) -> None:
        values = tuple(
            str(value).strip()
            for value in (
                self.target_id,
                self.channel_id,
                self.observed_outcome,
            )
        )
        if any(not value for value in values):
            raise ValueError("evidence event values must be non-empty")
        object.__setattr__(self, "target_id", values[0])
        object.__setattr__(self, "channel_id", values[1])
        object.__setattr__(self, "observed_outcome", values[2])


@dataclass(frozen=True)
class JointMember:
    ecological_world_id: str
    observation_world_id: str

    @property
    def joint_id(self) -> str:
        return f"{self.ecological_world_id}::{self.observation_world_id}"


@dataclass(frozen=True)
class JointWorldEvaluation:
    declared_ecological_world_ids: tuple[str, ...]
    declared_observation_world_ids: tuple[str, ...]
    evidence_events: tuple[EvidenceEvent, ...]
    surviving_members: tuple[JointMember, ...]
    ecological_projection: tuple[str, ...]
    observation_projection: tuple[str, ...]
    universe_falsified: bool
    coverage_certificate: str
    fingerprint: str

    @property
    def surviving_joint_world_ids(self) -> tuple[str, ...]:
        return tuple(member.joint_id for member in self.surviving_members)


@dataclass(frozen=True)
class ActionRanking:
    action_id: str
    guaranteed_joint_pair_splits: int
    worst_case_joint_survivors: int
    worst_case_ecological_survivors: int
    possible_outcomes: tuple[str, ...]


@dataclass(frozen=True)
class JointEvidencePlan:
    rankings: tuple[ActionRanking, ...]
    objective: str
    current_objective_value: int
    best_action_ids: tuple[str, ...]
    fail_closed_no_improvement: bool
    fingerprint: str


def _ordered_ecological_worlds(
    ecological_worlds: Sequence[EcologicalWorld],
) -> tuple[EcologicalWorld, ...]:
    rows = tuple(ecological_worlds)
    if not rows:
        raise ValueError("at least one ecological world is required")
    ids = [row.world_id for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("ecological world IDs must be unique")
    return tuple(sorted(rows, key=lambda row: row.world_id))


def _ordered_observation_worlds(
    observation_worlds: Sequence[ObservationWorld],
) -> tuple[ObservationWorld, ...]:
    rows = tuple(observation_worlds)
    if not rows:
        raise ValueError("at least one observation world is required")
    ids = [row.world_id for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("observation world IDs must be unique")
    return tuple(sorted(rows, key=lambda row: row.world_id))


def _joint_member_compatible(
    ecological_world: EcologicalWorld,
    observation_world: ObservationWorld,
    evidence_events: Sequence[EvidenceEvent],
) -> bool:
    states = ecological_world.states
    supports = observation_world.support_mapping
    for event in evidence_events:
        if event.target_id not in states:
            raise ValueError(
                f"target {event.target_id!r} is absent from ecological world "
                f"{ecological_world.world_id!r}"
            )
        state = states[event.target_id]
        key = (event.channel_id, state)
        if key not in supports:
            raise ValueError(
                f"observation world {observation_world.world_id!r} lacks support "
                f"for channel/state {key!r}"
            )
        if event.observed_outcome not in supports[key]:
            return False
    return True


def evaluate_joint_worlds(
    ecological_worlds: Sequence[EcologicalWorld],
    observation_worlds: Sequence[ObservationWorld],
    evidence_events: Sequence[EvidenceEvent] = (),
) -> JointWorldEvaluation:
    """Exhaustively evaluate the declared Cartesian-product world universe."""

    ecological = _ordered_ecological_worlds(ecological_worlds)
    observation = _ordered_observation_worlds(observation_worlds)
    events = tuple(evidence_events)

    survivors: list[JointMember] = []
    for eco in ecological:
        for obs in observation:
            if _joint_member_compatible(eco, obs, events):
                survivors.append(
                    JointMember(
                        ecological_world_id=eco.world_id,
                        observation_world_id=obs.world_id,
                    )
                )

    surviving = tuple(survivors)
    eco_projection = tuple(sorted({row.ecological_world_id for row in surviving}))
    obs_projection = tuple(sorted({row.observation_world_id for row in surviving}))
    certificate = "exact_exhaustive_finite_ecology_observation_product"
    payload = {
        "ecological_world_ids": [row.world_id for row in ecological],
        "observation_world_ids": [row.world_id for row in observation],
        "events": [
            {
                "target_id": event.target_id,
                "channel_id": event.channel_id,
                "observed_outcome": event.observed_outcome,
            }
            for event in events
        ],
        "surviving_joint_world_ids": [row.joint_id for row in surviving],
        "ecological_projection": list(eco_projection),
        "observation_projection": list(obs_projection),
        "coverage_certificate": certificate,
    }
    return JointWorldEvaluation(
        declared_ecological_world_ids=tuple(row.world_id for row in ecological),
        declared_observation_world_ids=tuple(row.world_id for row in observation),
        evidence_events=events,
        surviving_members=surviving,
        ecological_projection=eco_projection,
        observation_projection=obs_projection,
        universe_falsified=len(surviving) == 0,
        coverage_certificate=certificate,
        fingerprint=_sha256(payload),
    )


def evaluation_is_contraction(
    before: JointWorldEvaluation,
    after: JointWorldEvaluation,
) -> bool:
    """Check exact monotonic contraction for a fixed declared joint universe."""

    if before.declared_ecological_world_ids != after.declared_ecological_world_ids:
        raise ValueError("ecological world universe changed")
    if before.declared_observation_world_ids != after.declared_observation_world_ids:
        raise ValueError("observation world universe changed")
    return (
        set(after.surviving_joint_world_ids).issubset(before.surviving_joint_world_ids)
        and set(after.ecological_projection).issubset(before.ecological_projection)
        and set(after.observation_projection).issubset(before.observation_projection)
    )


def _validate_action_supports(
    evaluation: JointWorldEvaluation,
    action_supports: Mapping[str, Mapping[str, Sequence[str]]],
) -> tuple[str, ...]:
    if not action_supports:
        raise ValueError("action_supports must be non-empty")
    active = set(evaluation.surviving_joint_world_ids)
    action_ids = tuple(sorted(str(action_id) for action_id in action_supports))
    for action_id in action_ids:
        mapping = action_supports[action_id]
        if set(mapping) != active:
            raise ValueError(
                f"action {action_id!r} must define outcomes for every surviving joint world"
            )
        for joint_id, outcomes in mapping.items():
            normalized = tuple(sorted({str(value) for value in outcomes}))
            if not normalized:
                raise ValueError(
                    f"action {action_id!r} has empty outcome support for {joint_id!r}"
                )
    return action_ids


def _summarize_action(
    evaluation: JointWorldEvaluation,
    action_id: str,
    outcome_support: Mapping[str, Sequence[str]],
) -> ActionRanking:
    support = {
        joint_id: frozenset(str(value) for value in outcomes)
        for joint_id, outcomes in outcome_support.items()
    }
    member_by_id = {
        member.joint_id: member for member in evaluation.surviving_members
    }
    joint_ids = tuple(sorted(member_by_id))

    split_pairs = sum(
        1
        for left, right in combinations(joint_ids, 2)
        if support[left].isdisjoint(support[right])
    )
    outcomes = tuple(
        sorted(set().union(*(support[joint_id] for joint_id in joint_ids)))
    )
    worst_joint = 0
    worst_eco = 0
    for outcome in outcomes:
        surviving_ids = [
            joint_id for joint_id in joint_ids if outcome in support[joint_id]
        ]
        worst_joint = max(worst_joint, len(surviving_ids))
        worst_eco = max(
            worst_eco,
            len(
                {
                    member_by_id[joint_id].ecological_world_id
                    for joint_id in surviving_ids
                }
            ),
        )
    return ActionRanking(
        action_id=action_id,
        guaranteed_joint_pair_splits=split_pairs,
        worst_case_joint_survivors=worst_joint,
        worst_case_ecological_survivors=worst_eco,
        possible_outcomes=outcomes,
    )


def plan_next_evidence_action(
    evaluation: JointWorldEvaluation,
    action_supports: Mapping[str, Mapping[str, Sequence[str]]],
    *,
    objective: str,
) -> JointEvidencePlan:
    """Rank stochastic actions under a declared robust objective.

    objective='joint' minimizes worst-case surviving joint worlds.
    objective='ecological' minimizes worst-case ecological projection size.
    If no action strictly improves the current objective value, the planner fails closed
    and returns no best action.
    """

    if objective not in {"joint", "ecological"}:
        raise ValueError("objective must be 'joint' or 'ecological'")
    action_ids = _validate_action_supports(evaluation, action_supports)
    rankings = tuple(
        sorted(
            (
                _summarize_action(
                    evaluation,
                    action_id,
                    action_supports[action_id],
                )
                for action_id in action_ids
            ),
            key=lambda row: (
                row.worst_case_joint_survivors
                if objective == "joint"
                else row.worst_case_ecological_survivors,
                -row.guaranteed_joint_pair_splits,
                row.action_id,
            ),
        )
    )

    current_value = (
        len(evaluation.surviving_members)
        if objective == "joint"
        else len(evaluation.ecological_projection)
    )
    values = [
        row.worst_case_joint_survivors
        if objective == "joint"
        else row.worst_case_ecological_survivors
        for row in rankings
    ]
    best_value = min(values)
    if best_value >= current_value:
        best_ids: tuple[str, ...] = ()
        fail_closed = True
    else:
        best_ids = tuple(
            row.action_id
            for row, value in zip(rankings, values, strict=True)
            if value == best_value
        )
        fail_closed = False

    payload = {
        "evaluation_fingerprint": evaluation.fingerprint,
        "objective": objective,
        "current_value": current_value,
        "rankings": [
            {
                "action_id": row.action_id,
                "guaranteed_joint_pair_splits": row.guaranteed_joint_pair_splits,
                "worst_case_joint_survivors": row.worst_case_joint_survivors,
                "worst_case_ecological_survivors": row.worst_case_ecological_survivors,
                "possible_outcomes": list(row.possible_outcomes),
            }
            for row in rankings
        ],
        "best_action_ids": list(best_ids),
        "fail_closed_no_improvement": fail_closed,
    }
    return JointEvidencePlan(
        rankings=rankings,
        objective=objective,
        current_objective_value=current_value,
        best_action_ids=best_ids,
        fail_closed_no_improvement=fail_closed,
        fingerprint=_sha256(payload),
    )
