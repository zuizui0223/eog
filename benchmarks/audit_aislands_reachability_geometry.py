"""Audit unlabeled A-Islands geometry used to freeze reachability distance scales."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


EARTH_RADIUS_KM = 6371.0088


def _haversine_matrix(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    lat_r = np.radians(lat)[:, None]
    lon_r = np.radians(lon)[:, None]
    dlat = lat_r - lat_r.T
    dlon = lon_r - lon_r.T
    value = np.sin(dlat / 2.0) ** 2 + np.cos(lat_r) * np.cos(lat_r.T) * np.sin(dlon / 2.0) ** 2
    matrix = 2.0 * EARTH_RADIUS_KM * np.arcsin(np.minimum(1.0, np.sqrt(value)))
    np.fill_diagonal(matrix, np.inf)
    return matrix


def audit(path: Path) -> dict[str, object]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("island model audit is empty")
    required = {"island_id", "x", "y", "coordinate_evaluable"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"island model audit missing columns: {', '.join(sorted(missing))}")
    usable = [row for row in rows if int(row["coordinate_evaluable"]) == 1]
    lat = np.asarray([float(row["y"]) for row in usable], dtype=float)
    lon = np.asarray([float(row["x"]) for row in usable], dtype=float)
    distances = _haversine_matrix(lat, lon)
    nearest = np.min(distances, axis=1)
    quantiles = {
        "q25": float(np.quantile(nearest, 0.25)),
        "q50": float(np.quantile(nearest, 0.50)),
        "q75": float(np.quantile(nearest, 0.75)),
        "q90": float(np.quantile(nearest, 0.90)),
        "q95": float(np.quantile(nearest, 0.95)),
        "q975": float(np.quantile(nearest, 0.975)),
        "q99": float(np.quantile(nearest, 0.99)),
        "max": float(np.max(nearest)),
    }
    frozen = [25.0, 50.0, 125.0, 250.0]
    return {
        "n_islands": len(usable),
        "nearest_neighbor_distance_km": quantiles,
        "frozen_geographic_radii_km": frozen,
        "radius_rationale": (
            "Rounded pre-outcome geometry scales spanning approximately the 90th nearest-neighbour percentile, the 97.5th percentile, the 99th percentile, and the observed maximum nearest-neighbour separation. These radii are frozen as a sensitivity ensemble and no single best radius will be selected from held-out incidence outcomes."
        ),
        "species_labels_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.island_audit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
