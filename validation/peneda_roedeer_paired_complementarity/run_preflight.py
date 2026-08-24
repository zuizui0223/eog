from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import urllib.request
from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("source_contract.json")
RESULT_PATH = Path(__file__).with_name("preflight_result.json")


def stop(status: str, reason: str, **extra: object) -> None:
    result = {
        "schema": "eog.peneda_roedeer_preflight_result.v1",
        "status": status,
        "reason": reason,
        "response_requests": 0,
        "response_bytes": 0,
        "response_rows_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        **extra,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1)


def parse_dt(value: str) -> datetime:
    text = value.strip()
    if not text:
        raise ValueError("empty datetime")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def haversine_km(a: tuple[float, float], b: tuple[float, float], radius: float) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(math.sqrt(h))


def components(n: int, distances: list[list[float]], threshold: float) -> list[list[int]]:
    seen = [False] * n
    out: list[list[int]] = []
    for start in range(n):
        if seen[start]:
            continue
        stack = [start]
        seen[start] = True
        comp: list[int] = []
        while stack:
            i = stack.pop()
            comp.append(i)
            for j in range(n):
                if i != j and not seen[j] and distances[i][j] <= threshold:
                    seen[j] = True
                    stack.append(j)
        out.append(comp)
    return out


def lcc_thresholds(distances: list[list[float]], targets: list[float]) -> list[dict[str, float | int]]:
    n = len(distances)
    positive = sorted({distances[i][j] for i in range(n) for j in range(i + 1, n) if distances[i][j] > 0})
    if not positive:
        raise ValueError("no positive pairwise distances")
    results: list[dict[str, float | int]] = []
    for target in targets:
        chosen = positive[-1]
        chosen_comps = components(n, distances, chosen)
        for threshold in positive:
            comps = components(n, distances, threshold)
            if max(len(c) for c in comps) / n >= target:
                chosen = threshold
                chosen_comps = comps
                break
        lcc = max(len(c) for c in chosen_comps) / n
        isolated = sum(1 for c in chosen_comps if len(c) == 1) / n
        results.append(
            {
                "target": target,
                "threshold_km": chosen,
                "achieved_lcc_fraction": lcc,
                "components": len(chosen_comps),
                "isolated_fraction": isolated,
            }
        )
    return results


def iter_months(start: date, end: date):
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        yield y, m
        if m == 12:
            y += 1
            m = 1
        else:
            m += 1


def active_days_in_month(start: date, end: date, year: int, month: int) -> int:
    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])
    lo = max(start, month_start)
    hi = min(end, month_end)
    return max(0, (hi - lo).days + 1) if lo <= hi else 0


