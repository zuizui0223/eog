from __future__ import annotations

import base64
import hashlib
import json
import math
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pyreadr
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss

from eog.v2.source_symmetric_predictive_summary import summarize_source_symmetric_support

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "validation/mapppd_adelie_selective_promotion/final_once_only_contract.json"
OUTPUT = ROOT / "build/mapppd_adelie_selective_promotion/final_result.json"
EARTH_RADIUS_KM = 6371.0088


def _get_blob(sha: str, ua: str) -> bytes:
    url = f"https://api.github.com/repos/CCheCastaldo/mapppdr/git/blobs/{sha}"
    req = Request(url, headers={"User-Agent": ua, "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=60) as r:  # noqa: S310 - frozen public GitHub blob
        raw = r.read()
        status = int(getattr(r, "status", 200))
    if status != 200:
        raise RuntimeError(f"GitHub blob HTTP status {status}")
    obj = json.loads(raw.decode("utf-8"))
    if obj.get("sha") != sha or obj.get("encoding") != "base64":
        raise RuntimeError(f"GitHub blob identity/encoding mismatch for {sha}")
    return base64.b64decode(obj["content"])


def _read_rda(raw: bytes):
    with tempfile.NamedTemporaryFile(suffix=".rda") as fh:
        fh.write(raw)
        fh.flush()
        objects = pyreadr.read_r(fh.name)
    if len(objects) != 1:
        raise RuntimeError(f"expected exactly one R object, found {len(objects)}")
    return next(iter(objects.values()))


def _haversine_matrix(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    la = np.radians(lat)
    lo = np.radians(lon)
    dlat = la[:, None] - la[None, :]
    dlon = lo[:, None] - lo[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def _fit_predict(xtr, ytr, xte, cfg):
    clf = RandomForestClassifier(
        n_estimators=cfg["n_estimators"],
        min_samples_leaf=cfg["min_samples_leaf"],
        max_features=cfg["max_features"],
        class_weight=cfg["class_weight"],
        random_state=cfg["random_state"],
        n_jobs=cfg["n_jobs"],
    )
    clf.fit(xtr, ytr)
    classes = list(clf.classes_)
    if 1 not in classes:
        raise RuntimeError("fitted learner lacks positive class")
    return clf.predict_proba(xte)[:, classes.index(1)]


def _macro(y, p, years, kind="logloss"):
    vals = []
    details = []
    for year in sorted(set(int(x) for x in years)):
        idx = np.asarray([int(x) == year for x in years], dtype=bool)
        yy, pp = y[idx], p[idx]
        if len(set(yy.tolist())) < 2:
            continue
        if kind == "logloss":
            val = float(log_loss(yy, np.column_stack([1 - pp, pp]), labels=[0, 1]))
        else:
            val = float(np.mean((pp - yy) ** 2))
        vals.append(val)
        details.append({"year": year, "n": int(idx.sum()), "positive": int(yy.sum()), "negative": int(idx.sum() - yy.sum()), "value": val})
    if not vals:
        raise RuntimeError(f"no eligible macro years for {kind}")
    return float(np.mean(vals)), details


def _layer_b(dist, source_site_idx, target_site_idx, thresholds, site_ids):
    if not target_site_idx:
        return np.empty((0, 10), dtype=float)
    if not source_site_idx:
        return np.zeros((len(target_site_idx), 10), dtype=float)
    support = np.zeros((len(source_site_idx), 5, len(target_site_idx)), dtype=float)
    for si, s in enumerate(source_site_idx):
        ds = dist[s, target_site_idx]
        for wi, th in enumerate(thresholds):
            support[si, wi, :] = (ds <= th).astype(float)
        support[si, 4, :] = 1.0
    res = summarize_source_symmetric_support(
        support,
        source_ids=[site_ids[i] for i in source_site_idx],
        world_ids=["q20", "q40", "q60", "q80", "external_open"],
        node_ids=[site_ids[i] for i in target_site_idx],
        declared_world_count=5,
    )
    return np.asarray(res.feature_matrix, dtype=float)


def _features_for_rows(rows, dist, thresholds, site_ids, site_to_idx, positive_by_year):
    out = []
    for site_id, year, _ in rows:
        source_sites = sorted({s for y, ss in positive_by_year.items() if y < year for s in ss})
        source_idx = [site_to_idx[s] for s in source_sites if s in site_to_idx]
        target_idx = [site_to_idx[site_id]]
        out.append(_layer_b(dist, source_idx, target_idx, thresholds, site_ids)[0])
    return np.asarray(out, dtype=float)


def _baseline(rows, site_coords):
    return np.asarray([
        [site_coords[s][0], site_coords[s][1], (year - 2001.0) / 12.0]
        for s, year, _ in rows
    ], dtype=float)


def _partition(rows, lo, hi):
    return [r for r in rows if lo <= r[1] <= hi]


def _counts(rows):
    y = np.asarray([r[2] for r in rows], dtype=int)
    years = [r[1] for r in rows]
    both = 0
    for yr in sorted(set(years)):
        vals = {r[2] for r in rows if r[1] == yr}
        both += int(vals == {0, 1})
    return {"n": len(rows), "positive": int(y.sum()), "negative": int(len(y) - y.sum()), "years": len(set(years)), "years_with_both_classes": both}


def main() -> int:
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.mapppd_adelie_selective_promotion.final_result.v1",
        "attempt_id": c["attempt_id"],
        "response_payload_requests": 0,
        "response_payload_bytes_opened": 0,
        "response_values_opened": False,
        "counts_as_predictive_evidence": False,
        "closed_eog_wf_unchanged": True,
    }
    try:
        # Nonresponse geometry may be re-read; it is not a biological endpoint response.
        sites_raw = _get_blob(c["geometry"]["sites_blob_sha"], "eog-mapppd-final-sites/1.0")
        sites_df = _read_rda(sites_raw)
        required_sites = {"site_id", "latitude", "longitude"}
        if not required_sites.issubset(sites_df.columns):
            raise RuntimeError(f"sites schema mismatch: {sorted(required_sites - set(sites_df.columns))}")
        site_coords = {}
        for _, row in sites_df.iterrows():
            sid = str(row["site_id"]).strip()
            lat, lon = float(row["latitude"]), float(row["longitude"])
            if sid and math.isfinite(lat) and math.isfinite(lon):
                site_coords[sid] = (lat, lon)
        site_ids = sorted(site_coords)
        site_to_idx = {s: i for i, s in enumerate(site_ids)}
        lat = np.asarray([site_coords[s][0] for s in site_ids], dtype=float)
        lon = np.asarray([site_coords[s][1] for s in site_ids], dtype=float)
        dist = _haversine_matrix(lat, lon)
        thresholds = [float(x) for x in c["geometry"]["local_thresholds_km"]]

        # The single authorized biological-response access begins here.
        response_sha = c["authoritative_response"]["git_blob_sha"]
        resp_raw = _get_blob(response_sha, "eog-mapppd-adelie-response-once/1.0")
        base["response_payload_requests"] = 1
        base["response_payload_bytes_opened"] = len(resp_raw)
        base["response_values_opened"] = True
        if len(resp_raw) != c["authoritative_response"]["git_blob_size_bytes"]:
            raise RuntimeError(f"response blob size drift: {len(resp_raw)}")
        resp_df = _read_rda(resp_raw)
        required = set(c["authoritative_response"]["required_columns"])
        if not required.issubset(resp_df.columns):
            raise RuntimeError(f"response schema mismatch: missing {sorted(required - set(resp_df.columns))}")

        focal = c["focal_response"]["species_id"]
        eligible = []
        for _, row in resp_df.iterrows():
            if str(row["species_id"]).strip() != focal:
                continue
            sid = str(row["site_id"]).strip()
            if sid not in site_to_idx:
                continue
            try:
                yf = float(row["year"])
                pf = float(row["presence"])
            except Exception:
                continue
            if not math.isfinite(yf) or int(yf) != yf or pf not in (0.0, 1.0):
                continue
            eligible.append((sid, int(yf), int(pf)))
        agg = {}
        for sid, year, presence in eligible:
            agg.setdefault((sid, year), []).append(presence)
        rows = sorted((sid, year, 1 if any(vals) else 0) for (sid, year), vals in agg.items())
        if not rows:
            raise RuntimeError("no eligible focal site-year rows")

        ranges = c["partition"]
        tr = _partition(rows, *ranges["inner_train_years"])
        va = _partition(rows, *ranges["inner_validation_years"])
        ou = _partition(rows, *ranges["outer_heldout_years"])
        cc = {"inner_train": _counts(tr), "inner_validation": _counts(va), "outer": _counts(ou)}
        mins = c["estimability_minima"]
        checks = [
            cc["inner_train"]["positive"] >= mins["inner_train_positive_site_years"],
            cc["inner_train"]["negative"] >= mins["inner_train_negative_site_years"],
            cc["inner_validation"]["positive"] >= mins["inner_validation_positive_site_years"],
            cc["inner_validation"]["negative"] >= mins["inner_validation_negative_site_years"],
            cc["outer"]["positive"] >= mins["outer_positive_site_years"],
            cc["outer"]["negative"] >= mins["outer_negative_site_years"],
            cc["inner_validation"]["years_with_both_classes"] >= mins["inner_validation_years_with_both_classes"],
            cc["outer"]["years_with_both_classes"] >= mins["outer_years_with_both_classes"],
        ]
        if not all(checks):
            raise RuntimeError(f"estimability failure: {cc}")

        positive_by_year = {}
        for sid, year, y in rows:
            if y == 1:
                positive_by_year.setdefault(year, set()).add(sid)

        xb_tr = _baseline(tr, site_coords)
        xb_va = _baseline(va, site_coords)
        lb_tr = _features_for_rows(tr, dist, thresholds, site_ids, site_to_idx, positive_by_year)
        lb_va = _features_for_rows(va, dist, thresholds, site_ids, site_to_idx, positive_by_year)
        ytr = np.asarray([r[2] for r in tr], dtype=int)
        yva = np.asarray([r[2] for r in va], dtype=int)
        cfg = c["learner"]
        p_b_va = _fit_predict(xb_tr, ytr, xb_va, cfg)
        p_a_va = _fit_predict(np.column_stack([xb_tr, lb_tr]), ytr, np.column_stack([xb_va, lb_va]), cfg)
        val_years = [r[1] for r in va]
        val_base, val_base_year = _macro(yva, p_b_va, val_years)
        val_aug, val_aug_year = _macro(yva, p_a_va, val_years)
        promote = bool(val_aug < val_base)

        cal = sorted(tr + va)
        xb_cal = _baseline(cal, site_coords)
        lb_cal = _features_for_rows(cal, dist, thresholds, site_ids, site_to_idx, positive_by_year)
        ycal = np.asarray([r[2] for r in cal], dtype=int)
        clf_b = RandomForestClassifier(n_estimators=cfg["n_estimators"], min_samples_leaf=cfg["min_samples_leaf"], max_features=cfg["max_features"], class_weight=cfg["class_weight"], random_state=cfg["random_state"], n_jobs=cfg["n_jobs"])
        clf_a = RandomForestClassifier(n_estimators=cfg["n_estimators"], min_samples_leaf=cfg["min_samples_leaf"], max_features=cfg["max_features"], class_weight=cfg["class_weight"], random_state=cfg["random_state"], n_jobs=cfg["n_jobs"])
        clf_b.fit(xb_cal, ycal)
        clf_a.fit(np.column_stack([xb_cal, lb_cal]), ycal)
        if 1 not in clf_b.classes_ or 1 not in clf_a.classes_:
            raise RuntimeError("refit learner lacks positive class")
        ib, ia = list(clf_b.classes_).index(1), list(clf_a.classes_).index(1)

        p_b_all, p_a_all, y_all, yr_all = [], [], [], []
        per_year = []
        for year in range(ranges["outer_heldout_years"][0], ranges["outer_heldout_years"][1] + 1):
            rr = [r for r in ou if r[1] == year]
            if not rr:
                continue
            xb = _baseline(rr, site_coords)
            lb = _features_for_rows(rr, dist, thresholds, site_ids, site_to_idx, positive_by_year)
            yy = np.asarray([r[2] for r in rr], dtype=int)
            pb = clf_b.predict_proba(xb)[:, ib]
            pa = clf_a.predict_proba(np.column_stack([xb, lb]))[:, ia]
            p_b_all.extend(pb.tolist()); p_a_all.extend(pa.tolist()); y_all.extend(yy.tolist()); yr_all.extend([year] * len(rr))
            if len(set(yy.tolist())) == 2:
                llb = float(log_loss(yy, np.column_stack([1-pb, pb]), labels=[0, 1]))
                lla = float(log_loss(yy, np.column_stack([1-pa, pa]), labels=[0, 1]))
                per_year.append({"year": year, "n": len(rr), "positive": int(yy.sum()), "baseline_log_loss": llb, "augmented_log_loss": lla, "augmented_minus_baseline": lla-llb})

        yout = np.asarray(y_all, dtype=int); pbout = np.asarray(p_b_all); paout = np.asarray(p_a_all); yearsout = yr_all
        base_ll, _ = _macro(yout, pbout, yearsout)
        aug_ll, _ = _macro(yout, paout, yearsout)
        base_br, _ = _macro(yout, pbout, yearsout, "brier")
        aug_br, _ = _macro(yout, paout, yearsout, "brier")
        sel_ll = aug_ll if promote else base_ll
        sel_br = aug_br if promote else base_br
        delta = sel_ll - base_ll
        if promote and delta < 0:
            terminal = "favorable_predictive_improvement"
        elif not promote and delta == 0 and aug_ll < base_ll:
            terminal = "conservative_miss"
        elif not promote and delta == 0:
            terminal = "protective_null"
        elif delta > 0:
            terminal = "adverse_selective_promotion"
        else:
            terminal = "tie_or_unclassified"

        trajectory = []
        seen = set()
        for year in sorted(set(r[1] for r in rows)):
            new = sorted(positive_by_year.get(year, set()))
            trajectory.append({"year": year, "positive_source_sites_before_year": len(seen), "new_positive_sites_in_year": len(set(new) - seen), "positive_source_sites_after_year": len(seen | set(new)), "declared_world_count": 5})
            seen.update(new)

        result = {
            **base,
            "status": "terminal_predictive_result",
            "terminal_class": terminal,
            "counts_as_predictive_evidence": True,
            "response_blob_sha": response_sha,
            "response_object_rows": int(len(resp_df)),
            "eligible_focal_rows_before_aggregation": len(eligible),
            "eligible_site_years": len(rows),
            "partition_counts": cc,
            "inner_validation": {"baseline_macro_log_loss": val_base, "augmented_macro_log_loss": val_aug, "augmented_minus_baseline": val_aug-val_base, "promote_layer_b": promote, "baseline_per_year": val_base_year, "augmented_per_year": val_aug_year},
            "outer": {"baseline_macro_log_loss": base_ll, "always_augmented_macro_log_loss": aug_ll, "selected_macro_log_loss": sel_ll, "selected_minus_baseline": delta, "always_augmented_minus_baseline": aug_ll-base_ll, "selected_minus_always_augmented": sel_ll-aug_ll, "baseline_macro_brier": base_br, "always_augmented_macro_brier": aug_br, "selected_macro_brier": sel_br, "per_year": per_year},
            "source_state_trajectory": trajectory,
            "known_truth_translation_to_real_improvement_supported": bool(delta < 0),
            "selector_protective_behavior_observed": bool((not promote) and aug_ll >= base_ll),
        }
    except Exception as exc:
        result = {
            **base,
            "status": "terminal_stop_after_or_before_response",
            "reason": str(exc),
            "closed_eog_wf_unchanged": True,
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
