from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import urllib.request

import numpy as np
import sklearn

from eog.v2.predictive_complementarity import PredictiveComplementarityDeclaration

from runner_core import (
    AllWorldsEliminated,
    build_prepared_rows,
    canonical_sha256,
    exact_count_gate,
    fit_and_score_paired,
    haversine_km,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "validation/azores_yellow_eel_paired_complementarity"
OUT_DIR = ROOT / "build/azores_yellow_eel_outcome"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT = OUT_DIR / "terminal_result.json"

SPEC = json.loads((HERE / "full_freeze_spec.json").read_text(encoding="utf-8"))
SOURCE = json.loads((HERE / "source_contract.json").read_text(encoding="utf-8"))
STAGE1 = json.loads((HERE / "stage1_certificate.json").read_text(encoding="utf-8"))
HEADER = json.loads((HERE / "header_certificate.json").read_text(encoding="utf-8"))
AUTH = json.loads((HERE / "outcome_access_authorization.json").read_text(encoding="utf-8"))
MARKER = json.loads((HERE / "OUTCOME_AUTHORIZED_ONCE").read_text(encoding="utf-8"))

AUDIT = {
    "attempt_id": SPEC["attempt_id"],
    "response_payload_requests": 0,
    "response_payload_bytes_opened": 0,
    "response_rows_opened": False,
    "response_values_opened": False,
    "raw_data_rows_seen": 0,
    "model_fits": 0,
    "primary_outer_units_scored": 0,
}


def write_terminal(status: str, **extra) -> None:
    payload = {
        "schema": "eog.azores_yellow_eel_terminal_result.v1",
        "attempt_id": SPEC["attempt_id"],
        "status": status,
        "audit": dict(AUDIT),
        **extra,
    }
    payload["fingerprint"] = canonical_sha256(payload)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))


def stop(status: str, reason: str, **extra) -> None:
    write_terminal(status, reason=reason, **extra)
    raise SystemExit(3)


def parse_dt(value: str) -> datetime:
    token = str(value).strip()
    if not token:
        raise ValueError("empty datetime")
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    return datetime.fromisoformat(token)


def parse_optional_dt(value: str) -> datetime | None:
    token = str(value).strip()
    if token in {"", "NA", "NaN", "nan", "None"}:
        return None
    return parse_dt(token)


def first_monday_strictly_after(day: date) -> date:
    delta = (7 - day.weekday()) % 7
    if delta == 0:
        delta = 7
    return day + timedelta(days=delta)


def bounded_json(url: str, maximum: int = 5_000_000) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-Azores-eel-once-only/1.0", "Accept": "application/json", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read(maximum + 1)
        status = int(getattr(response, "status", 200))
    if status != 200 or len(body) > maximum:
        stop("terminal_pre_response_source_transport_failure", "bounded Zenodo metadata request failed", http_status=status, observed_bytes=len(body))
    return json.loads(body.decode("utf-8"))


