#!/usr/bin/env python3
"""Response-blind deployment probe for the Snapshot USA Herrera array.

This script downloads only the frozen deployment table.  It never requests the
sequence/response file.  The output is deliberately descriptive: it determines
whether a later prospective paired-complementarity freeze is even possible.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path


DEPLOYMENT_URL = "https://datadryad.org/downloads/file_stream/4016828"
DEPLOYMENT_SIZE = 1_731_332
DEPLOYMENT_SHA256 = "9e837bba556de86af5934abcb5d8a487206df2b340a8b28fa8cc135c7bb7ec56"
FOCAL_ARRAY = "Herrera"
YEARS = (2019, 2020, 2021, 2022, 2023)
PERIOD_DAYS = 7
PERIOD_COUNT = 7
MIN_COMPLETE_SITES = 40


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, path: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.1",
            "User-Agent": "eog-response-blind-preflight/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            output.write(chunk)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    x = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 6371.0088 * 2.0 * math.asin(math.sqrt(x))


def _covered(intervals: list[tuple[date, date]], start: date, end: date) -> bool:
    """Return whether inclusive intervals cover every day from start through end."""
    cursor = start
    for left, right in sorted(intervals):
        if right < cursor:
            continue
        if left > cursor:
            return False
        cursor = max(cursor, right + timedelta(days=1))
        if cursor > end:
            return True
    return cursor > end


def _best_block(
    year: int,
    intervals_by_site: dict[str, list[tuple[date, date]]],
) -> dict[str, object]:
    first = date(year, 8, 1)
    last_start = date(year, 12, 29) - timedelta(days=PERIOD_DAYS * PERIOD_COUNT - 1)
    candidates: list[tuple[int, int, date, list[list[str]]]] = []
    start = first
    while start <= last_start:
        eligible_by_period: list[list[str]] = []
        for period in range(PERIOD_COUNT):
            left = start + timedelta(days=PERIOD_DAYS * period)
            right = left + timedelta(days=PERIOD_DAYS - 1)
            eligible_by_period.append(
                sorted(
                    site
                    for site, intervals in intervals_by_site.items()
                    if _covered(intervals, left, right)
                )
            )
        counts = [len(sites) for sites in eligible_by_period]
        all_period_sites = sorted(set.intersection(*(set(x) for x in eligible_by_period)))
        candidates.append((min(counts), len(all_period_sites), start, eligible_by_period))
        start += timedelta(days=1)

    # Maximize the weakest period, then the complete seven-period registry;
    # the earliest calendar start is the deterministic final tie-breaker.
    best = max(candidates, key=lambda x: (x[0], x[1], -x[2].toordinal()))
    minimum, complete_count, start, eligible_by_period = best
    periods = []
    for index, sites in enumerate(eligible_by_period):
        left = start + timedelta(days=PERIOD_DAYS * index)
        right = left + timedelta(days=PERIOD_DAYS - 1)
        periods.append(
            {
                "index": index,
                "start": left.isoformat(),
                "end": right.isoformat(),
                "eligible_site_count": len(sites),
            }
        )
    complete_sites = sorted(set.intersection(*(set(x) for x in eligible_by_period)))
    return {
        "year": year,
        "start": start.isoformat(),
        "periods": periods,
        "minimum_period_site_count": minimum,
        "complete_all_period_site_count": complete_count,
        "complete_all_period_sites": complete_sites,
    }


def main(output_path: Path) -> None:
    deployment_path = output_path.parent / "ssusa_finaldeployments.csv"
    _download(DEPLOYMENT_URL, deployment_path)
    actual_size = deployment_path.stat().st_size
    actual_sha256 = _sha256(deployment_path)
    if actual_size != DEPLOYMENT_SIZE or actual_sha256 != DEPLOYMENT_SHA256:
        raise RuntimeError(
            f"deployment identity mismatch: size={actual_size}, sha256={actual_sha256}"
        )

    with deployment_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = list(reader.fieldnames or [])
        rows = [row for row in reader if row.get("Camera_Trap_Array", "").strip() == FOCAL_ARRAY]

    expected_header = [
        "Year",
        "Project",
        "Camera_Trap_Array",
        "Site_Name",
        "Deployment_ID",
        "Start_Date",
        "End_Date",
        "Survey_Nights",
        "Latitude",
        "Longitude",
        "Habitat",
        "Development_Level",
        "Feature_Type",
    ]
    if header != expected_header:
        raise RuntimeError(f"unexpected deployment header: {header!r}")
    if not rows:
        raise RuntimeError(f"array {FOCAL_ARRAY!r} absent")

    intervals: dict[int, dict[str, list[tuple[date, date]]]] = defaultdict(lambda: defaultdict(list))
    coords: dict[str, list[tuple[float, float]]] = defaultdict(list)
    deployment_ids: set[str] = set()
    survey_nights_sum = 0
    for row in rows:
        year = int(float(row["Year"]))
        site = row["Site_Name"].strip()
        deployment_id = row["Deployment_ID"].strip()
        if not site or not deployment_id:
            raise RuntimeError("empty site or deployment identity")
        left = _parse_date(row["Start_Date"])
        right = _parse_date(row["End_Date"])
        if right < left or year != left.year:
            raise RuntimeError(f"invalid deployment interval: {deployment_id}")
        intervals[year][site].append((left, right))
        coords[site].append((float(row["Latitude"]), float(row["Longitude"])))
        if deployment_id in deployment_ids:
            raise RuntimeError(f"duplicate deployment ID: {deployment_id}")
        deployment_ids.add(deployment_id)
        survey_nights_sum += int(float(row["Survey_Nights"]))

    coordinate_spans = {
        site: max((_haversine_km(a, b) for a in values for b in values), default=0.0)
        for site, values in coords.items()
    }
    max_coordinate_span_km = max(coordinate_spans.values(), default=0.0)
    coordinate_conflicts = sorted(site for site, span in coordinate_spans.items() if span > 0.1)

    blocks = [_best_block(year, intervals.get(year, {})) for year in YEARS]
    status = "eligible_for_full_response_blind_freeze"
    reasons: list[str] = []
    if sorted(intervals) != list(YEARS):
        status = "ineligible_pre_response"
        reasons.append("frozen five-year coverage is incomplete")
    if coordinate_conflicts:
        status = "ineligible_pre_response"
        reasons.append("site-name coordinate span exceeds 100 m")
    if any(int(block["minimum_period_site_count"]) < MIN_COMPLETE_SITES for block in blocks):
        status = "ineligible_pre_response"
        reasons.append("at least one year has fewer than 40 fully active sites in its best seven-week block")

    result = {
        "schema": "snapshot_usa_herrera_response_blind_deployment_probe_v1",
        "status": status,
        "reasons": reasons,
        "source": {
            "dataset_doi": "10.5061/dryad.k0p2ngfhn",
            "dryad_version_id": 358059,
            "dryad_version_number": 6,
            "file_id": 4016828,
            "file_name": "ssusa_finaldeployments.csv",
            "bytes": actual_size,
            "sha256": actual_sha256,
        },
        "response_firewall": {
            "response_file_id": 4016829,
            "response_file_name": "ssusa_finalsequences.csv",
            "response_file_bytes_published": 206_672_092,
            "response_file_sha256_published": "8a442b130f11272c354de10ff97f69c65ae738a6514459f1431e963708011ded",
            "response_requests": 0,
            "response_bytes_opened": 0,
            "response_rows_or_values_opened": False,
        },
        "focal_array": FOCAL_ARRAY,
        "deployment_rows": len(rows),
        "deployment_ids": len(deployment_ids),
        "unique_sites": len(coords),
        "survey_nights_sum": survey_nights_sum,
        "years": sorted(intervals),
        "sites_by_year": {str(year): len(intervals[year]) for year in sorted(intervals)},
        "max_same_site_coordinate_span_km": max_coordinate_span_km,
        "coordinate_conflict_sites": coordinate_conflicts,
        "selection_rule": {
            "window": "seven consecutive 7-day calendar periods within 1 Aug--29 Dec",
            "objective": "maximize minimum eligible-site count, then complete seven-period site count, then earliest start",
            "minimum_complete_sites_per_period": MIN_COMPLETE_SITES,
        },
        "selected_blocks": blocks,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    canonical = json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    result["fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: probe_deployments.py OUTPUT_JSON")
    destination = Path(sys.argv[1])
    destination.parent.mkdir(parents=True, exist_ok=True)
    main(destination)
