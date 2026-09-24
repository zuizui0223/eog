"""Deterministic response-independent balanced spatial folds for EOG-WF v2.

The folds are evaluation partitions only. They are not dispersal barriers, worlds,
connectivity classes, habitat patches, or ecological process estimates.

Starting from one group containing all frozen nodes, the algorithm repeatedly splits the
largest group at its coordinate median until the requested number of groups is reached.
The split axis is the one with the larger response-independent spatial span. For lon/lat
coordinates, longitude span is multiplied by cos(mean latitude) only for choosing and
ordering the split axis; no biological scale is inferred.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Literal, Mapping, Sequence


SpatialFoldMetric = Literal["lonlat", "euclidean"]


def _sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _text(value: object, label: str) -> str:
    result = str(value).strip()
    if not result:
        raise ValueError(f"{label} must be non-empty")
    return result


@dataclass(frozen=True)
class SpatialFoldSplit:
    path: str
    node_count: int
    axis: str
    axis_span: float
    left_count: int
    right_count: int
    fingerprint: str


@dataclass(frozen=True)
class BalancedSpatialFolds:
    node_ids: tuple[str, ...]
    n_folds: int
    metric: SpatialFoldMetric
    node_to_fold: tuple[tuple[str, int], ...]
    fold_node_ids: tuple[tuple[str, ...], ...]
    fold_counts: tuple[int, ...]
    split_history: tuple[SpatialFoldSplit, ...]
    fingerprint: str

    @property
    def mapping(self) -> dict[str, int]:
        return dict(self.node_to_fold)


@dataclass(frozen=True)
class _Node:
    node_id: str
    x: float
    y: float


@dataclass(frozen=True)
class _Group:
    path: str
    nodes: tuple[_Node, ...]


def _validated_nodes(
    node_ids: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    metric: SpatialFoldMetric,
) -> tuple[_Node, ...]:
    ids = tuple(_text(value, "node_id") for value in node_ids)
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("node_ids must be non-empty and unique")
    if set(coordinates) != set(ids):
        raise ValueError("coordinate keys must exactly equal node_ids")
    if metric not in {"lonlat", "euclidean"}:
        raise ValueError("metric must be lonlat or euclidean")

    result: list[_Node] = []
    for node_id in ids:
        pair = coordinates[node_id]
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("coordinates must contain x/y tuples")
        x = float(pair[0])
        y = float(pair[1])
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("coordinates must be finite")
        if metric == "lonlat":
            if not -180.0 <= x <= 180.0:
                raise ValueError("longitude must lie in [-180, 180]")
            if not -90.0 <= y <= 90.0:
                raise ValueError("latitude must lie in [-90, 90]")
        result.append(_Node(node_id=node_id, x=x, y=y))
    return tuple(result)


def _axis_values(
    nodes: tuple[_Node, ...],
    metric: SpatialFoldMetric,
) -> tuple[str, dict[str, tuple[float, float]], float]:
    if metric == "lonlat":
        mean_lat = sum(node.y for node in nodes) / len(nodes)
        lon_scale = math.cos(math.radians(mean_lat))
    else:
        lon_scale = 1.0

    values = {
        node.node_id: (node.x * lon_scale, node.y)
        for node in nodes
    }
    xs = [value[0] for value in values.values()]
    ys = [value[1] for value in values.values()]
    x_span = max(xs) - min(xs)
    y_span = max(ys) - min(ys)

    # x wins exact ties so the rule remains deterministic.
    if x_span >= y_span:
        return "x", values, float(x_span)
    return "y", values, float(y_span)


def _split_group(
    group: _Group,
    metric: SpatialFoldMetric,
) -> tuple[_Group, _Group, SpatialFoldSplit]:
    if len(group.nodes) < 2:
        raise ValueError("cannot split a one-node spatial group")

    axis, values, span = _axis_values(group.nodes, metric)
    primary_index = 0 if axis == "x" else 1
    secondary_index = 1 - primary_index
    ordered = tuple(
        sorted(
            group.nodes,
            key=lambda node: (
                values[node.node_id][primary_index],
                values[node.node_id][secondary_index],
                node.node_id,
            ),
        )
    )
    cut = len(ordered) // 2
    if cut <= 0 or cut >= len(ordered):
        raise RuntimeError("balanced spatial split produced an empty child group")
    left = _Group(path=group.path + "0", nodes=ordered[:cut])
    right = _Group(path=group.path + "1", nodes=ordered[cut:])

    payload = {
        "path": group.path,
        "node_ids": [node.node_id for node in ordered],
        "axis": axis,
        "axis_span": span,
        "left_node_ids": [node.node_id for node in left.nodes],
        "right_node_ids": [node.node_id for node in right.nodes],
    }
    audit = SpatialFoldSplit(
        path=group.path,
        node_count=len(group.nodes),
        axis=axis,
        axis_span=span,
        left_count=len(left.nodes),
        right_count=len(right.nodes),
        fingerprint=_sha256(payload),
    )
    return left, right, audit


def build_balanced_spatial_folds(
    node_ids: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    *,
    n_folds: int,
    metric: SpatialFoldMetric = "lonlat",
) -> BalancedSpatialFolds:
    """Freeze balanced coordinate-only evaluation folds.

    The result uses no biological response, effort outcome, world support, Layer-B state,
    taxon identity, or predictive score.
    """

    nodes = _validated_nodes(node_ids, coordinates, metric)
    if isinstance(n_folds, bool) or not isinstance(n_folds, int):
        raise TypeError("n_folds must be int")
    if n_folds < 2 or n_folds > len(nodes):
        raise ValueError("n_folds must lie between 2 and node count")

    groups: list[_Group] = [_Group(path="", nodes=nodes)]
    history: list[SpatialFoldSplit] = []

    while len(groups) < n_folds:
        splittable = [
            (index, group)
            for index, group in enumerate(groups)
            if len(group.nodes) >= 2
        ]
        if not splittable:
            raise RuntimeError("not enough splittable groups to reach requested n_folds")

        # Split the largest current group. Ties go to the lexicographically earlier
        # binary path, yielding deterministic balanced recursion.
        index, group = min(
            splittable,
            key=lambda item: (-len(item[1].nodes), item[1].path),
        )
        left, right, audit = _split_group(group, metric)
        history.append(audit)
        groups[index : index + 1] = [left, right]

    groups = sorted(groups, key=lambda group: group.path)
    fold_node_ids = tuple(
        tuple(sorted(node.node_id for node in group.nodes))
        for group in groups
    )
    node_to_fold = tuple(
        sorted(
            (
                node_id,
                fold_index,
            )
            for fold_index, ids in enumerate(fold_node_ids, start=1)
            for node_id in ids
        )
    )
    fold_counts = tuple(len(ids) for ids in fold_node_ids)
    if max(fold_counts) - min(fold_counts) > 1:
        raise RuntimeError("balanced recursive split produced fold sizes differing by >1")

    payload = {
        "schema": "eog.balanced_spatial_folds.v1",
        "node_ids": list(tuple(node_id for node_id, _ in node_to_fold)),
        "n_folds": n_folds,
        "metric": metric,
        "node_to_fold": [list(value) for value in node_to_fold],
        "fold_node_ids": [list(value) for value in fold_node_ids],
        "fold_counts": list(fold_counts),
        "split_history": [
            {
                "path": item.path,
                "node_count": item.node_count,
                "axis": item.axis,
                "axis_span": item.axis_span,
                "left_count": item.left_count,
                "right_count": item.right_count,
                "fingerprint": item.fingerprint,
            }
            for item in history
        ],
        "ecological_interpretation": (
            "evaluation partition only; folds are not ecological connectivity units"
        ),
        "response_used": False,
    }
    return BalancedSpatialFolds(
        node_ids=tuple(node_id for node_id, _ in node_to_fold),
        n_folds=n_folds,
        metric=metric,
        node_to_fold=node_to_fold,
        fold_node_ids=fold_node_ids,
        fold_counts=fold_counts,
        split_history=tuple(history),
        fingerprint=_sha256(payload),
    )
