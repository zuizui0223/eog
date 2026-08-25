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

import numpy as np

from eog.v2.world_adequacy import (
    StructuralAdequacyDeclaration,
    apply_structural_adequacy_gate,
    audit_world_universe_structure,
)
from eog.v2.world_scale_ladder import (
    StructuralScaleLadderDeclaration,
    build_structural_scale_ladder,
    structural_scale_adjacencies,
)

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "validation/azores_yellow_eel_paired_complementarity/source_contract.json"
OUT_DIR = ROOT / "build/azores_yellow_eel_stage1"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "preflight.json"
contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

result = {
    "attempt_id": contract["attempt_id"],
    "status": "not_evaluated",
    "zenodo_metadata_requests": 0,
    "deployment_payload_requests": 0,
    "deployment_payload_bytes_opened": 0,
    "eel_metadata_payload_requests": 0,
    "eel_metadata_payload_bytes_opened": 0,
    "response_payload_requests": 0,
    "response_payload_bytes_opened": 0,
    "response_header_bytes_opened": 0,
    "response_rows_opened": False,
    "response_values_opened": False,
    "model_fits": 0,
    "heldout_scores": 0,
}


def finish(status: str, **extra) -> None:
    result.update(extra)
    result["status"] = status
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))


def fail(status: str, reason: str, **extra) -> None:
    finish(status, reason=reason, **extra)
    raise SystemExit(3)


def get_json(url: str, maximum: int = 5_000_000) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Azores-eel-stage1/1.0", "Accept": "application/json", "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=60) as response:
        body = response.read(maximum + 1)
        status = int(getattr(response, "status", 200))
    if status != 200 or len(body) > maximum:
        fail("stop_source_transport", "bounded Zenodo metadata request failed", url=url, http_status=status, bytes=len(body))
    return json.loads(body.decode("utf-8"))


def get_bytes(url: str, role: str, maximum: int) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "EOG-Azores-eel-stage1/1.0", "Accept-Encoding": "identity"})
    if role == "deployment":
        result["deployment_payload_requests"] += 1
    elif role == "eel_metadata":
        result["eel_metadata_payload_requests"] += 1
    else:
        raise RuntimeError("stage1 may not request any other payload role")
    with urllib.request.urlopen(req, timeout=90) as response:
        body = response.read(maximum + 1)
        status = int(getattr(response, "status", 200))
    if status != 200 or len(body) > maximum:
        fail("stop_source_transport", f"bounded {role} payload request failed", http_status=status, bytes=len(body))
    if role == "deployment":
        result["deployment_payload_bytes_opened"] = len(body)
    else:
        result["eel_metadata_payload_bytes_opened"] = len(body)
    return body


def md5_hex(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()


def parse_csv(payload: bytes, expected_header: list[str], role: str) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        fail("stop_source_schema", f"{role} is not UTF-8 decodable")
    reader = csv.DictReader(io.StringIO(text))
    observed = list(reader.fieldnames or [])
    if observed != expected_header:
        fail("stop_source_schema", f"{role} physical header mismatch", observed_header=observed, expected_header=expected_header)
    rows = list(reader)
    if not rows:
        fail("stop_source_schema", f"{role} has zero rows")
    return rows


def parse_dt(value: str) -> datetime:
    token = str(value).strip()
    try:
        return datetime.fromisoformat(token)
    except ValueError:
        fail("stop_source_schema", "invalid ISO date-time", token=token)


def parse_optional_dt(value: str) -> datetime | None:
    token = str(value).strip()
    if token in {"", "NA", "NaN", "nan", "None"}:
        return None
    return parse_dt(token)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    radius = float(contract["deployment_semantics"]["earth_radius_km"])
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(h)))


def first_monday_strictly_after(day: date) -> date:
    delta = (7 - day.weekday()) % 7
    if delta == 0:
        delta = 7
    return day + timedelta(days=delta)


