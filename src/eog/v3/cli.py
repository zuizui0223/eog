"""JSON CLI for the EOG v3 joint-world engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .adaptive import (
    adaptive_forced_first_depth,
    plan_robust_evidence_set,
    solve_adaptive_evidence_policy,
)

from .joint_world_engine import (
    EcologicalWorld,
    EvidenceEvent,
    ObservationSupport,
    ObservationWorld,
    evaluate_joint_worlds,
    plan_next_evidence_action,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input JSON must contain one top-level object")
    return value


def _write_json(path: Path, value: dict[str, Any], *, force: bool) -> None:
    output = path.resolve()
    if output.exists() and not force:
        raise FileExistsError(
            f"output already exists: {output}; pass --force to replace it"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parse_ecological_worlds(payload: dict[str, Any]) -> tuple[EcologicalWorld, ...]:
    rows = payload.get("ecological_worlds")
    if not isinstance(rows, list) or not rows:
        raise ValueError("ecological_worlds must be a non-empty list")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each ecological world must be an object")
        states = row.get("state_by_target")
        if not isinstance(states, dict) or not states:
            raise ValueError("state_by_target must be a non-empty object")
        result.append(
            EcologicalWorld(
                world_id=str(row["world_id"]),
                state_by_target=tuple(
                    (str(target), str(state))
                    for target, state in states.items()
                ),
            )
        )
    return tuple(result)


def _parse_observation_worlds(payload: dict[str, Any]) -> tuple[ObservationWorld, ...]:
    rows = payload.get("observation_worlds")
    if not isinstance(rows, list) or not rows:
        raise ValueError("observation_worlds must be a non-empty list")
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each observation world must be an object")
        supports = row.get("supports")
        if not isinstance(supports, list) or not supports:
            raise ValueError("supports must be a non-empty list")
        result.append(
            ObservationWorld(
                world_id=str(row["world_id"]),
                supports=tuple(
                    ObservationSupport(
                        channel_id=str(item["channel_id"]),
                        ecological_state=str(item["ecological_state"]),
                        possible_outcomes=tuple(
                            str(value) for value in item["possible_outcomes"]
                        ),
                    )
                    for item in supports
                ),
            )
        )
    return tuple(result)


def _parse_evidence_events(payload: dict[str, Any]) -> tuple[EvidenceEvent, ...]:
    rows = payload.get("evidence_events", [])
    if not isinstance(rows, list):
        raise ValueError("evidence_events must be a list")
    return tuple(
        EvidenceEvent(
            target_id=str(row["target_id"]),
            channel_id=str(row["channel_id"]),
            observed_outcome=str(row["observed_outcome"]),
        )
        for row in rows
    )


def _evaluation_payload(result) -> dict[str, Any]:
    return {
        "schema": "eog.v3.joint_evaluation.v1",
        "declared_ecological_world_ids": list(
            result.declared_ecological_world_ids
        ),
        "declared_observation_world_ids": list(
            result.declared_observation_world_ids
        ),
        "evidence_events": [
            {
                "target_id": event.target_id,
                "channel_id": event.channel_id,
                "observed_outcome": event.observed_outcome,
            }
            for event in result.evidence_events
        ],
        "surviving_joint_world_ids": list(result.surviving_joint_world_ids),
        "ecological_projection": list(result.ecological_projection),
        "observation_projection": list(result.observation_projection),
        "universe_falsified": result.universe_falsified,
        "coverage_certificate": result.coverage_certificate,
        "fingerprint": result.fingerprint,
    }


def joint_evaluate_main() -> int:
    parser = argparse.ArgumentParser(prog="eog-v3-joint-evaluate")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        payload = _load_json(args.input)
        result = evaluate_joint_worlds(
            _parse_ecological_worlds(payload),
            _parse_observation_worlds(payload),
            _parse_evidence_events(payload),
        )
        output = _evaluation_payload(result)
        _write_json(args.output, output, force=args.force)
    except (KeyError, TypeError, ValueError, FileExistsError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "joint_survivors": len(result.surviving_members),
                "ecological_survivors": len(result.ecological_projection),
                "observation_survivors": len(result.observation_projection),
                "universe_falsified": result.universe_falsified,
                "fingerprint": result.fingerprint,
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


def _parse_action_supports(
    payload: dict[str, Any],
) -> dict[str, dict[str, tuple[str, ...]]]:
    rows = payload.get("action_supports")
    if not isinstance(rows, dict) or not rows:
        raise ValueError("action_supports must be a non-empty object")
    result: dict[str, dict[str, tuple[str, ...]]] = {}
    for action_id, mapping in rows.items():
        if not isinstance(mapping, dict) or not mapping:
            raise ValueError(
                f"action_supports[{action_id!r}] must be a non-empty object"
            )
        result[str(action_id)] = {
            str(joint_id): tuple(str(value) for value in outcomes)
            for joint_id, outcomes in mapping.items()
        }
    return result


def plan_evidence_main() -> int:
    parser = argparse.ArgumentParser(prog="eog-v3-plan-evidence")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--objective",
        choices=("joint", "ecological"),
        required=True,
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        payload = _load_json(args.input)
        evaluation = evaluate_joint_worlds(
            _parse_ecological_worlds(payload),
            _parse_observation_worlds(payload),
            _parse_evidence_events(payload),
        )
        plan = plan_next_evidence_action(
            evaluation,
            _parse_action_supports(payload),
            objective=args.objective,
        )
        output = {
            "schema": "eog.v3.evidence_plan.v1",
            "evaluation_fingerprint": evaluation.fingerprint,
            "objective": plan.objective,
            "current_objective_value": plan.current_objective_value,
            "rankings": [
                {
                    "action_id": row.action_id,
                    "guaranteed_joint_pair_splits": row.guaranteed_joint_pair_splits,
                    "worst_case_joint_survivors": row.worst_case_joint_survivors,
                    "worst_case_ecological_survivors": (
                        row.worst_case_ecological_survivors
                    ),
                    "possible_outcomes": list(row.possible_outcomes),
                }
                for row in plan.rankings
            ],
            "best_action_ids": list(plan.best_action_ids),
            "fail_closed_no_improvement": plan.fail_closed_no_improvement,
            "fingerprint": plan.fingerprint,
        }
        _write_json(args.output, output, force=args.force)
    except (KeyError, TypeError, ValueError, FileExistsError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "objective": plan.objective,
                "best_action_ids": list(plan.best_action_ids),
                "fail_closed_no_improvement": plan.fail_closed_no_improvement,
                "fingerprint": plan.fingerprint,
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


__all__ = ["joint_evaluate_main", "plan_evidence_main", "plan_adaptive_main"]


def plan_adaptive_main() -> int:
    parser = argparse.ArgumentParser(prog="eog-v3-plan-adaptive")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        payload = _load_json(args.input)
        evaluation = evaluate_joint_worlds(
            _parse_ecological_worlds(payload),
            _parse_observation_worlds(payload),
            _parse_evidence_events(payload),
        )
        action_supports = _parse_action_supports(payload)
        robust = plan_robust_evidence_set(evaluation, action_supports)
        adaptive = solve_adaptive_evidence_policy(evaluation, action_supports)
        forced_first = {
            action_id: adaptive_forced_first_depth(
                evaluation,
                action_supports,
                action_id,
            )
            for action_id in sorted(action_supports)
        }
        output = {
            "schema": "eog.v3.adaptive_evidence_plan.v1",
            "evaluation_fingerprint": evaluation.fingerprint,
            "active_joint_world_ids": list(evaluation.surviving_joint_world_ids),
            "minimum_robust_separating_set": (
                None
                if robust.minimum_robust_separating_set is None
                else list(robust.minimum_robust_separating_set)
            ),
            "minimum_robust_set_size": robust.minimum_robust_set_size,
            "all_pairs_robustly_separated": robust.all_pairs_robustly_separated,
            "insufficient_action_library": robust.insufficient_action_library,
            "adaptive_resolvable": adaptive.resolvable,
            "adaptive_worst_case_depth": adaptive.worst_case_depth,
            "adaptive_optimal_first_actions": list(
                adaptive.optimal_first_actions
            ),
            "adaptive_canonical_first_action": (
                adaptive.canonical_first_action
            ),
            "forced_first_action_depths": forced_first,
            "robust_plan_fingerprint": robust.fingerprint,
            "adaptive_policy_fingerprint": adaptive.fingerprint,
        }
        _write_json(args.output, output, force=args.force)
    except (KeyError, TypeError, ValueError, FileExistsError) as exc:
        parser.error(str(exc))

    print(
        json.dumps(
            {
                "minimum_robust_set_size": robust.minimum_robust_set_size,
                "adaptive_resolvable": adaptive.resolvable,
                "adaptive_worst_case_depth": adaptive.worst_case_depth,
                "adaptive_optimal_first_actions": list(
                    adaptive.optimal_first_actions
                ),
                "output": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0
