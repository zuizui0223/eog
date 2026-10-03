"""Frozen M-only external bridge for Swedish river-barrier fish time series.

A and B are unrestricted. The finite world family varies only movement/connectivity:
four response-independent Euclidean geometry thresholds crossed with closed/open
fragment assumptions, plus one fully open within-river world.

The engine contains no download code and must only be used after source/schema gates.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


RAW_COLUMNS = (
    "XKOORLOK",
    "YKOORLOK",
    "unique_frag",
    "riverID",
    "year",
    "ÖringTOT_mean",
    "Elrit_mean",
    "Gädda_mean",
)

SPECIES_COLUMNS = (
    ("Salmo trutta", "ÖringTOT_mean"),
    ("Phoxinus phoxinus", "Elrit_mean"),
    ("Esox lucius", "Gädda_mean"),
)

CALIBRATION_START = 1988
CALIBRATION_END = 2004
HELDOUT_START = 2005
HELDOUT_END = 2021

M_LEVELS = (
    "closed_q25",
    "closed_q50",
    "closed_q75",
    "closed_q90",
    "open_q25",
    "open_q50",
    "open_q75",
    "open_q90",
    "open_all",
)


class SwedenBridgeStop(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class PhysicalSite:
    river_id: str
    x: float
    y: float
    fragment: str

    @property
    def node_id(self) -> str:
        return (
            f"{self.river_id}|"
            f"{format(self.x, '.12g')}|{format(self.y, '.12g')}"
        )


@dataclass(frozen=True)
class MovementWorld:
    world_id: str
    barrier_mode: str
    threshold_level: str | None


@dataclass(frozen=True)
class SpeciesBridgeResult:
    species: str
    density_column: str
    calibration_positive_nodes: tuple[str, ...]
    heldout_positive_nodes: tuple[str, ...]
    calibration_world_ids: tuple[str, ...]
    final_survivor_world_ids: tuple[str, ...]
    heldout_witness_rows: tuple[dict[str, object], ...]


def _canonical_text(value: object, field: str) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        raise SwedenBridgeStop(f"{field} is missing")
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        raise SwedenBridgeStop(f"{field} is empty")
    return text


def _canonical_float(value: object, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SwedenBridgeStop(f"{field} is not numeric: {value!r}") from exc
    if not math.isfinite(result):
        raise SwedenBridgeStop(f"{field} is nonfinite")
    return result


def _canonical_year(value: object) -> int:
    numeric = _canonical_float(value, "year")
    if not numeric.is_integer():
        raise SwedenBridgeStop(f"year must be integer-valued: {value!r}")
    return int(numeric)


def validate_raw_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if tuple(frame.columns) != RAW_COLUMNS:
        raise SwedenBridgeStop(
            "rawdf physical schema mismatch: "
            f"expected={list(RAW_COLUMNS)}, observed={list(frame.columns)}"
        )

    rows = frame.copy()
    rows["riverID"] = rows["riverID"].map(
        lambda value: _canonical_text(value, "riverID")
    )
    rows["unique_frag"] = rows["unique_frag"].map(
        lambda value: _canonical_text(value, "unique_frag")
    )
    rows["XKOORLOK"] = rows["XKOORLOK"].map(
        lambda value: _canonical_float(value, "XKOORLOK")
    )
    rows["YKOORLOK"] = rows["YKOORLOK"].map(
        lambda value: _canonical_float(value, "YKOORLOK")
    )
    rows["year"] = rows["year"].map(_canonical_year)

    for _, column in SPECIES_COLUMNS:
        numeric = pd.to_numeric(rows[column], errors="coerce")
        # Missing is allowed and remains unknown; finite observed values must be >= 0.
        finite = numeric.dropna()
        if (finite < 0).any() or not np.isfinite(finite.to_numpy(dtype=float)).all():
            raise SwedenBridgeStop(
                f"density column {column} contains negative/nonfinite observed value"
            )
        rows[column] = numeric.astype(float)

    key = ["riverID", "XKOORLOK", "YKOORLOK", "year"]
    if rows.duplicated(key).any():
        raise SwedenBridgeStop("duplicate physical-site-year row")

    # Fragment identity is physical metadata and may not drift through time.
    grouped = rows.groupby(
        ["riverID", "XKOORLOK", "YKOORLOK"],
        sort=True,
        dropna=False,
    )["unique_frag"].nunique(dropna=False)
    if (grouped != 1).any():
        raise SwedenBridgeStop("physical site changes unique_frag across years")

    return rows


def site_registry(frame: pd.DataFrame) -> dict[str, PhysicalSite]:
    rows = validate_raw_frame(frame)
    registry: dict[str, PhysicalSite] = {}
    subset = rows.drop_duplicates(
        ["riverID", "XKOORLOK", "YKOORLOK", "unique_frag"]
    )
    for row in subset.to_dict("records"):
        site = PhysicalSite(
            river_id=str(row["riverID"]),
            x=float(row["XKOORLOK"]),
            y=float(row["YKOORLOK"]),
            fragment=str(row["unique_frag"]),
        )
        incumbent = registry.get(site.node_id)
        if incumbent is not None and incumbent != site:
            raise SwedenBridgeStop(f"physical-site identity drift: {site.node_id}")
        registry[site.node_id] = site
    if len(registry) < 2:
        raise SwedenBridgeStop("need at least two physical sites")
    return registry


def fit_distance_thresholds(frame: pd.DataFrame) -> tuple[tuple[str, float], ...]:
    registry = site_registry(frame)
    by_river: dict[str, list[PhysicalSite]] = {}
    for site in registry.values():
        by_river.setdefault(site.river_id, []).append(site)

    distances: list[float] = []
    for sites in by_river.values():
        ordered = sorted(sites)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                dx = ordered[i].x - ordered[j].x
                dy = ordered[i].y - ordered[j].y
                distance = math.hypot(dx, dy)
                if not math.isfinite(distance):
                    raise SwedenBridgeStop("nonfinite within-river distance")
                distances.append(distance)

    if not distances:
        raise SwedenBridgeStop("empty within-river distance population")
    values = np.asarray(distances, dtype=float)
    thresholds = tuple(
        (label, float(np.quantile(values, q, method="linear")))
        for label, q in (
            ("q25", 0.25),
            ("q50", 0.50),
            ("q75", 0.75),
            ("q90", 0.90),
        )
    )
    if any(value <= 0 or not math.isfinite(value) for _, value in thresholds):
        raise SwedenBridgeStop("invalid movement threshold")
    return thresholds


def all_worlds() -> tuple[MovementWorld, ...]:
    rows = []
    for mode in ("closed", "open"):
        for level in ("q25", "q50", "q75", "q90"):
            rows.append(
                MovementWorld(
                    world_id=f"M_{mode}_{level}",
                    barrier_mode=mode,
                    threshold_level=level,
                )
            )
    rows.append(
        MovementWorld(
            world_id="M_open_all",
            barrier_mode="open_all",
            threshold_level=None,
        )
    )
    if len(rows) != 9:
        raise RuntimeError("frozen movement family must contain exactly 9 worlds")
    return tuple(rows)


def build_graph(
    frame: pd.DataFrame,
    world: MovementWorld,
    thresholds: Mapping[str, float],
) -> dict[str, frozenset[str]]:
    registry = site_registry(frame)
    adjacency = {node_id: set() for node_id in registry}
    by_river: dict[str, list[PhysicalSite]] = {}
    for site in registry.values():
        by_river.setdefault(site.river_id, []).append(site)

    if world.barrier_mode == "open_all":
        cutoff = math.inf
    else:
        if world.threshold_level not in thresholds:
            raise SwedenBridgeStop(
                f"missing threshold {world.threshold_level!r}"
            )
        cutoff = float(thresholds[world.threshold_level])

    for sites in by_river.values():
        ordered = sorted(sites)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                left, right = ordered[i], ordered[j]
                distance = math.hypot(left.x - right.x, left.y - right.y)
                if distance > cutoff + 1e-12:
                    continue
                if (
                    world.barrier_mode == "closed"
                    and left.fragment != right.fragment
                ):
                    continue
                adjacency[left.node_id].add(right.node_id)
                adjacency[right.node_id].add(left.node_id)

    return {
        node_id: frozenset(sorted(neighbours))
        for node_id, neighbours in sorted(adjacency.items())
    }


def reachable(
    graph: Mapping[str, Sequence[str]],
    sources: Iterable[str],
) -> frozenset[str]:
    source_ids = tuple(sorted(set(str(value) for value in sources)))
    if not source_ids:
        return frozenset()
    unknown = set(source_ids).difference(graph)
    if unknown:
        raise SwedenBridgeStop(
            f"movement source absent from site registry: {sorted(unknown)}"
        )
    seen = set(source_ids)
    queue = deque(source_ids)
    while queue:
        node = queue.popleft()
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return frozenset(seen)


def positive_nodes(
    frame: pd.DataFrame,
    density_column: str,
    start_year: int,
    end_year: int,
) -> tuple[str, ...]:
    rows = validate_raw_frame(frame)
    registry = site_registry(rows)
    subset = rows.loc[
        (rows["year"] >= int(start_year))
        & (rows["year"] <= int(end_year))
        & rows[density_column].notna()
        & (rows[density_column] > 0)
    ]
    nodes = set()
    for row in subset.to_dict("records"):
        site = PhysicalSite(
            river_id=str(row["riverID"]),
            x=float(row["XKOORLOK"]),
            y=float(row["YKOORLOK"]),
            fragment=str(row["unique_frag"]),
        )
        if site.node_id not in registry:
            raise SwedenBridgeStop("positive site absent from site registry")
        nodes.add(site.node_id)
    return tuple(sorted(nodes))


def evaluate_species(
    frame: pd.DataFrame,
    species: str,
    density_column: str,
    thresholds: tuple[tuple[str, float], ...],
) -> SpeciesBridgeResult:
    calibration = positive_nodes(
        frame,
        density_column,
        CALIBRATION_START,
        CALIBRATION_END,
    )
    heldout = positive_nodes(
        frame,
        density_column,
        HELDOUT_START,
        HELDOUT_END,
    )

    if len(calibration) < 2:
        return SpeciesBridgeResult(
            species=species,
            density_column=density_column,
            calibration_positive_nodes=calibration,
            heldout_positive_nodes=heldout,
            calibration_world_ids=(),
            final_survivor_world_ids=(),
            heldout_witness_rows=(),
        )

    threshold_map = dict(thresholds)
    worlds = all_worlds()
    calibration_survivors = []
    reach_by_world: dict[str, frozenset[str]] = {}
    for world in worlds:
        graph = build_graph(frame, world, threshold_map)
        r = reachable(graph, calibration)
        reach_by_world[world.world_id] = r
        if all(node in r for node in calibration):
            calibration_survivors.append(world)

    if len(calibration_survivors) != 9:
        raise SwedenBridgeStop(
            "calibration compatibility invariant failed: "
            f"expected 9 worlds, got {len(calibration_survivors)}"
        )

    final = {world.world_id for world in calibration_survivors}
    witness_rows = []
    for node in heldout:
        eliminated = [
            world.world_id
            for world in calibration_survivors
            if node not in reach_by_world[world.world_id]
        ]
        final.difference_update(eliminated)
        closed = sum(world_id.startswith("M_closed_") for world_id in eliminated)
        open_ = sum(
            world_id.startswith("M_open_") and world_id != "M_open_all"
            for world_id in eliminated
        )
        witness_rows.append(
            {
                "node_id": node,
                "calibration_survivor_count": 9,
                "individually_eliminated_world_count": len(eliminated),
                "individually_eliminated_world_fraction": len(eliminated) / 9,
                "eliminated_closed_world_count": closed,
                "eliminated_open_threshold_world_count": open_,
                "open_all_eliminated": "M_open_all" in eliminated,
            }
        )

    return SpeciesBridgeResult(
        species=species,
        density_column=density_column,
        calibration_positive_nodes=calibration,
        heldout_positive_nodes=heldout,
        calibration_world_ids=tuple(
            world.world_id for world in calibration_survivors
        ),
        final_survivor_world_ids=tuple(sorted(final)),
        heldout_witness_rows=tuple(witness_rows),
    )


def execute_bridge(frame: pd.DataFrame) -> dict[str, object]:
    rows = validate_raw_frame(frame)
    thresholds = fit_distance_thresholds(rows)

    species_results = []
    for species, column in SPECIES_COLUMNS:
        result = evaluate_species(rows, species, column, thresholds)
        estimable = len(result.calibration_positive_nodes) >= 2
        calibration_count = len(result.calibration_world_ids)
        final_count = len(result.final_survivor_world_ids)
        eliminated = calibration_count - final_count
        species_results.append(
            {
                "species": species,
                "density_column": column,
                "estimable": estimable,
                "calibration_positive_node_count": len(
                    result.calibration_positive_nodes
                ),
                "heldout_positive_node_count": len(
                    result.heldout_positive_nodes
                ),
                "calibration_survivor_world_count": calibration_count,
                "final_survivor_world_count": final_count,
                "heldout_eliminated_world_count": eliminated,
                "heldout_contraction_fraction": (
                    None
                    if calibration_count == 0
                    else eliminated / calibration_count
                ),
                "status": (
                    "non_estimable_calibration_positive_sites"
                    if not estimable
                    else "no_heldout_positive_witness"
                    if not result.heldout_positive_nodes
                    else "heldout_falsified_all_calibration_worlds"
                    if final_count == 0
                    else "heldout_contracted_survivor_fiber"
                    if eliminated > 0
                    else "heldout_positive_no_contraction"
                ),
                "heldout_witness_rows": list(result.heldout_witness_rows),
            }
        )

    estimable_rows = [row for row in species_results if row["estimable"]]
    witness_rows = [
        witness
        for row in estimable_rows
        for witness in row["heldout_witness_rows"]
    ]

    return {
        "schema": "eog.bam_sweden_riverbarrier_external_bridge.result.v1",
        "status": "completed_retrospective_external_M_bridge",
        "scientific_role": (
            "retrospective_external_M_subfamily_bridge_not_fresh_confirmatory_evidence"
        ),
        "world_count": 9,
        "distance_thresholds": [
            {"level": level, "distance": value}
            for level, value in thresholds
        ],
        "species_results": species_results,
        "estimable_species_count": len(estimable_rows),
        "species_with_any_heldout_contraction": sum(
            (row["heldout_eliminated_world_count"] or 0) > 0
            for row in estimable_rows
        ),
        "species_with_complete_heldout_falsification": sum(
            row["status"] == "heldout_falsified_all_calibration_worlds"
            for row in estimable_rows
        ),
        "species_retaining_multiple_worlds_after_all_positive_evidence": sum(
            row["final_survivor_world_count"] > 1
            for row in estimable_rows
        ),
        "heldout_positive_witness_count": len(witness_rows),
        "witnesses_eliminating_at_least_one_world": sum(
            int(row["individually_eliminated_world_count"]) > 0
            for row in witness_rows
        ),
        "claim_boundary": [
            "A and B are unrestricted; this is an empirical M-only bridge",
            "only positive density records are hard ecological witnesses",
            "zero density is not interpreted as biological absence",
            "world contraction is not a causal barrier-effect estimate",
            "published synchrony results are not endpoints",
            "this retrospective bridge is not fresh confirmatory evidence",
        ],
    }
