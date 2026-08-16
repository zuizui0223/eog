#!/usr/bin/env python3
"""Freeze declared climate products at the nine immutable Azores nodes.

This stage is response-blind. It reads only the frozen node table and public climate
rasters. Any missing/nodata value is a hard block: no snapping, nearby-cell lookup,
interpolation, imputation, node drop, or resolution change is permitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import rasterio


VARIABLES = ("bio1", "bio5", "bio6", "bio12", "bio15")
EXPECTED_NODE_COUNT = 9
CHELSA_PRIMARY_BASE = (
    "https://os.zhdk.cloud.switch.ch/envicloud/chelsa/chelsa_V2/"
    "GLOBAL/climatologies/1981-2010/bio"
)
CHELSA_LEGACY_BASE = (
    "https://os.zhdk.cloud.switch.ch/chelsav2/"
    "GLOBAL/climatologies/1981-2010/bio"
)
WORLDCLIM_ARCHIVE_URL = (
    "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_nodes(path: Path) -> tuple[list[dict[str, str]], list[tuple[float, float]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"island_id", "latitude", "longitude", "geonameid"}
    if len(rows) != EXPECTED_NODE_COUNT:
        raise ValueError(f"expected {EXPECTED_NODE_COUNT} frozen nodes, got {len(rows)}")
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"node table missing columns: {sorted(required - set(rows[0] if rows else []))}")
    coords: list[tuple[float, float]] = []
    for row in rows:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise ValueError(f"non-finite frozen coordinate for {row['island_id']}")
        coords.append((lon, lat))
    return rows, coords


def probe(url: str) -> dict[str, object] | None:
    headers = {"User-Agent": "eog-azores-climate-freeze/1.0"}
    for request in (
        urllib.request.Request(url, method="HEAD", headers=headers),
        urllib.request.Request(url, headers={**headers, "Range": "bytes=0-0"}),
    ):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status not in (200, 206):
                    continue
                return {
                    "url": response.geturl(),
                    "http_status": response.status,
                    "content_length": response.headers.get("Content-Length"),
                    "content_range": response.headers.get("Content-Range"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "content_type": response.headers.get("Content-Type"),
                }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
    return None


def chelsa_source(variable: str) -> dict[str, object]:
    name = f"CHELSA_{variable}_1981-2010_V.2.1.tif"
    attempts: list[str] = []
    for base in (CHELSA_PRIMARY_BASE, CHELSA_LEGACY_BASE):
        url = f"{base}/{name}"
        attempts.append(url)
        metadata = probe(url)
        if metadata is not None:
            return {**metadata, "object_name": name, "candidate_urls_attempted": attempts}
    raise RuntimeError(f"unable to resolve CHELSA object {name}: {attempts}")


def sample_raster(path_or_url: str, coords: list[tuple[float, float]]) -> tuple[np.ndarray, dict[str, object]]:
    raster_env = {
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "GDAL_HTTP_MAX_RETRY": "4",
        "GDAL_HTTP_RETRY_DELAY": "1",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "VSI_CACHE": "TRUE",
        "VSI_CACHE_SIZE": "50000000",
    }
    with rasterio.Env(**raster_env), rasterio.open(path_or_url) as dataset:
        crs = dataset.crs.to_string() if dataset.crs else None
        if crs not in ("EPSG:4326", "OGC:CRS84"):
            raise ValueError(f"climate raster is not WGS84 lon/lat-compatible: {crs}")
        if dataset.count != 1:
            raise ValueError(f"expected one-band climate raster, got {dataset.count}")
        samples = list(dataset.sample(coords, indexes=1, masked=True))
        values = np.full(len(samples), np.nan, dtype=float)
        missing: list[int] = []
        for index, sample in enumerate(samples):
            scalar = sample[0]
            if np.ma.is_masked(scalar):
                missing.append(index)
                continue
            value = float(scalar)
            if dataset.nodata is not None and np.isclose(value, float(dataset.nodata), equal_nan=True):
                missing.append(index)
                continue
            if not np.isfinite(value):
                missing.append(index)
                continue
            values[index] = value
        metadata = {
            "driver": dataset.driver,
            "crs": crs,
            "width": dataset.width,
            "height": dataset.height,
            "dtype": dataset.dtypes[0],
            "nodata": None if dataset.nodata is None else float(dataset.nodata),
            "missing_sample_indices": missing,
        }
    return values, metadata


def download(url: str, path: Path) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "eog-azores-climate-freeze/1.0"})
    with urllib.request.urlopen(request, timeout=600) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle, length=1024 * 1024)
        return {
            "resolved_url": response.geturl(),
            "content_length": response.headers.get("Content-Length"),
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def worldclim_member(variable: str, names: list[str]) -> str:
    number = int(variable.replace("bio", ""))
    suffix = f"_bio_{number}.tif"
    matches = [name for name in names if name.lower().endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one WorldClim member ending {suffix!r}, found {matches}")
    return matches[0]


def freeze(nodes_csv: Path, output_csv: Path, output_manifest: Path) -> dict[str, object]:
    nodes, coords = load_nodes(nodes_csv)
    values: dict[str, np.ndarray] = {}
    chelsa_sources: list[dict[str, object]] = []

    for variable in VARIABLES:
        source = chelsa_source(variable)
        sampled, raster_meta = sample_raster(str(source["url"]), coords)
        missing = np.where(~np.isfinite(sampled))[0].tolist()
        if missing:
            island_ids = [nodes[i]["island_id"] for i in missing]
            raise RuntimeError(f"CHELSA {variable} missing/nodata at frozen nodes: {island_ids}")
        values[f"chelsa_{variable}"] = sampled
        chelsa_sources.append({**source, **raster_meta, "variable": variable})

    with tempfile.TemporaryDirectory(prefix="azores_worldclim_") as temp_dir:
        temp = Path(temp_dir)
        archive = temp / "wc2.1_2.5m_bio.zip"
        archive_headers = download(WORLDCLIM_ARCHIVE_URL, archive)
        archive_sha = sha256(archive)
        selected_members: list[dict[str, object]] = []
        with zipfile.ZipFile(archive) as bundle:
            names = bundle.namelist()
            for variable in VARIABLES:
                member = worldclim_member(variable, names)
                extracted = temp / Path(member).name
                with bundle.open(member) as source_handle, extracted.open("wb") as target:
                    shutil.copyfileobj(source_handle, target, length=1024 * 1024)
                sampled, raster_meta = sample_raster(str(extracted), coords)
                missing = np.where(~np.isfinite(sampled))[0].tolist()
                if missing:
                    island_ids = [nodes[i]["island_id"] for i in missing]
                    raise RuntimeError(
                        f"WorldClim 2.5m {variable} missing/nodata at frozen nodes: {island_ids}"
                    )
                values[f"worldclim_{variable}"] = sampled
                selected_members.append(
                    {
                        "variable": variable,
                        "member": member,
                        "member_sha256": sha256(extracted),
                        **raster_meta,
                    }
                )
        worldclim_source = {
            "dataset": "WorldClim bioclim",
            "version": "2.1",
            "resolution": "2.5m",
            "archive_url": WORLDCLIM_ARCHIVE_URL,
            "archive_sha256": archive_sha,
            "archive_bytes": archive.stat().st_size,
            **archive_headers,
            "selected_members": selected_members,
        }

    fields = [
        "island_id", "geonameid", "latitude", "longitude",
        *[f"chelsa_{v}" for v in VARIABLES],
        *[f"worldclim_{v}" for v in VARIABLES],
    ]
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for i, node in enumerate(nodes):
            writer.writerow({
                "island_id": node["island_id"],
                "geonameid": node["geonameid"],
                "latitude": node["latitude"],
                "longitude": node["longitude"],
                **{f"chelsa_{v}": repr(float(values[f'chelsa_{v}'][i])) for v in VARIABLES},
                **{f"worldclim_{v}": repr(float(values[f'worldclim_{v}'][i])) for v in VARIABLES},
            })

    manifest = {
        "status": "pre_outcome_climate_freeze",
        "nodes_csv_sha256": sha256(nodes_csv),
        "n_nodes": len(nodes),
        "variables": list(VARIABLES),
        "sampling_rule": "direct raster sample at immutable frozen GeoNames coordinates",
        "fallback_or_imputation_used": False,
        "species_incidence_used": False,
        "outcome_statistics_computed": False,
        "chelsa": {
            "dataset": "CHELSA-bioclim",
            "version": "2.1",
            "climatology": "1981-2010",
            "sources": chelsa_sources,
        },
        "worldclim": worldclim_source,
        "climate_csv_sha256": sha256(output_csv),
    }
    output_manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.nodes, args.output_csv, args.output_manifest), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
