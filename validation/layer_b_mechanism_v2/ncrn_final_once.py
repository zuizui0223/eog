#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_final_execution_contract_v1.json"
ROUTE_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_r1_response_route_contract_v1.json"
AUTH_PATH = ROOT / "validation/layer_b_mechanism_v2/ncrn_response_open_authorization_v1.json"
OUT = ROOT / "build/layer_b_mechanism_v2/ncrn_final/final_result.json"
REFERENCE = 2317363
POINTS_URL = f"https://irma.nps.gov/DataStore/DownloadFile/757401?Reference={REFERENCE}"
VISITS_URL = f"https://irma.nps.gov/DataStore/DownloadFile/757403?Reference={REFERENCE}"
RESPONSE_URL = f"https://irma.nps.gov/DataStore/DownloadFile/757402?Reference={REFERENCE}"
MISSING = {"", "na", "n/a", "nan", "null", "none"}


def get_bytes(url: str, ua: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/csv,text/plain,*/*"})
    with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 frozen public source
        return r.read()


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    raise RuntimeError("payload is not decodable as frozen public text")


def read_csv(raw: bytes) -> tuple[list[str], list[dict[str, str]]]:
    rd = csv.DictReader(io.StringIO(decode(raw)))
    if rd.fieldnames is None:
        raise RuntimeError("CSV has no header")
    return [str(x) for x in rd.fieldnames], list(rd)


def parse_year(raw: str) -> int:
    s = str(raw).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).year
        except ValueError:
            pass
    raise RuntimeError(f"cannot parse frozen EventDate year: {s!r}")


def parse_intlike(raw: str, label: str) -> int:
    s = str(raw).strip()
    try:
        x = float(s)
    except ValueError as exc:
        raise RuntimeError(f"{label} is not numeric: {s!r}") from exc
    if not math.isfinite(x) or not x.is_integer():
        raise RuntimeError(f"{label} is not finite integer-valued: {s!r}")
    return int(x)


def parse_flag(raw: str, label: str) -> int | None:
    s = str(raw).strip().lower()
    if s in MISSING:
        return None
    try:
        x = float(s)
    except ValueError as exc:
        raise RuntimeError(f"unexpected nonmissing {label} token: {raw!r}") from exc
    if not math.isfinite(x) or not x.is_integer() or int(x) not in (0, 1):
        raise RuntimeError(f"unexpected nonmissing {label} token: {raw!r}")
    return int(x)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(max(0.0, a))))


def macro_metric(y: np.ndarray, p: np.ndarray, years: np.ndarray, kind: str) -> float:
    vals: list[float] = []
    for year in sorted(set(int(v) for v in years.tolist())):
        mask = years == year
        yy, pp = y[mask], p[mask]
        if kind == "logloss":
            vals.append(float(log_loss(yy, np.column_stack([1.0 - pp, pp]), labels=[0, 1])))
        elif kind == "brier":
            vals.append(float(np.mean((pp - yy) ** 2)))
        else:
            raise ValueError(kind)
    if not vals:
        raise RuntimeError("no years available for macro metric")
    return float(np.mean(vals))


def fit_predict(xtr: np.ndarray, ytr: np.ndarray, xte: np.ndarray, cfg: dict) -> np.ndarray:
    clf = RandomForestClassifier(
        n_estimators=int(cfg["n_estimators"]),
        max_features=cfg["max_features"],
        min_samples_leaf=int(cfg["min_samples_leaf"]),
        class_weight=cfg["class_weight"],
        random_state=int(cfg["random_state"]),
        n_jobs=int(cfg["n_jobs"]),
    )
    clf.fit(xtr, ytr)
    if len(clf.classes_) != 2:
        raise RuntimeError(f"learner saw only one class: {clf.classes_.tolist()}")
    return clf.predict_proba(xte)[:, list(clf.classes_).index(1)]


def synthetic_payloads() -> tuple[bytes, bytes, bytes]:
    point_fields = ["Network", "Admin_Unit_Code", "Point_Name", "GRTS_Order", "Habitat", "Latitude", "Longitude", "ExportDate"]
    visit_fields = ["Admin_Unit_Code", "Point_Name", "GRTS_Order", "EventDate", "StartTime", "Visit", "Temperature", "AirTempUnits", "Humidity", "Sky_Condition", "Sky", "Wind_Code", "Wind", "Disturbance_Level", "Disturbance", "Observer", "Contact_Role", "Survey_Type", "DPL_Level", "EventNotes", "Event_ID", "ExportDate"]
    r1_fields = ["PointCode", "EventID", "EventYear", "EventDate", "ScientificName", "BirdCount", "ExcludeEvent", "NoObservations", "Incidental", "ExcludeObservation"]

    def csv_bytes(fields: list[str], rows: list[dict[str, object]]) -> bytes:
        buf = io.StringIO()
        wr = csv.DictWriter(buf, fieldnames=fields)
        wr.writeheader()
        for row in rows:
            wr.writerow(row)
        return buf.getvalue().encode()

    points: list[dict[str, object]] = []
    visits: list[dict[str, object]] = []
    r1: list[dict[str, object]] = []
    event = 100000
    nsites = 100
    for i in range(nsites):
        sid = f"S{i:03d}"
        lat = 38.0 + (i // 10) * 0.10
        lon = -78.0 + (i % 10) * 0.10
        points.append({"Network": "SYN", "Admin_Unit_Code": "SYN", "Point_Name": sid, "GRTS_Order": i, "Habitat": "Forest", "Latitude": lat, "Longitude": lon, "ExportDate": "2026-01-01"})
    for year in range(2007, 2020):
        for i in range(nsites):
            sid = f"S{i:03d}"
            event += 1
            date = f"05/15/{year}"
            visits.append({"Admin_Unit_Code": "SYN", "Point_Name": sid, "GRTS_Order": i, "EventDate": date, "StartTime": "06:00", "Visit": 1, "Temperature": 15, "AirTempUnits": "C", "Humidity": 50, "Sky_Condition": 1, "Sky": "clear", "Wind_Code": 0, "Wind": "calm", "Disturbance_Level": 0, "Disturbance": "none", "Observer": 1, "Contact_Role": "observer", "Survey_Type": "Forest", "DPL_Level": "1", "EventNotes": "", "Event_ID": event, "ExportDate": "2026-01-01"})
            # Moving spatial frontier with both classes every year.
            score = (i + 3 * (year - 2007)) % nsites
            positive = 20 <= score < 70
            species = "Melanerpes carolinus" if positive else "Cardinalis cardinalis"
            r1.append({"PointCode": sid, "EventID": event, "EventYear": year, "EventDate": date, "ScientificName": species, "BirdCount": 1, "ExcludeEvent": 0, "NoObservations": 0, "Incidental": 0, "ExcludeObservation": 0})
    return csv_bytes(point_fields, points), csv_bytes(visit_fields, visits), csv_bytes(r1_fields, r1)


def build_registry(points_raw: bytes, *, live: bool, contract: dict) -> tuple[dict[str, tuple[float, float]], set[str]]:
    header, rows = read_csv(points_raw)
    required = {"Point_Name", "Latitude", "Longitude"}
    if not required.issubset(header):
        raise RuntimeError(f"points missing frozen columns: {sorted(required - set(header))}")
    all_sites: set[str] = set()
    registry: dict[str, tuple[float, float]] = {}
    for row in rows:
        sid = str(row["Point_Name"]).strip()
        if not sid:
            raise RuntimeError("blank Point_Name in points")
        all_sites.add(sid)
        try:
            lat, lon = float(str(row["Latitude"]).strip()), float(str(row["Longitude"]).strip())
        except ValueError:
            continue
        if not math.isfinite(lat) or not math.isfinite(lon) or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            continue
        pair = (lat, lon)
        if sid in registry and registry[sid] != pair:
            raise RuntimeError(f"conflicting coordinates for {sid}")
        registry[sid] = pair
    if live:
        if len(registry) != int(contract["finite_registry"]["unique_sites"]):
            raise RuntimeError(f"finite registry count drift: {len(registry)}")
        payload = "\n".join(f"{s}\t{registry[s][0]:.12g}\t{registry[s][1]:.12g}" for s in sorted(registry)).encode()
        observed = hashlib.sha256(payload).hexdigest()
        if observed != contract["finite_registry"]["registry_sha256"]:
            raise RuntimeError(f"finite registry fingerprint drift: {observed}")
    if len(registry) < 50:
        raise RuntimeError(f"too few finite sites: {len(registry)}")
    return registry, all_sites


def build_visit_index(visits_raw: bytes, all_point_sites: set[str]) -> dict[int, tuple[str, int]]:
    header, rows = read_csv(visits_raw)
    required = {"Point_Name", "EventDate", "Event_ID"}
    if not required.issubset(header):
        raise RuntimeError(f"visits missing frozen columns: {sorted(required - set(header))}")
    out: dict[int, tuple[str, int]] = {}
    for row in rows:
        sid = str(row["Point_Name"]).strip()
        if sid not in all_point_sites:
            raise RuntimeError(f"visit Point_Name not in points registry: {sid}")
        year = parse_year(row["EventDate"])
        if year < 2007 or year > 2019:
            continue
        event = parse_intlike(row["Event_ID"], "Event_ID")
        value = (sid, year)
        if event in out and out[event] != value:
            raise RuntimeError(f"Event_ID maps to conflicting site/year: {event}")
        out[event] = value
    return out


def build_units(r1_raw: bytes, visit_index: dict[int, tuple[str, int]], registry: dict[str, tuple[float, float]], all_point_sites: set[str], route: dict) -> dict[int, dict[str, int]]:
    header, rows = read_csv(r1_raw)
    required = set(route["required_exact_columns_from_independent_metadata"])
    if not required.issubset(header):
        raise RuntimeError(f"response missing frozen exact columns: {sorted(required - set(header))}")
    target = route["target"]["scientific_name_exact"]
    event_state: dict[int, dict[str, object]] = defaultdict(lambda: {"eligible": False, "positive": False})
    for row in rows:
        year = parse_intlike(row["EventYear"], "EventYear")
        if year < 2007 or year > 2019:
            continue
        sid = str(row["PointCode"]).strip()
        if sid not in all_point_sites:
            raise RuntimeError(f"response PointCode not in frozen full points registry: {sid}")
        event = parse_intlike(row["EventID"], "EventID")
        if event not in visit_index:
            raise RuntimeError(f"response EventID missing from frozen visits registry: {event}")
        vsid, vyear = visit_index[event]
        if sid != vsid:
            raise RuntimeError(f"response/visit site mismatch for event {event}: {sid} != {vsid}")
        if year != vyear:
            raise RuntimeError(f"response/visit year mismatch for event {event}: {year} != {vyear}")
        # Frozen route requires all four flag columns to have only 0/1/nonmissing semantics.
        ex_event = parse_flag(row["ExcludeEvent"], "ExcludeEvent")
        no_obs = parse_flag(row["NoObservations"], "NoObservations")
        incidental = parse_flag(row["Incidental"], "Incidental")
        ex_obs = parse_flag(row["ExcludeObservation"], "ExcludeObservation")
        _ = no_obs
        state = event_state[event]
        if ex_event == 0:
            state["eligible"] = True
        if ex_event == 0 and str(row["ScientificName"]).strip() == target and incidental == 0 and ex_obs == 0:
            state["positive"] = True

    site_year: dict[tuple[str, int], int] = {}
    eligible_events_by_sy: dict[tuple[str, int], int] = defaultdict(int)
    for event, state in event_state.items():
        if not bool(state["eligible"]):
            continue
        sid, year = visit_index[event]
        if sid not in registry:
            continue
        key = (sid, year)
        eligible_events_by_sy[key] += 1
        site_year[key] = max(site_year.get(key, 0), int(bool(state["positive"])))
    units: dict[int, dict[str, int]] = defaultdict(dict)
    for (sid, year), y in site_year.items():
        if eligible_events_by_sy[(sid, year)] > 0:
            units[year][sid] = int(y)
    return dict(units)


def check_estimability(units: dict[int, dict[str, int]], years: list[int], minima: dict) -> dict[str, dict[str, int]]:
    receipt: dict[str, dict[str, int]] = {}
    for year in years:
        u = units.get(year, {})
        pos = int(sum(u.values()))
        neg = int(len(u) - pos)
        receipt[str(year)] = {"n": len(u), "positive": pos, "negative": neg, "unique_sites": len(u)}
        if pos < int(minima["per_scored_year_positive_site_years"]) or neg < int(minima["per_scored_year_negative_site_years"]) or len(u) < int(minima["per_scored_year_unique_sites"]):
            raise RuntimeError(f"estimability failure in {year}: {receipt[str(year)]}")
    return receipt


def build_distance_matrix(registry: dict[str, tuple[float, float]]) -> tuple[list[str], dict[str, int], np.ndarray]:
    sites = sorted(registry)
    index = {s: i for i, s in enumerate(sites)}
    d = np.zeros((len(sites), len(sites)), dtype=float)
    for i, s in enumerate(sites):
        for j in range(i + 1, len(sites)):
            t = sites[j]
            x = haversine(*registry[s], *registry[t])
            d[i, j] = d[j, i] = x
    return sites, index, d


def baseline_for_year(year: int, units: dict[int, dict[str, int]], registry: dict[str, tuple[float, float]]) -> tuple[list[str], np.ndarray, np.ndarray]:
    current = units.get(year, {})
    sites = sorted(current)
    prev = units.get(year - 1, {})
    prev_fraction = float(sum(prev.values()) / len(prev)) if prev else 0.0
    rows: list[list[float]] = []
    ys: list[int] = []
    for sid in sites:
        prior = [units[y][sid] for y in range(2007, year) if sid in units.get(y, {})]
        rate = float(sum(prior) / len(prior)) if prior else 0.0
        rows.append([
            float(registry[sid][0]),
            float(registry[sid][1]),
            float((year - 2007) / 12.0),
            float(prev.get(sid, 0)),
            rate,
            float(math.log1p(len(prior))),
            prev_fraction,
        ])
        ys.append(int(current[sid]))
    return sites, np.asarray(rows, dtype=float), np.asarray(ys, dtype=int)


def layer_b_for_year(year: int, dest_sites: list[str], source_sites: list[str], surviving: list[str], world_cfg: dict[str, float | None], site_index: dict[str, int], distances: np.ndarray) -> np.ndarray:
    if not source_sites:
        raise RuntimeError(f"empty previous-year positive source set for {year}")
    support = np.zeros((len(source_sites), len(surviving), len(dest_sites)), dtype=float)
    for si, source in enumerate(source_sites):
        sidx = site_index[source]
        for wi, wid in enumerate(surviving):
            threshold = world_cfg[wid]
            if threshold is None:
                support[si, wi, :] = 1.0
            else:
                for di, dest in enumerate(dest_sites):
                    support[si, wi, di] = float(distances[sidx, site_index[dest]] <= threshold)
    summary = summarize_source_symmetric_support(
        support,
        source_ids=source_sites,
        world_ids=surviving,
        node_ids=dest_sites,
        declared_world_count=5,
        support_threshold=0.0,
    )
    return summary.feature_matrix


def update_worlds(source_sites: list[str], positive_dest_sites: list[str], surviving: list[str], world_cfg: dict[str, float | None], site_index: dict[str, int], distances: np.ndarray) -> tuple[list[str], list[str]]:
    if not source_sites:
        raise RuntimeError("cannot update worlds from empty source set")
    kept: list[str] = []
    eliminated: list[str] = []
    for wid in surviving:
        threshold = world_cfg[wid]
        if threshold is None:
            kept.append(wid)
            continue
        compatible = True
        for dest in positive_dest_sites:
            didx = site_index[dest]
            reachable = any(distances[site_index[s], didx] <= threshold for s in source_sites)
            if not reachable:
                compatible = False
                break
        if compatible:
            kept.append(wid)
        else:
            eliminated.append(wid)
    if "external_open" not in kept:
        raise RuntimeError("external_open world was lost")
    return kept, eliminated


def prequential_features(units: dict[int, dict[str, int]], registry: dict[str, tuple[float, float]], start_year: int, end_year: int, initial_surviving: list[str], world_cfg: dict[str, float | None], site_index: dict[str, int], distances: np.ndarray) -> tuple[dict[int, dict[str, object]], list[str], list[dict[str, object]]]:
    surviving = list(initial_surviving)
    features: dict[int, dict[str, object]] = {}
    trajectory: list[dict[str, object]] = []
    for year in range(start_year, end_year + 1):
        source_sites = sorted(s for s, y in units.get(year - 1, {}).items() if y == 1)
        dest_sites, xb, yy = baseline_for_year(year, units, registry)
        lb = layer_b_for_year(year, dest_sites, source_sites, surviving, world_cfg, site_index, distances)
        features[year] = {"sites": dest_sites, "baseline": xb, "layer_b": lb, "y": yy}
        positive_dest = sorted(s for s, y in units.get(year, {}).items() if y == 1)
        before = list(surviving)
        surviving, eliminated = update_worlds(source_sites, positive_dest, surviving, world_cfg, site_index, distances)
        trajectory.append({
            "prediction_year": year,
            "source_year": year - 1,
            "source_positive_sites": len(source_sites),
            "positive_destinations": len(positive_dest),
            "surviving_before_prediction": before,
            "eliminated_after_year_observed": eliminated,
            "surviving_after_update": list(surviving),
        })
    return features, surviving, trajectory


def stack(feature_by_year: dict[int, dict[str, object]], years: list[int], augmented: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    return np.row_stack(xs), np.concatenate(ys), np.concatenate(yr)


def run_pipeline(points_raw: bytes, visits_raw: bytes, r1_raw: bytes, contract: dict, route: dict, *, live: bool) -> dict:
    registry, all_sites = build_registry(points_raw, live=live, contract=contract)
    visit_index = build_visit_index(visits_raw, all_sites)
    units = build_units(r1_raw, visit_index, registry, all_sites, route)
    scored_years = contract["partition"]["inner_train"] + contract["partition"]["inner_validation"] + contract["partition"]["outer_prequential"]
    counts = check_estimability(units, scored_years, contract["estimability_minima"])
    if not any(v == 1 for v in units.get(2007, {}).values()):
        raise RuntimeError("warmup 2007 has no positive finite-registry source sites")

    _, site_index, distances = build_distance_matrix(registry)
    world_cfg = {w["world_id"]: w["threshold_km"] for w in contract["geometry_worlds"]}
    all_worlds = [w["world_id"] for w in contract["geometry_worlds"]]

    # Calibration feature trajectory is completed only through 2015 before selection.
    cal_features, surviving_after_2015, cal_trajectory = prequential_features(
        units, registry, 2008, 2015, all_worlds, world_cfg, site_index, distances
    )
    tr_years = [int(x) for x in contract["partition"]["inner_train"]]
    va_years = [int(x) for x in contract["partition"]["inner_validation"]]
    xb_tr, y_tr, _ = stack(cal_features, tr_years, augmented=False)
    xa_tr, _, _ = stack(cal_features, tr_years, augmented=True)
    xb_va, y_va, yr_va = stack(cal_features, va_years, augmented=False)
    xa_va, _, _ = stack(cal_features, va_years, augmented=True)
    cfg = contract["learner"]
    pbv = fit_predict(xb_tr, y_tr, xb_va, cfg)
    pav = fit_predict(xa_tr, y_tr, xa_va, cfg)
    vbase = macro_metric(y_va, pbv, yr_va, "logloss")
    vaug = macro_metric(y_va, pav, yr_va, "logloss")
    promote = bool(vaug < vbase)
    selection_fingerprint = hashlib.sha256(json.dumps({"baseline": vbase, "augmented": vaug, "promote": promote}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    # Refit both arms on full calibration using exactly the already-created 2008-2015 prequential features.
    cal_years = [int(x) for x in contract["final_fit_and_outer"]["calibration_years"]]
    xb_cal, y_cal, _ = stack(cal_features, cal_years, augmented=False)
    xa_cal, _, _ = stack(cal_features, cal_years, augmented=True)

    # Outer features are now created prequentially. Earlier outer outcomes may update only biological state.
    outer_features, surviving_after_2019, outer_trajectory = prequential_features(
        units, registry, 2016, 2019, surviving_after_2015, world_cfg, site_index, distances
    )
    out_years = [int(x) for x in contract["partition"]["outer_prequential"]]
    xb_out, y_out, yr_out = stack(outer_features, out_years, augmented=False)
    xa_out, _, _ = stack(outer_features, out_years, augmented=True)
    pbo = fit_predict(xb_cal, y_cal, xb_out, cfg)
    pao = fit_predict(xa_cal, y_cal, xa_out, cfg)
    psel = pao if promote else pbo
    bll = macro_metric(y_out, pbo, yr_out, "logloss")
    all_ = macro_metric(y_out, pao, yr_out, "logloss")
    sll = macro_metric(y_out, psel, yr_out, "logloss")
    bbr = macro_metric(y_out, pbo, yr_out, "brier")
    abr = macro_metric(y_out, pao, yr_out, "brier")
    sbr = macro_metric(y_out, psel, yr_out, "brier")
    delta = float(sll - bll)
    if promote and delta < 0:
        terminal = "selective_favorable"
    elif (not promote) and delta == 0 and all_ < bll:
        terminal = "selective_conservative_miss"
    elif (not promote) and delta == 0:
        terminal = "selective_protective_null"
    elif delta > 0:
        terminal = "selective_adverse"
    else:
        terminal = "selective_protective_null"
    return {
        "status": "terminal_predictive_result" if live else "synthetic_validation_pass",
        "terminal_class": terminal,
        "partition_counts": counts,
        "inner_validation": {
            "baseline_macro_log_loss": vbase,
            "augmented_macro_log_loss": vaug,
            "augmented_minus_baseline": float(vaug - vbase),
            "promote_layer_b": promote,
            "selection_fingerprint_before_outer_scoring": selection_fingerprint,
        },
        "outer": {
            "baseline_macro_log_loss": bll,
            "always_augmented_macro_log_loss": all_,
            "selected_macro_log_loss": sll,
            "selected_minus_baseline": delta,
            "always_augmented_minus_baseline": float(all_ - bll),
            "selected_minus_always_augmented": float(sll - all_),
            "baseline_macro_brier": bbr,
            "always_augmented_macro_brier": abr,
            "selected_macro_brier": sbr,
        },
        "layer_a_trajectory": cal_trajectory + outer_trajectory,
        "surviving_worlds_after_2019": surviving_after_2019,
        "finite_registry_sites": len(registry),
        "eligible_site_years": int(sum(len(v) for v in units.values())),
        "known_truth_translation_to_real_improvement_supported": bool(delta < 0),
        "selector_protective_behavior_observed": bool((not promote) and all_ >= bll),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    contract = json.loads(CONTRACT_PATH.read_text())
    route = json.loads(ROUTE_PATH.read_text())
    base = {
        "schema": "eog.layer_b_mechanism_v2.ncrn_final_result.v1",
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
            points_raw, visits_raw, r1_raw = synthetic_payloads()
            result = {**base, **run_pipeline(points_raw, visits_raw, r1_raw, contract, route, live=False)}
        else:
            if not AUTH_PATH.exists():
                raise RuntimeError("live response access is not authorized: immutable authorization receipt missing")
            auth = json.loads(AUTH_PATH.read_text())
            if auth.get("attempt_id") != contract["attempt_id"] or auth.get("response_open_authorized") is not True:
                raise RuntimeError("live response authorization receipt does not match frozen attempt")
            points_raw = get_bytes(POINTS_URL, "eog-ncrn-final-points/1.0")
            visits_raw = get_bytes(VISITS_URL, "eog-ncrn-final-visits/1.0")
            if hashlib.sha256(points_raw).hexdigest() != contract["resources"]["points"]["sha256"]:
                raise RuntimeError("points checksum drift")
            if hashlib.sha256(visits_raw).hexdigest() != contract["resources"]["visits"]["sha256"]:
                raise RuntimeError("visits checksum drift")
            # Exactly one authorized biological response request occurs in the live runner.
            r1_raw = get_bytes(RESPONSE_URL, "eog-ncrn-final-response-once/1.0")
            base["response_payload_requests"] = 1
            base["response_payload_bytes_opened"] = len(r1_raw)
            base["response_values_opened"] = True
            response_sha = hashlib.sha256(r1_raw).hexdigest()
            result = {**base, **run_pipeline(points_raw, visits_raw, r1_raw, contract, route, live=True)}
            result["response_sha256"] = response_sha
            result["response_row_count"] = len(read_csv(r1_raw)[1])
            result["counts_as_predictive_evidence"] = result["status"] == "terminal_predictive_result"
    except Exception as exc:
        result = {**base, "status": "synthetic_validation_failure" if args.synthetic else "terminal_schema_or_transport_stop_after_response", "reason": f"{type(exc).__name__}: {exc}"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"synthetic_validation_pass", "terminal_predictive_result"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