# 1. Exact Zenodo record metadata. Response FILE metadata may be inventoried; response payload remains forbidden.
record_id = int(contract["scientific_anchor"]["dataset_record"])
metadata = get_json(f"https://zenodo.org/api/records/{record_id}")
result["zenodo_metadata_requests"] = 1
if int(metadata.get("id")) != record_id:
    fail("stop_source_identity", "Zenodo record id mismatch", observed=metadata.get("id"), expected=record_id)
files = metadata.get("files") or []
by_name = {str(row.get("key") or ""): row for row in files}
for role, spec in contract["public_files"].items():
    name = spec["name"]
    if name not in by_name:
        fail("stop_source_identity", "required public file is missing", role=role, name=name, observed_files=sorted(by_name))
    checksum = str(by_name[name].get("checksum") or "")
    observed_md5 = checksum.split(":", 1)[-1] if checksum else ""
    if observed_md5 != spec["md5"]:
        fail("stop_source_identity", "public file MD5 changed", role=role, observed_md5=observed_md5, expected_md5=spec["md5"])

# 2. Open only deployment and eel metadata payloads.
def content_url(name: str) -> str:
    row = by_name[name]
    links = row.get("links") or {}
    url = str(links.get("content") or links.get("self") or "")
    if not url:
        fail("stop_source_identity", "Zenodo file content URL missing", name=name)
    return url

deploy_spec = contract["public_files"]["deployment"]
eel_spec = contract["public_files"]["eel_metadata"]
deploy_bytes = get_bytes(content_url(deploy_spec["name"]), "deployment", 2_000_000)
eel_bytes = get_bytes(content_url(eel_spec["name"]), "eel_metadata", 1_000_000)
if md5_hex(deploy_bytes) != deploy_spec["md5"]:
    fail("stop_source_identity", "deployment payload MD5 mismatch")
if md5_hex(eel_bytes) != eel_spec["md5"]:
    fail("stop_source_identity", "eel metadata payload MD5 mismatch")

deploy_rows = parse_csv(deploy_bytes, contract["deployment_semantics"]["expected_physical_header"], "deployment")
eel_rows = parse_csv(eel_bytes, contract["eel_metadata_semantics"]["expected_physical_header"], "eel_metadata")

# 3. Closed response-independent study receiver registry: exact integer prefix 148..157.
study_rows: list[dict] = []
for row in deploy_rows:
    project = str(row["acoustic_project_code"]).strip()
    station = str(row["station_name"]).strip()
    parts = station.split(maxsplit=1)
    prefix = int(parts[0]) if parts and parts[0].isdigit() else None
    if project == "AZO" and prefix is not None and 148 <= prefix <= 157 and station == f"{prefix} FLO CRUZ":
        study_rows.append({**row, "station_name": station})
stations = sorted({row["station_name"] for row in study_rows}, key=lambda value: int(value.split()[0]))
if len(stations) != int(contract["deployment_semantics"]["expected_study_station_count"]):
    fail("stop_analysis_registry_not_closed", "study station rule did not yield exactly ten stations", stations=stations)
if stations != [f"{value} FLO CRUZ" for value in range(148, 158)]:
    fail("stop_analysis_registry_not_closed", "study station IDs differ from frozen 148-157 registry", stations=stations)

coords_by_station: dict[str, list[tuple[float, float]]] = defaultdict(list)
intervals_by_station: dict[str, list[tuple[datetime, datetime | None]]] = defaultdict(list)
for row in study_rows:
    try:
        lat = float(row["deploy_latitude"])
        lon = float(row["deploy_longitude"])
    except ValueError:
        fail("stop_source_schema", "non-numeric study receiver coordinate", station=row["station_name"])
    if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        fail("stop_source_schema", "invalid study receiver coordinate", station=row["station_name"])
    coords_by_station[row["station_name"]].append((lat, lon))
    start = parse_dt(row["deploy_date_time"])
    end = parse_optional_dt(row["recover_date_time"])
    if end is not None and end < start:
        fail("stop_source_schema", "receiver recovery precedes deployment", station=row["station_name"])
    intervals_by_station[row["station_name"]].append((start, end))

