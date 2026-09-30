"""Frozen A/M external-bridge engine for the Great Lakes low-head-dam dataset.

This module contains no source-download code.  It operates on already parsed tabular
frames after the source and parser gates have been satisfied.

Primary empirical scope is G = A ∩ M with B unrestricted.  Calibration positives serve
as environmental support anchors and known movement sources.  Heldout positives are
strict ecological witnesses that may falsify frozen tolerance/barrier/horizon worlds.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


HABITAT_FIELDS = (
    "width",
    "max_depth",
    "prop_clay",
    "prop_silt",
    "prop_sand",
    "prop_gravel",
    "prop_boulder",
)
HABITAT_KEY = (
    "period",
    "pair_id",
    "Stream.Name",
    "barrier",
    "position",
    "segment",
)
CATCH_REQUIRED = (
    "pair_id",
    "Year",
    "Stream.Name",
    "barrier",
    "position",
    "segment",
    "survey_length",
    "species",
    "total_caught",
    "period",
)
A_LEVELS = ("q25", "q50", "q75", "q90", "open")
M_LEVELS = (
    "barrier_closed_h1",
    "barrier_closed_h2",
    "barrier_closed_h5",
    "barrier_open_h1",
    "barrier_open_h2",
    "barrier_open_h5",
    "open_all",
)


class BridgeSchemaStop(RuntimeError):
    pass


@dataclass(frozen=True, order=True)
class PhysicalNode:
    pair_id: str
    stream_name: str
    position: str
    segment: int

    @property
    def node_id(self) -> str:
        return (
            f"{self.pair_id}|{self.stream_name}|"
            f"{self.position}|{self.segment}"
        )


@dataclass(frozen=True)
class HabitatScaling:
    median: tuple[float, ...]
    iqr: tuple[float, ...]
    thresholds: tuple[tuple[str, float], ...]

    def threshold(self, level: str) -> float:
        if level == "open":
            return float("inf")
        mapping = dict(self.thresholds)
        if level not in mapping:
            raise ValueError(f"unknown A level: {level}")
        return float(mapping[level])


@dataclass(frozen=True)
class AMWorld:
    world_id: str
    A_level: str
    M_level: str


@dataclass(frozen=True)
class SpeciesBridgeResult:
    species: str
    calibration_positive_nodes: tuple[str, ...]
    heldout_positive_nodes: tuple[str, ...]
    calibration_world_ids: tuple[str, ...]
    final_survivor_world_ids: tuple[str, ...]
    heldout_witness_rows: tuple[dict[str, object], ...]


def _canonical_period(value: object) -> str:
    text = str(value).strip()
    if text == "90s":
        return "90s"
    if text == "2023" or text == "2023.0":
        return "2023"
    raise BridgeSchemaStop(f"unsupported period value: {value!r}")


def _canonical_barrier(value: object) -> int:
    if isinstance(value, (bool, np.bool_)):
        return int(bool(value))
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeSchemaStop(f"invalid barrier value: {value!r}") from exc
    if numeric not in (0.0, 1.0):
        raise BridgeSchemaStop(f"barrier must be 0/1, got {value!r}")
    return int(numeric)


def _canonical_segment(value: object) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise BridgeSchemaStop(f"invalid segment: {value!r}") from exc
    if not np.isfinite(numeric) or numeric < 1 or not numeric.is_integer():
        raise BridgeSchemaStop(f"segment must be positive integer, got {value!r}")
    return int(numeric)


def _canonical_position(value: object) -> str:
    text = str(value).strip().lower()
    if text not in {"upstream", "downstream"}:
        raise BridgeSchemaStop(
            f"position must be upstream/downstream, got {value!r}"
        )
    return text


def _canonical_pair_id(value: object) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        raise BridgeSchemaStop(f"invalid pair_id: {value!r}")
    return text


def _canonical_stream(value: object) -> str:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        raise BridgeSchemaStop(f"invalid Stream.Name: {value!r}")
    return text


def _physical_node_from_row(row: Mapping[str, object]) -> PhysicalNode:
    return PhysicalNode(
        pair_id=_canonical_pair_id(row["pair_id"]),
        stream_name=_canonical_stream(row["Stream.Name"]),
        position=_canonical_position(row["position"]),
        segment=_canonical_segment(row["segment"]),
    )


def validate_habitat_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = set(HABITAT_KEY) | set(HABITAT_FIELDS)
    missing = required.difference(frame.columns)
    if missing:
        raise BridgeSchemaStop(f"habitat columns missing: {sorted(missing)}")

    rows = frame.copy()
    rows["period"] = rows["period"].map(_canonical_period)
    rows["pair_id"] = rows["pair_id"].map(_canonical_pair_id)
    rows["Stream.Name"] = rows["Stream.Name"].map(_canonical_stream)
    rows["barrier"] = rows["barrier"].map(_canonical_barrier)
    rows["position"] = rows["position"].map(_canonical_position)
    rows["segment"] = rows["segment"].map(_canonical_segment)

    for field in HABITAT_FIELDS:
        values = pd.to_numeric(rows[field], errors="coerce")
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            raise BridgeSchemaStop(f"habitat field {field} contains nonfinite values")
        rows[field] = values.astype(float)

    if rows.duplicated(list(HABITAT_KEY)).any():
        raise BridgeSchemaStop("duplicate habitat join key")

    return rows


def validate_catch_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(CATCH_REQUIRED).difference(frame.columns)
    if missing:
        raise BridgeSchemaStop(f"catch columns missing: {sorted(missing)}")

    rows = frame.copy()
    rows["period"] = rows["period"].map(_canonical_period)
    rows["pair_id"] = rows["pair_id"].map(_canonical_pair_id)
    rows["Stream.Name"] = rows["Stream.Name"].map(_canonical_stream)
    rows["barrier"] = rows["barrier"].map(_canonical_barrier)
    rows["position"] = rows["position"].map(_canonical_position)
    rows["segment"] = rows["segment"].map(_canonical_segment)

    species = rows["species"].map(lambda x: str(x).strip())
    if species.eq("").any() or species.str.lower().isin({"nan", "none"}).any():
        raise BridgeSchemaStop("catch table contains empty species value")
    rows["species"] = species

    total = pd.to_numeric(rows["total_caught"], errors="coerce")
    if total.isna().any() or (total < 0).any() or not np.isfinite(total).all():
        raise BridgeSchemaStop("total_caught must be finite and nonnegative")
    rows["total_caught"] = total.astype(float)

    length = pd.to_numeric(rows["survey_length"], errors="coerce")
    if length.isna().any() or (length <= 0).any() or not np.isfinite(length).all():
        raise BridgeSchemaStop("survey_length must be finite and positive")
    rows["survey_length"] = length.astype(float)

    year = pd.to_numeric(rows["Year"], errors="coerce")
    if year.isna().any() or not np.isfinite(year).all():
        raise BridgeSchemaStop("Year must be finite numeric")
    if not np.all(np.equal(year, np.floor(year))):
        raise BridgeSchemaStop("Year must be integer-valued")
    rows["Year"] = year.astype(int)

    species_key = [
        "period",
        "pair_id",
        "Stream.Name",
        "barrier",
        "position",
        "segment",
        "species",
    ]
    if rows.duplicated(species_key).any():
        raise BridgeSchemaStop("duplicate species-node-period catch row")

    return rows


def join_catch_to_habitat(
    catch: pd.DataFrame,
    habitat: pd.DataFrame,
) -> pd.DataFrame:
    c = validate_catch_frame(catch)
    h = validate_habitat_frame(habitat)
    joined = c.merge(
        h,
        how="left",
        on=list(HABITAT_KEY),
        validate="many_to_one",
        indicator=True,
    )
    if not joined["_merge"].eq("both").all():
        missing = joined.loc[joined["_merge"] != "both", list(HABITAT_KEY)]
        raise BridgeSchemaStop(
            f"catch rows missing habitat matches: {missing.head(5).to_dict('records')}"
        )
    return joined.drop(columns=["_merge"])


def fit_habitat_scaling(habitat: pd.DataFrame) -> HabitatScaling:
    h = validate_habitat_frame(habitat)
    calibration = h.loc[h["period"] == "90s", list(HABITAT_FIELDS)]
    if len(calibration) < 2:
        raise BridgeSchemaStop("need at least two 90s habitat nodes")

    matrix = calibration.to_numpy(dtype=float)
    med = np.median(matrix, axis=0)
    q25 = np.quantile(matrix, 0.25, axis=0, method="linear")
    q75 = np.quantile(matrix, 0.75, axis=0, method="linear")
    iqr = q75 - q25
    if not np.isfinite(iqr).all() or np.any(iqr <= 0.0):
        bad = [HABITAT_FIELDS[i] for i, value in enumerate(iqr) if value <= 0.0]
        raise BridgeSchemaStop(f"zero/nonpositive 90s habitat IQR: {bad}")

    scaled = (matrix - med) / iqr
    distances: list[float] = []
    for i in range(len(scaled)):
        for j in range(i + 1, len(scaled)):
            distances.append(float(np.max(np.abs(scaled[i] - scaled[j]))))
    if not distances:
        raise BridgeSchemaStop("empty habitat threshold population")

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
    if any((not np.isfinite(value)) or value < 0.0 for _, value in thresholds):
        raise BridgeSchemaStop("invalid habitat distance threshold")

    return HabitatScaling(
        median=tuple(float(x) for x in med),
        iqr=tuple(float(x) for x in iqr),
        thresholds=thresholds,
    )


def scaled_habitat(
    rows: pd.DataFrame,
    scaling: HabitatScaling,
) -> np.ndarray:
    matrix = rows.loc[:, HABITAT_FIELDS].to_numpy(dtype=float)
    med = np.asarray(scaling.median, dtype=float)
    iqr = np.asarray(scaling.iqr, dtype=float)
    return (matrix - med) / iqr


def habitat_support_by_node(
    joined: pd.DataFrame,
    species: str,
    scaling: HabitatScaling,
    A_level: str,
    target_period: str,
) -> dict[str, bool]:
    period = _canonical_period(target_period)
    threshold = scaling.threshold(A_level)

    calibration = joined.loc[
        (joined["period"] == "90s")
        & (joined["species"] == species)
        & (joined["total_caught"] > 0)
    ]
    if calibration.empty:
        raise BridgeSchemaStop(f"species {species!r} has no 90s positive anchors")

    anchor_nodes = calibration.drop_duplicates(
        ["pair_id", "Stream.Name", "position", "segment"]
    )
    anchor_scaled = scaled_habitat(anchor_nodes, scaling)

    target = (
        joined.loc[joined["period"] == period]
        .drop_duplicates(list(HABITAT_KEY))
        .copy()
    )
    target_scaled = scaled_habitat(target, scaling)
    result: dict[str, bool] = {}
    for row_values, vector in zip(
        target.to_dict("records"),
        target_scaled,
        strict=True,
    ):
        node_id = _physical_node_from_row(row_values).node_id
        if A_level == "open":
            result[node_id] = True
        else:
            d = np.max(np.abs(anchor_scaled - vector), axis=1)
            result[node_id] = bool(np.min(d) <= threshold + 1e-12)
    return result


def _union_node_registry(
    habitat: pd.DataFrame,
) -> dict[str, PhysicalNode]:
    h = validate_habitat_frame(habitat)
    registry: dict[str, PhysicalNode] = {}
    for row in h.to_dict("records"):
        node = _physical_node_from_row(row)
        incumbent = registry.get(node.node_id)
        if incumbent is not None and incumbent != node:
            raise BridgeSchemaStop(f"physical node identity drift: {node.node_id}")
        registry[node.node_id] = node
    return registry


def _stream_barrier_state(
    habitat: pd.DataFrame,
    period: str,
) -> dict[tuple[str, str], int]:
    h = validate_habitat_frame(habitat)
    p = _canonical_period(period)
    subset = h.loc[h["period"] == p]
    states: dict[tuple[str, str], int] = {}
    for (pair_id, stream_name), rows in subset.groupby(
        ["pair_id", "Stream.Name"],
        sort=True,
    ):
        values = sorted(set(int(value) for value in rows["barrier"]))
        if len(values) != 1:
            raise BridgeSchemaStop(
                f"barrier state varies within stream-period: {pair_id}|{stream_name}|{p}"
            )
        states[(str(pair_id), str(stream_name))] = values[0]
    return states


def build_period_graph(
    habitat: pd.DataFrame,
    period: str,
    *,
    barrier_open: bool,
) -> dict[str, frozenset[str]]:
    # Physical topology is the union of all sampled nodes across periods.  A site is
    # not removed from the movement graph merely because it was not sampled in the
    # target period.
    registry = _union_node_registry(habitat)
    barrier_state = _stream_barrier_state(habitat, period)
    adjacency: dict[str, set[str]] = {node_id: set() for node_id in registry}

    by_stream_position: dict[tuple[str, str, str], list[PhysicalNode]] = {}
    for node in registry.values():
        by_stream_position.setdefault(
            (node.pair_id, node.stream_name, node.position),
            [],
        ).append(node)

    for nodes in by_stream_position.values():
        by_segment = {node.segment: node for node in nodes}
        if len(by_segment) != len(nodes):
            raise BridgeSchemaStop("duplicate segment in physical stream-side topology")
        for segment, node in by_segment.items():
            nxt = by_segment.get(segment + 1)
            if nxt is not None:
                adjacency[node.node_id].add(nxt.node_id)
                adjacency[nxt.node_id].add(node.node_id)

    stream_keys = {
        (node.pair_id, node.stream_name)
        for node in registry.values()
    }
    for pair_id, stream_name in stream_keys:
        up_id = PhysicalNode(pair_id, stream_name, "upstream", 1).node_id
        down_id = PhysicalNode(pair_id, stream_name, "downstream", 1).node_id
        if up_id not in registry or down_id not in registry:
            continue

        key = (pair_id, stream_name)
        if key not in barrier_state:
            raise BridgeSchemaStop(
                f"stream lacks target-period barrier state: {pair_id}|{stream_name}|{period}"
            )
        barrier = barrier_state[key]
        if barrier == 0 or barrier_open:
            adjacency[up_id].add(down_id)
            adjacency[down_id].add(up_id)

    return {
        node_id: frozenset(sorted(neighbours))
        for node_id, neighbours in sorted(adjacency.items())
    }


def graph_reachable(
    graph: Mapping[str, Sequence[str]],
    sources: Iterable[str],
    horizon: int | None,
) -> frozenset[str]:
    source_ids = tuple(sorted(set(str(value) for value in sources)))
    if not source_ids:
        return frozenset()
    unknown = set(source_ids).difference(graph)
    if unknown:
        raise BridgeSchemaStop(f"movement source absent from graph: {sorted(unknown)}")

    distance = {source: 0 for source in source_ids}
    queue = deque(source_ids)
    while queue:
        node = queue.popleft()
        step = distance[node]
        if horizon is not None and step >= horizon:
            continue
        for nxt in graph[node]:
            if nxt not in distance:
                distance[nxt] = step + 1
                queue.append(nxt)
    return frozenset(distance)


def movement_support_by_node(
    habitat: pd.DataFrame,
    calibration_positive_nodes: Sequence[str],
    M_level: str,
    target_period: str,
) -> dict[str, bool]:
    if M_level not in M_LEVELS:
        raise ValueError(f"unknown M level: {M_level}")
    if M_level == "open_all":
        barrier_open = True
        horizon = None
    else:
        barrier_open = M_level.startswith("barrier_open_")
        horizon_text = M_level.rsplit("h", 1)[1]
        horizon = int(horizon_text)

    graph = build_period_graph(
        habitat,
        target_period,
        barrier_open=barrier_open,
    )
    present_sources = [source for source in calibration_positive_nodes if source in graph]
    reachable = graph_reachable(graph, present_sources, horizon)
    return {node_id: node_id in reachable for node_id in graph}


def all_worlds() -> tuple[AMWorld, ...]:
    rows = tuple(
        AMWorld(
            world_id=f"A_{a}|M_{m}",
            A_level=a,
            M_level=m,
        )
        for a in A_LEVELS
        for m in M_LEVELS
    )
    if len(rows) != 35:
        raise RuntimeError("frozen A/M product must contain exactly 35 worlds")
    return rows


def calibration_positive_nodes(joined: pd.DataFrame, species: str) -> tuple[str, ...]:
    rows = joined.loc[
        (joined["period"] == "90s")
        & (joined["species"] == species)
        & (joined["total_caught"] > 0)
    ]
    node_ids = tuple(
        sorted(
            {
                _physical_node_from_row(row).node_id
                for row in rows.to_dict("records")
            }
        )
    )
    return node_ids


def heldout_positive_nodes(joined: pd.DataFrame, species: str) -> tuple[str, ...]:
    rows = joined.loc[
        (joined["period"] == "2023")
        & (joined["species"] == species)
        & (joined["total_caught"] > 0)
    ]
    return tuple(
        sorted(
            {
                _physical_node_from_row(row).node_id
                for row in rows.to_dict("records")
            }
        )
    )


def calibration_species(joined: pd.DataFrame) -> tuple[str, ...]:
    species = []
    for name in sorted(set(joined["species"])):
        if len(calibration_positive_nodes(joined, name)) >= 2:
            species.append(name)
    return tuple(species)


def evaluate_species(
    joined: pd.DataFrame,
    habitat: pd.DataFrame,
    scaling: HabitatScaling,
    species: str,
) -> SpeciesBridgeResult:
    calibration_nodes = calibration_positive_nodes(joined, species)
    if len(calibration_nodes) < 2:
        raise BridgeSchemaStop(
            f"species {species!r} has fewer than two calibration positive nodes"
        )
    heldout_nodes = heldout_positive_nodes(joined, species)

    worlds = all_worlds()

    # By construction calibration positives are A anchors and M sources, but audit the
    # invariant rather than assuming it.
    calibration_survivors: list[AMWorld] = []
    for world in worlds:
        a = habitat_support_by_node(
            joined, species, scaling, world.A_level, "90s"
        )
        m = movement_support_by_node(
            habitat, calibration_nodes, world.M_level, "90s"
        )
        if all(a.get(node, False) and m.get(node, False) for node in calibration_nodes):
            calibration_survivors.append(world)

    witness_rows = []
    active = {world.world_id: world for world in calibration_survivors}
    for node_id in heldout_nodes:
        eliminated = []
        by_axis = {"A": 0, "M": 0, "AM": 0}
        for world_id, world in tuple(active.items()):
            a = habitat_support_by_node(
                joined, species, scaling, world.A_level, "2023"
            )
            m = movement_support_by_node(
                habitat, calibration_nodes, world.M_level, "2023"
            )
            a_ok = bool(a.get(node_id, False))
            m_ok = bool(m.get(node_id, False))
            if a_ok and m_ok:
                continue
            eliminated.append(world_id)
            if not a_ok and not m_ok:
                by_axis["AM"] += 1
            elif not a_ok:
                by_axis["A"] += 1
            else:
                by_axis["M"] += 1

        for world_id in eliminated:
            active.pop(world_id, None)
        witness_rows.append(
            {
                "node_id": node_id,
                "survivors_before": len(active) + len(eliminated),
                "eliminated_world_count": len(eliminated),
                "eliminated_by_axis": by_axis,
                "survivors_after": len(active),
            }
        )

    return SpeciesBridgeResult(
        species=species,
        calibration_positive_nodes=calibration_nodes,
        heldout_positive_nodes=heldout_nodes,
        calibration_world_ids=tuple(
            sorted(world.world_id for world in calibration_survivors)
        ),
        final_survivor_world_ids=tuple(sorted(active)),
        heldout_witness_rows=tuple(witness_rows),
    )
