from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median

CONTRACT_PATH = Path(__file__).with_name("source_contract.json")
RESULT_PATH = Path(__file__).with_name("preflight_result.json")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def write_result(payload: dict[str, object], *, exit_code: int = 0) -> None:
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    if exit_code:
        raise SystemExit(exit_code)


def stop(status: str, reason: str, **extra: object) -> None:
    write_result(
        {
            "schema": "eog.peneda_roedeer_preflight_result.v2",
            "status": status,
            "reason": reason,
            "response_requests": 0,
            "response_bytes": 0,
            "response_rows_opened": False,
            "response_values_opened": False,
            "model_fits": 0,
            "heldout_scores": 0,
            **extra,
        },
        exit_code=1,
    )


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
    result: list[list[int]] = []
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = True
        stack = [start]
        component: list[int] = []
        while stack:
            i = stack.pop()
            component.append(i)
            for j in range(n):
                if i != j and not seen[j] and distances[i][j] <= threshold:
                    seen[j] = True
                    stack.append(j)
        result.append(component)
    return result


def lcc_thresholds(
    distances: list[list[float]], targets: list[float]
) -> list[dict[str, float | int]]:
    n = len(distances)
    positive = sorted(
        {
            distances[i][j]
            for i in range(n)
            for j in range(i + 1, n)
            if distances[i][j] > 0
        }
    )
    if not positive:
        raise ValueError("no positive pairwise distances")
    rows: list[dict[str, float | int]] = []
    for target in targets:
        selected = positive[-1]
        selected_components = components(n, distances, selected)
        for threshold in positive:
            current = components(n, distances, threshold)
            if max(len(group) for group in current) / n >= target:
                selected = threshold
                selected_components = current
                break
        rows.append(
            {
                "target": target,
                "threshold_km": selected,
                "achieved_lcc_fraction": max(len(group) for group in selected_components) / n,
                "components": len(selected_components),
                "isolated_fraction": sum(len(group) == 1 for group in selected_components) / n,
            }
        )
    return rows


def deduplicated_hard_worlds(ladder: list[dict[str, float | int]]) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for row in ladder:
        threshold = float(row["threshold_km"])
        target = float(row["target"])
        match = next(
            (
                group
                for group in groups
                if math.isclose(float(group["threshold_km"]), threshold, rel_tol=0.0, abs_tol=1e-12)
            ),
            None,
        )
        target_label = int(round(target * 1000))
        if match is None:
            groups.append({"threshold_km": threshold, "targets_per_mille": [target_label]})
        else:
            match["targets_per_mille"].append(target_label)  # type: ignore[index]
    result = []
    for group in groups:
        labels = tuple(int(value) for value in group["targets_per_mille"])  # type: ignore[index]
        suffix = "_".join(str(value) for value in labels)
        result.append(
            {
                "world_id": f"geo_lcc{suffix}",
                "threshold_km": float(group["threshold_km"]),
                "targets_per_mille": list(labels),
            }
        )
    return result


def month_key(value: date) -> tuple[int, int]:
    return value.year, value.month


def next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


def month_text(value: tuple[int, int]) -> str:
    return f"{value[0]:04d}-{value[1]:02d}"


def quarter_text(value: tuple[int, int]) -> str:
    year, month = value
    return f"{year}_Q{((month - 1) // 3) + 1}"