station_coords: dict[str, tuple[float, float]] = {}
for station in stations:
    values = coords_by_station[station]
    if not values:
        fail("stop_analysis_registry_not_closed", "study station has no deployment coordinate", station=station)
    station_coords[station] = (
        float(np.median([value[0] for value in values])),
        float(np.median([value[1] for value in values])),
    )

# 4. Response-independent 36-yellow-eel registry and release anchors.
eel_sem = contract["eel_metadata_semantics"]
raw_tags: list[dict] = []
for row in eel_rows:
    if str(row["animal_project_code"]).strip() != eel_sem["required_animal_project_code"]:
        fail("stop_source_schema", "unexpected animal_project_code in eel metadata")
    if str(row["scientific_name"]).strip() != eel_sem["required_scientific_name"]:
        fail("stop_source_schema", "unexpected scientific_name in eel metadata")
    tag = str(row["acoustic_tag_id"]).strip().replace(
        contract["predeclared_source_processing"]["tag_prefix_normalization"]["from"],
        contract["predeclared_source_processing"]["tag_prefix_normalization"]["to"],
    )
    release_dt = parse_dt(row["release_date_time"])
    try:
        release_coord = (float(row["release_latitude"]), float(row["release_longitude"]))
    except ValueError:
        fail("stop_source_schema", "non-numeric eel release coordinate", tag=tag)
    raw_tags.append({"tag": tag, "release_dt": release_dt, "release_coord": release_coord, "release_location": str(row["release_location"]).strip()})
if len(raw_tags) != int(eel_sem["expected_raw_tag_records"]):
    fail("stop_analysis_registry_not_closed", "unexpected raw eel metadata tag count", observed=len(raw_tags), expected=eel_sem["expected_raw_tag_records"])
if len({row["tag"] for row in raw_tags}) != len(raw_tags):
    fail("stop_analysis_registry_not_closed", "eel metadata contains duplicate normalized tags")
target_tags = [row for row in raw_tags if row["tag"] != contract["predeclared_source_processing"]["excluded_non_yellow_tag"]]
if len(target_tags) != int(eel_sem["expected_yellow_target_tags_after_predeclared_exclusion"]):
    fail("stop_analysis_registry_not_closed", "yellow target tag count differs from frozen 36", observed=len(target_tags))

release_anchor_by_tag: dict[str, str] = {}
release_anchor_distance_km: dict[str, float] = {}
for row in target_tags:
    distances = {station: haversine_km(row["release_coord"], station_coords[station]) for station in stations}
    station = min(stations, key=lambda value: (distances[value], value))
    release_anchor_by_tag[row["tag"]] = station
    release_anchor_distance_km[row["tag"]] = float(distances[station])
release_anchor_stations = sorted(set(release_anchor_by_tag.values()), key=lambda value: int(value.split()[0]))
latest_release = max(row["release_dt"] for row in target_tags)
first_week_start = first_monday_strictly_after(latest_release.date())
study_end = date.fromisoformat(contract["temporal_design"]["study_coverage_end"])
week_starts: list[date] = []
cursor = first_week_start
while cursor + timedelta(days=6) <= study_end:
    week_starts.append(cursor)
    cursor += timedelta(days=7)
calibration_n = int(contract["temporal_design"]["calibration_full_weeks"])
if len(week_starts) <= calibration_n:
    fail("stop_insufficient_outer_units", "response-independent study calendar has no heldout weeks", full_weeks=len(week_starts), calibration_weeks=calibration_n)
calibration_weeks = week_starts[:calibration_n]
heldout_weeks = week_starts[calibration_n:]
full_heldout_blocks = [heldout_weeks[index:index + 4] for index in range(0, len(heldout_weeks) - 3, 4)]
if len(full_heldout_blocks) < int(contract["temporal_design"]["exact_count_minima"]["heldout_full_four_week_blocks_with_both_classes"]):
    fail("stop_insufficient_outer_units", "fewer than four response-independent full heldout blocks", block_count=len(full_heldout_blocks))

