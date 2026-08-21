#!/usr/bin/env python3
"""Canonical-node wrapper for the frozen giant-kelp complementarity runner.

The original runner was written before the response-blind cross-source label audit proved
that geometry uses ``socal_N`` while process uses ``N``.  This wrapper replaces only the
non-response loader so the already-validated bijective canonical node labels ``1..469``
use their own frozen centroid fingerprint.  Prediction, count-gate, Layer-A/B, learner,
metric and response logic remain in ``run_giant_kelp_complementarity_once.py``.
"""
from __future__ import annotations

import csv
import math
import re

import numpy as np

import run_giant_kelp_complementarity_once as base

CANONICAL_CENTROID_FINGERPRINT = (
    "827b0aca7179bd8e68176b559e4c1133531096f61aa6cc3c856aed33163b81f8"
)
CANONICAL_GEOMETRY_RESULT_FINGERPRINT = (
    "fd66b1ed16892e30966d0709a0478020f04eb5a0d8de6f474a0ea5cb3c896f72"
)


def load_nonresponse_inputs_v2() -> base.NonResponseInputs:
    geometry_contract = base.read_json(base.GEOMETRY_CONTRACT_PATH)
    process_contract = base.read_json(base.PROCESS_CONTRACT_PATH)
    identity_contract = base.read_json(base.PATCH_IDENTITY_PATH)
    geometry = geometry_contract["southern_geometry_entity"]
    process = process_contract["process_entity"]
    geometry_pattern = base.compile_one_group(identity_contract["geometry_raw_pattern"])
    process_pattern = base.compile_one_group(identity_contract["process_raw_pattern"])
    transport: list[dict[str, object]] = []

    geometry_path = base.download_object(
        geometry["data_pid"],
        expected_size=int(geometry["size_bytes"]),
        expected_sha1=geometry["checksum"],
        stem="giant_kelp_geometry_runner_v2",
        transport=transport,
    )
    grouped: dict[str, list[tuple[float, float]]] = {}
    raw_to_canonical: dict[str, str] = {}
    canonical_to_raw: dict[str, str] = {}
    with geometry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = ("patch_number", "pixel_latitude", "pixel_longitude")
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ValueError(f"geometry schema drift: {reader.fieldnames!r}")
        for row_no, row in enumerate(reader, 2):
            raw = str(row["patch_number"]).strip()
            node = base.canonical_patch_id(
                raw, (geometry_pattern,), f"geometry row {row_no} patch"
            )
            prior = raw_to_canonical.setdefault(raw, node)
            if prior != node:
                raise ValueError(f"geometry raw patch maps inconsistently: {raw!r}")
            other = canonical_to_raw.setdefault(node, raw)
            if other != raw:
                raise ValueError(
                    f"geometry canonical node collision: {node!r} from {other!r} and {raw!r}"
                )
            try:
                latitude = float(row["pixel_latitude"])
                longitude = float(row["pixel_longitude"])
            except Exception as exc:
                raise ValueError(f"invalid geometry coordinate at row {row_no}") from exc
            if not (
                math.isfinite(latitude)
                and math.isfinite(longitude)
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                raise ValueError(f"out-of-range geometry coordinate at row {row_no}")
            grouped.setdefault(node, []).append((latitude, longitude))
    if (
        len(grouped) != base.N
        or len(raw_to_canonical) != base.N
        or len(canonical_to_raw) != base.N
    ):
        raise ValueError("canonical geometry is not the frozen 469-node bijection")

    node_ids = tuple(sorted(grouped, key=int))
    if node_ids != tuple(str(index) for index in range(1, base.N + 1)):
        raise ValueError("canonical geometry node universe is not exactly 1..469")
    centroids = np.asarray(
        [
            [
                sum(value[0] for value in grouped[node]) / len(grouped[node]),
                sum(value[1] for value in grouped[node]) / len(grouped[node]),
            ]
            for node in node_ids
        ],
        dtype=float,
    )
    pixel_counts = np.asarray([len(grouped[node]) for node in node_ids], dtype=float)
    centroid_payload = [
        {
            "patch_number": node,
            "latitude": float(centroids[index, 0]),
            "longitude": float(centroids[index, 1]),
            "pixel_count": int(pixel_counts[index]),
        }
        for index, node in enumerate(node_ids)
    ]
    centroid_fingerprint = base.canonical_sha256(centroid_payload)
    if centroid_fingerprint != CANONICAL_CENTROID_FINGERPRINT:
        raise ValueError(
            f"canonical geometry centroid fingerprint drift: {centroid_fingerprint}"
        )

    lat = np.radians(centroids[:, 0])
    lon = np.radians(centroids[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    hav = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat[:, None])
        * np.cos(lat[None, :])
        * np.sin(dlon / 2.0) ** 2
    )
    hav = np.clip(hav, 0.0, 1.0)
    distance_km = 2.0 * 6371.0088 * np.arcsin(np.sqrt(hav))
    np.fill_diagonal(distance_km, 0.0)

    process_path = base.download_object(
        process["data_pid"],
        expected_size=int(process["size_bytes"]),
        expected_sha1=process["checksum"],
        stem="giant_kelp_process_runner_v2",
        transport=transport,
    )
    node_index = {node: index for index, node in enumerate(node_ids)}
    process_time = np.full(
        (len(base.PERIODS), base.N, base.N), np.nan, dtype=np.float32
    )
    seen = np.zeros((len(base.PERIODS), base.N, base.N), dtype=bool)
    int_re = re.compile(r"^[0-9]+$")
    expected_process_fields = tuple(process["required_columns"])
    row_count = 0
    with process_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_process_fields:
            raise ValueError(
                f"process schema drift: {reader.fieldnames!r} != {expected_process_fields!r}"
            )
        for row_no, row in enumerate(reader, 2):
            row_count += 1
            src = base.canonical_patch_id(
                row["source_patch"], (process_pattern,), f"process row {row_no} source"
            )
            dst = base.canonical_patch_id(
                row["destination_patch"],
                (process_pattern,),
                f"process row {row_no} destination",
            )
            year_token = str(row["year"]).strip()
            semester_token = str(row["semester"]).strip()
            if not int_re.fullmatch(year_token) or not int_re.fullmatch(semester_token):
                raise ValueError(f"non-strict process period token at row {row_no}")
            year = int(year_token)
            semester = int(semester_token)
            if not 1996 <= year <= 2006 or semester not in (1, 2):
                raise ValueError(f"out-of-contract process period at row {row_no}")
            period = f"{year}-H{semester}"
            try:
                dispersal_time = float(row["dispersal_time"])
            except Exception as exc:
                raise ValueError(f"invalid dispersal time at row {row_no}") from exc
            if not math.isfinite(dispersal_time) or dispersal_time < 0:
                raise ValueError(f"invalid dispersal time at row {row_no}")
            i = base.PERIOD_INDEX[period]
            j = node_index[src]
            k = node_index[dst]
            if seen[i, j, k]:
                raise ValueError(
                    f"duplicate process source-destination-period at row {row_no}"
                )
            seen[i, j, k] = True
            process_time[i, j, k] = dispersal_time
    if row_count != 22 * base.N * base.N:
        raise ValueError(
            f"expected {22 * base.N * base.N} process rows, found {row_count}"
        )
    if not bool(np.all(seen)) or not np.isfinite(process_time).all():
        raise ValueError("process matrix is not complete and finite")

    return base.NonResponseInputs(
        node_ids=node_ids,
        centroids=centroids,
        pixel_counts=pixel_counts,
        distance_km=distance_km,
        process_time=process_time,
        provenance={
            "geometry_pid": geometry["data_pid"],
            "geometry_sha1": geometry["checksum"],
            "raw_label_centroid_fingerprint": "358d66cdf1b039207e22ae575a23900c4405a7c9c556871e4a60c91e0a19128c",
            "canonical_centroid_fingerprint": centroid_fingerprint,
            "canonical_geometry_result_fingerprint": CANONICAL_GEOMETRY_RESULT_FINGERPRINT,
            "patch_identity_contract_sha256": "35396f8f77f1772b7744612933436424ec28068f9c079fb5be4db6e2f59ad13c",
            "process_pid": process["data_pid"],
            "process_sha1": process["checksum"],
            "process_mapping_fingerprint": "5f117614fdc6367e03bb6a8439320d567473fe8f7b2c831192575e2a1d1fa4c6",
            "process_row_count": row_count,
            "transport": transport,
        },
    )


base.load_nonresponse_inputs = load_nonresponse_inputs_v2

if __name__ == "__main__":
    base.main()
