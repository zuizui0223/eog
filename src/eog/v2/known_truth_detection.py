"""Known-truth observation-process boundary for exact EOG falsification.

This module separates ecological state from observation process.  Hard falsification
is permitted only when the observed history has exact probability zero under every
admissible observation world.

No arbitrary likelihood threshold is converted into impossibility.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Sequence


BiologicalState = Literal["present", "absent"]


def _sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ObservationWorld:
    world_id: str
    detection_probability: float
    false_positive_probability: float

    def __post_init__(self) -> None:
        if not self.world_id.strip():
            raise ValueError("world_id must be non-empty")
        for label, value in (
            ("detection_probability", self.detection_probability),
            ("false_positive_probability", self.false_positive_probability),
        ):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must lie in [0,1]")


def observation_history_probability(
    state: BiologicalState,
    *,
    detections: int,
    surveys: int,
    observation_world: ObservationWorld,
) -> float:
    """Binomial probability for an unordered detection count."""

    if isinstance(surveys, bool) or not isinstance(surveys, int) or surveys < 1:
        raise ValueError("surveys must be a positive integer")
    if isinstance(detections, bool) or not isinstance(detections, int):
        raise ValueError("detections must be an integer")
    if detections < 0 or detections > surveys:
        raise ValueError("detections must lie in [0, surveys]")

    probability = (
        observation_world.detection_probability
        if state == "present"
        else observation_world.false_positive_probability
    )
    return float(
        math.comb(surveys, detections)
        * probability**detections
        * (1.0 - probability) ** (surveys - detections)
    )


def state_possible(
    state: BiologicalState,
    *,
    detections: int,
    surveys: int,
    observation_world: ObservationWorld,
) -> bool:
    return (
        observation_history_probability(
            state,
            detections=detections,
            surveys=surveys,
            observation_world=observation_world,
        )
        > 0.0
    )


def robust_state_possible(
    state: BiologicalState,
    *,
    detections: int,
    surveys: int,
    observation_worlds: Sequence[ObservationWorld],
) -> bool:
    """Whether at least one admissible observation world keeps the state possible."""

    worlds = tuple(observation_worlds)
    if not worlds:
        raise ValueError("at least one observation world is required")
    return any(
        state_possible(
            state,
            detections=detections,
            surveys=surveys,
            observation_world=world,
        )
        for world in worlds
    )


def robustly_falsified_states(
    *,
    detections: int,
    surveys: int,
    observation_worlds: Sequence[ObservationWorld],
) -> tuple[BiologicalState, ...]:
    rows: list[BiologicalState] = []
    for state in ("present", "absent"):
        if not robust_state_possible(
            state,
            detections=detections,
            surveys=surveys,
            observation_worlds=observation_worlds,
        ):
            rows.append(state)
    return tuple(rows)


def run_detection_boundary_v26() -> dict[str, object]:
    ps = (0.25, 0.5, 0.75, 1.0)
    qs = (0.0, 0.01)
    ns = (1, 2, 4, 8)

    probability_rows: list[dict[str, object]] = []
    o1_failures = 0
    o2_failures = 0
    o3_failures = 0
    o4_failures = 0
    o5_failures = 0

    for p in ps:
        values = []
        world = ObservationWorld(
            world_id=f"p{p:.2f}_q0",
            detection_probability=p,
            false_positive_probability=0.0,
        )
        for n in ns:
            prob = observation_history_probability(
                "present",
                detections=0,
                surveys=n,
                observation_world=world,
            )
            values.append(prob)
            probability_rows.append(
                {
                    "p": p,
                    "q": 0.0,
                    "surveys": n,
                    "detections": 0,
                    "present_probability": prob,
                    "present_possible": prob > 0.0,
                }
            )
            if p < 1.0 and prob <= 0.0:
                o1_failures += 1
            if p == 1.0 and prob != 0.0:
                o2_failures += 1

        if p < 1.0:
            for earlier, later in zip(values, values[1:]):
                if later > earlier + 1e-15 or later <= 0.0:
                    o3_failures += 1

    # O4: one positive detection in one survey.
    strict_positive_worlds = (
        ObservationWorld("strict_p50_q0", 0.5, 0.0),
        ObservationWorld("strict_p100_q0", 1.0, 0.0),
    )
    broad_positive_worlds = (
        *strict_positive_worlds,
        ObservationWorld("fp_allowed_p50_q001", 0.5, 0.01),
    )
    strict_falsified = robustly_falsified_states(
        detections=1,
        surveys=1,
        observation_worlds=strict_positive_worlds,
    )
    broad_falsified = robustly_falsified_states(
        detections=1,
        surveys=1,
        observation_worlds=broad_positive_worlds,
    )
    if "absent" not in strict_falsified:
        o4_failures += 1
    if "absent" in broad_falsified:
        o4_failures += 1

    # O5: finite observation-world expansion can only weaken robust exclusion.
    strict_negative_worlds = (
        ObservationWorld("perfect", 1.0, 0.0),
    )
    expanded_negative_worlds = (
        ObservationWorld("perfect", 1.0, 0.0),
        ObservationWorld("imperfect", 0.75, 0.0),
    )
    strict_negative = set(
        robustly_falsified_states(
            detections=0,
            surveys=4,
            observation_worlds=strict_negative_worlds,
        )
    )
    expanded_negative = set(
        robustly_falsified_states(
            detections=0,
            surveys=4,
            observation_worlds=expanded_negative_worlds,
        )
    )
    if not expanded_negative.issubset(strict_negative):
        o5_failures += 1

    # Exhaustive expansion audit over nested finite p/q sets.
    world_grid = [
        ObservationWorld(f"p{p:.2f}_q{q:.2f}", p, q)
        for p in ps
        for q in qs
    ]
    for detections in (0, 1):
        for surveys in ns:
            if detections > surveys:
                continue
            for cut in range(1, len(world_grid)):
                smaller = world_grid[:cut]
                larger = world_grid[: cut + 1]
                small_falsified = set(
                    robustly_falsified_states(
                        detections=detections,
                        surveys=surveys,
                        observation_worlds=smaller,
                    )
                )
                large_falsified = set(
                    robustly_falsified_states(
                        detections=detections,
                        surveys=surveys,
                        observation_worlds=larger,
                    )
                )
                if not large_falsified.issubset(small_falsified):
                    o5_failures += 1

    hard_negative_cases = []
    hard_positive_cases = []
    for p in ps:
        for q in qs:
            world = ObservationWorld(
                f"p{p:.2f}_q{q:.2f}",
                detection_probability=p,
                false_positive_probability=q,
            )
            for n in ns:
                neg = robustly_falsified_states(
                    detections=0,
                    surveys=n,
                    observation_worlds=(world,),
                )
                pos = robustly_falsified_states(
                    detections=1,
                    surveys=n,
                    observation_worlds=(world,),
                )
                if neg:
                    hard_negative_cases.append(
                        {"p": p, "q": q, "n": n, "falsified_states": list(neg)}
                    )
                if pos:
                    hard_positive_cases.append(
                        {"p": p, "q": q, "n": n, "falsified_states": list(pos)}
                    )

    verdicts = {
        "O1_imperfect_nondetection_not_hard_absence": (
            "SUPPORTED" if o1_failures == 0 else "REFUTED"
        ),
        "O2_perfect_detection_hard_negative": (
            "SUPPORTED" if o2_failures == 0 else "REFUTED"
        ),
        "O3_more_nondetections_change_weight_not_possibility": (
            "SUPPORTED" if o3_failures == 0 else "REFUTED"
        ),
        "O4_false_positive_breaks_hard_positive": (
            "SUPPORTED" if o4_failures == 0 else "REFUTED"
        ),
        "O5_observation_world_expansion_weakens_or_preserves_falsification": (
            "SUPPORTED" if o5_failures == 0 else "REFUTED"
        ),
    }

    result: dict[str, object] = {
        "schema": "eog.known_truth_observation_process.result.v2_6",
        "p_values": list(ps),
        "q_values": list(qs),
        "survey_counts": list(ns),
        "all_zero_probability_rows": probability_rows,
        "hard_negative_cases": hard_negative_cases,
        "hard_positive_cases": hard_positive_cases,
        "strict_positive_falsified_states": list(strict_falsified),
        "expanded_positive_falsified_states": list(broad_falsified),
        "strict_negative_falsified_states": sorted(strict_negative),
        "expanded_negative_falsified_states": sorted(expanded_negative),
        "failure_counts": {
            "O1": o1_failures,
            "O2": o2_failures,
            "O3": o3_failures,
            "O4": o4_failures,
            "O5": o5_failures,
        },
        "verdicts": verdicts,
    }
    result["fingerprint"] = _sha256(result)
    return result
