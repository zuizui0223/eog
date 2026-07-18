#!/usr/bin/env python3
"""Predeclared real-taxon pilot for EOG issue #5."""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from eog import infer_occupancy_geometry
from eog.chelsa import DEFAULT_VARIABLES, sample_chelsa_at_coordinates

GBIF = "https://api.gbif.org/v1"
USER_AGENT = "eog-real-taxon-pilot/0.1 (https://github.com/zuizui0223/eog)"


def get_json(path: str, params: dict[str, object], retries: int = 4) -> dict:
    url = f"{GBIF}/{path}?{urlencode(params)}"
    error: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network path
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"GBIF request failed: {url}") from error


def polygon(row: dict[str, str]) -> str:
    x0, y0 = float(row["min_lon"]), float(row["min_lat"])
    x1, y1 = float(row["max_lon"]), float(row["max_lat"])
    return f"POLYGON(({x0} {y0},{x1} {y0},{x1} {y1},{x0} {y1},{x0} {y0}))"


def fetch_occurrences(row: dict[str, str], maximum: int) -> tuple[int, list[dict[str, object]]]:
    match = get_json("species/match", {"name": row["scientific_name"], "strict": "true"})
    taxon_key = int(match.get("usageKey") or 0)
    if not taxon_key:
        raise RuntimeError("GBIF taxon match failed")
    records: list[dict[str, object]] = []
    offset = 0
    while len(records) < maximum:
        payload = get_json(
            "occurrence/search",
            {
                "taxon_key": taxon_key,
                "geometry": polygon(row),
                "has_coordinate": "true",
                "has_geospatial_issue": "false",
                "limit": min(300, maximum - len(records)),
                "offset": offset,
            },
        )
        batch = payload.get("results", [])
        if not batch:
            break
        for item in batch:
            lat, lon = item.get("decimalLatitude"), item.get("decimalLongitude")
            if lat is None or lon is None:
                continue
            records.append({"key": int(item.get("key") or 0), "latitude": float(lat), "longitude": float(lon)})
        offset += len(batch)
        if payload.get("endOfRecords", False):
            break
    unique = {(r["latitude"], r["longitude"]): r for r in records}
    return taxon_key, sorted(unique.values(), key=lambda r: (r["key"], r["latitude"], r["longitude"]))


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def thin(records: list[dict[str, object]], distance_km: float) -> list[dict[str, object]]:
    kept: list[dict[str, object]] = []
    for record in records:
        point = (float(record["latitude"]), float(record["longitude"]))
        if all(haversine_km(point, (float(k["latitude"]), float(k["longitude"]))) >= distance_km for k in kept):
            kept.append(record)
    return kept


def cap_evenly(records: list[dict[str, object]], maximum: int) -> list[dict[str, object]]:
    if len(records) <= maximum:
        return records
    indices = np.linspace(0, len(records) - 1, maximum, dtype=int)
    return [records[int(i)] for i in indices]


def calibrated_gap(states: np.ndarray, raw: float, rng: np.random.Generator, draws: int) -> float:
    mean = states.mean(axis=0)
    cov = np.atleast_2d(np.cov(states, rowvar=False)) + np.eye(states.shape[1]) * 1e-8
    null = []
    for _ in range(draws):
        reference = rng.multivariate_normal(mean, cov, size=len(states))
        null.append(infer_occupancy_geometry(reference).gap_strength)
    values = np.asarray(null)
    return float(((values < raw).sum() + 0.5 * (values == raw).sum()) / draws)


def relative_error(value: float, reference: float) -> float:
    return abs(value - reference) / max(abs(reference), 1e-12)


