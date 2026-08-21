#!/usr/bin/env python3
"""Frozen paired-complementarity runner for the southern California giant-kelp candidate.

Smoke mode uses the real, checksum-frozen geometry and spore-dispersal process objects
but a deterministic synthetic biomass/fecundity history. It never opens the frozen
biomass/fecundity response object. Outcome mode exists for the eventual once-only runner
and must not be invoked until runtime identity and the generic outcome-access gate are
frozen and authorized.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
import tempfile
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.predictive_complementarity import (
    PairedOuterUnitScore,
    PredictiveComplementarityDeclaration,
    evaluate_predictive_complementarity,
)
from eog.v2.world_forecast import ForecastGateDeclaration
from eog.v2.world_predictive_summary import summarize_worldset_for_prediction

ROOT = Path("validation/giant_kelp_complementarity")
CONTRACT_PATH = ROOT / "gate2_prediction_contract.json"
GEOMETRY_CONTRACT_PATH = ROOT / "southern_geometry_object_contract.json"
PROCESS_CONTRACT_PATH = ROOT / "process_object_contract.json"
RESPONSE_CONTRACT_PATH = ROOT / "response_object_contract.json"
PATCH_IDENTITY_PATH = ROOT / "patch_identity_contract.json"

N = 469
PERIODS = tuple(
    [
        "1996-H1", "1996-H2", "1997-H1", "1997-H2", "1998-H1", "1998-H2",
        "1999-H1", "1999-H2", "2000-H1", "2000-H2", "2001-H1", "2001-H2",
        "2002-H1", "2002-H2", "2003-H1", "2003-H2", "2004-H1", "2004-H2",
        "2005-H1", "2005-H2", "2006-H1", "2006-H2",
    ]
)
PERIOD_INDEX = {period: index for index, period in enumerate(PERIODS)}
CALIBRATION_TRANSITION_INDICES = tuple(range(16))
HELDOUT_TRANSITION_INDICES = tuple(range(16, 21))
THRESHOLDS_KM = np.asarray(
    [8.784880554989936, 30.599950974020906, 33.76116917197375, 40.81254045279048],
    dtype=float,
)
LOCAL_SCALE_KM = 30.599950974020906
WORLD_IDS = (
    "geo_lcc250",
    "geo_lcc500",
    "geo_lcc750",
    "geo_lcc900",
    "geo_exponential_full",
)
SUPPORT_TOLERANCE = 1e-15
LOSS_SUPPORT = 1.0
SEED = 20260821
EPS = 1e-9

MIN_CAL_EVENTS = 10
MIN_CAL_NON_EVENTS = 40
MIN_HELD_EVENTS = 10
MIN_HELD_NON_EVENTS = 40
MIN_HELD_BOTH = 4

EXPECTED_FINGERPRINTS = {
    "split": "59d90ed93c929c578a3dcade17776af67f5b02ad993a00cfdf30f34c64869d59",
    "endpoint": "d30353f3942fbba443ecce682b11666e13c91e3edf6da8951a2a68f1e82009a1",
    "external_features": "2ff695069ce10e1154bed824b778100e8ed17f130dd20257a8f6c20ef900fd35",
    "learner": "d05b57faf4c6a1f9a3d71b666a78a8af958fd072269f86b310d40549780632d1",
    "layer_b": "8e68cf9dea4f4d76280786e22bc46fc2fd07211d4711e2c9af49775e7efcadef",
    "count_gate": "d94e407e260b3b686ad0922708bf6f2ea04d1c4ce71686c08963ecb7af37029d",
    "metric": "88a38feffb2932d83279957544ea557fe046e470d25ba034ca6fc96a60990e6c",
}

RF_ARGS = dict(
    n_estimators=500,
    max_features="sqrt",
    min_samples_leaf=5,
    class_weight=None,
    random_state=SEED,
    n_jobs=1,
)


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_prediction_contract() -> dict:
    contract = read_json(CONTRACT_PATH)
    if tuple(contract["periods"]) != PERIODS:
        raise ValueError("prediction contract period order drift")
    if contract["split"]["fingerprint"] != EXPECTED_FINGERPRINTS["split"]:
        raise ValueError("split fingerprint drift")
    if contract["response_endpoint"]["fingerprint"] != EXPECTED_FINGERPRINTS["endpoint"]:
        raise ValueError("endpoint fingerprint drift")
    if (
        contract["shared_external_features"]["feature_fingerprint"]
        != EXPECTED_FINGERPRINTS["external_features"]
    ):
        raise ValueError("external feature fingerprint drift")
    if contract["learner"]["fingerprint"] != EXPECTED_FINGERPRINTS["learner"]:
        raise ValueError("learner fingerprint drift")
    if contract["layer_b"]["fingerprint"] != EXPECTED_FINGERPRINTS["layer_b"]:
        raise ValueError("Layer-B fingerprint drift")
    if contract["count_gate"]["fingerprint"] != EXPECTED_FINGERPRINTS["count_gate"]:
        raise ValueError("count-gate fingerprint drift")
    if contract["metric_decision"]["fingerprint"] != EXPECTED_FINGERPRINTS["metric"]:
        raise ValueError("metric fingerprint drift")
    if tuple(contract["layer_a"]["world_ids"]) != WORLD_IDS:
        raise ValueError("Layer-A world IDs drift")
    if not np.allclose(
        np.asarray(contract["layer_a"]["thresholds_km"], dtype=float),
        THRESHOLDS_KM,
        rtol=0.0,
        atol=1e-12,
    ):
        raise ValueError("Layer-A thresholds drift")
    return contract


def compile_one_group(pattern_text: str) -> re.Pattern[str]:
    pattern = re.compile(pattern_text)
    if pattern.groups != 1:
        raise ValueError(f"patch identity regex must have exactly one capture group: {pattern_text!r}")
    return pattern


def canonical_patch_id(raw: object, patterns: tuple[re.Pattern[str], ...], label: str) -> str:
    token = str(raw).strip()
    matches = [pattern.fullmatch(token) for pattern in patterns]
    matches = [match for match in matches if match is not None]
    if len(matches) != 1:
        raise ValueError(f"{label} must match exactly one frozen patch-ID representation: {token!r}")
    digits = matches[0].group(1)
    if not re.fullmatch(r"[1-9][0-9]*", digits):
        raise ValueError(f"{label} capture is not a positive canonical integer: {digits!r}")
    canonical = str(int(digits))
    if canonical != digits:
        raise ValueError(f"{label} uses non-canonical integer digits: {digits!r}")
    return canonical


def resolve_object_url(pid: str, transport: list[dict[str, object]]) -> str:
    encoded = urllib.parse.quote(pid, safe="")
    resolve_url = f"https://cn.dataone.org/cn/v2/resolve/{encoded}"

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(
        resolve_url,
        headers={"User-Agent": "eog-giant-kelp-complementarity/1.0", "Accept": "*/*"},
    )
    try:
        with opener.open(request, timeout=60) as response:
            status = getattr(response, "status", None) or response.getcode()
            location = response.headers.get("Location")
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise
        status = exc.code
        location = exc.headers.get("Location")
    transport.append(
        {
            "pid": pid,
            "resolve_url": resolve_url,
            "resolve_status": status,
            "location": location,
        }
    )
    if not location:
        raise ValueError(f"DataONE resolve returned no object location for {pid!r}")
    object_url = urllib.parse.urljoin(resolve_url, location)
    parsed = urllib.parse.urlparse(object_url)
    if parsed.scheme != "https" or "/object/" not in parsed.path:
        raise ValueError(f"unsafe DataONE object location: {object_url!r}")
    return object_url


def download_object(
    pid: str,
    *,
    expected_size: int,
    expected_sha1: str,
    stem: str,
    transport: list[dict[str, object]],
) -> Path:
    url = resolve_object_url(pid, transport)
    path = Path(tempfile.gettempdir()) / f"{stem}.csv"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "eog-giant-kelp-complementarity/1.0", "Accept": "text/csv,*/*"},
    )
    digest = hashlib.sha1()
    size = 0
    with urllib.request.urlopen(request, timeout=240) as response, path.open("wb") as handle:
        status = getattr(response, "status", None) or response.getcode()
        final = str(response.geturl())
        content_type = str(response.headers.get("Content-Type", ""))
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            handle.write(chunk)
    transport.append(
        {
            "pid": pid,
            "object_url": url,
            "final": final,
            "status": status,
            "content_type": content_type,
            "bytes": size,
            "sha1": digest.hexdigest(),
        }
    )
    if status != 200:
        raise ValueError(f"DataONE object status {status} for {pid}")
    if size != expected_size:
        raise ValueError(f"object size drift for {stem}: {size} != {expected_size}")
    if digest.hexdigest().casefold() != expected_sha1.casefold():
        raise ValueError(
            f"object checksum drift for {stem}: {digest.hexdigest()} != {expected_sha1}"
        )
    return path


@dataclass(frozen=True)
class NonResponseInputs:
    node_ids: tuple[str, ...]
    centroids: np.ndarray
    pixel_counts: np.ndarray
    distance_km: np.ndarray
    process_time: np.ndarray
    provenance: dict[str, object]


def load_nonresponse_inputs() -> NonResponseInputs:
    geometry_contract = read_json(GEOMETRY_CONTRACT_PATH)
    process_contract = read_json(PROCESS_CONTRACT_PATH)
    identity_contract = read_json(PATCH_IDENTITY_PATH)
    geometry = geometry_contract["southern_geometry_entity"]
    process = process_contract["process_entity"]
    geometry_pattern = compile_one_group(identity_contract["geometry_raw_pattern"])
    process_pattern = compile_one_group(identity_contract["process_raw_pattern"])
    transport: list[dict[str, object]] = []

    geometry_path = download_object(
        geometry["data_pid"],
        expected_size=int(geometry["size_bytes"]),
        expected_sha1=geometry["checksum"],
        stem="giant_kelp_geometry_runner",
        transport=transport,
    )
    grouped: dict[str, list[tuple[float, float]]] = {}
    with geometry_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = ("patch_number", "pixel_latitude", "pixel_longitude")
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ValueError(f"geometry schema drift: {reader.fieldnames!r}")
        for row_no, row in enumerate(reader, 2):
            node = canonical_patch_id(
                row["patch_number"], (geometry_pattern,), f"geometry row {row_no} patch"
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
    if len(grouped) != N:
        raise ValueError(f"expected {N} geometry patches, found {len(grouped)}")
    node_ids = tuple(sorted(grouped, key=int))
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
    centroid_fingerprint = canonical_sha256(centroid_payload)
    if centroid_fingerprint != "358d66cdf1b039207e22ae575a23900c4405a7c9c556871e4a60c91e0a19128c":
        raise ValueError("frozen geometry centroid fingerprint drift")

    lat = np.radians(centroids[:, 0])
    lon = np.radians(centroids[:, 1])
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    hav = np.sin(dlat / 2.0) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2
    hav = np.clip(hav, 0.0, 1.0)
    distance_km = 2.0 * 6371.0088 * np.arcsin(np.sqrt(hav))
    np.fill_diagonal(distance_km, 0.0)

    process_path = download_object(
        process["data_pid"],
        expected_size=int(process["size_bytes"]),
        expected_sha1=process["checksum"],
        stem="giant_kelp_process_runner",
        transport=transport,
    )
    node_index = {node: index for index, node in enumerate(node_ids)}
    process_time = np.full((len(PERIODS), N, N), np.nan, dtype=np.float32)
    seen = np.zeros((len(PERIODS), N, N), dtype=bool)
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
            src = canonical_patch_id(
                row["source_patch"], (process_pattern,), f"process row {row_no} source"
            )
            dst = canonical_patch_id(
                row["destination_patch"], (process_pattern,), f"process row {row_no} destination"
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
            i = PERIOD_INDEX[period]
            j = node_index[src]
            k = node_index[dst]
            if seen[i, j, k]:
                raise ValueError(f"duplicate process source-destination-period at row {row_no}")
            seen[i, j, k] = True
            process_time[i, j, k] = dispersal_time
    if row_count != 22 * N * N:
        raise ValueError(f"expected {22 * N * N} process rows, found {row_count}")
    if not bool(np.all(seen)) or not np.isfinite(process_time).all():
        raise ValueError("process matrix is not complete and finite")

    return NonResponseInputs(
        node_ids=node_ids,
        centroids=centroids,
        pixel_counts=pixel_counts,
        distance_km=distance_km,
        process_time=process_time,
        provenance={
            "geometry_pid": geometry["data_pid"],
            "geometry_sha1": geometry["checksum"],
            "process_pid": process["data_pid"],
            "process_sha1": process["checksum"],
            "centroid_fingerprint": centroid_fingerprint,
            "process_mapping_fingerprint": "5f117614fdc6367e03bb6a8439320d567473fe8f7b2c831192575e2a1d1fa4c6",
            "process_row_count": row_count,
            "transport": transport,
        },
    )


@dataclass(frozen=True)
class ResponseState:
    biomass: np.ndarray
    fecundity: np.ndarray
    provenance: dict[str, object]


def synthetic_response(inputs: NonResponseInputs) -> ResponseState:
    rng = np.random.default_rng(SEED)
    biomass = np.zeros((N, len(PERIODS)), dtype=float)
    fecundity = np.zeros((N, len(PERIODS)), dtype=float)
    initial_probability = np.clip(
        0.28 + 0.10 * (inputs.pixel_counts / max(float(np.max(inputs.pixel_counts)), 1.0)),
        0.20,
        0.45,
    )
    positive = rng.random(N) < initial_probability
    if int(np.sum(positive)) < 40:
        positive[:40] = True
    biomass[positive, 0] = rng.lognormal(mean=0.0, sigma=0.55, size=int(np.sum(positive)))
    fecundity[positive, 0] = biomass[positive, 0] * rng.uniform(0.25, 1.0, size=int(np.sum(positive)))

    for t in range(len(PERIODS) - 1):
        current_positive = biomass[:, t] > 0
        source_indices = np.flatnonzero(current_positive)
        if source_indices.size == 0:
            biomass[0, t] = 1.0
            fecundity[0, t] = 0.5
            current_positive[0] = True
            source_indices = np.asarray([0], dtype=int)
        source_times = inputs.process_time[t, source_indices, :]
        min_time = np.min(source_times, axis=0)
        process_exposure = np.exp(-min_time / 18.0)
        colonization_probability = np.clip(0.08 + 0.30 * process_exposure, 0.05, 0.45)
        persistence_probability = np.clip(0.70 + 0.10 * process_exposure, 0.60, 0.90)
        draws = rng.random(N)
        next_positive = np.where(
            current_positive,
            draws < persistence_probability,
            draws < colonization_probability,
        )
        values = rng.lognormal(mean=0.0, sigma=0.6, size=int(np.sum(next_positive)))
        biomass[next_positive, t + 1] = values
        fecundity[next_positive, t + 1] = values * rng.uniform(
            0.20, 1.10, size=int(np.sum(next_positive))
        )

    return ResponseState(
        biomass=biomass,
        fecundity=fecundity,
        provenance={
            "mode": "synthetic",
            "seed": SEED,
            "response_object_bytes_opened": False,
            "response_rows_opened": False,
        },
    )


def read_released_response(inputs: NonResponseInputs) -> ResponseState:
    response_contract = read_json(RESPONSE_CONTRACT_PATH)
    identity_contract = read_json(PATCH_IDENTITY_PATH)
    response = response_contract["response_entity"]
    patterns = tuple(
        compile_one_group(pattern_text)
        for pattern_text in identity_contract["future_response_allowed_patterns"]
    )
    transport: list[dict[str, object]] = []
    response_path = download_object(
        response["data_pid"],
        expected_size=int(response["size_bytes"]),
        expected_sha1=response["checksum"],
        stem="giant_kelp_response_outcome",
        transport=transport,
    )
    node_index = {node: index for index, node in enumerate(inputs.node_ids)}
    biomass = np.full((N, len(PERIODS)), np.nan, dtype=float)
    fecundity = np.full((N, len(PERIODS)), np.nan, dtype=float)
    expected_fields = tuple(response["required_columns"])
    int_re = re.compile(r"^[0-9]+$")
    row_count = 0
    observed_nodes: set[str] = set()
    observed_periods: set[str] = set()
    with response_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ValueError(
                f"response schema drift: {reader.fieldnames!r} != {expected_fields!r}"
            )
        for row_no, row in enumerate(reader, 2):
            row_count += 1
            node = canonical_patch_id(
                row["patch_number"], patterns, f"response row {row_no} patch"
            )
            if node not in node_index:
                raise ValueError(f"response row {row_no} uses unknown canonical patch {node!r}")
            year_token = str(row["year"]).strip()
            semester_token = str(row["semester"]).strip()
            if not int_re.fullmatch(year_token) or not int_re.fullmatch(semester_token):
                raise ValueError(f"non-strict response period token at row {row_no}")
            year = int(year_token)
            semester = int(semester_token)
            if not 1996 <= year <= 2006 or semester not in (1, 2):
                raise ValueError(f"out-of-contract response period at row {row_no}")
            period = f"{year}-H{semester}"
            values: dict[str, float] = {}
            for field in (
                "pixel_latitude",
                "pixel_longitude",
                "patch_area",
                "patch_biomass",
                "patch_fecundity",
            ):
                token = str(row[field]).strip()
                if not token:
                    raise ValueError(f"blank required response token {field!r} at row {row_no}")
                try:
                    number = float(token)
                except Exception as exc:
                    raise ValueError(f"invalid response number {field!r} at row {row_no}") from exc
                if not math.isfinite(number):
                    raise ValueError(f"nonfinite response number {field!r} at row {row_no}")
                values[field] = number
            if not -90 <= values["pixel_latitude"] <= 90:
                raise ValueError(f"response latitude out of range at row {row_no}")
            if not -180 <= values["pixel_longitude"] <= 180:
                raise ValueError(f"response longitude out of range at row {row_no}")
            if any(
                values[field] < 0
                for field in ("patch_area", "patch_biomass", "patch_fecundity")
            ):
                raise ValueError(f"negative response quantity at row {row_no}")
            i = node_index[node]
            t = PERIOD_INDEX[period]
            if np.isfinite(biomass[i, t]) or np.isfinite(fecundity[i, t]):
                raise ValueError(f"duplicate response patch-period at row {row_no}: {node}/{period}")
            biomass[i, t] = values["patch_biomass"]
            fecundity[i, t] = values["patch_fecundity"]
            observed_nodes.add(node)
            observed_periods.add(period)

    return ResponseState(
        biomass=biomass,
        fecundity=fecundity,
        provenance={
            "mode": "outcome",
            "response_pid": response["data_pid"],
            "response_sha1": response["checksum"],
            "response_row_count": row_count,
            "observed_node_count": len(observed_nodes),
            "observed_period_count": len(observed_periods),
            "response_object_bytes_opened": True,
            "response_rows_opened": True,
            "transport": transport,
        },
    )


def transition_counts(state: ResponseState, transition_index: int) -> tuple[int, int, int]:
    source = state.biomass[:, transition_index]
    target = state.biomass[:, transition_index + 1]
    sources = int(np.sum(np.isfinite(source) & (source > 0)))
    risk = np.isfinite(source) & (source == 0) & np.isfinite(target)
    y = target[risk] > 0
    events = int(np.sum(y))
    non_events = int(np.sum(~y))
    return sources, events, non_events


def exact_count_gate(state: ResponseState) -> dict[str, object]:
    calibration = [transition_counts(state, index) for index in CALIBRATION_TRANSITION_INDICES]
    heldout = [transition_counts(state, index) for index in HELDOUT_TRANSITION_INDICES]
    cal_events = sum(row[1] for row in calibration)
    cal_non_events = sum(row[2] for row in calibration)
    held_events = sum(row[1] for row in heldout)
    held_non_events = sum(row[2] for row in heldout)
    held_both = sum(row[1] > 0 and row[2] > 0 for row in heldout)
    all_sources = all(row[0] > 0 for row in calibration + heldout)
    passed = bool(
        all_sources
        and cal_events >= MIN_CAL_EVENTS
        and cal_non_events >= MIN_CAL_NON_EVENTS
        and held_events >= MIN_HELD_EVENTS
        and held_non_events >= MIN_HELD_NON_EVENTS
        and held_both >= MIN_HELD_BOTH
    )
    return {
        "passed": passed,
        "all_transition_source_sets_nonempty": all_sources,
        "calibration_events": cal_events,
        "calibration_non_events": cal_non_events,
        "heldout_events": held_events,
        "heldout_non_events": held_non_events,
        "heldout_outer_units_with_both_classes": held_both,
        "calibration_transition_counts": [list(row) for row in calibration],
        "heldout_transition_counts": [list(row) for row in heldout],
        "frozen_minima": {
            "calibration_events": MIN_CAL_EVENTS,
            "calibration_non_events": MIN_CAL_NON_EVENTS,
            "heldout_events": MIN_HELD_EVENTS,
            "heldout_non_events": MIN_HELD_NON_EVENTS,
            "heldout_outer_units_with_both_classes": MIN_HELD_BOTH,
        },
    }


def compute_world_supports(distance_km: np.ndarray, source_indices: np.ndarray) -> np.ndarray:
    if source_indices.size == 0:
        raise ValueError("current source set must not be empty")
    source_distance = distance_km[source_indices, :]
    source_weight = 1.0 / float(source_indices.size)
    exponential = np.exp(-source_distance / LOCAL_SCALE_KM)
    supports = np.zeros((len(WORLD_IDS), N), dtype=float)
    for world_index, threshold in enumerate(THRESHOLDS_KM):
        raw = exponential * (source_distance <= threshold + 1e-12)
        raw[np.arange(source_indices.size), source_indices] = 0.0
        denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
        supports[world_index, :] = (source_weight / denominator) @ raw
    raw = exponential.copy()
    raw[np.arange(source_indices.size), source_indices] = 0.0
    denominator = LOSS_SUPPORT + np.sum(raw, axis=1)
    supports[-1, :] = (source_weight / denominator) @ raw
    return supports


def make_layer_b_summary(
    node_ids: tuple[str, ...],
    supports: np.ndarray,
    surviving: np.ndarray,
    transition_id: str,
):
    members = []
    for index, world_id in enumerate(WORLD_IDS):
        if not bool(surviving[index]):
            continue
        cumulative = np.vstack((np.zeros(N, dtype=float), supports[index]))
        supported = np.vstack(
            (np.zeros(N, dtype=bool), supports[index] > SUPPORT_TOLERANCE)
        )
        members.append(
            SimpleNamespace(
                cumulative_reachability=cumulative,
                supported_state=supported,
            )
        )
    if not members:
        raise ValueError("no surviving worlds remain")
    forecast = SimpleNamespace(
        node_ids=node_ids,
        members=tuple(members),
        max_steps=1,
        gate_declaration=ForecastGateDeclaration(
            reachability_threshold=SUPPORT_TOLERANCE
        ),
        world_fingerprints=tuple(
            (world_id, f"frozen::{world_id}") for world_id in WORLD_IDS
        ),
        fingerprint=canonical_sha256(
            {
                "transition_id": transition_id,
                "surviving_world_ids": [
                    world_id
                    for world_id, flag in zip(WORLD_IDS, surviving, strict=True)
                    if flag
                ],
            }
        ),
    )
    return summarize_worldset_for_prediction(forecast, step=1)


def update_rules(
    supports: np.ndarray,
    surviving: np.ndarray,
    positive_indices: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    after = surviving.copy()
    eliminated: list[str] = []
    if positive_indices.size == 0:
        return after, ()
    for index, world_id in enumerate(WORLD_IDS):
        if after[index] and np.any(
            supports[index, positive_indices] <= SUPPORT_TOLERANCE
        ):
            after[index] = False
            eliminated.append(world_id)
    return after, tuple(eliminated)


def period_year_semester(period: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]{4})-H([12])", period)
    if match is None:
        raise ValueError(f"unexpected frozen period label: {period!r}")
    return int(match.group(1)), int(match.group(2))


def shared_external_features(
    inputs: NonResponseInputs,
    state: ResponseState,
    source_indices: np.ndarray,
    transition_index: int,
) -> np.ndarray:
    source_period = PERIODS[transition_index]
    year, semester = period_year_semester(source_period)
    source_biomass = state.biomass[source_indices, transition_index]
    source_fecundity = state.fecundity[source_indices, transition_index]
    if not np.isfinite(source_biomass).all() or not np.isfinite(source_fecundity).all():
        raise ValueError("current positive-source biomass/fecundity must be finite")
    source_distance = inputs.distance_km[source_indices, :]
    process = inputs.process_time[transition_index, source_indices, :].astype(float)
    if not np.isfinite(process).all():
        raise ValueError("current process matrix contains non-finite values")

    nearest_geometry = np.min(source_distance, axis=0)
    mean_geometry = np.mean(source_distance, axis=0)
    threshold_counts = [
        np.sum(source_distance <= threshold + 1e-12, axis=0)
        for threshold in THRESHOLDS_KM
    ]
    min_process = np.min(process, axis=0)
    mean_process = np.mean(process, axis=0)
    fecundity_exposure = np.sum(
        source_fecundity[:, None] / (1.0 + process), axis=0
    )
    biomass_exposure = np.sum(source_biomass[:, None] / (1.0 + process), axis=0)

    source_count = float(source_indices.size)
    source_total_biomass = float(np.sum(source_biomass))
    source_total_fecundity = float(np.sum(source_fecundity))
    features = np.column_stack(
        [
            inputs.pixel_counts,
            inputs.centroids[:, 0],
            inputs.centroids[:, 1],
            np.full(N, float(year - 2001)),
            np.full(N, float(semester == 2)),
            np.full(N, source_count),
            np.full(N, source_total_biomass),
            np.full(N, source_total_fecundity),
            np.ones(N, dtype=float),
            nearest_geometry,
            mean_geometry,
            threshold_counts[0],
            threshold_counts[1],
            threshold_counts[2],
            threshold_counts[3],
            min_process,
            mean_process,
            fecundity_exposure,
            biomass_exposure,
        ]
    ).astype(float)
    if features.shape != (N, 19) or not np.isfinite(features).all():
        raise ValueError(f"shared feature matrix invalid: shape={features.shape}")
    return features


@dataclass(frozen=True)
class TransitionDesign:
    transition_index: int
    transition_id: str
    risk_indices: np.ndarray
    y: np.ndarray
    baseline: np.ndarray
    layer_b: np.ndarray
    supports: np.ndarray
    source_count: int
    positive_count: int
    negative_count: int
    surviving_before: tuple[str, ...]
    layer_b_feature_fingerprint: str


def build_transition(
    inputs: NonResponseInputs,
    state: ResponseState,
    surviving: np.ndarray,
    transition_index: int,
) -> TransitionDesign:
    source = state.biomass[:, transition_index]
    target = state.biomass[:, transition_index + 1]
    source_indices = np.flatnonzero(np.isfinite(source) & (source > 0))
    if source_indices.size == 0:
        raise ValueError(f"no current sources for {PERIODS[transition_index]}")
    risk_indices = np.flatnonzero(
        np.isfinite(source) & (source == 0) & np.isfinite(target)
    )
    y = (target[risk_indices] > 0).astype(int)
    supports = compute_world_supports(inputs.distance_km, source_indices)
    transition_id = f"{PERIODS[transition_index]}->{PERIODS[transition_index + 1]}"
    summary = make_layer_b_summary(
        inputs.node_ids, supports, surviving, transition_id
    )
    baseline_all = shared_external_features(
        inputs, state, source_indices, transition_index
    )
    return TransitionDesign(
        transition_index=transition_index,
        transition_id=transition_id,
        risk_indices=risk_indices,
        y=y,
        baseline=baseline_all[risk_indices],
        layer_b=summary.feature_matrix[risk_indices],
        supports=supports,
        source_count=int(source_indices.size),
        positive_count=int(np.sum(y == 1)),
        negative_count=int(np.sum(y == 0)),
        surviving_before=tuple(
            world_id
            for world_id, flag in zip(WORLD_IDS, surviving, strict=True)
            if flag
        ),
        layer_b_feature_fingerprint=summary.feature_fingerprint,
    )


def write_result(path: Path, payload: dict[str, object]) -> None:
    payload = dict(payload)
    payload["result_fingerprint"] = canonical_sha256(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_analysis(mode: str, output: Path) -> dict[str, object]:
    contract = verify_prediction_contract()
    inputs = load_nonresponse_inputs()
    if mode == "smoke":
        state = synthetic_response(inputs)
    elif mode == "outcome":
        state = read_released_response(inputs)
    else:
        raise ValueError(f"unsupported mode: {mode!r}")

    count_gate = exact_count_gate(state)
    base: dict[str, object] = {
        "candidate": contract["candidate"],
        "mode": mode,
        "prediction_contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "prediction_contract_id": contract["contract_id"],
        "nonresponse_provenance": inputs.provenance,
        "response_provenance": state.provenance,
        "response_object_bytes_opened": bool(state.provenance["response_object_bytes_opened"]),
        "response_rows_opened": bool(state.provenance["response_rows_opened"]),
        "count_gate": count_gate,
        "models_fit": 0,
        "heldout_scores": 0,
    }
    if not count_gate["passed"]:
        base.update(
            {
                "status": "non_estimable_response_balance",
                "complementarity_status": "non_estimable",
                "rule_history": [],
            }
        )
        write_result(output, base)
        return base

    surviving = np.ones(len(WORLD_IDS), dtype=bool)
    calibration: list[TransitionDesign] = []
    history: list[dict[str, object]] = []
    for transition_index in CALIBRATION_TRANSITION_INDICES:
        design = build_transition(inputs, state, surviving, transition_index)
        calibration.append(design)
        after, eliminated = update_rules(
            design.supports,
            surviving,
            design.risk_indices[design.y == 1],
        )
        history.append(
            {
                "transition": design.transition_id,
                "phase": "calibration",
                "source_count": design.source_count,
                "events": design.positive_count,
                "non_events": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": [
                    world_id
                    for world_id, flag in zip(WORLD_IDS, after, strict=True)
                    if flag
                ],
                "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving):
            base.update(
                {
                    "status": "universe_falsified_during_calibration",
                    "complementarity_status": "non_estimable",
                    "rule_history": history,
                    "final_surviving_world_ids": [],
                }
            )
            write_result(output, base)
            return base

    x_baseline = np.vstack([design.baseline for design in calibration])
    x_augmented = np.vstack(
        [np.column_stack([design.baseline, design.layer_b]) for design in calibration]
    )
    y_calibration = np.concatenate([design.y for design in calibration])
    if set(np.unique(y_calibration).tolist()) != {0, 1}:
        raise ValueError("count gate passed but calibration pooled target lacks both classes")

    baseline_rf = RandomForestClassifier(**RF_ARGS)
    augmented_rf = RandomForestClassifier(**RF_ARGS)
    baseline_rf.fit(x_baseline, y_calibration)
    augmented_rf.fit(x_augmented, y_calibration)
    base["models_fit"] = 2

    paired_scores: list[PairedOuterUnitScore] = []
    heldout_rows: list[dict[str, object]] = []
    for transition_index in HELDOUT_TRANSITION_INDICES:
        design = build_transition(inputs, state, surviving, transition_index)
        baseline_probability = baseline_rf.predict_proba(design.baseline)[:, 1]
        augmented_probability = augmented_rf.predict_proba(
            np.column_stack([design.baseline, design.layer_b])
        )[:, 1]
        baseline_loss = float(
            log_loss(design.y, baseline_probability, labels=[0, 1])
        )
        augmented_loss = float(
            log_loss(design.y, augmented_probability, labels=[0, 1])
        )
        paired_scores.append(
            PairedOuterUnitScore(
                outer_unit_id=design.transition_id,
                baseline_score=baseline_loss,
                augmented_score=augmented_loss,
            )
        )
        after, eliminated = update_rules(
            design.supports,
            surviving,
            design.risk_indices[design.y == 1],
        )
        heldout_rows.append(
            {
                "transition": design.transition_id,
                "source_count": design.source_count,
                "events": design.positive_count,
                "non_events": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "baseline_log_loss": baseline_loss,
                "augmented_log_loss": augmented_loss,
                "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
                "eliminated_after_observation": list(eliminated),
                "surviving_after": [
                    world_id
                    for world_id, flag in zip(WORLD_IDS, after, strict=True)
                    if flag
                ],
            }
        )
        history.append(
            {
                "transition": design.transition_id,
                "phase": "heldout",
                "source_count": design.source_count,
                "events": design.positive_count,
                "non_events": design.negative_count,
                "surviving_before": list(design.surviving_before),
                "eliminated_after_observation": list(eliminated),
                "surviving_after": heldout_rows[-1]["surviving_after"],
                "layer_b_feature_fingerprint": design.layer_b_feature_fingerprint,
            }
        )
        surviving = after
        if not np.any(surviving) and transition_index != HELDOUT_TRANSITION_INDICES[-1]:
            base.update(
                {
                    "status": "universe_falsified_during_heldout",
                    "complementarity_status": "non_estimable",
                    "rule_history": history,
                    "heldout_transition_results": heldout_rows,
                    "heldout_scores": 2 * len(heldout_rows),
                    "final_surviving_world_ids": [],
                }
            )
            write_result(output, base)
            return base

    declaration_data = contract["complementarity_declaration"]
    declaration = PredictiveComplementarityDeclaration(
        metric_name=declaration_data["metric_name"],
        lower_is_better=declaration_data["lower_is_better"],
        expected_outer_unit_count=declaration_data["expected_outer_unit_count"],
        favorable_min_augmented_wins=declaration_data["favorable_min_augmented_wins"],
        adverse_min_baseline_wins=declaration_data["adverse_min_baseline_wins"],
        learner_fit_fingerprint=declaration_data["learner_fit_fingerprint"],
        response_endpoint_fingerprint=declaration_data["response_endpoint_fingerprint"],
        split_fingerprint=declaration_data["split_fingerprint"],
        external_feature_fingerprint=declaration_data["external_feature_fingerprint"],
        eog_feature_fingerprint=declaration_data["eog_feature_fingerprint"],
    )
    complementarity = evaluate_predictive_complementarity(
        declaration,
        paired_scores,
        tie_tolerance=float(declaration_data["tie_tolerance"]),
    )
    base.update(
        {
            "status": "completed_paired_complementarity",
            "complementarity_status": complementarity.status,
            "models_fit": 2,
            "heldout_scores": 2 * len(heldout_rows),
            "rule_history": history,
            "heldout_transition_results": heldout_rows,
            "complementarity": {
                "metric_name": complementarity.metric_name,
                "outer_unit_count": complementarity.outer_unit_count,
                "baseline_macro_score": complementarity.baseline_macro_score,
                "augmented_macro_score": complementarity.augmented_macro_score,
                "augmented_minus_baseline": complementarity.augmented_minus_baseline,
                "augmented_better_outer_units": complementarity.augmented_better_outer_units,
                "baseline_better_outer_units": complementarity.baseline_better_outer_units,
                "tied_outer_units": complementarity.tied_outer_units,
                "declaration_fingerprint": complementarity.declaration_fingerprint,
                "paired_score_fingerprint": complementarity.paired_score_fingerprint,
                "fingerprint": complementarity.fingerprint,
            },
            "final_surviving_world_ids": [
                world_id
                for world_id, flag in zip(WORLD_IDS, surviving, strict=True)
                if flag
            ],
        }
    )
    write_result(output, base)
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("smoke", "outcome"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_analysis(args.mode, args.output)
    print(
        json.dumps(
            {
                "status": result.get("status"),
                "mode": args.mode,
                "count_gate": result.get("count_gate"),
                "models_fit": result.get("models_fit"),
                "heldout_scores": result.get("heldout_scores"),
                "complementarity_status": result.get("complementarity_status"),
                "response_object_bytes_opened": result.get("response_object_bytes_opened"),
                "response_rows_opened": result.get("response_rows_opened"),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
