from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTRACT = HERE / "stage0_nonresponse_contract.json"
OUTPUT = ROOT / "build/bbs_wild_turkey_selective_promotion/stage0_nonresponse.json"
BLOB_SHA = "bf82a3fce89aa1a6c86bc1669af6ff8a2bcc6d7e"
BLOB_URL = f"https://api.github.com/repos/pwilliams0/Bird_biotic_homogenization/git/blobs/{BLOB_SHA}"
EARTH_RADIUS_KM = 6371.0088


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _fetch_blob() -> bytes:
    req = Request(BLOB_URL, headers={"User-Agent": "eog-bbs-response-blind-stage0/1.0", "Accept": "application/vnd.github+json"})
    with urlopen(req, timeout=30) as r:  # noqa: S310 - frozen public GitHub blob URL
        raw = r.read()
        status = int(getattr(r, "status", 200))
    if status != 200:
        raise RuntimeError(f"GitHub blob HTTP status {status}")
    obj = json.loads(raw.decode("utf-8"))
    if obj.get("sha") != BLOB_SHA:
        raise RuntimeError("survey blob SHA drift")
    if obj.get("encoding") != "base64":
        raise RuntimeError("unexpected GitHub blob encoding")
    return base64.b64decode(obj["content"])


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def _quantile_linear(xs: list[float], q: float) -> float:
    vals = sorted(xs)
    if not vals:
        raise RuntimeError("no distances")
    pos = (len(vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    frac = pos - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    base = {
        "schema": "eog.bbs_wild_turkey_selective_promotion.stage0_nonresponse.v1",
        "attempt_id": contract["attempt_id"],
        "survey_blob_requests": 0,
        "response_blob_requests": 0,
        "response_header_bytes_opened": 0,
        "response_rows_opened": 0,
        "response_values_opened": False,
        "model_fits": 0,
        "heldout_scores": 0,
        "counts_as_predictive_evidence": False,
    }
    try:
        blob = _fetch_blob()
        base["survey_blob_requests"] = 1
        text = blob.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        required = {"cell_id", "Year", "Latitude", "Longitude", "First_year"}
        if not required.issubset(set(reader.fieldnames or [])):
            raise RuntimeError(f"missing required survey columns: {sorted(required - set(reader.fieldnames or []))}")

        grouped: dict[tuple[int, int], dict[str, list[float] | int]] = {}
        years: set[int] = set()
        for row in reader:
            cell = int(row["cell_id"])
            year = int(row["Year"])
            years.add(year)
            key = (cell, year)
            g = grouped.setdefault(key, {"lat": [], "lon": [], "first": [], "n": 0})
            g["lat"].append(float(row["Latitude"]))
            g["lon"].append(float(row["Longitude"]))
            g["first"].append(float(row["First_year"]))
            g["n"] += 1

        cell_years = []
        for (cell, year), g in sorted(grouped.items()):
            cell_years.append({
                "cell_id": cell,
                "Year": year,
                "Latitude": _mean(g["lat"]),
                "Longitude": _mean(g["lon"]),
                "observer_first_year_fraction": _mean(g["first"]),
                "survey_count": g["n"],
            })

        by_cell: dict[int, dict[str, list[float]]] = defaultdict(lambda: {"lat": [], "lon": []})
        for row in cell_years:
            by_cell[row["cell_id"]]["lat"].append(row["Latitude"])
            by_cell[row["cell_id"]]["lon"].append(row["Longitude"])
        centroids = {cell: (_mean(v["lat"]), _mean(v["lon"])) for cell, v in by_cell.items()}
        ids = sorted(centroids)
        distances = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                la, loa = centroids[a]
                lb, lob = centroids[b]
                distances.append(_haversine(la, loa, lb, lob))
        thresholds = [_quantile_linear(distances, q) for q in (0.2, 0.4, 0.6, 0.8)]

        partitions = {
            "inner_train": (1980, 2009),
            "inner_validation": (2010, 2015),
            "outer_heldout": (2016, 2022),
        }
        part_stats = {}
        for name, (lo, hi) in partitions.items():
            rows = [r for r in cell_years if lo <= r["Year"] <= hi]
            part_stats[name] = {
                "year_min": min((r["Year"] for r in rows), default=None),
                "year_max": max((r["Year"] for r in rows), default=None),
                "cell_year_rows": len(rows),
                "unique_cells": len({r["cell_id"] for r in rows}),
            }

        pass_gate = (
            min(years) <= 1980 and max(years) >= 2022
            and all(v["unique_cells"] >= 20 and v["cell_year_rows"] >= 100 for v in part_stats.values())
            and all(a < b for a, b in zip(thresholds, thresholds[1:]))
        )
        result = {
            **base,
            "status": "stage0_nonresponse_qualified" if pass_gate else "stop_pre_response_nonresponse_structure",
            "survey_blob_sha": BLOB_SHA,
            "survey_blob_bytes": len(blob),
            "year_min": min(years),
            "year_max": max(years),
            "unique_cells": len(ids),
            "cell_year_rows": len(cell_years),
            "partition_stats": part_stats,
            "distance_thresholds_km": thresholds,
            "external_open_world": True,
            "next_gate": "freeze final response semantics/model contract before any occurrence response payload access" if pass_gate else "none; no repair within this attempt",
        }
    except Exception as exc:
        result = {
            **base,
            "status": "stop_pre_response_nonresponse_transport_or_schema",
            "reason": str(exc),
            "next_gate": "none; no repair within this attempt",
        }
    result["fingerprint"] = _canonical_sha256(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
