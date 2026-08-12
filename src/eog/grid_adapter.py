"""Regular-grid adapters for EOG distribution modelling.

The core EOG graph API is intentionally point/patch based. This module provides a
small NumPy-only bridge from raster-like grids to deterministic :class:`BridgeNode`
objects and back again, so distribution predictions can occupy the same practical
workflow position as an SDM map without making rasterio a core dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .bridge_builder import BridgeNode
from .distribution import EOGDistributionPrediction


@dataclass(frozen=True)
class RegularGridNodeIndex:
    """Deterministic mapping between available grid cells and EOG node IDs."""

    shape: tuple[int, int]
    node_ids: tuple[str, ...]
    cells: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        if len(self.shape) != 2 or self.shape[0] <= 0 or self.shape[1] <= 0:
            raise ValueError("shape must contain two positive dimensions")
        if len(self.node_ids) != len(self.cells):
            raise ValueError("node_ids and cells must have equal length")
        if len(set(self.node_ids)) != len(self.node_ids):
            raise ValueError("grid node IDs must be unique")
        if len(set(self.cells)) != len(self.cells):
            raise ValueError("grid cells must be unique")
        for row, column in self.cells:
            if not (0 <= row < self.shape[0] and 0 <= column < self.shape[1]):
                raise ValueError("grid cell is outside declared shape")

    def node_id_at(self, row: int, column: int) -> str:
        """Return the node ID for an available cell."""
        cell = (int(row), int(column))
        try:
            position = self.cells.index(cell)
        except ValueError as exc:
            raise KeyError(f"cell is unavailable or outside the node index: {cell}") from exc
        return self.node_ids[position]

    def values_to_grid(
        self,
        values: Sequence[float] | np.ndarray,
        *,
        fill_value: float = np.nan,
    ) -> np.ndarray:
        """Restore node-aligned numeric values to a 2D grid."""
        array = np.asarray(values, dtype=float)
        if array.ndim != 1 or array.size != len(self.node_ids):
            raise ValueError("values must be one-dimensional and align with grid node IDs")
        grid = np.full(self.shape, float(fill_value), dtype=float)
        for value, cell in zip(array, self.cells):
            grid[cell] = float(value)
        return grid


def _coordinate_grid(
    latitude: np.ndarray,
    longitude: np.ndarray,
    shape: tuple[int, int],
) -> tuple[np.ndarray, np.ndarray]:
    lat = np.asarray(latitude, dtype=float)
    lon = np.asarray(longitude, dtype=float)
    if lat.ndim == 1 and lon.ndim == 1:
        if lat.size != shape[0] or lon.size != shape[1]:
            raise ValueError("1D latitude/longitude lengths must match grid rows/columns")
        lat_grid = np.repeat(lat[:, None], shape[1], axis=1)
        lon_grid = np.repeat(lon[None, :], shape[0], axis=0)
        return lat_grid, lon_grid
    if lat.shape == shape and lon.shape == shape:
        return lat, lon
    raise ValueError(
        "latitude/longitude must both be 1D row/column coordinates or 2D grid arrays"
    )


def _feature_cube(
    environmental_predictors: np.ndarray,
) -> tuple[np.ndarray, tuple[int, int]]:
    values = np.asarray(environmental_predictors, dtype=float)
    if values.ndim == 2:
        return values[:, :, None], (int(values.shape[0]), int(values.shape[1]))
    if values.ndim == 3 and values.shape[2] >= 1:
        return values, (int(values.shape[0]), int(values.shape[1]))
    raise ValueError(
        "environmental_predictors must have shape (rows, cols) or (rows, cols, features)"
    )


def build_regular_grid_nodes(
    latitude: np.ndarray,
    longitude: np.ndarray,
    environmental_predictors: np.ndarray,
    *,
    available_mask: np.ndarray | None = None,
    node_prefix: str = "cell",
) -> tuple[tuple[BridgeNode, ...], RegularGridNodeIndex]:
    """Convert an available regular grid into deterministic EOG nodes.

    ``available_mask`` uses ``True`` for cells that may participate in the EOG graph.
    Coordinates and predictors on unavailable cells are ignored; available cells must
    contain finite coordinates and feature values.
    """
    prefix = str(node_prefix).strip()
    if not prefix:
        raise ValueError("node_prefix must be non-empty")
    features, shape = _feature_cube(environmental_predictors)
    lat_grid, lon_grid = _coordinate_grid(latitude, longitude, shape)
    if available_mask is None:
        mask = np.ones(shape, dtype=bool)
    else:
        mask = np.asarray(available_mask, dtype=bool)
        if mask.shape != shape:
            raise ValueError("available_mask shape must match environmental grid")
    if not mask.any():
        raise ValueError("available_mask contains no available cells")

    available_features = features[mask]
    if not np.isfinite(available_features).all():
        raise ValueError("available environmental predictors must be finite")
    if not np.isfinite(lat_grid[mask]).all() or not np.isfinite(lon_grid[mask]).all():
        raise ValueError("available grid coordinates must be finite")
    if np.any((lat_grid[mask] < -90.0) | (lat_grid[mask] > 90.0)):
        raise ValueError("available latitude values are outside [-90, 90]")
    if np.any((lon_grid[mask] < -180.0) | (lon_grid[mask] > 180.0)):
        raise ValueError("available longitude values are outside [-180, 180]")

    nodes: list[BridgeNode] = []
    node_ids: list[str] = []
    cells: list[tuple[int, int]] = []
    for row, column in np.argwhere(mask):
        row_i, column_i = int(row), int(column)
        node_id = f"{prefix}_r{row_i:04d}c{column_i:04d}"
        nodes.append(
            BridgeNode(
                node_id=node_id,
                latitude=float(lat_grid[row_i, column_i]),
                longitude=float(lon_grid[row_i, column_i]),
                environmental_state=tuple(
                    float(value) for value in features[row_i, column_i, :]
                ),
            )
        )
        node_ids.append(node_id)
        cells.append((row_i, column_i))

    index = RegularGridNodeIndex(
        shape=shape,
        node_ids=tuple(node_ids),
        cells=tuple(cells),
    )
    return tuple(nodes), index


def prediction_field_to_grid(
    prediction: EOGDistributionPrediction,
    grid_index: RegularGridNodeIndex,
    *,
    field: str = "distribution_support",
    fill_value: float = np.nan,
) -> np.ndarray:
    """Project one EOG prediction field back to its declared regular grid."""
    if not hasattr(prediction, field):
        raise ValueError(f"unknown EOG prediction field: {field}")
    values = np.asarray(getattr(prediction, field), dtype=float)
    if values.ndim != 1 or values.size != len(prediction.node_ids):
        raise ValueError(f"prediction field {field} is not node-aligned")

    prediction_index = {node_id: i for i, node_id in enumerate(prediction.node_ids)}
    missing = [node_id for node_id in grid_index.node_ids if node_id not in prediction_index]
    if missing:
        raise ValueError(f"prediction is missing grid node IDs: {missing[:5]}")
    ordered = np.asarray(
        [values[prediction_index[node_id]] for node_id in grid_index.node_ids],
        dtype=float,
    )
    return grid_index.values_to_grid(ordered, fill_value=fill_value)
