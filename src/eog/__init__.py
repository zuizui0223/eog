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
from .reference_policy import (
    ReferenceDeclaration,
    allowed_claim_scope,
    validate_reference_declaration,
)
from .uncertainty import ComparativeContrast, compare_geometry, reference_fingerprint

__all__ = [
    "OccupancyGeometry",
    "RobustReference",
    "ReferenceDeclaration",
    "ComparativeContrast",
    "robust_scale",
    "fit_robust_reference",
    "transform_with_reference",
    "reference_fingerprint",
    "compare_geometry",
    "pairwise_distances",
    "minimum_spanning_tree",
    "infer_occupancy_geometry",
    "infer_comparative_geometry",
    "validate_reference_declaration",
    "allowed_claim_scope",
    "project_states",
]

__version__ = "0.1.0"
