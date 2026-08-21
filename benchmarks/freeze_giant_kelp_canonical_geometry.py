from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np

from audit_giant_kelp_process_mapping import download
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
)

ROOT = Path("validation/giant_kelp_complementarity")
OUT = Path("build/giant_kelp_canonical_geometry")
EXPECTED_THRESHOLDS = np.asarray(
    [8.784880554989936, 30.599950974020906, 33.76116917197375, 40.81254045279048],
    dtype=float,
)


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    geometry_contract = json.loads((ROOT / "southern_geometry_object_contract.json").read_text())
    identity_contract = json.loads((ROOT / "patch_identity_contract.json").read_text())
    entity = geometry_contract["southern_geometry_entity"]
    pattern = re.compile(identity_contract["geometry_raw_pattern"])
    if pattern.groups != 1:
        raise ValueError("geometry raw ID regex must have one group")
    transport: list[dict] = []
    path = download(
        entity["data_pid"],
        int(entity["size_bytes"]),
        entity["checksum"],
        "giant_kelp_canonical_geometry",
        transport,
    )

    grouped: dict[str, list[tuple[float, float]]] = {}
    raw_to_canonical: dict[str, str] = {}
    canonical_to_raw: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ("patch_number", "pixel_latitude", "pixel_longitude")
        if tuple(reader.fieldnames or ()) != expected:
            raise ValueError(f"geometry schema drift: {reader.fieldnames!r}")
        for row_no, row in enumerate(reader, 2):
            raw = str(row["patch_number"]).strip()
            match = pattern.fullmatch(raw)
            if match is None:
                raise ValueError(f"geometry ID does not match frozen pattern at row {row_no}: {raw!r}")
            digits = match.group(1)
            canonical = str(int(digits))
            if canonical != digits:
                raise ValueError(f"noncanonical captured digits at row {row_no}: {digits!r}")
            prior = raw_to_canonical.setdefault(raw, canonical)
            if prior != canonical:
                raise ValueError("raw geometry ID mapping changed")
            other = canonical_to_raw.setdefault(canonical, raw)
            if other != raw:
                raise ValueError(f"canonical collision: {canonical!r}")
            lat = float(row["pixel_latitude"])
            lon = float(row["pixel_longitude"])
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"invalid geometry coordinate at row {row_no}")
            grouped.setdefault(canonical, []).append((lat, lon))

    if len(grouped) != 469 or len(raw_to_canonical) != 469 or len(canonical_to_raw) != 469:
        raise ValueError("canonical geometry is not a 469-node bijection")
    node_ids = tuple(sorted(grouped, key=int))
    centroids = np.asarray(
        [
            [
                sum(v[0] for v in grouped[node]) / len(grouped[node]),
                sum(v[1] for v in grouped[node]) / len(grouped[node]),
            ]
            for node in node_ids
        ],
        dtype=float,
    )
    pixel_counts = np.asarray([len(grouped[node]) for node in node_ids], dtype=int)
    centroid_payload = [
        {
            "patch_number": node,
            "latitude": float(centroids[index, 0]),
            "longitude": float(centroids[index, 1]),
            "pixel_count": int(pixel_counts[index]),
        }
        for index, node in enumerate(node_ids)
    ]
    centroid_fingerprint = canonical_sha256(centroid_payload)

    lat = np.radians(centroids[:, 0])
    lon = np.radians(centroids[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    hav = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    hav = np.clip(hav, 0.0, 1.0)
    distance = 2.0 * 6371.0088 * np.arcsin(np.sqrt(hav))
    np.fill_diagonal(distance, 0.0)
    declaration = StructuralScaleLadderDeclaration(
        axis_id="giant_kelp_canonical_patch_centroid_haversine_km",
        target_largest_component_fractions=(0.25, 0.5, 0.75, 0.9),
    )
    ladder = build_structural_scale_ladder(node_ids, distance, declaration)
    observed = np.asarray(ladder.thresholds, dtype=float)
    thresholds_unchanged = bool(np.allclose(observed, EXPECTED_THRESHOLDS, rtol=0.0, atol=1e-12))
    if not thresholds_unchanged:
        raise ValueError(f"canonical relabeling changed frozen structural thresholds: {observed.tolist()}")

    payload = {
        "status": "canonical_geometry_relabeling_pass",
        "candidate": geometry_contract["candidate"],
        "patch_identity_contract_sha256": hashlib.sha256((ROOT / "patch_identity_contract.json").read_bytes()).hexdigest(),
        "raw_geometry_object_sha1": entity["checksum"],
        "raw_label_centroid_fingerprint": "358d66cdf1b039207e22ae575a23900c4405a7c9c556871e4a60c91e0a19128c",
        "canonical_centroid_fingerprint": centroid_fingerprint,
        "raw_patch_count": len(raw_to_canonical),
        "canonical_patch_count": len(node_ids),
        "bijection_pass": True,
        "canonical_node_order_first": list(node_ids[:20]),
        "canonical_node_order_last": list(node_ids[-20:]),
        "pixel_row_count": int(np.sum(pixel_counts)),
        "structural_thresholds_km": observed.tolist(),
        "expected_structural_thresholds_km": EXPECTED_THRESHOLDS.tolist(),
        "structural_thresholds_unchanged": thresholds_unchanged,
        "response_package_bytes_opened": False,
        "response_rows_opened": False,
        "transport": transport,
    }
    payload["fingerprint"] = canonical_sha256(payload)
    (OUT / "canonical_geometry_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
