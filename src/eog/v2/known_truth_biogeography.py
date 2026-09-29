"""Known-truth virtual biogeography benchmark for EOG finite-world falsification.

This module is deliberately synthetic.  It creates a virtual landscape, a declared
virtual niche and a declared distribution-forming process, simulates positive
occurrences from that known truth, and then hides the truth from EOG while evaluating
a finite candidate-world universe.

The benchmark tests whether EOG retains truth, eliminates falsified worlds, falsifies
a misspecified finite universe when positive witnesses exist, and abstains when
candidate worlds are observationally equivalent.  It does not claim that any virtual
process is a realistic biological mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Iterable, Sequence

import numpy as np

from ..dynamic_island_reachability import (
    DynamicReachabilityEdge,
    build_dynamic_transition_operator,
)
from .world_reconstruction import (
    FiniteWorld,
    forward_reachable_configuration,
    reconstruct_compatible_worlds,
)


def _sha256(payload: object) -> str:
    data = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class VirtualLandscape:
    width: int
    height: int
    node_ids: tuple[str, ...]
    coordinates: tuple[tuple[float, float], ...]
    environment: tuple[tuple[float, float], ...]
    barrier_col: int | None = None
    barrier_gap_rows: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        n = self.width * self.height
        if self.width < 2 or self.height < 1:
            raise ValueError("virtual landscape must contain at least two cells")
        if len(self.node_ids) != n or len(self.coordinates) != n or len(self.environment) != n:
            raise ValueError("landscape vectors must match width * height")
        if len(set(self.node_ids)) != n:
            raise ValueError("node IDs must be unique")
        if self.barrier_col is not None and not 1 <= self.barrier_col < self.width:
            raise ValueError("barrier_col must lie between grid columns")
        if any(row < 0 or row >= self.height for row in self.barrier_gap_rows):
            raise ValueError("barrier gap rows must lie inside the grid")

    @property
    def fingerprint(self) -> str:
        return _sha256(
            {
                "width": self.width,
                "height": self.height,
                "node_ids": self.node_ids,
                "coordinates": self.coordinates,
                "environment": self.environment,
                "barrier_col": self.barrier_col,
                "barrier_gap_rows": self.barrier_gap_rows,
            }
        )


@dataclass(frozen=True)
class VirtualProcess:
    world_id: str
    source_id: str
    niche_center: tuple[float, float]
    niche_radius: tuple[float, float]
    dispersal_radius: float
    environmental_transition_limit: float
    barrier_permeable: bool
    max_steps: int

    def __post_init__(self) -> None:
        if not self.world_id.strip() or not self.source_id.strip():
            raise ValueError("world_id and source_id must be non-empty")
        if any((not math.isfinite(v) or v <= 0.0) for v in self.niche_radius):
            raise ValueError("niche radii must be finite and positive")
        if not math.isfinite(self.dispersal_radius) or self.dispersal_radius <= 0.0:
            raise ValueError("dispersal_radius must be finite and positive")
        if (
            not math.isfinite(self.environmental_transition_limit)
            or self.environmental_transition_limit < 0.0
        ):
            raise ValueError("environmental_transition_limit must be finite and non-negative")
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")


@dataclass(frozen=True)
class KnownTruthCaseResult:
    case_id: str
    truth_world_id: str | None
    candidate_world_ids: tuple[str, ...]
    occurrence_ids: tuple[str, ...]
    compatible_world_ids: tuple[str, ...]
    truth_retained: bool | None
    identifiable: bool
    universe_falsified: bool
    coverage_certificate: str
    fingerprint: str


def make_gradient_landscape(
    *,
    width: int = 7,
    height: int = 3,
    spike_col: int | None = 3,
    spike_amount: float = 0.75,
    barrier_col: int | None = 4,
    barrier_gap_rows: Sequence[int] = (),
) -> VirtualLandscape:
    """Create a deterministic 2-D environmental gradient with optional bottlenecks."""

    node_ids: list[str] = []
    coordinates: list[tuple[float, float]] = []
    environment: list[tuple[float, float]] = []
    for row in range(height):
        for col in range(width):
            node_ids.append(f"r{row}c{col}")
            coordinates.append((float(col), float(row)))
            base = col / max(width - 1, 1)
            temp = 0.15 + 0.55 * base
            if spike_col is not None and col == spike_col:
                temp += float(spike_amount)
            moisture = 0.5 + 0.1 * math.cos(math.pi * base)
            environment.append((float(temp), float(moisture)))
    return VirtualLandscape(
        width=width,
        height=height,
        node_ids=tuple(node_ids),
        coordinates=tuple(coordinates),
        environment=tuple(environment),
        barrier_col=barrier_col,
        barrier_gap_rows=tuple(sorted(set(int(v) for v in barrier_gap_rows))),
    )


def _viable_mask(landscape: VirtualLandscape, process: VirtualProcess) -> np.ndarray:
    env = np.asarray(landscape.environment, dtype=float)
    center = np.asarray(process.niche_center, dtype=float)
    radius = np.asarray(process.niche_radius, dtype=float)
    scaled = (env - center) / radius
    return np.sum(scaled * scaled, axis=1) <= 1.0 + 1e-12


def _crosses_barrier(
    landscape: VirtualLandscape,
    source_index: int,
    target_index: int,
) -> bool:
    if landscape.barrier_col is None:
        return False
    sx, sy = landscape.coordinates[source_index]
    tx, ty = landscape.coordinates[target_index]
    left = min(sx, tx)
    right = max(sx, tx)
    crosses = left < landscape.barrier_col <= right
    if not crosses:
        return False
    if int(round(sy)) == int(round(ty)) and int(round(sy)) in set(landscape.barrier_gap_rows):
        return False
    return True


def build_virtual_world(
    landscape: VirtualLandscape,
    process: VirtualProcess,
) -> FiniteWorld:
    """Materialise one virtual niche/dispersal process as an EOG finite world."""

    if process.source_id not in landscape.node_ids:
        raise ValueError("source_id is outside the landscape")
    viable = _viable_mask(landscape, process)
    source_index = landscape.node_ids.index(process.source_id)
    if not bool(viable[source_index]):
        raise ValueError("declared source lies outside the virtual niche")

    coords = np.asarray(landscape.coordinates, dtype=float)
    env = np.asarray(landscape.environment, dtype=float)
    edges: list[DynamicReachabilityEdge] = []
    n = len(landscape.node_ids)
    for i in range(n):
        if not viable[i]:
            continue
        for j in range(n):
            if i == j or not viable[j]:
                continue
            geo = float(np.linalg.norm(coords[i] - coords[j]))
            if geo > process.dispersal_radius + 1e-12:
                continue
            env_jump = float(np.linalg.norm(env[i] - env[j]))
            if env_jump > process.environmental_transition_limit + 1e-12:
                continue
            if not process.barrier_permeable and _crosses_barrier(landscape, i, j):
                continue
            edges.append(
                DynamicReachabilityEdge(
                    source=i,
                    target=j,
                    geographic_support=1.0,
                    environmental_support=1.0,
                    barrier_support=1.0,
                )
            )

    operator = build_dynamic_transition_operator(
        landscape.node_ids,
        edges,
        loss_support=1.0,
    )
    return FiniteWorld(
        world_id=process.world_id,
        operator=operator,
        source_ids=(process.source_id,),
        geographic_relaxation=process.dispersal_radius,
        environmental_relaxation=process.environmental_transition_limit,
        barrier_relaxation=1.0 if process.barrier_permeable else 0.0,
        analytical_variant="known_truth_virtual_biogeography_v1",
    )


def simulate_true_positive_state(
    landscape: VirtualLandscape,
    process: VirtualProcess,
) -> tuple[str, ...]:
    """Return all states reachable from the true source within the declared horizon."""

    world = build_virtual_world(landscape, process)
    result = forward_reachable_configuration(world, max_steps=process.max_steps)
    return result.reachable_ids


def _ordered_subset(node_ids: Sequence[str], ids: Iterable[str]) -> tuple[str, ...]:
    wanted = set(ids)
    return tuple(node_id for node_id in node_ids if node_id in wanted)


def positive_witness_set(
    truth_world: FiniteWorld,
    false_worlds: Sequence[FiniteWorld],
    *,
    max_steps: int,
) -> tuple[str, ...]:
    """Greedily choose true-positive nodes that witness every distinguishable false world."""

    truth_reach = set(
        forward_reachable_configuration(truth_world, max_steps=max_steps).reachable_ids
    )
    false_reach = {
        world.world_id: set(
            forward_reachable_configuration(world, max_steps=max_steps).reachable_ids
        )
        for world in false_worlds
    }
    remaining = {
        world_id
        for world_id, reached in false_reach.items()
        if truth_reach.difference(reached)
    }
    witnesses: list[str] = []
    node_order = truth_world.operator.node_ids
    while remaining:
        candidates = []
        for node_id in node_order:
            if node_id not in truth_reach or node_id in truth_world.source_ids:
                continue
            killed = tuple(
                world_id
                for world_id in sorted(remaining)
                if node_id not in false_reach[world_id]
            )
            if killed:
                candidates.append((len(killed), node_id, killed))
        if not candidates:
            raise RuntimeError("no positive witness can distinguish the remaining false worlds")
        _, chosen, killed = max(candidates, key=lambda row: (row[0], row[1]))
        witnesses.append(chosen)
        remaining.difference_update(killed)
    return tuple(witnesses)


def evaluate_known_truth_case(
    *,
    case_id: str,
    candidate_worlds: Sequence[FiniteWorld],
    occurrence_ids: Sequence[str],
    max_steps: int,
    truth_world_id: str | None,
) -> KnownTruthCaseResult:
    reconstruction = reconstruct_compatible_worlds(
        candidate_worlds,
        occurrence_ids,
        max_steps=max_steps,
    )
    truth_retained: bool | None
    if truth_world_id is None:
        truth_retained = None
    else:
        truth_retained = truth_world_id in reconstruction.compatible_world_ids
    payload = {
        "case_id": case_id,
        "truth_world_id": truth_world_id,
        "candidate_world_ids": [world.world_id for world in candidate_worlds],
        "occurrence_ids": list(reconstruction.occurrence_ids),
        "compatible_world_ids": list(reconstruction.compatible_world_ids),
        "coverage_certificate": reconstruction.coverage_certificate,
    }
    return KnownTruthCaseResult(
        case_id=case_id,
        truth_world_id=truth_world_id,
        candidate_world_ids=tuple(world.world_id for world in candidate_worlds),
        occurrence_ids=reconstruction.occurrence_ids,
        compatible_world_ids=reconstruction.compatible_world_ids,
        truth_retained=truth_retained,
        identifiable=reconstruction.identifiable,
        universe_falsified=len(reconstruction.compatible_world_ids) == 0,
        coverage_certificate=reconstruction.coverage_certificate,
        fingerprint=_sha256(payload),
    )


def _bridge_fixture() -> tuple[VirtualLandscape, VirtualProcess, tuple[VirtualProcess, ...]]:
    landscape = make_gradient_landscape()
    truth = VirtualProcess(
        world_id="truth_open",
        source_id="r1c0",
        niche_center=(0.65, 0.5),
        niche_radius=(1.5, 1.5),
        dispersal_radius=1.01,
        environmental_transition_limit=1.0,
        barrier_permeable=True,
        max_steps=8,
    )
    alternatives = (
        VirtualProcess(
            world_id="env_blocked",
            source_id=truth.source_id,
            niche_center=truth.niche_center,
            niche_radius=truth.niche_radius,
            dispersal_radius=truth.dispersal_radius,
            environmental_transition_limit=0.25,
            barrier_permeable=True,
            max_steps=truth.max_steps,
        ),
        VirtualProcess(
            world_id="barrier_blocked",
            source_id=truth.source_id,
            niche_center=truth.niche_center,
            niche_radius=truth.niche_radius,
            dispersal_radius=truth.dispersal_radius,
            environmental_transition_limit=truth.environmental_transition_limit,
            barrier_permeable=False,
            max_steps=truth.max_steps,
        ),
    )
    return landscape, truth, alternatives


def run_canonical_known_truth_benchmark() -> dict[str, object]:
    """Run the frozen v1 canonical exact benchmark and return hypothesis verdicts."""

    landscape, truth_process, alternative_processes = _bridge_fixture()
    truth = build_virtual_world(landscape, truth_process)
    alternatives = tuple(build_virtual_world(landscape, p) for p in alternative_processes)
    witnesses = positive_witness_set(truth, alternatives, max_steps=truth_process.max_steps)
    if not witnesses:
        raise RuntimeError("bridge fixture must contain at least one discriminating witness")
    observation_ids = _ordered_subset(
        landscape.node_ids,
        (truth_process.source_id, *witnesses),
    )

    # H1: every sequential positive prefix must retain the exact truth.
    truth_state = simulate_true_positive_state(landscape, truth_process)
    ordered_truth = _ordered_subset(landscape.node_ids, truth_state)
    prefix_results: list[KnownTruthCaseResult] = []
    for end in range(2, len(ordered_truth) + 1):
        prefix = ordered_truth[:end]
        if truth_process.source_id not in prefix:
            continue
        prefix_results.append(
            evaluate_known_truth_case(
                case_id=f"truth_prefix_{end}",
                candidate_worlds=(truth, *alternatives),
                occurrence_ids=prefix,
                max_steps=truth_process.max_steps,
                truth_world_id=truth.world_id,
            )
        )
    h1_supported = bool(prefix_results) and all(
        result.truth_retained is True for result in prefix_results
    )

    # H2: the complete positive witness set should isolate truth.
    h2_case = evaluate_known_truth_case(
        case_id="truth_in_universe_with_complete_witness",
        candidate_worlds=(truth, *alternatives),
        occurrence_ids=observation_ids,
        max_steps=truth_process.max_steps,
        truth_world_id=truth.world_id,
    )
    h2_supported = h2_case.compatible_world_ids == (truth.world_id,)

    # H3: omit truth but retain the same witness observations.
    h3_case = evaluate_known_truth_case(
        case_id="truth_omitted_with_complete_witness",
        candidate_worlds=alternatives,
        occurrence_ids=observation_ids,
        max_steps=truth_process.max_steps,
        truth_world_id=None,
    )
    h3_supported = h3_case.universe_falsified

    # H4: two genuinely different operators but an observation-complete state that
    # both can realise within the generous horizon.
    equiv_landscape = make_gradient_landscape(
        width=5,
        height=2,
        spike_col=None,
        barrier_col=None,
    )
    common = dict(
        source_id="r0c0",
        niche_center=(0.5, 0.5),
        niche_radius=(2.0, 2.0),
        environmental_transition_limit=1.0,
        barrier_permeable=True,
        max_steps=12,
    )
    equiv_a = build_virtual_world(
        equiv_landscape,
        VirtualProcess(world_id="short_step", dispersal_radius=1.01, **common),
    )
    equiv_b = build_virtual_world(
        equiv_landscape,
        VirtualProcess(world_id="long_step", dispersal_radius=2.01, **common),
    )
    if equiv_a.operator.fingerprint == equiv_b.operator.fingerprint:
        raise RuntimeError("equivalence fixture requires different latent operators")
    equiv_occurrences = simulate_true_positive_state(
        equiv_landscape,
        VirtualProcess(world_id="equiv_truth", dispersal_radius=1.01, **common),
    )
    h4_case = evaluate_known_truth_case(
        case_id="observational_equivalence",
        candidate_worlds=(equiv_a, equiv_b),
        occurrence_ids=equiv_occurrences,
        max_steps=12,
        truth_world_id="short_step",
    )
    h4_supported = (
        set(h4_case.compatible_world_ids) == {"short_step", "long_step"}
        and not h4_case.identifiable
    )

    # H5 boundary demonstration: add one impossible positive beyond a deliberately
    # short truth horizon.  The naive positive-only core should eliminate truth.
    short_truth_process = VirtualProcess(
        world_id="short_horizon_truth",
        source_id="r1c0",
        niche_center=truth_process.niche_center,
        niche_radius=truth_process.niche_radius,
        dispersal_radius=1.01,
        environmental_transition_limit=1.0,
        barrier_permeable=True,
        max_steps=2,
    )
    short_truth = build_virtual_world(landscape, short_truth_process)
    contaminated_occurrences = (short_truth_process.source_id, "r1c6")
    h5_case = evaluate_known_truth_case(
        case_id="false_positive_boundary",
        candidate_worlds=(short_truth,),
        occurrence_ids=contaminated_occurrences,
        max_steps=short_truth_process.max_steps,
        truth_world_id=short_truth.world_id,
    )

    verdicts = {
        "H1_truth_retention": "SUPPORTED" if h1_supported else "REFUTED",
        "H2_discriminating_contraction": "SUPPORTED" if h2_supported else "REFUTED",
        "H3_omitted_truth_falsification": "SUPPORTED" if h3_supported else "REFUTED",
        "H4_nonidentification_honesty": "SUPPORTED" if h4_supported else "REFUTED",
        "H5_observation_error_boundary": (
            "BOUNDARY_CONFIRMED" if h5_case.truth_retained is False else "NOT_OBSERVED"
        ),
    }
    payload = {
        "schema": "eog.known_truth_biogeography.canonical_result.v1",
        "landscape_fingerprint": landscape.fingerprint,
        "witnesses": list(witnesses),
        "verdicts": verdicts,
        "h1_prefix_count": len(prefix_results),
        "h2_compatible_world_ids": list(h2_case.compatible_world_ids),
        "h3_compatible_world_ids": list(h3_case.compatible_world_ids),
        "h4_compatible_world_ids": list(h4_case.compatible_world_ids),
        "h5_compatible_world_ids": list(h5_case.compatible_world_ids),
    }
    payload["fingerprint"] = _sha256(payload)
    return payload


def exact_minimum_positive_witness_set(
    truth_world: FiniteWorld,
    candidate_worlds: Sequence[FiniteWorld],
    *,
    max_steps: int,
) -> tuple[str, ...] | None:
    """Return an exact minimum positive witness set, or None if truth is not identifiable."""

    false_worlds = tuple(world for world in candidate_worlds if world.world_id != truth_world.world_id)
    if not false_worlds:
        return ()

    truth_reach = set(
        forward_reachable_configuration(truth_world, max_steps=max_steps).reachable_ids
    )
    false_reach = [
        set(forward_reachable_configuration(world, max_steps=max_steps).reachable_ids)
        for world in false_worlds
    ]
    full_mask = (1 << len(false_worlds)) - 1
    node_masks: list[tuple[str, int]] = []
    source_set = set(truth_world.source_ids)
    for node_id in truth_world.operator.node_ids:
        if node_id not in truth_reach or node_id in source_set:
            continue
        mask = 0
        for idx, reached in enumerate(false_reach):
            if node_id not in reached:
                mask |= 1 << idx
        if mask:
            node_masks.append((node_id, mask))

    coverable = 0
    for _, mask in node_masks:
        coverable |= mask
    if coverable != full_mask:
        return None

    best: dict[int, tuple[str, ...]] = {0: ()}
    for node_id, node_mask in node_masks:
        prior = list(best.items())
        for mask, chosen in prior:
            updated = mask | node_mask
            candidate = (*chosen, node_id)
            incumbent = best.get(updated)
            if incumbent is None or (len(candidate), candidate) < (len(incumbent), incumbent):
                best[updated] = candidate
    return best[full_mask]


def _factorial_processes() -> tuple[VirtualProcess, ...]:
    rows: list[VirtualProcess] = []
    for niche_radius_temp in (0.5, 1.5):
        for dispersal_radius in (1.01, 2.01):
            for environmental_transition_limit in (0.25, 1.0):
                for barrier_permeable in (False, True):
                    world_id = (
                        f"n{niche_radius_temp:.2f}_"
                        f"d{dispersal_radius:.2f}_"
                        f"e{environmental_transition_limit:.2f}_"
                        f"b{int(barrier_permeable)}"
                    )
                    rows.append(
                        VirtualProcess(
                            world_id=world_id,
                            source_id="r1c0",
                            niche_center=(0.6, 0.6),
                            niche_radius=(niche_radius_temp, 1.5),
                            dispersal_radius=dispersal_radius,
                            environmental_transition_limit=environmental_transition_limit,
                            barrier_permeable=barrier_permeable,
                            max_steps=8,
                        )
                    )
    return tuple(rows)


def _factorial_landscapes() -> tuple[tuple[str, VirtualLandscape], ...]:
    return (
        (
            "continuous",
            make_gradient_landscape(spike_col=3, spike_amount=0.0, barrier_col=None),
        ),
        (
            "environmental_bottleneck",
            make_gradient_landscape(spike_col=3, spike_amount=0.75, barrier_col=None),
        ),
        (
            "hard_barrier",
            make_gradient_landscape(spike_col=3, spike_amount=0.0, barrier_col=4),
        ),
        (
            "combined_bottleneck",
            make_gradient_landscape(spike_col=3, spike_amount=0.75, barrier_col=4),
        ),
    )


def run_witness_factorial_benchmark() -> dict[str, object]:
    """Execute the preregistered witness-complexity factorial."""

    import time

    started = time.perf_counter()
    coverages = (0.1, 0.25, 0.5, 1.0)
    replicates = 32
    processes = _factorial_processes()

    eligible_cases = 0
    truth_retention_failures = 0
    f1_mismatches = 0
    f2_monotonicity_violations = 0
    f3_equivalence_violations = 0
    f4_boundary_violations = 0
    exact_identifiable = 0
    equivalent_cases = 0
    omitted_falsified = 0
    omitted_survived = 0
    omitted_with_superset = 0
    omitted_with_superset_survived = 0
    witness_histogram: dict[str, int] = {}
    identification_counts = {str(value): 0 for value in coverages}
    identification_denominators = {str(value): 0 for value in coverages}
    case_rows: list[dict[str, object]] = []

    for landscape_id, landscape in _factorial_landscapes():
        worlds_by_id: dict[str, FiniteWorld] = {}
        for process in processes:
            try:
                worlds_by_id[process.world_id] = build_virtual_world(landscape, process)
            except ValueError:
                continue
        worlds = tuple(worlds_by_id[key] for key in sorted(worlds_by_id))
        if len(worlds) < 2:
            continue

        reachable_by_world = {
            world.world_id: set(
                forward_reachable_configuration(world, max_steps=8).reachable_ids
            )
            for world in worlds
        }

        for truth in worlds:
            truth_reach = reachable_by_world[truth.world_id]
            if len(truth_reach) < 2:
                continue
            eligible_cases += 1
            false_worlds = tuple(world for world in worlds if world.world_id != truth.world_id)
            equivalent_false = tuple(
                world.world_id
                for world in false_worlds
                if reachable_by_world[world.world_id] == truth_reach
            )
            if equivalent_false:
                equivalent_cases += 1

            minimum_witness = exact_minimum_positive_witness_set(
                truth,
                worlds,
                max_steps=8,
            )
            if minimum_witness is None:
                witness_histogram["unidentifiable"] = witness_histogram.get("unidentifiable", 0) + 1
            else:
                exact_identifiable += 1
                key = str(len(minimum_witness))
                witness_histogram[key] = witness_histogram.get(key, 0) + 1

            full_occurrences = _ordered_subset(landscape.node_ids, truth_reach)
            full_reconstruction = reconstruct_compatible_worlds(
                worlds,
                full_occurrences,
                max_steps=8,
            )
            expected_full = tuple(
                world.world_id
                for world in worlds
                if set(full_occurrences).issubset(reachable_by_world[world.world_id])
            )
            if full_reconstruction.compatible_world_ids != expected_full:
                f1_mismatches += 1
            if truth.world_id not in full_reconstruction.compatible_world_ids:
                truth_retention_failures += 1
            if equivalent_false and not set(equivalent_false).issubset(
                full_reconstruction.compatible_world_ids
            ):
                f3_equivalence_violations += 1

            omitted_worlds = false_worlds
            omitted_reconstruction = reconstruct_compatible_worlds(
                omitted_worlds,
                full_occurrences,
                max_steps=8,
            )
            expected_omitted = tuple(
                world.world_id
                for world in omitted_worlds
                if set(full_occurrences).issubset(reachable_by_world[world.world_id])
            )
            if omitted_reconstruction.compatible_world_ids != expected_omitted:
                f4_boundary_violations += 1
            if omitted_reconstruction.compatible_world_ids:
                omitted_survived += 1
            else:
                omitted_falsified += 1
            superset_exists = any(
                truth_reach.issubset(reachable_by_world[world.world_id])
                for world in omitted_worlds
            )
            if superset_exists:
                omitted_with_superset += 1
                if omitted_reconstruction.compatible_world_ids:
                    omitted_with_superset_survived += 1
                else:
                    f4_boundary_violations += 1

            for replicate in range(replicates):
                identified_sequence: list[bool] = []
                seed_prefix = f"{landscape_id}|{truth.world_id}|{replicate}"
                full_non_source = [node for node in full_occurrences if node != truth.source_ids[0]]
                seed = int(hashlib.sha256(seed_prefix.encode("utf-8")).hexdigest()[:16], 16)
                rng = np.random.default_rng(seed)
                shuffled = list(full_non_source)
                rng.shuffle(shuffled)

                for coverage in coverages:
                    count = (
                        len(shuffled)
                        if coverage >= 1.0
                        else max(1, int(math.ceil(coverage * len(shuffled))))
                    )
                    sampled = _ordered_subset(
                        landscape.node_ids,
                        (truth.source_ids[0], *shuffled[:count]),
                    )
                    reconstruction = reconstruct_compatible_worlds(
                        worlds,
                        sampled,
                        max_steps=8,
                    )
                    expected = tuple(
                        world.world_id
                        for world in worlds
                        if set(sampled).issubset(reachable_by_world[world.world_id])
                    )
                    if reconstruction.compatible_world_ids != expected:
                        f1_mismatches += 1
                    if truth.world_id not in reconstruction.compatible_world_ids:
                        truth_retention_failures += 1
                    identified = reconstruction.compatible_world_ids == (truth.world_id,)
                    identified_sequence.append(identified)
                    key = str(coverage)
                    identification_denominators[key] += 1
                    if identified:
                        identification_counts[key] += 1

                if any(
                    earlier and not later
                    for earlier, later in zip(identified_sequence, identified_sequence[1:])
                ):
                    f2_monotonicity_violations += 1

            case_rows.append(
                {
                    "landscape_id": landscape_id,
                    "truth_world_id": truth.world_id,
                    "truth_reachable_count": len(truth_reach),
                    "full_compatible_count": len(full_reconstruction.compatible_world_ids),
                    "equivalent_false_world_count": len(equivalent_false),
                    "minimum_positive_witness_count": (
                        None if minimum_witness is None else len(minimum_witness)
                    ),
                    "omitted_truth_compatible_count": len(
                        omitted_reconstruction.compatible_world_ids
                    ),
                    "omitted_truth_falsified": (
                        len(omitted_reconstruction.compatible_world_ids) == 0
                    ),
                    "omitted_truth_superset_candidate_exists": superset_exists,
                }
            )

    identification_rate = {
        key: (
            0.0
            if identification_denominators[key] == 0
            else identification_counts[key] / identification_denominators[key]
        )
        for key in identification_counts
    }
    runtime_seconds = time.perf_counter() - started
    verdicts = {
        "F1_witness_criterion": "SUPPORTED" if f1_mismatches == 0 else "REFUTED",
        "F2_sampling_monotonicity": (
            "SUPPORTED" if f2_monotonicity_violations == 0 else "REFUTED"
        ),
        "F3_equivalence_ceiling": (
            "SUPPORTED" if f3_equivalence_violations == 0 else "REFUTED"
        ),
        "F4_omitted_truth_not_guaranteed": (
            "BOUNDARY_CONFIRMED"
            if (
                f4_boundary_violations == 0
                and omitted_survived > 0
                and omitted_falsified > 0
            )
            else "NOT_CONFIRMED"
        ),
    }
    result: dict[str, object] = {
        "schema": "eog.known_truth_biogeography.witness_factorial_result.v1",
        "eligible_exact_cases": eligible_cases,
        "process_worlds_per_landscape": len(processes),
        "sampling_replicates_per_case": replicates,
        "sampling_coverages": list(coverages),
        "truth_retention_failures": truth_retention_failures,
        "f1_criterion_mismatches": f1_mismatches,
        "f2_monotonicity_violations": f2_monotonicity_violations,
        "f3_equivalence_violations": f3_equivalence_violations,
        "f4_boundary_violations": f4_boundary_violations,
        "identifiable_at_full_coverage_fraction": (
            0.0 if eligible_cases == 0 else exact_identifiable / eligible_cases
        ),
        "observational_equivalence_fraction": (
            0.0 if eligible_cases == 0 else equivalent_cases / eligible_cases
        ),
        "minimum_positive_witness_count_distribution": witness_histogram,
        "identification_rate_by_sampling_coverage": identification_rate,
        "omitted_truth_falsification_fraction": (
            0.0
            if eligible_cases == 0
            else omitted_falsified / eligible_cases
        ),
        "omitted_truth_survival_fraction": (
            0.0
            if eligible_cases == 0
            else omitted_survived / eligible_cases
        ),
        "omitted_truth_survival_with_superset_fraction": (
            0.0
            if omitted_with_superset == 0
            else omitted_with_superset_survived / omitted_with_superset
        ),
        "runtime_seconds": runtime_seconds,
        "verdicts": verdicts,
        "cases": case_rows,
    }
    fingerprint_payload = dict(result)
    fingerprint_payload["runtime_seconds"] = None
    result["fingerprint"] = _sha256(fingerprint_payload)
    return result
