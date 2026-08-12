"""Build a fixed continental-mainland distance baseline for A-Islands centroids.

The mainland ring is frozen independently of species outcomes by
``fetch_natural_earth_australia_mainland.py``.  Distances are minimum spherical
point-to-minor-great-circle-segment distances, not nearest-vertex approximations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


EARTH_RADIUS_KM = 6371.0088


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unit_vectors(longitude_deg: np.ndarray, latitude_deg: np.ndarray) -> np.ndarray:
    lon = np.radians(np.asarray(longitude_deg, dtype=float))
    lat = np.radians(np.asarray(latitude_deg, dtype=float))
    cos_lat = np.cos(lat)
    return np.column_stack((cos_lat * np.cos(lon), cos_lat * np.sin(lon), np.sin(lat)))


def _angle_rows(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    cross = np.cross(left, right)
    numerator = np.linalg.norm(cross, axis=1)
    denominator = np.einsum("ij,ij->i", left, right)
    return np.arctan2(numerator, denominator)


def _prepare_ring_segments(ring_lonlat: np.ndarray):
    ring = np.asarray(ring_lonlat, dtype=float)
    if ring.ndim != 2 or ring.shape[1] != 2 or ring.shape[0] < 3 or not np.isfinite(ring).all():
        raise ValueError("mainland ring must be a finite N-by-2 lon/lat array")
    if not np.allclose(ring[0], ring[-1], atol=1e-12):
        ring = np.vstack((ring, ring[0]))
    vertices = _unit_vectors(ring[:, 0], ring[:, 1])
    a = vertices[:-1]
    b = vertices[1:]
    normals = np.cross(a, b)
    norm = np.linalg.norm(normals, axis=1)
    valid = norm > 1e-14
    normal_hat = np.zeros_like(normals)
    normal_hat[valid] = normals[valid] / norm[valid, None]
    ab_angle = _angle_rows(a, b)
    return a, b, normal_hat, ab_angle, valid


def minimum_spherical_polyline_distance_km(
    longitude_deg: float,
    latitude_deg: float,
    ring_lonlat: np.ndarray,
) -> float:
    """Minimum point-to-minor-great-circle-segment distance on a sphere."""
    if not (math.isfinite(longitude_deg) and math.isfinite(latitude_deg)):
        raise ValueError("query coordinate must be finite")
    if not (-180 <= longitude_deg <= 180 and -90 <= latitude_deg <= 90):
        raise ValueError("query coordinate outside lon/lat bounds")
    a, b, normal_hat, ab_angle, valid = _prepare_ring_segments(ring_lonlat)
    p = _unit_vectors(np.asarray([longitude_deg]), np.asarray([latitude_deg]))[0]

    # Endpoint distances are always valid and provide the fallback for projections
    # that land outside the minor arc represented by a segment.
    p_rows = np.broadcast_to(p, a.shape)
    pa = _angle_rows(p_rows, a)
    pb = _angle_rows(p_rows, b)
    endpoint = np.minimum(pa, pb)

    dot_pn = normal_hat @ p
    q_raw = p_rows - dot_pn[:, None] * normal_hat
    q_norm = np.linalg.norm(q_raw, axis=1)
    projection_valid = valid & (q_norm > 1e-14)
    q = np.zeros_like(q_raw)
    q[projection_valid] = q_raw[projection_valid] / q_norm[projection_valid, None]
    # Orthogonal projection has antipodal solutions. Choose the one nearest p.
    flip = np.einsum("ij,j->i", q, p) < 0
    q[flip] *= -1.0

    aq = _angle_rows(a, q)
    qb = _angle_rows(q, b)
    arc_tolerance = 1e-9 + 1e-7 * np.maximum(1.0, ab_angle)
    on_minor_arc = projection_valid & (np.abs((aq + qb) - ab_angle) <= arc_tolerance)
    cross_track = np.arcsin(np.clip(np.abs(dot_pn), 0.0, 1.0))
    angular = np.where(on_minor_arc, cross_track, endpoint)
    finite = angular[np.isfinite(angular)]
    if finite.size == 0:
        raise ValueError("no finite mainland coastline segment distance")
    return float(np.min(finite) * EARTH_RADIUS_KM)


def _read_ring(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or not {"longitude", "latitude"}.issubset(rows[0]):
        raise ValueError("mainland ring CSV lacks longitude/latitude")
    ring = np.asarray(
        [[float(row["longitude"]), float(row["latitude"])] for row in rows],
        dtype=float,
    )
    if not np.isfinite(ring).all():
        raise ValueError("mainland ring CSV contains non-finite coordinates")
    return ring


def build_mainland_distances(
    island_audit_csv: Path,
    mainland_ring_csv: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    with island_audit_csv.open(newline="", encoding="utf-8-sig") as handle:
        islands = list(csv.DictReader(handle))
    if len(islands) != 842:
        raise ValueError(f"expected 842 frozen island rows, got {len(islands)}")
    required = {"island_id", "x", "y", "coordinate_evaluable"}
    if not islands or not required.issubset(islands[0]):
        raise ValueError("island audit lacks required coordinate fields")

    ring = _read_ring(mainland_ring_csv)
    rows: list[dict[str, object]] = []
    distances: list[float] = []
    for row in islands:
        if row["coordinate_evaluable"].strip() != "1":
            raise ValueError(f"island {row['island_id']} lacks evaluable centroid")
        distance = minimum_spherical_polyline_distance_km(
            float(row["x"]), float(row["y"]), ring
        )
        if not math.isfinite(distance) or distance < 0:
            raise ValueError(f"invalid mainland distance for island {row['island_id']}")
        distances.append(distance)
        rows.append({
            "island_id": row["island_id"].strip(),
            "distance_to_australia_mainland_km": distance,
        })

    values = np.asarray(distances, dtype=float)
    summary = {
        "status": "outcome_free_aislands_mainland_distance_table",
        "islands": len(rows),
        "distance_km": {
            "min": float(np.min(values)),
            "q25": float(np.quantile(values, 0.25)),
            "median": float(np.quantile(values, 0.5)),
            "q75": float(np.quantile(values, 0.75)),
            "max": float(np.max(values)),
        },
        "method": "minimum spherical point-to-minor-great-circle-segment distance; Earth radius 6371.0088 km",
        "input_sha256": {
            "island_audit_csv": _sha256(island_audit_csv),
            "mainland_ring_csv": _sha256(mainland_ring_csv),
        },
        "species_outcomes_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
        "scientific_boundary": "fixed species-independent continental-mainland distance baseline only",
    }
    return rows, summary


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-audit-csv", type=Path, required=True)
    parser.add_argument("--mainland-ring-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    args = parser.parse_args()

    rows, summary = build_mainland_distances(args.island_audit_csv, args.mainland_ring_csv)
    _write_csv(args.output_csv, rows)
    summary["output_distance_table_sha256"] = _sha256(args.output_csv)
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