# 5. Receiver-week effort, with missing recoveries clipped only to the frozen study end.
min_active_days = int(contract["deployment_semantics"]["receiver_week_minimum_active_days"])
receiver_week_effort: list[dict] = []
for station in stations:
    intervals = intervals_by_station[station]
    for week_start in week_starts:
        week_end = week_start + timedelta(days=6)
        active_dates: set[date] = set()
        for start_dt, end_dt in intervals:
            start_day = max(start_dt.date(), week_start)
            raw_end = study_end if end_dt is None else min(end_dt.date(), study_end)
            end_day = min(raw_end, week_end)
            if end_day < start_day:
                continue
            day = start_day
            while day <= end_day:
                active_dates.add(day)
                day += timedelta(days=1)
        receiver_week_effort.append({
            "station": station,
            "week_start": week_start.isoformat(),
            "active_days": len(active_dates),
            "eligible": len(active_dates) >= min_active_days,
        })
eligible_receiver_weeks = [row for row in receiver_week_effort if row["eligible"]]
if not eligible_receiver_weeks:
    fail("stop_response_independent_availability_not_closed", "no receiver-week passes frozen effort rule")
eligible_by_week = defaultdict(int)
for row in eligible_receiver_weeks:
    eligible_by_week[row["week_start"]] += 1
if min(eligible_by_week.get(week.isoformat(), 0) for week in week_starts) < 1:
    fail("stop_response_independent_availability_not_closed", "a scored week has no active study receiver")

# 6. Standard response-blind structural ladder on median study-receiver coordinates.
n = len(stations)
distance_matrix = np.zeros((n, n), dtype=float)
for i, station_i in enumerate(stations):
    for j in range(i + 1, n):
        station_j = stations[j]
        d = haversine_km(station_coords[station_i], station_coords[station_j])
        distance_matrix[i, j] = distance_matrix[j, i] = d
ladder = build_structural_scale_ladder(
    stations,
    distance_matrix,
    StructuralScaleLadderDeclaration(
        axis_id="azores_yellow_eel_receiver_geometry",
        target_largest_component_fractions=tuple(float(value) for value in contract["deployment_semantics"]["structural_lcc_targets"]),
    ),
)
adjacencies = structural_scale_adjacencies(ladder, distance_matrix)
distinct_positive_thresholds = sorted({round(float(level.distance_threshold), 12) for level in ladder.levels if float(level.distance_threshold) > 0})
if len(distinct_positive_thresholds) < int(contract["deployment_semantics"]["minimum_distinct_positive_thresholds"]):
    fail("stop_structural_scale_collapse", "fewer than three distinct positive structural thresholds", thresholds=distinct_positive_thresholds)

# Deduplicate identical adjacency matrices before later Layer-B construction.
unique_worlds: dict[str, np.ndarray] = {}
world_target_labels: dict[str, list[str]] = {}
for level in ladder.levels:
    adjacency = adjacencies[level.level_id]
    fingerprint = hashlib.sha256(np.asarray(adjacency, dtype=np.uint8).tobytes()).hexdigest()
    if fingerprint not in unique_worlds:
        unique_worlds[fingerprint] = adjacency
        world_target_labels[fingerprint] = []
    world_target_labels[fingerprint].append(level.level_id)
if len(unique_worlds) < int(contract["deployment_semantics"]["minimum_distinct_positive_thresholds"]):
    fail("stop_structural_scale_collapse", "fewer than three distinct adjacency worlds after deduplication", unique_world_count=len(unique_worlds))
worlds = {f"geometry_world_{index + 1}": adjacency for index, adjacency in enumerate(unique_worlds.values())}
audit = audit_world_universe_structure(stations, worlds, horizon=1)
gate = apply_structural_adequacy_gate(
    audit,
    StructuralAdequacyDeclaration(
        min_largest_weak_component_fraction=float(contract["deployment_semantics"]["adequacy_min_largest_weak_component_fraction"]),
        max_isolated_node_fraction=float(contract["deployment_semantics"]["adequacy_max_isolated_node_fraction"]),
        require_at_least_one_world_pass=True,
    ),
)
if not gate.passed:
    fail("stop_structural_universe_inadequate", "no deduplicated receiver geometry world passes frozen adequacy gate")