def main() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    geometry = contract["geometry_semantics"]
    temporal = contract["temporal_semantics"]
    firewall = contract["response_firewall"]

    request = urllib.request.Request(
        firewall["deployment_geometry_url"],
        headers={
            "User-Agent": "EOG-prospective-validation/1.0 (response-blind geometry preflight)",
            "Accept": "text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read()
            http_status = int(getattr(response, "status", 200))
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
        )

    reader = csv.DictReader(io.StringIO(text))
    fields = tuple(reader.fieldnames or ())
    missing = [field for field in geometry["required_fields"] if field not in fields]
    if missing:
        stop(
            "stop_geometry_schema",
            f"missing prospectively required deployment fields: {missing}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
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
        )

    deployment_ids: set[str] = set()
    coords_by_location: dict[str, list[tuple[float, float]]] = defaultdict(list)
    active_dates: dict[tuple[str, int, int], set[date]] = defaultdict(set)
    start_year_counts: dict[int, int] = defaultdict(int)
    try:
        for physical_row, row in enumerate(rows, start=2):
            deployment_id = row["deploymentID"].strip()
            location_id = row["locationID"].strip()
            if not deployment_id or not location_id:
                raise ValueError(f"empty deployment/location identity at physical row {physical_row}")
            if deployment_id in deployment_ids:
                raise ValueError(f"duplicate deploymentID {deployment_id!r}")
            deployment_ids.add(deployment_id)
            latitude = float(row["latitude"])
            longitude = float(row["longitude"])
            if not (
                math.isfinite(latitude)
                and math.isfinite(longitude)
                and -90.0 <= latitude <= 90.0
                and -180.0 <= longitude <= 180.0
            ):
                raise ValueError(f"invalid coordinates at physical row {physical_row}")
            start = parse_dt(row["start"]).date()
            end = parse_dt(row["end"]).date()
            if end < start:
                raise ValueError(f"end before start at physical row {physical_row}")
            coords_by_location[location_id].append((latitude, longitude))
            start_year_counts[start.year] += 1
            current = start
            while current <= end:
                active_dates[(location_id, current.year, current.month)].add(current)
                current += timedelta(days=1)
    except Exception as exc:
        stop(
            "stop_analysis_registry_not_closed",
            str(exc),
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
        )

    if len(coords_by_location) != int(geometry["expected_unique_nodes"]):
        stop(
            "stop_analysis_registry_not_closed",
            f"unique location count {len(coords_by_location)} != frozen {geometry['expected_unique_nodes']}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
        )
    expected_start_years = set(int(value) for value in contract["study"]["published_year_blocks"])
    if set(start_year_counts) != expected_start_years:
        stop(
            "stop_analysis_registry_not_closed",
            f"deployment start-year set {sorted(start_year_counts)} != frozen {sorted(expected_start_years)}",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            start_year_counts=dict(sorted(start_year_counts.items())),
        )

    node_ids = sorted(coords_by_location)
    coordinates = [
        (
            median(point[0] for point in coords_by_location[node_id]),
            median(point[1] for point in coords_by_location[node_id]),
        )
        for node_id in node_ids
    ]
    radius = float(geometry["earth_radius_km"])
    n = len(node_ids)
    distances = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            value = haversine_km(coordinates[i], coordinates[j], radius)
            distances[i][j] = value
            distances[j][i] = value

    try:
        ladder = lcc_thresholds(
            distances, [float(value) for value in geometry["lcc_target_fractions"]]
        )
    except Exception as exc:
        stop(
            "stop_structural_scale_diversity_failed",
            str(exc),
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
        )
    hard_worlds = deduplicated_hard_worlds(ladder)
    if len(hard_worlds) < int(geometry["minimum_distinct_positive_thresholds"]):
        stop(
            "stop_structural_scale_diversity_failed",
            f"only {len(hard_worlds)} distinct positive LCC thresholds",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
            hard_worlds=hard_worlds,
        )
    if float(ladder[-1]["isolated_fraction"]) > float(
        geometry["maximum_isolated_fraction_at_lcc90"]
    ):
        stop(
            "stop_structural_adequacy_failed",
            "LCC90 isolated fraction exceeds the prospectively frozen maximum",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            structural_ladder=ladder,
            hard_worlds=hard_worlds,
        )

    minimum_days = int(temporal["minimum_active_days_in_each_adjacent_month"])
    minimum_nodes = int(temporal["minimum_response_blind_eligible_nodes_per_scored_transition"])
    calibration_years = set(int(value) for value in temporal["calibration_years"])
    heldout_years = set(int(value) for value in temporal["heldout_years"])
    months = sorted({(year, month) for _, year, month in active_dates})
    month_set = set(months)
    transitions: list[dict[str, object]] = []
    for source_month in months:
        target_month = next_month(*source_month)
        if target_month not in month_set:
            continue
        if source_month[0] in calibration_years and target_month[0] in calibration_years:
            split = "calibration"
        elif source_month[0] in heldout_years and target_month[0] in heldout_years:
            split = "heldout"
        else:
            continue
        eligible_ids = [
            node_id
            for node_id in node_ids
            if len(active_dates.get((node_id, *source_month), set())) >= minimum_days
            and len(active_dates.get((node_id, *target_month), set())) >= minimum_days
        ]
        if len(eligible_ids) >= minimum_nodes:
            transitions.append(
                {
                    "transition_id": f"{month_text(source_month)}->{month_text(target_month)}",
                    "source_month": month_text(source_month),
                    "target_month": month_text(target_month),
                    "split": split,
                    "eligible_nodes": len(eligible_ids),
                    "eligible_node_ids_sha256": canonical_sha256(eligible_ids),
                    "outer_unit_id": None if split == "calibration" else quarter_text(target_month),
                }
            )

    calibration_transitions = [row for row in transitions if row["split"] == "calibration"]
    heldout_transitions = [row for row in transitions if row["split"] == "heldout"]
    if len(calibration_transitions) < int(temporal["minimum_calibration_scored_transitions"]):
        stop(
            "stop_temporal_effort_inadequate",
            f"only {len(calibration_transitions)} calibration transitions clear the frozen effort gate",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            scored_transitions=transitions,
        )
    if len(heldout_transitions) < int(temporal["minimum_heldout_scored_transitions"]):
        stop(
            "stop_temporal_effort_inadequate",
            f"only {len(heldout_transitions)} heldout transitions clear the frozen effort gate",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            scored_transitions=transitions,
        )
    heldout_outer_ids = sorted(
        {str(row["outer_unit_id"]) for row in heldout_transitions if row["outer_unit_id"]}
    )
    if len(heldout_outer_ids) < int(contract["exact_outcome_count_minima"]["heldout_outer_units_with_both_classes"]):
        stop(
            "stop_temporal_score_unit_inadequate",
            f"only {len(heldout_outer_ids)} response-independent heldout quarter units exist",
            deployment_requests=1,
            deployment_bytes=len(raw),
            deployment_sha256=deployment_sha256,
            heldout_outer_ids=heldout_outer_ids,
        )

    raw_by_target = {float(row["target"]): float(row["threshold_km"]) for row in ladder}
    kernel_scale_km = raw_by_target[0.5]
    favorable_wins = len(heldout_outer_ids) // 2 + 1
    geometry_effort_payload = {
        "node_ids": node_ids,
        "coordinates": [[lat, lon] for lat, lon in coordinates],
        "deployment_sha256": deployment_sha256,
        "structural_ladder": ladder,
        "hard_worlds": hard_worlds,
        "kernel_scale_km": kernel_scale_km,
        "scored_transitions": transitions,
        "heldout_outer_ids": heldout_outer_ids,
    }
    result = {
        "schema": "eog.peneda_roedeer_preflight_result.v2",
        "status": "ready_for_next_response_blind_freeze",
        "deployment_requests": 1,
        "deployment_bytes": len(raw),
        "deployment_sha256": deployment_sha256,
        "deployment_http_status": http_status,
        "deployment_content_type": content_type,
        "deployment_rows": len(rows),
        "deployment_field_names": list(fields),
        "unique_nodes": len(node_ids),
        "node_ids": node_ids,
        "median_coordinates": [[lat, lon] for lat, lon in coordinates],
        "start_year_counts": dict(sorted(start_year_counts.items())),
        "structural_ladder": ladder,
        "hard_worlds": hard_worlds,
        "full_world_id": "geo_exponential_full",
        "kernel_scale_km": kernel_scale_km,
        "calibration_scored_transitions": len(calibration_transitions),
        "heldout_scored_transitions": len(heldout_transitions),
        "heldout_outer_ids": heldout_outer_ids,
        "expected_outer_score_units": len(heldout_outer_ids),
        "favorable_min_augmented_wins": favorable_wins,
        "adverse_min_baseline_wins": favorable_wins,
        "scored_transitions": transitions,
        "geometry_effort_fingerprint": canonical_sha256(geometry_effort_payload),
        "response_requests": 0,
        "response_bytes": 0,
        "response_rows_opened": False,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
    }
    write_result(result)


if __name__ == "__main__":
    main()
