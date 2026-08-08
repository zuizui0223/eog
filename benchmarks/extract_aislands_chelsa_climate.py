"""Freeze direct-centroid CHELSA-bioclim values for A-Islands model units.

This stage is deliberately species-outcome free. It resolves the public CHELSA V2.1
COG objects, samples the five predeclared bioclimatic rasters at the frozen A-Islands
centroids, and records source/object/raster metadata. No presence/absence labels, SDM
fits, EOG outputs or outcome-dependent spatial substitutions are used.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable
import urllib.error
import urllib.request

import numpy as np
import rasterio


VARIABLES: tuple[str, ...] = ("bio1", "bio5", "bio6", "bio12", "bio15")
PRIMARY_BASE = (
    "https://os.zhdk.cloud.switch.ch/envicloud/chelsa/chelsa_V2/"
    "GLOBAL/climatologies/1981-2010/bio"
)
LEGACY_PUBLIC_BASE = (
    "https://os.zhdk.cloud.switch.ch/chelsav2/"
    "GLOBAL/climatologies/1981-2010/bio"
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object_name(variable: str) -> str:
    return f"CHELSA_{variable}_1981-2010_V.2.1.tif"


def _candidate_urls(variable: str) -> tuple[str, ...]:
    name = _object_name(variable)
    return (
        f"{PRIMARY_BASE}/{name}",
        f"{LEGACY_PUBLIC_BASE}/{name}",
    )


def _probe(url: str) -> dict[str, object] | None:
    headers = {"User-Agent": "eog-aislands-chelsa-freeze/0.1"}
    requests = [
        urllib.request.Request(url, method="HEAD", headers=headers),
        urllib.request.Request(url, headers={**headers, "Range": "bytes=0-0"}),
    ]
    for request in requests:
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if response.status not in (200, 206):
                    continue
                return {
                    "url": response.geturl(),
                    "http_status": response.status,
                    "content_length": response.headers.get("Content-Length"),
                    "content_range": response.headers.get("Content-Range"),
                    "accept_ranges": response.headers.get("Accept-Ranges"),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                    "content_type": response.headers.get("Content-Type"),
                }
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
    return None


def resolve_url(variable: str) -> dict[str, object]:
    if variable not in VARIABLES:
        raise ValueError(f"unsupported frozen CHELSA variable: {variable}")
    attempts: list[str] = []
    for url in _candidate_urls(variable):
        attempts.append(url)
        metadata = _probe(url)
        if metadata is not None:
            metadata["requested_variable"] = variable
            metadata["object_name"] = _object_name(variable)
            metadata["candidate_urls_attempted"] = attempts.copy()
            return metadata
    raise RuntimeError(f"unable to resolve public CHELSA object for {variable}: {attempts}")


def _load_islands(path: Path) -> list[dict[str, object]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("island model audit is empty")
    required = {"island_id", "x", "y", "coordinate_evaluable"}
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"island model audit missing columns: {', '.join(sorted(missing))}")
    output: list[dict[str, object]] = []
    for row in rows:
        if int(row["coordinate_evaluable"]) != 1:
            continue
        lon = float(row["x"])
        lat = float(row["y"])
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise ValueError(f"non-finite centroid for island {row['island_id']}")
        output.append({"island_id": row["island_id"], "x": lon, "y": lat})
    output.sort(key=lambda item: int(str(item["island_id"])))
    if len(output) != 842:
        raise ValueError(f"expected 842 frozen model islands, found {len(output)}")
    return output


def _clean_metadata_value(value: object) -> object:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, tuple):
        return [_clean_metadata_value(item) for item in value]
    return value


def _sample_variable(
    url_metadata: dict[str, object],
    coordinates: Iterable[tuple[float, float]],
) -> tuple[np.ndarray, dict[str, object]]:
    url = str(url_metadata["url"])
    raster_env = {
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "GDAL_HTTP_MAX_RETRY": "4",
        "GDAL_HTTP_RETRY_DELAY": "1",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "VSI_CACHE": "TRUE",
        "VSI_CACHE_SIZE": "50000000",
    }
    with rasterio.Env(**raster_env), rasterio.open(url) as dataset:
        crs = dataset.crs.to_string() if dataset.crs else None
        if crs not in ("EPSG:4326", "OGC:CRS84"):
            raise ValueError(f"CHELSA raster is not lon/lat WGS84-compatible: {crs}")
        if dataset.count != 1:
            raise ValueError(f"expected one-band CHELSA COG, found {dataset.count}")
        samples = list(dataset.sample(coordinates, indexes=1, masked=True))
        values = np.full(len(samples), np.nan, dtype=float)
        masked_count = 0
        for index, sample in enumerate(samples):
            scalar = sample[0]
            if np.ma.is_masked(scalar):
                masked_count += 1
                continue
            number = float(scalar)
            if dataset.nodata is not None and number == float(dataset.nodata):
                masked_count += 1
                continue
            if not np.isfinite(number):
                masked_count += 1
                continue
            values[index] = number

        metadata = {
            **url_metadata,
            "driver": dataset.driver,
            "crs": crs,
            "width": dataset.width,
            "height": dataset.height,
            "bounds": [_clean_metadata_value(value) for value in dataset.bounds],
            "transform": [_clean_metadata_value(value) for value in dataset.transform[:6]],
            "dtype": dataset.dtypes[0],
            "nodata": _clean_metadata_value(dataset.nodata),
            "scale": _clean_metadata_value(dataset.scales[0] if dataset.scales else 1.0),
            "offset": _clean_metadata_value(dataset.offsets[0] if dataset.offsets else 0.0),
            "unit": dataset.units[0] if dataset.units else None,
            "tags": dataset.tags(1),
            "masked_or_nodata_samples": masked_count,
            "finite_samples": int(np.isfinite(values).sum()),
            "raw_min": None if not np.isfinite(values).any() else float(np.nanmin(values)),
            "raw_max": None if not np.isfinite(values).any() else float(np.nanmax(values)),
        }
    return values, metadata


def extract(island_audit: Path, output_csv: Path, output_manifest: Path) -> dict[str, object]:
    islands = _load_islands(island_audit)
    coordinates = [(float(row["x"]), float(row["y"])) for row in islands]
    columns: dict[str, np.ndarray] = {}
    sources: list[dict[str, object]] = []

    for variable in VARIABLES:
        url_metadata = resolve_url(variable)
        values, source = _sample_variable(url_metadata, coordinates)
        columns[variable] = values
        sources.append(source)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["island_id", "x", "y", *VARIABLES, "primary_climate_complete"]
    missing_islands: list[str] = []
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, island in enumerate(islands):
            values = {variable: columns[variable][index] for variable in VARIABLES}
            complete = all(np.isfinite(value) for value in values.values())
            if not complete:
                missing_islands.append(str(island["island_id"]))
            writer.writerow({
                "island_id": island["island_id"],
                "x": f"{float(island['x']):.10f}",
                "y": f"{float(island['y']):.10f}",
                **{
                    variable: "" if not np.isfinite(value) else repr(float(value))
                    for variable, value in values.items()
                },
                "primary_climate_complete": int(complete),
            })

    manifest = {
        "status": "preoutcome_climate_extraction",
        "dataset": "CHELSA-bioclim",
        "version": "2.1",
        "climatology": "1981-2010",
        "file_format": "COG GeoTIFF",
        "variables": list(VARIABLES),
        "extraction_rule": "direct sample at frozen A-Islands WGS84 centroid; no nearby-cell substitution",
        "sample_value_role": (
            "raw raster cell values are frozen. The benchmark standardizes predictors on training islands, so no outcome-dependent physical-unit transformation is needed. Raster scale/offset/unit metadata are recorded per source object."
        ),
        "n_islands": len(islands),
        "complete_islands": len(islands) - len(missing_islands),
        "incomplete_islands": len(missing_islands),
        "incomplete_island_ids": missing_islands,
        "source_objects": sources,
        "climate_csv_sha256": _sha256(output_csv),
        "species_outcomes_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
        "fallback_or_imputation_used": False,
    }
    output_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--island-audit", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    result = extract(args.island_audit, args.output_csv, args.output_manifest)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