most_spanning = max(ladder.levels, key=lambda level: level.target_largest_component_fraction)
most_spanning_fp = hashlib.sha256(np.asarray(adjacencies[most_spanning.level_id], dtype=np.uint8).tobytes()).hexdigest()
passing_fps = {
    hashlib.sha256(np.asarray(worlds[world_id], dtype=np.uint8).tobytes()).hexdigest()
    for world_id in gate.passing_world_ids
}
if most_spanning_fp not in passing_fps:
    fail("stop_structural_universe_inadequate", "most-spanning LCC90 receiver world does not pass frozen adequacy gate")

# 7. Freeze only response-blind evidence. Detection file header/payload remain untouched.
registry_payload = [{"station": station, "lat": station_coords[station][0], "lon": station_coords[station][1]} for station in stations]
availability_payload = sorted(receiver_week_effort, key=lambda row: (row["week_start"], row["station"]))
finish(
    "stage1_registry_availability_and_structural_pass",
    zenodo_record_id=record_id,
    public_file_inventory={name: {"size": int(row.get("size") or 0), "checksum": str(row.get("checksum") or "")} for name, row in sorted(by_name.items())},
    deployment_row_count=len(deploy_rows),
    study_deployment_row_count=len(study_rows),
    study_stations=stations,
    station_coordinates=registry_payload,
    station_registry_fingerprint=hashlib.sha256(json.dumps(registry_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    raw_eel_tag_count=len(raw_tags),
    yellow_target_tag_count=len(target_tags),
    yellow_target_tags=sorted(row["tag"] for row in target_tags),
    excluded_non_yellow_tag=contract["predeclared_source_processing"]["excluded_non_yellow_tag"],
    latest_yellow_release_datetime=latest_release.isoformat(sep=" "),
    release_anchor_stations=release_anchor_stations,
    release_anchor_by_tag=release_anchor_by_tag,
    maximum_release_to_anchor_distance_km=max(release_anchor_distance_km.values()),
    first_scored_week_start=first_week_start.isoformat(),
    full_scored_week_count=len(week_starts),
    calibration_week_count=len(calibration_weeks),
    calibration_week_starts=[value.isoformat() for value in calibration_weeks],
    heldout_week_count=len(heldout_weeks),
    heldout_week_starts=[value.isoformat() for value in heldout_weeks],
    full_four_week_heldout_block_count=len(full_heldout_blocks),
    full_four_week_heldout_blocks=[[value.isoformat() for value in block] for block in full_heldout_blocks],
    eligible_receiver_week_count=len(eligible_receiver_weeks),
    eligible_receiver_count_by_week={key: eligible_by_week[key] for key in sorted(eligible_by_week)},
    availability_fingerprint=hashlib.sha256(json.dumps(availability_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    structural_ladder_fingerprint=ladder.fingerprint,
    structural_levels=[{
        "level_id": level.level_id,
        "target_lcc": level.target_largest_component_fraction,
        "threshold_km": level.distance_threshold,
        "achieved_lcc": level.achieved_largest_component_fraction,
        "isolated_node_fraction": level.isolated_node_fraction,
        "adjacency_fingerprint": hashlib.sha256(np.asarray(adjacencies[level.level_id], dtype=np.uint8).tobytes()).hexdigest(),
    } for level in ladder.levels],
    distinct_positive_structural_thresholds_km=distinct_positive_thresholds,
    deduplicated_geometry_world_count=len(unique_worlds),
    deduplicated_world_target_labels=list(world_target_labels.values()),
    structural_audit_fingerprint=audit.fingerprint,
    structural_gate_fingerprint=gate.fingerprint,
    structural_passing_world_ids=list(gate.passing_world_ids),
    response_payload_requests=0,
    response_payload_bytes_opened=0,
    response_header_bytes_opened=0,
    response_rows_opened=False,
    response_values_opened=False,
    model_fits=0,
    heldout_scores=0,
)
