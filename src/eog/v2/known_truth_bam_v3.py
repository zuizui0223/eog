"""Truth-blind active intervention design for known-truth BAM v3."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Hashable, Sequence

from .known_truth_bam import (
    BAMWorld,
    compatible_positive_only,
    compatible_with_perfect_negatives,
    compatible_with_temporal_arrivals,
)
from .known_truth_bam_v2_2 import build_world_grid_v22
from .known_truth_bam_v2_1 import make_bam_v21_landscape


@dataclass(frozen=True)
class BAMIntervention:
    intervention_id: str
    axis: str
    target_node_id: str | None = None

    @property
    def key(self) -> str:
        return (
            self.intervention_id
            if self.target_node_id is None
            else f"{self.intervention_id}:{self.target_node_id}"
        )


@dataclass(frozen=True)
class ActiveInterventionStep:
    step: int
    intervention_key: str
    entropy: float
    observed_outcome: str
    before_world_ids: tuple[str, ...]
    after_world_ids: tuple[str, ...]


def intervention_library(node_ids: Sequence[str], source_id: str = "r1c0") -> tuple[BAMIntervention, ...]:
    rows = [
        BAMIntervention("A_transplant_challenge", "A"),
        BAMIntervention("B_partner_removal", "B_partner"),
        BAMIntervention("B_antagonist_addition", "B_antagonist"),
    ]
    rows.extend(
        BAMIntervention("M_arrival_probe", "M", node_id)
        for node_id in node_ids
        if node_id != source_id
    )
    return tuple(sorted(rows, key=lambda item: item.key))


def predicted_intervention_outcome(world: BAMWorld, intervention: BAMIntervention) -> str:
    if intervention.intervention_id == "A_transplant_challenge":
        return "survive" if world.abiotic_label == "A_broad" else "fail"
    if intervention.intervention_id == "B_partner_removal":
        requires_partner = world.biotic_mode in (
            "obligate_partner",
            "partner_and_antagonist",
        )
        return "fail" if requires_partner else "persist"
    if intervention.intervention_id == "B_antagonist_addition":
        excludes_antagonist = world.biotic_mode in (
            "antagonist_exclusion",
            "partner_and_antagonist",
        )
        return "fail" if excludes_antagonist else "persist"
    if intervention.intervention_id == "M_arrival_probe":
        if intervention.target_node_id is None:
            raise ValueError("movement probe requires target node")
        idx = world.node_ids.index(intervention.target_node_id)
        step = world.first_arrival_steps[idx]
        return "unreachable" if step is None else f"step_{step}"
    raise ValueError(f"unknown intervention: {intervention.intervention_id}")


def _partition_entropy(worlds: Sequence[BAMWorld], intervention: BAMIntervention) -> float:
    counts = Counter(predicted_intervention_outcome(world, intervention) for world in worlds)
    n = len(worlds)
    if n <= 1 or len(counts) <= 1:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        p = count / n
        entropy -= p * math.log2(p)
    return entropy


def complete_intervention_signature(world: BAMWorld, library: Sequence[BAMIntervention]) -> tuple[str, ...]:
    return tuple(predicted_intervention_outcome(world, intervention) for intervention in library)


def _passive_state(worlds: Sequence[BAMWorld], truth: BAMWorld) -> tuple[str, ...]:
    landscape = make_bam_v21_landscape()
    positives = truth.occupied_ids
    negatives = tuple(
        node_id for node_id in landscape.node_ids if node_id not in set(positives)
    )
    temporal_obs = {
        node_id: int(truth.first_arrival_steps[idx])
        for idx, node_id in enumerate(truth.node_ids)
        if node_id in set(positives) and truth.first_arrival_steps[idx] is not None
    }
    positive = compatible_positive_only(worlds, positives)
    negative = compatible_with_perfect_negatives(worlds, positives, negatives)
    temporal = compatible_with_temporal_arrivals(
        worlds,
        positives,
        negatives,
        temporal_obs,
    )
    if not set(temporal.compatible_world_ids).issubset(negative.compatible_world_ids):
        raise RuntimeError("temporal evidence expanded passive compatible set")
    if not set(negative.compatible_world_ids).issubset(positive.compatible_world_ids):
        raise RuntimeError("negative evidence expanded positive compatible set")
    return temporal.compatible_world_ids


def select_next_intervention(
    current_worlds: Sequence[BAMWorld],
    available: Sequence[BAMIntervention],
) -> tuple[BAMIntervention | None, float]:
    scored = [
        (_partition_entropy(current_worlds, intervention), intervention.key, intervention)
        for intervention in available
    ]
    informative = [row for row in scored if row[0] > 0.0]
    if not informative:
        return None, 0.0
    entropy, _, chosen = max(informative, key=lambda row: (row[0], tuple(-ord(c) for c in row[1])))
    # The max expression above reverses lexicographic order, so resolve ties explicitly.
    best_entropy = entropy
    tied = sorted(
        (intervention for value, _, intervention in informative if abs(value - best_entropy) <= 1e-15),
        key=lambda intervention: intervention.key,
    )
    return tied[0], best_entropy


def run_active_intervention_for_truth(
    worlds: Sequence[BAMWorld],
    truth: BAMWorld,
) -> tuple[tuple[str, ...], tuple[ActiveInterventionStep, ...], tuple[str, ...]]:
    by_id = {world.world_id: world for world in worlds}
    current_ids = _passive_state(worlds, truth)
    if truth.world_id not in current_ids:
        raise RuntimeError("truth missing before intervention")
    library = list(intervention_library(truth.node_ids))
    steps: list[ActiveInterventionStep] = []

    while len(current_ids) > 1:
        current_worlds = tuple(by_id[world_id] for world_id in current_ids)
        intervention, entropy = select_next_intervention(current_worlds, library)
        if intervention is None:
            break
        observed = predicted_intervention_outcome(truth, intervention)
        after = tuple(
            world.world_id
            for world in current_worlds
            if predicted_intervention_outcome(world, intervention) == observed
        )
        if truth.world_id not in after:
            raise RuntimeError("correct intervention outcome eliminated truth")
        if len(after) > len(current_ids):
            raise RuntimeError("intervention expanded compatible set")
        steps.append(
            ActiveInterventionStep(
                step=len(steps) + 1,
                intervention_key=intervention.key,
                entropy=entropy,
                observed_outcome=observed,
                before_world_ids=current_ids,
                after_world_ids=after,
            )
        )
        current_ids = after
        library = [candidate for candidate in library if candidate.key != intervention.key]

    full_library = intervention_library(truth.node_ids)
    truth_signature = complete_intervention_signature(truth, full_library)
    signature_equivalent = tuple(
        world.world_id
        for world in worlds
        if world.world_id in _passive_state(worlds, truth)
        and complete_intervention_signature(world, full_library) == truth_signature
    )
    return current_ids, tuple(steps), signature_equivalent


def _axis_orthogonality_audit(worlds: Sequence[BAMWorld]) -> dict[str, bool]:
    library = intervention_library(worlds[0].node_ids)
    a_probe = next(i for i in library if i.intervention_id == "A_transplant_challenge")
    partner_probe = next(i for i in library if i.intervention_id == "B_partner_removal")
    antagonist_probe = next(i for i in library if i.intervention_id == "B_antagonist_addition")
    m_probes = tuple(i for i in library if i.intervention_id == "M_arrival_probe")

    a_ok = all(
        predicted_intervention_outcome(left, a_probe)
        == predicted_intervention_outcome(right, a_probe)
        for left in worlds
        for right in worlds
        if left.abiotic_label == right.abiotic_label
    )
    partner_ok = all(
        predicted_intervention_outcome(left, partner_probe)
        == predicted_intervention_outcome(right, partner_probe)
        for left in worlds
        for right in worlds
        if (
            left.biotic_mode in ("obligate_partner", "partner_and_antagonist")
        )
        == (
            right.biotic_mode in ("obligate_partner", "partner_and_antagonist")
        )
    )
    antagonist_ok = all(
        predicted_intervention_outcome(left, antagonist_probe)
        == predicted_intervention_outcome(right, antagonist_probe)
        for left in worlds
        for right in worlds
        if (
            left.biotic_mode in ("antagonist_exclusion", "partner_and_antagonist")
        )
        == (
            right.biotic_mode in ("antagonist_exclusion", "partner_and_antagonist")
        )
    )
    m_ok = all(
        all(
            predicted_intervention_outcome(left, probe)
            == predicted_intervention_outcome(right, probe)
            for probe in m_probes
        )
        for left in worlds
        for right in worlds
        if left.movement_label == right.movement_label
    )
    return {
        "A_probe_depends_only_on_A": a_ok,
        "partner_probe_depends_only_on_partner_bit": partner_ok,
        "antagonist_probe_depends_only_on_antagonist_bit": antagonist_ok,
        "M_probes_depend_only_on_M": m_ok,
    }


def run_bam_active_intervention_v3() -> dict[str, object]:
    worlds = build_world_grid_v22()
    axis_audit = _axis_orthogonality_audit(worlds)
    truth_retention_failures = 0
    monotonicity_failures = 0
    signature_limit_failures = 0
    unique_before = 0
    unique_after = 0
    step_counts: list[int] = []
    selected_frequency: Counter[str] = Counter()
    axis_first_frequency: Counter[str] = Counter()
    terminal_sizes: Counter[int] = Counter()
    rows: list[dict[str, object]] = []

    for truth in worlds:
        passive = _passive_state(worlds, truth)
        if len(passive) == 1:
            unique_before += 1
        terminal, steps, signature_equivalent = run_active_intervention_for_truth(worlds, truth)
        if truth.world_id not in terminal:
            truth_retention_failures += 1
        for step in steps:
            if len(step.after_world_ids) > len(step.before_world_ids):
                monotonicity_failures += 1
            selected_frequency[step.intervention_key] += 1
        if steps:
            first_key = steps[0].intervention_key
            if first_key.startswith("A_"):
                axis_first_frequency["A"] += 1
            elif first_key.startswith("B_partner"):
                axis_first_frequency["B_partner"] += 1
            elif first_key.startswith("B_antagonist"):
                axis_first_frequency["B_antagonist"] += 1
            else:
                axis_first_frequency["M"] += 1
        if terminal != signature_equivalent:
            signature_limit_failures += 1
        if len(terminal) == 1:
            unique_after += 1
        terminal_sizes[len(terminal)] += 1
        step_counts.append(len(steps))
        rows.append(
            {
                "truth_world_id": truth.world_id,
                "passive_world_count": len(passive),
                "terminal_world_count": len(terminal),
                "signature_equivalence_size": len(signature_equivalent),
                "intervention_count": len(steps),
                "selected_interventions": [step.intervention_key for step in steps],
            }
        )

    signatures: dict[tuple[str, ...], list[str]] = {}
    full_library = intervention_library(worlds[0].node_ids)
    for world in worlds:
        signatures.setdefault(
            complete_intervention_signature(world, full_library),
            [],
        ).append(world.world_id)
    distinct_signature_count = len(signatures)

    verdicts = {
        "I1_truth_retention": "SUPPORTED" if truth_retention_failures == 0 else "REFUTED",
        "I2_axis_orthogonality": (
            "SUPPORTED" if all(axis_audit.values()) else "REFUTED"
        ),
        "I3_monotone_contraction": (
            "SUPPORTED" if monotonicity_failures == 0 else "REFUTED"
        ),
        "I4_full_panel_identifiability": (
            "SUPPORTED" if distinct_signature_count == len(worlds) else "PARTIAL"
        ),
        "I5_active_design_matches_signature_limit": (
            "SUPPORTED" if signature_limit_failures == 0 else "REFUTED"
        ),
    }

    ordered_steps = sorted(step_counts)
    median_steps = (
        0.0
        if not ordered_steps
        else (
            float(ordered_steps[len(ordered_steps) // 2])
            if len(ordered_steps) % 2 == 1
            else 0.5 * (
                ordered_steps[len(ordered_steps) // 2 - 1]
                + ordered_steps[len(ordered_steps) // 2]
            )
        )
    )
    return {
        "schema": "eog.known_truth_bam.active_intervention_result.v3",
        "candidate_world_count": len(worlds),
        "distinct_complete_intervention_signatures": distinct_signature_count,
        "axis_orthogonality_audit": axis_audit,
        "truth_retention_failures": truth_retention_failures,
        "monotonicity_failures": monotonicity_failures,
        "signature_limit_failures": signature_limit_failures,
        "unique_truth_fraction_before_intervention": unique_before / len(worlds),
        "unique_truth_fraction_after_active_intervention": unique_after / len(worlds),
        "median_interventions_to_terminal": median_steps,
        "max_interventions_to_terminal": max(step_counts),
        "terminal_signature_equivalence_class_size_distribution": dict(
            sorted(terminal_sizes.items())
        ),
        "selected_intervention_frequency": dict(selected_frequency),
        "axis_first_frequency": dict(axis_first_frequency),
        "verdicts": verdicts,
        "cases": rows,
    }
