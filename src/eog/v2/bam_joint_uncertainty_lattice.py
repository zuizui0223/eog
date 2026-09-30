"""Joint ecological-world and assay-observation uncertainty for future BAM targets.

Phase IX combines only previously frozen components:
- W0 original 64-world BAM family;
- W1 2,592-world ecological expansion lattice;
- O0 calibrated assay process;
- O1 calibrated + systematically miscalibrated assay processes;
- the three structured future binary targets;
- the eight parameter assays plus assay-process calibration.

The inferential target remains the future ecological decision. Ecological-world and
observation-world identities are nuisance unless they must be distinguished to identify
that target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Mapping, Sequence

from .bam_ecological_expansion_margin import (
    ExpandedBAMVariant,
    declared_world_coordinates,
)
from .bam_future_assay_observation import (
    JointAssayHypothesis,
    build_action_supports,
    exact_minimum_deterministic_target_design,
)
from .known_truth_bam_generality import GeneralitySystem


O0 = ("calibrated",)
O1 = ("calibrated", "systematically_miscalibrated")


@dataclass(frozen=True)
class JointUniverseBurden:
    ecological_universe: str
    observation_universe: str
    ecological_world_count: int
    joint_hypothesis_count: int
    target_class_count: int
    minimum_size: int | None
    minimum_action_ids: tuple[str, ...] | None
    sufficient: bool
    no_calibration_minimum_size: int | None
    calibration_required_for_minimum: bool


def build_joint_hypotheses_for_observation_universe(
    variants: Sequence[ExpandedBAMVariant],
    target_by_ecological_world: Mapping[str, Hashable],
    observation_world_ids: Sequence[str],
) -> tuple[JointAssayHypothesis, ...]:
    rows = tuple(variants)
    if not rows:
        raise ValueError("variants must be non-empty")
    obs_ids = tuple(sorted(set(str(value) for value in observation_world_ids)))
    if not obs_ids:
        raise ValueError("observation_world_ids must be non-empty")
    allowed = {"calibrated", "systematically_miscalibrated"}
    unknown = set(obs_ids).difference(allowed)
    if unknown:
        raise ValueError(f"unknown observation worlds: {sorted(unknown)}")

    ids = [row.variant_id for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("variant IDs must be unique")
    missing = set(ids).difference(target_by_ecological_world)
    if missing:
        raise ValueError(f"target mapping missing variants: {sorted(missing)}")

    return tuple(
        sorted(
            (
                JointAssayHypothesis(
                    ecological_world_id=row.variant_id,
                    observation_world_id=obs_id,
                    future_target=target_by_ecological_world[row.variant_id],
                )
                for row in rows
                for obs_id in obs_ids
            ),
            key=lambda row: row.joint_id,
        )
    )


def embedded_w0_same_g_variants(
    system: GeneralitySystem,
    lattice: Sequence[ExpandedBAMVariant],
    current_G: int,
) -> tuple[ExpandedBAMVariant, ...]:
    by_coords = {row.coordinates: row for row in lattice}
    if len(by_coords) != len(lattice):
        raise ValueError("expanded lattice coordinates must be unique")

    rows: list[ExpandedBAMVariant] = []
    for world in system.worlds:
        if int(world.occupied_mask) != int(current_G):
            continue
        coords = declared_world_coordinates(system, world)
        try:
            variant = by_coords[coords]
        except KeyError as exc:
            raise RuntimeError(
                f"declared world coordinates missing from W1 lattice: {world.world_id}"
            ) from exc
        if int(variant.occupied_mask) != int(current_G):
            raise RuntimeError("embedded W0 variant does not preserve current G")
        rows.append(variant)

    if not rows:
        raise ValueError("no W0 worlds share requested current G")
    return tuple(sorted(rows, key=lambda row: row.variant_id))


def same_g_w1_variants(
    lattice: Sequence[ExpandedBAMVariant],
    current_G: int,
) -> tuple[ExpandedBAMVariant, ...]:
    rows = tuple(
        sorted(
            (
                row
                for row in lattice
                if int(row.occupied_mask) == int(current_G)
            ),
            key=lambda row: row.variant_id,
        )
    )
    if not rows:
        raise ValueError("no W1 variants share requested current G")
    return rows


def exact_joint_target_burden(
    variants: Sequence[ExpandedBAMVariant],
    target_by_ecological_world: Mapping[str, Hashable],
    observation_world_ids: Sequence[str],
    *,
    ecological_universe: str,
    observation_universe: str,
    available_action_ids: Sequence[str],
) -> JointUniverseBurden:
    rows = tuple(variants)
    hypotheses = build_joint_hypotheses_for_observation_universe(
        rows,
        target_by_ecological_world,
        observation_world_ids,
    )
    actions = build_action_supports(rows, hypotheses)

    full = exact_minimum_deterministic_target_design(
        hypotheses,
        actions,
        available_action_ids=available_action_ids,
    )

    no_calibration_ids = tuple(
        action_id
        for action_id in available_action_ids
        if action_id != "assay_process_calibration"
    )
    no_calibration = exact_minimum_deterministic_target_design(
        hypotheses,
        actions,
        available_action_ids=no_calibration_ids,
    )

    requires_calibration = False
    if full.minimum_size is not None:
        if no_calibration.minimum_size is None:
            requires_calibration = True
        elif no_calibration.minimum_size > full.minimum_size:
            requires_calibration = True

    target_class_count = len(
        {
            target_by_ecological_world[row.variant_id]
            for row in rows
        }
    )
    return JointUniverseBurden(
        ecological_universe=ecological_universe,
        observation_universe=observation_universe,
        ecological_world_count=len(rows),
        joint_hypothesis_count=len(hypotheses),
        target_class_count=target_class_count,
        minimum_size=full.minimum_size,
        minimum_action_ids=full.minimum_action_ids,
        sufficient=full.all_target_pairs_separated,
        no_calibration_minimum_size=no_calibration.minimum_size,
        calibration_required_for_minimum=requires_calibration,
    )


def burden_order_value(value: int | None) -> float:
    return float("inf") if value is None else float(value)


def joint_burden_monotonicity_violations(
    burdens: Mapping[str, JointUniverseBurden],
) -> tuple[str, ...]:
    required = {"W0O0", "W0O1", "W1O0", "W1O1"}
    missing = required.difference(burdens)
    if missing:
        raise ValueError(f"missing joint burden levels: {sorted(missing)}")

    b00 = burden_order_value(burdens["W0O0"].minimum_size)
    b01 = burden_order_value(burdens["W0O1"].minimum_size)
    b10 = burden_order_value(burdens["W1O0"].minimum_size)
    b11 = burden_order_value(burdens["W1O1"].minimum_size)

    violations = []
    if b00 > b01:
        violations.append("W0O0<=W0O1")
    if b01 > b11:
        violations.append("W0O1<=W1O1")
    if b00 > b10:
        violations.append("W0O0<=W1O0")
    if b10 > b11:
        violations.append("W1O0<=W1O1")
    return tuple(violations)


def strict_joint_interaction(
    burdens: Mapping[str, JointUniverseBurden],
) -> bool:
    b01 = burden_order_value(burdens["W0O1"].minimum_size)
    b10 = burden_order_value(burdens["W1O0"].minimum_size)
    b11 = burden_order_value(burdens["W1O1"].minimum_size)
    if b11 == float("inf"):
        return b01 < float("inf") or b10 < float("inf")
    return b11 > max(b01, b10)


def ecological_expansion_creates_calibration_need(
    burdens: Mapping[str, JointUniverseBurden],
) -> bool:
    w0 = burdens["W0O1"]
    w1 = burdens["W1O1"]
    w0_no_cal = burden_order_value(w0.no_calibration_minimum_size)
    w1_full = burden_order_value(w1.minimum_size)
    w1_no_cal = burden_order_value(w1.no_calibration_minimum_size)

    w0_solvable_without_calibration = w0_no_cal < float("inf")
    w1_every_minimum_requires_calibration = (
        w1_full < float("inf") and w1_no_cal > w1_full
    )
    return w0_solvable_without_calibration and w1_every_minimum_requires_calibration
