"""Independent stochastic BAM counterfactual forecast targets.

IMPORTANT: this module imports no EOG package.  It extends the independent stochastic
BAM generator with exact conditional one-step forecast distributions under the frozen
Phase-VI counterfactual operators.

The forecast is conditional on a supplied current occupied snapshot.  Historical source
identity is not forced immortal after the conditioning time: every currently occupied
eligible node follows the same persistence rule.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from independent_stochastic_bam_generator import (
    AssociateRealization,
    FocalSpec,
    IndependentLandscape,
    abiotic_mask,
    biotic_mask,
    movement_adjacency,
)


@dataclass(frozen=True)
class CounterfactualForecast:
    transformation: str
    baseline_probability: tuple[float, ...]
    counterfactual_probability: tuple[float, ...]
    expected_baseline_count: float
    expected_counterfactual_count: float
    expected_count_delta: float
    binary_decision: bool


def _grid_neighbours(landscape: IndependentLandscape) -> tuple[tuple[int, ...], ...]:
    lookup = {
        (int(round(y)), int(round(x))): i
        for i, (x, y) in enumerate(landscape.coordinates)
    }
    rows = []
    for x, y in landscape.coordinates:
        r, c = int(round(y)), int(round(x))
        values = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            idx = lookup.get((r + dr, c + dc))
            if idx is not None:
                values.append(idx)
        rows.append(tuple(sorted(values)))
    return tuple(rows)


def _dilate(mask: np.ndarray, neighbours) -> np.ndarray:
    value = np.asarray(mask, dtype=bool)
    out = value.copy()
    for i, occupied in enumerate(value):
        if not bool(occupied):
            continue
        for j in neighbours[i]:
            out[j] = True
    return out


def _erode(mask: np.ndarray, neighbours) -> np.ndarray:
    value = np.asarray(mask, dtype=bool)
    out = np.zeros(value.shape[0], dtype=bool)
    for i, occupied in enumerate(value):
        if not bool(occupied):
            continue
        if all(bool(value[j]) for j in neighbours[i]):
            out[i] = True
    return out


def _biotic_stress_masks(
    landscape: IndependentLandscape,
    associates: AssociateRealization,
) -> tuple[np.ndarray, np.ndarray]:
    neighbours = _grid_neighbours(landscape)
    return (
        _erode(associates.partner_mask, neighbours),
        _dilate(associates.antagonist_mask, neighbours),
    )


def _shifted_abiotic_mask(
    landscape: IndependentLandscape,
    spec: FocalSpec,
    *,
    temperature_delta: float = 0.08,
    moisture_delta: float = -0.04,
) -> np.ndarray:
    environment = np.asarray(landscape.environment, dtype=float).copy()
    environment[:, 0] += float(temperature_delta)
    environment[:, 1] += float(moisture_delta)
    center = np.asarray(spec.niche_center, dtype=float)
    radius = np.asarray(spec.niche_radius, dtype=float)
    scaled = (environment - center) / radius
    return np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12


def one_step_probability_vector(
    landscape: IndependentLandscape,
    *,
    current_snapshot: np.ndarray,
    eligible_mask: np.ndarray,
    step_radius: float,
    barrier_permeable: bool,
    colonization_beta: float,
    persistence_probability: float,
) -> np.ndarray:
    current = np.asarray(current_snapshot, dtype=bool)
    eligible = np.asarray(eligible_mask, dtype=bool)
    if current.shape != eligible.shape:
        raise ValueError("current_snapshot and eligible_mask must share shape")

    adjacency = movement_adjacency(
        landscape,
        step_radius=step_radius,
        barrier_permeable=barrier_permeable,
    )
    probabilities = np.zeros(current.shape[0], dtype=float)
    for node in range(current.shape[0]):
        if not bool(eligible[node]):
            continue
        if bool(current[node]):
            probabilities[node] = float(persistence_probability)
            continue
        sources = sum(1 for neighbour in adjacency[node] if bool(current[neighbour]))
        if sources > 0:
            probabilities[node] = 1.0 - (1.0 - float(colonization_beta)) ** sources
    return probabilities


def _baseline_eligibility(
    landscape: IndependentLandscape,
    associates: AssociateRealization,
    spec: FocalSpec,
) -> np.ndarray:
    A = abiotic_mask(landscape, spec.niche_center, spec.niche_radius)
    B = biotic_mask(
        spec.biotic_mode,
        partner_mask=associates.partner_mask,
        antagonist_mask=associates.antagonist_mask,
    )
    return A & B


def _counterfactual_contract(
    landscape: IndependentLandscape,
    associates: AssociateRealization,
    spec: FocalSpec,
    transformation: str,
) -> tuple[np.ndarray, bool]:
    A = abiotic_mask(landscape, spec.niche_center, spec.niche_radius)
    B = biotic_mask(
        spec.biotic_mode,
        partner_mask=associates.partner_mask,
        antagonist_mask=associates.antagonist_mask,
    )
    barrier = bool(spec.barrier_permeable)

    if transformation == "climate_shift":
        eligible = _shifted_abiotic_mask(landscape, spec) & B
    elif transformation == "biotic_stress":
        partner, antagonist = _biotic_stress_masks(landscape, associates)
        B_stress = biotic_mask(
            spec.biotic_mode,
            partner_mask=partner,
            antagonist_mask=antagonist,
        )
        eligible = A & B_stress
    elif transformation == "barrier_restoration":
        eligible = A & B
        barrier = True
    else:
        raise ValueError("unknown counterfactual transformation")
    return eligible, barrier


def stochastic_counterfactual_forecast(
    landscape: IndependentLandscape,
    associates: AssociateRealization,
    spec: FocalSpec,
    *,
    current_snapshot: np.ndarray,
    transformation: str,
) -> CounterfactualForecast:
    baseline_eligible = _baseline_eligibility(landscape, associates, spec)
    baseline = one_step_probability_vector(
        landscape,
        current_snapshot=current_snapshot,
        eligible_mask=baseline_eligible,
        step_radius=spec.step_radius,
        barrier_permeable=spec.barrier_permeable,
        colonization_beta=spec.colonization_beta,
        persistence_probability=spec.persistence_probability,
    )

    cf_eligible, cf_barrier = _counterfactual_contract(
        landscape,
        associates,
        spec,
        transformation,
    )
    counterfactual = one_step_probability_vector(
        landscape,
        current_snapshot=current_snapshot,
        eligible_mask=cf_eligible,
        step_radius=spec.step_radius,
        barrier_permeable=cf_barrier,
        colonization_beta=spec.colonization_beta,
        persistence_probability=spec.persistence_probability,
    )

    baseline_count = float(np.sum(baseline))
    counterfactual_count = float(np.sum(counterfactual))
    delta = counterfactual_count - baseline_count
    if transformation in {"climate_shift", "biotic_stress"}:
        decision = delta < -1e-12
    else:
        decision = delta > 1e-12

    return CounterfactualForecast(
        transformation=transformation,
        baseline_probability=tuple(round(float(v), 12) for v in baseline),
        counterfactual_probability=tuple(
            round(float(v), 12) for v in counterfactual
        ),
        expected_baseline_count=baseline_count,
        expected_counterfactual_count=counterfactual_count,
        expected_count_delta=delta,
        binary_decision=bool(decision),
    )