def bounded_file(url: str, maximum: int, expected_md5: str, role: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EOG-Azores-eel-once-only/1.0", "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        body = response.read(maximum + 1)
        status = int(getattr(response, "status", 200))
    if status != 200 or len(body) > maximum:
        stop("terminal_pre_response_source_transport_failure", f"bounded {role} request failed", http_status=status, observed_bytes=len(body))
    observed_md5 = hashlib.md5(body).hexdigest()
    if observed_md5 != expected_md5:
        stop("terminal_pre_response_source_identity_failure", f"{role} MD5 mismatch", observed_md5=observed_md5, expected_md5=expected_md5)
    return body


def parse_csv_bytes(payload: bytes, expected_header: list[str], role: str) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        stop("terminal_pre_response_source_schema_failure", f"{role} is not UTF-8 decodable")
    reader = csv.DictReader(io.StringIO(text))
    observed = list(reader.fieldnames or [])
    if observed != expected_header:
        stop("terminal_pre_response_source_schema_failure", f"{role} header mismatch", observed_header=observed, expected_header=expected_header)
    rows = list(reader)
    if not rows:
        stop("terminal_pre_response_source_schema_failure", f"{role} has zero rows")
    return rows


def validate_authorization_and_runtime() -> None:
    if AUTH.get("status") != "authorized_once_only_exact_count_gate_required":
        stop("terminal_authorization_failure", "committed outcome authorization is not green")
    if AUTH.get("response_rows_opened") is not False or AUTH.get("model_fits") != 0:
        stop("terminal_authorization_failure", "authorization certificate does not precede response rows")
    if MARKER.get("attempt_id") != SPEC["attempt_id"]:
        stop("terminal_authorization_failure", "authorization marker attempt mismatch")
    if MARKER.get("authorization_fingerprint") != AUTH.get("fingerprint"):
        stop("terminal_authorization_failure", "authorization marker fingerprint mismatch")
    if MARKER.get("full_freeze_spec_sha256") != AUTH.get("full_freeze_spec_sha256"):
        stop("terminal_authorization_failure", "authorization marker freeze fingerprint mismatch")
    if canonical_sha256(SPEC) != AUTH.get("full_freeze_spec_sha256"):
        stop("terminal_authorization_failure", "full freeze changed after authorization")
    runtime = SPEC["preprocessing_model_fit"]["runtime"]
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if python_version != runtime["python"]:
        stop("terminal_runtime_mismatch", "Python runtime differs from freeze", observed=python_version, expected=runtime["python"])
    if np.__version__ != runtime["numpy"]:
        stop("terminal_runtime_mismatch", "NumPy runtime differs from freeze", observed=np.__version__, expected=runtime["numpy"])
    if sklearn.__version__ != runtime["scikit_learn"]:
        stop("terminal_runtime_mismatch", "scikit-learn runtime differs from freeze", observed=sklearn.__version__, expected=runtime["scikit_learn"])


def reconstruct_response_independent_inputs(metadata: dict):
    files = {str(row.get("key") or ""): row for row in (metadata.get("files") or [])}
    for name, expected_md5, expected_size in (
        SPEC["source_identity"]["deployment_file"],
        SPEC["source_identity"]["eel_metadata_file"],
        SPEC["source_identity"]["response_file"],
    ):
        if name not in files:
            stop("terminal_pre_response_source_identity_failure", "frozen Zenodo file missing", file_name=name)
        row = files[name]
        checksum = str(row.get("checksum") or "")
        observed_md5 = checksum.split(":", 1)[-1] if checksum else ""
        if observed_md5 != expected_md5 or int(row.get("size") or 0) != int(expected_size):
            stop("terminal_pre_response_source_identity_failure", "frozen Zenodo file identity changed", file_name=name)

    def content_url(name: str) -> str:
        links = files[name].get("links") or {}
        value = str(links.get("content") or links.get("self") or "")
        if not value:
            stop("terminal_pre_response_source_identity_failure", "Zenodo content URL missing", file_name=name)
        return value

    deployment_name, deployment_md5, _ = SPEC["source_identity"]["deployment_file"]
    eel_name, eel_md5, _ = SPEC["source_identity"]["eel_metadata_file"]
    deployment_bytes = bounded_file(content_url(deployment_name), 2_000_000, deployment_md5, "deployment")
    eel_bytes = bounded_file(content_url(eel_name), 1_000_000, eel_md5, "eel_metadata")
    deploy_rows = parse_csv_bytes(deployment_bytes, SOURCE["deployment_semantics"]["expected_physical_header"], "deployment")
    eel_rows = parse_csv_bytes(eel_bytes, SOURCE["eel_metadata_semantics"]["expected_physical_header"], "eel_metadata")

    study_rows = []
    for row in deploy_rows:
        project = str(row["acoustic_project_code"]).strip()
        station = str(row["station_name"]).strip()
        pieces = station.split(maxsplit=1)
        prefix = int(pieces[0]) if pieces and pieces[0].isdigit() else None
        if project == "AZO" and prefix is not None and 148 <= prefix <= 157 and station == f"{prefix} FLO CRUZ":
            study_rows.append({**row, "station_name": station})
    stations = sorted({row["station_name"] for row in study_rows}, key=lambda value: int(value.split()[0]))
    if stations != [f"{value} FLO CRUZ" for value in range(148, 158)]:
        stop("terminal_pre_response_registry_failure", "study receiver registry changed", stations=stations)

    coords_by_station: dict[str, list[tuple[float, float]]] = defaultdict(list)
    intervals_by_station: dict[str, list[tuple[datetime, datetime | None]]] = defaultdict(list)
    try:
        for row in study_rows:
            station = row["station_name"]
            lat = float(row["deploy_latitude"])
            lon = float(row["deploy_longitude"])
            if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("invalid coordinate")
            coords_by_station[station].append((lat, lon))
            start = parse_dt(row["deploy_date_time"])
            end = parse_optional_dt(row["recover_date_time"])
            if end is not None and end < start:
                raise ValueError("recovery precedes deployment")
            intervals_by_station[station].append((start, end))
    except Exception as exc:
        stop("terminal_pre_response_source_schema_failure", "deployment parse failed", error=repr(exc))
    station_coords = {
        station: (
            float(np.median([value[0] for value in coords_by_station[station]])),
            float(np.median([value[1] for value in coords_by_station[station]])),
        )
        for station in stations
    }
    registry_payload = [
        {"station": station, "lat": station_coords[station][0], "lon": station_coords[station][1]}
        for station in stations
    ]
    registry_fingerprint = hashlib.sha256(
        json.dumps(registry_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if registry_fingerprint != STAGE1["registry"]["station_registry_fingerprint"]:
        stop("terminal_pre_response_registry_failure", "station registry fingerprint changed", observed=registry_fingerprint)

    raw_tags = []
    normalization_from, normalization_to = SPEC["response_semantics"]["tag_prefix_normalization"]
    try:
        for row in eel_rows:
            if str(row["animal_project_code"]).strip() != SPEC["response_semantics"]["target_animal_project_code"]:
                raise ValueError("eel metadata animal_project_code mismatch")
            if str(row["scientific_name"]).strip() != SPEC["response_semantics"]["target_scientific_name"]:
                raise ValueError("eel metadata scientific_name mismatch")
            tag = str(row["acoustic_tag_id"]).strip().replace(normalization_from, normalization_to)
            raw_tags.append(
                {
                    "tag": tag,
                    "release_dt": parse_dt(row["release_date_time"]),
                    "release_coord": (float(row["release_latitude"]), float(row["release_longitude"])),
                }
            )
    except Exception as exc:
        stop("terminal_pre_response_source_schema_failure", "eel metadata parse failed", error=repr(exc))
    if len(raw_tags) != 37 or len({row["tag"] for row in raw_tags}) != 37:
        stop("terminal_pre_response_registry_failure", "raw eel tag registry changed", raw_tag_count=len(raw_tags))
    target_tags = [row for row in raw_tags if row["tag"] != SPEC["response_semantics"]["excluded_non_yellow_tag"]]
    if len(target_tags) != 36:
        stop("terminal_pre_response_registry_failure", "yellow tag cohort changed", target_tag_count=len(target_tags))
    release_anchor_by_tag = {}
    release_anchor_distances = {}
    for row in target_tags:
        distances = {station: haversine_km(row["release_coord"], station_coords[station]) for station in stations}
        station = min(stations, key=lambda value: (distances[value], value))
        release_anchor_by_tag[row["tag"]] = station
        release_anchor_distances[row["tag"]] = float(distances[station])
    if sorted(set(release_anchor_by_tag.values()), key=lambda value: int(value.split()[0])) != STAGE1["animal_sources"]["release_anchor_stations"]:
        stop("terminal_pre_response_registry_failure", "release-anchor station set changed")

    latest_release = max(row["release_dt"] for row in target_tags)
    if latest_release.isoformat(sep=" ") != STAGE1["animal_sources"]["latest_yellow_release_datetime"]:
        stop("terminal_pre_response_registry_failure", "latest release time changed")
    first_week = first_monday_strictly_after(latest_release.date())
    study_end = date.fromisoformat(SPEC["temporal_split"]["study_coverage_end"])
    week_dates = []
    cursor = first_week
    while cursor + timedelta(days=6) <= study_end:
        week_dates.append(cursor)
        cursor += timedelta(days=7)
    week_starts = [value.isoformat() for value in week_dates]
    if len(week_starts) != 49 or week_starts[0] != SPEC["temporal_split"]["first_scored_week_start"]:
        stop("terminal_pre_response_availability_failure", "scored week registry changed", week_count=len(week_starts))

    receiver_week_effort = []
    eligible_active_days: dict[tuple[str, str], int] = {}
    for station in stations:
        for week_start_date in week_dates:
            week_end = week_start_date + timedelta(days=6)
            active_dates: set[date] = set()
            for start_dt, end_dt in intervals_by_station[station]:
                start_day = max(start_dt.date(), week_start_date)
                raw_end = study_end if end_dt is None else min(end_dt.date(), study_end)
                end_day = min(raw_end, week_end)
                day = start_day
                while day <= end_day:
                    active_dates.add(day)
                    day += timedelta(days=1)
            active_days = len(active_dates)
            week_text = week_start_date.isoformat()
            eligible = active_days >= 5
            receiver_week_effort.append({"station": station, "week_start": week_text, "active_days": active_days, "eligible": eligible})
            if eligible:
                eligible_active_days[(week_text, station)] = active_days
    availability_payload = sorted(receiver_week_effort, key=lambda row: (row["week_start"], row["station"]))
    availability_fingerprint = hashlib.sha256(
        json.dumps(availability_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if availability_fingerprint != STAGE1["temporal_availability"]["availability_fingerprint"]:
        stop("terminal_pre_response_availability_failure", "receiver-week availability fingerprint changed", observed=availability_fingerprint)
    if len(eligible_active_days) != STAGE1["temporal_availability"]["eligible_receiver_week_count"]:
        stop("terminal_pre_response_availability_failure", "eligible receiver-week count changed")

    response_name, _, _ = SPEC["source_identity"]["response_file"]
    return {
        "files": files,
        "response_url": content_url(response_name),
        "stations": stations,
        "coordinates": station_coords,
        "target_tags": {row["tag"] for row in target_tags},
        "release_anchor_by_tag": release_anchor_by_tag,
        "week_starts": week_starts,
        "eligible_active_days": eligible_active_days,
    }


def stream_response_once(inputs: dict) -> tuple[dict[tuple[str, str], int], dict]:
    labels = {key: 0 for key in inputs["eligible_active_days"]}
    expected_header = list(SPEC["response_identity"]["physical_header"])
    required = tuple(SPEC["response_semantics"]["required_nonmissing_fields_stop_on_missing"])
    excluded_projects = set(SPEC["response_semantics"]["excluded_acoustic_project_codes"])
    excluded_pairs = {tuple(value) for value in SPEC["response_semantics"]["excluded_tag_station_pairs"]}
    target_tags = set(inputs["target_tags"])
    stations = set(inputs["stations"])
    normalization_from, normalization_to = SPEC["response_semantics"]["tag_prefix_normalization"]
    counters = defaultdict(int)
    hasher = hashlib.md5()
    expected_size = int(SPEC["source_identity"]["response_file"][2])
    expected_md5 = str(SPEC["source_identity"]["response_file"][1])

    request = urllib.request.Request(
        inputs["response_url"],
        headers={"User-Agent": "EOG-Azores-eel-once-only/1.0", "Accept-Encoding": "identity"},
    )
    AUDIT["response_payload_requests"] = 1
    try:
        response_cm = urllib.request.urlopen(request, timeout=180)
    except Exception as exc:
        stop("terminal_response_transport_failure", "sole response GET could not start", error=repr(exc))
    with response_cm as response:
        status = int(getattr(response, "status", 200))
        if status != 200:
            stop("terminal_response_transport_failure", "sole response GET did not return HTTP 200", http_status=status)
        for physical_line_index, raw_line in enumerate(response):
            hasher.update(raw_line)
            AUDIT["response_payload_bytes_opened"] += len(raw_line)
            try:
                text = raw_line.decode("utf-8-sig" if physical_line_index == 0 else "utf-8").rstrip("\r\n")
                parsed = list(csv.reader([text]))
            except Exception as exc:
                stop("terminal_response_parser_failure", "physical response row parse failed", physical_line_index=physical_line_index, error=repr(exc))
            if len(parsed) != 1:
                stop("terminal_response_parser_failure", "physical line did not parse as exactly one CSV row", physical_line_index=physical_line_index)
            fields = parsed[0]
            if physical_line_index == 0:
                if fields != expected_header:
                    stop("terminal_response_schema_failure", "full-stream response header differs from frozen header certificate", observed_header=fields)
                continue
            AUDIT["response_rows_opened"] = True
            AUDIT["response_values_opened"] = True
            AUDIT["raw_data_rows_seen"] += 1
            if len(fields) != len(expected_header):
                stop("terminal_response_parser_failure", "data row width differs from frozen physical header", physical_line_index=physical_line_index, observed_width=len(fields))
            row = dict(zip(expected_header, fields, strict=True))
            missing = [field for field in required if not str(row[field]).strip()]
            if missing:
                stop("terminal_response_missing_required", "required field is empty under frozen stop policy", physical_line_index=physical_line_index, missing_fields=missing)
            tag = str(row["acoustic_tag_id"]).strip().replace(normalization_from, normalization_to)
            if tag not in target_tags:
                counters["excluded_non_target_tag"] += 1
                continue
            if str(row["animal_project_code"]).strip() != SPEC["response_semantics"]["target_animal_project_code"]:
                stop("terminal_response_semantic_mismatch", "target tag has unexpected animal_project_code", physical_line_index=physical_line_index)
            if str(row["scientific_name"]).strip() != SPEC["response_semantics"]["target_scientific_name"]:
                stop("terminal_response_semantic_mismatch", "target tag has unexpected scientific_name", physical_line_index=physical_line_index)
            acoustic_project = str(row["acoustic_project_code"]).strip()
            station = str(row["station_name"]).strip()
            if acoustic_project in excluded_projects:
                counters["excluded_public_project_rule"] += 1
                continue
            if (tag, station) in excluded_pairs:
                counters["excluded_public_false_pair_rule"] += 1
                continue
            if station not in stations:
                counters["excluded_outside_study_station"] += 1
                continue
            try:
                timestamp = parse_dt(row["date_time"])
            except Exception as exc:
                stop("terminal_response_datetime_failure", "target study detection datetime failed frozen parser", physical_line_index=physical_line_index, error=repr(exc))
            day = timestamp.date()
            monday = day - timedelta(days=day.weekday())
            key = (monday.isoformat(), station)
            if key not in labels:
                counters["excluded_outside_eligible_receiver_week"] += 1
                continue
            labels[key] = 1
            counters["admissible_detection_rows"] += 1

    observed_size = AUDIT["response_payload_bytes_opened"]
    observed_md5 = hasher.hexdigest()
    if observed_size != expected_size or observed_md5 != expected_md5:
        stop("terminal_response_identity_failure", "sole streamed response bytes do not match frozen identity", observed_size=observed_size, expected_size=expected_size, observed_md5=observed_md5, expected_md5=expected_md5)
    counters["positive_receiver_weeks"] = sum(labels.values())
    counters["negative_receiver_weeks"] = len(labels) - sum(labels.values())
    return labels, {"response_md5": observed_md5, "response_size": observed_size, **dict(counters)}


def main() -> None:
    validate_authorization_and_runtime()
    metadata = bounded_json(f"https://zenodo.org/api/records/{SPEC['source_identity']['dataset_zenodo_record']}")
    inputs = reconstruct_response_independent_inputs(metadata)

    labels, response_audit = stream_response_once(inputs)
    calibration_weeks = inputs["week_starts"][:26]
    heldout_weeks = inputs["week_starts"][26:]
    count_result = exact_count_gate(
        labels,
        calibration_weeks=calibration_weeks,
        heldout_weeks=heldout_weeks,
        primary_outer_units=SPEC["temporal_split"]["primary_outer_units"],
        minima=SPEC["count_gate"],
    )
    if not count_result.passed:
        write_terminal(
            "terminal_exact_count_gate_failed",
            response_audit=response_audit,
            exact_count_gate=asdict(count_result),
            claim_boundary="no paired predictive complementarity fit was authorized after count failure",
        )
        return

    try:
        prepared = build_prepared_rows(
            stations=inputs["stations"],
            week_starts=inputs["week_starts"],
            eligible_active_days=inputs["eligible_active_days"],
            labels=labels,
            coordinates=inputs["coordinates"],
            thresholds=SPEC["world_scale"]["geometry_thresholds_km"],
            release_anchor_by_tag=inputs["release_anchor_by_tag"],
            structural_gate_fingerprint=SPEC["structural_adequacy"]["structural_gate_fingerprint"],
        )
    except AllWorldsEliminated as exc:
        write_terminal(
            "terminal_layer_a_structural_falsification",
            response_audit=response_audit,
            exact_count_gate=asdict(count_result),
            reason=str(exc),
            claim_boundary="exact Layer A falsified the complete frozen six-world universe before predictive fitting",
        )
        return
    except Exception as exc:
        stop("terminal_feature_construction_failure", "frozen feature construction failed after response access; no rescue permitted", error=repr(exc), response_audit=response_audit, exact_count_gate=asdict(count_result))

    declaration = PredictiveComplementarityDeclaration(
        metric_name=SPEC["metrics_decision"]["primary_metric"],
        lower_is_better=SPEC["metrics_decision"]["lower_is_better"],
        expected_outer_unit_count=SPEC["metrics_decision"]["primary_outer_unit_count"],
        favorable_min_augmented_wins=SPEC["metrics_decision"]["favorable_min_augmented_wins"],
        adverse_min_baseline_wins=SPEC["metrics_decision"]["adverse_min_baseline_wins"],
        learner_fit_fingerprint=AUTH["section_fingerprints"]["preprocessing_model_fit"],
        response_endpoint_fingerprint=AUTH["section_fingerprints"]["response_semantics"],
        split_fingerprint=AUTH["section_fingerprints"]["temporal_split"],
        external_feature_fingerprint=canonical_sha256(SPEC["comparators"]["conventional_feature_names"]),
        eog_feature_fingerprint=AUTH["section_fingerprints"]["layer_b_representation"],
    )
    if declaration.fingerprint != AUTH["predictive_complementarity_declaration_fingerprint"]:
        stop("terminal_authorization_failure", "predictive complementarity declaration drifted after authorization")

    try:
        AUDIT["model_fits"] = 2
        paired_result, paired_scores, supplementary = fit_and_score_paired(
            prepared,
            calibration_week_count=26,
            primary_outer_units=SPEC["temporal_split"]["primary_outer_units"],
            hyperparameters=SPEC["preprocessing_model_fit"]["hyperparameters"],
            probability_clip=float(SPEC["metrics_decision"]["probability_clip"]),
            declaration=declaration,
        )
        AUDIT["primary_outer_units_scored"] = len(paired_scores)
    except Exception as exc:
        stop("terminal_model_execution_failure", "frozen paired model execution failed after response access; no rerun or rescue permitted", error=repr(exc), response_audit=response_audit, exact_count_gate=asdict(count_result))

    write_terminal(
        paired_result.status,
        response_audit=response_audit,
        exact_count_gate=asdict(count_result),
        prepared_receiver_week_rows=len(prepared),
        paired_result=asdict(paired_result),
        paired_outer_scores=[asdict(score) for score in paired_scores],
        supplementary=supplementary,
        claim_boundary=(
            "favorable supports non-redundant predictive complementarity only; adverse/no-confirmed narrow Layer B without changing exact Layer A scientific update/falsification value"
        ),
    )


if __name__ == "__main__":
    main()
