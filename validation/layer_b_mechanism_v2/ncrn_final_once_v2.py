#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import ncrn_final_once as core

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_final_execution_contract_v1.json"
ROUTE_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_r1_response_route_contract_v1.json"
AUTH_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_response_open_authorization_v1.json"
OUT = ROOT / "build/layer_b_mechanism_v2/ncrn_final/final_result.json"


def build_registry_v2(points_raw: bytes, *, live: bool, contract: dict):
    header, rows = core.read_csv(points_raw)
    required = {"Point_Name", "Latitude", "Longitude"}
    if not required.issubset(header):
        raise RuntimeError(f"points missing frozen columns: {sorted(required - set(header))}")
    all_sites: set[str] = set()
    registry: dict[str, tuple[float, float]] = {}
    for row in rows:
        sid = str(row["Point_Name"] or "").strip()
        if not sid:
            continue
        all_sites.add(sid)
        lat_raw = str(row["Latitude"] or "").strip().lower()
        lon_raw = str(row["Longitude"] or "").strip().lower()
        if lat_raw in core.MISSING or lon_raw in core.MISSING:
            continue
        try:
            lat, lon = float(lat_raw), float(lon_raw)
        except ValueError:
            continue
        if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            continue
        pair = (lat, lon)
        if sid in registry and registry[sid] != pair:
            raise RuntimeError(f"conflicting coordinates for {sid}")
        registry[sid] = pair
    if len(registry) < 50:
        raise RuntimeError(f"too few finite sites: {len(registry)}")
    if live:
        expected_n = int(contract["finite_registry"]["unique_sites"])
        if len(registry) != expected_n:
            raise RuntimeError(f"finite registry count drift: expected {expected_n}, got {len(registry)}")
        registry_payload = [[sid, lat, lon] for sid, (lat, lon) in sorted(registry.items())]
        observed = hashlib.sha256(json.dumps(registry_payload, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()
        expected = contract["finite_registry"]["registry_sha256"]
        if observed != expected:
            raise RuntimeError(f"finite registry fingerprint drift: expected {expected}, got {observed}")
    return registry, all_sites


def build_units_v2(r1_raw: bytes, visit_index: dict[int, tuple[str, int]], registry: dict[str, tuple[float, float]], all_point_sites: set[str], route: dict):
    header, rows = core.read_csv(r1_raw)
    expected_header = [str(x) for x in route["exact_header_from_independent_eml"]]
    if header != expected_header:
        raise RuntimeError(f"response exact-header mismatch: expected {len(expected_header)} columns, got {len(header)}")
    target = route["target"]["scientific_name_exact"]
    event_state: dict[int, dict[str, object]] = defaultdict(lambda: {"exclude_flags": [], "target_candidate": False})
    for row in rows:
        year = core.parse_intlike(row["EventYear"], "EventYear")
        if year < 2007 or year > 2019:
            continue
        sid = str(row["PointCode"]).strip()
        if sid not in all_point_sites:
            raise RuntimeError(f"response PointCode not in frozen full points registry: {sid}")
        if sid not in registry:
            continue
        event = core.parse_intlike(row["EventID"], "EventID")
        if event not in visit_index:
            raise RuntimeError(f"response EventID missing from frozen visits registry: {event}")
        vsid, vyear = visit_index[event]
        if sid != vsid:
            raise RuntimeError(f"response/visit site mismatch for event {event}: {sid} != {vsid}")
        if year != vyear:
            raise RuntimeError(f"response/visit year mismatch for event {event}: {year} != {vyear}")
        ex_event = core.parse_flag(row["ExcludeEvent"], "ExcludeEvent")
        no_obs = core.parse_flag(row["NoObservations"], "NoObservations")
        incidental = core.parse_flag(row["Incidental"], "Incidental")
        ex_obs = core.parse_flag(row["ExcludeObservation"], "ExcludeObservation")
        _ = no_obs
        state = event_state[event]
        flags = state["exclude_flags"]
        assert isinstance(flags, list)
        if ex_event is not None:
            flags.append(int(ex_event))
        if str(row["ScientificName"]).strip() == target and incidental == 0 and ex_obs == 0:
            state["target_candidate"] = True

    site_year: dict[tuple[str, int], int] = {}
    eligible_events_by_sy: dict[tuple[str, int], int] = defaultdict(int)
    for event, state in event_state.items():
        flags = state["exclude_flags"]
        assert isinstance(flags, list)
        eligible = bool(flags) and all(int(v) == 0 for v in flags)
        if not eligible:
            continue
        sid, year = visit_index[event]
        if sid not in registry:
            continue
        key = (sid, year)
        eligible_events_by_sy[key] += 1
        positive = int(bool(state["target_candidate"]))
        site_year[key] = max(site_year.get(key, 0), positive)
    units: dict[int, dict[str, int]] = defaultdict(dict)
    for (sid, year), y in site_year.items():
        if eligible_events_by_sy[(sid, year)] > 0:
            units[year][sid] = int(y)
    return dict(units)


def stack_v2(feature_by_year: dict[int, dict[str, object]], years: list[int], augmented: bool):
    """NumPy-2.5-compatible implementation of the frozen stacking algebra."""
    xs: list[np.ndarray] = []
    ys: list[np.ndarray] = []
    yr: list[np.ndarray] = []
    for year in years:
        f = feature_by_year[year]
        x = np.asarray(f["baseline"], float)
        if augmented:
            x = np.column_stack([x, np.asarray(f["layer_b"], float)])
        y = np.asarray(f["y"], int)
        xs.append(x)
        ys.append(y)
        yr.append(np.full(len(y), year, dtype=int))
    return np.vstack(xs), np.concatenate(ys), np.concatenate(yr)


def _terminal_status_for_exception(exc: Exception, *, synthetic: bool) -> str:
    if synthetic:
        return "synthetic_validation_failure"
    msg = str(exc)
    non_estimable_markers = (
        "estimability failure",
        "warmup 2007 has no positive finite-registry source sites",
        "empty previous-year positive source set",
        "learner saw only one class",
    )
    if any(marker in msg for marker in non_estimable_markers):
        return "terminal_non_estimable_under_frozen_rules"
    return "terminal_schema_or_transport_stop_after_response"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text())
    route = json.loads(ROUTE_PATH.read_text())
    core.build_registry = build_registry_v2
    core.build_units = build_units_v2
    core.stack = stack_v2
    base = {
        "schema": "eog.layer_b_mechanism_v2.ncrn_final_result.v2",
        "runner_version": "ncrn_final_once_v2",
        "attempt_id": contract["attempt_id"],
        "mode": "synthetic" if args.synthetic else "live",
        "response_payload_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_values_opened": False,
        "counts_as_predictive_evidence": False,
        "closed_eog_wf_unchanged": True,
    }
    try:
        if args.synthetic:
            points_raw, visits_raw, r1_raw = core.synthetic_payloads()
            synthetic_route = copy.deepcopy(route)
            synthetic_route["exact_header_from_independent_eml"] = core.read_csv(r1_raw)[0]
            result = {**base, **core.run_pipeline(points_raw, visits_raw, r1_raw, contract, synthetic_route, live=False)}
        else:
            if not AUTH_PATH.exists():
                raise RuntimeError("live response access is not authorized: immutable authorization receipt missing")
            auth = json.loads(AUTH_PATH.read_text())
            if auth.get("attempt_id") != contract["attempt_id"] or auth.get("response_open_authorized") is not True:
                raise RuntimeError("live response authorization receipt does not match frozen attempt")
            points_raw = core.get_bytes(core.POINTS_URL, "eog-ncrn-final-v2-points/1.0")
            visits_raw = core.get_bytes(core.VISITS_URL, "eog-ncrn-final-v2-visits/1.0")
            if hashlib.sha256(points_raw).hexdigest() != contract["resources"]["points"]["sha256"]:
                raise RuntimeError("points checksum drift")
            if hashlib.sha256(visits_raw).hexdigest() != contract["resources"]["visits"]["sha256"]:
                raise RuntimeError("visits checksum drift")
            # Count the one authorized biological response request before issuing it, so a transport failure cannot be misreported as zero requests.
            base["response_payload_requests"] = 1
            r1_raw = core.get_bytes(core.RESPONSE_URL, "eog-ncrn-final-v2-response-once/1.0")
            base["response_payload_bytes_opened"] = len(r1_raw)
            base["response_values_opened"] = True
            response_sha = hashlib.sha256(r1_raw).hexdigest()
            header, response_rows = core.read_csv(r1_raw)
            if header != route["exact_header_from_independent_eml"]:
                raise RuntimeError("response exact 60-column header mismatch")
            result = {**base, **core.run_pipeline(points_raw, visits_raw, r1_raw, contract, route, live=True)}
            result["response_sha256"] = response_sha
            result["response_row_count"] = len(response_rows)
            result["response_header_column_count"] = len(header)
            result["counts_as_predictive_evidence"] = result["status"] == "terminal_predictive_result"
    except Exception as exc:
        result = {
            **base,
            "status": _terminal_status_for_exception(exc, synthetic=args.synthetic),
            "reason": f"{type(exc).__name__}: {exc}",
        }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"synthetic_validation_pass", "terminal_predictive_result", "terminal_non_estimable_under_frozen_rules", "terminal_schema_or_transport_stop_after_response"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
