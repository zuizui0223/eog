"""Freeze a deterministic Australian-continental-mainland ring from Natural Earth.

This is an outcome-free geographic baseline for the A-Islands isolation-adequacy
extension.  It does not read A-Islands occurrences, species identities, SDM outputs,
or EOG results.

Natural Earth Admin-0 countries contains Australia as multipart polygon geometry.
The continental mainland is defined mechanically as the polygon ring with the largest
absolute spherical area in the unique Australia feature.  This excludes Tasmania and
smaller offshore parts without a hand-curated island-name list.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import shutil
import urllib.request
import zipfile

import shapefile

from audit_aislands_polygon_area import _signed_ring_area_km2


DEFAULT_URL = "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip"
DEFAULT_VERSION = "5.1.1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": "eog-mainland-freeze/0.1"})


def _download(url: str, path: Path) -> None:
    with urllib.request.urlopen(_request(url), timeout=120) as response, path.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def _safe_extract(path: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"unsafe zip member: {member.filename}")
        archive.extractall(destination)


def _normalise(value: object) -> str:
    return str(value or "").strip().casefold()


def _find_australia_record(reader: shapefile.Reader):
    fields = [field[0] for field in reader.fields[1:]]
    candidates = []
    for shape_record in reader.iterShapeRecords():
        record = shape_record.record.as_dict()
        values = {
            key.casefold(): _normalise(value)
            for key, value in record.items()
        }
        code_match = any(
            values.get(key.casefold()) == "aus"
            for key in ("ADM0_A3", "SOV_A3", "GU_A3", "ISO_A3")
            if key.casefold() in values
        )
        name_match = any(
            values.get(key.casefold()) == "australia"
            for key in ("ADMIN", "SOVEREIGNT", "NAME", "NAME_LONG")
            if key.casefold() in values
        )
        if code_match or name_match:
            candidates.append(shape_record)
    if len(candidates) != 1:
        raise ValueError(
            f"expected exactly one Natural Earth Australia feature, found {len(candidates)}; fields={fields}"
        )
    return candidates[0], fields


def _rings(shape: shapefile.Shape):
    points = list(shape.points)
    starts = list(shape.parts) + [len(points)]
    return [points[int(start):int(end)] for start, end in zip(starts[:-1], starts[1:]) if end > start]


def _ring_center(ring) -> tuple[float, float]:
    lon = [float(point[0]) for point in ring]
    lat = [float(point[1]) for point in ring]
    return (min(lon) + max(lon)) / 2.0, (min(lat) + max(lat)) / 2.0


def _ring_digest(ring) -> str:
    text = "".join(f"{float(point[0]):.12f},{float(point[1]):.12f}\n" for point in ring)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def freeze_mainland(
    output_dir: Path,
    *,
    url: str = DEFAULT_URL,
    declared_version: str = DEFAULT_VERSION,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_zip = output_dir / "ne_10m_admin_0_countries.zip"
    extracted = output_dir / "extracted"
    extracted.mkdir(exist_ok=True)
    _download(url, raw_zip)
    _safe_extract(raw_zip, extracted)

    shapefiles = sorted(extracted.rglob("ne_10m_admin_0_countries.shp"))
    if len(shapefiles) != 1:
        raise ValueError(f"expected one Natural Earth countries shapefile, found {len(shapefiles)}")
    shp = shapefiles[0]
    reader = shapefile.Reader(str(shp), encoding="utf-8")
    shape_record, fields = _find_australia_record(reader)
    shape = shape_record.shape
    if shape.shapeType not in {shapefile.POLYGON, shapefile.POLYGONM, shapefile.POLYGONZ}:
        raise ValueError(f"Australia Natural Earth geometry is not polygonal: {shape.shapeTypeName}")

    rings = _rings(shape)
    if len(rings) < 2:
        raise ValueError("expected multipart Australia geometry with at least two polygon rings")

    ring_rows = []
    for index, ring in enumerate(rings):
        lon0, lat0 = _ring_center(ring)
        signed_area = _signed_ring_area_km2(
            ring,
            center_longitude_deg=lon0,
            center_latitude_deg=lat0,
        )
        if not math.isfinite(signed_area):
            raise ValueError("non-finite Natural Earth Australia ring area")
        ring_rows.append((index, ring, signed_area))

    ordered = sorted(ring_rows, key=lambda item: abs(item[2]), reverse=True)
    mainland_index, mainland_ring, mainland_signed_area = ordered[0]
    if len(ordered) > 1 and abs(ordered[0][2]) <= abs(ordered[1][2]):
        raise ValueError("continental-mainland ring is not uniquely largest")
    mainland_area = abs(float(mainland_signed_area))
    if mainland_area < 5_000_000:
        raise ValueError(f"largest Australia ring is implausibly small for continental mainland: {mainland_area}")

    longitudes = [float(point[0]) for point in mainland_ring]
    latitudes = [float(point[1]) for point in mainland_ring]
    bbox = [min(longitudes), min(latitudes), max(longitudes), max(latitudes)]
    if not (110.0 < bbox[0] < 116.0 and -40.0 < bbox[1] < -32.0 and 150.0 < bbox[2] < 155.0 and -12.0 < bbox[3] < -9.0):
        raise ValueError(f"largest Australia ring has unexpected mainland bbox: {bbox}")

    ring_path = output_dir / "australia_continental_mainland_ring.csv"
    with ring_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["vertex", "longitude", "latitude"])
        for index, point in enumerate(mainland_ring):
            writer.writerow([index, f"{float(point[0]):.12f}", f"{float(point[1]):.12f}"])

    extracted_files = {}
    for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
        path = shp.with_suffix(suffix)
        if path.exists():
            extracted_files[path.name] = _sha256(path)

    version_files = sorted(extracted.rglob("*.VERSION.txt"))
    embedded_versions = {
        path.name: path.read_text(encoding="utf-8", errors="replace").strip()
        for path in version_files
    }

    manifest = {
        "status": "outcome_free_natural_earth_australia_mainland_freeze",
        "source_url": url,
        "declared_version_from_official_download_page": declared_version,
        "archive_sha256": _sha256(raw_zip),
        "archive_size_bytes": raw_zip.stat().st_size,
        "embedded_version_files": embedded_versions,
        "extracted_file_sha256": extracted_files,
        "fields": fields,
        "shape_type": shape.shapeTypeName,
        "australia_ring_count": len(rings),
        "selected_mainland_ring_index": int(mainland_index),
        "selected_mainland_point_count": len(mainland_ring),
        "selected_mainland_area_km2": mainland_area,
        "selected_mainland_bbox_lonlat": bbox,
        "selected_mainland_ring_sha256": _ring_digest(mainland_ring),
        "ring_csv_sha256": _sha256(ring_path),
        "species_outcomes_used": False,
        "sdm_outputs_used": False,
        "eog_outputs_used": False,
        "scientific_boundary": "fixed species-independent continental-mainland geometry only",
    }
    manifest_path = output_dir / "mainland_source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--declared-version", default=DEFAULT_VERSION)
    args = parser.parse_args()
    print(json.dumps(
        freeze_mainland(args.output_dir, url=args.url, declared_version=args.declared_version),
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
