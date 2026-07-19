"""Environmental occupancy geometry public API."""

from .comparative import (
    RobustReference,
    fit_robust_reference,
    infer_comparative_geometry,
    transform_with_reference,
)
from .geometry import (
    OccupancyGeometry,
    infer_occupancy_geometry,
    minimum_spanning_tree,
    pairwise_distances,
    project_states,
    robust_scale,
)

__all__ = [
    "OccupancyGeometry",
    "RobustReference",
    "robust_scale",
    "fit_robust_reference",
    "transform_with_reference",
    "pairwise_distances",
    "minimum_spanning_tree",
    "infer_occupancy_geometry",
    "infer_comparative_geometry",
    "project_states",
]

__version__ = "0.1.0"
