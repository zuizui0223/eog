"""Graph-native serialisation for dynamic EOG-R visualisation.

This module does not draw a map. It converts a frozen operator and finite-horizon
reachability result into deterministic node/edge animation frames that can be rendered
by a web map, Plotly, GIS client, or other front end without turning EOG-R back into a
cellwise raster prediction.
"""
from __future__ import annotations

import hashlib
import json
from typing import Mapping, Sequence

import numpy as np

from .dynamic_island_reachability import DynamicReachabilityResult, DynamicTransitionOperator


def _sha256(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def build_dynamic_reachability_visualization_payload(
    operator: DynamicTransitionOperator,
    result: DynamicReachabilityResult,
    *,
    positions: Mapping[str, Sequence[float]] | None = None,
    viability: Mapping[str, float] | None = None,
    persistence: Mapping[str, float] | None = None,
    flux_tolerance: float = 0.0,
) -> dict[str, object]:
    """Return deterministic graph-native animation data.

    ``positions`` are optional two-dimensional display coordinates. They may be
    longitude/latitude, projected coordinates, or schematic graph coordinates; no CRS
    interpretation is imposed here.

    Each frame contains node reachability mass at one propagation depth and the directed
    flux that leaves those nodes toward the next frame. The final frame therefore has no
    outgoing flux. ``viability`` and ``persistence`` are optional static node layers and
    are never multiplied into the dynamic result by this serializer.
    """

    if operator.fingerprint != result.operator_fingerprint:
        raise ValueError("result and operator fingerprints do not match")
    if operator.node_ids != result.node_ids:
        raise ValueError("result and operator node IDs do not align")
    if not np.isfinite(flux_tolerance) or flux_tolerance < 0.0:
        raise ValueError("flux_tolerance must be finite and non-negative")

    ids = operator.node_ids
    index = {node_id: i for i, node_id in enumerate(ids)}

    def optional_layer(values: Mapping[str, float] | None, label: str):
        if values is None:
            return None
        extra = set(values) - set(ids)
        if extra:
            raise ValueError(f"{label} contains unknown node IDs: {sorted(extra)}")
        output = []
        for node_id in ids:
            value = None if node_id not in values else float(values[node_id])
            if value is not None and not np.isfinite(value):
                raise ValueError(f"{label} values must be finite")
            output.append(value)
        return output

    position_values: list[list[float] | None] = []
    if positions is None:
        position_values = [None for _ in ids]
    else:
        extra = set(positions) - set(ids)
        if extra:
            raise ValueError(f"positions contains unknown node IDs: {sorted(extra)}")
        for node_id in ids:
            if node_id not in positions:
                position_values.append(None)
                continue
            value = np.asarray(positions[node_id], dtype=float)
            if value.shape != (2,) or not np.isfinite(value).all():
                raise ValueError("each position must contain two finite coordinates")
            position_values.append([float(value[0]), float(value[1])])

    viability_values = optional_layer(viability, "viability")
    persistence_values = optional_layer(persistence, "persistence")
    source_lookup = {source_id: i for i, source_id in enumerate(result.source_ids)}

    nodes = []
    for node_id in ids:
        j = index[node_id]
        attribution = {
            source_id: float(result.source_attribution[source_index, j])
            for source_id, source_index in source_lookup.items()
            if result.source_attribution[source_index, j] > 0.0
        }
        nodes.append(
            {
                "id": node_id,
                "position": position_values[j],
                "viability": None if viability_values is None else viability_values[j],
                "persistence": None if persistence_values is None else persistence_values[j],
                "first_arrival_step": None
                if int(result.first_arrival_step[j]) < 0
                else int(result.first_arrival_step[j]),
                "integrated_reachability_support": float(result.integrated_node_support[j]),
                "source_attribution": attribution,
                "is_declared_source": node_id in source_lookup,
            }
        )

    static_edges = []
    for i in range(len(ids)):
        for j in range(len(ids)):
            if operator.transition[i, j] <= 0.0:
                continue
            static_edges.append(
                {
                    "source": ids[i],
                    "target": ids[j],
                    "raw_support": float(operator.raw_support[i, j]),
                    "transition_support": float(operator.transition[i, j]),
                    "integrated_flux": float(result.integrated_edge_flux[i, j]),
                }
            )

    frames = []
    n_steps = result.mass_by_step.shape[0] - 1
    for step in range(n_steps + 1):
        mass = result.mass_by_step[step]
        frame_nodes = [
            {"id": node_id, "reachability_mass": float(mass[j])}
            for j, node_id in enumerate(ids)
        ]
        frame_edges = []
        if step < n_steps:
            flux = mass[:, None] * operator.transition
            for i in range(len(ids)):
                for j in range(len(ids)):
                    value = float(flux[i, j])
                    if value <= flux_tolerance:
                        continue
                    frame_edges.append(
                        {"source": ids[i], "target": ids[j], "flux": value}
                    )
        frames.append(
            {
                "step": int(step),
                "total_mass": float(result.total_mass_by_step[step]),
                "lost_mass_after_step": None
                if step == n_steps
                else float(result.lost_mass_by_step[step]),
                "nodes": frame_nodes,
                "edges": frame_edges,
            }
        )

    payload: dict[str, object] = {
        "schema": "eog_dynamic_reachability_graph_v1",
        "interpretation": (
            "graph-native relative reachability support by propagation depth; not a "
            "colonisation probability or calibrated time series"
        ),
        "operator_fingerprint": operator.fingerprint,
        "source_ids": list(result.source_ids),
        "source_weights": result.source_weights.tolist(),
        "nodes": nodes,
        "edges": static_edges,
        "frames": frames,
    }
    payload["fingerprint"] = _sha256(payload)
    return payload
