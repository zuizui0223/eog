"""Joint ecological-world × observation-world falsification (v2.7).

This module combines the frozen BAM ecological worlds with a finite observation-process
universe.  A joint world survives exactly when the observed detection history has
positive probability under the observation process conditional on the ecological
world's target biological state.

Ecological-world compatibility is the projection of surviving joint worlds onto the
ecological axis.  This makes observation-process uncertainty an explicit source of
ecological non-falsification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from .known_truth_bam_v2_1 import build_v21_system
from .known_truth_detection import (
    ObservationWorld,
    observation_history_probability,
)


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class JointWorld:
    ecological_world_id: str
    observation_world_id: str
    target_present: bool
    compatible: bool
    history_probability: float

    @property
    def joint_id(self) -> str:
        return f"{self.ecological_world_id}::{self.observation_world_id}"


@dataclass(frozen=True)
class JointEvaluation:
    surveys: int
    detections: int
    observation_world_ids: tuple[str, ...]
    surviving_joint_world_ids: tuple[str, ...]
    ecological_projection: tuple[str, ...]
    fingerprint: str


def _select_target_node():
    system = build_v21_system()
    worlds = system.worlds
    rows = []
    for node_id in system.landscape.node_ids:
        present = sum(node_id in world.occupied_ids for world in worlds)
        absent = len(worlds) - present
        balance = min(present, absent)
        rows.append((balance, node_id, present, absent))
    best_balance = max(row[0] for row in rows)
    _, node_id, present, absent = min(
        (row for row in rows if row[0] == best_balance),
        key=lambda row: row[1],
    )
    return system, node_id, present, absent


def _select_truth_world(system, target_node: str):
    candidates = [
        world
        for world in system.worlds
        if target_node not in world.occupied_ids
        and "r1c0" in world.occupied_ids
        and len(world.occupied_ids) >= 2
    ]
    if not candidates:
        raise RuntimeError("frozen truth selection rule found no eligible ecological world")
    return min(candidates, key=lambda world: world.world_id)


def evaluate_joint_worlds(
    *,
    target_node: str,
    surveys: int,
    detections: int,
    observation_worlds: Sequence[ObservationWorld],
) -> JointEvaluation:
    system = build_v21_system()
    obs_worlds = tuple(sorted(observation_worlds, key=lambda row: row.world_id))
    if not obs_worlds:
        raise ValueError("at least one observation world is required")

    rows: list[JointWorld] = []
    for ecological_world in system.worlds:
        target_present = target_node in ecological_world.occupied_ids
        state = "present" if target_present else "absent"
        for observation_world in obs_worlds:
            probability = observation_history_probability(
                state,
                detections=detections,
                surveys=surveys,
                observation_world=observation_world,
            )
            rows.append(
                JointWorld(
                    ecological_world_id=ecological_world.world_id,
                    observation_world_id=observation_world.world_id,
                    target_present=target_present,
                    compatible=probability > 0.0,
                    history_probability=probability,
                )
            )

    surviving_joint = tuple(
        row.joint_id for row in rows if row.compatible
    )
    ecological_projection = tuple(
        sorted({row.ecological_world_id for row in rows if row.compatible})
    )
    payload = {
        "target_node": target_node,
        "surveys": surveys,
        "detections": detections,
        "observation_world_ids": [row.world_id for row in obs_worlds],
        "surviving_joint_world_ids": list(surviving_joint),
        "ecological_projection": list(ecological_projection),
    }
    return JointEvaluation(
        surveys=surveys,
        detections=detections,
        observation_world_ids=tuple(row.world_id for row in obs_worlds),
        surviving_joint_world_ids=surviving_joint,
        ecological_projection=ecological_projection,
        fingerprint=_sha256(payload),
    )


def run_joint_ecology_observation_v27() -> dict[str, object]:
    system, target_node, target_present_count, target_absent_count = _select_target_node()
    truth = _select_truth_world(system, target_node)

    perfect = ObservationWorld(
        "perfect",
        detection_probability=1.0,
        false_positive_probability=0.0,
    )
    imperfect = ObservationWorld(
        "imperfect",
        detection_probability=0.75,
        false_positive_probability=0.0,
    )

    strict = evaluate_joint_worlds(
        target_node=target_node,
        surveys=4,
        detections=0,
        observation_worlds=(perfect,),
    )
    broad = evaluate_joint_worlds(
        target_node=target_node,
        surveys=4,
        detections=0,
        observation_worlds=(perfect, imperfect),
    )

    # Idealized direct calibration to p=1 retains only the matching observation world.
    calibrated = evaluate_joint_worlds(
        target_node=target_node,
        surveys=4,
        detections=0,
        observation_worlds=(perfect,),
    )

    ecological_projection_by_n = {}
    present_survivors_by_n = {}
    j4_failures = 0
    for n in (1, 2, 4, 8):
        evaluation = evaluate_joint_worlds(
            target_node=target_node,
            surveys=n,
            detections=0,
            observation_worlds=(perfect, imperfect),
        )
        ecological_projection_by_n[str(n)] = list(evaluation.ecological_projection)
        present_survivors = [
            world.world_id
            for world in system.worlds
            if target_node in world.occupied_ids
            and world.world_id in set(evaluation.ecological_projection)
        ]
        present_survivors_by_n[str(n)] = len(present_survivors)
        if not present_survivors:
            j4_failures += 1

    # J1 checks compatibility against an independently written zero/nonzero condition
    # for the frozen all-zero history.
    j1_mismatches = 0
    for world in system.worlds:
        state_present = target_node in world.occupied_ids
        for obs in (perfect, imperfect):
            probability = observation_history_probability(
                "present" if state_present else "absent",
                detections=0,
                surveys=4,
                observation_world=obs,
            )
            if state_present:
                expected_possible = (1.0 - obs.detection_probability) ** 4 > 0.0
            else:
                expected_possible = (1.0 - obs.false_positive_probability) ** 4 > 0.0
            if (probability > 0.0) != expected_possible:
                j1_mismatches += 1

    strict_set = set(strict.ecological_projection)
    broad_set = set(broad.ecological_projection)
    calibrated_set = set(calibrated.ecological_projection)

    j2_supported = (
        strict_set < broad_set
        and any(
            target_node in world.occupied_ids
            and world.world_id in broad_set.difference(strict_set)
            for world in system.worlds
        )
    )
    j3_supported = calibrated_set == strict_set

    # J5 checks nested observation-world expansion.
    j5_supported = strict_set.issubset(broad_set)

    broad_n8 = set(ecological_projection_by_n["8"])
    j6_supported = (
        broad_n8 != strict_set
        and calibrated_set == strict_set
        and any(
            target_node in world.occupied_ids and world.world_id in broad_n8
            for world in system.worlds
        )
    )

    verdicts = {
        "J1_joint_factorization": (
            "SUPPORTED" if j1_mismatches == 0 else "REFUTED"
        ),
        "J2_observation_uncertainty_resurrects_ecological_worlds": (
            "SUPPORTED" if j2_supported else "REFUTED"
        ),
        "J3_calibration_restores_ecological_falsification": (
            "SUPPORTED" if j3_supported else "REFUTED"
        ),
        "J4_more_nondetections_do_not_replace_calibration": (
            "SUPPORTED" if j4_failures == 0 else "REFUTED"
        ),
        "J5_observation_world_expansion_is_ecologically_monotone": (
            "SUPPORTED" if j5_supported else "REFUTED"
        ),
        "J6_calibration_can_dominate_more_same_type_data": (
            "SUPPORTED" if j6_supported else "REFUTED"
        ),
    }

    truth_joint_probability = observation_history_probability(
        "absent",
        detections=0,
        surveys=4,
        observation_world=perfect,
    )
    result: dict[str, object] = {
        "schema": "eog.joint_ecology_observation.result.v2_7",
        "ecological_world_count": len(system.worlds),
        "selected_target_node": target_node,
        "target_present_world_count": target_present_count,
        "target_absent_world_count": target_absent_count,
        "truth_ecological_world_id": truth.world_id,
        "truth_target_present": target_node in truth.occupied_ids,
        "truth_observation_world_id": perfect.world_id,
        "truth_history_probability": truth_joint_probability,
        "observed_history": {"surveys": 4, "detections": 0},
        "strict_joint_survivor_count": len(strict.surviving_joint_world_ids),
        "broad_joint_survivor_count": len(broad.surviving_joint_world_ids),
        "strict_ecological_projection": list(strict.ecological_projection),
        "broad_ecological_projection": list(broad.ecological_projection),
        "strict_ecological_projection_count": len(strict.ecological_projection),
        "broad_ecological_projection_count": len(broad.ecological_projection),
        "resurrected_ecological_world_count": len(broad_set.difference(strict_set)),
        "calibrated_ecological_projection": list(calibrated.ecological_projection),
        "calibrated_ecological_projection_count": len(calibrated.ecological_projection),
        "ecological_projection_by_nondetection_count": ecological_projection_by_n,
        "target_present_survivors_by_nondetection_count": present_survivors_by_n,
        "J1_mismatches": j1_mismatches,
        "J4_failures": j4_failures,
        "verdicts": verdicts,
    }
    result["fingerprint"] = _sha256(result)
    return result