def run(args: argparse.Namespace) -> dict[str, object]:
    rng = np.random.default_rng(args.seed)
    declarations = list(csv.DictReader(args.manifest.open(encoding="utf-8")))
    output_rows: list[dict[str, object]] = []
    stability_rows: list[dict[str, object]] = []

    for declaration in declarations:
        base = {
            "pair_id": declaration["pair_id"],
            "kingdom": declaration["kingdom"],
            "scientific_name": declaration["scientific_name"],
            "status": "failed",
            "failure_reason": "",
        }
        try:
            taxon_key, raw_records = fetch_occurrences(declaration, args.max_gbif_records)
            thinned = cap_evenly(thin(raw_records, args.thinning_km), args.max_analysis_records)
            sampled = sample_chelsa_at_coordinates(pd.DataFrame(thinned), variables=DEFAULT_VARIABLES)
            complete = sampled.frame.iloc[sampled.complete_indices].reset_index(drop=True)
            n_complete = len(complete)
            base.update({
                "gbif_taxon_key": taxon_key,
                "raw_coordinate_count": len(raw_records),
                "thinned_count": len(thinned),
                "complete_chelsa_count": n_complete,
                "variables": ";".join(DEFAULT_VARIABLES),
            })
            if n_complete < args.minimum_n:
                base.update(status="ineligible", failure_reason=f"complete_n<{args.minimum_n}")
                output_rows.append(base)
                continue

            states = complete[list(DEFAULT_VARIABLES)].to_numpy(float)
            geometry = infer_occupancy_geometry(states)
            percentile = calibrated_gap(states, geometry.gap_strength, rng, args.null_draws)
            base.update({
                "status": "eligible",
                "span": geometry.span,
                "continuity": geometry.continuity,
                "gap_strength": geometry.gap_strength,
                "calibrated_gap_percentile": percentile,
            })
            output_rows.append(base)

            subset_n = max(args.minimum_n, int(math.floor(len(states) * args.subsample_fraction)))
            for repeat in range(args.stability_repeats):
                subset = states[rng.choice(len(states), size=subset_n, replace=False)]
                sub_geometry = infer_occupancy_geometry(subset)
                stability_rows.append({
                    "pair_id": declaration["pair_id"],
                    "repeat": repeat + 1,
                    "subset_n": subset_n,
                    "span_relative_error": relative_error(sub_geometry.span, geometry.span),
                    "continuity_absolute_error": abs(sub_geometry.continuity - geometry.continuity),
                    "gap_relative_error": relative_error(sub_geometry.gap_strength, geometry.gap_strength),
                })
        except Exception as exc:
            base["failure_reason"] = f"{type(exc).__name__}: {exc}"
            output_rows.append(base)

    args.output.mkdir(parents=True, exist_ok=True)
    pair_path = args.output / "pair_summary.csv"
    fields = sorted({key for row in output_rows for key in row})
    with pair_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(output_rows)
    stability_path = args.output / "thinning_stability.csv"
    stability_fields = list(stability_rows[0]) if stability_rows else ["pair_id", "repeat", "subset_n"]
    with stability_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=stability_fields)
        writer.writeheader(); writer.writerows(stability_rows)

    eligible = [row for row in output_rows if row["status"] == "eligible"]
    gate = {
        "declared_pairs": len(declarations),
        "status_rows": len(output_rows),
        "eligible_pairs": len(eligible),
        "failed_pairs": sum(row["status"] == "failed" for row in output_rows),
        "ineligible_pairs": sum(row["status"] == "ineligible" for row in output_rows),
        "eligible_with_stability": len({row["pair_id"] for row in stability_rows}),
    }
    gate["passes"] = bool(
        gate["status_rows"] == gate["declared_pairs"]
        and gate["eligible_pairs"] >= args.minimum_eligible
        and gate["eligible_with_stability"] == gate["eligible_pairs"]
    )
    (args.output / "pilot_gate.json").write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    return gate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("benchmarks/real_taxon_pilot_manifest.csv"))
    parser.add_argument("--output", type=Path, default=Path("benchmark_results/real_taxon_pilot"))
    parser.add_argument("--seed", type=int, default=20260815)
    parser.add_argument("--max-gbif-records", type=int, default=3000)
    parser.add_argument("--max-analysis-records", type=int, default=240)
    parser.add_argument("--thinning-km", type=float, default=10.0)
    parser.add_argument("--minimum-n", type=int, default=60)
    parser.add_argument("--minimum-eligible", type=int, default=4)
    parser.add_argument("--null-draws", type=int, default=40)
    parser.add_argument("--stability-repeats", type=int, default=20)
    parser.add_argument("--subsample-fraction", type=float, default=0.8)
    args = parser.parse_args()
    gate = run(args)
    print(json.dumps(gate, indent=2))
    if not gate["passes"]:
        raise SystemExit("real-taxon pilot gate failed")


if __name__ == "__main__":
    main()
