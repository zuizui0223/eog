"""Response-free replay of the historical Algar coordinate-registry STOP.

The three coordinates below are copied from the immutable response-independent
deployments.csv identified by the frozen Algar endpoint contract:

repository: WildCoLab/Introduction-to-Camera-Trap-Data-Management-and-Analysis-in-R
commit: 6b4170abbad9f7f7762ef6874e1246b28000f371
path: data/raw_data/example_data/deployments.csv
Git blob SHA-1: 0c178f132fedbc9b4e1d9eae842ff5c3a816cfaf

No images.csv bytes or biological responses are used.
"""

from __future__ import annotations

import json
import math

from eog.v2.coordinate_registry import (
    CoordinateObservation,
    CoordinateRegistryPolicy,
    audit_coordinate_registry,
)


ALG069 = (
    CoordinateObservation("ALG069", -113.5075, 56.49351647),
    CoordinateObservation("ALG069", -112.5074726, 56.49351647),
    CoordinateObservation("ALG069", -112.5074726, 56.49351647),
)
FROZEN_TOLERANCE_DEGREES = 1e-9
SOURCE_GIT_BLOB_SHA1 = "0c178f132fedbc9b4e1d9eae842ff5c3a816cfaf"


def _haversine_km(left: CoordinateObservation, right: CoordinateObservation) -> float:
    radius_km = 6371.0088
    phi1, phi2 = math.radians(left.y), math.radians(right.y)
    dphi = phi2 - phi1
    dlambda = math.radians(right.x - left.x)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius_km * math.asin(math.sqrt(min(1.0, max(0.0, a))))


def _passes(tolerance: float) -> bool:
    try:
        audit_coordinate_registry(
            ALG069,
            CoordinateRegistryPolicy(
                tolerance=tolerance,
                units="decimal_degrees",
                representative_policy="median",
            ),
        )
    except ValueError:
        return False
    return True


def run_replay() -> dict[str, object]:
    x_values = [row.x for row in ALG069]
    y_values = [row.y for row in ALG069]
    required_axis_tolerance = max(max(x_values) - min(x_values), max(y_values) - min(y_values))
    displacement_km = _haversine_km(ALG069[0], ALG069[1])

    original_pass = _passes(FROZEN_TOLERANCE_DEGREES)
    moderate_pass = _passes(0.01)
    required_pass = _passes(required_axis_tolerance)

    if original_pass:
        raise AssertionError("historical 1e-9-degree Algar policy unexpectedly passes")
    if moderate_pass:
        raise AssertionError("0.01-degree tolerance unexpectedly rescues ALG069")
    if not required_pass:
        raise AssertionError("exact required full-span tolerance must pass by construction")

    return {
        "schema": "eog.algar_coordinate_contract_replay.v1",
        "uses_biological_response": False,
        "reruns_frozen_endpoint": False,
        "counts_as_predictive_evidence": False,
        "source_git_blob_sha1": SOURCE_GIT_BLOB_SHA1,
        "node_id": "ALG069",
        "frozen_tolerance_degrees": FROZEN_TOLERANCE_DEGREES,
        "longitude_span_degrees": float(max(x_values) - min(x_values)),
        "latitude_span_degrees": float(max(y_values) - min(y_values)),
        "first_to_second_displacement_km": float(displacement_km),
        "passes_frozen_tolerance": original_pass,
        "passes_0_01_degree_tolerance": moderate_pass,
        "minimum_axis_tolerance_to_accept_degrees": float(required_axis_tolerance),
        "passes_at_exact_minimum_axis_tolerance": required_pass,
        "classification": "large_registry_discontinuity_not_interface_noise",
        "interpretation": (
            "A generic tolerance policy should not automatically rescue the historical "
            "Algar stop: accepting ALG069 requires roughly one degree of longitude "
            "relaxation, far beyond a small coordinate-rounding discrepancy."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_replay(), indent=2, sort_keys=True))