def next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    geometry = contract["geometry_semantics"]
    temporal = contract["temporal_semantics"]
    firewall = contract["response_firewall"]

    # One and only one preflight payload request: the response-independent deployments attachment.
    req = urllib.request.Request(
        firewall["deployment_geometry_url"],
        headers={
            "User-Agent": "EOG-prospective-validation/1.0 (response-blind geometry preflight)",
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            status_code = getattr(response, "status", 200)
            content_type = response.headers.get("Content-Type", "")
    except Exception as exc:
        stop(
            "stop_pre_response_geometry_transport_unavailable",
            repr(exc),
            deployment_requests=1,
            deployment_bytes=0,
        )

    if not raw:
        stop(
            "stop_pre_response_geometry_transport_unavailable",
            "deployment attachment returned zero bytes",
            deployment_requests=1,
            deployment_bytes=0,
        )

    deployment_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        stop(
            "stop_geometry_schema",
            f"deployment attachment is not UTF-8/UTF-8-SIG CSV: {exc}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            content_type=content_type,
        )

    reader = csv.DictReader(io.StringIO(text))
    fields = tuple(reader.fieldnames or ())
    required = tuple(geometry["required_fields"])
    missing = [field for field in required if field not in fields]
    if missing:
        stop(
            "stop_geometry_schema",
            f"missing prospectively required deployment fields: {missing}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            content_type=content_type,
            observed_fields=list(fields),
        )

    rows = list(reader)
    if len(rows) != int(geometry["expected_deployment_rows"]):
        stop(
            "stop_analysis_registry_not_closed",
            f"deployment row count {len(rows)} != frozen {geometry['expected_deployment_rows']}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            content_type=content_type,
            observed_fields=list(fields),
        )

    deployment_ids: set[str] = set()
    by_location_coords: dict[str, list[tuple[float, float]]] = defaultdict(list)
    deployments: list[tuple[str, date, date]] = []
    start_year_counts: dict[int, int] = defaultdict(int)

    try:
        for idx, row in enumerate(rows, start=2):
            deployment_id = row["deploymentID"].strip()
            location_id = row["locationID"].strip()
            if not deployment_id or not location_id:
                raise ValueError(f"empty deploymentID/locationID at physical row {idx}")
            if deployment_id in deployment_ids:
                raise ValueError(f"duplicate deploymentID {deployment_id!r}")
            deployment_ids.add(deployment_id)
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"invalid coordinates at physical row {idx}")
            start = parse_dt(row["start"]).date()
            end = parse_dt(row["end"]).date()
            if end < start:
                raise ValueError(f"end before start at physical row {idx}")
            by_location_coords[location_id].append((lat, lon))
            deployments.append((location_id, start, end))
            start_year_counts[start.year] += 1
    except Exception as exc:
        stop(
            "stop_analysis_registry_not_closed",
            str(exc),
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            content_type=content_type,
            observed_fields=list(fields),
        )

    if len(deployment_ids) != len(rows):
        stop("stop_analysis_registry_not_closed", "deployment IDs are not unique")
    if len(by_location_coords) != int(geometry["expected_unique_nodes"]):
        stop(
            "stop_analysis_registry_not_closed",
            f"unique location count {len(by_location_coords)} != frozen {geometry['expected_unique_nodes']}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
        )

    expected_years = set(contract["study"]["published_year_blocks"])
    if set(start_year_counts) != expected_years:
        stop(
            "stop_analysis_registry_not_closed",
            f"deployment start-year set {sorted(start_year_counts)} != frozen {sorted(expected_years)}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            start_year_counts=dict(sorted(start_year_counts.items())),
        )

    location_ids = sorted(by_location_coords)
    coords = [
        (
            median(p[0] for p in by_location_coords[location_id]),
            median(p[1] for p in by_location_coords[location_id]),
        )
        for location_id in location_ids
    ]
    radius = float(geometry["earth_radius_km"])
    n = len(coords)
    distances = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(coords[i], coords[j], radius)
            distances[i][j] = d
            distances[j][i] = d

    try:
        ladder = lcc_thresholds(distances, [float(x) for x in geometry["lcc_target_fractions"]])
    except Exception as exc:
        stop(
            "stop_structural_scale_diversity_failed",
            str(exc),
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
        )

    distinct = sorted({round(float(x["threshold_km"]), 12) for x in ladder if float(x["threshold_km"]) > 0})
    if len(distinct) < int(geometry["minimum_distinct_positive_thresholds"]):
        stop(
            "stop_structural_scale_diversity_failed",
            f"only {len(distinct)} distinct positive LCC thresholds: {distinct}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
        )

    lcc90 = ladder[-1]
    if float(lcc90["isolated_fraction"]) > float(geometry["maximum_isolated_fraction_at_lcc90"]):
        stop(
            "stop_structural_adequacy_failed",
            f"LCC90 isolated fraction {lcc90['isolated_fraction']} exceeds frozen maximum {geometry['maximum_isolated_fraction_at_lcc90']}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
        )

    # Response-independent effort ledger from deployment start/end dates.
    active_days: dict[tuple[str, int, int], int] = defaultdict(int)
    for location_id, start, end in deployments:
        for year, month in iter_months(start, end):
            active_days[(location_id, year, month)] += active_days_in_month(start, end, year, month)

    minimum_days = int(temporal["minimum_active_days_in_each_adjacent_month"])
    minimum_nodes = int(temporal["minimum_response_blind_eligible_nodes_per_scored_transition"])
    calibration_years = set(int(x) for x in temporal["calibration_years"])
    heldout_years = set(int(x) for x in temporal["heldout_years"])

    all_months = sorted({(year, month) for _, year, month in active_days})
    transition_counts: list[dict[str, object]] = []
    for year, month in all_months:
        y2, m2 = next_month(year, month)
        if (y2, m2) not in set(all_months):
            continue
        if year in calibration_years and y2 in calibration_years:
            split = "calibration"
        elif year in heldout_years and y2 in heldout_years:
            split = "heldout"
        else:
            continue
        eligible = [
            location_id
            for location_id in location_ids
            if active_days.get((location_id, year, month), 0) >= minimum_days
            and active_days.get((location_id, y2, m2), 0) >= minimum_days
        ]
        if len(eligible) >= minimum_nodes:
            transition_counts.append(
                {
                    "outer_unit": f"{year:04d}-{month:02d}->{y2:04d}-{m2:02d}",
                    "split": split,
                    "eligible_nodes": len(eligible),
                }
            )

    calibration_units = [x for x in transition_counts if x["split"] == "calibration"]
    heldout_units = [x for x in transition_counts if x["split"] == "heldout"]
    if len(calibration_units) < int(temporal["minimum_calibration_outer_units"]):
        stop(
            "stop_temporal_effort_inadequate",
            f"only {len(calibration_units)} response-blind calibration outer units clear the frozen effort gate",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
            scored_transitions=transition_counts,
        )
    if len(heldout_units) < int(temporal["minimum_heldout_outer_units"]):
        stop(
            "stop_temporal_effort_inadequate",
            f"only {len(heldout_units)} response-blind heldout outer units clear the frozen effort gate",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
            scored_transitions=transition_counts,
        )

    geometry_payload = {
        "location_ids": location_ids,
        "median_coordinates": [[lat, lon] for lat, lon in coords],
        "structural_ladder": ladder,
        "start_year_counts": dict(sorted(start_year_counts.items())),
        "scored_transitions": transition_counts,
    }
    geometry_fingerprint = hashlib.sha256(
        json.dumps(geometry_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    result = {
        "schema": "eog.peneda_roedeer_preflight_result.v1",
        "status": "ready_for_next_response_blind_freeze",
        "deployment_requests": 1,
        "deployment_bytes": len(raw),
        "deployment_sha256": deployment_sha256,
        "deployment_http_status": status_code,
        "deployment_content_type": content_type,
        "deployment_rows": len(rows),
        "unique_nodes": len(location_ids),
        "start_year_counts": dict(sorted(start_year_counts.items())),
        "structural_ladder": ladder,
        "distinct_positive_thresholds_km": distinct,
        "calibration_outer_units": len(calibration_units),
        "heldout_outer_units": len(heldout_units),
        "scored_transitions": transition_counts,
        "geometry_effort_fingerprint": geometry_fingerprint,
        "response_requests": 0,
        "response_bytes": 0,
        "response_rows_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
