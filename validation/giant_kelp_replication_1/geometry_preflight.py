from __future__ import annotations

import csv
from collections import defaultdict
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import urllib.request

import numpy as np

from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
OUT_DIR = ROOT / "build/giant_kelp_replication_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "geometry_preflight.json"

AUDIT = {
    "response_payload_requests": 0,
    "response_payload_bytes_opened": 0,
    "response_header_bytes_opened": 0,
    "response_rows_opened": False,
    "response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def finish(status: str, exit_code: int = 0, **extra: object) -> None:
    payload = {
        "schema": "eog.giant_kelp_replication_1_geometry_preflight.v1",
        "replication_id": CONTRACT["replication_id"],
        "status": status,
        "response_firewall": AUDIT,
        **extra,
    }
    payload["fingerprint"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(exit_code)


def haversine_matrix(lat: np.ndarray, lon: np.ndarray, radius_km: float) -> np.ndarray:
    phi = np.radians(lat)
    lam = np.radians(lon)
    dphi = phi[:, None] - phi[None, :]
    dlam = lam[:, None] - lam[None, :]
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi[:, None]) * np.cos(phi[None, :]) * np.sin(dlam / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    matrix = 2.0 * radius_km * np.arcsin(np.sqrt(a))
    np.fill_diagonal(matrix, 0.0)
    return matrix


def main() -> None:
    geometry = CONTRACT["public_role_separation"]["geometry"]
    url = (
        "https://raw.githubusercontent.com/"
        f"{geometry['public_snapshot_repository']}/{geometry['public_snapshot_commit']}/"
        "data/raw/knb-lter-sbc.101.2/"
        f"{geometry['southern_california_file']}"
    )
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-giant-kelp-response-blind-geometry/1.0", "Accept-Encoding": "identity"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as handle:
            raw = handle.read(int(geometry["public_snapshot_size_bytes"]) + 1)
    except Exception as exc:
        finish("stop_geometry_transport_failure", 2, error=repr(exc), geometry_url=url)

    observed_size = len(raw)
    observed_md5 = hashlib.md5(raw).hexdigest()
    if observed_size != int(geometry["public_snapshot_size_bytes"]):
        finish(
            "stop_geometry_size_mismatch",
            2,
            observed_size=observed_size,
            expected_size=geometry["public_snapshot_size_bytes"],
            observed_md5=observed_md5,
        )
    if observed_md5 != geometry["edi_md5"]:
        finish(
            "stop_geometry_md5_mismatch",
            2,
            observed_size=observed_size,
            observed_md5=observed_md5,
            expected_md5=geometry["edi_md5"],
        )

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        finish("stop_geometry_encoding_mismatch", 2, error=repr(exc))

    reader = csv.DictReader(io.StringIO(text, newline=""))
    expected_header = CONTRACT["geometry_semantics"]["expected_geometry_columns_exact"]
    if reader.fieldnames != expected_header:
        finish(
            "stop_geometry_schema_mismatch",
            2,
            observed_header=reader.fieldnames,
            expected_header=expected_header,
        )

    sums = defaultdict(lambda: [0.0, 0.0, 0])
    physical_rows = 0
    try:
        for row in reader:
            physical_rows += 1
            patch_id = str(row["patch_number"]).strip()
            if not patch_id:
                raise ValueError("empty patch_number")
            lat = float(row["pixel_latitude"])
            lon = float(row["pixel_longitude"])
            if not (math.isfinite(lat) and math.isfinite(lon) and -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                raise ValueError(f"invalid coordinate in patch {patch_id}")
            values = sums[patch_id]
            values[0] += lat
            values[1] += lon
            values[2] += 1
    except Exception as exc:
        finish("stop_geometry_row_parse_failure", 2, physical_rows_seen=physical_rows, error=repr(exc))

    node_ids = tuple(sorted(sums))
    expected_nodes = int(CONTRACT["frozen_historical_endpoint"]["expected_fixed_patch_count_from_selection_record"])
    if len(node_ids) != expected_nodes:
        finish(
            "stop_geometry_registry_not_reproduced",
            2,
            physical_pixel_rows=physical_rows,
            observed_patch_count=len(node_ids),
            expected_patch_count=expected_nodes,
            note="No response rows may be used to add, delete, or filter patches after this mismatch.",
        )

    lat = np.asarray([sums[node][0] / sums[node][2] for node in node_ids], dtype=float)
    lon = np.asarray([sums[node][1] / sums[node][2] for node in node_ids], dtype=float)
    pixel_counts = np.asarray([sums[node][2] for node in node_ids], dtype=int)
    radius = float(CONTRACT["geometry_semantics"]["earth_radius_km"])
    distance_matrix = haversine_matrix(lat, lon, radius)
    declaration = StructuralScaleLadderDeclaration(
        axis_id="giant_kelp_patch_haversine",
        target_largest_component_fractions=tuple(
            float(value) for value in CONTRACT["geometry_semantics"]["structural_lcc_targets"]
        ),
    )
    ladder = build_structural_scale_ladder(node_ids, distance_matrix, declaration)
    distinct_positive = sorted({round(float(value), 12) for value in ladder.thresholds if float(value) > 0.0})
    required_distinct = int(CONTRACT["geometry_semantics"]["minimum_distinct_positive_structural_scales"])
    if len(distinct_positive) < required_distinct:
        finish(
            "stop_structural_scale_collapse",
            2,
            patch_count=len(node_ids),
            thresholds_km=list(ladder.thresholds),
            distinct_positive_thresholds_km=distinct_positive,
            required_distinct_positive_thresholds=required_distinct,
        )

    registry_rows = [
        {
            "patch_id": node_ids[index],
            "latitude": float(lat[index]),
            "longitude": float(lon[index]),
            "pixel_count": int(pixel_counts[index]),
            "area_m2": int(pixel_counts[index]) * 900,
        }
        for index in range(len(node_ids))
    ]
    registry_fingerprint = hashlib.sha256(
        json.dumps(registry_rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()

    finish(
        "geometry_registry_and_structural_scales_pass",
        0,
        source={
            "url": url,
            "size_bytes": observed_size,
            "md5": observed_md5,
            "public_snapshot_git_blob_sha": geometry["public_snapshot_git_blob_sha"],
        },
        physical_pixel_rows=physical_rows,
        patch_count=len(node_ids),
        registry_fingerprint=registry_fingerprint,
        total_geometry_area_m2=int(np.sum(pixel_counts) * 900),
        min_patch_pixels=int(np.min(pixel_counts)),
        max_patch_pixels=int(np.max(pixel_counts)),
        structural_ladder_fingerprint=ladder.fingerprint,
        structural_levels=[
            {
                "level_id": level.level_id,
                "target_lcc": level.target_largest_component_fraction,
                "threshold_km": level.distance_threshold,
                "achieved_lcc": level.achieved_largest_component_fraction,
                "isolated_node_fraction": level.isolated_node_fraction,
            }
            for level in ladder.levels
        ],
        distinct_positive_thresholds_km=distinct_positive,
    )


if __name__ == "__main__":
    main()
